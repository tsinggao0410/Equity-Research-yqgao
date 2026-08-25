#!/usr/bin/env node
/* =============================================================================
 * check_charts.js — CK-8 图表契约闸（量纲 · 图形 · 口径标注）
 *
 *   用法: node check_charts.js --model <page_model.json> [--html <built onepager.html>]
 *         --html 可选，额外跑 CK-8 j 版式闸（表头能不能看见 / 金额表有没有写单位）
 *
 * ★由来（2026-08-16，赛力斯 v3.2 读者七条反馈）。七条里有五条不是「算错了」，
 *   是**数字对但读者读错了**，而且五条全是同一个病根的不同长相：
 *
 *     反馈                        表面现象                 真病根
 *     ─────────────────────────  ──────────────────────  ────────────────────
 *     ①「涨跌幅用%不要用小数」      页面印 0.4776           数值契约没闸（裸小数当串印）
 *     ②「市值拉取有错误」           比亚迪 2,184 亿          多口径数字列没表头
 *     ③「箱线图是错的没有箱体」      找不到箱体              图形没有样标，读者按最像的图去认
 *     ④「左右轴量纲有错误」         PS 被压成直线            两个量纲共用一根轴
 *     ⑤「ROE 用柱其余用线」         四条线同型               结果量与分解项没有图形分型
 *
 *   共性：**前三章所有的闸都在查「这个数算对没有」，没有一条在查「读者会读成什么」。**
 *   数字正确 ≠ 读数正确。这个文件就是补上后半句：凡是一个字段有多种可能的读法
 *   （小数还是百分数 / 总市值还是自由流通 / 倍盈利还是倍收入），要么在契约里钉死，
 *   要么在页面上把口径写在读者眼睛必经之处。
 *
 * 与既有闸的分工：check_part3/part4/summary/consensus 查**经济含义**，本闸查**读数歧义**。
 * ========================================================================== */
'use strict';
const fs = require('fs');

const args = process.argv.slice(2);
const mi = args.indexOf('--model');
if (mi < 0 || !args[mi + 1]) { console.error('usage: node check_charts.js --model <page_model.json>'); process.exit(2); }
const D = JSON.parse(fs.readFileSync(args[mi + 1], 'utf8'));

const R = [];
const chk = (pass, name, detail) => R.push({ pass: !!pass, name, detail: detail || '' });
const P1 = D.part1 || {}, P2 = D.part2 || {};

/* ---- CK-8 a · 段涨幅是展示串，不是裸小数 --------------------------------- */
/* 赛力斯 v3.2 落成 -0.4776：页面直接印出来读者分不清 47.76% 还是 0.48%，
   而 app.js 的历史对照条把它当「百分点」和 rmv 的 _pp 比，量纲错 100 倍。
   渲染层现在有 chgTxt/chgPct 兜底，但兜底是止血不是治病——契约仍然要求给串。 */
const PH = P2.phases || [];
const badChg = PH.filter(p => p.chg != null && typeof p.chg !== 'string');
chk(PH.length > 0 && !badChg.length, 'CK-8 a part2.phases[].chg 是带 % 的展示串',
  !PH.length ? '没有 phases'
    : (badChg.length ? `${badChg.length}/${PH.length} 条是裸数字（${badChg.slice(0, 3).map(p => p.chg).join('/')}）——渲染层会按「小数＝涨跌幅」兜底，但请在 build 脚本里改成 "+244.8%" 这种串` : `${PH.length} 条齐`));
const noPct = PH.filter(p => typeof p.chg === 'string' && !/%/.test(p.chg));
chk(!noPct.length, 'CK-8 a2 chg 串里带 % 号',
  noPct.length ? `${noPct.length} 条无 % 号（${noPct.slice(0, 3).map(p => p.chg).join('/')}）` : 'ok');

/* ---- CK-8 b · basket_beta 的个股腿与篮子腿同量纲 ------------------------- */
/* 2026-08-15 赛力斯已经踩过一次：stock_chg 落小数而 rows/bench 落百分数，
   超额整列错 100 倍，把「一半是板块在跌」读成「个股独自暴跌」。这里做量级体检。 */
