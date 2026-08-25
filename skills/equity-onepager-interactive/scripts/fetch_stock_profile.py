#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fetch_stock_profile.py — 开篇章「第一点 公司类型」的股性画像取数（确定性脚本）
==============================================================================
为什么存在：公司类型要回答「大盘还是小盘 / 历史涨停多少次 / 股性怎么样 / 谁在玩」，
这四问全部需要**日线级**数据 + 全市场市值分位，而 skill 原有的 fetch_kline.py 只出周线。
本脚本只做 FETCH+统计，**不做定性判断**（"游资票还是机构票"由 agent 结合
page_model.part1.shareholders.factions_ts 人工判定，脚本只给客观计数）。

用法:
  python scripts/fetch_stock_profile.py --ticker 002371 --market A --years 3 \
      --out _workspace/002371/stock_profile.json

产出 JSON:
  cap{mcap_yi,rank,pct,tier}            市值分层：全市场排名/分位/大中小盘判定
  limit{up,down,up_1y,max_streak,...}   涨停/跌停计数(A股口径 ±10%/20%；港美股退化为 ±9% 大波动日)
  vol{ann_vol,max_dd,avg_amp,turnover}  年化波动/最大回撤/日均振幅/日均换手
  beta{beta,corr,bench}                 对基准指数的 beta 与相关系数
  ⚠️ 所有字段带 window 与 caliber，口径不明的宁可缺失也不猜。
