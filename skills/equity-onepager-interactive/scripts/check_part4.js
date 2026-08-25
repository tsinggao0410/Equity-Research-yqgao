#!/usr/bin/env node
/* =============================================================================
 * check_part4.js — 第四章「矛盾地图」CK-6 自动验收（headless，无需浏览器）
 * 参考 references/09-contradiction-map.md §9 CK-6 / §10a 图面体检
 *      references/13-contradiction-typology.md（role/subtype 枚举与判定顺序）
 *
 * 做法：桩掉 DOM → 加载 app.js → 跑 renderContradictionMap() → 抓各挂点的 innerHTML
 *      → 解析生成的 SVG 字符串做几何体检（CJK 按 1 字≈1em 估宽，与 placeLabels 同口径）
 *
 * 覆盖：S1–S7 4.1 场景（含 knobs 实跑引擎对赔率）· T1–T7 分型 · D1–D3 深度研究
 *      · a–f 原契约 · g 图面几何（圆/方等面积）
 *
 * 用法: node scripts/check_part4.js --model _workspace/<ticker>/page_model.json
 * 退出码: 0=全过 1=有 FAIL
 * ========================================================================== */
'use strict';
const fs = require('fs'), path = require('path');
const HERE = path.dirname(path.resolve(__filename));
const SKILL = path.dirname(HERE);

function arg(n, d) { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; }
const modelPath = arg('model');
if (!modelPath) { console.error('usage: node check_part4.js --model <page_model.json>'); process.exit(2); }
const D = JSON.parse(fs.readFileSync(modelPath, 'utf8'));

/* ---- 最小 DOM 桩（沿用 _workspace/002138/headless_check.js 的形制）---------- */
const els = {};
function stubEl(id) {
  return { id, _html: '', style: {}, classList: { add(){}, remove(){}, toggle(){}, contains(){ return false; } },
    set innerHTML(v) { this._html = v; }, get innerHTML() { return this._html; },
    set textContent(v) { this._text = v; }, get textContent() { return this._text || ''; },
    querySelectorAll() { return []; }, querySelector() { return null; }, addEventListener() {},
    getBoundingClientRect() { return { left:0, right:0, top:0, bottom:0 }; },
    parentNode: { set innerHTML(v) {}, get innerHTML() { return ''; } },
    getContext() { return {}; }, scrollIntoView() {}, closest() { return null; }, dataset: {},
    setAttribute() {}, getAttribute() { return null; }, insertBefore() {}, removeChild() {},
    remove() {}, appendChild() {}, firstChild: null };
}
global.document = { readyState: 'complete',
  getElementById(id) { return els[id] || (els[id] = stubEl(id)); },
  querySelectorAll() { return []; }, querySelector() { return null; },
  addEventListener() {}, createElement() { return stubEl('x'); },
  documentElement: { getAttribute() { return null; }, setAttribute() {}, clientWidth: 1200 } };
global.window = { __DATA__: D, matchMedia() { return { matches: false }; }, scrollX: 0, scrollY: 0,
  addEventListener() {}, getComputedStyle: () => ({ getPropertyValue: () => '#123456' }) };
global.getComputedStyle = global.window.getComputedStyle;
global.Chart = function () { return { destroy() {}, update() {} }; };
global.Chart.defaults = { font: {}, plugins: { legend: { labels: {} }, tooltip: {} }, scale: { grid: {} } };
global.window.EONE = require(path.join(HERE, 'model_engine.js'));

let appSrc = fs.readFileSync(path.join(SKILL, 'templates', 'app.js'), 'utf8');
appSrc = appSrc.replace(/if\s*\(document\.readyState[\s\S]*?boot\);?/, '');   // 别自动 boot
// 脱掉 IIFE 外壳，让内部函数暴露到本作用域（app.js 形如 (function(){ ... })();）
appSrc = appSrc.replace(/\(function\s*\(\)\s*\{/, '').replace(/\}\)\(\);\s*$/, '');
const sandbox = { document: global.document, window: global.window, getComputedStyle: global.getComputedStyle,
  Chart: global.Chart, console, Math, JSON, Date, parseFloat, parseInt, isFinite, isNaN, Object, Array, String, Number };
let API;
try {
  const fn = new Function('document','window','getComputedStyle','Chart','console',
    appSrc + '\n;return {renderContradictionMap:renderContradictionMap, cmapSVG:cmapSVG, cmapTable:cmapTable,' +
             ' renderScenarios:renderScenarios, scenarioRun:scenarioRun, knobPath:knobPath, MODEL:MODEL};');
  API = fn(sandbox.document, sandbox.window, sandbox.getComputedStyle, sandbox.Chart, console);
} catch (e) { console.error('✗ app.js 加载失败:', e.message); process.exit(1); }

/* ---- 跑渲染 --------------------------------------------------------------- */
const P4 = D.part4;
const results = [];
function chk(pass, name, detail) { results.push({ pass: !!pass, name, detail: detail || '' }); }

if (!P4 || !(P4.items || []).length) {
  console.log('part4 缺失或为空 → 第四章将整章隐藏（若本次不出第四章，这是预期行为）');
  process.exit(0);
}
try { API.renderContradictionMap(); } catch (e) { console.error('✗ renderContradictionMap 抛错:', e.stack); process.exit(1); }

const html = { svg: els['cmap-svg']._html || '', tb: els['cmap-table']._html || '',
               nar: els['cmap-narratives']._html || '', core: els['cmap-core']._html || '',
               scen: els['cmap-scen']._html || '', deep: els['cmap-deep']._html || '' };

