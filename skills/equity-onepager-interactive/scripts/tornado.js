#!/usr/bin/env node
/* =============================================================================
 * tornado.js — 矛盾力度龙卷风图 + 跨轴「范式敞口」取期轴
 * （配套 references/09-contradiction-map.md §5 赔率 —— 旧注释指向的
 *   09-contradiction-typology.md 从未存在，分型现在在 13-contradiction-typology.md）
 * 下游：产出的下界/上界/传导率进 part4.items[].odds_basis，
 *       并给 4.1 场景的 odds_band 定带宽（09 §5.5d）。
 *
 * 为什么用 node 而不是 python：弹性必须走页面同一套 recomputePL/runValuation，
 * 在别处重写一遍 P&L 一定会和页面对不上。
 *
 * 轴A（参数弹性）：每个 segments[].assume.{q_growth,p_growth,gm} 在**它自己的锚离散
 *   区间**内摆动（q/p 锚=增速、gm 锚=水平值，见 04 §1.15），读 Δ加权市值/现市值。
 *   锚 <2 个时退化为相对区间并**显式标 [FALLBACK]**（不许静默默认）。
 * 跨轴（范式敞口）：对 link:true 的腿沿 forecast_years 扫 year_offset（PE 折现 n 同步），
 *   同一利润路径下读出「取期敞口」——芯原实测 2028E vs 2030E 差 2.2x，
 *   远大于任何单参数弹性。取期敞口 ≠ 范式风险，也 ≠ 利润预测分歧（后者要对卖方口径另列）。
 *
 * 用法:
 *   node tornado.js --model _workspace/002371/page_model.json
 *   node tornado.js --model ... --json
 *   node tornado.js --model ... --fallback-rel 0.3    # 无锚时的相对摆幅(默认0.3)
 * ========================================================================== */
'use strict';
const fs = require('fs');
const path = require('path');
const EONE = require(path.join(__dirname, 'model_engine.js'));

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i > 0 && process.argv[i + 1] && !process.argv[i + 1].startsWith('--') ? process.argv[i + 1] : def;
}
const HAS = (name) => process.argv.indexOf('--' + name) > 0;

const modelPath = arg('model');
if (!modelPath) { console.error('usage: node tornado.js --model <page_model.json> [--json]'); process.exit(2); }
const FALLBACK_REL = parseFloat(arg('fallback-rel', '0.3'));

const pm = JSON.parse(fs.readFileSync(modelPath, 'utf8'));
const p3 = pm.part3 || {};
const clone = (o) => JSON.parse(JSON.stringify(o));
const fmt = (x) => (Math.abs(x) >= 100 ? Math.round(x) : Math.round(x * 10) / 10).toLocaleString();
const pct = (x) => (x * 100 >= 0 ? '+' : '') + (x * 100).toFixed(1) + '%';

function blendOf(part3) {
  const pl = EONE.recomputePL(part3);
  const v = EONE.runValuation(part3.valuation || {}, pl);
  return { mcap: v.blend.mcap, pl, val: v };
}

const base = blendOf(p3);
const CUR = Number((p3.valuation || {}).current_mcap_yi) || 0;

/* ---- 弹性传导率：只有 link:true 的腿会跟着参数动 -------------------------
 * 05 §9.5 的 relinkAll 是页面 JS 层手工接线（sotp/leader/endgame 的 profit_yi /
 * net_margin 写回），引擎的 runValuation 不做。所以直接扰动参数时，静态腿被冻结，
 * 轴A弹性被按 link腿权重占比 系统性低估。此处显式披露传导率，bar 同时给下界与上界。 */
const _pds = ((p3.valuation || {}).paradigms || []).filter(p => !(p.params || {}).diagnostic && Number(p.weight) > 0);
const _wsum = _pds.reduce((a, p) => a + Number(p.weight || 0), 0);
const _wlink = _pds.filter(p => (p.params || {}).link === true).reduce((a, p) => a + Number(p.weight || 0), 0);
const TRANSMIT = _wsum ? _wlink / _wsum : 1;
const FROZEN = _pds.filter(p => (p.params || {}).link !== true).map(p => p.key + '(' + p.weight + ')');
const SHARES = Number((p3.valuation || {}).shares_yi || p3.shares_yi) || 0;
const F = (p3.forecast_years || []).length;
const warn = [];
if (!CUR) warn.push('part3.valuation.current_mcap_yi 缺失，bar 无法归一到 %现市值');
if (!F) warn.push('forecast_years 为空，取期轴不可算');

/* ---------- 轴A：参数弹性 bar --------------------------------------------- */
const FIELDS = [
  { field: 'q_growth', anchors: 'q_anchors', label: '量增速', kind: 'growth' },
  { field: 'p_growth', anchors: 'p_anchors', label: '价增速', kind: 'growth' },
  { field: 'gm', anchors: 'gm_anchors', label: '毛利率', kind: 'level' }
];

