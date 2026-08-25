# -*- coding: utf-8 -*-
"""
fetch_kline.py — Part2 周线 K 线真实 OHLC 取数（确定性脚本，禁止手填/编造 K 线）
==============================================================================
主源: AKShare 前复权日频 → 按周聚合(开=周首开/高=周内最高/低=周内最低/收=周末收)
      A/HK=东财 stock_zh_a_hist/stock_hk_hist(qfq); US=sina stock_us_daily(qfq, 裸ticker 如 AAPL)
备援: 腾讯 ifzq.gtimg.cn 前复权周K(qfq, 直接周频) —— akshare 撞代理墙/超时时自动切换
      腾讯前缀: A股 6/900→sh, 0/3→sz, 4/8→bj; 港股 hkXXXXX; 美股需带交易所后缀(AAPL.OQ)

用法:
  python scripts/fetch_kline.py --ticker 002138 --market A --weeks 160 \
      --out _workspace/002138/price_weekly.json

输出 JSON:
  { ticker, market, source, adjust:"qfq", asof, weeks,
    weekly:[ {d:"YYYY-MM-DD", o,h,l,c,v}, ... ] }     # 直接可作 page_model.part2.weekly
校验(脚本内置, 不过则报错拒绝落盘):
  - 每根 h >= max(o,c) 且 l <= min(o,c)
  - 每根 o/h/l/c 四值齐全(绝不允许 c-only 的"假蜡烛")
  - 周数 >= --min-weeks (默认 100)
"""
import argparse, datetime as dt, json, os, sys, urllib.request

# 国内直连: 剥代理(akshare/腾讯走代理会 flaky)
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(k, None)


def _week_key(d):
    iso = dt.date.fromisoformat(d).isocalendar()
    return (iso[0], iso[1])


def aggregate_weekly(daily):
    """daily: [{d,o,h,l,c,v}] 升序 → 周线: 开=周首开 高=周内高 低=周内低 收=周末收 量=周和"""
    out, cur, key = [], None, None
    for row in daily:
        wk = _week_key(row["d"])
        if wk != key:
            if cur: out.append(cur)
            key, cur = wk, dict(row)
        else:
            cur["h"] = max(cur["h"], row["h"])
            cur["l"] = min(cur["l"], row["l"])
            cur["c"] = row["c"]
            cur["v"] = round(cur.get("v", 0) + row.get("v", 0), 2)
            cur["d"] = row["d"]          # 周标签 = 周内最后交易日
    if cur: out.append(cur)
    return out


# ---------------------------------------------------------------- AKShare 主源
def fetch_akshare(ticker, market, start):
    import akshare as ak
    s = start.replace("-", "")
    if market == "A":
        df = ak.stock_zh_a_hist(symbol=ticker, period="daily", start_date=s, adjust="qfq")
        src = "akshare(东财 qfq 日频→周聚合)"
    elif market == "HK":
        df = ak.stock_hk_hist(symbol=ticker.zfill(5), period="daily", start_date=s, adjust="qfq")
        src = "akshare(东财 qfq 日频→周聚合)"
    else:  # US: stock_us_hist 需要东财带市场前缀代码(105.AAPL), 裸 ticker 走 sina stock_us_daily
        df = ak.stock_us_daily(symbol=ticker.upper(), adjust="qfq")
        df = df[df["date"].astype(str) >= start]
        src = "akshare(sina us qfq 日频→周聚合)"
    cols = {"日期": "d", "开盘": "o", "最高": "h", "最低": "l", "收盘": "c", "成交量": "v",
            "date": "d", "open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"}
    df = df.rename(columns=cols)
    daily = [{"d": str(r["d"])[:10], "o": float(r["o"]), "h": float(r["h"]),
              "l": float(r["l"]), "c": float(r["c"]), "v": float(r.get("v", 0) or 0)}
             for _, r in df.iterrows()]
    return daily, src


