#!/usr/bin/env node
/**
 * check_part3.js — 第三章两道结构闸（CK-3 里原来只有人肉纪律的那两条）
 *
 *   用法: node check_part3.js --model page_model.json
 *
 * 闸一 · 反算隐含份额（A 组）
 *   2026-08-14 阳光电源实跑抓出来的：5 个分部的 seg_val 全部是「2028E 分摊利润 × 倍数」，
 *   SOTP 4,353 亿是 ladder 里离现价 +78% 的那一档；但 driver_chain 最远只算到 2026，
 *   q_anchors 五个锚全是 2026 的。**举证全在 T+1，估值全押 T+3。**
 *   2027E–2030E 的 q_growth 是裸参数，没有 TAM×份额、没有锚、没有 ev。
 *
 *   所以：凡 seg_val 的锚年超出 driver_chain 覆盖的最远年份，该段必须给 `anchor_check`——
 *   把锚年的 q 反算成隐含市场份额（或隐含 TAM 占比），与一个外部锚对表，并给出判定。
 *   不要求逐年重算驱动链，只要求**外推的终点必须落地成一个可证伪的份额数字**。
 *
 * 闸二 · L 兜底段进 SOTP 的上限（B 组）
 *   driver_chain 与 calibers 皆空的段（＝没有量价拆分、只有增速外推），其 seg_val 市值
 *   在 SOTP 里的占比不得超过它的收入占比 + 容差。阳光当前 4.8% vs 4.7% 恰好合规，
 *   但结构上原来没有任何东西把守——一个 30% 收入占比的段照样可以这么进。
 */
'use strict';
const fs = require('fs');

const args = process.argv.slice(2);
const mi = args.indexOf('--model');
if (mi < 0 || !args[mi + 1]) { console.error('usage: node check_part3.js --model <page_model.json>'); process.exit(2); }
const TOL_PP = (() => { const i = args.indexOf('--tol-pp'); return i >= 0 ? parseFloat(args[i + 1]) : 3; })();
const M = JSON.parse(fs.readFileSync(args[mi + 1], 'utf8'));

const P3 = M.part3 || {};
const FY = P3.forecast_years || [];
const results = [];
const push = (ok, name, msg) => results.push({ ok, name, msg: msg || '' });
const yr = s => { const m = String(s || '').match(/(20\d\d)/g); return m ? Math.max(...m.map(Number)) : null; };
const num = v => (typeof v === 'number' && isFinite(v)) ? v : null;

/* ---------- 把预测期的 q 递推出来，锚年的 q 才好反算份额 ---------- */
function qAt(seg, yearLabel) {
  const idx = FY.indexOf(yearLabel);
  if (idx < 0) return null;
  const h = (seg.hist && seg.hist.q) || [];
  let q = num(h[h.length - 1]);
  const g = (seg.assume && seg.assume.q_growth) || [];
  if (q == null) return null;
  for (let i = 0; i <= idx; i++) { const gi = num(g[i]); if (gi == null) return null; q *= (1 + gi); }
  return q;
}

/* =========================== A · 反算隐含份额闸 =========================== */
const segs = P3.segments || [];
if (!segs.length) push(false, 'A0 有分部', 'part3.segments 为空');

