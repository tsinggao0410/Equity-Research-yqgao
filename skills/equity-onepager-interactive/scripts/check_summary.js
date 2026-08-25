#!/usr/bin/env node
/* =============================================================================
 * check_summary.js — 开篇章「一段话说清楚」CK-7 契约闸（headless，独立于第四章）
 * 规范：references/10-summary-backsolve.md §7（项号 a1…h1 与本文件一一对应）
 * 钩子登记表：scripts/summary_hooks.json（10 §2 的机器版）
 *
 *   node check_summary.js --model <page_model.json> [--json]     退出码 0＝全过
 *   node check_summary.js --hooks                                打印钩子登记表
 *
 * 为什么独立一个文件：check_part4.js 在 part4 缺失时整份提前退出（第四章允许不出），
 * 开篇章的闸挂在那里等于被第四章的存在与否挟持。
 *
 * 为什么按登记表查覆盖：company_type 的 k 列是提问框架不是排版。散文块或漏钩子在机器看来
 * 与写全一模一样，退化是静默的（2026-08-14 阳光 v3.1：(k,v) 14→0 而旧闸放行）。
 * points[].hook 填登记表 id 时按 id 查；没填时用 k_re 对 k 回退匹配，旧 page_model 不用改。
 * ========================================================================== */
'use strict';
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const HOOKS = JSON.parse(fs.readFileSync(path.join(__dirname, 'summary_hooks.json'), 'utf8'));

if (args.includes('--hooks')) {
  console.log(`开篇章钩子登记表 · ${HOOKS.version} · ${HOOKS.doc}`);
  HOOKS.blocks.forEach(b => {
    console.log(`\n【${b.name}】`);
    b.hooks.forEach(h => {
      const lvl = h.must ? '必答' : (h.must_when ? `条件必答(${h.must_when})` : '选答');
      console.log(`  ${h.id.padEnd(20)} ${lvl.padEnd(28)} ${h.ask}`);
      console.log(`  ${''.padEnd(20)} ↳ 去哪挖：${h.where}`);
    });
  });
  console.log('\n【第二点 pillars 链】');
  (HOOKS.pillars_chain.hooks || []).forEach(h => console.log(`  ${h.id.padEnd(20)} ${h.ask}`));
  process.exit(0);
}

const mi = args.indexOf('--model');
if (mi < 0 || !args[mi + 1]) { console.error('usage: node check_summary.js --model <page_model.json> [--json] | --hooks'); process.exit(2); }
const D = JSON.parse(fs.readFileSync(args[mi + 1], 'utf8'));
const SUM = D.summary || {};
const META = D.meta || {};
const asJson = args.includes('--json');

const R = [];
const chk = (id, pass, name, detail) => R.push({ id, pass: !!pass, name, detail: detail || '' });
const txt = s => String(s == null ? '' : s).replace(/<[^>]+>/g, '');
const TAGS = ['FACT', 'EST', 'DNA'];
const NUMS = t => (String(t).match(/[\d][\d,]*(?:\.\d+)?/g) || []).length;

/* ------------------------------ a · thesis ---------------------------------- */
const th = txt(SUM.thesis);
chk('a1', !!th && th.length <= 30, 'a1 thesis 非空且 ≤30 字', th ? `${th.length} 字：${th}` : '缺 summary.thesis');

/* ------------------- b · company_type ＝ 钩子体系（本闸的重点）------------------ */
const CT = SUM.company_type || [];
chk('b1', CT.length === 3, 'b1 company_type 恰好 3 块', `${CT.length} 块`);
const legacy = CT.filter(c => !c.points && (c.label || c.note));
chk('b1', CT.length > 0 && !legacy.length, 'b1 新契约 {title,points[]}（旧 {label,note} 已废弃）',
  legacy.length ? `${legacy.length}/${CT.length} 块是散文块——k 列提问框架、FACT/EST/DNA、ev 三层一起没了（10 §2.2）` : (CT.length ? 'ok' : '无'));