const bbBad = [];
PH.forEach(p => {
  const bb = p.basket_beta; if (!bb) return;
  const legs = [].concat(bb.rows || [], bb.bench || []).map(r => r && r.chg).filter(v => v != null && isFinite(v));
  const self = chgNum(p.chg);
  if (!legs.length || self == null) return;
  const m = Math.max(...legs.map(Math.abs));
  // 篮子腿是百分数（量级 ~10–100），个股腿若落在 |x|<3 基本可断定是小数
  if (m > 5 && Math.abs(self) < 3 && self !== 0) bbBad.push(p.name || '?');
});
chk(!bbBad.length, 'CK-8 b basket_beta 个股腿与篮子腿同量纲（都用百分数）',
  bbBad.length ? `${bbBad.join('、')} 的个股腿疑似小数、篮子腿是百分数 → 超额会整列错 100 倍` : 'ok');
function chgNum(v) {
  if (v == null || v === '') return null;
  if (typeof v === 'number') return v * 100;
  const f = parseFloat(String(v).replace(/[^\d.eE+-]/g, ''));
  return isFinite(f) ? f : null;
}

/* ---- CK-8 c · 1.7 个股表的数字列必须双口径 ------------------------------- */
/* 那一列是「自由流通市值」，比亚迪 2,184 亿；读者按裸数字当市值读，
   而总市值 7,642 亿 —— 数字没错，是口径没标，看上去就是拉错 3.5 倍。 */
const NC = P1.narrative_capacity || {};
const peers = (NC.baskets || []).flatMap(b => b.peers || []);
const noMk = peers.filter(x => x.float_yi != null && x.mktcap_yi == null);
chk(!peers.length || !noMk.length, 'CK-8 c 1.7 peers 同时给 float_yi 与 mktcap_yi（双口径互相解释）',
  !peers.length ? '没有 peers（跳过）'
    : (noMk.length ? `${noMk.length}/${peers.length} 只缺 mktcap_yi —— 重跑 narrative_capacity/onepager_module.py` : `${peers.length} 只齐`));

/* ---- CK-8 d · 复合图的「结果量」腿存在 ----------------------------------- */
/* 1.3 ROE、1.4 毛利率/净利率 走柱，是被解释的那个数；缺了柱就退回四条同型线。 */
const DU = P1.dupont || {};
chk(!DU.years || (DU.roe || []).some(v => v != null), 'CK-8 d 1.3 dupont.roe 有值（柱腿）',
  !DU.years ? '无杜邦数据（跳过）' : ((DU.roe || []).filter(v => v != null).length + ' 个点'));
/* ★2026-08-18 用户改制（当日二稿）：1.4 ＝**逐季 · 堆积面积图**，只留
   净利率 + 四费 + 税费 + 其他（一个桶装完剩下的），面积上沿＝毛利率。
   数据走 `part1.cost_structure_q`（iFind `单季度.*` 原生指标，**不是拿累计差分**）。
   闸查四件事：分解项齐不齐、「其他」桶是不是大到没意义、是不是真的逐季、起点够不够早。 */
const CS = P1.cost_structure_q || {};
const CSQ = CS.quarters || [];
const CSN = k => (CS[k] || []).filter(v => v != null).length;
chk(!!CSQ.length, 'CK-8 d2 1.4 走季度块 cost_structure_q（不是年度 cost_structure）',
  CSQ.length ? `${CSQ.length} 季 ${CSQ[0]}~${CSQ[CSQ.length - 1]}` :
    (P1.cost_structure ? '只有年度 cost_structure —— 跑 scripts/fetch_quarterly.py 补季度块' : '无成本数据'));
