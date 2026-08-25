#!/usr/bin/env python3
"""
type_card.py — 概览「公司类型卡」数据层（references/10 §2.8 · 2026-08-17 石英股份读者反馈固化）

读者原话：「需要添加公司的类型：真beta、假beta、sigma、叙事-题材股；然后根据不同的类型给到最核心的参数：
beta 类给最核心的叙事题材(一个或几个)+定位(龙头、中军、后排)+当前交易的位置(左侧、右侧突破、回踩与否、
5/10/20 日线排列)；sigma 类给预期利润率和 ROE 在历史的什么分位，外加 PE、PS、PB 在历史的什么分位。」

这些数在 page_model 里几乎都算完了（1.7 篮子 β/R²/分层/方位、1.3 杜邦、1.4 费率、1.5 一致预期、2.1b 估值序列），
只是散在四章里、没有在开篇合成一张卡。本脚本把它们**确定性地**合成 summary.type_card 的数字层；
`type`（真β/假β/σ/叙事-题材）由作者最终定（脚本给 suggest + basis），因为它要与开篇「股性」块的 beta_kind 钩子说同一句话。

用法:
  python3 scripts/type_card.py --model _workspace/<ticker>/page_model.json [--profile _workspace/<ticker>/stock_profile.json] [--write]
  不带 --write 只打印；带 --write 写回 page_model.summary.type_card（保留已填的 type/verdict）。
"""
import argparse, json, sys, statistics


def num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def pct_rank(hist, v):
    """v 在 hist 里的分位（0–100，≤v 的占比）；样本 <4 或 v 缺失返回 None"""
    xs = [num(h) for h in (hist or []) if num(h) is not None]
    if v is None or len(xs) < 4:
        return None
    return round(100.0 * sum(1 for x in xs if x <= v) / len(xs))


