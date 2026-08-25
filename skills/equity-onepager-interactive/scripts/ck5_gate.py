#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ck5_gate.py — 矛盾定型闸门 CK-5e 的两个指标 + 数据体检
（配套 references/09-contradiction-map.md · 旧注释指向的 09-contradiction-typology.md
  从未存在；矛盾分型现在在 references/13-contradiction-typology.md）

指标1  V主导阶段涨跌幅占比 = Σ|chg| where main_factor含V ÷ Σ|chg|
       三档: <50% 轴A主导 | 50-80% 双轴并重 | >=80% 轴B主导（阈值由案例库自然断点校准）
指标2  现价在静态范式区间中的分位 = (现市值-min腿)/(max腿-min腿)
       >100% = 现价越出全部可比范式锚上沿 → V4 强制判「切换中」+ 强制画跨轴bar

只读 page_model.json，不依赖 P&L 引擎（静态腿公式镜像 model_engine.js 的 PARADIGM，
link=true 的 pe/peg/evebitda 腿需要 Forward 利润，本脚本不算，由 tornado.js 负责）。

用法:
  python ck5_gate.py                      # 扫 _workspace/ 下全部案例 + 打印库分布
  python ck5_gate.py --ticker 002371      # 单标的
  python ck5_gate.py --root <dir> --json  # 机读
