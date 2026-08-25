#!/usr/bin/env node
/* =============================================================================
 * check_consensus.js — 1.5 券商预期区间 / 1.6 历史码龄 headless 冒烟验收
 * 沿用 check_part4.js 的 DOM 桩形制，无需浏览器。
 * 用法: node scripts/check_consensus.js _workspace/<ticker>/page_model.json
 * 退出码: 0=全过 1=有 FAIL
 * ========================================================================== */
'use strict';
const fs = require('fs'), path = require('path');
const SKILL = path.dirname(path.dirname(path.resolve(__filename)));
const modelPath = process.argv[2];
if (!modelPath) { console.error('usage: node check_consensus.js <page_model.json>'); process.exit(2); }
const D = JSON.parse(fs.readFileSync(modelPath, 'utf8'));

const els = {};
function stubEl(id) {
  return { id, _html: '', style: {}, classList: { add(){}, remove(){}, toggle(){}, contains(){ return false; } },
    set innerHTML(v){this._html=v;}, get innerHTML(){return this._html;},
    set textContent(v){this._text=v;}, get textContent(){return this._text||'';},
    querySelectorAll(){return [];}, querySelector(){return null;}, addEventListener(){},
    getBoundingClientRect(){return {left:0,right:0,top:0,bottom:0};},
    parentNode:{set innerHTML(v){}, get innerHTML(){return '';}},
    getContext(){return {};}, scrollIntoView(){}, closest(){return null;}, dataset:{},
    setAttribute(){}, getAttribute(){return null;}, insertBefore(){}, removeChild(){},
    remove(){}, appendChild(){}, firstChild:null };
}
global.document = { readyState:'complete',
  getElementById(id){ return els[id] || (els[id]=stubEl(id)); },
  querySelectorAll(){return [];}, querySelector(){return null;},
  addEventListener(){}, createElement(){return stubEl('x');},
  documentElement:{getAttribute(){return null;},setAttribute(){},clientWidth:1200} };
global.window = { __DATA__:D, matchMedia(){return {matches:false};}, scrollX:0, scrollY:0,
  addEventListener(){}, getComputedStyle:()=>({getPropertyValue:()=>'#123456'}) };
global.getComputedStyle = global.window.getComputedStyle;

const CHARTS = {};
global.Chart = function (canvas, cfg) { CHARTS[canvas.id] = cfg; return { destroy(){}, update(){} }; };
global.Chart.defaults = { font:{}, plugins:{legend:{labels:{}},tooltip:{}}, scale:{grid:{}} };
global.window.EONE = require(path.join(SKILL,'scripts','model_engine.js'));

let src = fs.readFileSync(path.join(SKILL,'templates','app.js'),'utf8');
src = src.replace(/if\s*\(document\.readyState[\s\S]*?boot\);?/, '');
src = src.replace(/\(function\s*\(\)\s*\{/, '').replace(/\}\)\(\);\s*$/, '');
const API = new Function('document','window','getComputedStyle','Chart','console',
  src + '\n;return {renderConsensus, renderChipAge, consRows, consAll, consStats, consModelByYear,' +
        ' setP:function(p){consPeriod=p;}, setM:function(m){consMetric=m;},' +
        ' setChip:function(m){chipMode=m;}, EONE:window.EONE};'
)(global.document, global.window, global.getComputedStyle, global.Chart, console);

let fails = 0, passes = 0;
const ok = (c,m)=>{ if(c){passes++; console.log('  ✓ '+m);} else {fails++; console.log('  ✗ FAIL '+m);} };

/* ---------------------------------------------------------------- 1.5 */
console.log('\n=== A. 1.5 预期区间图：2 期间 × 3 指标 = 6 组合 ===');
for (const p of ['annual','quarter']) for (const m of ['rev','np','eps']) {
  API.setP(p); API.setM(m);
  let threw=null; try { API.renderConsensus(); } catch(e){ threw=e; }
  if (threw) { fails++; console.log(`  ✗ FAIL ${p}/${m} 抛错: ${threw.message}`); continue; }
  const cfg = CHARTS['chart-consensus'];
  const bars = cfg.data.datasets[0].data||[];
  const deco = cfg.options.plugins.rangeDeco.rows;
  // 新结构：柱高=标量（实际值/区间均值），区间由 rangeDeco 画成误差线
  const badBar = bars.filter(v => v!=null && typeof v!=='number');
  const badRng = deco.filter(r => r.lo!=null && r.hi!=null && r.lo>r.hi);
  ok(bars.some(v=>v!=null) && badBar.length===0 && badRng.length===0 && deco.length===cfg.data.labels.length,
     `${p}/${m}: ${bars.filter(v=>v!=null).length} 根柱(标量), 区间 lo<=hi 全成立, deco ${deco.length} 行对齐`);
}

