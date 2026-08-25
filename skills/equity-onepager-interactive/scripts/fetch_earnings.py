#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fetch_earnings.py — 拉「业绩预告 + 定期报告」的**实际披露日期**，供 2.1 K线图标注时间节点。

为什么必须单独拉：催化清单里的 G1(数据高增长) 只收录了「涨跌显著」的那些财报，
而读图的人需要看到**全部**披露日——包括那些当周没怎么动的，因为「利好不涨」本身是信号
（002371 阶段①就是典型：业绩连续超预期而股价 −31%）。

数据源：AKShare 东财
  · 定期报告披露日 = stock_yjbb_em(date=报告期).最新公告日期
  · 业绩预告日     = stock_yjyg_em(date=报告期).公告日期     （只有部分报告期有）
两者都按报告期逐期拉，失败的期自动跳过并在 gaps 里列出（不编造日期）。

用法:
  python scripts/fetch_earnings.py --ticker 002371 --start 2023-06-01 --end 2026-07-31 \
      --out _workspace/002371/earnings.json
产物直接进 page_model.part2.earnings（契约见 SKILL.md / references/03 §4f）。
"""
import argparse, json, sys, datetime as dt

TYPE_BY_MMDD = {'0331': '一季报', '0630': '中报', '0930': '三季报', '1231': '年报'}
SHORT = {'业绩预告': '预', '一季报': 'Q1', '中报': 'H1', '三季报': 'Q3', '年报': '年'}


def periods(start, end):
    """窗口内所有报告期(YYYYMMDD)。多往前取一期——年报在次年 4 月才披露。"""
    y0, y1 = start.year - 1, end.year
    out = []
    for y in range(y0, y1 + 1):
        for md in ('0331', '0630', '0930', '1231'):
            out.append('%d%s' % (y, md))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ticker', required=True, help='裸代码，如 002371')
    ap.add_argument('--start', required=True)
    ap.add_argument('--end', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--with-forecast', action='store_true', help='additionally pull 业绩预告(耗时翻倍)')
    a = ap.parse_args()
    d0 = dt.date.fromisoformat(a.start)
    d1 = dt.date.fromisoformat(a.end)
    code = a.ticker.split('.')[0].zfill(6)

    try:
        import akshare as ak
    except ImportError:
        print('!! 需要 akshare: pip install akshare', file=sys.stderr); sys.exit(2)
    import warnings; warnings.filterwarnings('ignore')

    rows, gaps = [], []

    def norm(x):
        if x is None: return None
        s = str(x)[:10].replace('/', '-')
        try:
            dt.date.fromisoformat(s); return s
        except ValueError:
            return None

    for pd_ in periods(d0, d1):
        ptype = TYPE_BY_MMDD[pd_[4:]]
        # ---- 定期报告实际披露日 ----
        try:
            df = ak.stock_yjbb_em(date=pd_)
            hit = df[df['股票代码'].astype(str).str.zfill(6) == code]
            if len(hit):
                r = hit.iloc[0]
                dte = norm(r.get('最新公告日期'))
                if dte and d0.isoformat() <= dte <= d1.isoformat():
                    yoy = r.get('净利润-同比增长')
                    rows.append(dict(date=dte, period=pd_, type=ptype, short=SHORT[ptype],
                                     np_yoy=(None if yoy is None or str(yoy) == 'nan' else round(float(yoy), 1)),
                                     src='akshare stock_yjbb_em'))
            else:
                gaps.append(pd_ + ' 定期报告未命中该股')
        except Exception as e:
            gaps.append('%s 定期报告拉取失败: %s' % (pd_, type(e).__name__))
        # ---- 业绩预告（可选，耗时翻倍）----
        if not a.with_forecast:
            continue
        try:
            df = ak.stock_yjyg_em(date=pd_)
            hit = df[df['股票代码'].astype(str).str.zfill(6) == code]
            if len(hit):
                r = hit.iloc[0]
                dte = norm(r.get('公告日期'))
                if dte and d0.isoformat() <= dte <= d1.isoformat():
                    rows.append(dict(date=dte, period=pd_, type='业绩预告', short='预',
                                     note=str(r.get('预测指标') or r.get('业绩变动') or '')[:40],
                                     src='akshare stock_yjyg_em'))
        except Exception:
            pass          # 预告很多期本就没有，不算缺口

    # 去重 + 排序
    seen, uniq = set(), []
    for r in sorted(rows, key=lambda x: (x['date'], x['type'])):
        k = (r['date'], r['type'])
        if k in seen: continue
        seen.add(k); uniq.append(r)

    json.dump({'ticker': code, 'window': [a.start, a.end], 'earnings': uniq, 'gaps': gaps},
              open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('拉到 %d 条披露节点 → %s' % (len(uniq), a.out))
    for r in uniq:
        print('  %s  %-6s %s' % (r['date'], r['type'],
              ('归母同比 %+.1f%%' % r['np_yoy']) if r.get('np_yoy') is not None else (r.get('note') or '')))
    if gaps:
        print('\n缺口（不编造，页面按缺失处理）:')
        for g in gaps[:8]: print('  ·', g)


if __name__ == '__main__':
    main()