"""
import argparse, json, os, statistics as st, sys

STATIC_LEGS = ('sotp', 'leader', 'endgame', 'pbroe')
BANDS = ((50.0, '轴A主导'), (80.0, '双轴并重'), (float('inf'), '轴B主导'))


def clamp(x, a, b):
    return max(a, min(b, x))


def static_leg(key, p):
    """静态范式腿隐含市值(亿)。公式镜像 model_engine.js PARADIGM，不依赖 P&L。"""
    n = lambda k, d=0.0: float(p.get(k, d) or 0)
    try:
        if key == 'sotp':
            return sum(float(s.get('profit_yi', 0) or 0) * float(s.get('mult', 0) or 0)
                       for s in (p.get('segments') or [])) + n('net_cash_yi')
        if key == 'leader':
            lc, lm, fs = n('leader_current'), n('leader_mcap'), n('follower_steady')
            if lc <= 0:
                return None
            return (fs / lc) * lm * clamp(1 + n('adj'), 0.70, 1.30) / (1 + n('r', 0.12)) ** n('n')
        if key == 'endgame':
            return n('tam_yi') * n('share') * n('net_margin') * n('pe', 22) / (1 + n('r', 0.12)) ** n('n')
        if key == 'pbroe':
            coe = n('coe', 0.10)
            return n('equity_yi') * (n('roe') / coe) if coe else None
    except Exception:
        return None
    return None


def phase_chg(ph, weekly):
    """阶段涨跌幅绝对值；chg 缺失时从 weekly 收盘按 startIdx/endIdx 重算。"""
    v = ph.get('chg')
    if v not in (None, ''):
        try:
            return abs(float(str(v).replace('%', '').replace('+', ''))), False
        except ValueError:
            pass
    si, ei = ph.get('startIdx'), ph.get('endIdx')
    if weekly and si is not None and ei is not None and 0 <= si < len(weekly) and 0 <= ei < len(weekly):
        c0, c1 = weekly[si].get('c'), weekly[ei].get('c')
        if c0:
            return abs((c1 / c0 - 1) * 100), True
    return 0.0, True


def band_of(v_share):
    for hi, label in BANDS:
        if v_share < hi:
            return label
    return BANDS[-1][1]


def assess(path):
    d = json.load(open(path, encoding='utf-8'))
    meta, p2, p3 = d.get('meta', {}), d.get('part2', {}), d.get('part3', {})
    phases, cats, weekly = p2.get('phases') or [], p2.get('catalysts') or [], p2.get('weekly') or []
    issues = []

    # ---- 指标1 ----------------------------------------------------------------
    tot = vw = 0.0
    recomputed = 0
    for ph in phases:
        c, was_null = phase_chg(ph, weekly)
        tot += c
        recomputed += int(was_null)
        if 'V' in str(ph.get('main_factor') or ''):
            vw += c
    v_share = (vw / tot * 100) if tot else None
    if recomputed:
        issues.append('phases[].chg 有 %d 段缺失→已从 weekly 收盘重算（建议回填）' % recomputed)
    if not phases:
        issues.append('无 phases，指标1 不可算')
    for i, ph in enumerate(phases):
        if not ph.get('core_conflict'):
            issues.append('phases[%d] 缺 core_conflict（CK-5e 要求双侧标码）' % i)
        if not ph.get('main_factor'):
            issues.append('phases[%d] 缺 main_factor' % i)

    # dims 键名体检（前导点会让层级归因错标）
    bad_keys = set()
    for c in cats:
        for k in (c.get('dims') or {}):
            if k != k.lstrip('.'):
                bad_keys.add(k)
    if bad_keys:
        issues.append('catalysts[].dims 键带前导点 %s → app.js 层级归因会错标' % sorted(bad_keys))

    # ---- 指标2 ----------------------------------------------------------------
    val = p3.get('valuation') or {}
    cur = float(val.get('current_mcap_yi') or 0)
    legs, skipped = {}, []
    for pg in (val.get('paradigms') or []):
        k = pg.get('key')
        w = float(pg.get('weight') or 0)
        if k in STATIC_LEGS and w > 0:
            m = static_leg(k, pg.get('params') or {})
            if m and m > 0:
                legs[k] = m
            else:
                issues.append('静态腿 %s 参数不全，无法算隐含市值' % k)
        elif w > 0 and k in ('pe', 'peg', 'evebitda'):
            skipped.append(k)

    pos = spread = lo = hi = None
    if cur and len(legs) >= 2:
        lo, hi = min(legs.values()), max(legs.values())
        pos = (cur - lo) / (hi - lo) * 100
        spread = hi / lo
    elif cur:
        issues.append('可算静态腿 <2（%s），指标2 不可算；link腿 %s 需 tornado.js' % (list(legs), skipped or '无'))

    # ---- 范式敞口：低权重腿是否被稀释 ----------------------------------------
    exposure = []
    if legs:
        wsum = sum(float(pg.get('weight') or 0) for pg in (val.get('paradigms') or [])
                   if pg.get('key') in legs)
        blend = (sum(float(pg.get('weight') or 0) * legs[pg['key']]
                     for pg in (val.get('paradigms') or []) if pg.get('key') in legs) / wsum) if wsum else 0
        for pg in (val.get('paradigms') or []):
            k, w = pg.get('key'), float(pg.get('weight') or 0)
            if k in legs and 0 < w <= 0.1 and blend and abs(legs[k] - blend) / blend > 0.40:
                exposure.append('%s 权重%.2f 但隐含市值 %.0f亿 偏离加权 %.0f亿 达 %+.0f%% → 须单列范式敞口，不许混进加权'
                                % (k, w, legs[k], blend, (legs[k] / blend - 1) * 100))

    verdicts = []
    if v_share is not None:
        b = band_of(v_share)
        verdicts.append('指标1: V主导涨幅占比 %.0f%% → %s' % (v_share, b))
        if b == '轴B主导':
            verdicts.append('  ⚠️ 打警示「本标的主要由定价环境驱动」；轴A深度预算下调，改配轴B跟踪')
        elif b == '双轴并重':
            verdicts.append('  · 页面必须并列轴B状态带')
    if pos is not None:
        verdicts.append('指标2: 现价分位 %.0f%%（静态范式区间 %.0f–%.0f亿，跨度 %.1fx）' % (pos, lo, hi, spread))
        if pos > 100:
            verdicts.append('  ⚠️ 现价越出全部可比范式锚上沿 → V4 强制判「切换中」+ 强制画跨轴bar（要么漏了腿，要么市场换了范式）')

    return dict(ticker=os.path.basename(os.path.dirname(path)), name=meta.get('name', ''),
                v_share=v_share, band=band_of(v_share) if v_share is not None else None,
                cur_mcap=cur, legs=legs, lo=lo, hi=hi, pos=pos, spread=spread,
                verdicts=verdicts, exposure=exposure, issues=issues)


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--root', default=os.path.join(os.path.dirname(here), '_workspace'))
    ap.add_argument('--ticker')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    tickers = [a.ticker] if a.ticker else sorted(
        t for t in os.listdir(a.root) if os.path.exists(os.path.join(a.root, t, 'page_model.json')))
    out = []
    for t in tickers:
        f = os.path.join(a.root, t, 'page_model.json')
        if not os.path.exists(f):
            print('!! %s 无 page_model.json' % t, file=sys.stderr)
            continue
        out.append(assess(f))

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    for r in out:
        print('=' * 74)
        print('%s %s   现市值 %.0f亿' % (r['ticker'], r['name'], r['cur_mcap']))
        for v in r['verdicts']:
            print('  ' + v)
        for e in r['exposure']:
            print('  ⚠️ 范式敞口: ' + e)
        if r['issues']:
            print('  -- 数据体检 --')
            for i in r['issues']:
                print('     · ' + i)

    vs = [r['v_share'] for r in out if r['v_share'] is not None]
    ps = [r['pos'] for r in out if r['pos'] is not None]
    if len(out) > 1 and vs:
        print('\n' + '=' * 74)
        print('案例库分布 n=%d（阈值应随库重算）' % len(out))
        print('  V主导涨幅占比: 中位 %.0f%%  区间 %.0f–%.0f%%' % (st.median(vs), min(vs), max(vs)))
        cnt = {}
        for r in out:
            if r['band']:
                cnt[r['band']] = cnt.get(r['band'], 0) + 1
        print('  三档分布: %s' % cnt)
        if ps:
            print('  现价分位: 中位 %.0f%%  区间 %.0f–%.0f%%  越顶(>100%%) %d 个'
                  % (st.median(ps), min(ps), max(ps), sum(1 for x in ps if x > 100)))


if __name__ == '__main__':
    main()