function rangeFromAnchors(list, cur, kind) {
  const vs = (list || []).map(a => Number(a && a.v)).filter(v => isFinite(v));
  const uniq = Array.from(new Set(vs));
  if (uniq.length >= 2) {
    return { lo: Math.min(...uniq), hi: Math.max(...uniq), src: 'anchors(' + uniq.length + ')', fallback: false };
  }
  // 无足够锚 → 相对摆幅，显式标记
  const c = isFinite(cur) ? cur : (kind === 'level' ? 0.3 : 0.1);
  const half = Math.abs(c) > 1e-9 ? Math.abs(c) * FALLBACK_REL : (kind === 'level' ? 0.05 : 0.05);
  return { lo: c - half, hi: c + half, src: 'FALLBACK ±' + (FALLBACK_REL * 100).toFixed(0) + '%', fallback: true };
}

const bars = [];
(p3.segments || []).forEach((seg, si) => {
  const model = seg.model || {};
  const assume = seg.assume || {};
  FIELDS.forEach(f => {
    const curArr = assume[f.field];
    if (curArr === undefined && f.field !== 'gm') return;      // 该段没有这个驱动
    const curVal = Array.isArray(curArr) ? Number(curArr[0]) : Number(curArr);
    const r = rangeFromAnchors(model[f.anchors], curVal, f.kind);
    if (!isFinite(r.lo) || !isFinite(r.hi) || r.hi - r.lo < 1e-9) return;

    const mk = (v) => { const c = clone(p3); (c.segments[si].assume = c.segments[si].assume || {})[f.field] = [v]; return blendOf(c).mcap; };
    let mLo, mHi;
    try { mLo = mk(r.lo); mHi = mk(r.hi); } catch (e) { warn.push(seg.name + '/' + f.field + ' 扰动失败: ' + e.message); return; }
    const width = CUR ? Math.abs(mHi - mLo) / CUR : 0;
    const outside = isFinite(curVal) && (curVal < r.lo - 1e-9 || curVal > r.hi + 1e-9);
    bars.push({
      seg: seg.name, segKey: seg.key, field: f.field, label: f.label,
      lo: r.lo, hi: r.hi, cur: curVal, src: r.src, fallback: r.fallback,
      mcapLo: mLo, mcapHi: mHi, width,
      oddsLo: CUR ? mLo / CUR - 1 : 0, oddsHi: CUR ? mHi / CUR - 1 : 0,
      curOutsideAnchors: outside,
      driver: (model.driver_focus || {}).strength || null
    });
  });
});
bars.sort((a, b) => b.width - a.width);

/* ---------- 跨轴：取期轴 --------------------------------------------------- */
const ctx = { currentMcap: CUR, shares: SHARES };
const tenor = [];
((p3.valuation || {}).paradigms || []).forEach(pd => {
  const p = pd.params || {};
  if (p.link !== true || !EONE.PARADIGM[pd.key]) return;
  const pts = [];
  for (let y = 0; y < F; y++) {
    const pp = clone(p);
    pp.year_offset = y;
    if (pp.r !== undefined) pp.n = y;                 // 05 §9.5：折现年距随取期同步
    let m;
    try { m = EONE.PARADIGM[pd.key](pp, base.pl, ctx).mcap; } catch (e) { continue; }
    if (isFinite(m) && m > 0) pts.push({ year: (p3.forecast_years || [])[y], offset: y, mcap: m, odds: CUR ? m / CUR - 1 : 0 });
  }
  if (pts.length >= 2) {
    const ms = pts.map(x => x.mcap);
    tenor.push({
      key: pd.key, name: pd.name, weight: Number(pd.weight) || 0, pts,
      lo: Math.min(...ms), hi: Math.max(...ms), spread: Math.max(...ms) / Math.min(...ms),
      width: CUR ? (Math.max(...ms) - Math.min(...ms)) / CUR : 0,
      curOffset: Number(p.year_offset) || 0
    });
  }
});
tenor.sort((a, b) => b.width - a.width);

/* ---------- 静态腿 + 范式敞口 --------------------------------------------- */
const legs = base.val.rows.filter(r => r.ok && isFinite(r.mcap) && r.mcap > 0);
const blend = base.mcap;
const exposure = legs.filter(r => !r.diagnostic && r.weight > 0 && r.weight <= 0.1 &&
                                  blend && Math.abs(r.mcap - blend) / blend > 0.40);