// 块 ↔ 登记表：先按 title 正则，再按顺序兜底
const blockOf = (c, i) => {
  const t = txt(c.title || c.label);
  const hit = HOOKS.blocks.find(b => new RegExp(b.title_re).test(t));
  return hit || HOOKS.blocks[i] || null;
};
const mapped = CT.map((c, i) => ({ c, reg: blockOf(c, i) }));
const seen = new Set(mapped.map(m => m.reg && m.reg.id).filter(Boolean));
const missBlk = HOOKS.blocks.filter(b => !seen.has(b.id)).map(b => b.name);
chk('b2', CT.length === 3 && !missBlk.length, 'b2 三块覆盖 生意本身/盘子/股性', missBlk.length ? `缺 ${missBlk.join('、')}` : 'ok');
const weakTitle = mapped.filter(m => {
  const t = txt(m.c.title || m.c.label || '');
  const body = t.replace(/^(生意本身|盘子|股性|一|二|三|①|②|③|[123][.、])*[：:·\s—-]*/, '');
  return body.length < 6;
});
chk('b2', CT.length > 0 && !weakTitle.length, 'b2 每块 title 是结论句（冒号后 ≥6 字）',
  weakTitle.length ? weakTitle.map(m => `「${txt(m.c.title || m.c.label)}」`).join(' ') + '——只读 title 拿不走结论' : 'ok');

// 条件必答的判定条件
const nPh = ((D.part2 || {}).phases || []).length;
const mfCounts = {};
((D.part2 || {}).phases || []).forEach(p => { if (p.main_factor) mfCounts[p.main_factor] = (mfCounts[p.main_factor] || 0) + 1; });
const mfMode = Object.entries(mfCounts).sort((a, b) => b[1] - a[1])[0];
const COND = {
  market_A: String(META.market || '').toUpperCase() === 'A',
  has_narrative_capacity: !!(((D.part1 || {}).narrative_capacity || {}).baskets || []).length,
  phases_same_factor: !!(mfMode && nPh >= 3 && mfMode[1] / nPh >= 2 / 3),
};
const isMust = h => h.must === true || (h.must_when && COND[h.must_when]);

// 覆盖：hook id 优先，缺则 k 关键词回退
const covered = (h, pts) => pts.some(p => p.hook === h.id) || pts.some(p => p.k && new RegExp(h.k_re).test(txt(p.k)));
const missing = [], optionalHit = [];
mapped.forEach(m => {
  if (!m.reg) return;
  const pts = m.c.points || [];
  m.reg.hooks.forEach(h => {
    const ok = covered(h, pts);
    if (isMust(h) && !ok) missing.push(`${m.reg.name}.${h.id}(${h.k})`);
    if (!isMust(h) && ok) optionalHit.push(h.id);
  });
});
const condNote = Object.entries(COND).filter(([, v]) => v).map(([k]) => k).join('/') || '无';
chk('b3', CT.length === 3 && !missing.length, 'b3 必答钩子逐条覆盖（hook id 或 k 关键词）',
  missing.length ? `缺 ${missing.length} 条：${missing.join('；')}` : `全覆盖；条件必答已激活：${condNote}；选答命中：${optionalHit.join(',') || '无'}`);
const noHookId = CT.flatMap(c => c.points || []).filter(p => !p.hook).length;
if (noHookId) R.push({ id: 'b3', pass: true, name: 'b3 (提示) points[].hook 未填', detail: `${noHookId} 条按 k 关键词回退匹配；新报告建议填 hook id，见 10 §2.2` });

const pts = CT.flatMap(c => c.points || []);
const badKV = pts.filter(p => !p.k || !p.v || txt(p.v).length < 15);
chk('b4', pts.length > 0 && !badKV.length, 'b4 每子项 k/v 齐且 v ≥15 字',
  !pts.length ? '一个子项都没有' : (badKV.map(p => p.k || '(无k)').join(',') || `${pts.length} 项齐`));
const badTag = pts.filter(p => !TAGS.includes(p.tag));
chk('b4', pts.length > 0 && !badTag.length, 'b4 每子项 tag ∈ FACT/EST/DNA',
  !pts.length ? '一个子项都没有' : (badTag.length ? `${badTag.length}/${pts.length} 项未分层` : 'ok'));