/* ---- CK-6 a–f 契约检查 ---------------------------------------------------- */
const items = P4.items, nars = P4.narratives || [], core = P4.core || {};
const byId = {}; items.forEach(i => { byId[i.id] = i; });

/* ---- CK-6 S · 4.1 场景（09 §5.5） ---------------------------------------- */
const SC = P4.scenarios || {}, scs = SC.items || [];
const baseMcap = Number(SC.base_mcap_yi) ||
  Number(((D.part3 || {}).valuation || {}).current_mcap_yi) || Number((D.meta || {}).current_mcap_yi) || 0;
chk(scs.length >= 3 && scs.length <= 5, 'CK-6 S1 场景 3–5 条', scs.length + ' 条');
chk(scs.some(s => s.dir === 'down'), 'CK-6 S1 至少一条下行场景',
  scs.filter(s => s.dir === 'down').length + ' 条下行');

const badFrom = scs.filter(s => {
  const f = s.from || {};
  return !f.active || !f.passive || !byId[f.active] || !byId[f.passive] || !f.active_dir || !f.passive_dir;
});
chk(!badFrom.length, 'CK-6 S2 from 指名真实矛盾+方向', badFrom.map(s => s.key).join(',') || 'ok');
// from 的两端应分属主动/从动——叉乘的前提（13 §0）
const badPair = scs.filter(s => {
  const a = byId[(s.from || {}).active], p = byId[(s.from || {}).passive];
  return a && p && !(a.role === '主动' && p.role === '从动');
});
chk(!badPair.length, 'CK-6 S2 from 两端分属主动/从动', badPair.map(s => s.key).join(',') || 'ok');

