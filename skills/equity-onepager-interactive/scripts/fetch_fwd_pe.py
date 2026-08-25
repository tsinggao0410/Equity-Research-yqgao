#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_fwd_pe.py — ★2.1b Forward PE 带：由「逐份带日期的券商研报」自底向上重建时点一致预期（2026-08-12）

为什么要这个脚本（取代页面端用 FMP 财年快照合成）：
  1. FMP analyst-estimates 每财年只存一份≈财报前的最终一致预期 → 整年铺平线，早期日期用了当时
     不存在的数字（前视偏差），且合成区间/负利润期直接断线——用户打回：「肯定要历史的预测」。
  2. 东财研报原始接口 reportapi.eastmoney.com 每份研报带 publishDate + predictThisYearEps /
     predictNextYearEps / predictNextTwoYearEps（相对报告日的 本年/次年/后年 EPS 预测）——
     这就是逐份带时间戳的历史预测，可严格重建「当时市场看到的下一年 EPS」。
     ⚠️ 勿用 akshare stock_research_report_em：它把这些相对年字段错标成固定年份列（2026/2027/2028），
     老研报的 FY1 会整列丢失（实测 603766：43 份老报告只剩 14% 有值）。

口径（连续性两招）：
  a) 时点一致预期：对每个周五 t，取窗口 [t−lookback, t] 内每家券商**最新**一份研报，
     对各自然年 Y 取跨券商中位数 med(Y)、覆盖家数 n(Y)。研报未撤销前在窗口内持续有效 → 有覆盖处天然连续。
  b) NTM 混合消除财年换挡跳变：NTM_EPS(t) = w×med(Y_t) + (1−w)×med(Y_t+1)，w=当年剩余天数/365。
     forward+1 同理右移一年（Y_t+1 / Y_t+2）。次年预测缺失时退化为纯 FY1（series[].basis='fy1_only'）。
  Forward PE(t) = 周收盘 ÷ NTM_EPS(t)（EPS≤0 → pe=null）。零覆盖周 = 真实无卖方覆盖。
  c) ★负利润/无覆盖不留白（2026-08-12 用户追加：「负利润改成 PS 或者 PB 估值」）：
     每周同步算 trailing PS 与 PB —— akshare stock_financial_abstract 按报告期取
     营业总收入(YTD→TTM=本期YTD+上年年报−上年同期YTD)、每股净资产、净资产(反推期末股本)；
     报告期→可见日用法定披露截止（1231→次年04-30 / 0331→04-30 / 0630→08-31 / 0930→10-31，
     传 --earnings <earnings.json> 则用真实公告日，无前视）。PS=收盘×期末股本÷TTM营收、PB=收盘÷每股净资产。
     pe=null 的周（pe_gap='loss' 或 'no_coverage'）页面画替代线（左轴，cfg.loss_metric 选 ps|pb，默认 ps）。

市场覆盖：A 股（主源 eastmoney reportapi）。港美股该接口无券商 EPS 数据 → 退出并提示走页面端
FMP 财年近似（页面会标「近似口径」）+ 手工 anchors；后续可接 FMP price-target 逐日 TP 流。

用法：
  python3 scripts/fetch_fwd_pe.py --ticker 603766 --market A \
      --kline _workspace/<ticker>/kline_weekly.json \
      --out _workspace/<ticker>/fwd_pe.json [--lookback 180] [--min-brokers 3]