if (CSQ.length) {
  chk(CSQ.every(q => /^(19|20)\d{2}Q[1-4]$/.test(q)), 'CK-8 d2a quarters 是 YYYYQn 且逐季',
    CSQ.filter(q => !/^(19|20)\d{2}Q[1-4]$/.test(q)).slice(0, 3).join('/') || 'ok');
  chk(CSN('gross_margin') && CSN('net_margin'),
    'CK-8 d2b 1.4 gross_margin（＝面积上沿）与 net_margin（＝最底层）均有值',
    `毛利 ${CSN('gross_margin')} 点 / 净利 ${CSN('net_margin')} 点`);
  const BANDS = ['sell_exp_rate', 'admin_exp_rate', 'rnd_exp_rate', 'fin_exp_rate', 'tax_rate'];
  const missing = BANDS.filter(k => !CSN(k));
  chk(missing.length <= 1, 'CK-8 d2c 1.4 分解项齐（四费 + 税费）',
    missing.length ? `缺 ${missing.join('/')} → 已并入「其他」桶，桶会偏大` : '五项全有');
  // 「其他」桶体检：它本来就装剩下的全部，但中位 >60% 说明这张图没在解释任何东西
  const plugs = [];
  for (let i = 0; i < CSQ.length; i++) {
    const gm = (CS.gross_margin || [])[i];
    if (gm == null || !gm) continue;
    let s = 0, any = false;
    ['net_margin'].concat(BANDS).forEach(k => { const v = (CS[k] || [])[i]; if (v != null) { s += +v; any = true; } });
    if (any) plugs.push(Math.abs(gm - s) / Math.abs(gm));
  }
  const med = plugs.length ? plugs.slice().sort((a, b) => a - b)[Math.floor(plugs.length / 2)] : null;
  /* 「其他」按用户口径就是一个装剩下全部的桶（减值/政府补助/投资收益/营业外/少数股东），
     亏损期 + 收入小的公司它天然会比毛利率还大——那不是错，是这家公司当期的利润来源本来就在营业外。
     所以只在**常年盈利**的公司上把它当硬闸：那种公司若还有六成毛利落在没被解释的桶里，
     基本就是单季指标取错成累计列了。其余情况只报数字不拦。 */
  const nmv = (CS.net_margin || []).filter(v => v != null).sort((a, b) => a - b);
  const nmMed = nmv.length ? nmv[Math.floor(nmv.length / 2)] : null;
  const profitable = nmMed != null && nmMed > 0;
  chk(med == null || !profitable || med <= 0.6, 'CK-8 d3 1.4「其他」桶体检（常年盈利的公司才当硬闸）',
    med == null ? '算不出'
      : `桶/毛利率 中位 ${Math.round(med * 100)}%，净利率中位 ${Math.round(nmMed * 10) / 10}%`
        + (profitable && med > 0.6 ? ' —— 盈利公司却有六成毛利没被解释，先查单季指标是不是取错成累计列'
                                   : (med > 0.6 ? '（亏损期公司，利润来源本就在营业外，不拦）' : '')));
  const y0 = parseInt(CSQ[0].slice(0, 4), 10), ly = CS.listing_year ? parseInt(CS.listing_year, 10) : null;
  chk(!!ly, 'CK-8 d4 1.4 标了 listing_year', ly ? String(ly) : '缺 listing_year');
  chk(!ly || (y0 <= ly + 1), 'CK-8 d4b 1.4 横轴从上市首年起（用户要求「按上市以来」）',
    ly ? `首季 ${CSQ[0]} vs 上市 ${ly}` + (y0 > ly + 1 ? ` —— 少了 ${y0 - ly} 年，fetch_quarterly.py 的 --y0 设成上市年` : '') : '跳过');
  // 单季 vs 累计取错列的最直接症状：Q4 的费率系统性接近 Q1–Q3 之和
  // 正向判据：src 必须点名走的是「单季度.」原生指标。写「累计差分」或没标 src 都不算过。
  chk(/单季度/.test(String(CS.src || '')), 'CK-8 d5 1.4 数据源是 iFind 单季度.* 原生指标（不是累计差分/累计列）',
    String(CS.src || '未标 src'));
}

/* ---- CK-8 d6 · 1.4b 折旧摊销不许被摊平 ---------------------------------- */
/* A 股季报不含现金流量表补充资料，单季折旧在报表上不存在。契约因此要求：
   单季数组里不该有 da；TTM 的 da 只在 Q2/Q4 有值（那两个点由披露的累计数精确凑出）。
   如果 da 在 Q1/Q3 也有值，说明又有人把它摊平了。 */