segs.forEach(s => {
  const md = s.model || {};
  const sv = md.seg_val || {};
  const tag = `${s.key}/${s.name}`;
  const anchorY = yr(sv.method) || yr(sv.note);
  const chainY = Math.max(0, ...(md.driver_chain || []).map(d => yr(JSON.stringify(d)) || 0));
  if (!anchorY) { push(false, `A1 ${tag} seg_val 写明锚年`, 'method/note 里读不出年份'); return; }

  const anchorLabel = FY.find(y => yr(y) === anchorY) || `${anchorY}E`;
  const covered = chainY >= anchorY;
  push(true, `A1 ${tag} 锚年`, `seg_val 锚 ${anchorY}，driver_chain 覆盖到 ${chainY || '—'}${covered ? '（已覆盖）' : '（未覆盖→须 anchor_check）'}`);
  if (covered) return;

  const ac = md.anchor_check;
  if (!ac) {
    push(false, `A2 ${tag} 有 anchor_check`,
      `seg_val 押 ${anchorY} 而举证只到 ${chainY || '无'}——须补 anchor_check{year,tam,implied_share_pct,ref_share_pct,verdict,why}`);
    return;
  }
  push(yr(ac.year) === anchorY, `A2 ${tag} anchor_check.year 对上锚年`, `${ac.year} vs seg_val ${anchorY}`);

  const q = qAt(s, anchorLabel);
  const tamV = num(ac.tam && ac.tam.v);
  const impl = num(ac.implied_share_pct);
  const ref = num(ac.ref_share_pct);

  push(tamV != null && !!(ac.tam || {}).basis, `A3 ${tag} TAM 有值且写明出处`,
    tamV == null ? '缺 tam.v' : `${tamV} ${(ac.tam || {}).unit || ''} · ${(ac.tam || {}).basis || '⚠缺 basis'}`);

  if (q != null && tamV) {
    const calc = q / tamV * 100;
    const ok = impl != null && Math.abs(calc - impl) <= 0.5;
    push(ok, `A4 ${tag} 隐含份额与模型 q 自洽`,
      `模型递推 q(${anchorLabel})=${q.toFixed(1)} ÷ TAM ${tamV} = ${calc.toFixed(1)}% vs 填写 ${impl == null ? '—' : impl + '%'}`);
  } else {
    push(false, `A4 ${tag} 隐含份额与模型 q 自洽`, `算不出：q=${q == null ? '—' : q.toFixed(1)} tam=${tamV || '—'}`);
  }

  const V = ['扩张', '持平', '收缩'];
  push(V.includes(ac.verdict), `A5 ${tag} verdict 合法`, `${ac.verdict || '空'}（须为 ${V.join('/')} 之一）`);
  push(!!(ac.why && String(ac.why).length >= 20 && /\d/.test(ac.why)), `A6 ${tag} why 带数字且 ≥20 字`, String(ac.why || '').slice(0, 60));

  if (impl != null && ref != null) {
    const drift = impl - ref;
    const claims = ac.verdict === '扩张' ? drift > TOL_PP : ac.verdict === '收缩' ? drift < -TOL_PP : Math.abs(drift) <= TOL_PP;
    push(claims, `A7 ${tag} verdict 与份额漂移一致`,
      `隐含 ${impl}% vs 参照 ${ref}%（${(drift >= 0 ? '+' : '') + drift.toFixed(1)}pp，容差 ±${TOL_PP}pp）→ 判「${ac.verdict}」`);
    if (ac.verdict === '扩张') {
      push(!!ac.share_gain_from, `A8 ${tag} 份额扩张须指名从谁手里抢`, ac.share_gain_from || '缺 share_gain_from');
    }
  } else {
    push(false, `A7 ${tag} verdict 与份额漂移一致`, '缺 implied_share_pct 或 ref_share_pct');
  }
  push(!!(ac.cost_if_wrong && /\d/.test(ac.cost_if_wrong)), `A9 ${tag} cost_if_wrong 带量级`, String(ac.cost_if_wrong || '').slice(0, 60));
});

/* ====================== B · L 兜底段进 SOTP 的上限 ====================== */
const totSV = segs.reduce((a, s) => a + (num((s.model || {}).seg_val && s.model.seg_val.mcap_yi) || 0), 0);
const lastRev = s => { const r = (s.hist && s.hist.rev) || []; return num(r[r.length - 1]) || 0; };
const totRev = segs.reduce((a, s) => a + lastRev(s), 0);

segs.forEach(s => {
  const md = s.model || {};
  const bare = !(md.driver_chain && md.driver_chain.length) && !md.calibers;
  if (!bare) return;
  const mc = num((md.seg_val || {}).mcap_yi) || 0;
  const wV = totSV ? mc / totSV * 100 : 0;
  const wR = totRev ? lastRev(s) / totRev * 100 : 0;
  push(wV <= wR + TOL_PP, `B1 ${s.key}/${s.name} L兜底段市值占比 ≤ 收入占比`,
    `无 driver_chain 且无 calibers → SOTP 占比 ${wV.toFixed(1)}% vs 收入占比 ${wR.toFixed(1)}%（容差 +${TOL_PP}pp）`
    + (wV > wR + TOL_PP ? '　该段没有量价拆分却拿到超过其收入份额的估值权重，要么补驱动链要么下调倍数' : ''));
  push(/兜底|未披露|不可得|降级/.test(String(md.logic || '')), `B2 ${s.key} 兜底已在 logic 里明说`,
    String(md.logic || '').replace(/<[^>]+>/g, '').slice(0, 50));
});

/* --------------------------------- 输出 --------------------------------- */
console.log('第三章 结构闸 · CK-3 A/B 组');
console.log('─'.repeat(72));
let bad = 0;
results.forEach(r => { if (!r.ok) bad++; console.log(` ${r.ok ? '✓' : '✗'} ${r.name.padEnd(46)} ${r.msg}`); });
console.log('─'.repeat(72));
console.log(bad ? `✗ ${bad}/${results.length} 项不过` : `✓ 全部 ${results.length} 项通过`);
process.exit(bad ? 1 : 0);