const nDna = pts.filter(p => p.tag === 'DNA').length, nEv = pts.filter(p => (p.ev || []).length).length;
chk('b5', nDna >= 2, 'b5 全章 ≥2 个 DNA 子项', `DNA ${nDna} 项${nDna < 2 ? '——纯 FACT 堆砌＝只搬数字没写 knowhow' : ''}`);
chk('b5', nEv >= 1, 'b5 ≥1 个子项挂 ev 原句', `${nEv} 项挂了 ev`);

// b6/b7：两条分类判定必须落成判定句（不是出现关键词就算）
const blkText = id => {
  const m = mapped.find(x => x.reg && x.reg.id === id);
  if (!m) return '';
  return [txt(m.c.title || m.c.label), txt(m.c.verdict), (m.c.points || []).map(p => txt(p.k) + ' ' + txt(p.v)).join(' ')].join(' ');
};
const hookDef = (bid, hid) => (HOOKS.blocks.find(b => b.id === bid) || { hooks: [] }).hooks.find(h => h.id === hid);
const cyc = hookDef('biz', 'cycle_or_growth'), bizT = blkText('biz');
const hasCyc = cyc && new RegExp(cyc.v_re).test(bizT);
chk('b6', hasCyc, 'b6 cycle_or_growth 落成判定句（收入/利润曲线分开、决定用哪把尺子）',
  hasCyc ? '已落成判定句' : (/周期|成长/.test(bizT) ? '出现了词但没落成判定句' : '生意本身块未出现周期/成长判定'));
const bk = hookDef('trade', 'beta_kind'), tradeT = blkText('trade');
const hasBeta = bk && /[βΒ]|beta/i.test(tradeT) && new RegExp(bk.v_re, 'i').test(tradeT);
chk('b7', hasBeta, 'b7 beta_kind 落成判定句（真β/假β/σ + 推论）',
  hasBeta ? '已落成判定句' : (/[βΒ]|beta/i.test(tradeT) ? '提到 β 但没判真/假/σ' : '股性块未出现 β/σ 判定'));

/* b9 · 密度：少而狠（10 §2.2）。这一章是要念出来的：8/8 华创 14 条约 2,300 字、用户原稿约 1,600 字都能讲清，
   24 条 4,400 字就不是「一段话」了。深度不是删掉，是下沉到第三章；开篇只留结论 + 关键数字 + 「所以你会怎么看错」。 */
const vlen = p => txt(p.v).replace(/\*\*/g, '').length;
const capOf = p => (p.tag === 'FACT' ? 110 : 165);   // 规范 100/150，闸门按 +10% 容差拦（10 §2.2）
const longV = pts.filter(p => vlen(p) > capOf(p));
chk('b9', pts.length > 0 && !longV.length, 'b9 每条 v 只说一件事：FACT ≤100 字 / EST·DNA ≤150 字（容差 +10%）',
  longV.length ? `${longV.length}/${pts.length} 条超长：${longV.slice(0, 5).map(p => `${p.hook || p.k}(${vlen(p)}字/${p.tag || '?'})`).join('、')}${longV.length > 5 ? '…' : ''}——拆成一件事一条，或把细节下沉到第三章` : `${pts.length} 条齐`);
const totalV = pts.reduce((a, p) => a + vlen(p), 0);
chk('b9', totalV > 0 && totalV <= 4000, 'b9 三块 v 合计 ≤4,000 字（目标 ≤3,000）',
  `${totalV} 字` + (totalV > 4000 ? '——念不出来的不是「一段话」' : (totalV > 3000 ? '（已过硬上限以内，但超过 3,000 目标，建议再压）' : '')));
// 选答每块 ≤2 条：不属于任何必答钩子的子项算「额外」；有 hook id 按 id 判，没有按 k 关键词判
const extraPer = mapped.map(m => {
  if (!m.reg) return null;
  const musts = m.reg.hooks.filter(isMust);
  const optIds = new Set(m.reg.hooks.filter(h => !isMust(h)).map(h => h.id));
  const isMustPt = p => p.hook ? musts.some(h => h.id === p.hook) : musts.some(h => p.k && new RegExp(h.k_re).test(txt(p.k)));
  const extra = (m.c.points || []).filter(p => !isMustPt(p));
  return { name: m.reg.name, n: extra.length, ids: extra.map(p => p.hook || p.k) };
}).filter(Boolean);
const overOpt = extraPer.filter(x => x.n > 2);
chk('b9', !overOpt.length, 'b9 选答每块 ≤2 条（必答之外的子项）',
  overOpt.length ? overOpt.map(x => `${x.name} ${x.n} 条：${x.ids.slice(0, 5).join('/')}`).join('；') + '——挑最狠的两条，其余下沉' : extraPer.map(x => `${x.name} ${x.n}`).join(' · '));