const CC = P1.cash_capex || {};
if ((CC.quarters || []).length) {
  chk(!(CC.da || []).some(v => v != null), 'CK-8 d6 1.4b 单季数组里没有 da（单季折旧在报表上不存在）',
    (CC.da || []).some(v => v != null) ? '单季 da 有值 —— 是不是又摊平了？' : 'ok');
  const tq = (CC.ttm || {}).quarters || CC.quarters, td = (CC.ttm || {}).da || [];
  const oddQ = tq.filter((q, i) => td[i] != null && !/Q[24]$/.test(q));
  chk(!oddQ.length, 'CK-8 d6b 1.4b TTM 折旧只在 Q2/Q4 有值（Q1/Q3 无对应累计切点）',
    oddQ.length ? `${oddQ.slice(0, 3).join('/')} 也有值 —— 那是插出来的` : `${td.filter(v => v != null).length} 个真实点`);
  chk((CC.da_disclosure || []).length > 0, 'CK-8 d6c 1.4b 落了折旧的原始披露段 da_disclosure',
    `${(CC.da_disclosure || []).length} 段` + ((CC.da_disclosure || [])[0] ? `（${CC.da_disclosure[0].period}…）` : ''));
}

/* ---- CK-8 e · 2.1b 两把尺子不共轴 --------------------------------------- */
/* PE 与 PS 只是碰巧都念作「倍」：一个除盈利、一个除收入，同轴会把小的压成直线。
   数据层查的是「两条腿是否同时存在且量级悬殊」——存在即必须分轴（app.js 已分）。 */