"""
import argparse, datetime as dt, json, math, os, sys

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)


def _ak():
    import akshare as ak
    return ak


def retry(fn, n=4, wait=1.5, label=""):
    """东财/新浪接口 flaky（实测 RemoteDisconnected 随机命中任一步）→ 统一重试"""
    import time
    last = None
    for i in range(n):
        try:
            return fn()
        except Exception as e:
            last = e
            if i < n - 1:
                print("      ⚠️ %s 第%d次失败(%s)，重试" % (label or "取数", i + 1, type(e).__name__),
                      file=sys.stderr, flush=True)
                time.sleep(wait * (i + 1))
    raise last


# ---------------------------------------------------------------- 涨跌停幅度口径
def limit_pct(ticker, market):
    """A 股按板块定涨跌停幅度；港美股无涨跌停 → 退化为 ±9% 大波动日计数"""
    if market != "A":
        return 9.0, "无涨跌停制度，口径退化为『单日涨跌幅≥9%』的大波动日计数"
    t = ticker.zfill(6)
    if t.startswith(("688", "689")):
        return 20.0, "科创板 ±20%"
    if t.startswith("30"):
        return 20.0, "创业板 ±20%"
    if t.startswith(("8", "4")):
        return 30.0, "北交所 ±30%"
    return 10.0, "主板 ±10%"


# ---------------------------------------------------------------- 腾讯备援(东财/新浪不可达时)
# 为什么加：实测东财 push2his 直连被拒 + 代理挂掉时，akshare 整条腿失效；
# 腾讯 ifzq.gtimg.cn 是 fetch_kline.py 已验证可用的同源备援，此处复用同一取数口径。
def _tencent_sym(ticker, market):
    if market == "A":
        return ("sh" if ticker[0] in "69" else ("bj" if ticker[0] in "48" else "sz")) + ticker
    if market == "HK":
        return "hk" + ticker.zfill(5)
    return "us" + ticker.upper()


def _tencent_daily(sym, start, adjust=""):
    """腾讯日K → [{d,o,h,l,c,v}]（升序）。adjust=''(不复权,涨跌停口径) / 'qfq'。"""
    import json as _json, urllib.request
    tag = "qfq" if adjust == "qfq" else ""
    url = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           "param=%s,day,,,2000,%s" % (sym, tag))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = _json.loads(urllib.request.urlopen(req, timeout=25).read().decode("utf-8"))
    node = (raw.get("data") or {}).get(sym) or {}
    bars = node.get(("qfq" if tag else "") + "day") or node.get("day") or []
    out = []
    for b in bars:
        if str(b[0])[:10] < start:
            continue
        out.append({"d": str(b[0])[:10], "o": float(b[1]), "c": float(b[2]),
                    "h": float(b[3]), "l": float(b[4]), "v": float(b[5] or 0)})
    return out


def _fill_pct_amp(rows):
    for i, r in enumerate(rows):
        if r.get("pct") is None and i:
            pc = rows[i - 1]["c"]
            r["pct"] = round((r["c"] / pc - 1) * 100, 4) if pc else None
        if r.get("amp") is None and i:
            pc = rows[i - 1]["c"]
            r["amp"] = round((r["h"] - r["l"]) / pc * 100, 4) if pc else None
    return rows


# ---------------------------------------------------------------- 日线
def daily(ticker, market, start):
    ak = _ak()
    try:
        return _daily_ak(ak, ticker, market, start)
    except Exception as e:
        print("      ⚠️ akshare 日线整腿失败(%s)，切腾讯备援" % type(e).__name__,
              file=sys.stderr, flush=True)
        rows = _tencent_daily(_tencent_sym(ticker, market), start, adjust="")
        if not rows:
            raise
        # 腾讯不给换手率 → to 缺失，由 main() 记 gap；pct/amp 自算
        return _fill_pct_amp(rows)


def _daily_ak(ak, ticker, market, start):
    if market == "A":
        df = retry(lambda: ak.stock_zh_a_hist(symbol=ticker, period="daily",
                   start_date=start.replace("-", ""), adjust=""), n=2, label="A股日线")
        # ⚠️ 涨跌停要用**不复权**价，复权后 pct 会失真
        cols = {"日期": "d", "开盘": "o", "最高": "h", "最低": "l", "收盘": "c",
                "成交量": "v", "换手率": "to", "涨跌幅": "pct", "振幅": "amp"}
    elif market == "HK":
        df = retry(lambda: ak.stock_hk_hist(symbol=ticker.zfill(5), period="daily",
                   start_date=start.replace("-", ""), adjust=""), label="港股日线")
        cols = {"日期": "d", "开盘": "o", "最高": "h", "最低": "l", "收盘": "c",
                "成交量": "v", "涨跌幅": "pct", "振幅": "amp"}
    else:
        df = retry(lambda: ak.stock_us_daily(symbol=ticker.upper(), adjust=""), label="美股日线")
        df = df[df["date"].astype(str) >= start]
        cols = {"date": "d", "open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"}
    df = df.rename(columns=cols)
    rows = []
    for _, r in df.iterrows():
        row = {"d": str(r["d"])[:10]}
        for k in ("o", "h", "l", "c", "v", "to", "pct", "amp"):
            if k in df.columns:
                try:
                    row[k] = float(r[k])
                except (TypeError, ValueError):
                    row[k] = None
        rows.append(row)
    # pct/amp 缺失时自算（美股接口不给）
    for i, r in enumerate(rows):
        if r.get("pct") is None and i:
            pc = rows[i - 1]["c"]
            r["pct"] = round((r["c"] / pc - 1) * 100, 4) if pc else None
        if r.get("amp") is None and i:
            pc = rows[i - 1]["c"]
            r["amp"] = round((r["h"] - r["l"]) / pc * 100, 4) if pc else None
    return rows


# ---------------------------------------------------------------- 市值分层
def cap_tier(ticker, market, gaps):
    """全 A 总市值排名 → 分位 → 大/中/小盘。港美股无零鉴权全市场快照 → 只给市值不给分位。"""
    if market != "A":
        gaps.append("市值分位：港美股无零鉴权全市场快照，只能给绝对市值，分层需人工按当地市场惯例判定")
        return None
    ak = _ak()
    # 主口径＝指数成分归属（A 股通行的大/中/小盘分层，比"市值前x%"更可辩护，
    # 且只需 3 个小请求；全市场快照实测长时间 RemoteDisconnected，只作补充）
    idx_tier = None
    IDX = [("000300", "沪深300", "大盘股"), ("000905", "中证500", "中盘股"), ("000852", "中证1000", "小盘股")]
    t6 = ticker.zfill(6)
    for code, name, tier in IDX:
        try:
            cons = retry(lambda c=code: ak.index_stock_cons_csindex(symbol=c), n=2, label=name + "成分")
            colc = "成分券代码" if "成分券代码" in cons.columns else cons.columns[4]
            if (cons[colc].astype(str).str.zfill(6) == t6).any():
                idx_tier = {"tier": tier, "index": name,
                            "caliber": "指数成分归属：沪深300＝大盘 / 中证500＝中盘 / 中证1000＝小盘（A 股通行分层）"}
                break
        except Exception as e:
            gaps.append("%s 成分取数失败(%s)" % (name, type(e).__name__))
    if idx_tier is None and not any("成分取数失败" in g for g in gaps):
        idx_tier = {"tier": "微盘/指数外", "index": None,
                    "caliber": "不在沪深300/中证500/中证1000 任一成分内"}

    # 补充：全市场市值排名分位（拿得到就给，拿不到不阻塞）
    sp, col, src = None, None, None
    for attempt in (1, 2):
        try:
            sp = retry(ak.stock_zh_a_spot_em, n=2, label="全A快照(东财)"); col = "总市值"; src = "东财实时快照"
            break
        except Exception as e:
            err = str(e)[:60]
    if sp is None:
        try:
            sp = retry(ak.stock_zh_a_spot, n=2, label="全A快照(新浪)")   # 新浪：`mktcap` 单位万元
            col = "mktcap"; src = "新浪实时快照"
            sp[col] = sp[col].astype(float) * 1e4
        except Exception as e2:
            gaps.append("市值分位(补充项)：东财(%s)与新浪(%s)全市场快照均失败 → 只给指数成分分层"
                        % (err, str(e2)[:50]))
            return idx_tier
    if col not in sp.columns:
        gaps.append("市值分位(补充项)：快照无市值列")
        return idx_tier
    if "代码" not in sp.columns and "symbol" in sp.columns:
        sp["代码"] = sp["symbol"].astype(str).str[-6:]
    sp = sp[[c for c in ("代码", "名称", col) if c in sp.columns]].dropna()
    sp = sp.sort_values(col, ascending=False).reset_index(drop=True)
    hit = sp[sp["代码"].astype(str).str.zfill(6) == ticker.zfill(6)]
    if not len(hit):
        gaps.append("市值分位(补充项)：全市场快照里没找到 %s" % ticker)
        return idx_tier
    idx = int(hit.index[0]); n = len(sp)
    mcap = float(hit.iloc[0][col])
    pct = (idx + 1) / n            # 从大到小的位置分位，越小越大盘
    # A 股常用分层：前 5% 大盘 / 5-20% 中盘 / 其余小盘（另给绝对市值口径交叉验证）
    tier_pct = "大盘股" if pct <= 0.05 else ("中盘股" if pct <= 0.20 else "小盘股")
    out = dict(idx_tier or {})
    out.update({"mcap_yi": round(mcap / 1e8, 1), "rank": idx + 1, "universe": n,
                "pct_from_top": round(pct * 100, 2), "tier_by_pct": tier_pct,
                "pct_caliber": "全 A 总市值降序排名；前 5%%＝大盘、5–20%%＝中盘、其余小盘（%s）" % src})
    out.setdefault("tier", tier_pct)
    return out


# ---------------------------------------------------------------- 统计
def stats(rows, lim, years, gaps):
    if len(rows) < 60:
        gaps.append("股性统计：日线仅 %d 根，样本不足" % len(rows))
    up = [r for r in rows if r.get("pct") is not None and r["pct"] >= lim - 0.3]
    dn = [r for r in rows if r.get("pct") is not None and r["pct"] <= -(lim - 0.3)]
    today = dt.date.today()
    y1 = (today - dt.timedelta(days=365)).isoformat()
    # 连板：连续交易日涨停
    streak = best = 0
    for r in rows:
        if r.get("pct") is not None and r["pct"] >= lim - 0.3:
            streak += 1; best = max(best, streak)
        else:
            streak = 0
    rets = [r["pct"] / 100.0 for r in rows if r.get("pct") is not None]
    mu = sum(rets) / len(rets) if rets else 0
    var = sum((x - mu) ** 2 for x in rets) / (len(rets) - 1) if len(rets) > 1 else 0
    ann = math.sqrt(var) * math.sqrt(252) * 100
    peak = -1e18; mdd = 0
    for r in rows:
        peak = max(peak, r["c"])
        if peak > 0:
            mdd = min(mdd, r["c"] / peak - 1)
    amps = [r["amp"] for r in rows if r.get("amp") is not None]
    tos = [r["to"] for r in rows if r.get("to") is not None]
    return {
        "limit": {"window_years": years, "n_days": len(rows),
                  "up": len(up), "down": len(dn),
                  "up_last_1y": len([r for r in up if r["d"] >= y1]),
                  "max_streak": best,
                  "up_dates_recent": [r["d"] for r in up][-8:],
                  "caliber": "涨跌幅达 ±%.0f%%（留 0.3pct 容差）计一次；不复权价" % lim},
        "vol": {"ann_vol_pct": round(ann, 1),
                "max_drawdown_pct": round(mdd * 100, 1),
                "avg_amplitude_pct": round(sum(amps) / len(amps), 2) if amps else None,
                "avg_turnover_pct": round(sum(tos) / len(tos), 2) if tos else None,
                "caliber": "年化波动＝日收益标准差×√252；最大回撤按窗口内收盘价"},
    }


def beta(rows, market, start, gaps):
    """对基准指数的 beta（A股=沪深300；港=恒生；美股跳过）"""
    if market == "US":
        return None
    ak = _ak()
    try:
        if market == "A":
            bench = "沪深300"
            try:
                b = retry(lambda: ak.stock_zh_index_daily(symbol="sh000300"), n=2, label="沪深300")
                bd = {str(r["date"])[:10]: float(r["close"]) for _, r in b.iterrows()}
            except Exception:
                bd = {r["d"]: r["c"] for r in _tencent_daily("sh000300", start)}
        else:
            b = ak.stock_hk_index_daily_em(symbol="HSI")
            bench = "恒生指数"
            bd = {str(r["latest"])[:10] if "latest" in b.columns else str(r.iloc[0])[:10]: float(r["close"])
                  for _, r in b.iterrows()}
    except Exception as e:
        gaps.append("beta：基准指数取数失败(%s)" % str(e)[:80])
        return None
    ds = sorted(set(bd) & {r["d"] for r in rows})
    ds = [x for x in ds if x >= start]
    if len(ds) < 60:
        gaps.append("beta：与基准重叠交易日仅 %d 根" % len(ds))
        return None
    cd = {r["d"]: r["c"] for r in rows}
    rs, bs = [], []
    for i in range(1, len(ds)):
        p0, p1 = cd.get(ds[i - 1]), cd.get(ds[i])
        q0, q1 = bd.get(ds[i - 1]), bd.get(ds[i])
        if p0 and p1 and q0 and q1:
            rs.append(p1 / p0 - 1); bs.append(q1 / q0 - 1)
    n = len(rs)
    if n < 60:
        return None
    mr = sum(rs) / n; mb = sum(bs) / n
    cov = sum((rs[i] - mr) * (bs[i] - mb) for i in range(n)) / (n - 1)
    vb = sum((x - mb) ** 2 for x in bs) / (n - 1)
    vr = sum((x - mr) ** 2 for x in rs) / (n - 1)
    return {"bench": bench, "beta": round(cov / vb, 2) if vb else None,
            "corr": round(cov / math.sqrt(vr * vb), 2) if vr and vb else None, "n_days": n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--market", default="A", choices=["A", "HK", "US"])
    ap.add_argument("--years", type=int, default=3, help="股性统计窗口(默认3年,与Part2对齐)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    gaps = []
    start = (dt.date.today() - dt.timedelta(days=int(a.years * 365.25))).isoformat()
    lim, lim_note = limit_pct(a.ticker, a.market)
    print("[1/3] 日线 (%s, %s起) ..." % (a.market, start), flush=True)
    rows = daily(a.ticker, a.market, start)
    print("      %d 根" % len(rows))
    print("[2/3] 市值分层 ...", flush=True)
    cap = cap_tier(a.ticker, a.market, gaps)
    print("[3/3] 股性统计 + beta ...", flush=True)
    st = stats(rows, lim, a.years, gaps)
    bt = beta(rows, a.market, start, gaps)

    out = {"ticker": a.ticker, "market": a.market, "asof": dt.date.today().isoformat(),
           "window": {"start": start, "years": a.years}, "limit_rule": lim_note,
           "cap": cap, "limit": st["limit"], "vol": st["vol"], "beta": bt, "gaps": gaps}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("✅ %s" % a.out)
    if cap:
        line = "   分层 %s" % cap.get("tier")
        if cap.get("index"): line += "（%s 成分）" % cap["index"]
        if cap.get("rank"): line += " · 全A第 %d/%d (前 %.1f%%)" % (cap["rank"], cap["universe"], cap["pct_from_top"])
        print(line)
    L, V = st["limit"], st["vol"]
    print("   近%d年: 涨停 %d 次(近1年 %d 次) · 最高 %d 连板 · 跌停 %d 次"
          % (a.years, L["up"], L["up_last_1y"], L["max_streak"], L["down"]))
    print("   年化波动 %s%% · 最大回撤 %s%% · 日均振幅 %s%% · 日均换手 %s%%"
          % (V["ann_vol_pct"], V["max_drawdown_pct"], V["avg_amplitude_pct"], V["avg_turnover_pct"]))
    if bt:
        print("   beta(%s) %s · corr %s" % (bt["bench"], bt["beta"], bt["corr"]))
    if gaps:
        print("\n⚠️ gaps:")
        for g in gaps:
            print("   -", g)


if __name__ == "__main__":
    main()