产物整份塞进 page_model.part2.fwd_pe（手工 anchors 合并在同一对象里，勿覆盖 series）。
"""
import argparse, json, math, sys, time, datetime as dt
import urllib.request, urllib.parse

API = "https://reportapi.eastmoney.com/report/list"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def http_json(url, params, retries=3):
    qs = urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            req = urllib.request.Request(url + "?" + qs, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def fnum(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def fetch_reports(code, begin, end):
    """拉 [begin,end] 全部个股研报（qType=0），返回 [{date,org,y0,eps:{Y:v}}]；分页 + 按年分块防截断。"""
    out, seen = [], set()
    b = dt.date.fromisoformat(begin)
    while b <= dt.date.fromisoformat(end):
        e = min(b.replace(year=b.year + 2), dt.date.fromisoformat(end))
        page = 1
        while True:
            d = http_json(API, dict(pageSize=100, pageNo=page, qType=0, code=code,
                                    beginTime=str(b), endTime=str(e), industryCode="*",
                                    industry="*", rating="", ratingChange="", fields="", orgCode=""))
            rows = d.get("data") or []
            for r in rows:
                pd = str(r.get("publishDate") or "")[:10]
                org = (r.get("orgSName") or r.get("orgName") or "").strip()
                if not pd or not org:
                    continue
                key = (pd, org, r.get("title"))
                if key in seen:
                    continue
                seen.add(key)
                y0 = int(pd[:4])
                eps = {}
                for off, fld in ((0, "predictThisYearEps"), (1, "predictNextYearEps"), (2, "predictNextTwoYearEps")):
                    v = fnum(r.get(fld))
                    if v is not None and -50 < v < 500:      # 粗 sanity（分红股 EPS 不会到三位数）
                        eps[y0 + off] = v
                if eps:
                    out.append(dict(date=pd, org=org, y0=y0, eps=eps, title=r.get("title") or ""))
            total = int(d.get("hits") or 0)
            if page * 100 >= total or not rows:
                break
            page += 1
        b = e + dt.timedelta(days=1)
    out.sort(key=lambda r: r["date"])
    return out


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


STATUTORY = {"0331": "-04-30", "0630": "-08-31", "0930": "-10-31", "1231": "+04-30"}  # 1231 → 次年


def fetch_fundamentals(code, earnings_path=None):
    """按报告期取 TTM营收/每股净资产/期末股本 → [(可见日, {ttm_rev, bps, shares})] 升序。
    可见日=真实公告日(--earnings)或法定披露截止日（保证无前视）。取数失败返回 []（PS/PB 腿静默降级）。"""
    try:
        import warnings; warnings.filterwarnings("ignore")
        import akshare as ak
        df = ak.stock_financial_abstract(symbol=code)
    except Exception as e:
        print(f"⚠️ PS/PB 腿取数失败（stock_financial_abstract: {e}），仅出 PE。", file=sys.stderr)
        return []
    rows = {}
    for name in ("营业总收入", "每股净资产", "股东权益合计(净资产)"):
        sub = df[df["指标"] == name]
        if not len(sub):
            continue
        r = sub.iloc[0]
        for c in df.columns:
            cs = str(c)
            if cs[:4].isdigit() and len(cs) == 8:
                v = fnum(r[c])
                if v is not None:
                    rows.setdefault(cs, {})[name] = v
    ann = {}
    if earnings_path:
        try:
            ej = json.load(open(earnings_path, encoding="utf-8"))
            for e in (ej.get("earnings") or ej or []):
                if e.get("period") and e.get("date") and e.get("type") != "业绩预告":
                    p = str(e["period"]).replace("-", "")[:8]
                    if p not in ann or e["date"] < ann[p]:
                        ann[p] = e["date"]
        except Exception:
            pass

    def visible(p):  # p='20241231' → 真实公告日 or 法定披露截止（1231 归次年）
        if p in ann:
            return ann[p]
        y, md = int(p[:4]), p[4:]
        s = STATUTORY.get(md, "+04-30")
        return f"{y+1}-{s[2:]}" if s[0] == "+" else f"{y}{s}"

    out = []
    periods = sorted(rows)
    for p in periods:
        cur = rows[p]
        ytd = cur.get("营业总收入")
        ttm = None
        if ytd is not None:
            if p.endswith("1231"):
                ttm = ytd
            else:
                py, md = int(p[:4]), p[4:]
                prev_fy = rows.get(f"{py-1}1231", {}).get("营业总收入")
                prev_same = rows.get(f"{py-1}{md}", {}).get("营业总收入")
                if prev_fy is not None and prev_same is not None:
                    ttm = ytd + prev_fy - prev_same
        bps = cur.get("每股净资产")
        eq = cur.get("股东权益合计(净资产)")
        shares = (eq / bps) if (eq and bps) else None
        if ttm or bps:
            out.append((visible(p), dict(period=p, ttm_rev=ttm, bps=bps, shares=shares)))
    out.sort(key=lambda x: x[0])
    return out


def build_series(weekly, reports, lookback, min_brokers, fnd=None):
    """逐周重建：每家取窗口内最新一份 → 各自然年中位数 → NTM 混合；同步给 trailing PS/PB 替代腿。"""
    series, gaps = [], 0
    fnd = fnd or []
    fi = 0
    cur_f = None
    for w in weekly:
        d = w["d"]; close = fnum(w.get("c"))
        t = dt.date.fromisoformat(d)
        lo = str(t - dt.timedelta(days=lookback))
        latest = {}                                   # org -> report（窗口内最新）
        for r in reports:
            if lo <= r["date"] <= d:
                cur = latest.get(r["org"])
                if cur is None or r["date"] >= cur["date"]:
                    latest[r["org"]] = r
        byY = {}
        for r in latest.values():
            for y, v in r["eps"].items():
                byY.setdefault(y, []).append(v)
        Y = t.year
        m1, m2, m3 = median(byY.get(Y, [])), median(byY.get(Y + 1, [])), median(byY.get(Y + 2, []))
        n1 = len(byY.get(Y, []))
        days_left = (dt.date(Y, 12, 31) - t).days
        wgt = max(0.0, min(1.0, days_left / 365.0))
        basis = None
        if m1 is not None and m2 is not None:
            ntm = wgt * m1 + (1 - wgt) * m2; basis = "ntm"
        elif m1 is not None:
            ntm = m1; basis = "fy1_only"
        else:
            ntm = None
        if m2 is not None and m3 is not None:
            f1 = wgt * m2 + (1 - wgt) * m3
        elif m2 is not None:
            f1 = m2
        else:
            f1 = None
        pe = round(close / ntm, 2) if (close and ntm and ntm > 0) else None
        pe1 = round(close / f1, 2) if (close and f1 and f1 > 0) else None
        # ── trailing PS/PB（最新可见报告期，向前滚动指针）──────────────────
        while fi < len(fnd) and fnd[fi][0] <= d:
            cur_f = fnd[fi][1]; fi += 1
        ps = pb = None
        if close and cur_f:
            if cur_f.get("ttm_rev") and cur_f.get("shares") and cur_f["ttm_rev"] > 0:
                ps = round(close * cur_f["shares"] / cur_f["ttm_rev"], 2)
            if cur_f.get("bps") and cur_f["bps"] > 0:
                pb = round(close / cur_f["bps"], 2)
        gap_reason = None
        if pe is None:
            gaps += 1
            gap_reason = "loss" if (ntm is not None and ntm <= 0) else "no_coverage"
        series.append(dict(d=d, close=close, ntm_eps=(round(ntm, 4) if ntm else None),
                           fwd1_eps=(round(f1, 4) if f1 else None), pe=pe, pe1=pe1,
                           ps=ps, pb=pb, pe_gap=gap_reason,
                           n=n1, thin=(0 < n1 < min_brokers), basis=basis))
    return series, gaps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True, help="裸代码，如 603766")
    ap.add_argument("--market", default="A", choices=["A", "HK", "US"])
    ap.add_argument("--kline", required=True, help="fetch_kline.py 产物（周线网格与下标对齐的唯一依据）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lookback", type=int, default=180, help="研报有效窗口（天），窗口内每家取最新")
    ap.add_argument("--min-brokers", type=int, default=3, help="低于此家数标 thin（虚线段）")
    ap.add_argument("--earnings", default=None, help="fetch_earnings.py 产物（真实公告日→PS/PB 可见性；缺省用法定披露截止日）")
    ap.add_argument("--loss-metric", default="ps", choices=["ps", "pb"], help="pe 空档周页面画哪条替代线（左轴）")
    a = ap.parse_args()

    if a.market != "A":
        print("⚠️ 港美股无东财券商研报 EPS 源：本脚本不产 series。页面将回退 FMP 财年近似口径（标「近似」），"
              "卖方锚点走 part2.fwd_pe.anchors 手工取证（03 §4g）。", file=sys.stderr)
        sys.exit(2)

    kl = json.load(open(a.kline, encoding="utf-8"))
    weekly = kl.get("weekly") or kl
    if not weekly or "d" not in weekly[0]:
        sys.exit("kline 文件不含 weekly[{d,o,h,l,c,v}]")
    begin = str(dt.date.fromisoformat(weekly[0]["d"]) - dt.timedelta(days=a.lookback + 30))
    end = weekly[-1]["d"]

    reports = fetch_reports(a.ticker, begin, end)
    fnd = fetch_fundamentals(a.ticker, a.earnings)
    series, gaps = build_series(weekly, reports, a.lookback, a.min_brokers, fnd)
    covered = sum(1 for s in series if s["pe"] is not None)
    sub_n = sum(1 for s in series if s["pe"] is None and s.get(a.loss_metric.replace("-", "_")) is not None)
    orgs = sorted({r["org"] for r in reports})

    out = dict(
        asof=str(dt.date.today()), src="eastmoney reportapi 逐份券商研报（相对年字段）+ 财务摘要(TTM营收/BPS)",
        caliber=("NTM 时点一致预期：每周取窗口内各券商最新研报，按自然年取中位数；"
                 "NTM=w×FY1+(1−w)×FY2（w=当年剩余天数/365，财年换挡无跳变）；EPS≤0 或零覆盖不出 PE，"
                 "改画 trailing PS/PB 替代线（报告期按公告日/法定截止日可见，无前视）"),
        lookback_days=a.lookback, min_brokers=a.min_brokers, loss_metric=a.loss_metric,
        reports_n=len(reports), orgs_n=len(orgs), orgs=orgs, fundamentals_periods=len(fnd),
        window=[weekly[0]["d"], end], weeks=len(series), weeks_covered=covered, weeks_substituted=sub_n,
        report_points=[dict(date=r["date"], org=r["org"], eps=r["eps"]) for r in reports][-200:],
        series=series,
        gaps=([] if covered else ["全窗口零券商覆盖——PE 线缺席是事实不是缺陷"]) +
             ([f"{gaps} 周无 PE（负利润/无覆盖），其中 {sub_n} 周有 {a.loss_metric.upper()} 替代线"] if gaps else []),
        note="anchors[]（卖方目标市值/TP 锚点）由人工 RAG 取证后合并进本对象，勿覆盖 series",
    )
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"研报 {len(reports)} 份 / {len(orgs)} 家机构；{len(series)} 周中 {covered} 周有 Forward PE，"
          f"{gaps} 周无 PE（其中 {sub_n} 周有 {a.loss_metric.upper()} 替代）→ {a.out}")
    if covered and covered < len(series) * 0.5:
        print("⚠️ 覆盖率 <50%：该标的卖方覆盖本来就薄，曲线只在有覆盖区间连续——这是信息不是 bug；"
              "页面会标注覆盖家数。", file=sys.stderr)


if __name__ == "__main__":
    main()