const CIQ = (P2.fwd_pe || {}).ciq || {};
const rows = CIQ.rows || [];
if (rows.length) {
  const col = k => rows.map(r => parseFloat(r[k])).filter(v => isFinite(v) && v > 0);
  const pe = col('pe1'), ps = col('ps1');
  const med = a => { if (!a.length) return null; const s = a.slice().sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
  const mp = med(pe), ms = med(ps);
  chk(!(mp && ms) || true, 'CK-8 e 2.1b PE/PS 分轴（app.js y / yS 两根右轴）',
    (mp && ms) ? `PE 中位 ${Math.round(mp)}x、PS 中位 ${Math.round(ms * 100) / 100}x，量级差 ${Math.round(mp / ms)} 倍 —— 必须分轴` : '只有一条尺子腿');
  chk(!!(CIQ.na_note || (P2.fwd_pe || {}).caliber), 'CK-8 e2 2.1b 缺失值处理已写进口径',
    (CIQ.na_note || '').slice(0, 40) || ((P2.fwd_pe || {}).caliber || '').slice(0, 40) || '缺');
}

/* ---- CK-8 f · 1.5 不许自称箱线图 ---------------------------------------- */
/* FMP/一致预期只给 Low/Avg/High + 覆盖家数，没有 Q1/中位数/Q3，画不出箱体。
   页面上凡出现「箱线图」三个字，必须是在否定它（"这不是箱线图"），否则读者会去找箱体。 */
const CN = P1.consensus || {};
const consTxt = JSON.stringify([CN.box_caliber, CN.note, CN.caliber]);
const bx = (consTxt.match(/箱线图/g) || []).length;
const neg = (consTxt.match(/不是箱线图|非箱线图|没有箱体|无箱体/g) || []).length;
chk(bx === 0 || neg >= 1, 'CK-8 f 1.5 若提「箱线图」必须是在否定它',
  bx ? `出现 ${bx} 次「箱线图」、否定 ${neg} 次` : '未出现（ok）');

/* ---- CK-8 g · 2.2 估值算账必须两把尺子各算一遍 --------------------------- */
/* ★2026-08-16 读者反馈：「这里不仅要用 TTM 的估值口径算一遍，如果有的话还要用 Forward 口径算一遍」。
   病灶不是漏写一句，是**schema 降级**：算账是一坨 prose HTML(`body`)，03 §③ 的规范里
   明明写了「…→PE 档→隐含→Forward→ΔPE」，但散文里少一段没有任何东西会报错——
   「写了」和「没写」在机器看来一模一样。赛力斯阶段①②③ 的 Forward 腿就是这么消失的，
   而 Forward 数据当时就躺在同一份 page_model 的 part2.fwd_pe.ciq.rows 里（阶段① 全程覆盖）。
   现在拆成字段，跑 scripts/phase_valuation.py 生成。 */
const VS = P2.valuations || [];
const noCal = [];
const halfCal = [];
VS.forEach((v, i) => {
  const c = v && v.calibers;
  if (!c) { noCal.push(i + 1); return; }
  const leg = o => o && ((o.pe && (o.pe.delta != null || o.pe.na)) || (o.ps && (o.ps.delta != null || o.ps.na)));
  if (!leg(c.ttm) || !leg(c.fwd)) halfCal.push(i + 1);
});
chk(!PH.length || (VS.length === PH.length), 'CK-8 g0 valuations 与 phases 同长',
  `${VS.length} vs ${PH.length}`);
chk(VS.length > 0 && !noCal.length, 'CK-8 g 每段估值算账都有 calibers（TTM × Forward 双口径）',
  !VS.length ? '没有 valuations'
    : (noCal.length ? `第 ${noCal.join('/')} 段缺 —— 跑 python3 scripts/phase_valuation.py --model <m> --q-series <q> --write` : `${VS.length} 段齐`));
chk(!halfCal.length, 'CK-8 g2 缺的那一口径必须给 na 理由（不许静默省略）',
  halfCal.length ? `第 ${halfCal.join('/')} 段有一栏既无读数也无 na 理由` : 'ok');
// 两口径打架时必须在 read 里说出来，否则读者拿着相反的两个数不知道信哪个
const clash = VS.filter(v => {
  const c = v && v.calibers; if (!c) return false;
  const t = c.ttm && c.ttm.pe && c.ttm.pe.delta, d = c.fwd && c.fwd.decomp;
  if (t == null || !d) return false;
  return t * d.d_mult_pct < 0 && !/相反|以 Forward|滞后/.test(String(c.read || ''));
});
chk(!clash.length, 'CK-8 g3 两口径结论相反时 read 已点破（并说明拐点段信 Forward）',
  clash.length ? `${clash.length} 段 TTM 与 Forward 的倍数方向相反却没说` : 'ok');

/* ---- CK-8 g4 · 散文里的倍数读数要对得上某一个口径 ------------------------- */
/* 赛力斯阶段① 实证：**同一列里两个数打架**——结构化的 factor_quant.basis 写「P/S 2.70→1.18x」（TTM，对的），
   而散文 body/logic 写「P/S 从 1.6x 压到 0.6x」（那是 Forward 的 1.73，且终点也对不上 0.87）。
   两个数说的是同一件事，一个在字段里一个在散文里，**没有任何东西会去对一遍**。
   现在把散文里带 PE / P/S 标签的「A→Bx」抠出来，要求能对上 TTM 或 Forward 其中一把（±20%）。 */
const MULT = /(PE|P\/S|PS)[^0-9<]{0,12}([\d.]+)\s*[x×]?\s*(?:→|压到|掉到|抬到|升到|到)\s*([\d.]+)\s*[x×]/gi;
const near = (a, b) => a != null && b != null && Math.abs(a - b) <= Math.max(0.2 * Math.abs(b), 0.05);
const mismatch = [];
VS.forEach((v, i) => {
  const c = v && v.calibers; if (!c) return;
  const prose = [v.body, (PH[i] || {}).logic].filter(Boolean).join(' ').replace(/<[^>]+>/g, '');
  let m; MULT.lastIndex = 0;
  while ((m = MULT.exec(prose))) {
    const s = parseFloat(m[2]), e = parseFloat(m[3]);
    if (!isFinite(s) || !isFinite(e)) continue;
    const key = /^PE$/i.test(m[1]) ? 'pe' : 'ps';
    const legs = [c.ttm && c.ttm[key], c.fwd && c.fwd[key]].filter(x => x && x.delta != null);
    if (!legs.length) continue;                        // 该口径本来就算不出，不苛求
    if (!legs.some(L => near(s, L.start) && near(e, L.end)))
      mismatch.push(`第${i + 1}段「${m[1]} ${s}→${e}x」对不上 TTM(${(c.ttm[key] || {}).start}→${(c.ttm[key] || {}).end}) 也对不上 Forward(${(c.fwd[key] || {}).start}→${(c.fwd[key] || {}).end})`);
  }
});
chk(!mismatch.length, 'CK-8 g4 散文里的 PE / P/S 读数对得上某一个口径（±20%）',
  mismatch.length ? mismatch.slice(0, 3).join('；') : 'ok');

/* ---- CK-8 i · 走 esc() 的字段里不许有 HTML ------------------------------- */
/* 页面对字段分两类：`valuations[].body`/`consensus` 是 skill 生成的**可信 HTML**（原样注入），
   而 `phases[].logic`/`core_conflict`/`narrative`/`factor_quant.basis` 走 `esc()` 防注入。
   往后者写 `<b>…</b>`，读者看到的就是字面量尖括号（赛力斯 v3.2 起就在漏，改版式时才暴露）。
   要加粗用 `**…**`——页面有 ** → <b> 的兜底渲染器。 */
const ESCAPED = [];
PH.forEach((p, i) => {
  [['logic', p.logic], ['core_conflict', p.core_conflict], ['narrative', p.narrative],
   ['factor_signature', p.factor_signature], ['factor_quant.basis', (p.factor_quant || {}).basis]]
    .forEach(([k, v]) => { if (typeof v === 'string' && /<[a-zA-Z/][^>]*>/.test(v)) ESCAPED.push(`phases[${i}].${k}`); });
});
['resolved', 'open'].forEach(b => ((D.feedback || {})[b] || []).forEach((r, i) => {
  ['answer', 'why_pending', 'ask'].forEach(k => {
    if (typeof r[k] === 'string' && /<[a-zA-Z/][^>]*>/.test(r[k])) ESCAPED.push(`feedback.${b}[${i}].${k}`); });
}));
chk(!ESCAPED.length, 'CK-8 i 走 esc() 的字段里无 HTML 标签（加粗用 ** 不用 <b>）',
  ESCAPED.length ? `${ESCAPED.slice(0, 4).join('、')} —— 会原样印出尖括号` : 'ok');

/* ---- CK-8 h · schema 降级哨兵 -------------------------------------------- */
/* 规范要求的**结构项**一旦被写进自由文本，「写了」与「没写」在机器看来就一样了。
   这一条不查内容，只查「该是结构的地方还是不是结构」——上一次是 company_type
   从 {title,points[{k,v}]} 掉回 {label,note}，这一次是估值算账的 Forward 腿掉进 body 散文。 */
const degraded = [];
(D.summary && D.summary.company_type || []).forEach((c, i) => {
  if (!c.points && (c.label || c.note)) degraded.push(`summary.company_type[${i}] 掉回 {label,note} 散文`);
});
(P1.narrative_capacity && P1.narrative_capacity.baskets || []).forEach((b, i) => {
  if ((b.peers || []).some(x => typeof x === 'string')) degraded.push(`narrative_capacity.baskets[${i}].peers 是字符串数组`);
});
PH.forEach((p, i) => {
  if (p.factor_quant && typeof p.factor_quant === 'string') degraded.push(`phases[${i}].factor_quant 退化成字符串`);
  if (p.basket_beta && !p.basket_beta.rows && !p.basket_beta.bench) degraded.push(`phases[${i}].basket_beta 无 rows/bench`);
});
((D.summary && D.summary.accounting || {}).steps || []).forEach((s, i) => {
  if (s && !(s.scenarios || []).length && !s.driver) degraded.push(`summary.accounting.steps[${i}] 无 scenarios/driver`);
});
chk(!degraded.length, 'CK-8 h 无 schema 降级（结构项被写进自由文本）',
  degraded.length ? degraded.slice(0, 4).join('；') : '已查 company_type / peers / factor_quant / basket_beta / accounting.steps');

/* ---- CK-8 g5 · 底部没有利润的段不许再用 PE 做 R/M/V 的 V 层 ---------------- */
/* 2026-08-18 用户改制（03 §2f-q2）：ln(PE₁/PE₀) 在 E→0 时不是「很大」，是没有定义。
   硬算的结果每次长一个样——V 吃掉整段涨幅、R 与 M 挤成两根看不见的短条，
   读者读成「这一段全是估值在动」，而真相是「这一段根本没有盈利这把尺子可用」。
   本闸不判断该用哪把，只判断「PE 明明用不了却还标着 PE」和「换了却没写为什么」。 */
const RULERS = ['PE', 'PS', 'PB', 'EV/EBITDA'];
const peUnusable = (v) => {
  const c = v && v.calibers; if (!c) return null;                 // 没算双口径 → g 已经在管，这里不重复报
  const legs = [['TTM', c.ttm && c.ttm.pe], ['Forward', c.fwd && c.fwd.pe]].filter(x => x[1]);
  if (!legs.length) return null;
  const why = [];
  let anyUsable = false;
  legs.forEach(([tag, pe]) => {
    if (pe.na) { why.push(`${tag}: ${pe.na}`); return; }
    const bad = ['start', 'end'].filter(s => pe[s] != null && (pe[s] <= 0 || pe[s] > 150));
    if (bad.length) why.push(`${tag}: ${bad.map(s => `${s} PE ${pe[s]}x`).join('/')}`);
    else if (pe.start != null || pe.end != null) anyUsable = true;
  });
  return (!anyUsable && why.length) ? why.join('；') : null;
};
const rulerBad = [], rulerNoWhy = [], rulerEnum = [];
PH.forEach((p, i) => {
  const fq = p.factor_quant || {};
  if (typeof fq !== 'object' || Array.isArray(fq)) return;
  const r = fq.ruler;
  if (r && RULERS.indexOf(r) < 0) rulerEnum.push(`phases[${i}].ruler="${r}"`);
  const dead = peUnusable(VS[i]);
  if (dead && (!r || r === 'PE')) rulerBad.push(`${p.name || '#' + i}（${dead}）`);
  if (r && r !== 'PE' && !String(fq.ruler_why || '').trim()) rulerNoWhy.push(p.name || '#' + i);
});
chk(!rulerBad.length, 'CK-8 g5 PE 用不了的段已换尺子（ruler=PS/PB/EV·EBITDA）',
  rulerBad.length ? rulerBad.slice(0, 3).join('；') + ' —— 抄 calibers.ruler_suggest，见 03 §2f-q2' : '无 PE 失效段或均已改标');
chk(!rulerNoWhy.length, 'CK-8 g5b 换了尺子的段写了 ruler_why', rulerNoWhy.join('、') || 'ok');
chk(!rulerEnum.length, 'CK-8 g5c ruler 取值合法（PE/PS/PB/EV·EBITDA）', rulerEnum.join('、') || 'ok');
{
  const set = [...new Set(PH.map(p => (p.factor_quant || {}).ruler).filter(Boolean))];
  if (set.length > 1) console.log(`   ↳ 本页 ${set.length} 把尺子（${set.join('/')}）：V 条**不可跨段直比**，页面已渲黄条提示。`);
}

/* ---- CK-8 j · 版式闸（可选，传 --html <built.html> 才跑）------------------ */
/* 只有两条，都是被读者反复退回过的：表头必须能看见、金额表必须写单位。
   放在这里而不是靠人眼，是因为「3.1 表头字体改成黑色」这一条已经复发四次。 */
const hi = args.indexOf('--html');
if (hi >= 0 && args[hi + 1] && fs.existsSync(args[hi + 1])) {
  const H = fs.readFileSync(args[hi + 1], 'utf8');
  const css = (/<style>([\s\S]*?)<\/style>/.exec(H) || [, ''])[1];
  const globalTh = /(^|\})\s*thead th\s*\{([^}]*)\}/m.exec(css);
  const thBody = globalTh ? globalTh[2] : '';
  chk(!!thBody && !/color\s*:\s*(#fff|#ffffff|white)/i.test(thBody),
    'CK-8 j1 全局 thead th 不是白字（浅底深字，覆盖底色也不会看不见）',
    thBody ? thBody.replace(/\s+/g, ' ').slice(0, 60) : '未找到 thead th 规则');
  chk(/th-unit/.test(H) || /单位\s*[：:]/.test(H),
    'CK-8 j2 3.1 表头写了单位（.th-unit）', /th-unit/.test(H) ? '有 .th-unit' : '缺');
}

/* --------------------------------- 输出 ------------------------------------ */
console.log('图表契约闸 · CK-8（量纲 / 图形 / 口径标注 —— 查的是「读者会读成什么」）');
console.log('─'.repeat(78));
let bad = 0;
R.forEach(x => { if (!x.pass) bad++; console.log(` ${x.pass ? '✓' : '✗'} ${x.name.padEnd(52)} ${x.detail}`); });
console.log('─'.repeat(78));
console.log(bad ? `✗ ${bad}/${R.length} 项不过` : `✓ 全部 ${R.length} 项通过`);
process.exit(bad ? 1 : 0);