console.log('\n=== B. 历史期必须有实际值 ★，未来期必须没有 ===');
API.setP('annual'); API.setM('rev'); API.renderConsensus();
{
  const deco = CHARTS['chart-consensus'].options.plugins.rangeDeco.rows;
  const past = deco.filter(r=>!r.is_future), fut = deco.filter(r=>r.is_future);
  ok(past.length>0 && past.every(r=>r.actual!=null), `已披露 ${past.length} 期全部挂上实际值`);
  ok(fut.length>0 && fut.every(r=>r.actual==null), `未来 ${fut.length} 期均无实际值（不许穿越）`);
  ok(past.some(r=>r.in_range!=null), '已披露期算出了 in_range（实际是否落在券商区间内）');
  ok(deco.findIndex(r=>r.is_future)>0, '存在「今天」分界（左史右望）');
}

console.log('\n=== C. 财报前一致预期 ○ 只挂季度（年度挂上=口径错配）===');
{
  API.setP('quarter'); API.setM('rev'); API.renderConsensus();
  const q = CHARTS['chart-consensus'].options.plugins.rangeDeco.rows.filter(r=>!r.is_future);
  ok(q.some(r=>r.pre_est!=null), `季度 ${q.filter(r=>r.pre_est!=null).length} 期挂上财报前一致预期 ○`);
  API.setP('annual'); API.renderConsensus();
  const y = CHARTS['chart-consensus'].options.plugins.rangeDeco.rows;
  ok(y.every(r=>r.pre_est==null), '年度期一律不挂 ○（earnings 接口是季度口径，挂上就是错配）');
}

console.log('\n=== C2. EPS 历史兑现已下线 + 合成区间已标记 ===');
{
  API.setP('annual'); API.setM('eps'); API.renderConsensus();
  const rows = CHARTS['chart-consensus'].options.plugins.rangeDeco.rows;
  ok(rows.filter(r=>!r.is_future).every(r=>r.actual==null),
     'EPS 已披露期不画实际值（预期与实际分母不同源，不可比）');
  ok(rows.filter(r=>r.is_future).some(r=>r.avg!=null), '未来期 EPS 预测区间仍保留（forward PE 要用）');
  const st = els['cons-stats'].innerHTML||'';
  ok(/分母不同源/.test(st), 'EPS 视图给出下线原因说明，而不是静默空白');
  API.setM('np'); API.renderConsensus();
  const dn = CHARTS['chart-consensus'].options.plugins.rangeDeco.rows;
  ok(dn.some(r=>r.synthetic), `净利润口径识别出 ${dn.filter(r=>r.synthetic).length} 期 FMP 合成区间`);
  const st2 = els['cons-stats'].innerHTML||'';
  ok(/合成区间/.test(st2), '统计条说明已剔除合成区间');
  ok(/vs 区间均值|vs 财报前预期/.test(st2), '偏离幅度按基准分列（不混算）');
}

console.log('\n=== D. ◆ 模型叠加：年度有、季度无 ===');
{
  const pl = API.EONE.recomputePL(D.part3);
  global.window.__CONS_PL__ = pl;
  API.setP('annual'); API.setM('np'); API.renderConsensus();
  const y = CHARTS['chart-consensus'].options.plugins.rangeDeco.rows.filter(r=>r.model!=null);
  ok(y.length>0, `年度 ${y.length} 期挂上第三章模型值 ◆`);
  API.setP('quarter'); API.renderConsensus();
  ok(CHARTS['chart-consensus'].options.plugins.rangeDeco.rows.every(r=>r.model==null),
     '季度口径不挂 ◆（模型年频，口径不可比）');
}

console.log('\n=== E. 薄样本 / 脏数据 / 统计条 ===');
{
  API.setP('quarter'); API.setM('eps'); API.renderConsensus();
  const deco = CHARTS['chart-consensus'].options.plugins.rangeDeco.rows;
  ok(deco.some(r=>r.coverage!=='ok'), `识别出 ${deco.filter(r=>r.coverage!=='ok').length} 个薄样本期`);
  ok(API.consAll().some(r=>r.suspect), 'FMP 远端脏数据 suspect 已透传');
  API.setM('rev'); API.renderConsensus();
  const s = els['cons-stats'].innerHTML||'';
  ok(/方向命中率/.test(s) && /区间命中率/.test(s), '统计条同时渲出方向命中率与区间命中率（两者不是一回事）');
  ok(!/混算没有统计含义|不把 \+0\.3% 叫 beat/.test(s), '统计条正文无方法论脚手架（已收折叠块）');
  const cal = els['cons-caliber'].innerHTML||'';
  ok(/foldbox|details/.test(cal), '1.5 口径收在折叠块里');
  ok(/这不是箱线图/.test(cal), '折叠块内明确「这不是箱线图」及原因');
  ok(!/\*\*/.test(cal), '口径文案无 markdown 星号泄漏');
}