/* ---------- 判决 ----------------------------------------------------------- */
const topA = bars[0] || null;
const topT = tenor[0] || null;
const verdict = [];
if (topA) verdict.push('轴A第一名: ' + topA.seg + ' · ' + topA.label + '  幅度 ' + (topA.width * 100).toFixed(0) + '%现市值' + (topA.fallback ? '  [区间来自FALLBACK,不可作结论]' : ''));
if (topT) verdict.push('取期敞口第一名: ' + topT.key + '  幅度 ' + (topT.width * 100).toFixed(0) + '%现市值（' + topT.spread.toFixed(1) + 'x）');
if (topA) verdict.push('  轴A上界估计（÷传导率 ' + (TRANSMIT * 100).toFixed(0) + '%）: ' + (TRANSMIT ? (topA.width / TRANSMIT * 100).toFixed(0) : '∞') + '%现市值');
if (topA && topT) {
  const aUpper = TRANSMIT ? topA.width / TRANSMIT : Infinity;
  if (topT.width > aUpper) verdict.push('  （即便按上界比，取期敞口仍胜出 ⇒ 结论对传导率修正稳健）');
  else if (topT.width > topA.width) verdict.push('  （按下界取期敞口胜出，但按上界反转 ⇒ 必须先 relink 静态腿再定 CK-5b 路由）');
  if (topT.width > topA.width) {
    verdict.push('→ CK-5b 路由: **跨轴敞口 > 轴A第一名** ⇒ 页面主叙事必须是「市场在用哪个(范式,取期)定价」，轴A龙卷风降为附图');
  } else {
    verdict.push('→ CK-5b 路由: 轴A第一名胜出 ⇒ 声明的主矛盾必须 == ' + topA.seg + '·' + topA.label + '，否则嘴上的矛盾≠模型里的杠杆');
  }
}
const fbCount = bars.filter(b => b.fallback).length;
if (fbCount) warn.push(fbCount + '/' + bars.length + ' 根 bar 的区间来自 FALLBACK（缺 anchors）→ 这些 bar 只能排序参考，不能当力度结论');
bars.filter(b => b.curOutsideAnchors).forEach(b =>
  warn.push('本页假设落在锚区间之外: ' + b.seg + '·' + b.label + ' 现值 ' + b.cur + ' vs 锚 [' + b.lo + ',' + b.hi + ']'));

/* ---------- 输出 ----------------------------------------------------------- */
if (HAS('json')) {
  console.log(JSON.stringify({ ticker: (pm.meta || {}).ticker, name: (pm.meta || {}).name, current_mcap_yi: CUR, blend_mcap_yi: blend, bars, tenor, legs, exposure, verdict, warnings: warn }, null, 2));
  process.exit(0);
}

console.log('='.repeat(78));
console.log((pm.meta || {}).name || '', (pm.meta || {}).ticker || '', ' 现市值', fmt(CUR), '亿  加权隐含', fmt(blend), '亿  (' + pct(CUR ? blend / CUR - 1 : 0) + ')');
console.log('\n【轴A · 参数弹性龙卷风】区间来自各参数自己的锚离散度');
console.log('  弹性传导率 ' + (TRANSMIT * 100).toFixed(0) + '%（link腿权重占比）；冻结腿 ' + (FROZEN.join(' ') || '无') +
            '\n  → 下方「幅度」是**下界**（静态腿未活链）；上界≈下界÷传导率' +
            (TRANSMIT < 0.999 ? '＝×' + (1 / TRANSMIT).toFixed(1) : '') +
            '。要拿真值须按 05 §9.5 手工 relink 静态腿。');
console.log('  ' + '下界%'.padEnd(6) + ' '.padEnd(6) + '分部·参数'.padEnd(28) + '  区间→隐含市值(亿)          来源');
bars.forEach(b => {
  const bar = '█'.repeat(Math.max(1, Math.round(b.width * 40)));
  console.log('  ' + ((b.width * 100).toFixed(0) + '%').padEnd(6) + bar.padEnd(6) +
    ('  ' + (b.seg || '').slice(0, 14) + '·' + b.label + (b.driver === 'core' ? '★' : '')).padEnd(28) +
    '  [' + b.lo.toFixed(3) + '→' + b.hi.toFixed(3) + '] ' + fmt(b.mcapLo) + '→' + fmt(b.mcapHi) +
    '  ' + b.src + (b.curOutsideAnchors ? ' ⚠假设出锚' : ''));
});

if (tenor.length) {
  console.log('\n【跨轴 · 范式敞口：取期轴】同一利润路径，只改 Forward 取期（PE 折现年距同步）');
  tenor.forEach(t => {
    console.log('  ' + t.key + ' (w=' + t.weight + ', 现取 ' + ((p3.forecast_years || [])[t.curOffset] || '?') + ')  敞口 ' +
      (t.width * 100).toFixed(0) + '%现市值  跨度 ' + t.spread.toFixed(1) + 'x');
    console.log('     ' + t.pts.map(p => p.year + ':' + fmt(p.mcap) + '亿(' + pct(p.odds) + ')').join('  '));
  });
  console.log('  注: 取期敞口 ≠ 范式风险，也 ≠ 利润预测分歧——卖方常取更远年份配更高倍数，须另列其利润路径对照。');
}

console.log('\n【静态腿全景】');
legs.forEach(r => console.log('  ' + (r.key + (r.diagnostic ? '(诊断)' : '')).padEnd(12) + 'w=' + String(r.weight).padEnd(5) +
  fmt(r.mcap).padStart(8) + '亿  ' + pct(r.odds).padStart(8) + '  ' + (r.name || '')));
exposure.forEach(r => console.log('  ⚠️ 范式敞口: ' + r.key + ' 权重仅 ' + r.weight + ' 但偏离加权 ' +
  pct(r.mcap / blend - 1) + ' → 须单列，不许混进加权平均'));

console.log('\n【判决】');
verdict.forEach(v => console.log('  ' + v));
if (warn.length) { console.log('\n【告警】'); warn.forEach(w => console.log('  · ' + w)); }