def build(model, profile=None):
    p1 = model.get('part1') or {}
    p2 = model.get('part2') or {}
    meta = model.get('meta') or {}
    prof = profile or {}
    out = {'asof': meta.get('asof'), 'src': 'scripts/type_card.py', 'gaps': []}

    # ---------- β 面：叙事/题材篮子 + 定位 + 方位（1.7 已算） ----------
    nc = p1.get('narrative_capacity') or {}
    lines, posture, best = [], None, None
    for b in nc.get('baskets') or []:
        disp = b.get('disp') or {}
        me = next((q for q in (b.get('peers') or []) if q.get('is_self')), None)
        s = b.get('self') or {}
        turn = b.get('turnover') or {}
        line = {
            'name': b.get('name'), 'kind': b.get('kind'), 'n': b.get('n'),
            'beta': num(disp.get('beta_self')), 'r2': num(disp.get('r2_self')),
            'cum_self': num((me or {}).get('cum')), 'cum_med': num(disp.get('cum_med')),
            'tier': (me or {}).get('tier'), 'tier_basis': (me or {}).get('tier_basis'),
            'share_pct': num(s.get('share_pct')), 'rank': s.get('rank'), 'of': s.get('of'),
            'turnover_pct': num(turn.get('pct')), 'float_yi': num(b.get('float_yi')),
        }
        lines.append(line)
        if line['r2'] is not None and (best is None or line['r2'] > best['r2']):
            best = line
        if me and not posture and me.get('posture'):
            ma = me.get('ma') or []
            posture = {'label': me.get('posture'), 'why': me.get('posture_why'),
                       'ma': {'ma5': num(ma[0]) if len(ma) > 0 else None, 'ma10': num(ma[1]) if len(ma) > 1 else None,
                              'ma20': num(ma[2]) if len(ma) > 2 else None, 'ma60': num(ma[3]) if len(ma) > 3 else None},
                       'caliber': '日线 MA5/10/20/60，口径同 kline-reviewer（1.7 tiering.py）'}
    lines.sort(key=lambda x: (-(x['r2'] or -1), -(x['turnover_pct'] or -1)))
    if not lines:
        out['gaps'].append('无 part1.narrative_capacity（港美股或未跑 1.7）→ β 面只能给 stock_profile 的宽基 β/相关性')

    # 方位退化：没有 1.7 的日线方位就用周线 MA 排列，口径写明
    if not posture:
        wk = p2.get('weekly') or []
        closes = [num(w.get('c')) for w in wk if num(w.get('c')) is not None]
        if len(closes) >= 60:
            ma = lambda n: sum(closes[-n:]) / n
            m5, m10, m20, m60 = ma(5), ma(10), ma(20), ma(60)
            m20_prev = sum(closes[-24:-4]) / 20
            c = closes[-1]
            arr = '多头排列' if m5 > m10 > m20 else ('空头排列' if m5 < m10 < m20 else '均线粘合/交叉')
            side = '右侧（站上 20 周线且 20 周线走平向上）' if (c > m20 and m20 >= m20_prev) else '左侧（20 周线之下或仍向下）'
            posture = {'label': arr + ' · ' + side + (' · 站上季线' if c > m60 else ' · 未站上季线'),
                       'why': '周线口径退化：1.7 未给日线方位', 'ma': {'ma5': round(m5, 2), 'ma10': round(m10, 2), 'ma20': round(m20, 2), 'ma60': round(m60, 2)},
                       'caliber': '周线 MA5/10/20/60（退化口径，非日线）'}
        else:
            out['gaps'].append('K 线不足 60 周，方位无法判定')

    beta_face = {'lines': lines[:6], 'best': best, 'posture': posture,
                 'bench': {'beta': num(((prof.get('beta') or {}).get('beta'))), 'corr': num(((prof.get('beta') or {}).get('corr'))),
                           'bench': (prof.get('beta') or {}).get('bench')}}

    # ---------- σ 面：预期利润率 / ROE 历史分位 + PE/PS/PB 分位 ----------
    dp = p1.get('dupont') or {}
    cs = p1.get('cost_structure') or {}
    roe_hist = dp.get('roe') or []
    nm_hist = cs.get('net_margin') or dp.get('net_margin') or []
    yrs = dp.get('years') or cs.get('years') or []
    roe_now = num(roe_hist[-1]) if roe_hist else None
    nm_now = num(nm_hist[-1]) if nm_hist else None
    snap = p1.get('snapshot') or {}
    ttm = snap.get('ttm') or {}
    nm_ttm = None
    if num(ttm.get('rev')) and num(ttm.get('np')) is not None:
        nm_ttm = round(100.0 * num(ttm['np']) / num(ttm['rev']), 2)
    # 预期利润率：1.5 一致预期最近一个未来财年 np/rev（市场预期口径）
    nm_fwd, fwd_lbl = None, None
    for y in (p1.get('consensus') or {}).get('years') or []:
        if y.get('is_future'):
            r, n = (y.get('rev') or {}).get('avg'), (y.get('np') or {}).get('avg')
            if num(r) and num(n) is not None:
                nm_fwd, fwd_lbl = round(100.0 * num(n) / num(r), 2), y.get('label')
                break
    sigma = {
        'nm': {'now': nm_now, 'ttm': nm_ttm, 'fwd': nm_fwd, 'fwd_label': fwd_lbl,
               'pct_now': pct_rank(nm_hist, nm_now), 'pct_ttm': pct_rank(nm_hist, nm_ttm), 'pct_fwd': pct_rank(nm_hist, nm_fwd),
               'hist_years': f"{yrs[0]}–{yrs[-1]}" if len(yrs) >= 2 else None, 'hist_min': min([x for x in map(num, nm_hist) if x is not None], default=None),
               'hist_max': max([x for x in map(num, nm_hist) if x is not None], default=None)},
        'roe': {'now': roe_now, 'pct': pct_rank(roe_hist, roe_now), 'hist_years': f"{yrs[0]}–{yrs[-1]}" if len(yrs) >= 2 else None,
                'hist_min': min([x for x in map(num, roe_hist) if x is not None], default=None),
                'hist_max': max([x for x in map(num, roe_hist) if x is not None], default=None)},
    }
    fp = p2.get('fwd_pe') or {}
    ser = fp.get('series') or []
    for k, lbl in (('pe', 'Forward PE(NTM)'), ('ps', 'PS(trailing)'), ('pb', 'PB')):
        vals = [num(s.get(k)) for s in ser if num(s.get(k)) is not None]
        now = vals[-1] if vals else None
        sigma[k] = {'now': now, 'pct': pct_rank(vals, now), 'n': len(vals), 'label': lbl,
                    'window': (fp.get('window') or [ser[0].get('d') if ser else None, ser[-1].get('d') if ser else None])}
    if not ser:
        out['gaps'].append('无 part2.fwd_pe.series → PE/PS/PB 分位不可得（港美股可用 pe_history）')
    if len([x for x in map(num, roe_hist) if x is not None]) < 4:
        out['gaps'].append('杜邦历史 <4 年，ROE 分位不可得')

    # ---------- 建议类型（作者最终定 type，要与开篇股性 beta_kind 说同一句话） ----------
    r2 = best['r2'] if best else None
    corr = beta_face['bench']['corr']
    ups = ((prof.get('limit') or {}).get('up'))
    hot = [l for l in lines if (l['turnover_pct'] or 0) >= 70]
    if r2 is not None and r2 >= 0.30:
        sug, why = '真β', f"对「{best['name']}」篮子 β {best['beta']}、R² {r2}（篮子解释了约 {round(r2*100)}% 方差{'，另一半是 σ' if r2 < 0.5 else ''}）"
    elif lines and ((ups or 0) >= 10 or hot):
        sug, why = '叙事-题材', f"篮子解释度低（最高 R² {r2}）但题材热度高：近 3 年涨停 {ups} 次、换手强度 ≥70 分位的篮子 {len(hot)} 条"
    elif lines:
        sug, why = '假β', f"挂着 {len(lines)} 条篮子标签，但最高 R² 只有 {r2}（β {best['beta'] if best else None}），钱没顺着这些线走"
    else:
        sug, why = 'σ', f"无叙事篮子可挂；对宽基相关性 {corr}"
    if corr is not None and corr < 0.4 and (r2 is None or r2 < 0.3):
        why += f"；对沪深300 相关性 {corr}，指数对冲不掉"
    out.update({'suggest': sug, 'basis': why, 'beta': beta_face, 'sigma': sigma})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--profile')
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    model = json.load(open(a.model, encoding='utf-8'))
    prof = json.load(open(a.profile, encoding='utf-8')) if a.profile else None
    card = build(model, prof)
    prev = ((model.get('summary') or {}).get('type_card') or {})
    for k in ('type', 'verdict', 'core_lines'):          # 作者手填项保留
        if prev.get(k) is not None:
            card[k] = prev[k]
    print(json.dumps({k: card[k] for k in ('suggest', 'basis', 'gaps')}, ensure_ascii=False, indent=1))
    b = card['beta']
    if b.get('best'):
        print(f"β 面：最像的线 {b['best']['name']} β {b['best']['beta']} R² {b['best']['r2']} tier {b['best']['tier']}；方位 {(b.get('posture') or {}).get('label')}")
    s = card['sigma']
    print(f"σ 面：净利率 now {s['nm']['now']}%(分位 {s['nm']['pct_now']}) fwd {s['nm']['fwd']}%(分位 {s['nm']['pct_fwd']})；ROE {s['roe']['now']}%(分位 {s['roe']['pct']})；"
          f"PE {s['pe']['now']}(分位 {s['pe']['pct']}) PS {s['ps']['now']}(分位 {s['ps']['pct']}) PB {s['pb']['now']}(分位 {s['pb']['pct']})")
    if a.write:
        model.setdefault('summary', {})['type_card'] = card
        json.dump(model, open(a.model, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f"→ 已写回 {a.model} summary.type_card（type={card.get('type') or '⚠️ 未定，作者按 10 §2.8 填'}）")


if __name__ == '__main__':
    main()