# ---------------------------------------------------------------- 腾讯备援(qfq 周K 直取)
def _tencent_symbol(ticker, market):
    if market == "A":
        # 6xxxxx→sh, 900xxx 沪B→sh, 0/3→sz, 4/8→bj(北交所)
        pre = "sh" if ticker[0] in "69" else ("bj" if ticker[0] in "48" else "sz")
        return pre + ticker
    if market == "HK":
        return "hk" + ticker.zfill(5)
    # US: 腾讯需带交易所后缀(usAAPL.OQ/usBRK.N)——调用方给裸码时大概率查不到, 由上层报清晰错误
    return "us" + ticker.upper()


def fetch_tencent(ticker, market, weeks):
    sym = _tencent_symbol(ticker, market)
    url = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           f"param={sym},week,,,{max(weeks + 10, 120)},qfq")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))
    node = (raw.get("data") or {}).get(sym) or {}
    bars = node.get("qfqweek") or node.get("week") or []
    if not bars:
        raise SystemExit(f"❌ 腾讯备援也无数据: {sym}。美股请用带交易所后缀的代码(如 AAPL.OQ)重试, "
                         f"或 A/HK 检查代码是否正确。")
    weekly = [{"d": b[0], "o": float(b[1]), "c": float(b[2]),
               "h": float(b[3]), "l": float(b[4]), "v": float(b[5])} for b in bars]
    return weekly, "腾讯 ifzq.gtimg.cn(qfq 周K)"


# ---------------------------------------------------------------- 校验闸门
def validate(weekly, min_weeks):
    if len(weekly) < min_weeks:
        raise SystemExit(f"❌ 周数 {len(weekly)} < {min_weeks}, 拒绝落盘(拉长 start 或查代码)")
    bad = [w for w in weekly
           if not all(isinstance(w.get(k), (int, float)) for k in "ohlc")
           or w["h"] < max(w["o"], w["c"]) - 1e-9
           or w["l"] > min(w["o"], w["c"]) + 1e-9]
    if bad:
        raise SystemExit(f"❌ {len(bad)} 根K线 OHLC 不自洽(如 {bad[0]}), 数据源异常, 拒绝落盘")
    flat = sum(1 for w in weekly if w["h"] == w["l"])
    if flat > len(weekly) * 0.1:
        raise SystemExit(f"❌ {flat} 根K线 高==低(疑似 c-only 假蜡烛), 拒绝落盘")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True, help="裸代码: 002138 / 00700 / AAPL")
    ap.add_argument("--market", default="A", choices=["A", "HK", "US"])
    ap.add_argument("--weeks", type=int, default=160, help="目标周数(默认160≈3年)")
    ap.add_argument("--min-weeks", type=int, default=120,
                    help="与 CK-2 对齐默认 120; 次新股不足时显式调低并在页面声明降级")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    start = (dt.date.today() - dt.timedelta(weeks=a.weeks + 6)).isoformat()
    weekly, src = None, None
    try:
        daily, src = fetch_akshare(a.ticker, a.market, start)
        weekly = aggregate_weekly(daily)
    except Exception as e:
        print(f"⚠️ akshare 失败({type(e).__name__}: {e}), 切腾讯备援", file=sys.stderr)
        weekly, src = fetch_tencent(a.ticker, a.market, a.weeks)

    weekly = [w for w in weekly if w["d"] >= start][-a.weeks:]
    for w in weekly:                      # 统一保留2位小数, v 转手为准不强求
        for k in "ohlc": w[k] = round(w[k], 3)
    validate(weekly, a.min_weeks)

    out = {"ticker": a.ticker, "market": a.market, "source": src, "adjust": "qfq",
           "asof": dt.date.today().isoformat(), "weeks": len(weekly), "weekly": weekly}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"✅ {a.ticker} {len(weekly)} 周 OHLC ← {src} → {a.out}")
    print(f"   首末: {weekly[0]['d']} .. {weekly[-1]['d']}  "
          f"收盘区间 {min(w['c'] for w in weekly)}–{max(w['c'] for w in weekly)}")


if __name__ == "__main__":
    main()