const noKnobs = scs.filter(s => !s.knobs || !Object.keys(s.knobs).length);
chk(!noKnobs.length, 'CK-6 S3 每条都有 knobs(含下行)', noKnobs.map(s => s.key).join(',') || 'ok');
// knobs 实跑引擎：路径可解析 + 市值/赔率自洽（容差 1%/1pp）
const knobErr = [];
scs.forEach(s => {
  if (!s.knobs) return;
  let r; try { r = API.scenarioRun(s.knobs); } catch (e) { knobErr.push(s.key + ':抛错 ' + e.message); return; }
  if (!r) { knobErr.push(s.key + ':跑不动'); return; }
  if ((r.bad || []).length) { knobErr.push(s.key + ':路径不存在 ' + r.bad.join('/')); return; }
  if (r.err) { knobErr.push(s.key + ':引擎 ' + r.err); return; }
  if (!isFinite(r.mcap)) { knobErr.push(s.key + ':市值非有限值'); return; }
  if (isFinite(+s.mcap_yi) && +s.mcap_yi > 0) {
    const d = Math.abs(r.mcap - +s.mcap_yi) / +s.mcap_yi;
    if (d > 0.01) knobErr.push(s.key + ':实跑 ' + r.mcap.toFixed(1) + '亿 vs 填 ' + s.mcap_yi + '亿 差 ' + (d * 100).toFixed(1) + '%');
  }
  if (baseMcap > 0 && isFinite(+s.odds)) {
    const o = (r.mcap / baseMcap - 1) * 100;
    if (Math.abs(o - +s.odds) > 1) knobErr.push(s.key + ':实跑赔率 ' + o.toFixed(0) + '% vs 填 ' + s.odds + '%');
  }
});
chk(!knobErr.length, 'CK-6 S3 knobs 实跑与 mcap/odds 自洽', knobErr.join(' | ') || 'ok');
// knobs 估值腿必须按 paradigm key 寻址，不许用下标（下标会随增删腿漂移）
const idxKnob = [];
scs.forEach(s => Object.keys(s.knobs || {}).forEach(k => {
  if (/^valuation\.paradigms[.[]\d/.test(k)) idxKnob.push(s.key + ':' + k); }));
chk(!idxKnob.length, 'CK-6 S3 估值腿按 key 不按下标', idxKnob.join(',') || 'ok');

// dir 是「股价涨还是跌」，必须与 odds 符号一致——标 down 却算出正赔率＝方向标签或 knobs 有一个是错的
const dirBad = scs.filter(s => (s.dir === 'down') !== (+s.odds < 0));
chk(!dirBad.length, 'CK-6 S3 dir 与 odds 符号一致',
  dirBad.map(s => s.key + '(' + s.dir + '/' + s.odds + '%)').join(',') || 'ok');
// 赔率带必须把点估计夹在中间，否则带子是摆设
const bandBad = scs.filter(s => { const b = s.odds_band || [];
  if (b.length !== 2) return true;
  const lo = Math.min(+b[0], +b[1]), hi = Math.max(+b[0], +b[1]);
  return !(+s.odds >= lo - 0.5 && +s.odds <= hi + 0.5); });
chk(!bandBad.length, 'CK-6 S3 odds_band 夹住 odds', bandBad.map(s => s.key).join(',') || 'ok');

const rmvBad = scs.filter(s => {
  const q = s.rmv || {};
  const sum = (+q.r_pp || 0) + (+q.m_pp || 0) + (+q.v_pp || 0);
  return !s.rmv || Math.abs(sum - (+s.odds || 0)) > 3;
});
chk(!rmvBad.length, 'CK-6 S4 ΣR/M/V 对 odds 差 ≤3pp', rmvBad.map(s => s.key).join(',') || 'ok');
chk(scs.every(s => (s.rmv || {}).basis), 'CK-6 S4 rmv.basis 写明降级链',
  scs.filter(s => !(s.rmv || {}).basis).map(s => s.key).join(',') || 'ok');

const catBad = scs.filter(s => !(s.catalysts || []).length ||
  (s.catalysts || []).some(c => !c.when || !c.watch));
chk(!catBad.length, 'CK-6 S5 催化 ≥1 且 when+watch 齐', catBad.map(s => s.key).join(',') || 'ok');
chk(scs.every(s => s.rmv_check), 'CK-6 S6 rmv_check 已与第二章对照',
  scs.filter(s => !s.rmv_check).map(s => s.key).join(',') || 'ok');

const mainKey = (D.summary || {}).main_scenario;
chk(!!mainKey && scs.some(s => s.key === mainKey), 'CK-6 S7 开篇主线对上某个场景',
  mainKey ? (scs.some(s => s.key === mainKey) ? mainKey : mainKey + ' 不存在') : '缺 summary.main_scenario');

/* S8 · 概率与期望值（2026-08-14 阳光固化）。
   赔率没有概率就不是赔率，是情景标价——五条 Case 摆着 +77/+57/−16/−13/−18，
   读者合不出 EV 来。三件一起要：我填的概率、由它算出的 EV、以及现价隐含的上行概率。 */
const noProb = scs.filter(s => s.prob == null || !isFinite(Number(s.prob)));
chk(!noProb.length, 'CK-6 S8 每条 Case 有 prob',
  noProb.length ? noProb.map(s => s.key).join(',') + ' 未填' : `${scs.length} 条齐`);
if (!noProb.length) {
  const sumP = scs.reduce((a, s) => a + Number(s.prob), 0);
  chk(Math.abs(sumP - 1) <= 0.02, 'CK-6 S8 Σprob = 100%±2pp', `Σ=${(sumP * 100).toFixed(1)}%`);
  const rng = scs.filter(s => Number(s.prob) < 0 || Number(s.prob) > 1);
  chk(!rng.length, 'CK-6 S8 prob ∈ [0,1]', rng.map(s => s.key).join(',') || 'ok');
  const noBasis = scs.filter(s => !s.prob_basis || String(s.prob_basis).length < 10);
  chk(!noBasis.length, 'CK-6 S8 每条 prob_basis ≥10 字',
    noBasis.map(s => s.key).join(',') || 'ok');
  // 现价隐含上行概率：令 EV=0 反解 p_up，组内相对权重沿用填写的 prob
  const wm = list => { let w = 0, s = 0; list.forEach(x => { const p = Number(x.prob) || 0; w += p; s += p * Number(x.odds); });
    return w > 0 ? s / w : (list.length ? list.reduce((a, x) => a + Number(x.odds), 0) / list.length : null); };
  const mu = wm(scs.filter(s => s.dir !== 'down')), md = wm(scs.filter(s => s.dir === 'down'));
  const ev = scs.reduce((a, s) => a + Number(s.prob) * Number(s.odds), 0);
  const pUp = (mu != null && md != null && mu !== md) ? (-md / (mu - md)) * 100 : null;
  const myUp = scs.filter(s => s.dir !== 'down').reduce((a, s) => a + Number(s.prob), 0) * 100;
  chk(pUp != null, 'CK-6 S8 现价隐含上行概率可解',
    pUp == null ? '上行/下行均值相等，解不出' :
      `EV ${ev >= 0 ? '+' : ''}${ev.toFixed(1)}% · 我给上行 ${myUp.toFixed(1)}% vs 现价隐含 ${pUp.toFixed(1)}% · 差 ${(myUp - pUp >= 0 ? '+' : '') + (myUp - pUp).toFixed(1)}pp`);
  if (pUp != null) chk(Math.abs(myUp - pUp) >= 10 || !!(D.part4.scenarios || {}).thin_edge_why,
    'CK-6 S8 与市场差 <10pp 时须说明为何还下注',
    `差 ${(myUp - pUp).toFixed(1)}pp` + (Math.abs(myUp - pUp) >= 10 ? '（≥10pp，免）' : '，须填 scenarios.thin_edge_why'));
}

/* S9 · 历史对照＝跨公司/跨叙事（2026-08-17 石英股份读者反馈固化，09 §5.5h）。
   读者原话「历史对照不是要和自己历史上对照，而是和历史上其他公司或者其他叙事对照」——
   scenCard 原来只画本股历史最强段的 R/M/V 同尺度条（那是 S6 的量纲对照，已改名）。
   每条 Case 要给别家走过同一条路的样本：case（公司/叙事+年份）+ what（发生了什么、多久、多大）+ diff（与本例差异，必填）。 */
const selfName = String((D.meta || {}).name || '');
const anBad = scs.filter(s => { const a = s.analog || {}; const c = String(a.case || a.company || '');
  return !(c.length >= 4 && (!selfName || !c.includes(selfName)) && String(a.diff || '').length >= 15); });
chk(!anBad.length, 'CK-6 S9 每条 Case 有跨公司/跨叙事 analog（case≠本股 + diff≥15字）',
  anBad.length ? anBad.map(s => s.key + (s.analog ? (String((s.analog.case || '')).includes(selfName) && selfName ? '(对照的是本股自己)' : '(缺 diff/case)') : '(缺 analog)')).join(',') : `${scs.length} 条齐`);

/* ---- CK-6 T · 分型（references/13） -------------------------------------- */
const SUB_ACT = ['采用/可及型','份额型','产业边界型','单机配置型','使用强度型','存量更新型',
                 '周期复苏型','政策-强制型','政策-激励型','新场景型'];
const SUB_PSV = ['弹性型','资本/回报型','纪律型','物理/技术型','禀赋/衰减型','要素型',
                 '系统协同型','制度/权利型','临时失衡型'];
const SUB_RIGHT = ['配额','许可审批','诉讼与地方否决','出口许可','合同锁定'];
const noRole = items.filter(i => ['主动','从动'].indexOf(i.role) < 0);
chk(!noRole.length, 'CK-6 T1 每条 role 合法', noRole.map(i => i.id + ':' + i.role).join(',') || 'ok');
const nAct = items.filter(i => i.role === '主动').length, nPsv = items.filter(i => i.role === '从动').length;
chk(nAct >= 1 && nPsv >= 1, 'CK-6 T1 主动/从动各 ≥1', '主动 ' + nAct + ' / 从动 ' + nPsv);
const badSub = items.filter(i => {
  const pool = i.role === '主动' ? SUB_ACT : i.role === '从动' ? SUB_PSV : [];
  return pool.length && pool.indexOf(i.subtype) < 0; });
chk(!badSub.length, 'CK-6 T1 subtype 在本 role 枚举内', badSub.map(i => i.id + ':' + i.subtype).join(',') || 'ok');

/* 默认时钟以 references/13 §2b 九型定义表为准（2026-08-14 对齐）。
   原来 checker 写 弹性型:'多年'、临时失衡型:'季度'，与 13 表的「时滞 18–24m」「数月」打架——
   照 13 写会被判 T2 不过，照 checker 写又和分型文档不一致。现在每型给一组可接受写法，
   首项＝13 表的规范值，其余是等价别名；写别的仍要 clock_override_why。 */
const SUB_CLOCK = {
  '周期复苏型':['季度'], '单机配置型':['代际'], '使用强度型':['季度'], '存量更新型':['多年'],
  '新场景型':['多年'],
  '弹性型':['时滞 18–24m','时滞 18-24m','18–24m','多年'],
  '资本/回报型':['价格触发，非固定','价格触发'],
  '纪律型':['季度'],
  '物理/技术型':['多年'], '禀赋/衰减型':['多年'],
  '要素型':['建设周期'],
  '系统协同型':['= 最慢那一环','最慢那一环','多年'],
  '制度/权利型':['政策周期'],
  '临时失衡型':['数月','季度'] };
const clkBad = items.filter(i => i.subtype && SUB_CLOCK[i.subtype] &&
  i.clock && SUB_CLOCK[i.subtype].indexOf(i.clock) < 0 && !i.clock_override_why);
chk(!clkBad.length, 'CK-6 T2 偏离默认时钟须写理由',
  clkBad.map(i => `${i.id}:${i.clock}（默认 ${SUB_CLOCK[i.subtype][0]}）`).join(',') || 'ok');

const noRuled = items.filter(i => i.role === '从动' && !(i.ruled_out || []).length);
chk(!noRuled.length, 'CK-6 T3 从动型有 ruled_out 排除链', noRuled.map(i => i.id).join(',') || 'ok');

const disc = items.filter(i => i.subtype === '纪律型');
const discBad = disc.filter(i => {
  const t = i.discipline_upgrade_test || {};
  return Number(i.coverage) === 0 || !(i.ev || []).length ||
    !(t.profitable && t.certifiable && t.still_not_expanding) ||
    !(t.profitable.ev && t.certifiable.ev && t.still_not_expanding.ev) ||
    !t.certifiable.holding_period; });
chk(!discBad.length, 'CK-6 T4 纪律型 coverage>0+ev+升格三条件', discBad.map(i => i.id).join(',') || (disc.length ? 'ok' : '无纪律型'));

const sysBad = items.filter(i => i.subtype === '系统协同型' &&
  (!((i.stack || []).length >= 2) || !(i.binding_now || {}).link ||
   !(i.stack || []).some(s => s.link === i.binding_now.link)));
chk(!sysBad.length, 'CK-6 T5 系统协同型 stack≥2 且 binding_now 在 stack 内', sysBad.map(i => i.id).join(',') || 'ok');

const rightBad = items.filter(i => i.subtype === '制度/权利型' && SUB_RIGHT.indexOf(i.sub_right) < 0);
chk(!rightBad.length, 'CK-6 T6 制度/权利型填了 sub_right', rightBad.map(i => i.id).join(',') || 'ok');

const coBad = [];
items.forEach(i => (i.co_kill || []).forEach(o => {
  if (!byId[o]) coBad.push(i.id + '→' + o + '(不存在)');
  else if ((byId[o].co_kill || []).indexOf(i.id) < 0) coBad.push(i.id + '→' + o + '(未互指)');
  else if (!/co_kill|同源|扣除|重复/.test(i.odds_basis || '')) coBad.push(i.id + '(odds_basis 未说明扣重)'); }));
chk(!coBad.length, 'CK-6 T7 co_kill 互指且赔率已扣重', coBad.join(',') || 'ok');

/* ---- CK-6 V · 覆盖与语言（09 §0 / §5.5-0） ------------------------------- */
// V1 覆盖：没被任何场景 from 引用的 item，必须交代去向，否则读者分不出"评估过"还是"没研究"
const CUT_WHY = ['已定价', '重述叙事', '赔率虚高', '与主线无因果'];
const usedIds = new Set();
scs.forEach(s => { const f = s.from || {}; if (f.active) usedIds.add(f.active); if (f.passive) usedIds.add(f.passive); });
const orphan = items.filter(i => !usedIds.has(i.id));
const noWhere = orphan.filter(i => {
  const n = i.no_scenario;
  // 只有两种合法去向。★没有「待研究」：上了图就意味着过了 CK-6b 取证与 tornado 赔率，
  //   它已经研究过了。真正缺的是「横切」——不定义某个 Case，而是把所有 Case 的赔率整体推一档。
  if (!n || ['剪掉', '横切'].indexOf(n.status) < 0 || !n.why) return true;
  if (n.status === '剪掉') return !CUT_WHY.some(w => n.why.indexOf(w) >= 0);
  return !/\d/.test(n.why); });                 // 横切必须给出它把赔率推多少（带数字）
chk(!noWhere.length, 'CK-6 V1 未成 Case 的矛盾已交代去向(剪掉/横切)',
  noWhere.map(i => i.id).join(',') || (orphan.length ? orphan.length + ' 条已交代' : '无孤儿项'));

// V2/V3 语言：规范全文在 buyside-voice，这里只在生成期做机检。
// ★引用豁免：ev[].quote 与 chain[].ev 是逐字原句，为过闸改信源比命中禁词严重得多。
// 规范唯一出处是 buyside-voice，本 skill 不留副本。它可能装在 ~/.claude/skills/ 下，
// 也可能在插件会话目录里（路径带随机 uuid，会变），所以按序探测 + 兜底 glob。
function findVoiceRules() {
  const H = process.env.HOME || '';
  if (process.env.VOICE_RULES && fs.existsSync(process.env.VOICE_RULES)) return process.env.VOICE_RULES;
  const direct = [path.join(H, '.claude/skills/buyside-voice/references/voice-rules.md'),
                  path.join(H, '.claude/skills/anthropic-skills/buyside-voice/references/voice-rules.md')];
  for (const p of direct) if (fs.existsSync(p)) return p;
  const root = path.join(H, 'Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin');
  try {                                    // <root>/<uuid>/<uuid>/skills/buyside-voice/references/
    for (const a of fs.readdirSync(root)) for (const b of fs.readdirSync(path.join(root, a))) {
      const p = path.join(root, a, b, 'skills/buyside-voice/references/voice-rules.md');
      if (fs.existsSync(p)) return p;
    }
  } catch (e) { /* 目录不存在就算了 */ }
  return null;
}
const VOICE = findVoiceRules();
let BAN = [];
if (VOICE) try {
  const sec = /## §3 禁词表[\s\S]*?(?=\n## )/.exec(fs.readFileSync(VOICE, 'utf8'));
  if (sec) BAN = [...new Set((sec[0].match(/`([^`]{2,12})`/g) || [])
    .map(x => x.slice(1, -1)).filter(w => !/[（(]/.test(w)))];
} catch (e) { /* 读不动就跳过，不阻断验收 */ }

const AUTHORED = ['detail', 'one_liner', 'dispersion_basis', 'odds_basis', 'verify', 'why', 'action',
  'story', 'weakest', 'name', 'note', 'essence', 'mechanism', 'resolve_up', 'resolve_down',
  'why_core', 'common_mistake', 'primary', 'fallback', 'blind_spot', 'means', 'claim',
  'then', 'outcome', 'tell', 'diff', 'rmv_check', 'cond', 'what'];
const QUOTED = new Set(['quote', 'ev']);          // 逐字原句：整支豁免
function harvest(o, out, key) {
  if (o == null) return;
  if (typeof o === 'string') { if (AUTHORED.indexOf(key) >= 0) out.push({ k: key, t: o }); return; }
  if (Array.isArray(o)) { o.forEach(v => harvest(v, out, key)); return; }
  if (typeof o === 'object') Object.keys(o).forEach(k => { if (!QUOTED.has(k)) harvest(o[k], out, k); });
}
const authored = []; harvest(P4, authored, null);
const banHit = [];
if (BAN.length) authored.forEach(x => BAN.forEach(w => { if (x.t.indexOf(w) >= 0) banHit.push(x.k + ':' + w); }));
chk(!banHit.length, 'CK-6 V2 自撰字段禁词 0 命中（引用豁免）',
  BAN.length ? ([...new Set(banHit)].slice(0, 8).join(' ') || ('ok · 词表 ' + BAN.length + ' 词'))
             : '找不到 voice-rules.md，本项跳过；可设 VOICE_RULES=<路径>');

const dash = authored.reduce((a, x) => a + (x.t.match(/——/g) || []).length, 0);
const chars = authored.reduce((a, x) => a + x.t.length, 0);
const per1k = chars ? dash / (chars / 1000) : 0;
chk(dash <= 8 && per1k <= 1, 'CK-6 V3 自撰字段「——」≤8 且每千字 ≤1',
  dash + ' 个 / ' + Math.round(chars / 1000) + ' 千字 = 每千字 ' + per1k.toFixed(1));

/* ---- CK-6 D · 深度研究（09 §6b/§6c） ------------------------------------- */
const slots = [['pricing', core.pricing], ['actionable', core.actionable]];
const ddMiss = slots.filter(([k, s]) => {
  const dd = (s || {}).deepdive;
  return !dd || !(dd.understanding || {}).mechanism || !(dd.plan || {}).primary || !(dd.ruling || []).length; });
chk(!ddMiss.length, 'CK-6 D1 双槽位 deepdive 三块齐', ddMiss.map(x => x[0]).join(',') || 'ok');
const blindMiss = slots.filter(([k, s]) => !(((s || {}).deepdive || {}).plan || {}).blind_spot);
chk(!blindMiss.length, 'CK-6 D2 plan.blind_spot 非空', blindMiss.map(x => x[0]).join(',') || 'ok');
const agBad = slots.filter(([k, s]) => { const a = ((s || {}).deepdive || {}).analog; return !a || !a.diff; });
chk(!agBad.length, 'CK-6 D3 analog.diff 非空', agBad.map(x => x[0]).join(',') || 'ok');
chk(items.length >= 8 && items.length <= 12, 'CK-6a 矛盾 8–12 条', items.length + ' 条');
const badLabel = items.filter(i => !i.label || i.label.length < 4 || i.label.length > 9);
chk(!badLabel.length, 'CK-6a label 5–8 字', badLabel.map(i => i.id + ':' + i.label).join(',') || 'ok');
const badDetail = items.filter(i => !i.detail || i.detail.length < 25 || !/\d/.test(i.detail));
chk(!badDetail.length, 'CK-6a detail ≥25字且带数字', badDetail.map(i => i.id).join(',') || 'ok');
const noOne = items.filter(i => !i.one_liner);
chk(!noOne.length, 'CK-6a 每条有 one_liner', noOne.map(i => i.id).join(',') || 'ok');

const noDisp = items.filter(i => !i.dispersion_basis);
const dispNoNum = items.filter(i => i.dispersion_basis && !/\d/.test(i.dispersion_basis) && Number(i.coverage) !== 0);
chk(!noDisp.length, 'CK-6b 每条有 dispersion_basis', noDisp.map(i => i.id).join(',') || 'ok');
chk(!dispNoNum.length, 'CK-6b 非零覆盖项的分歧口径带具体数字', dispNoNum.map(i => i.id).join(',') || 'ok');
const withEv = items.filter(i => (i.ev || []).length).length;
chk(withEv * 2 >= items.length, 'CK-6b 至少半数挂逐字原句', withEv + '/' + items.length);

const noOdds = items.filter(i => !i.odds_basis);
chk(!noOdds.length, 'CK-6c 每条有 odds_basis', noOdds.map(i => i.id).join(',') || 'ok');
/* ★2026-08-17 石英股份：10 条矛盾 odds 全是 null，odds_basis 写得很像算过——覆盖表与三坐标图全空，读者「赔率都没算出来」。
   写了怎么算 ≠ 算了：tornado bar 或手算上界必须落成 items[].odds 这个数（可为 0，不可为空）。 */
const oddsNaN = items.filter(i => i.odds == null || !isFinite(Number(i.odds)));
chk(!oddsNaN.length, 'CK-6c 每条 odds 是数字（写了 odds_basis 不等于算了）',
  oddsNaN.length ? `${oddsNaN.length}/${items.length} 条 odds 为空：${oddsNaN.map(i => i.id).join(',')}` : 'ok');
const fallback = items.filter(i => /FALLBACK/i.test(i.odds_basis || ''));
chk(!fallback.length, 'CK-6c 无 FALLBACK 区间直接当赔率', fallback.map(i => i.id).join(',') || 'ok');

const PL = ['收入', '利润率', '费用率'];
const noHook = items.filter(i => PL.indexOf(i.layer) >= 0 && !i.hooked);
chk(!noHook.length, 'CK-6d P&L三层必填 hooked', noHook.map(i => i.id + '(' + i.layer + ')').join(',') || 'ok');
const badLayer = items.filter(i => ['叙事','估值'].concat(PL).indexOf(i.layer) < 0);
chk(!badLayer.length, 'CK-6d layer 取值合法', badLayer.map(i => i.id + ':' + i.layer).join(',') || 'ok');

chk(core.pricing && core.actionable, 'CK-6e 双槽位齐全',
  (core.pricing ? '' : '缺 pricing ') + (core.actionable ? '' : '缺 actionable'));
chk(!(core.pricing && core.actionable && core.pricing.id === core.actionable.id),
  'CK-6e 两槽位不是同一条', core.pricing ? (core.pricing.id + ' vs ' + (core.actionable || {}).id) : '—');
chk(core.pricing && core.pricing.why && core.pricing.action && core.actionable && core.actionable.why && core.actionable.action,
  'CK-6e 双槽位 why+action 齐全');

chk(nars.length > 0, 'CK-6f 有叙事拆解', nars.length + ' 条');
const badNar = nars.filter(n => !(n.chain || []).length || !n.weakest || !(n.subs || []).length);
chk(!badNar.length, 'CK-6f 每条叙事有 chain+weakest+subs', badNar.map(n => n.key).join(',') || 'ok');
const badStatus = nars.reduce((a, n) => a.concat((n.chain || []).filter(c => ['已证实','部分证实','未证实','已证伪'].indexOf(c.status) < 0)), []);
chk(!badStatus.length, 'CK-6f chain 每步 status 合法', badStatus.length + ' 处非法');

/* ---- CK-6f2/f3/f4 叙事链的**可读性**闸（2026-08-18 用户反馈固化）------------
   用户原话：「你本身做的都不很清楚，说的内容也很 ai，即使没有用禁词，也很难去阅读和理解。」
   最后半句是关键——**禁词表管不住这件事**。让链读不动的不是某几个词，是三种结构性毛病：
     ① 一环里没有任何一个数 →「下游需求持续释放带动价值量提升」这种句子，四条链可以共用，
        换个标的照抄成立，它没有说任何关于这家公司的事；
     ② 一环写成一段 → 60 字以上就不是「一环」了，是把推导过程原样倒出来；
     ③ 一条链十几环 → 环越多越像在凑，真正传导的关节通常 4–6 个。
   三条都是可机检的**结构**判据，不靠词表。'已证实' 还必须挂原句——
   证实与否是这一节唯一的产出，空口标'已证实'等于把结论白送。 */
const chainAll = nars.reduce((a, n) => a.concat((n.chain || []).map(c => ({ k: n.key, c }))), []);
const noNum = chainAll.filter(x => !/\d/.test(String(x.c.claim || '')));
chk(!noNum.length, 'CK-6f2 chain 每环 claim 带数字（无数字＝换个标的照抄也成立）',
  noNum.length ? noNum.slice(0, 3).map(x => `${x.k}#${x.c.step}`).join('、') + (noNum.length > 3 ? ` 等 ${noNum.length} 环` : '') : `${chainAll.length} 环全带数`);
const tooLong = chainAll.filter(x => String(x.c.claim || '').replace(/\s/g, '').length > 60);
chk(!tooLong.length, 'CK-6f2 chain 每环 claim ≤60 字（超了就不是一环，是一段）',
  tooLong.length ? tooLong.slice(0, 3).map(x => `${x.k}#${x.c.step}(${String(x.c.claim).replace(/\s/g, '').length}字)`).join('、') : 'ok');
const tooDeep = nars.filter(n => (n.chain || []).length > 6);
chk(!tooDeep.length, 'CK-6f3 每条链 ≤6 环（十几环是在凑传导，不是在传导）',
  tooDeep.length ? tooDeep.map(n => `${n.key} ${n.chain.length}环`).join('、') : 'ok');
const okNoEv = chainAll.filter(x => x.c.status === '已证实' && !String(x.c.ev || '').trim());
chk(!okNoEv.length, 'CK-6f3 标「已证实」的环必须挂原句 ev',
  okNoEv.length ? okNoEv.slice(0, 3).map(x => `${x.k}#${x.c.step}`).join('、') : 'ok');
const vagueWeak = nars.filter(n => !/第\s*\d|#\d|\d\s*环|\d\s*步/.test(String(n.weakest || '')));
chk(!vagueWeak.length, 'CK-6f4 weakest 点名是第几环（只说"最弱的是需求端"没法跟踪）',
  vagueWeak.length ? vagueWeak.map(n => n.key).join('、') : 'ok');
const narKeys = nars.map(n => n.key);
const linkOK = items.filter(i => i.narrative).every(i => narKeys.indexOf(i.narrative) >= 0);
chk(linkOK, 'CK-6f 下钻超链接指向存在的叙事');
chk(/href="#nar-/.test(html.svg), 'CK-6f 主图渲出下钻链接');
chk((html.nar.match(/id="nar-/g) || []).length === nars.length, 'CK-6f 叙事锚点数对得上');

/* ---- CK-6g 图面几何体检 --------------------------------------------------- */
// 估宽：CJK/全角 ≈ 1em，ASCII ≈ 0.55em（与浏览器实测差 <5%，够做越界判定）
function textW(t, fs) {
  let w = 0; for (const ch of String(t || '')) w += (ch.charCodeAt(0) > 0x2e80 ? 1 : 0.55);
  return w * fs;
}
function parseSVG(s) {
  const vb = /viewBox="0 0 (\d+) (\d+)"/.exec(s);
  const W = vb ? +vb[1] : 900, H = vb ? +vb[2] : 620;
  const circles = [], tips = [], labels = [];
  let m;
  const reC = /<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"(?![^>]*class="hit")/g;
  while ((m = reC.exec(s))) circles.push({ x: +m[1], y: +m[2], r: +m[3], shape: 'circle' });
  // ★从动矛盾渲成等面积方块（09 §8a）：折成等效半径 a/2 参与重叠/压标签体检。
  //   浮窗底板也是 rect，但它带 rx="6"；方块 rx="2"，两者不会互串。
  const reQ = /<rect class="qmark" x="([\d.-]+)" y="([\d.-]+)" width="([\d.]+)" height="([\d.]+)" rx="2"/g;
  while ((m = reQ.exec(s))) {
    const a = +m[3];
    circles.push({ x: +m[1] + a / 2, y: +m[2] + a / 2, r: a / 2, shape: 'square', side: a });
  }
  const reR = /<rect x="([\d.-]+)" y="([\d.-]+)" width="(\d+)" height="([\d.]+)" rx="6"/g;
  while ((m = reR.exec(s))) tips.push({ x: +m[1], y: +m[2], w: +m[3], h: +m[4] });
  const reL = /<text class="qlab" x="([\d.-]+)" y="([\d.-]+)" text-anchor="middle"[^>]*>([^<]*)</g;
  while ((m = reL.exec(s))) { const t = m[3], w = t.length * 12;
    labels.push({ cx: +m[1], y: +m[2], w: w, x: +m[1] - w / 2, h: 14, t: t }); }
  // 浮窗：必须按 <g class="hot"> 块逐个取，否则会把坐标轴/象限文字误当浮窗文字（假阳性）
  const blocks = s.match(/<g class="hot">[\s\S]*?<\/g><\/g>/g) || [];
  const tipBlocks = blocks.map(b => {
    const r = /<rect x="([\d.-]+)" y="([\d.-]+)" width="(\d+)" height="([\d.]+)" rx="6"/.exec(b);
    const texts = []; let t;
    const reT = /<text x="([\d.-]+)" y="([\d.-]+)" font-size="([\d.]+)"[^>]*>([^<]*)</g;
    while ((t = reT.exec(b))) texts.push({ x: +t[1], y: +t[2], fs: +t[3], t: t[4] });
    return r ? { rect: { x: +r[1], y: +r[2], w: +r[3], h: +r[4] }, texts } : null;
  }).filter(Boolean);
  return { W, H, circles, tips, labels, tipBlocks };
}
const svgBlobs = [];
(html.svg.match(/<svg class="cmap"[\s\S]*?<\/svg>/g) || []).forEach(s => svgBlobs.push({ tag: '4.1 主图', s }));
/* ★2026-08-18：4.5 次级矛盾**不再出图**（用户：图本身不清楚，读不动）。
   这条闸因此从「主1 + 每条叙事一张子坐标」翻成「全页只有 4.1 那一张」——
   4.5 里再出现 <svg class="cmap"> 就是渲染层退回旧版了，要报错，不是要放行。 */
const narSVG = (html.nar.match(/<svg class="cmap"[\s\S]*?<\/svg>/g) || []).length;
chk(svgBlobs.length === 1 && narSVG === 0, 'CK-6g 坐标系只此一张（4.1 主图；4.5 不出图）',
  svgBlobs.length + ' 张主图' + (narSVG ? `；4.5 仍渲了 ${narSVG} 张子坐标系（应为 0）` : '；4.5 无图 ✓'));

let gOOB = 0, gOvl = 0, gLab = 0, gLL = 0, gTxt = 0;
svgBlobs.forEach(b => {
  const P = parseSVG(b.s);
  P.tips.forEach(t => { if (t.x < 0 || t.y < 0 || t.x + t.w > P.W || t.y + t.h > P.H) gOOB++; });
  for (let i = 0; i < P.circles.length; i++) for (let j = i + 1; j < P.circles.length; j++) {
    const a = P.circles[i], c = P.circles[j];
    if (Math.hypot(a.x - c.x, a.y - c.y) < a.r + c.r) gOvl++; }
  P.labels.forEach(L => { P.circles.forEach(c => {
    const cx = Math.max(L.x, Math.min(c.x, L.x + L.w)), cy = Math.max(L.y - 11, Math.min(c.y, L.y + 3));
    if (Math.hypot(c.x - cx, c.y - cy) < c.r - 1) gLab++; }); });
  for (let i = 0; i < P.labels.length; i++) for (let j = i + 1; j < P.labels.length; j++) {
    const a = P.labels[i], c = P.labels[j];
    if (a.x < c.x + c.w + 4 && c.x < a.x + a.w + 4 && Math.abs(a.y - c.y) < 15) gLL++; }
  // 浮窗文字宽度 vs 自己的底板（CJK≈1em，ASCII≈0.55em）
  P.tipBlocks.forEach(B => B.texts.forEach(x => {
    if (x.x + textW(x.t, x.fs) > B.rect.x + B.rect.w - 3 ||
        x.y > B.rect.y + B.rect.h || x.y < B.rect.y) gTxt++; }));
});
chk(gOOB === 0, 'CK-6g 浮窗底板不越界', gOOB + ' 处');
chk(gTxt === 0, 'CK-6g 浮窗文字不溢出底板', gTxt + ' 处');
chk(gOvl === 0, 'CK-6g 气泡两两不重叠', gOvl + ' 对');
chk(gLab === 0, 'CK-6g 标签不压气泡', gLab + ' 处');
chk(gLL === 0, 'CK-6g 标签不互压', gLL + ' 对');
chk(/class="tip"/.test(html.svg) && !/onmouseover|addEventListener/.test(html.svg),
  'CK-6g 浮窗纯 CSS（无 JS 事件）');
// 面积严格正比赔率：主动=圆 r=4.3√odds，从动=等面积方 a=√π·r
const SQK = Math.sqrt(Math.PI);
const areaBad = items.filter(it => {
  const r = Math.max(8, 4.3 * Math.sqrt(Math.max(0, +it.odds || 0)));
  return it.role === '从动'
    ? !new RegExp('class="qmark"[^>]*width="' + (SQK * r).toFixed(1) + '"').test(html.svg)
    : !new RegExp('<circle cx="[\\d.]+" cy="[\\d.]+" r="' + r.toFixed(1) + '"').test(html.svg); });
chk(!areaBad.length, 'CK-6g 面积正比赔率(圆 4.3√odds/方 ×1.772)', areaBad.map(i => i.id).join(',') || 'ok');
// 形状与 role 对得上：方块数应等于从动矛盾条数
const nSquare = (html.svg.match(/<rect class="qmark"/g) || []).length;
chk(nSquare === nPsv, 'CK-6g 方块数=从动矛盾条数', nSquare + ' vs ' + nPsv);

/* ---- 输出 ----------------------------------------------------------------- */
const fail = results.filter(r => !r.pass);
console.log('\n第四章 矛盾地图 · CK-6 验收  [' + path.basename(path.dirname(modelPath)) + ']');
console.log('─'.repeat(64));
results.forEach(r => console.log((r.pass ? ' ✓ ' : ' ✗ ') + r.name.padEnd(34) + (r.detail || '')));
console.log('─'.repeat(64));
console.log(fail.length ? ('✗ ' + fail.length + '/' + results.length + ' 项不过') : ('✓ 全部 ' + results.length + ' 项通过'));
process.exit(fail.length ? 1 : 0);