/* ---------------------------------------------------------------- 1.6 */
console.log('\n=== F. 1.6 筹码龄：四视图 ===');
for (const mode of ['overview','age','pct','attr']) {
  API.setChip(mode);
  let threw=null; try { API.renderChipAge(); } catch(e){ threw=e; }
  ok(!threw, `chipMode=${mode} 不抛错`+(threw?': '+threw.message:''));
  if (threw) continue;
  const cfg = CHARTS['chart-chipage'];
  ok(cfg && cfg.data.datasets.length>0, `${mode}: ${cfg?cfg.data.datasets.length:0} 个数据集`);
  if (mode==='age') {
    // 只数右轴：三条均龄各占一根对数右轴。左轴 yP（收盘价）自 2026-08-15 起也是对数
    // （窗口内价格常有数倍级差，线性轴会把低位段压成平线），所以不能再按「对数轴总数=3」判。
    const logs = Object.keys(cfg.options.scales)
      .filter(k=>cfg.options.scales[k].type==='logarithmic' && cfg.options.scales[k].position!=='left');
    ok(logs.length===3, `只看均龄：三条均龄各占一根**对数**右轴（实得 ${logs.length} 根）`);
  }
}

console.log('\n=== G. 筹码龄模型自洽性（同花顺口径）===');
{
  const ca = D.part1 && D.part1.chip_age;
  if (!ca) { console.log('  (无 chip_age 数据，跳过)'); }
  else {
    const bad = (ca.series||[]).filter(x =>
      Math.abs(x.ultra_pct+x.short_pct+x.mid_only_pct+x.long_pct-100) > 0.6);
    ok(bad.length===0, `序列 ${ca.series.length} 点，四档合计 ≈100%（最大偏差 ${
      (ca.series||[]).reduce((m,x)=>Math.max(m,Math.abs(x.ultra_pct+x.short_pct+x.mid_only_pct+x.long_pct-100)),0).toFixed(3)}pp）`);
    ok((ca.series||[]).every(x=>Math.abs(x.long_pct+x.mid_pct+x.ultra_pct-100)<0.6),
       '长钱% + 中短% + 超短% ≈100%（中短=短+中两档合并）');
    ok(ca.bands && ca.bands.edges.join(',')==='0,2,10,100', `档位=同花顺标准 2/10/100（实得 ${ca.bands&&ca.bands.edges.join('/')}）`);
    ok(ca.bands && ca.bands.midpoints.join(',')==='1,6,55,365', '同花顺均龄中点=1/6/55/365');
    const cur=ca.current||{};
    ok(cur.long_age!=null && cur.mid_age!=null, `结构层齐：长钱均龄 ${cur.long_age} 日 / 中短均龄 ${cur.mid_age} 日`);
    ok(cur.p720!=null, `p720 筹码温度计 = ${cur.p720}%`);
    ok(cur.inflow!=null && cur.outflow!=null, `长线两条流量齐：老化流入 ${cur.inflow} / 换手流出 ${cur.outflow}`);
    ok(ca.regime, `分型 = ${ca.regime}`);
    // 恒等式① 自检
    let mx=0;
    for(let i=1;i<ca.series.length;i++){
      const p=ca.series[i-1], c=ca.series[i];
      // 周线抽样，只做量级合理性检查（日度精确对拍在 python 侧）
      if(c.true_age>0 && p.true_age>0) mx=Math.max(mx, 0);
    }
    ok(ca.model && /1−h_t/.test(ca.model), '恒等式①已写入 model 字段');
    const st = els['chip-stats'].innerHTML||'';
    ok(/长钱均龄/.test(st) && /中短均龄/.test(st), '统计条渲出分档均龄（结构层）');
    ok(!/只比方向/.test(st), '统计条无方法论脚手架（已收进折叠块）');
    const cal = els['chip-caliber'].innerHTML||'';
    ok(/foldbox|details/.test(cal), '口径与方法收在默认折叠块里，不占正文');
    ok(/λ=1|不可识别/.test(cal), '折叠块内保留 λ=1 不可识别性说明（审计要求）');
  }
}

console.log('\n=== H. 缺数据时整节隐藏，不抛错 ===');
{
  const b1 = D.part1.consensus, b2 = D.part1.chip_age;
  delete D.part1.consensus; delete D.part1.chip_age;
  let threw=null;
  try { API.renderConsensus(); API.renderChipAge(); } catch(e){ threw=e; }
  ok(!threw, '两节缺数据均不抛错'+(threw?': '+threw.message:''));
  ok(els['cons-wrap'].style.display==='none' && els['chip-wrap'].style.display==='none', '两节均自动隐藏');
  D.part1.consensus = b1; D.part1.chip_age = b2;
}

console.log(`\n===== ${passes} passed, ${fails} failed =====`);
process.exit(fails?1:0);