/* ------------------------------ c · pillars -------------------------------- */
const PL = SUM.pillars || [];
const plPts = PL.flatMap(p => p.points || []);
const plText = p => txt(p && typeof p === 'object' ? (p.claim || p.v || p.text || '') : p);
const keys = new Set(PL.map(p => String(p.key || '')));
const needKeys = ['demand', 'supply', 'company'].filter(k => !keys.has(k));
chk('c1', PL.length >= 3 && !needKeys.length, 'c1 pillars ≥3 组且覆盖 demand/supply/company',
  `${PL.length} 组` + (needKeys.length ? `，缺 key：${needKeys.join(',')}` : ''));
const plNoNum = plPts.filter(p => !/\d/.test(plText(p)));
const plNoTag = plPts.filter(p => !TAGS.includes(p && p.tag));
chk('c1', plPts.length > 0 && !plNoNum.length && !plNoTag.length, 'c1 每条 pillar point 带数字 + tag',
  !plPts.length ? '一个 point 都没有' : `${plPts.length} 条；无数字 ${plNoNum.length}，未分层 ${plNoTag.length}`);

const plTexts = [];
PL.forEach(x => {
  (x.points || []).forEach(p => { plTexts.push(plText(p)); (p.subs || []).forEach(s => plTexts.push(plText(s))); });
  (x.subs || []).forEach(s => {
    if (s && typeof s === 'object' && s.points) { plTexts.push(txt(s.name)); (s.points || []).forEach(p => plTexts.push(plText(p))); }
    else plTexts.push(plText(s));
  });
});
const nSubs = PL.reduce((a, x) => a + (x.subs || []).length + (x.points || []).reduce((b, p) => b + ((p.subs || []).length ? 1 : 0), 0), 0);
const calc = plTexts.filter(t => /[×÷x*/]/.test(t) && /[=＝]/.test(t) && NUMS(t) >= 3);
const bind = plTexts.filter(t => /min\(|打满|顶死|上限|瓶颈|受限于|封顶|卡在|天花板/.test(t));
const xchk = plTexts.filter(t => /互证|交叉验证|反推.{0,24}与|差\s*<\s*\d|对得上|两条.{0,8}路径|口径.{0,4}互/.test(t));
chk('c2', calc.length >= 1, 'c2 ≥1 条显式算式把行业盘推成公司自己的数',
  calc.length ? `${calc.length} 条：${calc[0].slice(0, 46)}…` : '全是并列事实，没有一条把行业盘推成本公司的量——这一章成了行业简报（10 §3）');
chk('c3', bind.length >= 1, 'c3 说出这条链撞上的约束（上限/打满/瓶颈）',
  bind.length ? `${bind.length} 条：${bind[0].slice(0, 46)}…` : '没说什么会让这条链封顶');
chk('c4', nSubs >= 1 || xchk.length >= 1, 'c4 ≥1 层深度（subs 下钻 或 两路径互证）',
  `subs ${nSubs} 处 · 互证 ${xchk.length} 处${nSubs || xchk.length ? '' : '——全是一层平铺'}`);
const weakest = (((D.part4 || {}).narratives) || []).filter(n => n && n.weakest).length;
const plAll = plTexts.join(' ') + ' ' + txt(SUM.thesis);
if (weakest) {
  const said = /最先断|先断|断在|最先失效|最脆|最先被打破|第\s*\d+\s*环/.test(plAll);
  chk('c5', said, 'c5 pillars 点名了主叙事「最先断的一环」（part4.narratives[].weakest 已算出）',
    said ? 'ok' : `第四章有 ${weakest} 条 weakest，开篇没搬——烂在图里`);
} else chk('c5', true, 'c5 最先断的一环', '第四章无 narratives.weakest，跳过');

/* ----------------------------- d · accounting ------------------------------ */
const A = SUM.accounting || {};
const ms = A.mcap_split || [];
// 差额行＝「现市值 − 可解释部分」那一行：超出/多给/缺口/残值/减去…——没有它，第三点只是把第三章估值抄了一遍
const gapRow = ms.some(m => /超出|多给|未解释|解释不了|溢价|折价|剩余|差额|多出|少给|缺口|残值|减去|没有为|实际给|真正要解释/.test(txt(m.part) + ' ' + txt(m.basis)));
chk('d1', ms.length >= 3 && gapRow, 'd1 mcap_split ≥3 行且有一行「超出 SOTP / 多给的部分」',
  `${ms.length} 行` + (gapRow ? '，含差额行' : '，缺「多给的这部分才是要解释的」那一行'));
const steps = A.steps || (A.scenarios ? [{ name: '情景分档', scenarios: A.scenarios }] : []);
const scs = steps.flatMap(s => s.scenarios || []);
const tri = steps.some(s => (s.scenarios || []).length >= 3 && (s.scenarios || []).every(x => x.driver && txt(x.driver).length >= 8));
chk('d1', steps.length >= 1 && tri, 'd1 steps ≥1 步且某步含三档 scenarios 各带 driver',
  `${steps.length} 步 · ${scs.length} 档` + (tri ? '' : '——缺三档或 driver 没写怎么算出来的'));
const concl = txt(A.conclusion);
chk('d2', concl.length >= 40, 'd2 conclusion ≥40 字给市值空间', concl.slice(0, 50) || '缺');
const pa = txt(A.price_assumes);
const paLegacy = !pa && /既成事实|已经计入|已经反映|当成|price.?in|隐含|默认了|定价的是/.test(concl);
chk('d2', pa.length >= 8 || paLegacy, 'd2 price_assumes 非空（现价把什么当成了既成事实）',
  pa ? pa.slice(0, 60) : (paLegacy ? '（旧模型）从 conclusion 里读出了「现价把…当成既成事实」，建议拆成 price_assumes 字段' : '缺——读者不知道自己在赌哪几件事'));
const badStake = scs.filter(s => s.stake != null && !isFinite(parseFloat(s.stake)));
chk('d3', !badStake.length, 'd3 stake 是数字（持股比例），分段标签走 segment',
  badStake.length ? `${badStake.length}/${scs.length} 条是字符串（${[...new Set(badStake.map(s => JSON.stringify(s.stake)))].slice(0, 3).join('/')}）——页面渲「持股 —」` : `${scs.length} 条齐`);
const noAttrib = scs.filter(s => s.attrib_yi == null && !isFinite(parseFloat(s.stake)));
chk('d3', !noAttrib.length, 'd3 attrib_yi 缺省时 stake 必须可乘', noAttrib.length ? `${noAttrib.length} 条既无 attrib_yi 又无数字 stake` : 'ok');

/* ------------------------------ e · backsolve ------------------------------ */
const B = SUM.backsolve || {};
chk('e1', !!B.anchor_pe && txt(B.anchor_pe_basis).length >= 20, 'e1 anchor_pe 已填且 anchor_pe_basis ≥20 字',
  `${B.anchor_pe ? B.anchor_pe + '×' : '缺 anchor_pe'}；basis ${txt(B.anchor_pe_basis).length} 字`);
const r = Number(B.r == null ? 0.09 : B.r);
chk('e1', isFinite(r) && r >= 0.08 && r <= 0.10, 'e1 折现率 r ∈ [0.08,0.10]', isFinite(r) ? String(r) : '缺');
chk('e1', !/落点被截/.test(String(B.anchor_pe_basis || '')), 'e1 anchor_pe_basis 无「落点被截」手写找补', /落点被截/.test(String(B.anchor_pe_basis || '')) ? '引擎已支持 inHist，删掉这段（10 §5.1）' : 'ok');
const lad = B.ladder || [];
const badTier = lad.filter(x => !(Number(x.tier) >= 1 && Number(x.tier) <= 5));
chk('e2', lad.length >= 4 && !badTier.length, 'e2 ladder ≥4 档且 tier 1–5 齐（五档估值等级）',
  `${lad.length} 档` + (badTier.length ? `，${badTier.length} 档缺 tier：${badTier.map(x => x.key).join(',')}` : ''));
chk('e2', lad.some(x => x.current), 'e2 ladder 已标 current', lad.filter(x => x.current).map(x => x.key).join(',') || '无');
const needIf = lad.filter(x => !x.current && x.status !== '成立' && x.mcap_if_yi == null);
chk('e2', !needIf.length, 'e2 前提未成立的档填了 mcap_if_yi', needIf.map(x => x.key).join(',') || 'ok');

/* ------------------------------ f · switches ------------------------------- */
const sw = B.switches || [];
const four = sw.filter(x => !(x.catalyst && x.watch && x.when && x.elasticity));
const down = sw.some(x => /向下|下行|降档|跌|失效/.test(JSON.stringify(x)) || x.kill);
chk('f1', sw.length >= 2 && !four.length && down, 'f1 switches ≥2 条、四格齐、≥1 条向下',
  `${sw.length} 条；四格不齐 ${four.length}；${down ? '有向下' : '只有升档路径'}`);
const swBadP = sw.filter(x => !isFinite(Number(x.prob)) || Number(x.prob) <= 0 || Number(x.prob) > 1);
chk('f2', sw.length > 0 && !swBadP.length, 'f2 每条 switch 的 prob ∈ (0,1]',
  !sw.length ? '没有 switches' : (swBadP.length ? `${swBadP.length}/${sw.length} 条是占位符或越界（如 '—'）` : `${sw.length} 条齐`));
const cases = (((D.part4 || {}).scenarios) || {}).items || [];
const upP = cases.filter(c => c.dir !== 'down' && isFinite(Number(c.prob))).reduce((a, c) => a + Number(c.prob), 0);
const swUp = sw.filter(x => !/向下|下行|降档|跌/.test(JSON.stringify(x)) && isFinite(Number(x.prob)));
const swUpP = swUp.reduce((a, x) => a + Number(x.prob), 0);
if (cases.length && upP > 0 && swUp.length) {
  const gap = Math.abs(swUpP - upP) * 100;
  chk('f3', gap <= 10, 'f3 升档 switch 概率合计 ≈ 第四章上行 Case 概率合计（±10pp）',
    `switches 升档 ${(swUpP * 100).toFixed(0)}% vs 上行 Case ${(upP * 100).toFixed(0)}%，差 ${gap.toFixed(0)}pp` + (gap > 10 ? '——同一件事两处各说各的' : ''));
} else chk('f3', true, 'f3 升档 switch 概率对第四章上行 Case', !cases.length ? '第四章无 scenarios，跳过' : '两侧概率不全，跳过');

/* --------------------------- g · main_scenario ----------------------------- */
if (cases.length) {
  const ok = cases.some(c => c.key === SUM.main_scenario);
  chk('g', ok, 'g main_scenario 对上 part4.scenarios.items[].key', ok ? String(SUM.main_scenario) : `summary.main_scenario=${JSON.stringify(SUM.main_scenario)}，可选：${cases.map(c => c.key).join(',')}`);
} else chk('g', true, 'g main_scenario', '第四章无 scenarios，跳过');

/* ------------------ t · 概览类型卡（2026-08-17 石英股份读者反馈，10 §2.8）------------------
   类型（真β/假β/σ/叙事-题材）+ 类型对应的核心参数：β 类＝核心叙事线+定位+K 线方位；σ 类＝预期利润率/ROE/PE/PS/PB 分位。
   数据层 scripts/type_card.py 从 1.7/1.3/1.4/1.5/2.1b 合成；type 作者定，且要与股性块 beta_kind 说同一句话。 */
const TC = SUM.type_card;
const TCT = ['真β', '假β', 'σ', '叙事-题材'];
chk('t1', !!TC && TCT.includes(TC.type), 't1 type_card 已填且 type ∈ 真β/假β/σ/叙事-题材',
  !TC ? '缺 summary.type_card（跑 scripts/type_card.py --write 后作者填 type）' : (TCT.includes(TC.type) ? `type=${TC.type}` : `type=${JSON.stringify(TC.type)} 不合法（脚本建议 ${TC.suggest || '—'}）`));
if (TC && TCT.includes(TC.type)) {
  const isB = TC.type !== 'σ';
  const B = TC.beta || {}, lines = (TC.core_lines && TC.core_lines.length) ? TC.core_lines : (B.lines || []);
  const S = TC.sigma || {};
  const okB = lines.length >= 1 && lines.some(l => l.tier) && !!((B.posture || {}).label);
  const okS = !!(S.nm && (S.nm.pct_fwd != null || S.nm.pct_ttm != null || S.nm.pct_now != null)) && !!(S.roe && S.roe.pct != null)
    && ['pe', 'ps', 'pb'].some(k => S[k] && S[k].pct != null);
  chk('t1', isB ? okB : okS, isB ? 't1 β 类：核心叙事线(≥1 条带定位) + K 线方位 已给' : 't1 σ 类：预期利润率/ROE 历史分位 + PE/PS/PB 分位 已给',
    isB ? `叙事线 ${lines.length} 条，定位 ${lines.filter(l => l.tier).length} 条，方位 ${(B.posture || {}).label || '缺'}`
        : `净利率分位 ${(S.nm || {}).pct_fwd ?? (S.nm || {}).pct_ttm ?? '缺'} · ROE 分位 ${(S.roe || {}).pct ?? '缺'} · PE/PS/PB 分位 ${['pe', 'ps', 'pb'].map(k => (S[k] || {}).pct ?? '—').join('/')}`
        + ((TC.gaps || []).length ? `；缺口：${TC.gaps.join('；')}` : ''));
  chk('t1', !!(TC.verdict && txt(TC.verdict).length >= 10), 't1 type_card.verdict ≥10 字（一句话：这类票该怎么拿）', txt(TC.verdict || '').slice(0, 60) || '缺——只给类型不给拿法，读者拿到的是标签');
  const typeRe = TC.type === '叙事-题材' ? /题材|叙事/ : new RegExp(TC.type.replace('β', '\\s*[βΒ]'));
  chk('t2', typeRe.test(tradeT), 't2 type_card.type 与股性块 beta_kind 判定一致（同一个词出现在股性块）',
    typeRe.test(tradeT) ? 'ok' : `股性块里没出现「${TC.type}」——概览类型卡与开篇股性两处不许各说各的`);
}

/* --------------------- h · 内部叫法 / 脚手架语句（用户可见文本） -------------------- */
const visible = [];
(function walk(o, k) {
  if (o == null) return;
  if (typeof o === 'string') { if (!/^(note|hook|key|tag|ev|id|src|doc_id|cite)$/.test(k || '')) visible.push(o); return; }
  if (Array.isArray(o)) return o.forEach(x => walk(x, k));
  if (typeof o === 'object') Object.keys(o).forEach(kk => walk(o[kk], kk));
})(SUM, '');
const vis = visible.join('\n');
chk('h1', !/反算/.test(vis), 'h1 用户可见文本无「反算」', /反算/.test(vis) ? '出现「反算」——内部叫法不外泄，用 利润兑现期限/估值范式上界/潜在催化' : 'ok');
const scaf = /申万|通行分层|个交易日|本模型|本案|本页|本表|见第[一二三四]章|实跑|不手估|拖动.*滑块/g;
const scafHits = vis.match(scaf) || [];
chk('h1', !scafHits.length, 'h1 无脚手架语句（分类注解/口径解释/样本窗口/内部交叉引用/UI 自指）',
  scafHits.length ? `${scafHits.length} 处：${[...new Set(scafHits)].slice(0, 6).join(' / ')}（10 §6.5）` : 'ok');

/* --------------------------------- 输出 ------------------------------------ */
const bad = R.filter(x => !x.pass).length;
if (asJson) {
  console.log(JSON.stringify({ total: R.length, failed: bad, cond: COND, items: R }, null, 1));
} else {
  console.log(`开篇章「一段话说清楚」· CK-7 契约闸（10 §7）· 钩子表 ${HOOKS.version}`);
  console.log('─'.repeat(78));
  R.forEach(x => console.log(` ${x.pass ? '✓' : '✗'} ${x.name.padEnd(52)} ${x.detail}`));
  console.log('─'.repeat(78));
  console.log(bad ? `✗ ${bad}/${R.length} 项不过` : `✓ 全部 ${R.length} 项通过`);
}
process.exit(bad ? 1 : 0);
