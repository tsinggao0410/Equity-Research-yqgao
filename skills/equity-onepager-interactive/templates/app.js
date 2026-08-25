/* =============================================================================
 * equity-onepager-interactive · app.js
 * Renders the whole page from window.__DATA__ (page_model) + window.EONE (engine).
 * Chart cookbook follows the pboc house style; Part-3 is fully interactive.
 * ========================================================================== */
(function () {
'use strict';
var D = window.__DATA__ || {};
var EONE = window.EONE;
var CH = {};                 // chart registry (id -> Chart)
var MODEL = D.part3 || {};   // live-edited model slice

// ---- palette / theme -------------------------------------------------------
function cv(n){ return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
function PAL(){ return {
  s:[cv('--s1'),cv('--s2'),cv('--s3'),cv('--s4'),cv('--s5'),cv('--s6'),cv('--s7'),cv('--s8')],
  fg:cv('--fg'), muted:cv('--muted'), ink3:cv('--ink3'), grid:cv('--grid'), good:cv('--good'), bad:cv('--bad'),
  accent:cv('--accent'), panel:cv('--panel'), elev:cv('--elev'), bg:cv('--bg') }; }
var CODE_COLOR = {R:'#D85A30',M:'#639922',V:'#7a5af5',RM:'#BA7517',RV:'#0b5fff',MV:'#1D9E75',RMV:'#e34948'};
// 五大催化剂 G1-G5（用户口径，取代 D/E/S/O/L）
var CAT_COLOR = {G1:{bg:'#E6F1FB',fg:'#0C447C'},G2:{bg:'#FAECE7',fg:'#712B13'},G3:{bg:'#EEEDFE',fg:'#3C3489'},G4:{bg:'#E1F5EE',fg:'#085041'},G5:{bg:'#FDF0DA',fg:'#7a5a12'}};
var CAT_LABEL = {G1:'数据高增长',G2:'接到大订单',G3:'有大佬站台',G4:'传播面出圈',G5:'公司有诉求'};
var DIM_LABELS = {'1.1':'行业量价','1.2':'公司份额','2.1':'财报披露','2.2':'供给侧','2.3':'供需差','3.1':'情绪筹码','3.2':'叙事','3.3':'板块筹码','3.4':'范式转移'};

// ---- number formatting -----------------------------------------------------
function num(x,d){ x=parseFloat(x); return isFinite(x)?x:(d===undefined?0:d); }
function yi(x){ x=parseFloat(x); if(!isFinite(x))return '—'; var a=Math.abs(x); return (a>=100?Math.round(x):Math.round(x*10)/10).toLocaleString(); }
function pct(x,d){ x=parseFloat(x); if(!isFinite(x))return '—'; return (Math.round(x*(Math.pow(10,(d===undefined?1:d)+2)))/Math.pow(10,(d===undefined?1:d))).toFixed(d===undefined?1:d)+'%'; }
function spct(x,d){ if(x==null||!isFinite(x))return '—'; return (x>=0?'+':'')+pct(x,d); }
function esc(s){ return String(s==null?'':s).replace(/[&<>]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;'}[c];}); }

/* ★2026-08-16 涨跌幅量纲兜底（赛力斯 v3.2 读者反馈）─────────────────────────────
 * 契约：part2.phases[].chg 是**可读字符串**（"+244.8%" / "-47.8%"）。
 * 病灶：赛力斯 v3.2 的 build 脚本把它落成了裸小数 -0.4776，两处同时错：
 *   ① 页面直接 esc(ph.chg) 印出「0.4776」——读者分不清是 47.76% 还是 0.48%；
 *   ② 2679 行历史对照条 num(hp.chg) 拿它当**百分点**去和 rmv 的 _pp 比，量纲错 100 倍
 *      （和 1.7 basket_beta 那次「stock_chg 落小数而 bench 是百分数」是同一个病）。
 * 治法：不信任上游，渲染层收口——数字一律按「小数＝涨跌幅」解释，字符串原样透传。
 * 两个出口分开，是因为「印出来的串」和「参与算术的数」量纲不同，混用就是下一次 100 倍。 */
function chgPct(v){                                   // → 百分数（-47.76），给算术用
  if(v==null||v==='') return null;
  if(typeof v==='number') return isFinite(v)?v*100:null;
  var f=parseFloat(String(v).replace(/[^\d.eE+-]/g,''));
  return isFinite(f)?f:null;
}
function chgTxt(v){                                   // → 展示串（"-47.8%"），给页面用
  if(v==null||v==='') return '';
  if(typeof v==='number') return isFinite(v)?spct(v,1):'';
  return String(v);
}

/* ★2026-08-16 第二版：裸数字的**量纲要靠数据判，不能靠约定猜**。
 * 上面两个函数按「数字＝小数」解释，那是照赛力斯（-0.4776）写的；
 * 回归到阳光电源才发现它的 chg 落的是 **117.9 / -36.4（百分数）**——同一个字段两个 build 两种量纲，
 * 按小数解释会渲成 +11790%。**「裸数字」这件事本身就是病，两种猜法都会错一半。**
 * 判据不能是量级拍脑袋（|x|∈[1,10] 天然歧义：2.448 是 +244.8% 还是 +2.4%？），
 * 要用**同一段里已有的第二个观测**：factor_quant 的 r/m/v 都是**百分点**，
 * 三者之和按契约要对上段涨幅（±3pp，见 03 §2f-q）。拿 Σ 当尺子，两种解释里选贴得近的那个。
 * 取不到 Σ 时才退回量级启发式，并在控制台留话——静默猜是下一次事故。
 * 归一化在**渲染前一次做完**，把 chg 就地改写成规范展示串，下游全部只见字符串，不再有歧义。 */
function normalizePhaseChg(){
  var phs=(D.part2&&D.part2.phases)||[]; var fixed=0, guessed=[];
  phs.forEach(function(ph,i){
    var v=ph.chg;
    if(v==null||typeof v==='string') return;           // 已是串（含 %）＝契约内，不动
    if(!isFinite(v)) { ph.chg=''; return; }
    var f=ph.factor_quant, sigma=null;
    if(f){ var s=num(f.r_pp,NaN)+num(f.m_pp,NaN)+num(f.v_pp,NaN); if(isFinite(s)) sigma=s; }
    var asPct=v, asFrac=v*100, pick;
    if(sigma!=null && (Math.abs(asPct)>0||Math.abs(asFrac)>0)){
      pick=(Math.abs(asFrac-sigma)<=Math.abs(asPct-sigma))?asFrac:asPct;   // 谁离 Σ 近听谁的
    }else{
      pick=(Math.abs(v)<=5)?asFrac:asPct;                                   // 无 Σ：退回量级启发式
      guessed.push('phases['+i+']');
    }
    ph.chg=(pick>=0?'+':'')+(Math.round(pick*10)/10)+'%';
    fixed++;
  });
  if(fixed) try{ console.warn('[onepager] part2.phases[].chg 有 '+fixed+' 条是裸数字，已按'
    +(guessed.length?('Σfactor_quant 归一（其中 '+guessed.join('/')+' 无 Σ 可对，按量级猜）'):'Σfactor_quant 归一')
    +'。请在 build 脚本里直接落 "+244.8%" 这种串（CK-8 a）。'); }catch(e){}
}

/* ★ **强调** 渲染层兜底：page_model 里大量字段走 esc()（防注入），所以 markdown 的 ** 会以字面量泄漏。
   这里在渲染完成后做一次纯文本节点扫描，把 **…** 变成真正的 <b>，不碰 script/style/表单。 */
function mdBold(root){
  root=root||document.body; if(!root) return;
  var w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:function(n){
    var p=n.parentNode; if(!p) return NodeFilter.FILTER_REJECT;
    var t=p.nodeName; if(t==='SCRIPT'||t==='STYLE'||t==='TEXTAREA'||t==='OPTION') return NodeFilter.FILTER_REJECT;
    return /\*\*[^*]+\*\*/.test(n.nodeValue)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT; }});
  var hit=[],n; while((n=w.nextNode())) hit.push(n);
  hit.forEach(function(node){
    var frag=document.createDocumentFragment(), s=node.nodeValue, re=/\*\*([^*]+)\*\*/g, last=0, m;
    while((m=re.exec(s))){
      if(m.index>last) frag.appendChild(document.createTextNode(s.slice(last,m.index)));
      var b=document.createElement('b'); b.textContent=m[1]; frag.appendChild(b); last=re.lastIndex; }
    if(last<s.length) frag.appendChild(document.createTextNode(s.slice(last)));
    node.parentNode.replaceChild(frag,node); });
}

function CURU(){ try{ return (D&&D.meta&&D.meta.price_unit)||' 元'; }catch(e){ return ' 元'; } }
/* 金额表头的单位串。3.1 全表金额一律「亿 + 报告币种」，币种取 meta.currency（CNY/HKD/USD…），取不到按人民币。
   ★读者反馈「看不懂是万元还是百万元」——单位必须写在**表头上**，写在图注/cap 里等于没写：
   表能横向滚，滚起来 cap 早滚出视野了。 */
function MONEYU(){ try{ var c=String(((D&&D.meta)||{}).currency||'').toUpperCase();
  if(/HKD|港/.test(c)) return '亿港元';
  if(/USD|美元/.test(c)) return '亿美元';
  if(/EUR|欧元/.test(c)) return '亿欧元';
  return '亿元'; }catch(e){ return '亿元'; } }
function el(id){ return document.getElementById(id); }
// hex 色 + alpha 后缀安全拼接：3位hex(#888)先展开为6位，非hex原样返回（防 '#888'+'10' 变非法色→canvas 黑块）
function hexA(c,a){ if(!c) return null; c=String(c).trim();
  var m=/^#([0-9a-fA-F]{3})$/.exec(c); if(m) c='#'+m[1].split('').map(function(x){return x+x;}).join('');
  return /^#[0-9a-fA-F]{6}$/.test(c) ? c+a : c; }
// 契约允许 assume/opex 率写「标量或短数组广播」(引擎 at() 支持)，但滑块层按下标读写——
// boot 时先物化：assume.* 补齐到 F 长(尾值延展)；opex 标量转 [x]（保持"常数广播"语义，滑块只编辑[0]）。
function normalizeModel(){ var F=(MODEL.forecast_years||[]).length||1;
  (MODEL.segments||[]).forEach(function(s){ var a=s.assume=s.assume||{};
    ['q_growth','p_growth','gm'].forEach(function(k){ var v=a[k]; if(v==null)return;
      if(typeof v==='number') v=[v]; else v=v.slice();
      if(v.length&&v.length<F){ var lastv=v[v.length-1]; while(v.length<F) v.push(lastv); }
      a[k]=v; }); });
  var op=MODEL.opex=MODEL.opex||{};
  ['sga_rate','rnd_rate','tax_rate','da','net_interest','minority_rate','other_op','other_nonop','impair'].forEach(function(k){
    if(typeof op[k]==='number') op[k]=[op[k]]; });
  // 拆分比例 λ（母段→子段）：预测段补齐到 F 长，滑块按下标读写
  var sp=MODEL.splits||{};
  Object.keys(sp).forEach(function(k){ var v=sp[k].share; if(v==null)return;
    if(typeof v==='number') v=[v]; else v=v.slice();
    if(v.length&&v.length<F){ var lv=v[v.length-1]; while(v.length<F) v.push(lv); }
    sp[k].share=v; });
  // 境外占比→毛利率的桥：物化基准路径，供滑块算 Δ
  var ob=MODEL.overseas_bridge;
  if(ob&&ob.ov_share){ if(!ob.ov_share_base) ob.ov_share_base=ob.ov_share.slice();
    if(!ob.gm_base){ var tg=(MODEL.segments||[]).filter(function(s){return s.key===ob.target_seg;})[0];
      ob.gm_base=tg&&tg.assume&&tg.assume.gm?tg.assume.gm.slice():[]; } }
}
// 境外占比滑块 → 目标分部毛利率：Δgm = Δ境外占比 × (境外AIDC毛利率 − 境内毛利率) × (全公司营收/该分部收入)
// 基准点上恒等于原假设路径（不改默认值，只提供杠杆）。口径见分部口径卡三。
function applyOverseasBridge(){ var ob=MODEL.overseas_bridge; if(!ob||!ob.gm_base||!ob.gm_base.length) return;
  var segs=MODEL.segments||[], tg=null; segs.forEach(function(s){ if(s.key===ob.target_seg) tg=s; });
  if(!tg) return;
  var pl=EONE.recomputePL(MODEL), H=pl.H, si=segs.indexOf(tg);
  var spread=num(ob.gm_overseas,0.38)-num(ob.gm_domestic,0.24);
  (MODEL.forecast_years||[]).forEach(function(y,i){
    var segRev=num((pl.seg[si]||{}).rev&&pl.seg[si].rev[H+i],0), coRev=num((pl.byYear[H+i]||{}).rev,0);
    var lev=segRev>0?coRev/segRev:0;
    var d=(num(ob.ov_share[i])-num(ob.ov_share_base[i]))*spread*lev;
    tg.assume.gm[i]=Math.max(0.05,Math.min(0.75,num(ob.gm_base[i])+d)); });
}

// ---- Chart.js house defaults + shared tooltip/legend -----------------------
var FONT='"Times New Roman",Times,"KaiTi","楷体","STKaiti",serif';   // 拉丁=TNR, CJK=楷体
function chartDefaults(){ var p=PAL();
  Chart.defaults.color=p.muted; Chart.defaults.borderColor=p.grid;
  Chart.defaults.font.family=FONT; Chart.defaults.font.size=12; Chart.defaults.animation=false;
  if(!Chart.__eone){ Chart.register(stackTotals, endLabels); Chart.__eone=true; } }
function TT(){ var p=PAL(); return { backgroundColor:p.bg, borderColor:p.grid, borderWidth:1,
  titleColor:p.fg, bodyColor:p.fg, displayColors:false, padding:10 }; }
function legPts(){ return { labels:{usePointStyle:true,boxWidth:9,boxHeight:9,color:PAL().muted} }; }
function legLine(){ return { labels:{usePointStyle:true,pointStyle:'line',boxWidth:18,boxHeight:2,color:PAL().muted} }; }
function mkChart(id,cfg){ if(CH[id]) CH[id].destroy(); var c=el(id); if(!c) return null; CH[id]=new Chart(c,cfg); return CH[id]; }

// BCG-style direct labels: total on top of a stacked bar column
var stackTotals = { id:'stackTotals', afterDatasetsDraw:function(ch,a,opts){ if(!opts||!opts.on)return; var ctx=ch.ctx,p=PAL();
  var n=(ch.data.labels||[]).length;
  ctx.save(); ctx.font='bold 11px '+FONT; ctx.textAlign='center'; ctx.fillStyle=p.fg;
  for(var i=0;i<n;i++){ var sum=0, topY=null, x=null;
    ch.data.datasets.forEach(function(ds,di){ if(ds.type==='line')return; var v=parseFloat(ds.data[i]); if(isFinite(v))sum+=v;
      var m=ch.getDatasetMeta(di).data[i]; if(m){ if(topY===null||m.y<topY)topY=m.y; x=m.x; } });
    if(x!=null&&topY!=null&&isFinite(sum)&&sum!==0) ctx.fillText((Math.round(sum*10)/10).toLocaleString(), x, topY-6); }
  ctx.restore(); } };
// BCG-style direct labels: value at the right end of chosen line series
var endLabels = { id:'endLabels', afterDatasetsDraw:function(ch,a,opts){ if(!opts||!opts.series)return; var ctx=ch.ctx;
  ctx.save(); ctx.font='bold 11px '+FONT; ctx.textAlign='left'; ctx.textBaseline='middle';
  opts.series.forEach(function(cfg){ var ds=ch.data.datasets[cfg.di]; if(!ds)return;
    var pts=ch.getDatasetMeta(cfg.di).data; if(!pts||!pts.length)return;
    var i=ds.data.length-1; while(i>=0 && !isFinite(parseFloat(ds.data[i]))) i--;
    if(i<0||!pts[i])return; ctx.fillStyle=ds.borderColor||'#333';
    ctx.fillText(cfg.fmt?cfg.fmt(ds.data[i]):ds.data[i], pts[i].x+6, pts[i].y); }); ctx.restore(); } };
// value-label plugin for bars
var barLabels = { id:'barLabels', afterDatasetsDraw:function(ch,a,opts){ if(!opts||!opts.on)return; var ctx=ch.ctx,p=PAL();
  ctx.save(); ctx.font='10px system-ui'; ctx.textAlign='center'; ctx.fillStyle=p.muted;
  var di=opts.di==null?ch.data.datasets.length-1:opts.di;
  var meta=ch.getDatasetMeta(di); if(!meta)return;
  meta.data.forEach(function(bar,i){ var v=ch.data.datasets[di].data[i]; if(v==null)return;
    var raw=Array.isArray(v)?(Math.abs(v[1]-v[0])):v;
    var t=opts.fmt?opts.fmt(raw):(typeof raw==='number'?(Math.round(raw*10)/10):raw);
    // 负柱的标签压在柱下沿，否则会盖住 0 轴上方的线
    var below=(typeof raw==='number'&&raw<0&&!Array.isArray(v));
    ctx.fillText(t, bar.x, below?(bar.y+11):(bar.y-4)); }); ctx.restore(); } };

/* ===========================================================================
 * KPI header
 * ======================================================================== */
function renderKPI(){ var m=D.meta||{};
  el('kpi-sub').textContent=m.positioning||'';
  var tiles=[
    ['当前市值', yi(m.current_mcap_yi)+' 亿', m.currency||''],
    ['现价', (m.current_price!=null?m.current_price:'—')+(m.price_unit||' 元'), m.price_asof||''],
    ['总股本', yi(m.shares_yi)+' 亿股', ''],
    ['PE(TTM)', (m.pe_ttm!=null?m.pe_ttm+'x':'—'), ''],
    ['数据截止', m.asof||'', m.market||'']
  ];
  el('kpi').innerHTML=tiles.map(function(t){ return '<div class="stat"><div class="k">'+esc(t[0])+'</div><div class="v">'+esc(t[1])+'</div><div class="s">'+esc(t[2])+'</div></div>'; }).join('');
  // meta.note / snapshot.note 属方法论·免责·口径说明 → 不进正文（注意力预算，06 §纪律）。
  // 字段保留在 page_model 里供检索与追溯；有结论性内容的请挪进开篇章。
  el('kpi-note').innerHTML='';
  var h=el('sec-kpi');                                    // 版本徽章：认知螺旋第几轮
  if(m.version&&h&&!h.querySelector('.ver-chip'))
    h.insertAdjacentHTML('beforeend',' <span class="ver-chip" title="'+esc(m.changelog||'')+'">'+esc(m.version)+(m.updated?(' · '+esc(m.updated)):'')+'</span>');
}

/* ===========================================================================
 * 反馈闭环：上一轮标注 → 本版处理记录（已改 / 已答复 / 待补数据）
 * feedback.resolved[] 里每条带 path，渲完给对应 [data-fbk] 打绿边，可一键跳过去。
 * ======================================================================== */
var FB_ACT={fixed:['','本版已改'],answered:['answered','已答复'],pending:['pending','待补数据']};
function renderFeedbackLog(){ var host=el('fb-answers'); if(!host) return;
  var fb=D.feedback||{}; var res=(fb.resolved||[]).slice(), open=(fb.open||[]).slice();
  if(!res.length&&!open.length){ host.innerHTML=''; return; }
  var m=D.meta||{};
  var card=function(x,act){ var a=FB_ACT[act]||FB_ACT.answered;
    return '<div class="fb-ans '+a[0]+'">'
      +'<div class="fa-hd">'+esc(x.id||'')+(x.on_ver?(' · 提于 '+esc(x.on_ver)):'')+(x.sec_title?(' · '+esc(x.sec_title)):'')+(x.reader?(' · '+esc(x.reader)):'')+'</div>'
      +'<div class="fa-ask">'+esc(x.ask||x.note||x.quote||'')+'</div>'
      +'<div class="fa-do"><b>'+a[1]+'：</b>'+esc(x.answer||x.why_pending||'')+'</div>'
      +(x.path?('<div class="fa-link" data-jump="'+esc(x.path)+'">↧ 跳到对应模块</div>'):'')+'</div>'; };
  host.innerHTML='<h2 id="sec-fb" style="margin-top:22px">本版反馈回应（认知螺旋 · '+esc(m.version||'v1')+'）</h2>'
    +'<div class="callout">'+(m.changelog?esc(m.changelog):'上一轮标注的逐条处理：改了什么、答了什么、还缺什么。')
      +'　<span class="small muted">共 '+(res.length+open.length)+' 条：已处理 '+res.length+' · 待补 '+open.length+'</span></div>'
    +'<div class="fb-ans-grid">'+res.map(function(x){ return card(x,x.action||'fixed'); }).join('')
      +open.map(function(x){ return card(x,'pending'); }).join('')+'</div>';
  (fb.resolved||[]).forEach(function(x){ if(!x.path||(x.action&&x.action!=='fixed')) return;
    var n=document.querySelector('[data-fbk="'+cssq(x.path)+'"]'); if(n) n.classList.add('fb-fixed'); });
  if(host.__fbBound) return; host.__fbBound=1;          // 只绑一次(renderFeedbackLog 可被手动重调)
  host.addEventListener('click',function(e){ var j=e.target.closest('[data-jump]'); if(!j) return;
    var n=document.querySelector('[data-fbk="'+cssq(j.getAttribute('data-jump'))+'"]');
    if(!n){ toast('对应模块已重构，路径 '+j.getAttribute('data-jump')+' 未找到'); return; }
    n.scrollIntoView({behavior:'smooth',block:'center'});
    n.classList.add('fb-fixed'); });
  var toc=document.getElementById('toc');
  if(toc&&!toc.querySelector('a[href="#sec-fb"]')){ var a=document.createElement('a'); a.className='l1';
    a.href='#sec-fb'; a.textContent='本版反馈回应'; var p1=toc.querySelector('a[href="#sec-p1"]');
    if(p1) toc.insertBefore(a,p1); else toc.appendChild(a); }
}

/* ===========================================================================
 * PART 1.1 revenue stacked bar + YoY line + event pointers
 * ======================================================================== */
function renderRevenue(){ var r=(D.part1&&D.part1.revenue)||{}; var p=PAL();
  if(!r.years){ el('rev-sub').innerHTML='<span class="datagap">⚠️ 未查到 营收拆分数据</span>'; return; }
  var segs=(r.segments||[]).map(function(s,i){ return { type:'bar',label:s.name,data:s.values,
    backgroundColor:p.s[i%8],stack:'rev',borderWidth:0,yAxisID:'y' }; });
  var yoyDs={ type:'line',label:'总营收YoY',data:r.yoy,borderColor:p.bad,borderWidth:2,pointRadius:0,pointHitRadius:6,tension:0,yAxisID:'y1' };
  var events=r.events||[];
  var pins={ id:'revpins', afterDatasetsDraw:function(ch){ var ctx=ch.ctx,xs=ch.scales.x,area=ch.chartArea;
    ctx.save(); events.forEach(function(ev,i){ var xi=r.years.indexOf(ev.year); if(xi<0)return;
      var x=xs.getPixelForValue(xi), y=area.top+9;
      ctx.beginPath(); ctx.arc(x,y,8,0,6.283); ctx.fillStyle=p.accent; ctx.fill();
      ctx.fillStyle='#fff'; ctx.font='bold 10px system-ui'; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText((i+1),x,y);
      ctx.strokeStyle=p.accent; ctx.globalAlpha=.35; ctx.setLineDash([3,3]); ctx.beginPath(); ctx.moveTo(x,y+9); ctx.lineTo(x,area.bottom); ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha=1;
    }); ctx.restore(); } };
  mkChart('chart-revenue',{ data:{labels:r.years,datasets:segs.concat([yoyDs])},
    options:{ maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
      scales:{ x:{stacked:true,grid:{display:false},ticks:{color:p.muted}},
        y:{stacked:true,position:'left',grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'亿';}},title:{display:true,text:'营业收入(亿元)',color:p.muted,font:{size:11}}},
        y1:{position:'right',grid:{drawOnChartArea:false},ticks:{color:p.muted,callback:function(v){return v+'%';}}} },
      plugins:{ legend:legPts(), stackTotals:{on:true}, tooltip:Object.assign(TT(),{callbacks:{label:function(c){var v=c.raw; return c.dataset.label+': '+(c.dataset.type==='line'?spct(v/100):yi(v)+'亿');}}}) } },
    plugins:[pins] });
  var evlist=events.map(function(ev,i){ return '<b>'+(i+1)+'</b> '+esc(ev.year)+' '+esc(ev.label); }).join(' &nbsp;·&nbsp; ');
  el('rev-sub').innerHTML=(r.caliber?('口径：'+esc(r.caliber)+'。 '):'')+(events.length?('节点 '+evlist):'')+cite(r.cite);
  el('rev-customers').innerHTML=(r.customers||[]).map(function(c){return '<span class="tag" style="border-color:var(--bad);color:var(--bad)">'+esc(c)+'</span>';}).join('')||'<span class="muted">—</span>';
  el('rev-business').innerHTML=(r.business_tags||[]).map(function(b){return '<span class="tag blue">'+esc(b)+'</span>';}).join('')||'<span class="muted">—</span>';
  renderMilestones();
}
// 1.1 业务/客户里程碑 —— 按年份对齐的标注带（红=客户/蓝=业务）
function renderMilestones(){ var r=(D.part1&&D.part1.revenue)||{}; var years=r.years||[]; var ms=r.milestones||[];
  if(!years.length || !ms.length){ el('rev-milestones').innerHTML=''; return; }
  var byYear={}; ms.forEach(function(m){ byYear[m.year]=m; });
  el('rev-milestones').innerHTML='<div class="ms-grid" style="grid-template-columns:repeat('+years.length+',minmax(0,1fr))">'+
    years.map(function(y){ var m=byYear[y]||{}; var cust=m.cust||[], biz=m.biz||[]; var has=cust.length||biz.length;
      return '<div class="ms-col'+(has?' has':'')+'"><div class="ms-yr">'+esc(y)+'</div>'+(has?'<div class="ms-line"></div>':'')+
        cust.map(function(t){return '<div class="ms-item ms-cust">'+esc(t)+'</div>';}).join('')+
        biz.map(function(t){return '<div class="ms-item ms-biz">'+esc(t)+'</div>';}).join('')+
      '</div>'; }).join('')+'</div>';
}

/* ===========================================================================
 * PART 1.2 shareholders concentration + latest top-10 table + subsidiaries
 * ======================================================================== */
function renderHolders(){ var sh=(D.part1&&D.part1.shareholders)||{}; var p=PAL();
  var periods=sh.periods||[];
  var conc=sh.concentration; // 前十大合计%
  if(!conc && sh.top){ conc=sh.top.map(function(t){ return (t.holders||[]).reduce(function(a,h){return a+num(h.pct);},0); }); }
  if(periods.length && conc){
    mkChart('chart-holderconc',{ data:{labels:periods,datasets:[
      {type:'line',label:'前十大合计',data:conc,borderColor:p.s[0],backgroundColor:p.s[0]+'22',fill:'origin',borderWidth:2,pointRadius:2,tension:0} ]},
      options:{ maintainAspectRatio:false, plugins:{legend:{display:false},tooltip:Object.assign(TT(),{callbacks:{label:function(c){return '前十大合计 '+pct(c.raw/100);}}})},
        scales:{x:{grid:{display:false},ticks:{color:p.muted}},y:{grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'%';}}}} } });
  } else { var c=el('chart-holderconc'); if(c)c.parentNode.innerHTML='<span class="datagap">⚠️ 未查到 股东持股比例时序</span>'; }
  // latest top-10 table
  var latest = sh.top && sh.top.length ? sh.top[sh.top.length-1] : null;
  if(latest && latest.holders){
    var rows=latest.holders.map(function(h,i){ return '<tr><td class="num">'+(i+1)+'</td><td>'+esc(h.name)+'</td><td class="num">'+pct(h.pct/100)+'</td><td class="num">'+(h.shares_yi!=null?yi(h.shares_yi):'—')+'</td><td>'+esc(h.nature||'')+'</td></tr>'; }).join('');
    el('tbl-holders').innerHTML='<div class="cap">最新报告期 '+esc(latest.period||'')+' 前十大股东'+cite(sh.cite)+'</div><table><thead><tr><th class="num">#</th><th>股东名称</th><th class="num">持股比例</th><th class="num">持股(亿股)</th><th>性质</th></tr></thead><tbody>'+rows+'</tbody></table>';
  } else el('tbl-holders').innerHTML='<span class="datagap">⚠️ 未查到 前十大股东明细</span>';
}

// 概览 · 最新财务快照（单季 + TTM 年化）
function renderSnapshot(){ var s=(D.part1&&D.part1.snapshot)||(D.meta&&D.meta.snapshot); if(!s){ el('snapshot').innerHTML=''; return; }
  var q=s.latest_q||{}, t=s.ttm||{};
  var tile=function(k,v,sub,cls){ return '<div class="snap-tile"><div class="k">'+esc(k)+'</div><div class="v '+(cls||'')+'">'+esc(v)+'</div><div class="s">'+esc(sub||'')+'</div></div>'; };
  el('snapshot').innerHTML='<div class="snap-title">最新财务快照 · '+esc(q.period||'')+cite(s.cite)+'</div><div class="snap-row">'+
    tile('单季收入', yi(q.rev)+' 亿', 'YoY '+spct(q.rev_yoy)+(q.rev_qoq!=null?(' · QoQ '+spct(q.rev_qoq)):'')) +
    tile('单季归母', yi(q.np)+' 亿', 'YoY '+spct(q.np_yoy)+(q.np_qoq!=null?(' · QoQ '+spct(q.np_qoq)):''), (q.np>=0?'pos':'neg')) +
    tile('单季毛利率', pct(q.gm), q.nm!=null?('净利率 '+pct(q.nm)):'') +
    tile('TTM 收入(年化)', yi(t.rev)+' 亿', t.rev_yoy!=null?('YoY '+spct(t.rev_yoy)):'') +
    tile('TTM 归母(年化)', yi(t.np)+' 亿', t.np_yoy!=null?('YoY '+spct(t.np_yoy)):'') +
    '</div>';   // s.note 同上，不渲
}

/* ★概览 · 类型卡（2026-08-17 石英股份读者反馈固化，10 §2.8）
   读者原话：「需要添加公司的类型：真beta、假beta、sigma、叙事-题材股；然后根据不同的类型给到最核心的参数：
   beta 类给最核心的叙事题材(一个或几个)+定位(龙头/中军/后排)+当前交易的位置(左侧/右侧、回踩、5/10/20 均线排列)；
   sigma 类给预期利润率和 ROE 在历史的什么分位，外加 PE、PS、PB 在历史的什么分位」。
   数据层由 scripts/type_card.py 从 1.7 / 1.3 / 1.4 / 1.5 / 2.1b 合成（都算完了，只是散在四章里）；
   type 由作者定，必须与开篇「股性」beta_kind 钩子说同一句话（CK-7 t2）。 */
var TC_TYPES={'真β':'跟着这条线交易；能用篮子/行业对冲','假β':'标签在、钱不在；别按题材线买','σ':'指数与板块都对冲不掉，仓位按单票风险管','叙事-题材':'按情绪与换手强度交易，不按利润'};
function renderTypeCard(){
  var host=el('type-card'); if(!host) return;
  var tc=(D.summary||{}).type_card; if(!tc){ host.style.display='none'; return; }
  host.style.display='';
  var t=tc.type, isBeta=(t==='真β'||t==='假β'||t==='叙事-题材');
  var h='<div class="tc-type">公司类型：'+(t?('<b>'+esc(t)+'</b>'):'<span class="tc-warn">⚠ 未定（type_card.py 建议 '+esc(tc.suggest||'—')+'，作者按 10 §2.8 填 type）</span>')+
    (t&&TC_TYPES[t]?('<span class="muted"> · '+TC_TYPES[t]+'</span>'):'')+
    (tc.verdict?('<span class="tc-sug">'+esc(tc.verdict)+'</span>'):(tc.basis?('<span class="tc-sug">依据：'+esc(tc.basis)+'</span>'):''))+'</div>';
  // β 面：核心叙事/题材 + 定位 + 方位
  var B=tc.beta||{}, lines=(tc.core_lines&&tc.core_lines.length)?tc.core_lines:(B.lines||[]).slice(0,3);
  var lineTxt=lines.length?lines.map(function(l){
      var tierCls=l.tier==='龙头'?'lead':(l.tier==='中军'?'mid':'');
      return '<span class="tc-chip '+tierCls+'">'+esc(l.name||'')+(l.tier?('·'+esc(l.tier)):'')+'</span>'+
        '<span class="muted">β '+(l.beta!=null?num(l.beta).toFixed(2):'—')+' R² '+(l.r2!=null?num(l.r2).toFixed(2):'—')+
        (l.share_pct!=null?('，占 '+num(l.share_pct)+'%'+(l.rank?(' 排 '+l.rank+'/'+l.of):'')):'')+
        (l.turnover_pct!=null?('，换手 '+Math.round(num(l.turnover_pct))+' 分位'):'')+'</span>'; }).join('　')
    :'<span class="muted">无叙事/题材篮子（未跑 1.7 或港美股）'+(B.bench&&B.bench.beta!=null?('；对'+esc(B.bench.bench||'宽基')+' β '+B.bench.beta+' 相关 '+B.bench.corr):'')+'</span>';
  var P=B.posture||{}, ma=P.ma||{};
  var maTxt=[['MA5',ma.ma5],['MA10',ma.ma10],['MA20',ma.ma20],['MA60',ma.ma60]].filter(function(x){return x[1]!=null;}).map(function(x){return x[0]+' '+num(x[1]).toFixed(2);}).join(' / ');
  var posTxt=P.label?('<b>'+esc(P.label)+'</b>'+(maTxt?('<span class="muted">（'+maTxt+(P.caliber?('；'+esc(P.caliber)):'')+'）</span>'):'')):'<span class="muted">方位未判（K 线不足）</span>';
  var betaRows='<div class="tc-row'+(isBeta?'':' dim')+'"><span class="tc-k">核心叙事线</span><span>'+lineTxt+'</span></div>'+
               '<div class="tc-row'+(isBeta?'':' dim')+'"><span class="tc-k">K 线方位</span><span>'+posTxt+'</span></div>';
  // σ 面：预期利润率 / ROE / PE / PS / PB 的历史分位
  var S=tc.sigma||{}, pq=function(v,d){ return v==null?'—':(d?num(v).toFixed(1):String(Math.round(num(v)))); };
  var pctTxt=function(o,k){ return (o&&o[k]!=null)?('<b>'+o[k]+'</b> 分位'):'<span class="muted">分位不可得</span>'; };
  var nm=S.nm||{}, roe=S.roe||{};
  var sigTxt='预期净利率 '+(nm.fwd!=null?(pq(nm.fwd,1)+'%（'+esc(nm.fwd_label||'FY+1')+'，历史 '+pctTxt(nm,'pct_fwd')+'）'):(nm.ttm!=null?('TTM '+pq(nm.ttm,1)+'%（历史 '+pctTxt(nm,'pct_ttm')+'）'):'—'))+
    '　ROE '+(roe.now!=null?(pq(roe.now,1)+'%（历史 '+pctTxt(roe,'pct')+'）'):'—')+
    ['pe','ps','pb'].map(function(k){ var o=S[k]||{}; return o.now==null?'':('　'+k.toUpperCase()+' '+pq(o.now,1)+'x（窗口 '+pctTxt(o,'pct')+'）'); }).join('')+
    (nm.hist_years?('<span class="muted">　· 历史窗口 '+esc(nm.hist_years)+'；估值分位取 2.1b 窗口</span>'):'');
  var sigRow='<div class="tc-row'+(isBeta?' dim':'')+'"><span class="tc-k">σ 面读数</span><span>'+sigTxt+'</span></div>';
  h+= isBeta ? (betaRows+sigRow) : (sigRow+betaRows);
  if((tc.gaps||[]).length) h+='<div class="tc-row dim"><span class="tc-k">缺口</span><span>'+tc.gaps.map(esc).join('；')+'</span></div>';
  host.innerHTML=h;
}

// 1.2 股东派系构成 + 定价权分析
// 1.2 股东派系构成 —— 近5年逐季时间序列(堆积柱)，只保留百分比图 + 一行定价权结论
/* ★1.2 上市前融资史 + 派系类型（2026-08-12 用户需求）：派系时间序列只从上市起算，
   看不出「这批股东是怎么进来的」——把 IPO 前的融资轮次接到堆积图前面，并给一个类型判定：
   founder=创始人/家族控盘(产业坐庄型) · pe_diluted=上市前多轮稀释(PE 退出型) · soe=国资控股型 · dispersed=无实控人/股权分散型 */
var PREIPO_ARCH={founder:{lb:'创始人/家族控盘 · 产业坐庄型',c:'#8a4b12'},
  pe_diluted:{lb:'上市前股权稀释重 · PE 逐步退出型',c:'#3C3489'},
  soe:{lb:'国资控股型',c:'#0C447C'},
  dispersed:{lb:'无实控人 · 股权分散型',c:'#555'}};
function renderPreIPO(){ var host=el('factions-preipo'); if(!host) return;
  var sh=(D.part1&&D.part1.shareholders)||{}; var pi=sh.pre_ipo;
  if(!pi){ host.innerHTML='<div class="cap muted">（未收录上市前融资史 · shareholders.pre_ipo）</div>'; return; }
  var ar=PREIPO_ARCH[pi.archetype]||null;
  var head=(ar?('<span class="preipo-arch" style="border-color:'+ar.c+';color:'+ar.c+'">'+esc(ar.lb)+'</span>'):'')
    +(pi.archetype_note?('<span class="preipo-note">'+esc(pi.archetype_note)+'</span>'):'')+cite(pi.cite);
  var chips=(pi.rounds||[]).map(function(r){
    return '<span class="preipo-rd"><b>'+esc(r.round||'')+'</b><i>'+esc(r.date||'')+'</i>'
      +((r.investors||[]).length?('<em>'+esc(r.investors.slice(0,3).join('/'))+((r.investors||[]).length>3?'…':'')+'</em>'):'')
      +(r.post_val_yi!=null?('<u>投后 '+yi(r.post_val_yi)+' 亿</u>'):'')
      +(r.founder_pct!=null?('<s>创始人 '+pct(r.founder_pct/100,0)+'</s>'):'')
      +(r.note?('<span class="rd-note">'+esc(r.note)+'</span>'):'')+'</span>'; }).join('<span class="preipo-arr">→</span>');
  var ipoChip='<span class="preipo-rd ipo"><b>IPO</b>'
    +(pi.ipo_founder_pct!=null?('<s>创始人 '+pct(pi.ipo_founder_pct/100,0)+'</s>'):'')
    +(pi.pe_ipo_pct!=null?('<u>PE/VC 合计 '+pct(pi.pe_ipo_pct/100,0)+'</u>'):'')+'</span>';
  var meter='';
  if(pi.pe_ipo_pct!=null&&pi.pe_now_pct!=null&&pi.pe_ipo_pct>0){
    var done=Math.max(0,Math.min(1,1-pi.pe_now_pct/pi.pe_ipo_pct));
    meter='<div class="preipo-meter"><span class="pm-k">PE/VC 退出进度</span>'
      +'<span class="pm-track"><i style="width:'+(Math.round(done*100))+'%"></i></span>'
      +'<span class="pm-v">IPO 时 '+pct(pi.pe_ipo_pct/100,0)+' → 现 '+pct(pi.pe_now_pct/100,0)
      +'（已退 '+pct(done,0)+'）</span></div>'; }
  host.innerHTML='<div class="preipo-hd">上市前融资 → IPO → 退出'+head+'</div>'
    +((pi.rounds||[]).length?('<div class="preipo-line">'+chips+'<span class="preipo-arr">→</span>'+ipoChip+'</div>'):'')
    +meter;
}
function renderFactions(){ var sh=(D.part1&&D.part1.shareholders)||{}; var p=PAL();
  renderPreIPO();
  var ts=sh.factions_ts;
  if(ts&&ts.periods&&ts.series){
    var ds=ts.series.map(function(s,i){ return {label:s.faction,data:s.values,backgroundColor:s.color||p.s[i%8],stack:'f',borderWidth:0}; });
    mkChart('chart-factions',{ type:'bar', data:{labels:ts.periods,datasets:ds},
      options:{ maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
        plugins:{ legend:legPts(), tooltip:Object.assign(TT(),{callbacks:{label:function(c){return c.dataset.label+': '+pct(c.raw/100);}}}) },
        scales:{ x:{stacked:true,grid:{display:false},ticks:{color:p.muted,maxTicksLimit:12}}, y:{stacked:true,max:100,grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'%';}}} } } });
  } else {
    var fs=sh.factions||[];
    // 无派系序列时仍要渲「定价权判断」——港美韩股这一格结构性缺失，正是最需要那段文字的时候
    if(!fs.length){ el('faction-analysis').innerHTML='<span class="datagap">⚠️ 未生成 股东派系时间序列（shareholders.factions_ts：近5年逐季）</span>'
        +(sh.faction_analysis?('<div class="callout"><b>定价权判断：</b>'+esc(sh.faction_analysis)+cite(sh.faction_cite)+'</div>'):''); return; }
    mkChart('chart-factions',{ type:'bar', data:{labels:['最新期'],datasets:fs.map(function(f,i){ return {label:f.faction,data:[num(f.pct)],backgroundColor:f.color||p.s[i%8],stack:'f',borderWidth:0}; })},
      options:{ indexAxis:'y', maintainAspectRatio:false, plugins:{legend:legPts(),tooltip:Object.assign(TT(),{callbacks:{label:function(c){return c.dataset.label+': '+pct(c.raw/100);}}})},
        scales:{ x:{stacked:true,max:100,grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'%';}}}, y:{stacked:true,grid:{display:false},ticks:{display:false}} } } });
  }
  el('faction-analysis').innerHTML=sh.faction_analysis?('<div class="callout"><b>定价权判断：</b>'+esc(sh.faction_analysis)+cite(sh.faction_cite)+'</div>'):'';
}

// 1.2 股权结构树（实控人→平台→上市公司→子公司分类）
function renderOwnership(){ var o=(D.part1&&D.part1.ownership); var p=PAL();
  if(!o){ el('ownership-tree').innerHTML='<span class="datagap">⚠️ 未生成 股权结构（qcc: get_actual_controller/beneficial_owners/external_investments）</span>'; return; }
  var ctrl=(o.controllers||[]).map(function(c){ return '<span class="own-chip ctrl">'+esc(c.name)+(c.pct!=null?(' '+pct(c.pct/100,1)):'')+(c.role?('<small>'+esc(c.role)+'</small>'):'')+'</span>'; }).join('');
  var direct=(o.direct||[]).map(function(c){ return '<span class="own-chip">'+esc(c.name)+' '+pct(c.pct/100,1)+'</span>'; }).join('');
  var groups=(o.sub_groups||[]).map(function(g){ return '<div class="own-group" style="border-top-color:'+(g.color||p.accent)+'"><div class="og-hd">'+esc(g.group)+(g.note?(' · '+esc(g.note)):'')+'</div><div class="og-subs">'+
    (g.subs||[]).map(function(s){ return '<div class="og-sub"><div class="sn">'+esc(s.name)+' <span class="sp">'+(s.stake!=null?pct(s.stake/100,0):'')+'</span></div><div class="sb">'+esc(s.business||'')+'</div>'+(s.location?('<div class="sl">📍'+esc(s.location)+'</div>'):'')+'</div>'; }).join('')+
    '</div></div>'; }).join('');
  el('ownership-tree').innerHTML=
    '<div class="own-tier"><div class="own-lbl">实控人 / 一致行动人（持控股平台）</div><div class="own-boxes">'+(ctrl||'<span class="muted">—</span>')+'</div></div>'+
    '<div class="own-arrow">▼</div>'+
    '<div class="own-tier"><div class="own-boxes"><span class="own-chip platform">'+esc((o.platform||{}).name||'控股平台')+' '+pct(((o.platform||{}).pct||0)/100,1)+'</span>'+(direct?('<span class="own-sep">＋个人直接</span>'+direct):'')+(o.float_pct!=null?('<span class="own-chip float">其它流通 '+pct(o.float_pct/100,1)+'</span>'):'')+'</div></div>'+
    '<div class="own-arrow">▼</div>'+
    '<div class="own-listed">'+esc((D.meta||{}).name||'上市公司')+'</div>'+
    '<div class="own-arrow">▼ 控股/参股子公司（按业务分类）</div>'+
    '<div class="own-groups">'+groups+'</div>';
}

/* ===========================================================================
 * PART 1.3 ROE + DuPont
 * ======================================================================== */
function renderDupont(){ var d=(D.part1&&D.part1.dupont)||{}; var p=PAL();
  if(!d.years){ var c=el('chart-dupont'); if(c)c.parentNode.innerHTML='<span class="datagap">⚠️ 未查到 ROE/杜邦数据</span>'; return; }
  /* ★2026-08-16 改复合图（赛力斯 v3.2 读者反馈）：**被解释量走柱，解释项走线**。
     原来四条线同型，读者要靠图例才知道哪条是结果、哪条是拆解项；ROE 是杜邦式的左边，
     三个乘数是右边，图形上必须分型——柱＝要解释的那个数，线＝把它拆开的三个因子。 */
  var mkL=function(name,data,color,axis,dash){ return {type:'line',label:name,data:data,borderColor:color,borderWidth:2,pointRadius:2,pointHitRadius:6,tension:0,yAxisID:axis,borderDash:dash||[],order:1}; };
  var roeBar={type:'bar',label:'ROE',data:d.roe,yAxisID:'y',order:9,borderWidth:0,barPercentage:0.62,categoryPercentage:0.8,
    backgroundColor:(d.roe||[]).map(function(v){ return num(v)<0?(hexA(p.bad,'66')||p.bad):(hexA(p.s[0],'8c')||p.s[0]); })};
  mkChart('chart-dupont',{ type:'bar', data:{labels:d.years,datasets:[
      roeBar, mkL('净利率',d.net_margin,p.s[1],'y'),
      mkL('总资产周转率',d.asset_turnover,p.s[2],'y1',[5,4]), mkL('权益乘数',d.equity_multiplier,p.s[4],'y1',[2,3]) ]},
    options:{ maintainAspectRatio:false, interaction:{mode:'index',intersect:false}, layout:{padding:{right:58}},
      scales:{ x:{grid:{display:false},ticks:{color:p.muted}},
        y:{position:'left',grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'%';}},title:{display:true,text:'ROE(柱) / 净利率(线)　%',color:p.muted,font:{size:11}}},
        y1:{position:'right',grid:{drawOnChartArea:false},ticks:{color:p.muted,callback:function(v){return v+'×';}},title:{display:true,text:'周转率(次)/乘数(倍)　×',color:p.muted,font:{size:11}}} },
      plugins:{ legend:legLine(), endLabels:{series:[{di:1,fmt:function(v){return '净利 '+v+'%';}}]},
        barLabels:{on:true,di:0,fmt:function(v){return (Math.round(v*10)/10)+'%';}},
        tooltip:Object.assign(TT(),{displayColors:true,callbacks:{label:function(c){var t=c.dataset.label; var v=c.raw; return t+': '+(t==='ROE'||t==='净利率'?pct(v/100):v+'×');}}}) } },
    plugins:[barLabels] });
}

/* ===========================================================================
 * PART 1.4 cost/expense — rate trend (stacked area) <-> profit waterfall
 * ======================================================================== */
var costMode='rate';
function renderCost(){ var c=(D.part1&&D.part1.cost_structure_q)||{}; var p=PAL();
  var qs=c.quarters||[];
  if(!qs.length){ var cc0=el('chart-cost');
    if(cc0) cc0.parentNode.innerHTML='<span class="datagap">⚠️ 未查到 季度成本费用数据（part1.cost_structure_q）——'
      +'跑 <code>python3 scripts/fetch_quarterly.py --name &lt;名&gt; --ticker &lt;码&gt; --y0 &lt;上市年&gt; --model &lt;page_model&gt; --write</code></span>';
    return; }
  el('btn-cost-rate').classList.toggle('on',costMode==='rate');
  el('btn-cost-fall').classList.toggle('on',costMode==='fall');
  var g=function(k){ return (c[k]||[]).map(function(v){ return (v==null||!isFinite(v))?null:num(v); }); };
  var gmA=g('gross_margin');

  if(costMode==='rate'){
    /* ★2026-08-18 用户定稿：**逐季 · 堆积面积图 · 只留 净利率 + 四费 + 税费 + 其他**。
       毛利率不画成一条线——**堆起来的那条上沿就是它**。
       「其他」是一个桶，把剩下的全装进去（减值 / 其他收益(政府补助) / 投资收益 / 公允价值变动 /
       营业外收支 / 少数股东损益），按恒等式反算，所以恒等式永远严格成立：

         毛利率 ＝ 净利率 ＋ 销售 ＋ 管理 ＋ 研发 ＋ 财务费用率 ＋ 税费 ＋ 其他

       为什么面积图比柱状图对：Chart.js 的**堆积折线是代数累加**（负值也照样累加进running total），
       所以上沿恒等于各段之和＝毛利率；柱状堆积则把正负段分到零轴两侧，视觉顶 ≠ 总和，
       亏损期公司要靠额外画一根记号才读得对。面积图不需要那根记号。
       为什么逐季：费率的结构变化（研发爬坡、补贴退坡、规模摊薄）是**季度级**发生的，
       年度序列会把拐点抹成一条斜线。 */
    el('cost-title').textContent='毛利率分解（逐季 · 堆积面积，上沿＝毛利率）';
    var SEG=[
      {k:'net_margin',    label:'净利率（留给股东的）', col:p.good},
      {k:'sell_exp_rate', label:'销售费用率',          col:p.s[6]},
      {k:'admin_exp_rate',label:'管理费用率',          col:p.s[2]},
      {k:'rnd_exp_rate',  label:'研发费用率',          col:p.s[3]},
      {k:'fin_exp_rate',  label:'财务费用率',          col:p.s[7]},
      {k:'tax_rate',      label:'税费（税金及附加＋所得税）', col:p.s[4]}
    ];
    var have=SEG.filter(function(x){ return (c[x.k]||[]).some(function(v){return v!=null&&isFinite(v);}); });
    var miss=SEG.filter(function(x){ return have.indexOf(x)<0; });
    var other=qs.map(function(_,i){ if(gmA[i]==null) return null;
      var s=0; have.forEach(function(x){ var v=(c[x.k]||[])[i]; if(v!=null&&isFinite(v)) s+=num(v); });
      return Math.round((gmA[i]-s)*1000)/1000; });
    /* ★★ fill 必须是 '-1'（填到**上一层**），不是 true。
       `fill:true` ＝ 填到零轴：每一层都从自己的高度一路铺到 0，七层全部叠在一起糊成一片，
       看上去像半透明的重叠而不是堆积——那不是堆积图，是七张各自独立的面积图摞着。
       第一层（净利率）填到 origin，其余逐层填到前一层，band 才是彼此相邻、互不重叠的。
       背景色同时改成不透明（原来 42% alpha 也在助长「看着像叠着」）。 */
    var mkA=function(label,data,color,dash,first){ return {label:label,data:data,
      borderColor:hexA(color,'00')||color, backgroundColor:color, borderWidth:0, borderDash:dash||[],
      fill:first?'origin':'-1', tension:0, pointRadius:0, pointHitRadius:8, spanGaps:false}; };
    var ds=have.map(function(x,i){ return mkA(x.label,g(x.k),x.col,null,i===0); });
    ds.push(mkA('其他（减值/政府补助/投资收益/营业外/少数股东…）',other,p.ink3||p.muted,null,false));

    /* ★纵轴稳健截断。分母是**单季营业总收入**，上市初期收入极小的公司（寒武纪 2020Q1 营收 0.12 亿、
       研发费用率 1300%）会把量域拉到 ±1500%，最近八个季度的真实结构被压成贴着零轴的一条线——
       那时候读者什么也读不出来。做法：轴范围按**最近 8 季**的堆积上下沿定（×1.2 留白），
       更早的极端季度让它出界，并在图注里逐一点名被截掉的是谁、极值多少。
       悬停仍给真值，所以信息没丢，只是不让 2020 年的比率绑架整张图。 */
    var bnd=qs.map(function(_,i){ var run=0, lo=0, hi=0;
      ds.forEach(function(d){ var v=d.data[i]; if(v==null) return; run+=num(v); lo=Math.min(lo,run); hi=Math.max(hi,run); });
      return [lo,hi]; });
    var rec=bnd.slice(-8), mx=10;
    rec.forEach(function(b){ mx=Math.max(mx,Math.abs(b[0]),Math.abs(b[1])); });
    var cap=Math.ceil(mx*1.2/10)*10;
    var clipped=[]; bnd.forEach(function(b,i){ if(Math.abs(b[0])>cap||Math.abs(b[1])>cap)
      clipped.push({q:qs[i], v:Math.round(Math.max(Math.abs(b[0]),Math.abs(b[1])))}); });

    mkChart('chart-cost',{ type:'line', data:{labels:qs,datasets:ds},
      options:{ maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
        scales:{ x:{grid:{display:false},ticks:{color:p.muted,autoSkip:true,maxTicksLimit:18,maxRotation:60,minRotation:0,font:{size:10.5}}},
          y:{stacked:true,min:-cap,max:cap,grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'%';}},
             title:{display:true,text:'占单季营业总收入 %　（上沿＝毛利率）',color:p.muted,font:{size:11}}} },
        plugins:{ legend:legPts(),
          tooltip:Object.assign(TT(),{displayColors:true,callbacks:{
            label:function(x){ return x.dataset.label+': '+(x.raw==null?'—':(Math.round(num(x.raw)*100)/100)+'%'); },
            footer:function(items){ var i=items&&items[0]?items[0].dataIndex:-1;
              if(i<0) return '';
              var t=(gmA[i]==null?'':'毛利率合计 '+(Math.round(gmA[i]*10)/10)+'%');
              var r=(c.rev_yi||[])[i]; return t+(r!=null?('　单季营收 '+yi(r)+'亿'):''); }}}) } } });

    var neg=other.filter(function(v){return v!=null&&v<0;}).length;
    var clipNote=clipped.length
      ? ('<div class="callout warn" style="margin:6px 0;font-size:12.5px"><b>纵轴已截到 ±'+cap+'%</b>'
         +'（按最近 8 季的量域定）。上市初期营收还很小，费率＝费用÷营收会大到把近期结构压成一条线——'
         +'<b>被截出界的 '+clipped.length+' 个季度：</b>'
         +clipped.slice(0,6).map(function(x){ return esc(x.q)+' 峰值 '+x.v+'%'; }).join('、')
         +(clipped.length>6?(' 等 '+clipped.length+' 季'):'')
         +'。<b>悬停仍给真值</b>，信息没丢；只是不让 2020 年的比率绑架整张图。</div>')
      : '';
    el('cost-sub').innerHTML=clipNote+
      '<b>恒等式：毛利率 ＝ 净利率 ＋ 销售 ＋ 管理 ＋ 研发 ＋ 财务费用率 ＋ 税费 ＋ 其他。</b>'
      +'每一季堆起来的<b>上沿就是当季毛利率</b>，往下每一层是它被谁拿走了；<b>最底下那层是留给股东的</b>。'
      +'<br>口径：全部占<b>单季营业总收入</b>；<b>「税费」＝税金及附加＋所得税费用</b>（同分母，<b>不是实际税率</b>）；'
      +'「其他」是一个桶，装剩下的全部——减值损失、其他收益（政府补助）、投资收益、公允价值变动、营业外收支、少数股东损益，'
      +'按恒等式反算，<b>它落到零轴下方说明这些项净贡献了利润</b>（'+neg+'/'+qs.length+' 个季度如此），不是算错。'
      +'<br>数据：'+esc(c.src||'iFind 单季度.* 原生指标')+'（<b>不是拿累计差分</b>）　区间 '+esc(String(qs[0]||''))+' ~ '+esc(String(qs[qs.length-1]||''))
      +(c.listing_year?('　起点 '+esc(String(c.listing_year))+' 上市'):' <span class="datagap">（未标 listing_year，无法核对是否自上市首季起）</span>')
      +cite(c.cite)
      +(miss.length?('<div class="datagap" style="margin-top:4px">⚠️ 未取到 '+miss.map(function(x){return esc(x.label);}).join('、')
          +'，已并入「其他」——该桶因此偏大。</div>'):'')
      +((c.gaps&&c.gaps.length)?('<div class="datagap" style="margin-top:4px">⚠️ '+c.gaps.map(esc).join('；')+'</div>'):'');
  } else {
    // 利润瀑布：取最新一个季度，金额由 单季营收 × 各费率 还原
    var i=qs.length-1; while(i>0 && (c.rev_yi||[])[i]==null) i--;
    var rev=num((c.rev_yi||[])[i]);
    el('cost-title').textContent='利润瀑布 '+(qs[i]||'')+'（单季：营收 → 成本 → 毛利 → 四费 → 税费 → 归母，单位亿元）';
    var at=function(k){ var v=(c[k]||[])[i]; return (v==null||!isFinite(v))?0:rev*num(v)/100; };
    var opc=rev-at('gross_margin');
    var steps=[['营业总收入',rev,'tot'],['营业成本',-opc,'neg'],['毛利',null,'sub'],
               ['销售费用',-at('sell_exp_rate'),'neg'],['管理费用',-at('admin_exp_rate'),'neg'],
               ['研发费用',-at('rnd_exp_rate'),'neg'],['财务费用',-at('fin_exp_rate'),'neg'],
               ['税费',-at('tax_rate'),'neg'],['归母净利润(其余入其他)',null,'sub']];
    var run=0, labels=[], bars=[], colors=[];
    steps.forEach(function(s){ labels.push(s[0]);
      if(s[2]==='tot'){ bars.push([0,s[1]]); colors.push(p.s[0]); run=s[1]; }
      else if(s[2]==='sub'){ bars.push([0,run]); colors.push(p.s[3]); }
      else { var to=run+s[1]; bars.push([run,to]); colors.push(s[1]<0?p.bad:p.good); run=to; } });
    mkChart('chart-cost',{ type:'bar', data:{labels:labels,datasets:[{label:'金额(亿)',data:bars,backgroundColor:colors,borderWidth:0,barPercentage:0.7}]},
      options:{ maintainAspectRatio:false, plugins:{legend:{display:false},tooltip:Object.assign(TT(),{callbacks:{label:function(x){var a=x.raw;return yi(Math.abs(a[1]-a[0]))+'亿';}}}),barLabels:{on:true,di:0}},
        scales:{ x:{grid:{display:false},ticks:{color:p.muted,maxRotation:30,minRotation:0}}, y:{grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'亿';}}} } },
      plugins:[barLabels] });
    el('cost-sub').innerHTML=esc(qs[i])+' 单季利润瀑布（金额＝单季营收 × 各费率还原）。末端与实际归母的差额＝「其他」桶，'
      +'在堆积图里是单独一层。'+cite(c.cite);
  }
}

/* ===========================================================================
 * PART 1.4b 利润 vs 经营现金流 · 资本开支 · 折旧   数据源 iFind 单季度.* 原生指标
 * ---------------------------------------------------------------------------
 * ★2026-08-18 用户新增，同日按「不要你随便搞」重做取数口径。
 *   ① 经营现金流 vs 归母净利润 —— 利润的含金量。长期背离＝应收/存货在吃现金，或利润里有非现金项。
 *   ② CAPEX vs 折旧 —— 在扩张还是在维持。铺下去的产能两三年后以折旧回来压毛利率（接回 1.4）。
 *
 * ★★ 折旧那条线为什么不是逐季的：**A 股季报不含现金流量表补充资料**，
 *    折旧摊销一年只有中报、年报两个披露点（实测 688256：0630/1231 有值，0331/0930 空）。
 *    单季折旧在报表上**不存在**，所以这里不摊平、不插值：
 *      · 单季视图只画三条（经营现金流/归母/CAPEX，全部取 iFind `单季度.*` 原生指标）；
 *        折旧不画——半年值摆在单季轴上会被读大一倍，那比"估算"更糟，它长得像真值。
 *      · 滚动四季视图才画折旧，且**只在 Q2 / Q4 有点**（TTM 恰好由披露的累计数精确凑出），
 *        Q1/Q3 留空，线段是把两个真实点连起来的视觉连接。
 *    默认落在滚动四季视图：两个读数（含金量、扩张强度）本来就是 TTM 概念，单季比值全是噪声。
 * 四条同为金额（亿元），共用一根左轴——不给第二根轴（CK-8 通则③）。
 * ======================================================================== */
var cashMode='ttm';
function renderCashCapex(){ var cc=(D.part1&&D.part1.cash_capex)||{}; var p=PAL();
  var wrap=el('cash-wrap'); if(!wrap) return;
  var qs=cc.quarters||[];
  if(!qs.length){ wrap.style.display='none';
    try{ var tl=document.querySelector('a[href="#sec-cash"]'); if(tl){ (tl.closest('li')||tl).style.display='none'; } }catch(e){}
    return; }
  wrap.style.display='';
  var isT=(cashMode==='ttm')&&!!(cc.ttm&&(cc.ttm.ocf||[]).length);
  if(!(cc.ttm&&(cc.ttm.ocf||[]).length)) cashMode='q';
  var bq=el('btn-cash-q'), bt=el('btn-cash-ttm');
  if(bq) bq.classList.toggle('on',!isT);
  if(bt){ bt.classList.toggle('on',isT); bt.style.display=(cc.ttm&&(cc.ttm.ocf||[]).length)?'':'none'; }
  var S=isT?cc.ttm:cc;
  var arr=function(k){ return (S[k]||[]).map(function(v){ return (v==null||!isFinite(parseFloat(v)))?null:num(v); }); };
  var ocf=arr('ocf'), np=arr('np'), capex=arr('capex'), da=isT?arr('da'):[];

  var mkL=function(label,data,color,dash){ return {label:label,data:data,borderColor:color,
    backgroundColor:color, borderWidth:2, borderDash:dash||[], tension:0, spanGaps:true, fill:false,
    /* 「数据点加重一些」：实心大圆点，让每个季度都是一个可数的观测 */
    pointRadius:data.map(function(v){ return v==null?0:3.4; }), pointHoverRadius:6.5,
    pointStyle:'circle', pointBackgroundColor:color, pointBorderColor:p.panel, pointBorderWidth:1.4 }; };
  var ds=[ mkL('经营活动现金流净额',ocf,p.s[1]),
           mkL('归母净利润',np,p.s[0]),
           mkL('CAPEX（购建长期资产支付的现金）',capex,p.s[2]) ];
  var nDA=da.filter(function(v){return v!=null;}).length;
  if(isT&&nDA) ds.push(mkL('折旧与摊销（仅中报/年报披露，一年两点）',da,p.s[4],[5,3]));

  el('cash-title').textContent=(isT?'滚动四季（TTM）':'单季')+'：经营现金流 · 归母净利润 · CAPEX'+((isT&&nDA)?' · 折旧摊销':'')+'（'+MONEYU()+'）';
  mkChart('chart-cash',{ type:'line', data:{labels:qs,datasets:ds},
    options:{ maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
      scales:{ x:{grid:{display:false},ticks:{color:p.muted,autoSkip:true,maxTicksLimit:16,maxRotation:60,minRotation:0,font:{size:10.5}}},
        y:{grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'亿';}},
           title:{display:true,text:'金额　'+MONEYU()+'（四条同量纲，共用一轴）',color:p.muted,font:{size:11}}} },
      plugins:{
        /* 图例自造：默认 usePointStyle 图例拿 pointBorderColor 当描边色，而这里描边是面板色（白），
           样标会变成白线画在白底上整个消失。自造之后样标就是线本身的颜色与虚实。 */
        legend:{ labels:{ usePointStyle:true, boxWidth:20, boxHeight:2, color:p.muted,
          generateLabels:function(ch){ return (ch.data.datasets||[]).map(function(d,i){
            return { text:d.label, pointStyle:'line', fillStyle:d.borderColor, strokeStyle:d.borderColor,
                     lineWidth:2.4, lineDash:d.borderDash||[], hidden:!ch.isDatasetVisible(i), datasetIndex:i }; }); } } },
        tooltip:Object.assign(TT(),{displayColors:true,callbacks:{
          label:function(x){ return x.dataset.label+': '+(x.raw==null?'未披露':(yi(x.raw)+'亿')); }}}) } } });

  /* ---- 读数：一律走 TTM（含金量与扩张强度本来就是滚动概念，单季比值全是噪声）---- */
  var T=cc.ttm||{};
  var lastOf=function(k){ var a=(T[k]||[]); for(var i=a.length-1;i>=0;i--){ if(a[i]!=null&&isFinite(a[i])) return {v:num(a[i]),q:qs[i]}; } return null; };
  var Focf=lastOf('ocf'), Fnp=lastOf('np'), Fcap=lastOf('capex'), Fda=lastOf('da');
  var r=function(x,y){ return (!x||!y||!y.v)?null:(Math.round(x.v/y.v*100)/100); };
  var cashQ=r(Focf,Fnp), capD=r(Fcap,Fda);
  var fcf=(!Focf||!Fcap)?null:(Math.round((Focf.v-Fcap.v)*10)/10);
  var stat=function(k,v,s,col){ return '<div class="stat"><div class="k">'+k+'</div>'
    +'<div class="v"'+(col?(' style="color:'+col+'"'):'')+'>'+v+'</div><div class="s">'+s+'</div></div>'; };
  el('cash-read').innerHTML='<div class="stat-row" style="margin-top:10px">'
    +stat('利润含金量　OCF ÷ 归母净利',(cashQ==null?'—':cashQ.toFixed(2)+'×'),
        'TTM 截至 '+esc((Focf||{}).q||'—')+'：'+(Focf?yi(Focf.v):'—')+'亿 ÷ '+(Fnp?yi(Fnp.v):'—')
        +'亿　>1 利润有现金支撑，长期 <0.7 说明利润被应收/存货占住',
        cashQ==null?null:(cashQ>=1?p.good:(cashQ<0.7?p.bad:null)))
    +stat('扩张强度　CAPEX ÷ 折旧',(capD==null?'—':capD.toFixed(2)+'×'),
        (Fda?('TTM 截至 '+esc(Fda.q)+'（折旧最近一个可算的滚动点）：'+(Fcap?yi(Fcap.v):'—')+'亿 ÷ '+yi(Fda.v)+'亿')
             :'折旧无可算的 TTM 点（中报/年报都缺）')
        +'　≈1 只是维持，>1.5 在铺产能（未来两三年回来压毛利率）',
        capD==null?null:(capD>=1.5?p.s[2]:null))
    +stat('经营自由现金流　OCF − CAPEX',(fcf==null?'—':(yi(fcf)+'亿')),
        'TTM；为负＝这四个季度经营赚的钱不够付资本开支', fcf==null?null:(fcf<0?p.bad:p.good))
    +'</div>';

  var dis=cc.da_disclosure||[];
  el('cash-sub').innerHTML=
    '<b>三条同为金额（'+MONEYU()+'）共用一根左轴。</b>'+esc(cc.caliber||'')
    +'<br><b>折旧摊销这条线跟其他三条不是一个频率：</b>'+esc(cc.da_note||'')
    +(dis.length?('<br>披露点（原值，未摊平）：'+dis.slice(-6).map(function(d){
        return '<b>'+esc(d.period)+'</b> '+yi(d.yi)+'亿'; }).join('　')
        +(dis.length>6?('　…共 '+dis.length+' 段'):'')):'')
    +(isT?'':'<div class="datagap" style="margin-top:4px">当前是<b>单季</b>视图，折旧摊销不在图上——单季折旧在报表上不存在。切到「滚动四季(TTM)」看它。</div>')
    +'<br>窗口 '+esc(String(qs[0]||''))+' ~ '+esc(String(qs[qs.length-1]||''))+'　数据源 '+esc(cc.src||'iFind')
    +cite(cc.cite)
    +((cc.gaps&&cc.gaps.length)?('<div class="datagap" style="margin-top:4px">⚠️ '+cc.gaps.map(esc).join('；')+'</div>'):'');
}

/* ===========================================================================
 * PART 1.5 券商预期区间 vs 实际披露   数据源 FMP（schema 2）
 * ---------------------------------------------------------------------------
 * ★ 图形：**实际披露值 = 柱**；券商预测区间 = 叠在柱上的误差线（上下沿+须帽）。
 *   已披露期：实心柱=实际值 │ 误差线=券商 Low–High │ ▬=区间均值 │ ○=财报前一致预期
 *   未来期  ：空心柱=区间均值 │ 误差线=Low–High │ ◆=第三章模型值（随滑块动）
 *
 * ★ 为什么不叫「箱线图」：FMP `analyst-estimates` 一期只返回 Low/Avg/High + numAnalysts，
 *   **没有任何分位数字段**，也不给逐家机构明细。箱线图的箱体需要 Q1/中位数/Q3——一个都拿不到。
 *   而且剔除合成区间后样本本身也薄（002371 年度非合成仅 6 期、季度覆盖 2–8 家），
 *   n<5 算四分位统计上无意义。所以这里画的是**全距误差线**，不是箱线图，措辞不许含糊。
 * ======================================================================== */
var consPeriod='annual', consMetric='rev';
var CONS_METRIC = { rev:{key:'rev',name:'收入',unit:'亿'}, np:{key:'np',name:'净利润',unit:'亿'}, eps:{key:'eps',name:'EPS',unit:''} };

function consAll(){
  var c=(D.part1&&D.part1.consensus)||{};
  return (consPeriod==='quarter'?c.quarters:c.years)||[];
}
function consRows(){
  var src=consAll();
  var past=src.filter(function(r){return !r.is_future;});
  var fut=src.filter(function(r){return r.is_future;});
  var nP=(consPeriod==='quarter')?8:6, nF=(consPeriod==='quarter')?8:4;
  return past.slice(-nP).concat(fut.slice(0,nF));
}
function consStats(){
  var c=(D.part1&&D.part1.consensus)||{};
  var s=c.stats&&c.stats[consPeriod==='quarter'?'quarter':'annual'];
  return (s&&s[consMetric])||null;
}

/* 误差线层：区间上下沿+须帽 / ▬均值 / ○财报前预期 / ◆模型 / n= / 今天分界 */
var rangeDeco = { id:'rangeDeco', afterDatasetsDraw:function(ch,a,opts){
  if(!opts||!opts.rows) return; var ctx=ch.ctx, p=PAL(), ys=ch.scales.y;
  var meta=ch.getDatasetMeta(0); if(!meta||!meta.data) return;
  ctx.save();
  var fi=opts.rows.findIndex(function(r){return r.is_future;});
  if(fi>0&&meta.data[fi]&&meta.data[fi-1]){
    var xm=(meta.data[fi].x+meta.data[fi-1].x)/2;
    ctx.save(); ctx.setLineDash([5,4]); ctx.strokeStyle=p.muted; ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(xm,ch.chartArea.top); ctx.lineTo(xm,ch.chartArea.bottom); ctx.stroke();
    ctx.setLineDash([]); ctx.font='10px system-ui'; ctx.fillStyle=p.muted;
    ctx.textAlign='left';  ctx.fillText('未来预期 →', xm+5, ch.chartArea.top+11);
    ctx.textAlign='right'; ctx.fillText('← 已披露',  xm-5, ch.chartArea.top+11);
    ctx.restore();
  }
  meta.data.forEach(function(bar,i){
    var r=opts.rows[i]; if(!r) return;
    var cap=Math.max((bar.width||24)*0.28, 4);
    if(r.synthetic){ ctx.save(); ctx.globalAlpha=0.4; }
    if(r.lo!=null&&r.hi!=null){                       // 误差线：区间竖线 + 上下须帽
      var yL=ys.getPixelForValue(r.lo), yH=ys.getPixelForValue(r.hi);
      ctx.strokeStyle=p.fg; ctx.lineWidth=1.3;
      ctx.beginPath(); ctx.moveTo(bar.x,yL); ctx.lineTo(bar.x,yH); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(bar.x-cap,yL); ctx.lineTo(bar.x+cap,yL);
                       ctx.moveTo(bar.x-cap,yH); ctx.lineTo(bar.x+cap,yH); ctx.stroke();
    }
    if(r.avg!=null){                                  // ▬ 区间均值
      var yA=ys.getPixelForValue(r.avg);
      ctx.strokeStyle=p.fg; ctx.lineWidth=2.6;
      ctx.beginPath(); ctx.moveTo(bar.x-cap*1.5,yA); ctx.lineTo(bar.x+cap*1.5,yA); ctx.stroke();
    }
    if(r.pre_est!=null){                              // ○ 财报前一致预期
      var yP=ys.getPixelForValue(r.pre_est);
      ctx.strokeStyle=p.s[7]; ctx.lineWidth=1.7;
      ctx.beginPath(); ctx.arc(bar.x,yP,4.2,0,Math.PI*2); ctx.stroke();
    }
    if(r.model!=null){                                // ◆ 第三章模型值
      var yM=ys.getPixelForValue(r.model);
      ctx.fillStyle=p.accent||p.s[0]; ctx.beginPath();
      ctx.moveTo(bar.x,yM-5.5); ctx.lineTo(bar.x+5.5,yM); ctx.lineTo(bar.x,yM+5.5); ctx.lineTo(bar.x-5.5,yM);
      ctx.closePath(); ctx.fill();
    }
    if(r.synthetic) ctx.restore();
    ctx.font='9.5px system-ui'; ctx.textAlign='center';
    ctx.fillStyle=r.synthetic?p.muted:((r.coverage==='ok')?p.muted:p.bad);
    var top=Math.min.apply(null,[r.hi,r.actual,r.avg].filter(function(v){return v!=null;})
      .map(function(v){return ys.getPixelForValue(v);}).concat([bar.y]));
    ctx.fillText(r.synthetic?'合成区间':((r.n==null)?'':((r.coverage==='ok'?'n=':'⚠ n=')+r.n)), bar.x, top-13);
  });
  ctx.restore();
}};

function consModelByYear(){
  var out={}, pl=window.__CONS_PL__; if(!pl||!pl.byYear) return out;
  pl.byYear.forEach(function(r){
    if(!r.isForecast) return;
    var y=String(r.year).match(/\d{4}/); if(!y) return;
    out['FY'+y[0]]={ rev:r.rev, np:r.netProfit, eps:r.eps };
  });
  return out;
}

function renderConsensus(){
  var c=(D.part1&&D.part1.consensus); var p=PAL();
  if(!el('chart-consensus')) return;
  if(!c||!consAll().length){ var w=el('cons-wrap'); if(w) w.style.display='none'; return; }
  ['btn-cons-q','btn-cons-y'].forEach(function(id,k){ var b=el(id); if(b) b.classList.toggle('on',(k===0)===(consPeriod==='quarter')); });
  ['rev','np','eps'].forEach(function(m){ var b=el('btn-cons-'+m); if(b) b.classList.toggle('on',consMetric===m); });

  var M=CONS_METRIC[consMetric], rows=consRows(), mByY=consModelByYear();
  var labels=[], bars=[], deco=[], fills=[], borders=[];
  rows.forEach(function(r){
    var b=r[M.key]||{};
    labels.push(r.is_future?r.label:[r.label,'已披露']);
    // ★ 柱高 = 实际披露值（已披露）/ 区间均值（未来）
    var v=r.is_future?b.avg:(b.actual!=null?b.actual:null);
    bars.push(v);
    var cov=b.coverage||r.coverage;
    deco.push({ lo:b.lo, hi:b.hi, avg:b.avg, n:b.n, coverage:cov, suspect:r.suspect, is_future:r.is_future,
      synthetic:b.synthetic, hist_disabled:b.hist_disabled, degenerate:b.degenerate,
      pre_est:b.pre_est, actual:b.actual, verdict:b.verdict, in_range:b.in_range, range_pos:b.range_pos,
      surp_pre:b.surp_vs_pre, surp_avg:b.surp_vs_avg,
      px_1w:r.px_1w, px_4w:r.px_4w, divergence:r.divergence,
      model:(consPeriod==='annual'&&mByY[r.label])?mByY[r.label][M.key]:null });
    // 已披露实心（按 beat/miss 着色）；未来空心（描边）
    var col = r.is_future ? (hexA(p.s[0],'1f')||p.s[0])
            : (b.verdict==='beat'?(hexA(p.good,'99')||p.good)
              :b.verdict==='miss'?(hexA(p.bad,'99')||p.bad)
              :(hexA(p.s[0],'80')||p.s[0]));
    fills.push(b.synthetic?(hexA(p.muted,'26')||p.muted):col);
    borders.push(r.is_future?p.s[0]:(hexA(p.fg,'55')||p.fg));
  });

  var f=function(v){ return v==null?'—':(M.unit?yi(v)+M.unit:(Math.round(v*100)/100)); };
  mkChart('chart-consensus',{ type:'bar',
    data:{ labels:labels, datasets:[{ label:M.name, data:bars,
      backgroundColor:fills, borderColor:borders, borderWidth:1.2,
      barPercentage:0.62, categoryPercentage:0.84 }] },
    options:{ maintainAspectRatio:false, layout:{padding:{top:26}},
      scales:{ x:{grid:{display:false},ticks:{color:p.muted,maxRotation:0,autoSkip:false,font:{size:10}}},
        y:{beginAtZero:true,grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return M.unit?(v+M.unit):v;}},
           title:{display:true,text:M.name+(M.unit?'（'+M.unit+'）':''),color:p.muted,font:{size:11}}} },
      plugins:{ legend:{display:false},
        tooltip:Object.assign(TT(),{callbacks:{ label:function(x){
          var r=deco[x.dataIndex]; if(!r) return '';
          var out=[];
          if(r.actual!=null) out.push('柱高 = 实际披露 '+f(r.actual)+
            (r.verdict?'（'+({beat:'超预期',miss:'低于预期',inline:'基本符合'}[r.verdict])+'）':''));
          else if(r.is_future) out.push('柱高 = 券商区间均值 '+f(r.avg)+'（未来期，尚无实际值）');
          out.push('券商区间 '+f(r.lo)+' – '+f(r.hi)+'　▬均值 '+f(r.avg));
          out.push('覆盖 '+(r.n==null?'—':r.n+' 家')+(r.coverage==='ok'?'':'（样本过薄）'));
          if(r.avg&&r.lo!=null&&r.hi!=null) out.push('分歧度 = 全距/均值 = '+pct((r.hi-r.lo)/Math.abs(r.avg)));
          if(r.pre_est!=null) out.push('○ 财报前一致预期 '+f(r.pre_est));
          if(r.surp_pre!=null) out.push('　vs 财报前预期 '+spct(r.surp_pre/100));
          if(r.surp_avg!=null) out.push('　vs 区间均值 '+spct(r.surp_avg/100));
          if(r.in_range!=null) out.push(r.in_range?('　落在区间内'+(r.range_pos!=null?'（位置 '+Math.round(r.range_pos*100)+'%，0=下沿）':'')):'　⚠ 落在区间外');
          if(r.px_1w!=null) out.push('财报后 1 周股价 '+spct(r.px_1w/100)+(r.px_4w!=null?'，4 周 '+spct(r.px_4w/100):''));
          if(r.divergence==='beat_but_down') out.push('⚠ 超预期但股价下跌 → 预期已 price in');
          if(r.divergence==='miss_but_up')   out.push('⚠ 低于预期但股价上涨 → 利空出尽');
          if(r.model!=null) out.push('◆ 本报告模型 '+f(r.model)+(r.avg?'（'+spct(r.model/r.avg-1)+' vs 均值）':''));
          if(r.hist_disabled) out.push('※ '+r.hist_disabled);
          if(r.synthetic) out.push('⚠ 该期区间为 FMP 合成（固定比例回填，非真实分歧）→ 已排除出统计');
          if(r.degenerate) out.push('※ 区间宽度不足均值 1%，视为退化区间，不计区间位置');
          if(r.suspect) out.push('⚠ '+r.suspect);
          return out; } }}),
        rangeDeco:{rows:deco} } },
    plugins:[rangeDeco] });

  var nP=rows.filter(function(r){return !r.is_future;}).length;
  /* ★2026-08-16 读者反馈「这里的箱线图是错的，没有箱体」——图形本来就不是箱线图（FMP 不给分位数，
     见下方口径折叠块），但页面只用文字说「竖线＝区间」，读者按最像的图形去认，认成了缺箱体的箱线图。
     文字解释治不了图形误认，得**把图例画成图形本身**：下面这条样标是真 SVG，长什么样就是图上什么样。 */
  var GL=function(inner,w){ return '<svg class="cons-gl" width="'+(w||22)+'" height="20" viewBox="0 0 '+(w||22)+' 20" aria-hidden="true">'+inner+'</svg>'; };
  var legend='<div class="cons-legend">'
    + '<span>'+GL('<rect x="6" y="4" width="10" height="14" fill="'+(hexA(p.good,'99')||p.good)+'"/>')+'实际披露·超预期</span>'
    + '<span>'+GL('<rect x="6" y="4" width="10" height="14" fill="'+(hexA(p.bad,'99')||p.bad)+'"/>')+'实际披露·低于预期</span>'
    + '<span>'+GL('<rect x="6" y="4" width="10" height="14" fill="none" stroke="'+p.s[0]+'" stroke-width="1.2"/>')+'未来期·区间均值（空心）</span>'
    + '<span>'+GL('<g stroke="'+p.fg+'" stroke-width="1.3" fill="none"><path d="M11 3v14M6 3h10M6 17h10"/></g>')
      +'<b>全距</b>：券商最低–最高（工字，<b>无箱体</b>）</span>'
    + '<span>'+GL('<path d="M4 10h14" stroke="'+p.fg+'" stroke-width="2.6"/>')+'区间均值</span>'
    + '<span>'+GL('<circle cx="11" cy="10" r="4.2" fill="none" stroke="'+p.s[7]+'" stroke-width="1.7"/>')+'财报前一致预期</span>'
    + (consPeriod==='annual'?('<span>'+GL('<path d="M11 5l5 5-5 5-5-5z" fill="'+(p.accent||p.s[0])+'"/>')+'本报告模型值（随滑块动）</span>'):'')
    + '</div>';
  el('cons-sub').innerHTML= legend
    + '<b>这不是箱线图，也不该有箱体</b>——箱体要 Q1/中位数/Q3，卖方一致预期只给「最低/均值/最高＋覆盖家数」，'
    + '三个分位数一个都拿不到，所以画的是<b>全距误差线</b>（工字上下沿＝最低/最高）。'
    + '虚线右侧为未来预期。'+cite(c.cite);
  var cal=el('cons-caliber');
  if(cal) cal.innerHTML=foldBox('口径与方法',
    '<b>这不是箱线图。</b>FMP 只返回 Low/Avg/High + 覆盖家数，不提供任何分位数（Q1/中位数/Q3），也无逐家机构明细，'+
    '画不出箱体；剔除合成区间后样本本身也薄（季度覆盖常在 2–8 家，n&lt;5 算四分位无统计意义）。'+
    '所以图上画的是全距误差线。要真箱线图须补逐家机构预测（港股 etnet、A股 AlphaPai/iFind）。<br>'+
    esc(c.box_caliber||'')+
    '<br>合成区间：FMP 对早年缺失分歧会回填固定比例的假区间（lo/hi 为均值的固定倍数、与覆盖家数脱钩），已探测剔除、柱画灰。'+
    '<br>EPS 历史兑现已下线：FMP 预期与实际 EPS 分母不同源，相减会出现「净利 miss 但 EPS beat」的矛盾。'+
    '<br>数据源 '+esc(c.src||'FMP')+'　取数 '+esc(c.asof||'')+(c.reported_currency?'　报告币种 '+esc(c.reported_currency):''))+
    (c.currency_warn?'<div class="datagap" style="margin-top:4px">⚠️ '+esc(c.currency_warn)+'</div>':'');
  renderConsStats();
}

function renderConsStats(){
  var host=el('cons-stats'); if(!host) return;
  var s=consStats(), p=PAL();
  var epsOff=(consMetric==='eps')&&consAll().some(function(r){return r.eps&&r.eps.hist_disabled;});
  if(epsOff){
    host.innerHTML='<div class="datagap">⚠️ <b>EPS 的历史兑现比较已下线</b>——FMP 的预期 EPS 与实际 EPS '+
      '<b>分母不同源</b>（预期用固定/漂移的隐含股本，实际用当年报告加权股本），两者相减会得出'+
      '「净利润 miss 但 EPS beat」这种自相矛盾的结论（实测 002371 FY2016 净利 −12.7% 而 EPS +48.5%）。'+
      '<br>看兑现记录请切到 <b>收入</b> 或 <b>净利润</b>。未来期 EPS 预测区间仍然有效（分母是当前股本，与市值同口径），可用于 forward PE。</div>';
    return;
  }
  if(!s){ host.innerHTML='<span class="muted small">该口径无可用兑现样本（券商预期缺失或全为合成区间），本块不出。</span>'; return; }
  var chip=function(lbl,val,color){ return '<span class="kpi-chip" style="display:inline-block;margin:0 10px 4px 0">'+
      '<b style="color:'+(color||p.fg)+'">'+val+'</b> <span class="muted">'+lbl+'</span></span>'; };
  var div=consAll().filter(function(r){return r.divergence;});
  var basisName=(s.surp_basis==='pre')?'财报前一致预期':'区间均值';
  var html=
    chip('有效样本',s.n+' 期')+
    chip('方向命中率',s.beat_rate+'%',s.beat_rate>=60?p.good:s.beat_rate<40?p.bad:p.fg)+
    chip('beat/miss/符合',s.beat+' / '+s.miss+' / '+s.inline)+
    (s.in_range_rate!=null?chip('区间命中率',s.in_range_rate+'%',s.in_range_rate>=70?p.good:s.in_range_rate<50?p.bad:p.fg):'')+
    (s.streak?chip('连续'+(s.streak_dir==='beat'?'超预期':'低于预期'),s.streak+' 期',s.streak_dir==='beat'?p.good:p.bad):'');
  var extra='';
  if(s.synthetic_excluded) extra+='已剔除 '+s.synthetic_excluded+' 期 FMP 合成区间（回填的假分歧，不进统计）。';
  if(s.degenerate_excluded) extra+='另剔除 '+s.degenerate_excluded+' 期退化区间。';
  if(div.length) html+='<div class="small" style="margin-top:4px;color:'+p.bad+'"><b>'+div.length+
    ' 次预期与股价背离</b>——beat 不涨 / miss 不跌，当期股价交易的不是这份财报，读第二章对应阶段的主要矛盾。</div>';
  html+=foldBox('判定口径',
    '判定基准 = '+basisName+'；|偏离| ≤ '+(s.inline_band_pct==null?2:s.inline_band_pct)+'% 记为「基本符合」。'+
    '偏离幅度按基准分列（两个基准不可混算）：'+
    (s.vs_pre&&s.vs_pre.n?'vs 财报前预期 n='+s.vs_pre.n+'，均值 '+spct(s.vs_pre.avg/100)+'、中位 '+spct(s.vs_pre.median/100)+'；':'')+
    (s.vs_avg&&s.vs_avg.n?'vs 区间均值 n='+s.vs_avg.n+'，均值 '+spct(s.vs_avg.avg/100)+'、中位 '+spct(s.vs_avg.median/100)+'。':'')+
    (s.avg_range_pos!=null?'区间内样本平均位置 '+Math.round(s.avg_range_pos*100)+'%（n='+s.n_pos_inrange+
      '，50%=正中，&lt;50%=券商偏乐观）'+((s.n_above_hi||s.n_below_lo)?'；越上沿 '+s.n_above_hi+' 期 / 越下沿 '+s.n_below_lo+' 期。':'。'):'')+
    extra);
  host.innerHTML=html;
}

/* ===========================================================================
 * PART 1.6 筹码龄结构   口径=同花顺「筹码龄分析」复刻（档位 2/10/100 · 系数 1.0）
 * ---------------------------------------------------------------------------
 * 对齐用户《沪深300+中证500 全生命周期筹码结构》标准：
 *   · 三条均龄各占一根右轴、各自缩放 —— **均龄轴走对数**
 *     （中短 10–70 日与长线 100–520 日差一个数量级，线性轴会把中短压成直线）
 *   · 配色纪律：**红绿为 K 线独占**；均龄族=暖色（真实橙／长钱深棕／中短金黄，靠明度分层）；
 *     占比族=冷色（长钱蓝／中短紫）；分位线走灰虚线
 *   · 一条总均龄分不开「结构」与「总量」两种成因，所以必须拆长钱/中短分档均龄
 *   · 长线档只有一个入口（中线熬过 100 日线）和一个出口（被换手卖掉），**没有主动买入路径**
 *     → 长线占比上升永远是被动的；真长钱进场是两段式：先中短占比抬升，100 日后才轮到长线
 * ======================================================================== */
var chipMode='overview';
// 对数轴刻度：只标"好看"的尾数（1/1.5/2/2.5/3/4/5/6/7/8/9 × 10^k），
// 否则 Chart.js 的对数次刻度要么全标要么只剩一个（实测长钱均龄 150–250 只标出 200）
var LOG_MANT=[1,1.5,2,2.5,3,4,5,6,7,8,9];
function logTick(v){
  if(!(v>0)) return '';
  var e=Math.floor(Math.log10(v)), m=v/Math.pow(10,e);
  return LOG_MANT.some(function(x){return Math.abs(m-x)<0.03;}) ? (Math.round(v*10)/10)+'日' : '';
}
var CHIP_C = { true_age:'#E07B39', long_age:'#8B5A2B', mid_age:'#D4A017',      // 均龄族=暖色
               long_pct:'#2E6FAD', mid_pct:'#7A5AF5',                          // 占比族=冷色
               ultra:'#9AA7B4', short:'#6E8CA8' };

function renderChipAge(){
  var ca=(D.part1&&D.part1.chip_age); var p=PAL();
  if(!el('chart-chipage')) return;
  if(!ca||!ca.series||!ca.series.length){ var w=el('chip-wrap'); if(w) w.style.display='none';
    // 整节隐藏时同步摘掉目录里的死链（韩股/美股无逐日换手与自由流通披露时会走到这里）
    try{ var tl=document.querySelector('a[href="#sec-chip"]'); if(tl){ var li=tl.closest('li')||tl; li.style.display='none'; } }catch(e){}
    return; }
  [['btn-chip-ov','overview'],['btn-chip-age','age'],['btn-chip-pct','pct'],['btn-chip-attr','attr']]
    .forEach(function(x){ var b=el(x[0]); if(b) b.classList.toggle('on',chipMode===x[1]); });

  var S=ca.series, lab=S.map(function(x){return x.d;}), cur=ca.current||{};
  var px={type:'line',label:'收盘价(前复权)',data:S.map(function(x){return x.close;}),
    borderColor:p.fg,borderWidth:1.5,pointRadius:0,tension:0,fill:false,yAxisID:'yP',order:9};
  var line=function(name,key,color,axis,dash){ return {type:'line',label:name,data:S.map(function(x){return x[key];}),
    borderColor:color,borderWidth:1.8,pointRadius:0,tension:0,fill:false,yAxisID:axis,spanGaps:true,
    borderDash:dash||[]}; };
  // 收盘价走**对数轴**：本节要比的是「筹码结构变化」与「价格变化」的形状是否同步，
  // 而窗口内价格常有数倍级差（线性轴会把低位段压成一条平线、把高位段的小波动放大成主导视觉）。
  var axP={type:'logarithmic',position:'left',grid:{color:p.grid},ticks:{color:p.fg,callback:logTick},
    title:{display:true,text:'收盘价(对数)',color:p.fg,font:{size:11}}};
  var cfg, sub;

  if(chipMode==='age'){
    // 三条均龄各一根轴、各自缩放；**对数轴**
    var logAx=function(id,name,color,pos,off){ return {type:'logarithmic',position:pos,offset:off,
      grid:{drawOnChartArea:false},ticks:{color:color,callback:logTick},
      title:{display:true,text:name,color:color,font:{size:10}}}; };
    cfg={ data:{labels:lab,datasets:[
        line('真实均龄','true_age',CHIP_C.true_age,'y1'),
        line('长钱均龄(龄≥100日)','long_age',CHIP_C.long_age,'y2'),
        line('中短均龄(龄2–99日)','mid_age',CHIP_C.mid_age,'y3'), px]},
      options:{maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
        scales:{ x:{grid:{display:false},ticks:{color:p.muted,maxTicksLimit:10,font:{size:10}}}, yP:axP,
          y1:logAx('y1','真实均龄',CHIP_C.true_age,'right',false),
          y2:logAx('y2','长钱均龄',CHIP_C.long_age,'right',true),
          y3:logAx('y3','中短均龄',CHIP_C.mid_age,'right',true) },
        plugins:{legend:legLine(),tooltip:Object.assign(TT(),{displayColors:true})}} };
    sub='三条均龄<b>各占一根右轴、各自缩放</b>（量级差一个数量级，共轴必压平其中一条）——<b>比形状与方向，不比高低</b>；轴的颜色对应线的颜色。均龄轴为<b>对数轴</b>。';
  } else if(chipMode==='pct'){
    var area=function(name,key,color){ return {type:'line',label:name,data:S.map(function(x){return x[key];}),
      borderColor:color,backgroundColor:hexA(color,'59')||color,fill:'stack',tension:0,pointRadius:0,borderWidth:1,yAxisID:'y'}; };
    cfg={ data:{labels:lab,datasets:[
        area('超短 <2日','ultra_pct',CHIP_C.ultra), area('短 2–10日','short_pct',CHIP_C.short),
        area('中 10–100日','mid_only_pct',CHIP_C.mid_pct), area('长 >100日','long_pct',CHIP_C.long_pct), px]},
      options:{maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
        scales:{x:{grid:{display:false},ticks:{color:p.muted,maxTicksLimit:10,font:{size:10}}},yP:axP,
          y:{stacked:true,min:0,max:100,position:'right',grid:{drawOnChartArea:false},
             ticks:{color:p.muted,callback:function(v){return v+'%';}},
             title:{display:true,text:'四档占比 (%)',color:p.muted,font:{size:11}}}},
        plugins:{legend:legLine(),tooltip:Object.assign(TT(),{displayColors:true})}} };
    sub='四档占比堆积（合计 100%）。档位=同花顺口径 超短&lt;2 / 短 2–10 / 中 10–100 / 长 &gt;100 交易日。';
  } else if(chipMode==='attr'){
    cfg={ data:{labels:lab,datasets:[
        {type:'line',label:'老化流入 a₁₀₀（中线熬过100日线）',data:S.map(function(x){return x.inflow_ma!=null?x.inflow_ma:x.inflow;}),
         borderColor:CHIP_C.long_pct,backgroundColor:hexA(CHIP_C.long_pct,'40')||CHIP_C.long_pct,
         fill:'origin',pointRadius:0,borderWidth:1.2,tension:0,yAxisID:'y'},
        {type:'line',label:'换手流出 h·L（长线筹码被卖掉）',data:S.map(function(x){return -(x.outflow_ma!=null?x.outflow_ma:x.outflow);}),
         borderColor:CHIP_C.mid_pct,backgroundColor:hexA(CHIP_C.mid_pct,'40')||CHIP_C.mid_pct,
         fill:'origin',pointRadius:0,borderWidth:1.2,tension:0,yAxisID:'y'},
        {type:'line',label:'净变化 ΔL',data:S.map(function(x){var a=x.inflow_ma!=null?x.inflow_ma:x.inflow,b=x.outflow_ma!=null?x.outflow_ma:x.outflow;return a-b;}),
         borderColor:p.fg,borderWidth:1.8,pointRadius:0,tension:0,fill:false,yAxisID:'y'}, px]},
      options:{maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
        scales:{x:{grid:{display:false},ticks:{color:p.muted,maxTicksLimit:10,font:{size:10}}},yP:axP,
          y:{position:'right',grid:{drawOnChartArea:false},ticks:{color:p.muted,callback:function(v){return v+'pp';}},
             title:{display:true,text:'长线占比日流量 (pp/日)',color:p.muted,font:{size:11}}}},
        plugins:{legend:legLine(),tooltip:Object.assign(TT(),{displayColors:true})}} };
    sub='<b>长线占比归因：这波沉淀是「老化推的」还是「没人卖」？</b>　恒等式② ΔL = 老化流入 a₁₀₀ − 换手流出 h·L。'+
        '蓝色恒为正（中线筹码熬过 100 日线，时钟推的）、紫色恒为负（长线筹码被换手卖掉），黑线是两者赛跑的净结果。'+
        '<b>已做 20 交易日滚动平滑</b>（日流量噪声会淹掉赛跑信号；原始值见 tooltip）。'+
        '<b>模型里长线档没有「买入」入口</b>——长线占比上升永远是被动的。';
  } else {
    cfg={ data:{labels:lab,datasets:[
        {type:'line',label:'长钱占比(龄≥100日)',data:S.map(function(x){return x.long_pct;}),
         borderColor:CHIP_C.long_pct,backgroundColor:hexA(CHIP_C.long_pct,'33')||CHIP_C.long_pct,
         fill:'origin',pointRadius:0,borderWidth:1.6,tension:0,yAxisID:'y'},
        line('中短占比(龄2–99日)','mid_pct',CHIP_C.mid_pct,'y'),
        line('真实均龄(右2)','true_age',CHIP_C.true_age,'y1'),
        {type:'line',label:'p720 分位',data:S.map(function(x){return x.p720;}),
         borderColor:p.muted,borderDash:[4,3],borderWidth:1.1,pointRadius:0,tension:0,fill:false,yAxisID:'y',spanGaps:true},
        px]},
      options:{maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
        scales:{x:{grid:{display:false},ticks:{color:p.muted,maxTicksLimit:10,font:{size:10}}},yP:axP,
          y:{position:'right',min:0,max:100,grid:{drawOnChartArea:false},
             ticks:{color:CHIP_C.long_pct,callback:function(v){return v+'%';}},
             title:{display:true,text:'占比 / 分位 (%)',color:CHIP_C.long_pct,font:{size:11}}},
          y1:{type:'logarithmic',position:'right',offset:true,grid:{drawOnChartArea:false},
             ticks:{color:CHIP_C.true_age,callback:logTick},
             title:{display:true,text:'真实均龄(对数)',color:CHIP_C.true_age,font:{size:10}}}},
        plugins:{legend:legLine(),tooltip:Object.assign(TT(),{displayColors:true,callbacks:{
          afterBody:function(items){ var x=S[items[0].dataIndex]; if(!x) return '';
            return ['同花顺口径均龄 '+x.ths_age+' 日',
                    '长钱均龄 '+(x.long_age==null?'—':x.long_age+' 日')+'　中短均龄 '+(x.mid_age==null?'—':x.mid_age+' 日'),
                    '当日换手 '+x.h+'%']; }}})}} };
    sub='<b>结构总览</b>：长钱/中短占比（冷色，左轴%）＋真实均龄（暖色，对数右轴）＋p720 分位（灰虚线）。'+
        '<b>p720 低 = 当前筹码龄处于三年低位（换手最猛段）</b>。';
  }
  mkChart('chart-chipage',cfg,[]);
  el('chip-sub').innerHTML=sub+cite(ca.cite);

  var chip=function(lbl,val,color){ return '<span class="kpi-chip" style="display:inline-block;margin:0 10px 4px 0">'+
      '<b style="color:'+(color||p.fg)+'">'+val+'</b> <span class="muted">'+lbl+'</span></span>'; };
  var co=ca.corr||{};
  el('chip-stats').innerHTML=
    chip('真实均龄',cur.true_age+' 日',CHIP_C.true_age)+
    chip('同花顺口径均龄',cur.ths_age+' 日')+
    chip('p720 分位',(cur.p720==null?'—':cur.p720+'%'),cur.p720!=null&&cur.p720<10?p.bad:p.fg)+
    chip('长钱占比',cur.long_pct+'%',CHIP_C.long_pct)+
    chip('长钱均龄',(cur.long_age==null?'—':cur.long_age+' 日'),CHIP_C.long_age)+
    chip('中短占比',cur.mid_pct+'%',CHIP_C.mid_pct)+
    chip('中短均龄',(cur.mid_age==null?'—':cur.mid_age+' 日'),CHIP_C.mid_age)+
    chip('分型',esc(ca.regime||'—'))+
    '<div class="small" style="margin-top:6px">'+
    '四档占比：超短 '+cur.ultra_pct+'% / 短 '+cur.short_pct+'% / 中 '+cur.mid_only_pct+'% / 长 '+cur.long_pct+'%　'+
    '长线日流量：老化流入 '+cur.inflow+' pp vs 换手流出 '+cur.outflow+' pp → 净 '+
      ((cur.inflow-cur.outflow)>=0?'+':'')+(Math.round((cur.inflow-cur.outflow)*1000)/1000)+' pp<br>'+
    '相关性（区间涨幅 '+spct((ca.period_chg_pct||0)/100)+'）：ρ(价,真实龄)='+(co.price_true_age==null?'—':co.price_true_age)+
    '　ρ(价,长钱龄)='+(co.price_long_age==null?'—':co.price_long_age)+
    '　ρ(价,中短龄)='+(co.price_mid_age==null?'—':co.price_mid_age)+
    '　ρ(价,长钱%)='+(co.price_long_pct==null?'—':co.price_long_pct)+'</div>';
  var cal=el('chip-caliber');
  if(cal) cal.innerHTML=foldBox('口径与方法',
    '<b>口径</b>（'+esc(ca.std||'')+'）：'+esc(ca.caliber||'')+
    '<br><b>模型</b>：'+esc(ca.model||'')+
    '<br><b>已知边界</b>：'+esc(ca.limits||'')+
    '<br>数据源 '+esc(ca.src||'')+'　窗口 '+esc((ca.window||[])[0]||'')+' ~ '+esc((ca.window||[])[1]||'')+
    '（'+(ca.n_days||0)+' 个交易日，日度计算、周线展示）　'+esc((ca.ifind_check||{}).note||''))+
    ((ca.gaps&&ca.gaps.length)?'<div class="datagap" style="margin-top:4px">⚠️ '+ca.gaps.map(esc).join('；')+'</div>':'');
}

/* ===========================================================================
 * PART 2 price review — weekly line + catalyst scatter + phase bands
 * ======================================================================== */
function snapIdx(dates,d){ // nearest week index with weekday <= d
  var t=new Date(d).getTime(), best=-1;
  for(var i=0;i<dates.length;i++){ if(new Date(dates[i]).getTime()<=t) best=i; else break; }
  return best<0?0:best;
}
function movAvg(a,n){ var o=[],s=0; for(var i=0;i<a.length;i++){ s+=a[i]; if(i>=n)s-=a[i-n]; o.push(i>=n-1?Math.round(s/n*100)/100:null);} return o; }
var CANDLE_UP='#e34948', CANDLE_DOWN='#1a9e75', MA_COL={5:'#eda100',10:'#7a5af5',20:'#2a78d6',60:'#8b93a1'};
// 披露日节点配色（2.1 图底 chip）：预告单列，四张定期报告同色系深浅区分
var EARN_COL={'业绩预告':'#c28a2b','业绩快报':'#c28a2b','一季报':'#6a93b8','中报':'#47709e','三季报':'#6a93b8','年报':'#2f5578'};

/* ===== 1.7 叙事/题材 可交易容量与波动位置（part1.narrative_capacity）=====
   叙事＝韭研公社人工梳理的产业链（点名给成分，20~30 只）；
   题材＝问财所属概念里关联度最高的几个（机器打标，几十到上千只）。
   容量按「自由流通市值」读——那才是真正能换手的部分；成交额是今天实际吃得下多少钱。
   两组数量级差 1~2 个数量级，所以 x 轴走对数，否则叙事篮子会被题材压成零。 */
var NCAP_C = {叙事:'--s1', 题材:'--s3'};
function ncapColor(kind,dim){ var c=cv(NCAP_C[kind]||'--s5'); return dim?(c+'88'):c; }

function renderNarrativeCapacity(){
  var nc=(D.part1&&D.part1.narrative_capacity); var p=PAL();
  var wrap=el('ncap-wrap'); if(!wrap) return;
  var bs=(nc&&nc.baskets)||[];
  if(!bs.length){ wrap.style.display='none';
    try{ var tl=document.querySelector('a[href="#sec-ncap"]'); if(tl){ (tl.closest('li')||tl).style.display='none'; } }catch(e){}
    return; }
  wrap.style.display='';
  if(el('ncap-note')) el('ncap-note').innerHTML=esc(nc.note||'');
  if(el('ncap-caliber')) el('ncap-caliber').innerHTML='口径：'+esc(nc.caliber||'')+(nc.src?('　数据源：'+esc(nc.src)):'');

  var band=function(x){ return x==null?'':(x<10?'极低':x<30?'偏低':x<70?'中枢':x<90?'偏高':'极高'); };

  /* 一条线一块，四行读完：抬头 / 三个量 / 这条线上有谁 / 上一次钱为什么来。
     不画柱状图——横向条只表达了「谁大谁小」，而决策要的是「谁在里面、我排第几」。 */
  el('ncap-cards').innerHTML = bs.map(function(b){
    var c=ncapColor(b.kind), t=b.turnover||{}, se=b.self||{};
    /* ★2026-08-14：原来 rank<=3 就标「龙头」。那是**规模**排名，不是行情属性——
       阳光在 8 条 AI 电力篮子里市值全排第 1，页面全标龙头，而按窗口超额它每条都是中军
       （英伟达电源方案那条：龙头 +88%~+104%，阳光 −18%）。市值只回答「买不买得到我」。
       龙头/中军/后排改由下表按 超额+β 判定。 */
    var myTier=((b.peers||[]).filter(function(x){return x.is_self;})[0]||{}).tier;
    var reach = (se.rank==null)?''
      : ('市值第 '+se.rank+'/'+se.of+' 占 '+se.share_pct+'%'
         + (myTier ? ('　本股 <b style="color:'+(myTier==='龙头'?p.good:(myTier==='后排'?p.bad:p.fg))+'">'+esc(myTier)+'</b>') : '')
         + ((se.share_pct!=null&&se.share_pct<1) ? ' <b style="color:'+p.bad+'">钱来了轮不到</b>' : ''));
    var meas = '<span class="ncap-m">容量 <b>'+yi(b.float_yi)+'亿</b><span class="ncap-cal">自由流通市值加总</span>'
      + (t.now!=null ? ('　换手 <b>'+t.now+'%</b>（第 '+t.pct+' 分位 '+band(t.pct)+'）') : '　换手 数据不可得')
      + (reach ? ('　'+reach) : '') + '</span>';

    /* ★2026-08-14 分层 + K 线方位（tiering.py；方位口径照抄 kline-reviewer skill）。
       分层判据随标签走 title，不给裸标签；方位是「这只票现在在什么位置」，
       和「谁在定义这条线的涨幅」一起读才有下单含义。 */
    var TC={'龙头':p.good,'相对最强':p.good,'中军':p.fg,'后排':p.muted};
    var POS=function(s){ if(!s) return p.muted;
      return /主升|反转|右侧启动|转强/.test(s)?p.good : (/主跌|回调升级|向下试探|超跌/.test(s)?p.bad : p.fg); };
    var headless=(b.peers||[]).some(function(x){return x.tier==='相对最强';});
    /* ★2026-08-16 读者反馈「这里的市值拉取有错误」——数字没错，是**列没有表头**：
       那一列是问财的「自由流通市值」，比亚迪 2,184 亿；读者按裸数字当「市值」读，
       而比亚迪总市值 7,642 亿，看上去就是拉错了 3.5 倍。凡是有多口径的数字列，
       表头必须写死口径与单位；这里再把总市值并列出来，让两个口径自己互相解释。 */
    var peers='<table class="ncap-t">'
      +'<thead><tr><th>个股</th><th>分层</th><th>K线方位</th>'
      +'<th class="n">自由流通市值<br><span class="u">亿元 · 容量口径</span></th>'
      +'<th class="n">总市值<br><span class="u">亿元</span></th>'
      +'<th>同花顺行业</th><th>入选理由</th></tr></thead><tbody>'+(b.peers||[]).map(function(pr){
      return '<tr'+(pr.is_self?' class="me"':'')+'><td class="nm">'+(pr.is_self?'▶ ':'')+esc(pr.name)+'</td>'
        +'<td class="tier"'+(pr.tier_basis?(' title="'+esc(pr.tier_basis)+'"'):'')+'>'
          +(pr.tier?('<b style="color:'+(TC[pr.tier]||p.fg)+'">'+esc(pr.tier)+'</b>'):'<span class="muted">—</span>')+'</td>'
        +'<td class="pos"'+(pr.posture_why?(' title="'+esc(pr.posture_why)+'"'):'')+'>'
          +(pr.posture?('<span style="color:'+POS(pr.posture)+'">'+esc(pr.posture)+'</span>')
                      :'<span class="muted">方位不可得</span>')+'</td>'
        +'<td class="n">'+yi(pr.float_yi)+'</td>'
        +'<td class="n">'+(pr.mktcap_yi==null?'<span class="muted">—</span>':yi(pr.mktcap_yi))+'</td>'
        +'<td class="ind">'+esc(pr.ind||'')+'</td>'
        +'<td class="why" title="'+esc(pr.why||'')+'">'+esc((pr.why||'—').slice(0,28))
        +((pr.why||'').length>28?'…':'')+'</td></tr>'; }).join('')
      +'</tbody></table>'
      +(headless?('<div class="ncap-hl">本条线<b>没有龙头</b>：超额最高的那只也是负的。'
                 +'叙事在讲，但钱还没进来（或者进来又走了）。</div>'):'');

    /* 题材的关联度并进抬头，不再单占一行；叙事保留一条最近催化 */
    var relTag = (b.kind==='题材'&&b.rel!=null)
      ? ('<span class="muted" style="font-size:11.5px">关联度 '+b.rel
         +(b.rel_hit?('·命中「'+esc(b.rel_hit)+'」'):'')+'</span>') : '';
    /* 离散度：这条线上选股重不重要。
       R² 高＝齐涨齐跌可吃贝塔；R² 低＝叙事只是标签，选错票叙事对了也不赚钱。
       我的 β 与「份额」互补：份额＝钱会不会买到我，β＝买到了我涨多少。 */
    var dp=b.disp, dsp='';
    if(dp){
      var tight = dp.r2_mean==null?'' : (dp.r2_mean>=0.45?'齐涨齐跌·吃贝塔'
        : (dp.r2_mean>=0.25?'半跟随·选股有用':'各走各的·只是标签'));
      var bs = dp.beta_self;
      var bcol = (bs==null)?p.muted : (bs<0.3?p.bad : (bs>1.3?p.good:p.fg));
      dsp='<div class="ncap-d">'
        +'离散 <b>'+dp.csd_daily+'%/日</b>'
        +'　R² <b>'+(dp.r2_mean==null?'—':dp.r2_mean)+'</b>'+(tight?(' <span class="muted">'+tight+'</span>'):'')
        +'　我的β <b style="color:'+bcol+'">'+(bs==null?'—':bs)+'</b>'
        +'<span class="muted"> (成分 '+(dp.beta_p25==null?'—':dp.beta_p25+'~'+dp.beta_p75)+')</span>'
        +'　<span class="muted">自 '+esc(dp.window[0])+' 累计超额中位 '+(dp.cum_med>=0?'+':'')+dp.cum_med+'%'
        +'；最强 '+esc(dp.best.name)+' '+(dp.best.r>=0?'+':'')+Math.round(dp.best.r)+'%'
        +'　最弱 '+esc(dp.worst.name)+' '+Math.round(dp.worst.r)+'%</span>'
        +'</div>';
    }

    var e0=(b.catalysts||[])[0];
    var cat = e0 ? ('<div class="ncap-cat"><b>'+esc(e0.date)+'</b> '
       +esc(e0.text.slice(0,84))+(e0.text.length>84?'…':'')+'</div>') : '';

    return '<div class="ncap-c" style="border-left-color:'+c+'">'
      + '<div class="ncap-h"><span class="ncap-kind" style="color:'+c+';border-color:'+c+'">'+esc(b.kind)+'</span>'
      + '<b>'+esc(b.name)+'</b>'+(b.sub?('<span class="muted" style="font-size:11.5px">'+esc(b.sub)+'</span>'):'')
      + '<span class="muted" style="font-size:11.5px">'+b.n+' 只</span>'+relTag+meas+'</div>'
      + peers + dsp + cat
      + '</div>';
  }).join('');
}

function renderPrice(){ var pr=D.part2||{}; var p=PAL();
  /* ★ 第二章标题可覆写（2026-07-31 长鑫 688825 加）：新上市/次新股没有「近三年股价」，
     写死标题会与内容打架。填 part2.title 即改标题与目录，缺省沿用模板文案。 */
  if(pr.title){ var _h=document.getElementById('sec-p2'); if(_h) _h.textContent=pr.title;
    var _a=document.querySelector('#toc a[href="#sec-p2"]'); if(_a) _a.textContent=pr.title; }
  var cnv=el('chart-price'); if(!cnv) return;   // canvas 可能已被 datagap 替换(主题重建时)
  var raw=pr.weekly||[]; if(!raw.length){ if(cnv.parentNode) cnv.parentNode.innerHTML='<span class="datagap">⚠️ 未查到 周度股价</span>'; return; }
  // OHLC 完整度闸门：真 K 线必须有独立的 o/h/l（fetch_kline.py 取真数据），c-only 假蜡烛必须显式警示
  var realN=raw.filter(function(w){ return isFinite(parseFloat(w.o))&&isFinite(parseFloat(w.h))&&isFinite(parseFloat(w.l))&&parseFloat(w.h)>parseFloat(w.l); }).length;
  var ohlcOK = realN >= raw.length*0.9;
  var wk=raw.map(function(w){ var c=num(w.c); return {d:w.d,o:num(w.o,c),h:num(w.h,c),l:num(w.l,c),c:c}; });
  var dates=wk.map(function(w){return w.d;}), closes=wk.map(function(w){return w.c;});
  var his=wk.map(function(w){return w.h;}), los=wk.map(function(w){return w.l;});
  var pmax=Math.max.apply(null,his), pmin=Math.min.apply(null,los);
  var useLog=(pmax/pmin)>1.8;
  var cats=(pr.catalysts||[]).map(function(c){ var xi=c.snapIdx!=null?c.snapIdx:snapIdx(dates,c.date); return Object.assign({},c,{x:xi,y:(wk[xi]?wk[xi].h:closes[xi])}); });
  /* ★2026-08-12 标记语义改版：形状=R/M/V 主因子（复合码首字母：R●圆 / M▲三角 / V★五角星），
     颜色=五大催化剂原色系（codes[0]；负面/流动性节点 codes:[] 灰），
     编号=该催化剂类型在窗口内第几次出现（#3=「传播面出圈」第 3 次），不再用全局 id。 */
  (function(){ var occ={}; cats.slice().sort(function(a,b){return a.x-b.x||String(a.date).localeCompare(String(b.date));})
    .forEach(function(c){ var g=(c.codes||[])[0]; if(!g){ c._occ=null; return; } occ[g]=(occ[g]||0)+1; c._occ=occ[g]; }); })();
  var MA_LIST=[5,10,20,60];
  var maDs=MA_LIST.map(function(n){ return {type:'line',label:'MA'+n,data:movAvg(closes,n),borderColor:MA_COL[n],borderWidth:1.2,pointRadius:0,pointHitRadius:0,tension:0,order:5,spanGaps:true}; });
  var CAT_DI=maDs.length;   // 催化 scatter 的 dataset 下标——由 MA 数量推得，禁止硬编码
  // scatter 只当命中区（透明），真正的 ●▲★ 由 catlab 插件手绘（Chart.js 无五角星 pointStyle）
  var catDs={ type:'scatter',label:'催化',data:cats.map(function(c){return {x:c.x,y:c.y,_c:c};}),parsing:false,order:1,
    pointRadius:7,pointHoverRadius:9,pointHitRadius:11,pointStyle:'circle',
    backgroundColor:'rgba(0,0,0,0)', borderColor:'rgba(0,0,0,0)',borderWidth:0 };
  var catShapeOf=function(c){ var f=String(c.code||'')[0]; return f==='M'?'tri':(f==='V'?'star':'dot'); };
  var catColorOf=function(c){ var g=(c.codes||[])[0]; return g&&CAT_COLOR[g]?CAT_COLOR[g].fg:'#8c8474'; };
  function drawCatMk(ctx,x,y,shape,col,bg){ var r=6; ctx.save(); ctx.fillStyle=col; ctx.strokeStyle=bg; ctx.lineWidth=1.4;
    ctx.beginPath();
    if(shape==='tri'){ ctx.moveTo(x,y-r-0.5); ctx.lineTo(x-r,y+r*0.72); ctx.lineTo(x+r,y+r*0.72); ctx.closePath(); }
    else if(shape==='star'){ var R=r+1.6,ri=R*0.42,i,a; for(i=0;i<10;i++){ a=-Math.PI/2+i*Math.PI/5; var rr=(i%2===0)?R:ri;
        var px=x+rr*Math.cos(a), py=y+rr*Math.sin(a); if(i)ctx.lineTo(px,py); else ctx.moveTo(px,py); } ctx.closePath(); }
    else { ctx.arc(x,y,r-0.6,0,Math.PI*2); }
    ctx.fill(); ctx.stroke(); ctx.restore(); }
  var phases=pr.phases||[];
  // 蜡烛图（涨红跌绿·A股惯例）
  var candles={ id:'candles', beforeDatasetsDraw:function(ch){ var xs=ch.scales.x,ys=ch.scales.y,ctx=ch.ctx;
    var cw=Math.max(2,(ch.chartArea.width/wk.length)*0.62); ctx.save();
    wk.forEach(function(b,i){ var x=xs.getPixelForValue(i); var up=b.c>=b.o; var col=up?CANDLE_UP:CANDLE_DOWN;
      ctx.strokeStyle=col; ctx.fillStyle=col; ctx.lineWidth=1;
      ctx.beginPath(); ctx.moveTo(x,ys.getPixelForValue(b.h)); ctx.lineTo(x,ys.getPixelForValue(b.l)); ctx.stroke();
      var yo=ys.getPixelForValue(b.o), yc=ys.getPixelForValue(b.c); var top=Math.min(yo,yc), bh=Math.max(Math.abs(yc-yo),1);
      ctx.fillRect(x-cw/2,top,cw,bh); }); ctx.restore(); } };
  var bands={ id:'phbands', beforeDraw:function(ch){ var ctx=ch.ctx,xs=ch.scales.x,a=ch.chartArea;
    ctx.save(); phases.forEach(function(ph,i){ var x0=Math.max(xs.getPixelForValue(ph.startIdx),a.left), x1=Math.min(xs.getPixelForValue(ph.endIdx),a.right);
      if(i%2){ ctx.fillStyle='rgba(120,120,120,0.05)'; ctx.fillRect(x0,a.top,x1-x0,a.bottom-a.top); }
      if(ph.color){ ctx.fillStyle=hexA(ph.color,'10')||'rgba(120,120,120,0.04)'; ctx.fillRect(x0,a.top,x1-x0,a.bottom-a.top); }
      ctx.fillStyle=p.muted; ctx.font='bold 10px '+FONT; ctx.textAlign='center';
      ctx.fillText((ph.name||'')+(ph.chg!=null?(' '+chgTxt(ph.chg)):''),(x0+x1)/2,a.top+11); }); ctx.restore(); } };
  // ★披露日节点层（业绩预告/一季报/中报/三季报/年报）——画在图底，与顶部催化▲互不遮挡。
  // 为什么要全量画：催化清单只收「涨跌显著」的财报，而「利好不涨」本身是信号，必须让没动的那几次也看得见。
  var earns=(pr.earnings||[]).map(function(e){
      var xi=(e.snapIdx!=null)?e.snapIdx:snapIdx(dates,e.date);
      return Object.assign({},e,{x:xi});
    }).filter(function(e){ return e.x>=0 && e.x<dates.length; });
  var earnmk={ id:'earnmk', afterDatasetsDraw:function(ch){ if(!earns.length) return;
    var xs=ch.scales.x,a=ch.chartArea,ctx=ch.ctx; ctx.save();
    var lanes=[];                                  // 同周多条时上下错开，避免chip叠字
    earns.forEach(function(e){ var x=xs.getPixelForValue(e.x); if(!isFinite(x)) return;
      var col=EARN_COL[e.type]||p.muted;
      ctx.setLineDash([3,4]); ctx.strokeStyle=hexA(col,'2e')||col; ctx.lineWidth=1;
      ctx.beginPath(); ctx.moveTo(x,a.top); ctx.lineTo(x,a.bottom); ctx.stroke(); ctx.setLineDash([]);
      var lane=0; while(lanes.some(function(L){ return L.lane===lane && Math.abs(L.x-x)<20; })) lane++;
      lanes.push({x:x,lane:lane});
      var w=(e.short||'?').length>1?19:15, h=13, y=a.bottom-4-lane*15;
      // 归母同比为负 → 空心（一眼看出哪次是 miss）
      var neg=(e.np_yoy!=null && e.np_yoy<0);
      ctx.fillStyle=neg?p.bg:col; ctx.strokeStyle=col; ctx.lineWidth=1.2;
      ctx.beginPath(); ctx.rect(x-w/2,y-h,w,h); if(!neg)ctx.fill(); ctx.stroke();
      ctx.fillStyle=neg?col:'#fff'; ctx.font='bold 9.5px '+FONT; ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(e.short||'?',x,y-h/2+.5);
    }); ctx.textBaseline='alphabetic'; ctx.restore(); } };
  var catlab={ id:'catlab', afterDatasetsDraw:function(ch){ var meta=ch.getDatasetMeta(CAT_DI); if(!meta)return; var ctx=ch.ctx;
    ctx.save();
    meta.data.forEach(function(pt,i){ var c=cats[i]; if(!c)return; var col=catColorOf(c);
      drawCatMk(ctx,pt.x,pt.y,catShapeOf(c),col,p.bg);
      if(c._occ!=null){ ctx.font='bold 10px '+FONT; ctx.textAlign='center'; ctx.fillStyle=col; ctx.fillText('#'+c._occ,pt.x,pt.y-13); } });
    ctx.restore(); } };
  var chart=mkChart('chart-price',{ data:{labels:dates,datasets:maDs.concat([catDs])},
    options:{ maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
      // ★悬停即出浮窗（2026-08-12）：命中催化 scatter → openCatPop(hover)；点击=钉住/解钉（移动端兜底）
      onHover:function(evt){ if(!chart)return; var hit=null;
        try{ var els=chart.getElementsAtEventForMode(evt,'nearest',{intersect:true},false)
              .filter(function(e){return e.datasetIndex===CAT_DI;});
          if(els.length) hit=cats[els[0].index]; }catch(_){}
        if(evt&&evt.native&&evt.native.target) evt.native.target.style.cursor=hit?'pointer':'default';
        if(hit) openCatPop(hit,evt.native,true); else scheduleCatClose(); },
      onClick:function(evt){ var xs=chart&&chart.scales&&chart.scales.x; if(!xs)return; var px=(evt&&evt.x!=null)?evt.x:(evt.native?evt.native.offsetX:0);
        var idx=Math.round(xs.getValueForPixel(px)); var c=cats.filter(function(cc){return Math.abs(cc.x-idx)<=1;}).sort(function(a,b){return Math.abs(a.x-idx)-Math.abs(b.x-idx);})[0];
        if(c){ openCatPop(c, evt.native, false); CATPOP.pin=true; } else closeCatPop(); },
      scales:{ x:{type:'category',grid:{display:false},ticks:{color:p.muted,maxTicksLimit:14,autoSkip:true,maxRotation:0,callback:function(v){var d=dates[v]; return d?d.slice(0,7):'';}}},
        y:{ type:useLog?'logarithmic':'linear', position:'right', min:Math.floor(pmin*0.95), max:Math.ceil(pmax*1.05), grid:{color:p.grid},
            ticks:{color:p.muted,callback:function(v){ if(useLog){ var ok=[10,15,20,30,40,50,60,80,100,150,200,300,400,600]; return ok.indexOf(v)>=0?v+CURU().trim():''; } return v+CURU().trim(); }} } },
      plugins:{ legend:{display:false}, tooltip:Object.assign(TT(),{
        // 催化行不进按周悬停(index 模式下 scatter 会按元素序号错配到别的周)——催化详情走 ▲ 点击弹卡
        filter:function(it){ return !(it.dataset&&it.dataset.type==='scatter'); },
        callbacks:{
        title:function(it){ if(!it.length)return ''; var i=it[0].dataIndex; var b=wk[i]; var c=cats.filter(function(x){return x.x===i;})[0];
          var ev=earns.filter(function(x){return x.x===i;});
          return [(c?('#'+c.id+' '+c.name+' · '):'')+(b?b.d:''), b?('开'+b.o+' 高'+b.h+' 低'+b.l+' 收'+b.c+CURU()):'',
                  ev.length?('披露：'+ev.map(function(x){return x.type+'('+x.date+')';}).join('、')):''].filter(Boolean); },
        label:function(it){ var lbl=(it.dataset&&it.dataset.label)||''; var val=(it.raw!=null?it.raw:'—');
          return lbl+' '+val; } }}) } },
    plugins:[candles,bands,catlab,earnmk] });
  el('price-legend').innerHTML='K线 <i style="background:'+CANDLE_UP+'"></i>涨 <i style="background:'+CANDLE_DOWN+'"></i>跌 &nbsp;·&nbsp; 均线 '+MA_LIST.map(function(n){return '<i style="background:'+MA_COL[n]+'"></i>MA'+n;}).join(' ')+
    (earns.length?('<br>披露节点 '+Object.keys(EARN_COL).filter(function(k,i,ar){return ar.indexOf(k)===i;}).filter(function(k){return earns.some(function(e){return e.type===k;});}).map(function(k){return '<i style="background:'+EARN_COL[k]+'"></i>'+k;}).join(' ')+' <span class="muted">（图底方块，虚线对齐 K 线；仅标披露日）</span>'):'')+
    '<br>催化标记：形状=主因子 <b style="color:'+CODE_COLOR.R+'">● R收入</b> <b style="color:'+CODE_COLOR.M+'">▲ M利润率</b> <b style="color:'+CODE_COLOR.V+'">★ V估值</b>（复合码取首字母）'+
    ' · 颜色=五大催化剂 '+Object.keys(CAT_COLOR).map(function(k){return '<b style="color:'+CAT_COLOR[k].fg+'">'+CAT_LABEL[k]+'</b>';}).join(' · ')+
    ' · <b>#n＝该类型第 n 次出现</b> &nbsp;<b>悬停标记看详情（点击=钉住）</b>';
  el('price-sub').innerHTML=(ohlcOK?'':'<span class="datagap">⚠️ K线 OHLC 不完整（'+(raw.length-realN)+'/'+raw.length+' 根缺真实高开低，蜡烛退化）——必须用 scripts/fetch_kline.py 重拉真实数据后重建。</span><br>')+(pr.window||'')+cite(pr.cite);
  renderFwdPE(dates,closes); renderPhasePanel(); renderCatStats(cats); renderCatIndex(cats);
}
/* 催化浮窗（★2026-08-12 悬停版）：鼠标移到标记上直接弹出（不用点击），
   9 维归因默认展开在下方；原始材料不进浮窗正文，做成超链接（catalysts[].links）。
   点击标记=钉住（钉住后悬停别处不换卡），×/Esc/点图外解除。浮窗自身可进入（点链接不消失）。 */
var CATPOP={pin:false,over:false,cur:null,t:null};
function scheduleCatClose(){ if(CATPOP.pin) return; clearTimeout(CATPOP.t);
  CATPOP.t=setTimeout(function(){ if(!CATPOP.over&&!CATPOP.pin) closeCatPop(); },260); }
function closeCatPop(){ var e=el('catpop'); if(e)e.style.display='none'; CATPOP.pin=false; CATPOP.cur=null; }
function openCatPop(c, native, hover){ var e=el('catpop'); if(!e)return;
  if(hover&&CATPOP.pin) return;                       // 钉住时悬停不抢卡
  clearTimeout(CATPOP.t);
  if(CATPOP.cur===c&&e.style.display==='block'){ if(!hover) CATPOP.pin=true; return; }
  CATPOP.cur=c; if(!hover) CATPOP.pin=true;
  if(!e.__hoverBound){ e.__hoverBound=1;
    e.addEventListener('mouseenter',function(){ CATPOP.over=true; clearTimeout(CATPOP.t); });
    e.addEventListener('mouseleave',function(){ CATPOP.over=false; scheduleCatClose(); }); }
  var badges=(c.codes||[]).map(function(k){var cc=CAT_COLOR[k]||{bg:'#eee',fg:'#333'};return '<span class="badge" style="background:'+cc.bg+';color:'+cc.fg+'">'+esc(CAT_LABEL[k]||k)+'</span>';}).join(' ');
  var dims=Object.keys(DIM_LABELS).map(function(k){ var v=(c.dims||{})[k]; var hit=v&&v.indexOf('✓')>=0; return '<span class="dim '+(hit?'hit':'miss')+'" title="'+esc(DIM_LABELS[k]+'：'+(v||'—'))+'">'+k+(hit?'✓':'—')+'</span>'; }).join(' ');
  var detail=Object.keys(DIM_LABELS).filter(function(k){var v=(c.dims||{})[k];return v&&v.indexOf('✓')>=0;}).map(function(k){return '<b>'+k+' '+DIM_LABELS[k]+'</b>：'+esc((c.dims[k]||'').replace('✓','').trim());}).join('<br>')||'—';
  var links=(c.links||[]).map(function(L){ if(!L||!L.url) return ''; return '<a class="cp-lnk" href="'+esc(L.url)+'" target="_blank" rel="noopener">↗ '+esc(L.label||'原始材料')+'</a>'; }).join('');
  if(!links&&c.rationale) links='<span class="cp-lnk off" title="'+esc(c.rationale)+'">原始材料推演见 2.3 清单（未给链接）</span>';
  e.innerHTML='<span class="cp-close">×</span><div class="cp-hd"><b style="color:'+(catColorOfPop(c))+'">#'+c.id+' '+esc(c.name)+'</b> '+badges+'</div>'+
    '<div class="cp-meta">'+esc(c.date||'')+' · ¥'+(c.price!=null?c.price:'')+' · 周涨跌 <b style="color:'+((c.weekChg||0)>=0?p_good():p_bad())+'">'+spct((c.weekChg||0)/100)+'</b> · 主因子 <b style="color:'+(CODE_COLOR[c.code]||'')+'">'+esc(c.code||'')+'</b>'+(c._occ!=null&&(c.codes||[])[0]?(' · '+esc(CAT_LABEL[(c.codes||[])[0]])+' 第 '+c._occ+' 次'):'')+'</div>'+
    '<div class="cp-driver">'+esc(c.driver||'')+'</div>'+
    (links?('<div class="cp-links">'+links+'</div>'):'')+
    '<div class="cp-dimline">'+dims+'</div>'+
    '<div class="cp-dt-hd">9 维度归因</div><div class="cp-detail">'+detail+'</div>'+
    '<div class="cp-sum">主导 '+esc(c.lead||'')+' — '+esc(c.summary||'')+'</div>';
  e.style.display='block';
  var vw=document.documentElement.clientWidth, vh=document.documentElement.clientHeight;
  var x=((native&&native.pageX)||220)+14, y=((native&&native.pageY)||220)+10;
  x=Math.min(x,(window.scrollX||0)+vw-e.offsetWidth-16);
  if(native&&native.clientY!=null&&native.clientY+e.offsetHeight+24>vh) y=y-e.offsetHeight-26; // 贴下缘时翻到指针上方
  e.style.left=x+'px'; e.style.top=Math.max(window.scrollY||0,y)+'px';
  e.querySelector('.cp-close').onclick=function(ev){ ev.stopPropagation(); closeCatPop(); };
}
function catColorOfPop(c){ var g=(c.codes||[])[0]; return g&&CAT_COLOR[g]?CAT_COLOR[g].fg:(CODE_COLOR[c.code]||''); }
function p_good(){ return PAL().good; } function p_bad(){ return PAL().bad; }
/* ===========================================================================
 * 2.1b Forward PE 带（★2026-08-12 两版口径）：K 线下方共 x 轴子图。
 * 【主口径·时点一致预期】part2.fwd_pe.series 由 scripts/fetch_fwd_pe.py 产出——
 *   逐份带日期的券商研报（东财 reportapi 相对年字段）自底向上重建：每周取窗口内各券商最新报告
 *   → 自然年中位数 → NTM=w×FY1+(1−w)×FY2 混合（财年换挡无跳变）。无前视；空档=真无卖方覆盖。
 * 【fallback·近似口径】series 缺失时退回 FMP 财年快照合成（每财年一份≈财报前最终一致预期，
 *   整年铺平线 → 有前视偏差 + 阶梯粗），图注明确标「近似口径」并提示重跑脚本。
 * ◆ 锚点 = 卖方纪要/研报当时的目标市值÷当年盈利预测（part2.fwd_pe.anchors 手工 RAG 取证，超链接原文）。
 * ======================================================================== */
/* ── 2.1b 复合口径分支（part2.fwd_pe.ciq 存在时走这条）─────────────────────────
 * 数据商（Capital IQ 等）能同时给 Forward PE / Forward PS / 分财年收入一致预期的日频序列时，
 * 单画一条 PE 带是浪费：把「价格」与「市场愿意给的倍数」「市场认的收入体量」摞在同一根 x 轴上，
 * 才看得出某一段到底是数字变了还是尺子变了。
 * 三条纪律：① 价格走对数轴（窗口内常有数倍级差，线性轴会让低位段的形状消失）；
 *          ② 缺失值只在「整段无覆盖」时截断、窗口内散点前向填充，填充数必须写进图注；
 *          ③ 不同量纲分轴，且图注写明两段不可比高低。 */
var fwdMode='all', FWD_ARGS=null;
function renderFwdPE_CIQ(dates,closes,cfg){
  var p=PAL(), blk=el('fwdpe-block'), C=cfg.ciq||{}, rows=C.rows||[];
  var byD={}; rows.forEach(function(x){ if(x&&x.d) byD[x.d]=x; });
  var pick=function(k){ return dates.map(function(d){ var x=byD[d]||{};
    var v=parseFloat(x[k]); return isFinite(v)?v:null; }); };
  var pe1=pick('pe1'), pe2=pick('pe2'), ps1=pick('ps1'), ps2=pick('ps2');
  var r1=pick('rev1'), r2=pick('rev2'), n1=pick('ni1'), n2=pick('ni2');
  var nz=function(a){ return a.filter(function(v){return v!=null;}).length; };
  if(nz(pe1)<8 && nz(ps1)<8){ blk.style.display='none'; return; }

  var ttl=el('fwdpe-title'); if(ttl) ttl.style.display='flex';
  var wrap=el('fwdpe-wrap'); if(wrap) wrap.style.height='460px';   // 拉到与 2.1a(480px) 同量级
  [['btn-fwd-all','all'],['btn-fwd-pe','pe'],['btn-fwd-ps','ps'],['btn-fwd-rev','rev'],['btn-fwd-ni','ni']]
    .forEach(function(x){ var b=el(x[0]); if(b) b.classList.toggle('on',fwdMode===x[1]); });

  /* ★2026-08-16 读者反馈「左右轴的量纲有错误，并且不清楚」——两处硬错：
     ① PE 与 PS **同挂一根右轴**（原来 `scales.y` 标题只写「倍数」）。PE 是「几倍盈利」、
        PS 是「几倍收入」，只是碰巧都念作「倍」，量纲根本不同；赛力斯 PE 15–60x 而 PS 0.7–1.7x，
        同轴一画 PS 被压成贴着 0 的一条直线，读者看到的是「PS 常年不动」这个假读数。
     ② 「全部」一口气开四条腿、右侧摞四根轴，谁读哪根全靠猜。
     治法：PE / PS 各自独占一根轴且轴标题写死量纲；「全部」只保留**价格 + 两把尺子**
     （这张图的本意就是把价格和尺子摞起来看），亿元量级的收入/归母预期改为单独查看。 */
  var showPE=(fwdMode==='all'||fwdMode==='pe'), showPS=(fwdMode==='all'||fwdMode==='ps'),
      showRV=(fwdMode==='rev'), showNI=(fwdMode==='ni');
  var ds=[{type:'line',label:'收盘价（前复权·左轴·对数·元）',data:closes,borderColor:p.fg,borderWidth:1.6,
           pointRadius:0,tension:0,fill:false,yAxisID:'yP',order:9}];
  var mk=function(lbl,data,color,dash,axis){ return {type:'line',label:lbl,data:data,borderColor:color,
    borderWidth:1.8,borderDash:dash||[],pointRadius:0,tension:0,fill:false,spanGaps:false,yAxisID:axis,order:2}; };
  if(showPE){ ds.push(mk('Forward PE · FY+1（右轴①·倍盈利）',pe1,p.accent,null,'y'));
              ds.push(mk('Forward PE · FY+2（右轴①·倍盈利）',pe2,p.accent,[5,4],'y')); }
  if(showPS){ ds.push(mk('Forward PS · FY+1（右轴'+(showPE?'②':'①')+'·倍收入）',ps1,p.s[3],null,'yS'));
              ds.push(mk('Forward PS · FY+2（右轴'+(showPE?'②':'①')+'·倍收入）',ps2,p.s[3],[5,4],'yS')); }
  if(showRV){ ds.push(mk('收入一致预期 · FY+1（右轴·亿元）',r1,p.s[5],null,'y2'));
              ds.push(mk('收入一致预期 · FY+2（右轴·亿元）',r2,p.s[5],[5,4],'y2')); }
  if(showNI){ ds.push(mk('归母一致预期 · FY+1（右轴·亿元）',n1,p.s[1],null,'y3'));
              ds.push(mk('归母一致预期 · FY+2（右轴·亿元）',n2,p.s[1],[5,4],'y3')); }

  var anchors=(cfg.anchors||[]).map(function(a){ var v=parseFloat(a.pe);
      return Object.assign({},a,{x:snapIdx(dates,a.date),peA:v}); })
    .filter(function(a){ return a.x>=0&&a.x<dates.length&&isFinite(a.peA); });
  if(showPE&&anchors.length) ds.push({type:'scatter',label:'◆ 卖方自家算的 PE',parsing:false,
    data:anchors.map(function(a){return {x:a.x,y:a.peA};}),pointStyle:'rectRot',pointRadius:6,pointHoverRadius:9,
    backgroundColor:p.s[6],borderColor:p.bg,borderWidth:1,order:1});

  var scales={ x:{type:'category',grid:{display:false},
        ticks:{color:p.muted,maxTicksLimit:14,autoSkip:true,maxRotation:0,
               callback:function(v){var d=dates[v];return d?d.slice(0,7):'';}}},
    yP:{type:'logarithmic',position:'left',grid:{color:p.grid},ticks:{color:p.fg,callback:logTick},
        title:{display:true,text:'收盘价（元·对数轴）',color:p.fg,font:{size:11}}} };
  if(showPE) scales.y={position:'right',grid:{drawOnChartArea:false},
        ticks:{color:p.accent,callback:function(v){return v+'x';}},
        title:{display:true,text:'Forward PE（倍·盈利）',color:p.accent,font:{size:11}}};
  if(showPS) scales.yS={position:'right',offset:showPE,grid:{drawOnChartArea:false},
        ticks:{color:p.s[3],callback:function(v){return (Math.round(v*100)/100)+'x';}},
        title:{display:true,text:'Forward PS（倍·收入）',color:p.s[3],font:{size:11}}};
  if(showRV) scales.y2={position:'right',offset:true,grid:{drawOnChartArea:false},
        ticks:{color:p.s[5],callback:function(v){return v+'亿';}},
        title:{display:true,text:'收入一致预期（亿元）',color:p.s[5],font:{size:10}}};
  if(showNI) scales.y3={position:'right',offset:true,grid:{drawOnChartArea:false},
        ticks:{color:p.s[1],callback:function(v){return v+'亿';}},
        title:{display:true,text:'归母一致预期（亿元）',color:p.s[1],font:{size:10}}};

  mkChart('chart-fwdpe',{ data:{labels:dates,datasets:ds},
    options:{ maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
      plugins:{ legend:legLine(), tooltip:Object.assign(TT(),{displayColors:true,callbacks:{
        title:function(it){ return it.length?dates[it[0].dataIndex]:''; },
        label:function(it){ if(it.dataset.type==='scatter'){ var a=anchors[it.dataIndex]||{};
            return '◆ '+(a.label||'')+(a.src?(' · '+a.src):''); }
          if(it.raw==null) return it.dataset.label+' —';
          var ax=it.dataset.yAxisID;
          var u=(ax==='y2'||ax==='y3')?' 亿元':(ax==='yP'?' 元':(ax==='yS'?'x 收入':'x 盈利'));
          return it.dataset.label+' '+(Math.round(it.raw*100)/100)+u; } }}) },
      scales:scales } });

  var f=C.filled||{}, tot=(f.pe1||0)+(f.ps1||0);
  var AXN=[]; if(showPE) AXN.push('<b style="color:'+p.accent+'">右轴① Forward PE＝几倍<u>盈利</u></b>');
              if(showPS) AXN.push('<b style="color:'+p.s[3]+'">右轴'+(showPE?'②':'①')+' Forward PS＝几倍<u>收入</u></b>');
              if(showRV) AXN.push('<b style="color:'+p.s[5]+'">右轴 收入一致预期（亿元）</b>');
              if(showNI) AXN.push('<b style="color:'+p.s[1]+'">右轴 归母一致预期（亿元）</b>');
  el('fwdpe-sub').innerHTML='<b>价格与尺子摞在一起看</b>：左轴＝收盘价（元·对数轴，所以斜率可以跨区间直接比）；'
    +AXN.join('；')+'。'
    +'<b>PE 与 PS 分两根轴，因为「倍」字相同但量纲不同（一个除盈利、一个除收入），同轴会把小的那条压成直线。</b>'
    +'<br><b>线不动而价格涨＝盈利预期同步上修（数字变了）；线抬台阶＝市场换了尺子。</b>'
    +cite(cfg.cite);
  blk.style.display='';
  var fold=foldBox('口径与方法（财年怎么钉的 · 缺失值怎么处理 · 哪条腿不可用）',
    esc(cfg.caliber||'')
    +'<br><br><b>缺失值</b>：'+esc(C.na_note||'')+'（本次前向填充 PE '+(f.pe1||0)+' 点、PS '+(f.ps1||0)+' 点，共 '+tot+' 点）。'
    +'<br><br><b>收入腿的口径警告</b>：'+esc(C.rev_caliber_warn||'')
    +'<br><br>数据来源 '+esc(cfg.src||'')+'。PE 与 PS 同在右轴但含义不同，'
    +'收入预期在第二右轴、单位亿元，三者不可直接比高低。');
  var old=el('fwdpe-fold'); if(old&&old.parentNode) old.parentNode.removeChild(old);  // 切模式会重渲，先清旧的
  var host=el('fwdpe-sub');
  if(host) host.insertAdjacentHTML('afterend','<div id="fwdpe-fold">'+fold+'</div>');
}

/* ★2.1b 折叠块展开时重绘（2026-08-17）：<details> 收起时 canvas 宽度为 0，Chart.js 的 ResizeObserver 通常会在展开时补一次 resize，
   这里再挂一次 toggle→resize 兜底（file:// 下 ResizeObserver 偶尔不触发）。 */
function bindFwdFold(){ var blk=el('fwdpe-block'); if(!blk||blk.__foldBound||blk.tagName!=='DETAILS') return; blk.__foldBound=1;
  blk.addEventListener('toggle',function(){ if(!blk.open) return;
    try{ var cv=el('chart-fwdpe'); var ch=cv&&window.Chart&&Chart.getChart?Chart.getChart(cv):null; if(ch) setTimeout(function(){ ch.resize(); ch.update('none'); },30); }catch(_){} }); }
function renderFwdPE(dates,closes){ var blk=el('fwdpe-block'); if(!blk) return; bindFwdFold();
  var p=PAL(); var cfg=(D.part2||{}).fwd_pe||{};
  var bail=function(){ blk.style.display='none'; };
  if(cfg.enabled===false||!dates||!dates.length) return bail();
  FWD_ARGS={dates:dates,closes:closes};
  if(cfg.ciq&&(cfg.ciq.rows||[]).length) return renderFwdPE_CIQ(dates,closes,cfg);
  var pe1=null,pe2=null,thin=null,nArr=null,subArr=null,subLbl='',capHTML='',foldHTML='';
  // ── 主口径：fetch_fwd_pe.py 的时点序列（按日期对齐 K 线网格）──────────────
  var sr=cfg.series||[];
  if(sr.length){
    var byD={}; sr.forEach(function(x){ if(x&&x.d) byD[x.d]=x; });
    var lm=(cfg.loss_metric==='pb')?'pb':'ps'; subLbl=(lm==='pb')?'PB':'PS(TTM)';
    pe1=[];pe2=[];thin=[];nArr=[];subArr=[];
    dates.forEach(function(d){ var x=byD[d]||{};
      var pe=isFinite(parseFloat(x.pe))?parseFloat(x.pe):null;
      pe1.push(pe);
      pe2.push(isFinite(parseFloat(x.pe1))?parseFloat(x.pe1):null);
      thin.push(!!x.thin||x.basis==='fy1_only'); nArr.push(x.n||0);
      // ★负利润/无覆盖不留白（2026-08-12 用户追加）：pe 空档周画 trailing PS/PB 替代线（左轴）
      var sv=isFinite(parseFloat(x[lm]))?parseFloat(x[lm]):null;
      subArr.push((pe==null&&sv!=null)?sv:null); });
    if(pe1.filter(function(v){return v!=null;}).length<8&&subArr.filter(function(v){return v!=null;}).length<8) return bail();
    var subN=subArr.filter(function(v){return v!=null;}).length;
    capHTML='<b>2.1b 隐含 Forward PE 带（时点一致预期）</b>：价格涨、线不涨＝盈利上修消化（R）；线整体抬台阶＝重估值（M/V）；'
      +(cfg.weeks_covered!=null?('PE '+cfg.weeks_covered+'/'+cfg.weeks+' 周'):'')
      +(subN?('，无PE周（负利润/无卖方覆盖）已切 <b>'+subLbl+'</b> 替代线（左轴·第一档口径）'):'')+'。';
    foldHTML=foldBox('口径与方法（时点一致预期怎么重建的）',
      esc(cfg.caliber||'')+'；来源 '+esc(cfg.src||'')+'，研报 '+(cfg.reports_n||0)+' 份/'+(cfg.orgs_n||0)+' 家（窗口 '
      +(cfg.lookback_days||180)+' 天，<'+(cfg.min_brokers||3)+' 家标虚线段）。逐份研报无前视；PE=周收盘÷NTM EPS（券商股本口径，看形态与拐点为主）；'
      +'替代线='+subLbl+'（报告期按公告日/法定披露截止日可见，无前视），量纲与 PE 不同走左轴，PE/'+subLbl+' 两段不可直接比高低。');
  } else {
  // ── fallback：FMP 财年快照合成（近似，有前视）────────────────────────────
    var cons=D.part1&&D.part1.consensus; var m=D.meta||{}; var shares=num(m.shares_yi,0);
    if(!cons||!(cons.years||[]).length||!shares) return bail();
    var fx=1;
    if(cons.reported_currency&&cons.page_currency&&cons.reported_currency!==cons.page_currency){
      if(isFinite(parseFloat(m.fx))&&parseFloat(m.fx)>0) fx=parseFloat(m.fx); else return bail(); }
    var ys=(cons.years||[]).map(function(y){ var np=y.np||{};
        return {yr:parseInt(String(y.label||'').replace(/\D/g,''),10),
                avg:parseFloat(np.avg),synth:!!(np.synthetic||y.synthetic)}; })
      .filter(function(y){ return isFinite(y.yr); }).sort(function(a,b){ return a.yr-b.yr; });
    if(!ys.length) return bail();
    var ann={}; ((D.part2||{}).earnings||[]).forEach(function(e){ if(e&&e.type==='年报'&&e.period){
      var yy=parseInt(String(e.period).slice(0,4),10); if(isFinite(yy)) ann[yy]=e.date; } });
    var annOf=function(yr){ return ann[yr]||((yr+1)+'-04-30'); };
    var usable=function(y){ return y&&!y.synth&&isFinite(y.avg)&&y.avg*fx>0; };
    pe1=[];pe2=[];
    dates.forEach(function(d,i){ var fy1=null,fy2=null;
      for(var k=0;k<ys.length;k++){ if(annOf(ys[k].yr)>d){ fy1=ys[k]; fy2=ys[k+1]||null; break; } }
      var mc=num(closes[i])*shares;
      pe1.push(usable(fy1)?mc/(fy1.avg*fx):null);
      pe2.push(usable(fy2)?mc/(fy2.avg*fx):null); });
    if(pe1.filter(function(v){return v!=null;}).length<8) return bail();
    capHTML='<b>2.1b 隐含 Forward PE 带 <span class="datagap">（近似口径：FMP 财年快照，有前视——跑 scripts/fetch_fwd_pe.py 换真·时点一致预期）</span></b>';
    foldHTML=foldBox('口径与方法（近似合成，建议升级）',
      'fwd 净利=各财年财报前一致预期（FMP 快照，每财年仅一份 → 整年铺平线，早期日期用了当时不存在的数字=前视偏差）；年报公告日换挡；合成区间期与净利≤0 期断线。A 股请改跑 fetch_fwd_pe.py 由逐份券商研报重建时点序列。');
  }
  var med=(function(a){ a=a.filter(function(v){return v!=null;}).slice().sort(function(x,y){return x-y;});
    return a.length?a[Math.floor(a.length/2)]:null; })(pe1);
  var anchors=(cfg.anchors||[]).map(function(a){ var peA=parseFloat(a.pe);
      if(!isFinite(peA)&&isFinite(parseFloat(a.mcap_yi))&&isFinite(parseFloat(a.profit_yi))&&parseFloat(a.profit_yi)>0)
        peA=parseFloat(a.mcap_yi)/parseFloat(a.profit_yi);
      return Object.assign({},a,{x:snapIdx(dates,a.date),peA:peA}); })
    .filter(function(a){ return a.x>=0&&a.x<dates.length&&isFinite(a.peA); });
  var thinDash=function(ctx){ return (thin&&(thin[ctx.p0DataIndex]||thin[ctx.p1DataIndex]))?[4,3]:undefined; };
  var ds=[
    {type:'line',label:sr.length?'Forward PE（NTM 时点一致预期）':'Forward PE（FY1 财报前快照·近似）',data:pe1,
     borderColor:p.accent,borderWidth:1.8,pointRadius:0,tension:0,spanGaps:false,order:2,
     segment:{borderDash:thinDash}},
    {type:'line',label:'Forward+1 PE（再往后一年）',data:pe2,borderColor:p.s[3],borderWidth:1.4,borderDash:[5,4],
     pointRadius:0,tension:0,spanGaps:false,fill:'-1',backgroundColor:hexA(p.accent,'12'),order:3}];
  if(med!=null) ds.push({type:'line',label:'中位 '+(Math.round(med*10)/10)+'x',data:dates.map(function(){return med;}),
    borderColor:p.muted,borderWidth:1,borderDash:[2,4],pointRadius:0,tension:0,order:4});
  var subHas=subArr&&subArr.some(function(v){return v!=null;});
  if(subHas) ds.push({type:'line',label:'无PE周 → '+subLbl+'（左轴）',data:subArr,
    borderColor:p.s[5],borderWidth:1.6,borderDash:[3,3],pointRadius:0,tension:0,spanGaps:false,yAxisID:'y2',order:5});
  if(anchors.length) ds.push({type:'scatter',label:'◆ 卖方锚(纪要/研报当时账)',data:anchors.map(function(a){return {x:a.x,y:a.peA};}),
    parsing:false,pointStyle:'rectRot',pointRadius:5.5,pointHoverRadius:8,backgroundColor:p.s[6],borderColor:p.bg,borderWidth:1,order:1});
  var scales={ x:{type:'category',grid:{display:false},ticks:{color:p.muted,maxTicksLimit:14,autoSkip:true,maxRotation:0,callback:function(v){var d=dates[v];return d?d.slice(0,7):'';}}},
        y:{ position:'right',grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'x';}} } };
  if(subHas) scales.y2={ position:'left',grid:{display:false},ticks:{color:p.s[5],callback:function(v){return v+'x';}},
    title:{display:true,text:subLbl,color:p.s[5],font:{size:10}} };
  mkChart('chart-fwdpe',{ data:{labels:dates,datasets:ds},
    options:{ maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
      plugins:{ legend:legLine(), tooltip:Object.assign(TT(),{displayColors:true,callbacks:{
        title:function(it){ if(!it.length)return ''; var i=it[0].dataIndex;
          return dates[i]+(nArr&&nArr[i]?('　覆盖 '+nArr[i]+' 家'+(thin&&thin[i]?'（薄）':'')):''); },
        label:function(it){ if(it.dataset.type==='scatter'){ var a=anchors[it.dataIndex]||{};
            return '◆ '+(a.label||'卖方锚')+' '+(Math.round(a.peA*10)/10)+'x'+(a.src?(' · '+a.src):''); }
          return it.dataset.label+' '+(it.raw==null?'—':(Math.round(it.raw*10)/10)+'x')+(it.dataset.yAxisID==='y2'?'（左轴）':''); } }}) },
      scales:scales } });
  blk.style.display='';
  var alist=anchors.length?('<div class="fwd-anchors">'+anchors.map(function(a){
      return '<span class="fwd-a">◆ '+esc(a.date||'')+' '+esc(a.label||'')+' '+(Math.round(a.peA*10)/10)+'x'
        +(a.src?(' <span class="muted">'+esc(a.src)+'</span>'):'')
        +(a.url?(' <a href="'+esc(a.url)+'" target="_blank" rel="noopener">↗原文</a>'):'')+'</span>'; }).join('')+'</div>'):'';
  el('fwdpe-sub').innerHTML=capHTML+(cfg.note?(' '+esc(cfg.note)):'')+alist+foldHTML;
}
// 2.2 阶段分解 + 估值算账 —— 横向列(左→右对齐 K线)，每列=一个阶段
function renderPhasePanel(){ var phases=(D.part2&&D.part2.phases)||[]; var vs=(D.part2&&D.part2.valuations)||[]; var p=PAL();
  if(!phases.length){ el('phase-panel').innerHTML='<span class="datagap">⚠️ 未生成 阶段划分</span>'; return; }
  var span=function(ph){ return Math.max(1,(ph.endIdx-ph.startIdx)); };
  var sec=function(k,b){ return b?('<div class="phc-sec"><div class="phc-k">'+k+'</div><div class="phc-v">'+b+'</div></div>'):''; };
  /* ★2026-08-12 因子量化：每段涨幅分解成 R/M/V 各贡献多少 pp（phases[].factor_quant，
     对数三因子分解：ln(P1/P0)=Δln(fwd收入)+Δln(fwd净利率)+Δln(fwd PE)，见 03 §2f-q）。
     所有阶段共用同一坐标尺度（fqMax），条长可以跨列直接比——这是「放在阶段里但可横向比较」的实现。 */
  var fqMax=0; phases.forEach(function(ph){ var f=ph.factor_quant; if(!f) return;
    ['r_pp','m_pp','v_pp'].forEach(function(k){ var x=Math.abs(num(f[k])); if(x>fqMax) fqMax=x; }); });
  /* compact=true 用于上层对齐条带：只留 条 + 形态 + Σ 核对；
     basis（口径说明，常有 60–150 字）搬到下层详情区，条带里放不下也不该放。 */
  /* ★2026-08-18 用户改制：**底部没有利润的段不许再用 PE 做 V 层**（03 §2f-q2）。
     ln(PE1/PE0) 在 E→0 时不是「大」，是**没有定义**；勉强算出来的 V 会吃掉整段涨幅，
     R 和 M 被挤成两根看不见的短条，读者据此得出「这一段全是估值」——而真相往往是
     「这一段根本没有盈利这把尺子可用」。第一档估值（PB/重置成本，周期底部与当期亏损）的公司同理。
     所以 factor_quant 带 `ruler`：PE / PS / PB / EV/EBITDA，三层的**含义随尺子换**。
     换了尺子的段，V 条与别段的 V 条**不是同一个量**，页面必须说出来——三根条本来就是
     「全阶段共用同一尺度、可跨列直接比」，跨段换尺子会把这个前提悄悄毁掉。 */
  var RULER_MEAN={
    'PE': {R:'收入（一致预期）',M:'净利率',V:'PE'},
    'PS': {R:'收入（一致预期）',M:'—（无盈利可拆，已并入 V）',V:'PS'},
    'PB': {R:'净资产',        M:'—（无盈利可拆，已并入 V）',V:'PB'},
    'EV/EBITDA': {R:'收入',   M:'EBITDA 利润率',V:'EV/EBITDA'}
  };
  var rulerOf=function(ph){ var r=(ph.factor_quant||{}).ruler; return (r&&RULER_MEAN[r])?r:'PE'; };
  var rulers={}; phases.forEach(function(ph){ if(ph.factor_quant) rulers[rulerOf(ph)]=1; });
  var mixed=Object.keys(rulers).length>1;
  var fqHTML=function(ph,compact){ var f=ph.factor_quant;
    if(!f||!fqMax) return '<div class="fq-missing">⚠️ 未量化 R/M/V 贡献（phases[].factor_quant）</div>';
    var rk=rulerOf(ph), mean=RULER_MEAN[rk];
    var row=function(k,v){ v=num(v); var w=fqMax?Math.min(50,Math.abs(v)/fqMax*50):0; var pos=v>=0;
      return '<div class="fq-row"><span class="fq-k" style="color:'+CODE_COLOR[k]+'" title="'+esc(k+' 层＝'+mean[k])+'">'+k+'</span>'
        +'<span class="fq-track"><i class="fq-zero"></i><i class="fq-bar" style="'+(pos?'left:50%':'right:50%')+';width:'+w+'%;background:'+CODE_COLOR[k]+'"></i></span>'
        +'<span class="fq-v" style="color:'+CODE_COLOR[k]+'">'+(v>=0?'+':'')+(Math.round(v))+'pp</span></div>'; };
    var sum=num(f.r_pp)+num(f.m_pp)+num(f.v_pp);
    var tail=isFinite(sum)?('Σ='+(sum>=0?'+':'')+Math.round(sum)+'pp vs 段涨幅 '+esc(chgTxt(ph.chg))):'';
    // 尺子徽章：只要全页不止一把尺子，每段都印（印在有异常的那一段上会让读者以为别段"没问题"）
    var badge=(mixed||rk!=='PE')
      ? ('<div class="fq-ruler'+(rk!=='PE'?' alt':'')+'" title="'+esc('R＝'+mean.R+'　M＝'+mean.M+'　V＝'+mean.V)+'">尺子 '+esc(rk)
         +'　<span class="fq-note">R＝'+esc(mean.R.replace(/（.*/,''))+' · M＝'+(/^—/.test(mean.M)?'无（并入 V）':esc(mean.M))+' · V＝'+esc(mean.V)+'</span></div>')
      : '';
    var why=(!compact&&rk!=='PE'&&f.ruler_why)?('<div class="fq-basis"><b>为什么换尺子：</b>'+esc(f.ruler_why)+'</div>')
           :((!compact&&rk!=='PE')?'<div class="fq-basis"><span class="rd">未写 ruler_why（CK-8 g5 不过）</span></div>':'');
    return '<div class="fq">'+badge+row('R',f.r_pp)+row('M',f.m_pp)+row('V',f.v_pp)
      +(ph.factor_signature?('<div class="fq-basis"><b>形态：'+esc(ph.factor_signature)+'</b></div>'):'')
      +why
      +(compact ? ('<div class="fq-basis">'+tail+'</div>')
                : ('<div class="fq-basis">'+(f.basis?esc(f.basis):'')+(tail?(' '+tail):'')+'</div>'))
      +'</div>'; };
  /* ★2026-08-14 篮子/行业对照（phases[].basket_beta，见 14 §7b-0/§7b-1）。
     概念篮子有诞生日：建链日晚于阶段起点的行已在生成期硬闸掉，落在 dropped[] 里只交代不给数。
     行业锚（申万二级+沪深300）分类持续维护、成分非事后圈定，与概念篮子不同源，所以分两组渲不混表。 */
  var bbHTML=function(ph){ var bb=ph.basket_beta; if(!bb) return '';
    var fmt=function(v,u){ v=Math.round(v*10)/10; return (v>=0?'+':'')+v.toFixed(1)+u; };
    var line=function(r,showBorn){ var c=num(r.chg), e=r.excess;
      if(r.chg==null) return '<div class="bb-r"><span class="bb-n">'+esc(r.name)+'</span><span class="bb-none" style="flex:none">'+esc(r.error||'数据不可得')+'</span></div>';
      return '<div class="bb-r"><span class="bb-n">'+esc(r.name)
        +(showBorn&&r.born?(' <span class="bb-born">'+esc(r.born)+'起</span>'):'')+'</span>'
        +'<span class="bb-c">'+fmt(c,'%')+'</span>'
        +'<span class="bb-e" style="color:'+(num(e)>=0?PAL().good:PAL().bad)+'">'+(e==null?'—':fmt(num(e),'pp'))+'</span></div>'; };
    var rows=bb.rows||[], bench=bb.bench||[], drop=bb.dropped||[];
    var usable=rows.length||bench.some(function(b){return b.chg!=null;});
    var h='<div class="bb">';
    if(!usable){
      h+='<div class="bb-none">本段无任何同期存在的对照：叙事篮子 '+drop.length+' 条全部为事后定义、行业锚未覆盖。'
        +'不给超额读数，分析逻辑里也不引用篮子数字。</div>';
    }else{
      if(rows.length) h+='<div class="bb-grp">叙事篮子（已剔本股 · 当前成分回溯）</div>'+rows.map(function(r){return line(r,true);}).join('');
      if(bench.length) h+='<div class="bb-grp">行业 / 市场锚（申万二级 · 同期成分）</div>'+bench.map(function(r){return line(r,false);}).join('');
    }
    if(drop.length) h+='<details class="bb-drop"><summary>▸ 已剔除 '+drop.length+' 条（概念诞生日晚于本段起点）</summary><ul>'
      +drop.map(function(d){ return '<li>'+esc(d.name)+'：'+esc(d.why||'')+'</li>'; }).join('')+'</ul></details>';
    return h+'</div>'; };
  /* ★2026-08-16 双口径估值算账（valuations[i].calibers，见 03 §4e-2）——读者反馈：
     「这里不仅要用 TTM 的估值口径算一遍，如果有的话还要用 Forward 口径算一遍」。
     病灶不是漏写一句，是 **schema 降级**：算账原本是一坨 prose HTML(`body`)，
     03 §③ 的规范里明明写了「…→PE 档→隐含→Forward→ΔPE」，但散文里少一段没有任何东西会报错，
     「写了」和「没写」在机器看来一模一样。赛力斯阶段①③ 的 Forward 腿就是这么消失的——
     而 Forward 数据当时就躺在同一份 page_model 的 part2.fwd_pe.ciq.rows 里。
     现在拆成字段：ttm / fwd 两栏并排，缺哪一栏必须给 na 理由，机器闸 CK-8 g/g2 查。
     ★分子共用同一个市值，所以两个读数的差异只可能来自分母，才可比。
     ★Forward 那栏还给一条**恒等式**分解（市值 ≡ 前瞻盈利 × 前瞻PE）——不是估计、不是回归，
     所以「这段跌的是盈利还是倍数」在前瞻口径下有唯一答案；与 TTM 口径打架时以它为准
     （TTM 的 E 装的是过去四个季度已经赚到的钱，拐点上天然滞后）。 */
  var mult=function(x,d){ return x==null?null:(Math.round(x*Math.pow(10,d==null?2:d))/Math.pow(10,d==null?2:d)); };
  var calLeg=function(nm,o,unit){
    if(!o) return '';
    if(o.delta==null) return '<div class="cl-r"><span class="cl-k">'+nm+'</span><span class="cl-na">'+esc(o.na||'不可得')+'</span></div>';
    var up=o.delta>=0, c=up?PAL().good:PAL().bad;
    return '<div class="cl-r"><span class="cl-k">'+nm+'</span>'
      +'<span class="cl-v">'+mult(o.start)+' → '+mult(o.end)+unit+'</span>'
      +'<span class="cl-d" style="color:'+c+'">'+(up?'+':'')+mult(o.delta)+unit+'</span></div>'; };
  var calHTML=function(c){
    if(!c) return '<div class="fq-missing">⚠️ 未算双口径（valuations[].calibers，CK-8 g）——'
      +'只用一把尺子算的算账不知道自己错在哪。</div>';
    var t=c.ttm||{}, f=c.fwd||{}, n=c.numerator||{}, dc=f.decomp;
    var col=function(ttl,o,sub){ return '<div class="cl-c"><div class="cl-h">'+ttl+'</div>'
      +calLeg('PE',o.pe,'x')+calLeg('P/S',o.ps,'x')
      +'<div class="cl-s">'+esc(sub||'')+'</div></div>'; };
    var h='<div class="cl">'
      +'<div class="cl-num">分子共用：市值 '+yi(n.mcap_start_yi)+' → '+yi(n.mcap_end_yi)+' 亿'
      +'<span class="cl-why">（两把尺子换的只是分母，所以读数差异可比）</span></div>'
      +'<div class="cl-grid">'
      + col('已发生 · TTM', t, (t.q_asof&&t.q_asof.start)?('分母＝当时可见 TTM（'+esc(t.q_asof.start||'')+' → '+esc(t.q_asof.end||'')+'，按公告日不按期末日）'):(t.gap_note||''))
      + col('前瞻 · Forward FY+1', f, (f.fy&&f.fy.start)?('分母＝当时的 FY'+f.fy.start+' → FY'+f.fy.end+' 一致预期'+(f.snap_note?('；'+esc(f.snap_note)):'')):(f.snap_note||''))
      +'</div>';
    if(dc) h+='<div class="cl-id"><b>恒等式</b>　市值 <b>'+(dc.d_mcap_pct>=0?'+':'')+dc.d_mcap_pct+'%</b>'
      +' ＝ 前瞻盈利 <b style="color:'+(dc.d_earn_pct>=0?PAL().good:PAL().bad)+'">'+(dc.d_earn_pct>=0?'+':'')+dc.d_earn_pct+'%</b>'
      +' × 前瞻PE <b style="color:'+(dc.d_mult_pct>=0?PAL().good:PAL().bad)+'">'+(dc.d_mult_pct>=0?'+':'')+dc.d_mult_pct+'%</b>'
      +'　<span class="cl-why">'+esc(dc.ni_start)+'→'+esc(dc.ni_end)+' 亿 × '+esc(dc.pe_start)+'→'+esc(dc.pe_end)+'x</span></div>';
    if(c.read) h+='<div class="cl-read">'+c.read+'</div>';
    return h+'</div>'; };

  /* ★2026-08-16 版式重构（读者反馈「分析逻辑、估值算账排版过于长了，正文分成了好几个部分，宽度不够」）
   * ─────────────────────────────────────────────────────────────────────────
   * 实测病灶：6 段并排 → 每列被压到 **180px 宽（min-width 触底）却 2,741px 高**，
   * 长宽比 1:15；光「估值算账」一节就是 805 字在 180px 里折成 976px 高。
   * 这不是字太多，是**把两种阅读方式塞进了同一个容器**：
   *   · 「对齐 K 线横向扫读」要的是**窄而齐**——每段一眼看完、跨列比长短；
   *   · 「读懂一段的算账」要的是**宽而连贯**——算式、双口径两栏、Step A/B/C 都需要横向空间。
   * 宽度是零和的，一个容器同时满足不了。所以拆成两层，各自拿到合适的宽度：
   *   ① 上层「对齐条带」：只放扫读得动的东西（名/涨跌/主要矛盾一行/R/M/V 条/双口径数字摘要），
   *      仍按 span 比例对齐 K 线，列变成可点的 tab，目标高度压到 ~1/6；
   *   ② 下层「详情区」：**整页宽**渲选中段的 分析逻辑 + 估值算账（双口径并排两栏此时各有 ~450px）。
   * 禁止纵向堆卡那条规矩管的是①（对齐扫读那一层），不是②——②本来就该是全宽正文。
   * 打印时②全部展开（见 @media print），纸面不丢内容。 */
  var selPh = (window.__PH_SEL__==null) ? (phases.length-1) : Math.max(0,Math.min(phases.length-1,window.__PH_SEL__));
  window.__PH_SEL__ = selPh;

  /* 条带里的双口径**数字摘要**：一行一把尺子，只给 Δ 与主因徽章，细节在下面详情区 */
  var calMini=function(c){
    if(!c) return '<div class="pm-cal pm-cal-none">未算双口径</div>';
    var pick=function(o){ if(!o) return null;
      if(o.pe&&o.pe.delta!=null) return {k:'PE',d:o.pe.delta,u:'x'};
      if(o.ps&&o.ps.delta!=null) return {k:'P/S',d:o.ps.delta,u:'x'};
      return {k:(o.pe&&o.pe.na)?'PE':'P/S',na:true}; };
    var row=function(tag,o){ var x=pick(o); if(!x) return '';
      if(x.na) return '<div class="pm-r"><span class="pm-t">'+tag+'</span><span class="pm-na">'+x.k+' 无定义</span></div>';
      var col=x.d>=0?PAL().good:PAL().bad;
      return '<div class="pm-r"><span class="pm-t">'+tag+'</span><span class="pm-m">'+x.k+'</span>'
        +'<span class="pm-d" style="color:'+col+'">'+(x.d>=0?'+':'')+(Math.round(x.d*100)/100)+x.u+'</span></div>'; };
    var dc=(c.fwd||{}).decomp;
    return '<div class="pm-cal">'+row('已发生',c.ttm)+row('前瞻',c.fwd)
      +(dc?('<div class="pm-lead">前瞻拆解主因 <b>'+esc(dc.lead)+'</b>'
            +'<span class="pm-eq">盈利 '+(dc.d_earn_pct>=0?'+':'')+dc.d_earn_pct+'% × 倍数 '+(dc.d_mult_pct>=0?'+':'')+dc.d_mult_pct+'%</span></div>'):'')
      +'</div>'; };

  var strip='<div class="ph-cols">'+phases.map(function(ph,i){ var v=vs[i]||{}; var acc=ph.accounting||{};
    var col=ph.color||((chgPct(ph.chg)==null||chgPct(ph.chg)>=0)?p.good:p.bad);
    return '<button type="button" class="phc'+(i===selPh?' is-sel':'')+'" data-ph="'+i+'"'
      +' aria-pressed="'+(i===selPh)+'" data-fbk="part2.phases['+i+']" style="flex:'+span(ph)+' '+span(ph)+' 0;border-top-color:'+col+'">'+
      '<div class="phc-hd"><b>'+esc(ph.name)+'</b><span class="phc-chg" style="color:'+col+'">'+esc(chgTxt(ph.chg))+'</span></div>'+
      '<div class="phc-meta">'+esc(ph.period||'')+'</div>'+
      '<div class="phc-cc" title="'+esc(ph.core_conflict||acc.headline||ph.narrative||'')+'">'
        +esc(ph.core_conflict||acc.headline||ph.narrative||'')+'</div>'+
      '<div class="phc-fac">主 <b style="color:'+(CODE_COLOR[ph.main_factor]||'')+'">'+esc(ph.main_factor||'')+'</b>'
        +(ph.sub_factor?(' · 次 '+esc(ph.sub_factor)):'')+'</div>'+
      fqHTML(ph,true)+ calMini(v.calibers)+
      '<div class="phc-more">'+(i===selPh?'▼ 详情在下方':'点看详情')+'</div>'+
    '</button>'; }).join('')+'</div>';

  /* 换过尺子就必须在这里说破：三根条的全部意义建立在「同尺度、可跨列比」上，
     而 PB 段的 V 与 PE 段的 V 根本不是同一个量。不说，读者会照旧横着比。 */
  var mixNote=mixed?('<div class="callout warn" style="margin-top:6px;font-size:12.5px">'
      +'<b>本页用了不止一把尺子：'+Object.keys(rulers).join(' / ')+'。</b>'
      +'底部无利润（或第一档估值）的段 PE 无定义，V 层改用 PB／PS——'
      +'<b>这些段的 V 条与 PE 段的 V 条不是同一个量，不要横着比长短</b>；R 与 M 的含义也随之改变（见每段的尺子徽章）。'
      +'同一把尺子的段之间仍可直接比。</div>'):'';
  el('phase-panel').innerHTML = strip
    + '<div class="cap" style="margin-top:4px">← 横向对齐上方 K 线各阶段：一列＝一段的矛盾/因子/分解/双口径摘要，R/M/V 条同尺度可跨列比长短；'
    + '<b>点任一列，下方整页宽展开该段的分析逻辑与估值算账</b> →</div>'
    + mixNote
    + '<div id="phase-detail"></div>';
  renderPhaseDetail();

  /* 列＝tab：点一下换详情。用事件委托，重渲后不用重新绑 */
  var host=el('phase-panel');
  if(host && !host.__phBound){ host.__phBound=true;
    host.addEventListener('click',function(e){
      var b=e.target&&e.target.closest&&e.target.closest('.phc[data-ph]'); if(!b) return;
      var i=parseInt(b.getAttribute('data-ph'),10); if(!isFinite(i)) return;
      window.__PH_SEL__=i;
      host.querySelectorAll('.phc').forEach(function(x,k){ x.classList.toggle('is-sel',k===i);
        x.setAttribute('aria-pressed',String(k===i));
        var m=x.querySelector('.phc-more'); if(m) m.textContent=(k===i)?'▼ 详情在下方':'点看详情'; });
      renderPhaseDetail();
    });
  }

  /* 下层详情：整页宽。选中段渲全文，其余段折进 <details> 供打印/检索（打印时 CSS 强制展开） */
  function detailBody(i){ var ph=phases[i]||{}, v=vs[i]||{}, acc=ph.accounting||{};
    var acct=(v.body||(acc.steps||[]).map(esc).join('<br>'));
    var head=(v.cap?('<b>市值 '+esc(v.cap)+' · PE '+esc(v.pe||acc.pe_tiers||'')+'</b><br>'):(acc.pe_tiers?('<b>PE '+esc(acc.pe_tiers)+'</b><br>'):''));
    var col=ph.color||((chgPct(ph.chg)==null||chgPct(ph.chg)>=0)?p.good:p.bad);
    return '<div class="phd-hd" style="border-left-color:'+col+'">'
        +'<b>'+esc(ph.name)+'</b><span class="phd-chg" style="color:'+col+'">'+esc(chgTxt(ph.chg))+'</span>'
        // period 常常本来就是 "from→to"，两个都渲会印成同一串日期两遍
        +'<span class="phd-meta">'+esc(ph.period||((ph.from||'')+'→'+(ph.to||'')))+'</span></div>'
      + '<div class="phd-grid">'
        + '<div class="phd-c"><div class="phc-k">分析逻辑</div><div class="phd-txt">'+esc(ph.logic||ph.narrative||'')+'</div>'
          + ((ph.factor_quant&&ph.factor_quant.basis)
             ? ('<div class="phd-basis"><b>R/M/V 分解口径</b>　'+esc(ph.factor_quant.basis)+'</div>'):'')
          + (ph.basket_beta?('<div class="phc-k" style="margin-top:9px">对照 · 个股 '+esc(chgTxt(ph.chg))
             +' vs <span class="fq-note">篮子/行业（右列＝超额）</span></div>'+bbHTML(ph)):'')+'</div>'
        + '<div class="phd-c"><div class="phc-k">估值算账 <span class="fq-note">（两把尺子各算一遍）</span></div>'
          + calHTML(v.calibers) + '<div class="phd-txt">'+head+acct+'</div>'
          + (v.consensus?('<div class="phc-cons">质检：'+v.consensus+'</div>'):'')+'</div>'
      + '</div>'; }

  function renderPhaseDetail(){ var host=el('phase-detail'); if(!host) return;
    var i=window.__PH_SEL__;
    host.innerHTML='<div class="phd" data-fbk="part2.valuations['+i+']">'+detailBody(i)+'</div>'
      + '<details class="phd-all"><summary>▸ 一次看全部 '+phases.length+' 段的逻辑与算账（打印时自动展开）</summary>'
      + phases.map(function(x,k){ return k===i?'':('<div class="phd phd-alt">'+detailBody(k)+'</div>'); }).join('')
      + '</details>'; }
}
// 2.3 催化清单（紧凑索引；9 维详情走图上▲标记二阶弹卡）
function renderCatIndex(cats){
  // ★2026-08-12 默认收起：清单是索引不是正文，点开才展开（<details>，file:// 下无 JS 依赖）
  var tbl='<table><thead><tr><th class="num">#</th><th>类型内#</th><th>日期</th><th>催化节点</th><th>催化剂类型</th><th>码</th><th class="num">周涨跌</th><th>原文</th></tr></thead><tbody>'+
    cats.map(function(c){ var types=(c.codes||[]).map(function(k){return CAT_LABEL[k]||k;}).join(' / ')||'—';
      var lk=(c.links||[]).map(function(L){ return (L&&L.url)?('<a href="'+esc(L.url)+'" target="_blank" rel="noopener">↗'+esc(L.label||'原文')+'</a>'):''; }).join(' ')||'—';
      return '<tr><td class="num">'+c.id+'</td><td class="num">'+(c._occ!=null?('#'+c._occ):'—')+'</td><td>'+esc(c.date||'')+'</td><td>'+esc(c.name||'')+'</td><td>'+esc(types)+'</td><td style="color:'+(CODE_COLOR[c.code]||'')+';font-weight:700">'+esc(c.code||'')+'</td><td class="num '+((c.weekChg||0)>=0?'pos':'neg')+'">'+spct((c.weekChg||0)/100)+'</td><td class="small">'+lk+'</td></tr>'
      +(c.rationale?('<tr class="ratrow"><td></td><td></td><td colspan="6">↳ '+esc(c.rationale)+'</td></tr>'):''); }).join('')+'</tbody></table>';
  el('cat-index').innerHTML='<details class="cat-fold"><summary>▸ 展开催化清单（'+cats.length+' 条 · 含原始材料推演与链接；详情也可悬停图上标记）</summary>'+tbl+'</details>';
}

function renderCatStats(cats){ var p=PAL();
  var typeCount={},codeCount={};
  cats.forEach(function(c){ (c.codes||[]).forEach(function(k){var lb=CAT_LABEL[k]||k; typeCount[lb]=(typeCount[lb]||0)+1;}); codeCount[c.code]=(codeCount[c.code]||0)+1; });
  var n=cats.length||1;
  var bar=function(m,colorMap){ return Object.keys(m).map(function(k){var w=Math.round(m[k]/n*100); return '<div style="display:flex;align-items:center;gap:6px;font-size:11.5px;margin:2px 0"><span style="width:86px;flex:none">'+k+'</span><span style="height:9px;width:'+Math.max(w,4)+'%;background:'+((colorMap&&colorMap[k])||p.accent)+';border-radius:3px;display:inline-block"></span><span class="muted">'+m[k]+' ('+w+'%)</span></div>';}).join(''); };
  var concl=(D.part2&&D.part2.conclusions)||[];
  var gcol={}; Object.keys(CAT_COLOR).forEach(function(k){ gcol[CAT_LABEL[k]||k]=CAT_COLOR[k].fg; });
  el('stats-catalysts').innerHTML='<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div><b class="small">五大催化剂分布</b>'+bar(typeCount,gcol)+'</div><div><b class="small">复合编码分布</b>'+bar(codeCount,CODE_COLOR)+'</div></div>'+
    (concl.length?'<div style="margin-top:10px" class="small">'+concl.map(function(x){return '• '+esc(x);}).join('<br>')+'</div>':'');
}

/* ===========================================================================
 * PART 3 P&L table + assumptions + charts + valuation (interactive)
 * ======================================================================== */

/* ★静态腿活链写回（05 §9.5）：引擎不支持 sotp/endgame 的 link，改假设后必须在回路里回写，
   否则「拖滑块 → SOTP 卡不动」= 勾稽断了。leader 若用 TTM 同期口径对标则不回写（时间语义锚）。 */
/* mdl 缺省＝live MODEL（原行为不变）。传入克隆体时只算数不碰 DOM——4.2 场景要在
   MODEL 之外跑一遍 knobs，不能让它把 live 模型和页面卡片改掉（09 §5.5d）。 */
function relinkStatic(pl,mdl){
  var MDL=mdl||MODEL, live=(MDL===MODEL);
  try{
    var v=(MDL.valuation||{}), ps=v.paradigms||[], byY=pl.byYear||[], H=pl.H||0;
    var sotp=ps.filter(function(r){return r.key==='sotp';})[0];
    if(sotp&&sotp.params&&(sotp.params.segments||[]).length){
      var off=isFinite(sotp.params.year_offset)?sotp.params.year_offset:1;   // 缺省锚首个可见利润年之后一年
      var t=H+off; if(t>=byY.length) t=byY.length-1;
      var row=byY[t]||{}; var gm=num(row.gm), nm=num(row.netMargin);
      var tr=(isFinite(gm)&&gm!==0)?nm/gm:null;                              // 传导率＝净利率÷毛利率（05 §10）
      if(tr!=null){
        sotp.params.segments.forEach(function(sg,i){
          var seg=(pl.seg||[])[i]; if(!seg) return;
          var rev=num(seg.rev&&seg.rev[t]), sgm=num(seg.gm&&seg.gm[t]);
          if(isFinite(rev)&&isFinite(sgm)) sg.profit_yi=Math.round(rev*sgm*tr*10)/10; });
      }
      // 分部估值卡 DOM 同步（.sm-val 与 segments 同序）；克隆体跑分只算数不写页面
      var cards=live?document.querySelectorAll('.sm-val'):[];
      (live?(MDL.segments||[]):[]).forEach(function(ms,i){
        var sv=(ms.model||{}).seg_val; if(!sv||!cards[i]) return;
        var pr=(sotp.params.segments[i]||{}).profit_yi; if(!isFinite(pr)) return;
        sv.profit_yi=pr; sv.mcap_yi=Math.round(pr*num(sv.mult)*10)/10;
        cards[i].innerHTML='稳态净利 '+yi(pr)+' 亿 × '+(sv.mult!=null?sv.mult:'—')+'x = <b>'+yi(sv.mcap_yi)+' 亿</b>'; });
    }
    var eg=ps.filter(function(r){return r.key==='endgame';})[0];
    if(eg&&eg.params&&byY.length){ var last=byY[byY.length-1]||{};
      if(isFinite(num(last.netMargin))) eg.params.net_margin=Math.round(num(last.netMargin)*1000)/1000; }
  }catch(e){}
}

function recompute(){ var pl=EONE.recomputePL(MODEL); relinkStatic(pl); renderPL(pl); renderPLCharts(pl); renderSegTables(pl); renderSegQPCharts(pl); renderValuation(pl); renderLamOut(pl);
  window.__CONS_PL__=pl; if(consPeriod==='annual') renderConsensus();   // 1.5 箱线图上的 ◆(我的模型) 随假设滑块实时移动
  renderSummary(pl); mdBold(); }   // 开篇章「利润兑现期限」随假设联动：改模型 → 兑现年份/隐含PE/赔率同步刷新

/* ★3.1 利润表（2026-08-12 重排为人类阅读顺序）：TOPLINE 总营收在最上，之后每一块都是
 *   「总行 → 分部明细」的小总分结构，左侧加序号列标清归属：
 *   1 营业总收入 → 1.x 分部收入(含量/价子行)
 *   2 毛利汇总(=1−营业成本=Σ2.x) → 2.x 分部毛利(+YoY/毛利率)
 *   3 费用桥 → 3.x 各费用
 *   4 利润链(EBIT→EBITDA→税→少数股东)
 *   5 归母净利润(+净利率/EPS)
 *   钩稽闸门不放松：Σ1.x=1(±0.5%)、Σ2.x=2(±5%)，超限亮红。 */
/* ★2026-08-14 用户要求：YoY 从「每行下面单开一行」搬到「每行右边一组列」。
   右侧列组的表头同样是年份，但**少一年**（首年没有同比）。
   核心变化上色，A 股口径 **涨红跌绿**——注意不能直接套 p.good/p.bad：
   本页调色板里 --good 是绿、--bad 是红，语义名和 A 股方向相反，所以走 .pl-up/.pl-dn 两个类。 */
var YOY_STRONG = 0.50, YOY_LIGHT = 0.20;   // 金额行：|YoY| 阈值
var PP_STRONG = 5.0,  PP_LIGHT = 2.0;      // 比率行：|Δ| 阈值（百分点）

function plYoY(vals, mode){
  var out=[];
  for(var i=1;i<vals.length;i++){
    var a=parseFloat(vals[i-1]), b=parseFloat(vals[i]);
    if(!isFinite(a)||!isFinite(b)){ out.push(null); continue; }
    if(mode==='pp'){ out.push((b-a)*100); continue; }         // 比率行给百分点差
    if(mode==='none'){ out.push(null); continue; }
    // 费用/成本行整列为负，用绝对值算才读得懂（「费用 YoY +20%」＝费用涨了 20%）
    var A=Math.abs(a), B=Math.abs(b);
    out.push(A>1e-9 ? (B/A-1) : null);
  }
  return out;
}
function plYoYCell(v, mode){
  if(v==null||!isFinite(v)) return '<td class="num yoyc">—</td>';
  var strong = mode==='pp' ? Math.abs(v)>=PP_STRONG : Math.abs(v)>=YOY_STRONG;
  var light  = mode==='pp' ? Math.abs(v)>=PP_LIGHT  : Math.abs(v)>=YOY_LIGHT;
  var cls = !light ? '' : ((v>0?' pl-up':' pl-dn') + (strong?' pl-hot':''));
  var txt = mode==='pp' ? ((v>0?'+':'')+(Math.round(v*10)/10)+'pp') : spct(v);
  return '<td class="num yoyc'+cls+'">'+txt+'</td>';
}

function renderPL(pl){ var p=PAL(); var Y=pl.years, H=pl.H;
  var YY=Y.slice(1);                                     // YoY 列组：比值列少一年
  // 组标题在上、年份在下——先告诉读者左右两块各是什么，再看年份。
  // 单位写在这两行里（不是写在下面的 cap 里）：表会横向滚，滚两屏之后 cap 早就不在视野内了。
  var MU=MONEYU();
  var head='<tr class="pl-grp"><th></th><th></th><th colspan="'+Y.length+'">金额'
      +'<span class="th-unit">单位 '+MU+'　·　比率行＝%　·　量／价行的单位写在行名里</span></th>'
    +'<th class="ysep"></th><th colspan="'+YY.length+'">同比 · 核心变化上色'
      +'<span class="th-unit">金额行＝%　·　比率行＝pp　·　涨红跌绿</span></th></tr>'
    +'<tr><th class="rowno">#</th><th class="rowlbl">项目（TOPLINE → 分部 → 毛利 → 费用桥 → 归母）'
      +'<span class="th-unit">金额单位 '+MU+'</span></th>'
    +Y.map(function(y,i){return '<th class="num '+(i<H?'col-hist':'col-fcst')+'">'+esc(y)+'</th>';}).join('')
    +'<th class="ysep"></th>'
    +YY.map(function(y,i){return '<th class="num yoyc '+((i+1)<H?'col-hist':'col-fcst')+'">'+esc(y)+'</th>';}).join('')
    +'</tr>';
  function row(no,label,vals,opt){ opt=opt||{};
    var ys=plYoY(vals, opt.yoyMode);
    return '<tr class="'+(opt.cls||'')+'"><td class="rowno">'+(no||'')+'</td><td class="rowlbl">'+esc(label)+'</td>'+
    vals.map(function(v,i){ var cell=opt.fmt?opt.fmt(v,i):(v==null?'—':yi(v)); var neg=(typeof v==='number'&&v<0);
      return '<td class="num '+(i<H?'col-hist':'col-fcst')+' '+(i<H?'c-actual':'c-calc')+(neg?' neg':'')+'">'+cell+'</td>'; }).join('')
    +'<td class="ysep"></td>'
    +ys.map(function(v){ return plYoYCell(v, opt.yoyMode); }).join('')+'</tr>'; }
  var NCOL=Y.length+1+YY.length;
  function sechd(no,label,note){ return '<tr class="pl-sechd"><td class="rowno">'+no+'</td><td class="rowlbl">'+esc(label)+'</td><td colspan="'+NCOL+'" class="pl-secnote">'+esc(note||'')+'</td></tr>'; }
  var body='';
  var fq=function(v){ v=parseFloat(v); if(!isFinite(v))return '—'; var a=Math.abs(v); return (a>=100?Math.round(v):a>=10?(Math.round(v*10)/10):(Math.round(v*100)/100)).toLocaleString(); };
  // ── 块 1：TOPLINE 总营收 → 分部收入 ─────────────────────────────
  body+=row('1','营业总收入（TOPLINE）',pl.byYear.map(function(r){return r.rev;}),{cls:'totrow'});
  var parDone={}, segNo={}, r1=0;
  pl.seg.forEach(function(s,si){ var ms=(MODEL.segments||[])[si]||{}; var md=ms.model||{};
    var hp=(ms.hist&&ms.hist.p)||[]; var realQP=hp.some(function(v){return isFinite(v)&&Math.abs(v-1)>1e-6;});
    var pk=(ms.derive||{}).parent, no;
    if(pk){ // 派生段：母段先出（1.k），两个子段挂 1.k.1 / 1.k.2
      if(!parDone[pk]){ r1++; parDone[pk]={no:r1,child:0};
        var par=(pl.parents||[]).filter(function(x){return x.key===pk;})[0];
        if(par){ body+=row('1.'+r1,par.name+' 收入（披露合计＝下两段之和）',par.rev,{cls:'subrow parrow'});
          var spl=(MODEL.splits||{})[pk]||{};
          body+=row('','　└ '+(spl.label||'拆分比例 λ')+(spl.adjustable!==false?'（★可调滑块）':''),par.share,
            {cls:'yoy',yoyMode:'pp',fmt:function(v,i){ return (v==null||!isFinite(v))?'—':(pct(v,0)+(i<H?'<span style="font-size:10px;color:#b8860b;margin-left:3px">EST</span>':'')); }}); } }
      parDone[pk].child++; no='1.'+parDone[pk].no+'.'+parDone[pk].child;
    } else { r1++; no='1.'+r1; }
    segNo[si]=no.replace(/^1\./,'');                    // 记住分部编号尾巴，毛利块用 2.同尾
    body+=row(no,s.name+' 收入',s.rev,{cls:'subrow'});
    if(realQP){
      body+=row('','　├ 量'+(md.q_unit?('('+md.q_unit+')'):''),s.q,{cls:'yoy',fmt:fq});
      body+=row('','　└ 价'+(md.p_unit?('('+md.p_unit+')'):''),s.p,{cls:'yoy',fmt:fq});
    }
  });
  // ── 块 2：毛利汇总 → 分部毛利（YoY/毛利率）───────────────────────
  body+=row('','−营业成本（＝1 − 2 反推）',pl.byYear.map(function(r){ return (isFinite(r.rev)&&isFinite(r.gp))?-(r.rev-r.gp):null; }),{cls:'yoy'});
  body+=row('2','毛利（＝1−营业成本＝Σ2.x 分部毛利）',pl.byYear.map(function(r){return r.gp;}),{cls:'totrow'});
  body+=row('','　毛利率（＝2÷1）',pl.byYear.map(function(r){return r.gm;}),{cls:'yoy',yoyMode:'pp',fmt:function(v){return pct(v);}});
  pl.seg.forEach(function(s,si){
    var no='2.'+segNo[si];
    var hasGP=(s.gp||[]).some(function(v){return isFinite(v)&&v!==0;});
    if(!hasGP){ body+=row(no,s.name+' 毛利（⚠️分部毛利率未披露，未拆）',Y.map(function(){return null;}),{cls:'yoy',yoyMode:'none'}); return; }
    body+=row(no,s.name+' 毛利',s.gp,{cls:'subrow'});
    body+=row('','　└ 毛利率',s.gm,{cls:'yoy',yoyMode:'pp',fmt:function(v){return v==null?'—':pct(v);}});
  });
  // ── 块 3：费用桥 ────────────────────────────────────────────────
  var anyv=function(k){ return pl.byYear.some(function(r){return Math.abs(r[k]||0)>1e-9;}); };
  var reg=(MODEL.opex||{}).sga_reg; var e3=0;
  body+=sechd('3','费用桥（2 − 费用 ＝ EBIT）','费用＝费率×营收；回归式则为 固定费用＋变动费率×营收（经营杠杆显式化）');
  var sgaLbl=reg?('−销售及管理费用(回归式 '+(Math.round(num(reg.fc)*10000)/10000)+'亿 ＋ '+pct(num(reg.vc),2)+'×营收)')
                :'−销售及管理费用(承载=sga_rate口径)';
  if(anyv('sga')){ body+=row('3.'+(++e3),sgaLbl,pl.byYear.map(function(r){return r.sga?-r.sga:null;}),{cls:'subrow'});
    if(reg) body+=row('','　└ 隐含费率(＝固定费用被摊薄的轨迹)',pl.byYear.map(function(r){return r.rev?r.sga/r.rev:null;}),
      {cls:'yoy',yoyMode:'pp',fmt:function(v){return v==null?'—':pct(v,2);}}); }
  if(anyv('rnd')) body+=row('3.'+(++e3),'−研发费用',pl.byYear.map(function(r){return r.rnd?-r.rnd:null;}),{cls:'subrow'});
  if(anyv('impair')) body+=row('3.'+(++e3),'−信用及资产减值(可调)',pl.byYear.map(function(r){return r.impair?-r.impair:null;}),{cls:'subrow'});
  // ── 块 4：利润链 ────────────────────────────────────────────────
  var e4=0;
  body+=sechd('4','利润链（EBIT → EBITDA → 税 → 少数股东）','历史列 pretax=EBIT、税为轧差 plug，非纯所得税');
  body+=row('4.'+(++e4),'EBIT（＝2 − 3.x 合计）',pl.byYear.map(function(r){return r.ebit;}));
  if(anyv('da'))  body+=row('4.'+(++e4),'＋D&A(机房/产线等资产折旧摊销)',pl.byYear.map(function(r){return r.da||null;}),{cls:'subrow'});
  body+=row('4.'+(++e4),'EBITDA',pl.byYear.map(function(r){return r.ebitda;}));
  var nonop=pl.byYear.map(function(r){var d=r.pretax-r.ebit; return (r.isForecast&&Math.abs(d)>1e-9)?d:null;});
  if(nonop.some(function(v){return v!=null;})) body+=row('4.'+(++e4),'±营业外·−净利息(预测列)',nonop,{cls:'subrow'});
  if(anyv('tax')) body+=row('4.'+(++e4),'−税(历史列为轧差plug)',pl.byYear.map(function(r){return r.tax?-r.tax:null;}),{cls:'subrow'});
  var mino=pl.byYear.map(function(r){var m=r.pretax-r.tax-r.netProfit; return (r.isForecast&&Math.abs(m)>1e-9)?-m:null;});
  if(mino.some(function(v){return v!=null;})) body+=row('4.'+(++e4),'−少数股东损益(预测列)',mino,{cls:'subrow'});
  // ── 块 5：归母 ─────────────────────────────────────────────────
  body+=row('5','归母净利润',pl.byYear.map(function(r){return r.netProfit;}),{cls:'totrow'});
  body+=row('','　净利率（＝5÷1）',pl.byYear.map(function(r){return r.netMargin;}),{cls:'yoy',yoyMode:'pp',fmt:function(v){return pct(v);}});
  body+=row('','　EPS(元)',pl.byYear.map(function(r){return r.eps;}),{fmt:function(v){return v==null?'—':(Math.round(v*100)/100).toFixed(2);}});
  // ★钩稽运行时闸门(CK-3)：Σ1.x 对 1（±0.5%）；Σ2.x 对 2（±5%，仅分部毛利可算的年份）
  var exBad=[];
  for(var t=0;t<H;t++){ var act=pl.byYear[t].rev, ss=pl.seg.reduce(function(a,s){return a+num(s.rev[t]);},0);
    if(act>0&&Math.abs(ss-act)/act>0.005) exBad.push(Y[t]+'(Σ分部'+yi(ss)+'亿 vs 财报'+yi(act)+'亿)'); }
  var gpBad=[];
  for(var t2=0;t2<Y.length;t2++){ var tg=pl.byYear[t2].gp;
    var allg=pl.seg.every(function(s){return isFinite((s.gp||[])[t2]);});
    if(!allg||!(tg>0)) continue;
    var sg=pl.seg.reduce(function(a,s){return a+num(s.gp[t2]);},0);
    if(Math.abs(sg-tg)/tg>0.05) gpBad.push(Y[t2]+'(Σ分部毛利'+yi(sg)+'亿 vs 合计'+yi(tg)+'亿)'); }
  var uEl=el('pl-unit'); if(uEl) uEl.textContent='　金额单位 '+MU+'（比率行＝%）';
  el('tbl-pl').innerHTML='<table><thead>'+head+'</thead><tbody>'+body+'</tbody></table>'
    +(exBad.length?('<div class="datagap" style="margin-top:4px">⚠️ 拆分不穷尽(Σ1.x 对 1 差>0.5%): '+esc(exBad.join('、'))+' —— 机房/物业等其他资产必须显式入残差段，不得静默丢弃。</div>'):'')
    +(gpBad.length?('<div class="datagap" style="margin-top:4px">⚠️ 分部毛利不闭合(Σ2.x 对 2 差>5%): '+esc(gpBad.join('、'))+' —— 查分部毛利率口径或补残差段毛利。</div>'):'');
}

function renderPLCharts(pl){ var p=PAL();
  var segDs=pl.seg.map(function(s,i){ return {label:s.name,data:s.rev,backgroundColor:p.s[i%8],stack:'r',borderWidth:0}; });
  mkChart('chart-plrev',{ type:'bar', data:{labels:pl.years,datasets:segDs},
    options:{ maintainAspectRatio:false, plugins:{legend:legPts(),tooltip:Object.assign(TT(),{callbacks:{label:function(c){return c.dataset.label+': '+yi(c.raw)+'亿';}}})},
      scales:{x:{stacked:true,grid:{display:false},ticks:{color:p.muted}},y:{stacked:true,grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'亿';}}}} } });
  mkChart('chart-plmargin',{ data:{labels:pl.years,datasets:[
      {type:'line',label:'毛利率',data:pl.byYear.map(function(r){return r.gm*100;}),borderColor:p.s[0],borderWidth:2,pointRadius:2,tension:0},
      {type:'line',label:'净利率',data:pl.byYear.map(function(r){return r.netMargin*100;}),borderColor:p.bad,borderWidth:2,borderDash:[4,3],pointRadius:2,tension:0} ]},
    options:{ maintainAspectRatio:false, layout:{padding:{right:56}}, plugins:{legend:legLine(), endLabels:{series:[{di:0,fmt:function(v){return '毛利 '+Math.round(v)+'%';}},{di:1,fmt:function(v){return '净利 '+Math.round(v)+'%';}}]}, tooltip:Object.assign(TT(),{displayColors:true,callbacks:{label:function(c){return c.dataset.label+': '+pct(c.raw/100);}}})},
      scales:{x:{grid:{display:false},ticks:{color:p.muted}},y:{grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'%';}}}} } });
}

/* ===========================================================================
 * PART 3.2..3.(N+1) 分部细分模型（每个 segment 一节：建模方法+量价锚图+分部估值）
 * ======================================================================== */
function segGrowth(arr){ return (arr||[]).map(function(v,i){ return i&&isFinite(arr[i-1])&&arr[i-1]?(v/arr[i-1]-1):null; }); }
function cagr(arr,n){ if(!arr||arr.length<2)return null; var m=Math.min(n,arr.length-1); var a=arr[arr.length-1-m],b=arr[arr.length-1];
  if(!isFinite(a)||!isFinite(b)||a<=0||b<=0)return null; return Math.pow(b/a,1/m)-1; }
function segRealQP(s){ var hp=(s.hist&&s.hist.p)||[]; return hp.some(function(v){return isFinite(v)&&Math.abs(v-1)>1e-6;}); }
// Part3 章节基数：3.1 利润表 → (有叙事映射时 3.2=叙事↔分部) → 分部模型 → 假设 → 估值
function nmActive(){ var nm=MODEL.narrative_map; return !!(nm&&nm.eras&&nm.eras.length); }
function NBASE(){ return nmActive()?3:2; }
function drvBadge(md){ var st=(md.driver_focus||{}).strength;
  return st==='core'?'<span class="drv-badge core">★ 当下逻辑最强</span>'
       : st==='support'?'<span class="drv-badge sup">逻辑支线</span>'
       : st==='weak'?'<span class="drv-badge weak">弱驱动</span>':''; }
// 3.2 叙事 ↔ 分部映射：旧/现叙事各作用在哪些分部、哪个参数、什么时点、多强
function renderNarrativeMap(){ var host=el('nmap-sec'); if(!host) return;
  if(!nmActive()){ host.innerHTML=''; return; }
  var nm=MODEL.narrative_map;
  var segName={}; (MODEL.parents||[]).forEach(function(p){ segName[p.key]=p.name+'（母段·两个子段一起动）'; });
  (MODEL.segments||[]).forEach(function(s){ segName[s.key]=s.name; });
  var dots=function(x){ x=Math.max(0,Math.min(3,x||0)); var o=''; for(var i=0;i<3;i++)o+=(i<x?'●':'○'); return '<span class="nm-dots">'+o+'</span>'; };
  host.innerHTML='<h2 id="sec-nmap">3.2 叙事 ↔ 分部映射（作用在哪、怎么作用、多强）</h2>'
    +(nm.note?('<div class="callout">'+esc(nm.note)+cite(nm.cite)+'</div>'):'')
    +nm.eras.map(function(e,ei){ var now=/现|当前|进行/.test(e.era||'')||e.now;
      return '<div class="panel nm-era'+(now?' now':'')+'" data-fbk="part3.narrative_map.eras['+ei+']"><div class="nm-hd"><span class="nm-tag'+(now?' now':'')+'">'+esc(e.era||'')+'</span> <b>'+esc(e.name||'')+'</b>'+(e.status?('<span class="nm-status">'+esc(e.status)+'</span>'):'')+'</div>'
      +'<table><thead><tr><th>作用分部</th><th>参数</th><th>时点</th><th>强度</th><th>作用机制（原始材料推演）</th></tr></thead><tbody>'
      +(e.impacts||[]).map(function(im){ return '<tr><td>'+esc(segName[im.seg]||im.seg||'')+'</td><td class="num">'+esc(im.param||'')+'</td><td class="num">'+esc(im.timing||'')+'</td><td>'+dots(im.strength)+'</td><td class="small">'+esc(im.how||'')+'</td></tr>'; }).join('')
      +'</tbody></table></div>'; }).join('');
}
// 分部次级模型表（年为列；量/价/收入/毛利率 + YoY 行；driver_focus 命中格高亮）
function segFocusHit(df,param,year){ if(!df||!df.targets) return false;
  return df.targets.some(function(t){ return t.param===param && (!t.years||t.years.indexOf(year)>=0); }); }
function renderSegTables(pl){ var Y=pl.years,H=pl.H;
  (MODEL.segments||[]).forEach(function(s,si){ var host=el('segtbl-'+si); if(!host) return;
    var md=s.model||{}; var df=md.driver_focus; var es=pl.seg[si]||{}; var realQP=segRealQP(s);
    var fnum=function(v){ v=parseFloat(v); if(!isFinite(v))return '—'; var a=Math.abs(v); return (a>=100?Math.round(v):a>=10?Math.round(v*10)/10:Math.round(v*1000)/1000).toLocaleString(); };
    var fpct=function(v){ return v==null?'—':spct(v); };
    var row=function(label,vals,param,fmt,cls){ return '<tr class="'+(cls||'')+'"><td class="rowlbl">'+label+'</td>'+
      (vals||[]).map(function(v,i){ var hit=param&&(segFocusHit(df,param,Y[i])
          || (param==='rev'&&!realQP&&segFocusHit(df,'q',Y[i])));   // 量价未拆段: q 目标落到收入YoY行
        return '<td class="num '+(i<H?'col-hist c-actual':'col-fcst c-calc')+(hit?' drv-hit':'')+'">'+(v==null||!isFinite(v)?'—':fmt(v))+'</td>'; }).join('')+'</tr>'; };
    var head='<tr><th class="rowlbl">次级模型</th>'+Y.map(function(y,i){ return '<th class="num '+(i<H?'col-hist':'col-fcst')+'">'+esc(y)+'</th>'; }).join('')+'</tr>';
    var body='';
    if(realQP){
      body+=row('量'+(md.q_unit?('('+md.q_unit+')'):''),es.q,null,fnum);
      body+=row('量YoY',segGrowth(es.q),'q',fpct,'yoy');
      body+=row('价'+(md.p_unit?('('+md.p_unit+')'):''),es.p,null,fnum);
      body+=row('价YoY',segGrowth(es.p),'p',fpct,'yoy');
    }
    body+=row('收入(亿)',es.rev,'rev',function(v){return yi(v);});
    body+=row('收入YoY',segGrowth(es.rev),'rev',fpct,'yoy');
    body+=row('分部毛利率',es.gm,'gm',function(v){return pct(v);});
    var note='';
    if(df&&df.targets){ var PN={q:'量YoY',p:'价YoY',gm:'毛利率',rev:'收入YoY'};
      note='<div class="drv-note" data-fbk="part3.segments['+si+'].model.driver_focus"><span class="dn-lead">⚡ 逻辑作用点：</span>'
        +df.targets.map(function(t){ return '<b>'+(PN[t.param]||t.param)+'</b> @ '+(t.years?t.years.join('/'):'全预测期'); }).join(' · ')
        +(df.note?('<br>'+esc(df.note)+evSup(si,df.ev)):'')+'</div>'; }   // verify 只在段末小结出现,不重复
    // 派生段（收入＝母段×λ、量＝收入÷价）：把「量×价＝收入」的对账误差直接摆出来
    var tie='';
    if(s.derive){ var worst=0, fac=num(es.factor,1);
      (es.rev||[]).forEach(function(r,i){ if(!isFinite(r)||!r) return;
        var d=Math.abs(num(es.q[i])*num(es.p[i])*fac-r)/Math.abs(r); if(d>worst) worst=d; });
      var okk=worst<=0.005;
      tie='<div class="tiecheck '+(okk?'ok':'bad')+'">'+(okk?'✓':'✗')+' 量价自洽：量('+esc(md.q_unit||'')+') × 价('+esc(md.p_unit||'')
        +') × '+fac+' ＝ 收入(亿元)，全期最大对账差 '+(Math.round(worst*100000)/1000)+'%'+(okk?'（≤0.5% 闸门通过）':'（超 0.5% 闸门）')+'</div>'; }
    host.innerHTML='<table>'+head+'<tbody>'+body+'</tbody></table>'+tie+note;
    // 小结卡里的活数字（每次 recompute 刷新，防止拖完滑块小结还挂旧账）
    var rev0=(es.rev||[])[H], prev=(es.rev||[])[H-1];
    var nR=document.querySelector('[data-segsum-rev="'+si+'"]'), nY=document.querySelector('[data-segsum-yoy="'+si+'"]');
    if(nR) nR.textContent=(rev0==null||!isFinite(rev0))?'—':yi(rev0);
    if(nY) nY.textContent=(isFinite(rev0)&&isFinite(prev)&&prev)?spct(rev0/prev-1,0):'—';
    var sv2=md.seg_val||{}; var nV=document.querySelector('[data-segsum-val="'+si+'"]');
    if(nV&&sv2.mult!=null) nV.textContent=yi(sv2.mcap_yi!=null?sv2.mcap_yi:(num(sv2.profit_yi)*num(sv2.mult)));
  });
}
/* ---------------------------------------------------------------------------
 * Driver 三件套（2026-07-25 用户反馈固化）：分部的「逻辑」不能只是一段小字散文——
 *   ① driver_chain  逐步算账链（每步 15px 大字 + [Ex] 证据角标 + 结果值）
 *   ② calibers      口径对账表（同一参数不同口径差多少 / 选哪个 / 为什么）
 *   ③ evidence      RAG 原句卡（逐字原文 blockquote + 我的推论分层 + 取原文命令）
 * 三者都可缺省（老 page_model 照旧渲染），但主力分部缺 ①③ 页面会打提示。
 * ------------------------------------------------------------------------ */
var EVIX={};                                   // 'si::E3' -> evidence 对象
function evKey(si,id){ return si+'::'+id; }
function evRegister(si,list){ (list||[]).forEach(function(e){ if(e&&e.id) EVIX[evKey(si,e.id)]=e; }); }
function evSup(si,ids){ if(ids==null||ids==='')return ''; if(!Array.isArray(ids))ids=[ids];
  return ids.map(function(id){ var k=evKey(si,id); var ok=!!EVIX[k];
    return '<sup class="evc'+(ok?'':' miss')+'" data-ev="'+esc(k)+'" title="'+(ok?'点开原始材料原句':'未登记该证据')+'">['+esc(id)+']</sup>'; }).join(''); }
var EV_TYPE={minutes:'纪要',report:'研报',model:'卖方模型',memo:'备忘',news:'公告/新闻',expert:'专家',company:'公司口径',data:'数据库'};
function ragWs(){ return (D.feedback&&D.feedback.rag_ws)||(D.meta&&D.meta.ticker||'').replace(/\..*$/,''); }
// 取原文的两条路：① 有 doc_id → rag_query get_doc（库已建索引/目录）② 只有 file → 直接给原件路径
// （embedding 配额挂掉时 catalog.jsonl 不生成，get_doc 会失败——那种工作区就填 file）
function evRagCmd(e){ return e.doc_id ? ('python scripts/rag_query.py '+ragWs()+' get_doc '+e.doc_id+' --text') : ''; }
// normalized/<doc_id>/content.md 这种路径 basename 全一样 → 取上一级目录名当标签
function evFileLabel(fp){ var xs=String(fp).split(/[\\/]/).filter(Boolean); var b=xs[xs.length-1]||'';
  return (/^(content|card)\.(md|json)$/i.test(b)&&xs.length>1) ? xs[xs.length-2] : b; }
// ---- 证据浮层（原句不再占正文版面：[Ex]/chip 点击 → 浮在另一层上，可翻页/Esc 关） ----
var EVLIST={};                                  // si -> [key,...] 供浮层内翻页
function evChipsHTML(si,md){ var evs=md.evidence||[]; if(!evs.length) return '';
  EVLIST[si]=evs.map(function(e){ return evKey(si,e.id); });
  return '<div class="ev-wrap" data-fbk="part3.segments['+si+'].model.evidence">'
    +'<span class="ev-lead">原始材料原句（'+evs.length+' 条 · 点开＝浮层看逐字原文 → 我的推论，不占正文版面）</span>'
    +'<span class="ev-chips">'+evs.map(function(e){ return '<span class="ev-chip" data-evid="'+esc(evKey(si,e.id))+'" title="点开浮层看原句"><b>['+esc(e.id)+']</b>'
        +esc((EV_TYPE[e.type]||e.type||'材料'))+(e.date?(' '+esc(e.date)):'')+'</span>'; }).join('')+'</span>'
    +'</div>'; }
function evPopHTML(key){ var e=EVIX[key]; if(!e) return '';
  var si=+String(key).split('::')[0]; var cmd=evRagCmd(e); var fp=e.file||'';
  var list=EVLIST[si]||[]; var at=list.indexOf(key);
  var seg=(MODEL.segments||[])[si]||{};
  return '<div class="evp-hd"><b>['+esc(e.id)+']</b> '+esc(EV_TYPE[e.type]||e.type||'材料')
      +(e.src?(' · '+esc(e.src)):'')+'<span class="evp-x" data-evclose="1" title="关闭（Esc / 点页面任意处）">✕</span></div>'
    +'<div class="evp-meta">'+(e.date?esc(e.date):'')+(e.confidence?(' · 可信度 '+esc(e.confidence)):'')
      +(e.doc_id?(' · doc_id '+esc(e.doc_id)+(e.page?(' '+esc(e.page)):'')):'')
      +(!e.doc_id&&fp?(' · 原件 '+esc(evFileLabel(fp))+(e.page?(' '+esc(e.page)):'')):'')
      +(!e.doc_id&&!fp?' · ⚠️ 无 doc_id/原件路径(非 RAG 来源)':'')
      +' · 用在 '+esc(seg.name||('分部'+si))+(e.used_in?('（'+esc([].concat(e.used_in).join('/'))+'）'):'')+'</div>'
    +'<div class="evp-body">'
    +(e.quote?('<div class="evp-tag">逐字原文</div><blockquote>「'+esc(e.quote)+'」</blockquote>')
             :'<div class="datagap">⚠️ 未录原句（evidence.quote 必填逐字原文）</div>')
    +(e.implication?('<div class="evp-tag imp">我的推论（非原文）</div><div class="ev-imp">'+esc(e.implication)+'</div>'):'')
    +'</div>'
    +'<div class="evp-foot">'
      +(cmd?('<code>'+esc(cmd)+'</code><button data-cp="'+esc(cmd)+'" data-cpwhat="取原文命令">复制命令</button>')
        :(fp?('<code>'+esc(fp)+'</code><button data-cp="'+esc(fp)+'" data-cpwhat="原件路径">复制原件路径</button>'):''))
      +'<span class="evp-nav">'+(list.length>1?('<button data-evnav="-1" title="上一条 (←)">‹</button><span class="evp-at">'+(at+1)+' / '+list.length+'</span><button data-evnav="1" title="下一条 (→)">›</button>'):'')+'</span>'
    +'</div>'; }
var EV_OPEN=null;
function openEvPop(key){ var pop=el('evpop'), mask=el('evmask'); if(!pop||!EVIX[key]) return;
  EV_OPEN=key; pop.innerHTML=evPopHTML(key); pop.style.display='block'; if(mask) mask.style.display='block';
  pop.scrollTop=0;
  [].slice.call(document.querySelectorAll('.ev-chip.on')).forEach(function(c){c.classList.remove('on');});
  var chip=document.querySelector('.ev-chip[data-evid="'+cssq(key)+'"]'); if(chip) chip.classList.add('on');
}
function closeEvPop(){ var pop=el('evpop'), mask=el('evmask');
  if(pop) pop.style.display='none'; if(mask) mask.style.display='none'; EV_OPEN=null;
  [].slice.call(document.querySelectorAll('.ev-chip.on')).forEach(function(c){c.classList.remove('on');}); }
function evNav(d){ if(!EV_OPEN) return; var si=+String(EV_OPEN).split('::')[0]; var list=EVLIST[si]||[];
  var at=list.indexOf(EV_OPEN); if(at<0||list.length<2) return;
  openEvPop(list[(at+d+list.length)%list.length]); }
function drvChainHTML(si,md){ var ch=md.driver_chain; if(!ch||!ch.length) return '';
  return '<div class="drv-chain" data-fbk="part3.segments['+si+'].model.driver_chain">'
    +'<div class="dc-hd">外部物理量 → 本段收入（一步一个数，末行=确认收入；点 [Ex] 追原句）</div>'
    +ch.map(function(st){ return '<div class="dc-step'+(st.out?' dc-out':'')+'">'
      +'<div class="dc-k">'+esc(st.step||'')+'</div>'
      +'<div class="dc-x">'+esc(st.expr||'')+evSup(si,st.ev)+(st.tag?(' <span class="dtag '+esc(st.tag)+'">'+esc(st.tag)+'</span>'):'')
        +(st.note?('<div class="dc-note">'+esc(st.note)+'</div>'):'')+'</div>'
      +'<div class="dc-v">'+esc(st.val==null?'':st.val)+'</div></div>'; }).join('')
    +'</div>'; }
var CAL_FLAG={chosen:['ok','✓ 采用'],ref:['ref','参考·交叉验证'],rejected:['no','✗ 弃用']};
var CAL_ORD={chosen:0,ref:1,rejected:2};
/* 口径取舍（★2026-07-25 第三轮反馈：原 6 列表格"很丑、不符合人类认知的顺序和逻辑"）
 * 改为决策卡，按读者真实提问顺序排：
 *   ① 这是哪个数（subject）→ ② 有几种说法·差多少（刻度条，把倍差画出来）
 *   → ③ 我用哪个·为什么·用错的代价（结论先给）→ ④ 候选逐条明细（采用在前，弃用降级）
 * 刻度条要求 rows[].v（数值）；两端差 >10 倍自动切对数轴；给了 v_lo/v_hi 则画区间带。 */
function calScaleHTML(rows,unit){
  var pts=rows.map(function(r,ri){ return {ri:ri,r:r,
      v:(isFinite(parseFloat(r.v))?parseFloat(r.v):null),
      lo:(isFinite(parseFloat(r.v_lo))?parseFloat(r.v_lo):null),
      hi:(isFinite(parseFloat(r.v_hi))?parseFloat(r.v_hi):null)}; })
    .filter(function(x){ return x.v!=null||(x.lo!=null&&x.hi!=null); });
  if(pts.length<2) return '';
  var vals=[]; pts.forEach(function(x){ if(x.v!=null)vals.push(x.v); if(x.lo!=null)vals.push(x.lo); if(x.hi!=null)vals.push(x.hi); });
  var mn=Math.min.apply(null,vals), mx=Math.max.apply(null,vals);
  if(!(mn>0)||!(mx>mn)) return '';
  var logMode=(mx/mn>10);
  var pos=function(v){ var t=logMode?(Math.log(v/mn)/Math.log(mx/mn)):((v-mn)/(mx-mn));
    return Math.max(3,Math.min(97,6+t*88)); };
  var fmt=function(v){ var a=Math.abs(v);
    return (a>=1000?Math.round(v).toLocaleString():a>=100?Math.round(v):a>=10?Math.round(v*10)/10:Math.round(v*100)/100)+(unit||''); };
  var ratio=mx/mn, rtxt=(ratio>=10?Math.round(ratio):Math.round(ratio*10)/10)+'×';
  if(ratio<1.5){                                  // 口径互证(差<50%)：一行说清即可,不必画条
    var pl2=pts.map(function(x){ return esc(x.r.short||fmt(x.v)); }).join(' vs ');
    return '<div class="cal-agree">✓ 这些口径彼此互证：'+pl2+'（差 '+Math.round((ratio-1)*100)+'%），任一层都能当锚</div>'; }
  var marks='', labels='';
  pts.forEach(function(x,k){ var chosen=x.r.status==='chosen', rej=x.r.status==='rejected';
    var cls=chosen?'cs-chosen':(rej?'cs-rej':'cs-ref');
    if(x.lo!=null&&x.hi!=null){ var l=pos(x.lo), w=Math.max(1.5,pos(x.hi)-l);
      marks+='<span class="cs-band '+cls+'" style="left:'+l+'%;width:'+w+'%" title="'+esc(fmt(x.lo)+'–'+fmt(x.hi))+'"></span>'; }
    var at=pos(x.v!=null?x.v:(x.lo+x.hi)/2);
    marks+='<span class="cs-dot '+cls+'" style="left:'+at+'%">'+(chosen?'✓':'')+'</span>';
    var lab=x.r.short||fmt(x.v!=null?x.v:x.lo);
    var needNum=!/[0-9]/.test(String(lab));      // 短标签已含数字就不再重复一行数值
    labels+='<span class="cs-lab '+cls+(k%2?' alt':'')+'" style="left:'+at+'%">'
      +'<b>'+esc(lab)+'</b>'+(needNum&&x.v!=null?('<i>'+esc(fmt(x.v))+'</i>'):'')+'</span>';
  });
  return '<div class="cal-scale"><div class="cs-labs">'+labels+'</div>'
    +'<div class="cs-track'+(logMode?' logmode':'')+'">'+marks+'</div>'
    +'<div class="cs-foot"><span>'+esc(fmt(mn))+'</span><span class="cs-ratio">跨口径差 '+rtxt+(logMode?'（对数轴）':'')+'</span><span>'+esc(fmt(mx))+'</span></div></div>';
}
function calHTML(si,md){ var cs=md.calibers; if(!cs) return ''; if(!Array.isArray(cs)) cs=[cs];
  var xs=cs.filter(function(c){return c&&(c.rows||[]).length;});
  return xs.map(function(cb,ci){
    var rows=(cb.rows||[]).slice().sort(function(a,b){ return (CAL_ORD[a.status]==null?1:CAL_ORD[a.status])-(CAL_ORD[b.status]==null?1:CAL_ORD[b.status]); });
    var ch=rows.filter(function(r){return r.status==='chosen';})[0]||{};
    var nAlt=rows.length;
    return '<div class="cal-box" data-fbk="part3.segments['+si+'].model.calibers['+ci+']">'
      // ① 哪个数 + ② 有几种说法/差多少
      +'<div class="cal-hd"><span class="cal-q">'+(xs.length>1?((ci+1)+'）'):'')+esc(cb.subject||'关键参数')+'</span>'
        +'<span class="cal-n">'+nAlt+' 种口径</span>'
        +(cb.spread?('<span class="cal-spread">'+esc(cb.spread)+'</span>'):'')+'</div>'
      +calScaleHTML(rows,cb.unit)
      // ③ 结论先给：用哪个 · 为什么 · 用错的代价
      +'<div class="cal-pick">'
        +'<div class="cp-hd">✓ 本模型采用</div>'
        +'<div class="cp-name">'+esc(cb.chosen_label||ch.caliber||cb.chosen||'—')+'</div>'
        +(cb.why?('<div class="cp-why"><b>为什么：</b>'+esc(cb.why)+evSup(si,cb.ev)+'</div>')
          :'<div class="datagap">⚠️ 未写口径选择理由（calibers.why：为什么用这个口径、与公式怎么对齐）</div>')
        +(cb.cost_if_wrong?('<div class="cp-cost"><b>用错的代价：</b>'+esc(cb.cost_if_wrong)+'</div>'):'')
      +'</div>'
      // ④ 候选逐条（采用在前，弃用视觉降级）
      +'<div class="cal-alts"><div class="ca-lead">'+nAlt+' 种口径各自的账</div>'
      +rows.map(function(r){ var f=CAL_FLAG[r.status]||CAL_FLAG.ref;
        var num=(r.raw!=null&&r.raw!=='')?esc(r.raw):'—';
        var nm=String(r.norm==null?'':r.norm);
        var dead=/不可用|不可入模|—/.test(nm)||r.status==='rejected';
        var same=/同左|基准/.test(nm)||nm===''||nm===String(r.raw);
        return '<div class="cal-alt '+(r.status||'ref')+'">'
          +'<div class="ca-top"><span class="cal-flag '+f[0]+'">'+f[1]+'</span>'
            +'<b>'+esc(r.caliber||r.key||'')+'</b></div>'
          +'<div class="ca-num"><span class="ca-raw">'+num+'</span>'
            +(dead?'<span class="ca-nono">不可直接入模</span>'
                  :(same?'<span class="ca-base">＝本模型基准口径</span>'
                        :('<span class="ca-arrow">→ 归一 </span><span class="ca-norm">'+esc(nm)+'</span>')))+'</div>'
          +(r.conv?('<div class="ca-conv">'+esc(r.conv)+'</div>'):'')
          +'<div class="ca-src">'+esc(r.src||'')+(r.date&&r.date!=='—'?(' · '+esc(r.date)):'')+evSup(si,r.ev)+'</div>'
          +'</div>'; }).join('')
      +'</div></div>'; }).join(''); }

/* ---------------------------------------------------------------------------
 * 分部模型章节 = 一条有编号的阅读动线（★2026-07-25 第二轮反馈：原来"东一块西一块"，
 * 不知从哪看起、也不知何时结束）。每段固定顺序：
 *   ① 怎么建模 → ② 驱动链算账 → ③ 口径取舍 → ④ 模型表 → ⑤ 量价锚图 → ⑥ 分部估值 → ✓ 小结
 * 缺失步骤自动跳过并重排编号；顶部「阅读顺序」条可跳转；末尾小结卡明确"到此结束 → 下一段"。
 * 原句一律走浮层（evpop），不再在正文里展开——避免版面被原文撑长。
 * ------------------------------------------------------------------------ */
function stepHTML(si,k,title,hint,body,fbk){
  return '<section class="sm-step" id="seg'+si+'-s'+k+'"'+(fbk?(' data-fbk="'+fbk+'"'):'')+'>'
    +'<div class="sm-step-hd"><span class="sm-step-n">'+k+'</span><b>'+esc(title)+'</b>'
      +(hint?('<span class="sm-step-hint">'+esc(hint)+'</span>'):'')+'</div>'
    +'<div class="sm-step-bd">'+body+'</div></section>'; }
// ★2026-08-12 编号改制：分部不再各占一个 3.x——3.3(无叙事映射时 3.2)＝「分部建模与计算」总节，
//   每个分部是它的孙级小节 3.3.1 / 3.3.2 / …；核心假设/加权估值固定 3.4/3.5（或 3.3/3.4），不再随分部数漂移。
function segSecNo(){ return nmActive()?'3.3':'3.2'; }
// 段内假设滑块（与 3.4 核心假设同一 data-path，改哪边都联动·由 bindRangeInputs 委托绑定）——
// 「核心模型表 + 修改的方式」必须在段内自足，不能只把读者赶去假设区。
function segAnchorSets(s){ var md=s.model||{};
  return { qA:[{label:'历史3yCAGR',v:cagr((s.hist&&s.hist.q)||[],3)}].concat(md.q_anchors||[]),
           pA:[{label:'历史3yCAGR',v:cagr((s.hist&&s.hist.p)||[],3)}].concat(md.p_anchors||[]),
           gA:[{label:'历史均值',v:(function(g){var f=(g||[]).filter(isFinite);return f.length?f.reduce(function(x,y){return x+y;},0)/f.length:null;})(s.hist&&s.hist.gm)}].concat(md.gm_anchors||[]) }; }
function segInlineKnobs(s,si,isCore){ var a=s.assume||{}; var fy=MODEL.forecast_years||[]; var derived=!!s.derive;
  if(!fy.length) return '';
  var an=segAnchorSets(s); var g='';
  fy.forEach(function(y,i){
    if(!derived) g+=knobRange('segments.'+si+'.assume.q_growth.'+i, y+' 量增速',(a.q_growth&&a.q_growth[i])||0,-0.3,0.6,0.01,function(v){return spct(v,0);},an.qA);
    g+=knobRange('segments.'+si+'.assume.p_growth.'+i, y+' 价增速',(a.p_growth&&a.p_growth[i])||0,-0.3,0.5,0.01,function(v){return spct(v,0);},an.pA);
    g+=knobRange('segments.'+si+'.assume.gm.'+i, y+' 毛利率',(a.gm&&a.gm[i])||0,0,0.8,0.005,function(v){return pct(v,1);},an.gA);
  });
  return '<details class="seg-edit"'+(isCore?' open':'')+'><summary>✎ 改本段假设（'+(derived?'价/毛利率':'量/价/毛利率')
    +' · 与「核心假设」区同一份数据，改哪边都联动）</summary>'
    +'<div class="knob-grid" data-fbk="part3.segments['+si+'].assume">'+g+'</div></details>'; }
function renderSegmentModels(){ var host=el('seg-models'); if(!host) return;
  var pl=EONE.recomputePL(MODEL);
  var segs=MODEL.segments||[];
  if(!segs.length){ host.innerHTML='<h2 id="sec-segs">'+segSecNo()+' 分部建模与计算</h2><div class="datagap">⚠️ part3.segments 为空——分部模型整章缺失，CK-3 不过（最大分部的模型表与可调假设是必选交付）。</div>'; return; }
  var coreCnt=segs.filter(function(s){return ((s.model||{}).driver_focus||{}).strength==='core';}).length;
  var secHd='<h2 id="sec-segs">'+segSecNo()+' 分部建模与计算（每分部一小节：方法→驱动→口径→模型表→锚→估值）</h2>'
    +(coreCnt!==1?('<div class="datagap">⚠️ driver_focus 为 core 的分部数＝'+coreCnt+'（规范要求全模型有且只有 1 段 core）。</div>'):'');
  EVIX={}; EVLIST={}; segs.forEach(function(s,si){ evRegister(si,(s.model||{}).evidence); });
  host.innerHTML=secHd+segs.map(function(s,si){ var md=s.model||{}; var sv=md.seg_val||{}; var eseg=pl.seg[si]||{};
    var realQP=segRealQP(s); var isCore=(md.driver_focus||{}).strength==='core';
    var steps=[], k=0;                                  // 逐段收集实际存在的步骤(编号连续)
    k++; steps.push({n:k,label:'怎么建模',html:stepHTML(si,k,'怎么建模：量价的物理定义 + 驱动逻辑','先看清 Q/P 各是什么物理量、收入怎么勾稽出来',
        (md.q_def?('<div><b>量(Q)：</b>'+esc(md.q_def)+evSup(si,md.q_ev)+'</div>'):'')
        +(md.p_def?('<div><b>价(P)：</b>'+esc(md.p_def)+evSup(si,md.p_ev)+'</div>'):'')
        +(md.logic?('<div class="sm-logic" data-fbk="part3.segments['+si+'].model.logic">'+md.logic+'</div>'):'')
        +(md.assets_note?('<div class="sm-assets"><b>资产/产能注记：</b>'+esc(md.assets_note)+'</div>'):'')
        +'<div class="sm-mini">勾稽：收入 = Q × P × factor（自校准 '+(isFinite(eseg.factor)?(Math.round(eseg.factor*1000)/1000):'—')+'＝历史年 rev/(Q·P) 均值）→ 毛利 = 收入 × 分部毛利率</div>'
        +(realQP?'':'<div class="datagap">⚠️ 本分部未拆出物理量价（q=收入指数、p=1 兜底），仅收入外推——按规范最大分部必须有真实量价拆分。</div>')
        +(md.q_def||md.logic?'':'<div class="datagap">⚠️ 未生成细分建模说明（segments[].model：q_def/p_def/logic）</div>'))});
    var chain=drvChainHTML(si,md);
    if(chain){ k++; steps.push({n:k,label:'驱动链算账',html:stepHTML(si,k,'驱动链：从外部物理量算到本段收入','一步一个数，末行=确认收入（与模型表、3.1 利润表同源）',chain)}); }
    else if(isCore){ k++; steps.push({n:k,label:'驱动链(缺)',html:stepHTML(si,k,'驱动链','',
        '<div class="datagap">⚠️ 当下逻辑最强段缺 driver_chain（逐步算账链）——按规范 core 段必须把「外部物理量→收入」拆成可追的步骤。</div>')}); }
    var cal=calHTML(si,md);
    if(cal){ k++; steps.push({n:k,label:'口径取舍',html:stepHTML(si,k,'口径取舍：同一个数为什么有好几个值','采用哪层、为什么；弃用的口径也留表写明不能用的原因',cal)}); }
    k++; steps.push({n:k,label:'模型表',html:stepHTML(si,k,'次级模型表：量 / 价 / 收入 / 毛利率 逐年（表下就能改）',
        '灰底=历史实际 · 米底=预测（随假设滑块联动）· 黄底格=当下逻辑作用的参数×时点',
        '<div class="segtbl" id="segtbl-'+si+'"></div>'+segInlineKnobs(s,si,isCore),'part3.segments['+si+'].assume')});
    k++; steps.push({n:k,label:'量价锚图',html:stepHTML(si,k,'量价增速 vs 类比锚','实色柱=历史实际 · 淡色柱=预测假设 · 虚线=行业/大哥/卖方锚',
        '<div class="chart-wrap" style="height:225px"><canvas id="chart-segqp-'+si+'"></canvas></div>')});
    k++; steps.push({n:k,label:'分部估值',html:stepHTML(si,k,'分部估值：这一段值多少钱','与 SOTP 对应行逐一对齐（改假设会联动）',
        (sv.method?('<div><b>锚：</b>'+esc(sv.method)+'</div>'
          +'<div class="sm-val">稳态净利 '+yi(sv.profit_yi)+' 亿 × '+(sv.mult!=null?sv.mult:'—')+'x = <b>'+yi(sv.mcap_yi!=null?sv.mcap_yi:(num(sv.profit_yi)*num(sv.mult)))+' 亿</b></div>'
          +(sv.note?('<div class="muted small">'+esc(sv.note)+'</div>'):''))
          :'<span class="datagap">⚠️ 未生成分部估值（segments[].model.seg_val：method/profit_yi/mult/note）</span>')
        +(md.cite?cite(md.cite):''),'part3.segments['+si+'].model.seg_val')});
    var nextName=(segs[si+1]&&segs[si+1].name)||null;
    var evc=evChipsHTML(si,md);
    var evGap=(isCore&&!evc)?'<div class="datagap">⚠️ 当下逻辑最强段缺 evidence（RAG 原句）——量价/毛利率假设必须挂原文。</div>':'';
    var y0=(MODEL.forecast_years&&MODEL.forecast_years[0])||'首预测年';
    var end='<div class="seg-end" data-fbk="part3.segments['+si+'].model.driver_focus">'
      +'<div class="se-hd">✓ 本段到此结束 · 小结</div>'
      +'<div class="se-line"><b>算出来什么：</b>'+esc(y0)+' 收入 <b data-segsum-rev="'+si+'">—</b> 亿'
        +'（YoY <span data-segsum-yoy="'+si+'">—</span>），分部估值 <b data-segsum-val="'+si+'">'
        +yi(sv.mcap_yi!=null?sv.mcap_yi:(num(sv.profit_yi)*num(sv.mult)))+'</b> 亿</div>'
      +((md.driver_focus||{}).verify?('<div class="se-line"><b>往后盯什么：</b>'+esc(md.driver_focus.verify)+'</div>'):'')
      +(md.fragile?('<div class="se-line se-weak"><b>最脆的一格：</b>'+esc(md.fragile)+'</div>'):'')
      +evc+evGap
      +'<div class="se-next">'+(nextName?('→ 下一段：'+esc(nextName)):'→ 分部全部看完，进入下一节：核心假设（拖动即时重算）')+'</div>'
      +'</div>';
    var rp='<div class="readpath"><span class="rp-lead">阅读顺序</span>'
      +steps.map(function(st){ return '<a class="rp-chip" href="#seg'+si+'-s'+st.n+'"><i>'+st.n+'</i>'+esc(st.label)+'</a>'; }).join('<span class="rp-arr">›</span>')
      +'<span class="rp-arr">›</span><span class="rp-chip rp-end"><i>✓</i>小结</span></div>';
    return '<h3 class="seg-h3" id="sec-seg-'+si+'">'+segSecNo()+'.'+(si+1)+' '+esc(s.name)+drvBadge(md)+'</h3>'
      +'<div class="panel seg-model'+(isCore?' seg-core':'')+'" data-fbk="part3.segments['+si+']">'
      +rp+steps.map(function(st){return st.html;}).join('')+end+'</div>';
  }).join('');
  renderSegTables(pl); renderSegQPCharts(pl); setupEvidence();
}
// 事件：chip/[Ex] → 浮层；浮层内翻页/复制/关闭；Esc 关、←/→ 翻页
function setupEvidence(){
  if(document.__evBound) return; document.__evBound=1;
  document.addEventListener('click',function(e){
    var cp=e.target.closest('button[data-cp]');
    if(cp){ copyText(cp.getAttribute('data-cp')); toast('已复制'+(cp.getAttribute('data-cpwhat')||'内容')); return; }
    var nav=e.target.closest('button[data-evnav]');
    if(nav){ evNav(+nav.getAttribute('data-evnav')); return; }
    if(e.target.closest('[data-evclose]')){ closeEvPop(); return; }
    var trig=e.target.closest('.ev-chip,sup.evc');
    if(trig){ var k=trig.getAttribute('data-evid')||trig.getAttribute('data-ev');
      if(!EVIX[k]){ toast('该证据未登记（model.evidence 里补 id='+String(k).split('::')[1]+'）'); return; }
      openEvPop(k); return; }
    var pop=el('evpop');
    if(pop&&pop.style.display==='block'&&!e.target.closest('#evpop')) closeEvPop();
  });
  document.addEventListener('keydown',function(e){ if(!EV_OPEN) return;
    if(e.key==='Escape') closeEvPop();
    else if(e.key==='ArrowLeft') evNav(-1);
    else if(e.key==='ArrowRight') evNav(1); });
}
function cssq(s){ return String(s).replace(/"/g,'\\"'); }
function copyText(t){ try{ if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(t); return; } }catch(_){}
  var ta=document.createElement('textarea'); ta.value=t; ta.style.position='fixed'; ta.style.opacity='0';
  document.body.appendChild(ta); ta.select(); try{document.execCommand('copy');}catch(_){} document.body.removeChild(ta); }
function toast(msg,ms){ var t=el('fb-toast'); if(!t){ return; } t.textContent=msg; t.style.display='block';
  clearTimeout(toast._t); toast._t=setTimeout(function(){ t.style.display='none'; }, ms||1900); }
function renderSegQPCharts(pl){ var p=PAL(); var segs=MODEL.segments||[]; var H=pl.H;
  segs.forEach(function(s,si){ if(!el('chart-segqp-'+si)) return;
    var md=s.model||{}; var a=s.assume||{}; var realQP=segRealQP(s);
    var qg=segGrowth((s.hist&&s.hist.q)||[]).slice(0,H), pg=segGrowth((s.hist&&s.hist.p)||[]).slice(0,H);
    var F=(MODEL.forecast_years||[]).length;
    for(var i=0;i<F;i++){ qg.push((a.q_growth&&a.q_growth[Math.min(i,(a.q_growth.length||1)-1)])||0);
      pg.push((a.p_growth&&a.p_growth[Math.min(i,(a.p_growth.length||1)-1)])||0); }
    var colQ=function(v,i){ return i<H?p.s[0]:p.s[0]+'66'; }, colP=function(v,i){ return i<H?p.s[3]:p.s[3]+'66'; };
    var ds=[{type:'bar',label:realQP?'量增速':'收入增速(量价未拆)',data:qg.map(function(v){return v==null?null:Math.round(v*1000)/10;}),
             backgroundColor:qg.map(colQ),borderWidth:0}];
    if(realQP) ds.push({type:'bar',label:'价增速',data:pg.map(function(v){return v==null?null:Math.round(v*1000)/10;}),
             backgroundColor:pg.map(colP),borderWidth:0});
    var anchors=[].concat((md.q_anchors||[]).map(function(x){return Object.assign({m:'量'},x);}),
                          realQP?(md.p_anchors||[]).map(function(x){return Object.assign({m:'价'},x);}):[]).slice(0,4);
    anchors.forEach(function(an,ai){ ds.push({type:'line',label:'锚·'+an.m+'·'+an.label+' '+spct(an.v,0),
      data:pl.years.map(function(){return Math.round(an.v*1000)/10;}),
      borderColor:[p.s[2],p.s[4],p.s[5],p.s[6]][ai%4],borderWidth:1.4,borderDash:[6,4],pointRadius:0,tension:0}); });
    mkChart('chart-segqp-'+si,{ data:{labels:pl.years,datasets:ds},
      options:{ maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
        plugins:{ legend:legPts(), tooltip:Object.assign(TT(),{displayColors:true,callbacks:{label:function(c){return c.dataset.label+': '+spct(c.raw/100);}}}) },
        scales:{ x:{grid:{display:false},ticks:{color:p.muted}}, y:{grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'%';}}} } } });
  });
}
// Part3 编号（★2026-08-12 固定制）：3.1 利润表 → [3.2 叙事↔分部映射(有则)] →
//   3.3 分部建模与计算（分部为孙级 3.3.1..3.3.N）→ 3.4 核心假设 → 3.5 加权估值。
//   无叙事映射时整体前移一位（3.2 分部建模…3.3 假设…3.4 估值）。编号不再随分部数漂移。
function renumberPart3(){ var segs=MODEL.segments||[]; var NB=NBASE();
  var SS=segSecNo();                                  // '3.3' or '3.2'
  var AS=nmActive()?'3.4':'3.3', VA=nmActive()?'3.5':'3.4';
  var hA=el('sec-assume'), hV=el('sec-val');
  if(hA) hA.textContent=AS+' 核心假设（拖动即时重算 · 含类比锚）';
  if(hV) hV.textContent=VA+' 多范式加权估值（按五档估值等级排列）';
  // 章级阅读动线（用户反馈：不知道从哪开始看、看到哪算结束）
  var ph=el('p3-path');
  if(ph){ var items=[['3.1 全公司利润表','#sec-pl']];
    if(nmActive()) items.push(['3.2 叙事↔分部','#sec-nmap']);
    items.push([SS+' 分部建模与计算','#sec-segs']);
    segs.forEach(function(s,si){ items.push([SS+'.'+(si+1)+' '+(s.name.length>8?s.name.slice(0,8)+'…':s.name)
      +(((s.model||{}).driver_focus||{}).strength==='core'?' ★':''),'#sec-seg-'+si]); });
    items.push([AS+' 核心假设(可调)','#sec-assume']);
    items.push([VA+' 加权估值 = 终点','#sec-val']);
    ph.innerHTML='<span class="rp-lead">本章怎么读</span>'
      +items.map(function(x,ix){ return '<a class="rp-chip'+(ix===items.length-1?' rp-end':'')+'" href="'+x[1]+'"><i>'+(ix+1)+'</i>'+esc(x[0])+'</a>'; }).join('<span class="rp-arr">›</span>')
      +'<div class="rp-note">先看 3.1 的总账 → 进 '+SS+' 逐小节看分部（每段内部也有 1→6 的顺序条，模型表下可直接改假设）→ 或回 '+AS+' 集中改参数 → 落到 '+VA+' 加权估值收口。</div>'; }
  var toc=document.getElementById('toc'); if(!toc) return;
  var aAs=toc.querySelector('a[href="#sec-assume"]'), aVal=toc.querySelector('a[href="#sec-val"]');
  if(aAs) aAs.textContent=AS+' 核心假设(可调·带锚)';
  if(aVal) aVal.textContent=VA+' 加权估值(五档等级排列)';
  [].slice.call(toc.querySelectorAll('a[data-seg],a[data-nmap],a[data-segs]')).forEach(function(n){n.parentNode.removeChild(n);});
  if(nmActive()&&aAs){ var an=document.createElement('a'); an.className='l2'; an.setAttribute('data-nmap','1');
    an.href='#sec-nmap'; an.textContent='3.2 叙事↔分部映射'; toc.insertBefore(an,aAs); }
  if(aAs){ var hd=document.createElement('a'); hd.className='l2'; hd.setAttribute('data-segs','1');
    hd.href='#sec-segs'; hd.textContent=SS+' 分部建模与计算'; toc.insertBefore(hd,aAs); }
  segs.forEach(function(s,si){ var a=document.createElement('a'); a.className='l3'; a.setAttribute('data-seg',si);
    var core=((s.model||{}).driver_focus||{}).strength==='core';
    a.href='#sec-seg-'+si; a.textContent=SS+'.'+(si+1)+' '+(core?'★':'')+(s.name.length>9?s.name.slice(0,9)+'…':s.name);
    if(aAs) toc.insertBefore(a,aAs); });
}

// ---- assumption knobs ------------------------------------------------------
function knobRange(path,label,val,min,max,step,disp,anchors){
  /* ★ 量程自适应（2026-07-31 长鑫 688825 实测修复）：假设值或类比锚落在写死量程之外时按实际值撑开。
     不修则滑块把手贴边 —— 标签显示 +233% 但把手停在 +50% 上，用户一碰就把模型静默改成边界值。
     超高增速/高毛利标的（存储超级周期、涨价链、扭亏股）必踩，属静默失效。 */
  var _vs=[+val].concat((anchors||[]).map(function(a){return (a&&isFinite(a.v))?+a.v:NaN;})).filter(isFinite);
  if(_vs.length){
    var _lo=Math.min.apply(null,_vs), _hi=Math.max.apply(null,_vs), _rate=(max<=1&&min>=-1);
    if(_lo<min){ min=_lo-Math.max(Math.abs(_lo)*0.15,0.05); if(_rate&&_lo>=0&&min<0) min=0; }
    if(_hi>max){ max=_hi+Math.max(Math.abs(_hi)*0.15,0.05); if(_rate&&_hi<=1&&max>0.99) max=0.99; }
    if((max-min)/step>400) step=Math.round((max-min)/200*1000)/1000;
  }
  var ticks=(anchors||[]).filter(function(a){return a&&isFinite(a.v);}).map(function(a){
    var lp=Math.max(0,Math.min(100,(a.v-min)/(max-min)*100));
    return '<span class="atick" style="left:'+(Math.round(lp*10)/10)+'%" title="'+esc(a.label+' '+disp(a.v))+'"></span>'; }).join('');
  return '<div class="knob"><label title="'+esc(label)+'">'+esc(label)+'</label>'+
    '<span class="rng"><input type="range" min="'+min+'" max="'+max+'" step="'+step+'" value="'+val+'" data-path="'+path+'">'+ticks+'</span>'+
    '<span class="kv" data-kv="'+path+'">'+disp(val)+'</span></div>';
}
function anchorLegend(tag,anchors,disp){ var xs=(anchors||[]).filter(function(a){return a&&isFinite(a.v);}); disp=disp||function(v){return spct(v,0);};
  if(!xs.length) return ''; return '<span class="a-leg"><b>'+tag+'锚</b> '+xs.map(function(a){return esc(a.label)+' '+disp(a.v);}).join(' · ')+'</span>'; }
/* ---- ★ 单点最大假设：母段拆分比例 λ（可调滑块，联动收入/毛利/估值）-------- */
function renderSplitKnobs(){ var sp=MODEL.splits||{}; var ks=Object.keys(sp); if(!ks.length) return '';
  var fy=MODEL.forecast_years||[]; var hy=MODEL.hist_years||[];
  return ks.map(function(k){ var s=sp[k];
    var anchors=(s.anchors||[]).concat([{label:'2025 实际(推导)',v:(s.share_hist||[]).slice(-1)[0]}]);
    var hist='<div class="a-legend"><b>历史 λ（锁定·研究者推导非披露）</b> '
      +hy.map(function(y,i){ return esc(y)+' '+pct(num((s.share_hist||[])[i]),0); }).join(' · ')+'</div>';
    return '<div class="subhd lam-hd">★ '+esc(s.label||('拆分比例 '+k))+'　<span class="lam-warn">全链最大单点假设 · 公司未单独披露</span></div>'
      +(s.note?('<div class="callout lam-note">'+s.note+'</div>'):'')+hist
      +'<div class="knob-grid" data-fbk="part3.splits.'+k+'.share">'
      +fy.map(function(y,i){ return knobRange('splits.'+k+'.share.'+i, y+' '+(s.short||'λ'),
          num((s.share||[])[i]), 0, 0.95, 0.01, function(v){return pct(v,0);}, anchors); }).join('')
      +'</div><div id="lam-out" class="lam-out"></div>'; }).join('');
}
function renderLamOut(pl){ var host=el('lam-out'); if(!host||!pl) return;
  var sp=MODEL.splits||{}; var k=Object.keys(sp)[0]; if(!k) return;
  var par=(pl.parents||[]).filter(function(x){return x.key===k;})[0]; if(!par) return;
  var segs=MODEL.segments||[], H=pl.H;
  var ci=-1,ri=-1; segs.forEach(function(s,i){ if((s.derive||{}).parent!==k)return;
    if((s.derive||{}).take==='residual') ri=i; else ci=i; });
  var cells=(MODEL.forecast_years||[]).map(function(y,i){ var t=H+i;
    var lc=ci>=0?num(pl.seg[ci].rev[t]):0, ar=ri>=0?num(pl.seg[ri].rev[t]):0;
    var q=ci>=0?num(pl.seg[ci].q[t]):0, p=ci>=0?num(pl.seg[ci].p[t]):0;
    var chk=lc?Math.abs(q*p*num(pl.seg[ci].factor,1)-lc)/lc:0;
    return '<span class="lamc"><b>'+esc(y)+'</b> 液冷 '+yi(lc)+'亿 ／ 非液冷 '+yi(ar)+'亿'
      +'<i>量 '+Math.round(q)+' MW × 价 '+Math.round(p)+' 元/kW ＝ '+yi(lc)+'亿（对账差 '+(Math.round(chk*10000)/100)+'%）</i></span>'; }).join('');
  host.innerHTML='<div class="lam-out-hd">拖动后即时结果（母段合计不变，只在两段之间移动）</div>'+cells;
}
function renderAssumptions(){ var html=renderSplitKnobs(); var PARDONE={};
  (MODEL.segments||[]).forEach(function(s,si){ var a=s.assume||{}; var fy=MODEL.forecast_years||[]; var md=s.model||{};
    // 类比锚：自动历史3yCAGR + model 提供的行业/大哥/卖方锚（与段内滑块共用 segAnchorSets）
    var an0=segAnchorSets(s), qA=an0.qA, pA=an0.pA, gA=an0.gA;
    // 母段驱动（合计量价）排在它的第一个子段前面：先定盘子，再定 λ 怎么分
    var pk=(s.derive||{}).parent;
    if(pk&&PARDONE[pk]==null){ PARDONE[pk]=1;
      var pi=-1,pn=null; (MODEL.parents||[]).forEach(function(x,ix){ if(x.key===pk){pi=ix;pn=x;} });
      if(pn){ var pa=pn.assume||{};
        html+='<div class="subhd">'+esc(pn.name)+'　<span class="muted small">（母段：决定盘子多大，λ 决定怎么分）</span></div>'
          +'<div class="knob-grid" data-fbk="part3.parents['+pi+'].assume">'
          +fy.map(function(y,i){ return knobRange('parents.'+pi+'.assume.q_growth.'+i, y+' 合计量增速',(pa.q_growth&&pa.q_growth[i])||0,-0.3,0.6,0.01,function(v){return spct(v,0);},pn.q_anchors)
            +knobRange('parents.'+pi+'.assume.p_growth.'+i, y+' 合计价增速',(pa.p_growth&&pa.p_growth[i])||0,-0.3,0.5,0.01,function(v){return spct(v,0);},pn.p_anchors); }).join('')
          +'</div>'; } }
    var derived=!!s.derive;
    html+='<div class="subhd">'+esc(s.name)+(derived?'　<span class="muted small">（量＝收入÷价，是结果不是驱动；此处只调价与毛利率）</span>':'')+'</div>'
        +'<div class="a-legend">'+(derived?'':anchorLegend('量',qA))+anchorLegend('价',pA)+anchorLegend('毛利率',gA,function(v){return pct(v,0);})+'<span class="muted small">（滑轨上 ▲ 刻度即锚位；毛利率锚为水平值非增速）</span></div>'
        +'<div class="knob-grid" data-fbk="part3.segments['+si+'].assume">';
    fy.forEach(function(y,i){
      if(!derived) html+=knobRange('segments.'+si+'.assume.q_growth.'+i, y+' 量增速', (a.q_growth&&a.q_growth[i])||0, -0.3,0.6,0.01, function(v){return spct(v,0);}, qA);
      html+=knobRange('segments.'+si+'.assume.p_growth.'+i, y+' 价增速', (a.p_growth&&a.p_growth[i])||0, -0.3,0.5,0.01, function(v){return spct(v,0);}, pA);
      html+=knobRange('segments.'+si+'.assume.gm.'+i, y+' 毛利率', (a.gm&&a.gm[i])||0, 0,0.8,0.005, function(v){return pct(v,1);}, gA);
    });
    html+='</div>';
  });
  // 境外收入占比：不是独立收入项，而是通过「境外 vs 境内毛利率差」作用到目标分部的毛利率
  var ob=MODEL.overseas_bridge;
  if(ob&&ob.ov_share){ var ofy=MODEL.forecast_years||[];
    html+='<div class="subhd">境外收入占比（→ 经毛利率差作用到 '+esc(ob.target_name||ob.target_seg)+'）</div>'
      +(ob.note?('<div class="callout lam-note">'+ob.note+'</div>'):'')
      +'<div class="knob-grid" data-fbk="part3.overseas_bridge.ov_share">'
      +ofy.map(function(y,i){ return knobRange('overseas_bridge.ov_share.'+i, y+' 境外占比',
          num(ob.ov_share[i]),0,0.8,0.01,function(v){return pct(v,0);},
          [{label:'2025 实际',v:num(ob.ov_share_2025,0.14)}]); }).join('')
      +'</div>'; }
  var op=MODEL.opex||{};
  if(op.impair){ var ify=MODEL.forecast_years||[];
    html+='<div class="subhd">信用及资产减值（亿元／年）'
      +'<span class="muted small">　26Q1 已计提 3,016 万元、同比 +3 倍；应收账款 30.6亿＝TTM 收入 48%</span></div>'
      +'<div class="knob-grid" data-fbk="part3.opex.impair">'
      +ify.map(function(y,i){ return knobRange('opex.impair.'+i, y+' 减值', num(op.impair[i]),0,4,0.05,
          function(v){return (Math.round(v*100)/100).toFixed(2)+'亿';},
          [{label:'26Q1×4 年化',v:1.21}]); }).join('')+'</div>'; }
  var reg=op.sga_reg;
  html+='<div class="subhd">费用与税（预测期）'+(reg?'　<span class="muted small">销售+管理走六年回归，不是手填费率</span>':'')+'</div><div class="knob-grid">';
  if(reg){
    html+=knobRange('opex.sga_reg.fc','销管·固定费用(亿)',num(reg.fc),0,4,0.01,function(v){return (Math.round(v*100)/100).toFixed(2)+'亿';},
      [{label:'2020–25 回归',v:1.3588}]);
    html+=knobRange('opex.sga_reg.vc','销管·变动费率(×营收)',num(reg.vc),0,0.15,0.0001,function(v){return pct(v,2);},
      [{label:'2020–25 回归',v:0.059064}]);
  } else html+=knobRange('opex.sga_rate.0','销售费用率',(op.sga_rate&&op.sga_rate[0])||0,0,0.3,0.005,function(v){return pct(v);});
  html+=knobRange('opex.rnd_rate.0','研发费用率',(op.rnd_rate&&op.rnd_rate[0])||0,0,0.3,0.005,function(v){return pct(v);});
  html+=knobRange('opex.tax_rate.0','所得税率',(op.tax_rate&&op.tax_rate[0])||0,0,0.4,0.005,function(v){return pct(v);});
  html+='</div>';
  el('assumptions').innerHTML=html;
}
/* ★委托绑定（2026-08-12）：假设滑块现在出现在两处——3.4 核心假设区 + 3.3.x 段内「模型表下就能改」。
   统一在 document 层监听 input[data-path]，同 path 的镜像滑块与读数一起同步：改哪边都联动、只 recompute 一次。 */
function bindRangeInputs(){ if(document.__rangeBound) return; document.__rangeBound=1;
  document.addEventListener('input',function(e){ var inp=e.target;
    if(!inp||inp.tagName!=='INPUT'||inp.type!=='range'||!inp.dataset||!inp.dataset.path) return;
    var pth=inp.dataset.path, v=parseFloat(inp.value);
    setPath(MODEL,pth,v);
    if(pth.indexOf('overseas_bridge')===0) applyOverseasBridge();
    [].slice.call(document.querySelectorAll('input[data-path]')).forEach(function(o){ if(o!==inp&&o.dataset.path===pth) o.value=v; });
    [].slice.call(document.querySelectorAll('[data-kv]')).forEach(function(kv){ if(kv.getAttribute('data-kv')===pth) kv.textContent=knobDisp(pth,v); });
    recompute(); });
}
// 滑块读数格式：按路径判类型（比例/费率/金额/增速）
function knobDisp(pth,v){
  if(/sga_reg\.fc|opex\.impair/.test(pth)) return (Math.round(v*100)/100).toFixed(2)+'亿';
  if(/sga_reg\.vc/.test(pth)) return pct(v,2);
  if(/splits\..*\.share|overseas_bridge\.ov_share/.test(pth)) return pct(v,0);
  if(pth.indexOf('gm')>=0||pth.indexOf('_rate')>=0) return pct(v);
  return spct(v,0);
}
function setPath(obj,path,val){ var ks=path.split('.'),o=obj; for(var i=0;i<ks.length-1;i++){ var k=ks[i]; if(o[k]==null)o[k]=/^\d+$/.test(ks[i+1])?[]:{}; o=o[k]; } o[ks[ks.length-1]]=val; }
function getPath(obj,path){ return path.split('.').reduce(function(o,k){return o==null?undefined:o[k];},obj); }

/* ===========================================================================
 * PART 3.3 valuation
 * ======================================================================== */
function voutHTML(r,p){ return '隐含市值 <b style="color:'+(r.diagnostic?p.muted:p.accent)+'">'+yi(r.mcap)+'</b> 亿 · 目标 '+(Math.round(r.target*100)/100)+' 元 · 赔率 <b style="color:'+(r.odds>=0?p.good:p.bad)+'">'+spct(r.odds)+'</b>'; }
// light=true: 只更新 hero/横条/卡片读数,不重建卡片 DOM——权重滑块拖动中调用(重建会掐断拖动、numbox 失焦)
/* ★五档估值等级系统（2026-08-12 用户口径固化，详见 05 §0.5）：
   第一档 景气最差/亏损 → PB·重置成本·合理利润率×PE ｜ 第二档 静态/Forward PE（含 EV/EBITDA）
   第三档 PEG / N+1 PE ｜ 第四档 PS(高利润假设×PE)/单位利润法/N+2 PE（含 SOTP 混合锚）
   第五档 TAM终局法/五年规划法/对标大哥法。升档赔率：二 20–50% / 三 30–50% / 四 50–100% / 五 100–300%。
   估值卡与横条一律按 第一档→第五档 排（可验证 → 叙事），implied 诊断腿殿后。 */
var TIER_INFO=[null,
  {n:'第一档',hint:'景气最差·当期亏损·重置成本思维',fam:'PB / 合理利润率×PE / 单位市值法',odds:'—',c:'#616a76'},
  {n:'第二档',hint:'景气一般，静态估值；或利润爆发但预期不可持续',fam:'静态 / Forward PE · EV/EBITDA',odds:'20–50%',c:'#2a78d6'},
  {n:'第三档',hint:'景气较好·增速 20–40%·拔静态估值',fam:'PEG / N+1 PE',odds:'30–50%',c:'#1D9E75'},
  {n:'第四档',hint:'增速 40%+ 空间大·缺当期业绩·经营杠杆高',fam:'PS(高利润假设×PE) / 单位利润法 / N+2 PE · SOTP',odds:'50–100%',c:'#BA7517'},
  {n:'第五档',hint:'故事大·叙事 FOMO·催化点燃情绪',fam:'TAM终局 / 五年规划 / 对标大哥',odds:'100–300%',c:'#8a2be2'}];
function tierOf(pd){ if(!pd) return 3; var k=pd.key, ps=pd.params||{};
  if(k==='pbroe') return 1;
  if(k==='implied') return 1;                          // 合理利润率×PE 反推＝第一档族（且诊断殿后）
  if(k==='pe') return (num(ps.year_offset,99)>=2&&num(ps.year_offset,99)<90)?4:2;  // N+2 PE 升第四档
  if(k==='evebitda') return 2;
  if(k==='peg') return 3;
  if(k==='sotp') return 4;
  if(k==='leader'||k==='endgame') return 5;
  return 3; }
function tierBadge(t){ var ti=TIER_INFO[t]; if(!ti) return '';
  return '<span class="tier-badge" style="border-color:'+ti.c+';color:'+ti.c+'" title="'+esc(ti.hint+' · 范式族：'+ti.fam+' · 升档赔率 '+ti.odds)+'">'+ti.n+'</span>'; }
function renderTierStrip(res,v){ var host=el('val-tier-strip'); if(!host) return;
  var wmax=-1, curT=null;
  (v.paradigms||[]).forEach(function(pd,i){ var r=(res.rows||[])[i]||{}; if(r.diagnostic) return;
    if(num(pd.weight)>wmax){ wmax=num(pd.weight); curT=tierOf(pd); } });
  host.innerHTML='<div class="tier-strip">'+TIER_INFO.slice(1).map(function(ti,ix){ var t=ix+1;
    return '<div class="tier-cell'+(curT===t?' cur':'')+'" style="border-top-color:'+ti.c+'">'
      +'<b style="color:'+ti.c+'">'+ti.n+'</b>'+(curT===t?'<span class="tier-cur">当前主锚</span>':'')
      +'<span class="tier-fam">'+esc(ti.fam)+'</span>'
      +'<span class="tier-hint">'+esc(ti.hint)+'</span>'
      +'<span class="tier-odds">升档赔率 '+esc(ti.odds)+'</span></div>'; }).join('')
    +'</div><div class="cap" style="margin:2px 0 8px">五档＝随景气度/叙事强度升档的定价范式阶梯；下方估值卡按 第一档→第五档 排列（越靠下越靠叙事，前提越强、证伪回撤越快）。折现率统一 8–10%。</div>'; }
/* ★权重显示口径（2026-08-17 石英股份读者反馈「彼此的权重需要有影响啊，加权的权重=1」）：
   引擎里加权一直是归一的（wnorm=weight/Σweight），但卡片印的是滑块原始值 8%、13%…，Σ 不等于 100%，
   而且拖一根滑块别的卡片纹丝不动——读者当然以为权重彼此独立。现在卡片印**有效权重**（已归一，Σ=100%），
   括号里给滑块原始值；拖任一根，全部卡片同步重算。05 §加权 同步。 */
function wLabel(r){ var wn=isFinite(r.wnorm)?r.wnorm:0; var raw=num(r.weight);
  return Math.round(wn*100)+'%'+(Math.abs(wn-raw)>0.005?('<span class="muted" style="font-weight:400"> (滑块 '+Math.round(raw*100)+'%)</span>'):''); }
function renderValuation(pl,light){ var v=MODEL.valuation||{}; var res=EONE.runValuation(v,pl); var p=PAL();
  // blend hero
  var vd=res.range.verdict;
  el('valuation-blend').innerHTML=
    '<div><div class="stat" style="border:none;background:transparent;padding:0"><div class="k">加权目标市值</div><div class="v" style="color:var(--accent)">'+yi(res.blend.mcap)+' 亿</div></div></div>'+
    '<div class="stat" style="background:transparent;border:none;padding:0"><div class="k">目标价</div><div class="v">'+(res.shares?(Math.round(res.blend.target*100)/100):'—')+CURU()+'</div></div>'+
    '<div class="stat" style="background:transparent;border:none;padding:0"><div class="k">赔率(目标/当前−1)</div><div class="v '+(res.blend.odds>=0?'pos':'neg')+'">'+spct(res.blend.odds)+'</div></div>'+
    '<div class="stat" style="background:transparent;border:none;padding:0"><div class="k">当前市值锚</div><div class="v">'+yi(res.currentMcap)+' 亿</div></div>'+
    '<div style="grid-column:1/-1"><div class="callout '+(vd.level==='ok'?'':vd.level)+'" style="margin:4px 0">区间 '+yi(res.range.min)+'–'+yi(res.range.max)+' 亿（中位 '+yi(res.range.median)+'）· '+esc(vd.text)+
    '<span class="muted"> · 权重已归一（有效权重 Σ=100%；拖任一根滑块，其余同步重算）</span></div></div>';
  // bars: implied mcap per paradigm vs current —— ★按五档等级排序（第一档→第五档），诊断腿殿后
  var ord=res.rows.map(function(r,ri){ return {r:r,ri:ri,t:tierOf((v.paradigms||[])[ri])}; })
    .sort(function(a,b){ return ((a.r.diagnostic?99:a.t)-(b.r.diagnostic?99:b.t)) || (num(b.r.weight)-num(a.r.weight)); });
  var TN=['','①','②','③','④','⑤'];
  var bars=ord.filter(function(x){return !x.r.diagnostic;});
  var cur=res.currentMcap;
  var curLine={ id:'curline', afterDraw:function(ch){ var xs=ch.scales.x,ys=ch.scales.y,a=ch.chartArea,ctx=ch.ctx;
    var x=xs.getPixelForValue(cur); ctx.save(); ctx.strokeStyle=p.bad; ctx.setLineDash([5,4]); ctx.lineWidth=1.5;
    ctx.beginPath(); ctx.moveTo(x,a.top); ctx.lineTo(x,a.bottom); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle=p.bad; ctx.font='10px system-ui'; ctx.textAlign='left'; ctx.fillText('当前 '+yi(cur)+'亿',x+3,a.top+10); ctx.restore(); } };
  mkChart('chart-valbars',{ type:'bar', data:{labels:bars.map(function(x){return TN[x.t]+' '+x.r.name+' ('+Math.round(x.r.wnorm*100||0)+'%)';}),
      datasets:[{label:'隐含市值(亿)',data:bars.map(function(x){return Math.round(x.r.mcap);}),
        backgroundColor:bars.map(function(x){return x.r.mcap>=cur?p.good:p.s[0];}),borderWidth:0,barPercentage:0.72}]},
    options:{ indexAxis:'y', maintainAspectRatio:false, plugins:{legend:{display:false},tooltip:Object.assign(TT(),{callbacks:{label:function(c){var x=bars[c.dataIndex];return [yi(x.r.mcap)+'亿 · 目标'+(Math.round(x.r.target*100)/100)+'元 · 赔率'+spct(x.r.odds)+' · '+(TIER_INFO[x.t]||{}).n];}}})},
      scales:{x:{grid:{color:p.grid},ticks:{color:p.muted,callback:function(v){return v+'亿';}}},y:{grid:{display:false},ticks:{color:p.fg,font:{size:11}}}} },
    plugins:[curLine] });
  if(light){ var host=el('cards-valuation');
    res.rows.forEach(function(r,ri){
      var vo=host.querySelector('[data-vout="'+ri+'"]'); if(vo) vo.innerHTML=voutHTML(r,p);
      var wd=host.querySelector('[data-w="'+ri+'"]'); if(wd) wd.innerHTML=wLabel(r);   // ★全部卡片同步刷新：一根滑块动，其余有效权重跟着重新归一
      var det=host.querySelector('[data-vd="'+ri+'"]'); if(det) det.textContent=r.detail; });
    return; }
  renderTierStrip(res,v);
  // paradigm cards with editable params + weight —— 卡序=五档等级；data-* 仍用原始 ri，light 局部刷新不受排序影响
  el('cards-valuation').innerHTML=ord.map(function(x){ var r=x.r, ri=x.ri, pd=v.paradigms[ri];
    var params=paramInputs(pd,ri);
    var ldr=''; if(pd.key==='leader'){ var ps=pd.params||{}; var lnm=ps.leader_name;
      ldr='<div class="leader-line'+(lnm?'':' missing')+'">对标大哥：<b>'+(lnm?esc(lnm):'⚠️ 未指明——必须点名是谁')+'</b> · 口径 '+((ps.basis==='profit'||ps.metric==='利润')?'利润':'收入')+'占比 → 市值占比</div>'; }
    return '<div class="val-card'+(r.diagnostic?' diag':'')+'" data-fbk="part3.valuation.paradigms['+ri+']" style="border-left-color:'+(r.diagnostic?p.muted:((TIER_INFO[x.t]||{}).c||p.accent))+'">'+
      '<h4><span>'+tierBadge(x.t)+esc(r.name)+'</span><span class="small">'+(r.diagnostic?'诊断':('有效权重 <b data-w="'+ri+'">'+wLabel(r)+'</b>'))+'</span></h4>'+ldr+
      (r.diagnostic?'':'<div class="knob" style="grid-template-columns:52px 1fr;margin:2px 0"><label>权重</label><input type="range" min="0" max="1" step="0.05" value="'+r.weight+'" data-wpath="'+ri+'"></div>')+
      '<div class="vout" data-vout="'+ri+'">'+voutHTML(r,p)+'</div>'+
      params+
      '<div class="vdetail" data-vd="'+ri+'">'+esc(r.detail)+'</div>'+
    '</div>'; }).join('');
  // wire weight sliders: 拖动中 light 局部更新(保住拖动), 松手 change 再整体重建
  el('cards-valuation').querySelectorAll('input[data-wpath]').forEach(function(inp){
    inp.addEventListener('input',function(){ v.paradigms[+inp.dataset.wpath].weight=parseFloat(inp.value);
      renderValuation(pl,true); });
    inp.addEventListener('change',function(){ renderValuation(pl); }); });
  // wire param number boxes: change(提交/失焦)才重算——input 每敲一字就重建会把输入框敲飞
  el('cards-valuation').querySelectorAll('input.numbox').forEach(function(inp){
    inp.addEventListener('change',function(){ var x=parseFloat(inp.value); if(!isFinite(x))return;
      setPath(v.paradigms[+inp.dataset.pi].params,inp.dataset.pp,x); recompute(); }); });
}
// render a compact whitelist of scalar params per paradigm as number boxes
var PARAM_LABEL={pe:'PE',r:'折现r',n:'年数N',g:'增速g%',peg:'PEG',mult:'倍数',net_cash_yi:'净现金',net_debt_yi:'净债务',
  leader_mcap:'大哥市值',leader_current:'大哥口径',follower_steady:'本司稳态',adj:'调整±',roe:'ROE',coe:'COE',
  equity_yi:'净资产',tam_yi:'TAM',share:'份额',net_margin:'净利率',pe_mid:'中枢PE',fwd_profit_yi:'Fwd净利',year_offset:'预测年序'};
function paramInputs(pd,ri){ var ps=pd.params||{}; var out=[];
  Object.keys(ps).forEach(function(k){ var val=ps[k];
    if(typeof val==='number' && PARAM_LABEL[k]!=null){
      out.push('<span style="display:inline-flex;align-items:center;gap:3px;margin:2px 6px 2px 0;font-size:11px"><span class="muted">'+PARAM_LABEL[k]+'</span><input class="numbox" data-pi="'+ri+'" data-pp="'+k+'" value="'+val+'"></span>');
    }
  });
  // SOTP segment mults
  if(pd.key==='sotp' && ps.segments){ ps.segments.forEach(function(s,si){
    out.push('<span style="display:inline-flex;align-items:center;gap:3px;margin:2px 6px 2px 0;font-size:11px"><span class="muted">'+esc(s.name)+'倍</span><input class="numbox" data-pi="'+ri+'" data-pp="segments.'+si+'.mult" value="'+s.mult+'"></span>');
  }); }
  return out.length?'<div style="margin:4px 0">'+out.join('')+'</div>':'';
}

/* ===========================================================================
 * references + citation popover + TOC scrollspy + theme
 * ======================================================================== */
function foldBox(title,html){
  // 反脚手架：方法论/口径不进正文流，收进默认折叠块（结论在页面上，"我怎么做的"点开才看）
  return '<details class="foldbox" style="margin-top:6px"><summary style="cursor:pointer;color:var(--muted);'+
    'font-size:12.5px;list-style:none;user-select:none">▸ '+esc(title)+'</summary>'+
    '<div class="small muted" style="margin-top:5px;line-height:1.65">'+html+'</div></details>';
}
function cite(n){ if(n==null)return ''; if(!Array.isArray(n))n=[n]; return n.map(function(x){return '<sup class="cite" data-n="'+x+'"><a>['+x+']</a></sup>';}).join(''); }
var REFS={};
function renderRefs(){ var refs=D.references||[];
  refs.forEach(function(r){ REFS[r.n]='<span class="pn">['+r.n+']</span>'+esc(r.text)+(r.tag?(' <span class="dtag '+r.tag+'">'+r.tag+'</span>'):''); });
  el('refs').innerHTML=refs.map(function(r){ return '<li><span class="ref-num" id="ref-'+r.n+'">['+r.n+']</span> '+esc(r.text)+(r.tag?(' <span class="dtag '+r.tag+'">'+r.tag+'</span>'):'')+'</li>'; }).join('');
  el('ref-intro').textContent='交互说明：点击正文 [n] 角标弹出来源卡；左侧目录可直达章节；Part 3 拖动滑块即时重算 P&L 与估值。数据标记 FACT(≥2源可验)/EST(测算或卖方)/DNA(判断)。';
}
function setupPopover(){ var pop=el('pop'),openFor=null;
  // 图上催化弹卡：点卡外 / 图外 / ESC 关闭（点图内标记由 chart.onClick 处理）
  document.addEventListener('click',function(e){ var cp=el('catpop'); if(!cp||cp.style.display!=='block')return;
    if(e.target.closest('#catpop'))return; if(e.target.closest('#chart-price'))return; closeCatPop(); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape') closeCatPop(); });
  function hide(){ pop.style.display='none'; openFor=null; }
  document.addEventListener('click',function(e){ var a=e.target.closest('sup.cite a');
    if(a){ e.preventDefault(); var n=a.closest('sup.cite').dataset.n; if(openFor===n){hide();return;}
      pop.innerHTML=(REFS[n]||'<span class="pn">['+n+']</span>未收录')+'<br><span class="goto" data-goto="'+n+'">↧ 跳到参考文献 ['+n+']</span>';
      pop.style.display='block'; var r=a.getBoundingClientRect();
      var x=window.scrollX+r.left, y=window.scrollY+r.bottom+6;
      pop.style.left=Math.min(x,window.scrollX+document.documentElement.clientWidth-pop.offsetWidth-16)+'px'; pop.style.top=y+'px'; openFor=n;
    } else if(e.target.dataset&&e.target.dataset.goto){ var g=e.target.dataset.goto; hide();
      var li=document.getElementById('ref-'+g); if(li){ li.scrollIntoView({behavior:'smooth',block:'center'}); var pli=li.closest('li'); if(pli){pli.classList.add('flash'); setTimeout(function(){pli.classList.remove('flash');},2200);} }
    } else if(!e.target.closest('#pop')) hide(); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape') hide(); });
}
function setupScrollspy(){ var links=[].slice.call(document.querySelectorAll('#toc a'));
  var byId={}; links.forEach(function(a){ byId[a.getAttribute('href').slice(1)]=a; });
  var obs=new IntersectionObserver(function(es){ es.forEach(function(en){ if(en.isIntersecting){ links.forEach(function(a){a.classList.remove('active');}); if(byId[en.target.id])byId[en.target.id].classList.add('active'); } }); },{rootMargin:'0px 0px -78% 0px'});
  Object.keys(byId).forEach(function(id){ var e=document.getElementById(id); if(e)obs.observe(e); });
}
function rebuildAllCharts(){ chartDefaults();
  renderRevenue(); renderHolders(); renderFactions(); renderDupont(); renderCost(); renderCashCapex(); renderConsensus(); renderChipAge(); renderNarrativeCapacity(); renderPrice();
  var pl=EONE.recomputePL(MODEL); renderPLCharts(pl); renderSegTables(pl); renderSegQPCharts(pl); renderValuation(pl); }
/* 打印时把折叠块全部展开——2.2 的详情区只渲选中段，纸面不能丢另外五段。
   纯 CSS 撬不开 <details>（未展开时内容在浏览器内部被隐藏），只能在 beforeprint 里改属性；
   打印结束再还原，不影响屏幕上的选中态。 */
function setupPrintExpand(){
  var opened=[];
  var open=function(){ opened=[]; document.querySelectorAll('details:not([open])').forEach(function(d){
      opened.push(d); d.setAttribute('open',''); }); };
  var close=function(){ opened.forEach(function(d){ d.removeAttribute('open'); }); opened=[]; };
  if(window.matchMedia){ var mq=window.matchMedia('print');
    if(mq.addEventListener) mq.addEventListener('change',function(e){ e.matches?open():close(); });
    else if(mq.addListener) mq.addListener(function(e){ e.matches?open():close(); }); }
  window.addEventListener('beforeprint',open);
  window.addEventListener('afterprint',close);
}

function setupTheme(){ var btn=el('themeBtn'); btn.addEventListener('click',function(){
  var cur=document.documentElement.getAttribute('data-theme');
  var dark=cur? cur==='dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme',dark?'light':'dark');
  setTimeout(rebuildAllCharts,30); }); }

// background-tab 0-width fix
function fixZero(){ var tries=0; (function loop(){ var broken=Object.values(Chart.instances||{}).filter(function(c){return !c.width;}); broken.forEach(function(c){c.resize();}); if(broken.length && ++tries<30) setTimeout(loop,400); })(); }

/* ============================================================================
 * 第四章 · 矛盾地图（references/09-contradiction-map.md）
 * 横轴=可证伪性 F  纵轴=分歧度 D  圆面积正比赔率(r=4.3√odds)  颜色=layer
 * 虚线圈=coverage:0(零覆盖)  浮窗=纯 CSS :hover（file:// 不跑 JS，禁用 JS 浮窗）
 * ========================================================================== */
var CMAP_LAYER={'叙事':'#8a6bbf','估值':'#47709e','收入':'#c2703d','利润率':'#5b7f4b','费用率':'#3f8486'};
function cmLayColor(l){ return CMAP_LAYER[l]||'#8c8474'; }
/* ★形状通道（09 §8a）：role='从动' 渲方块，其余渲圆。等面积边长 a=√π·r。
   面积仍严格正比赔率——形状只换轮廓，不动标度，所以 CK-6g 的面积闸不受影响。 */
var SQ_K=Math.sqrt(Math.PI);                       // ≈1.7725
function isPassive(it){ return (it&&it.role)==='从动'; }
function cmShape(q,c,fo,sw,dash){
  var common=' fill="'+c+'" fill-opacity="'+fo+'" stroke="'+c+'" stroke-width="'+sw+'"'+dash+'/>';
  if(!isPassive(q.it)) return '<circle cx="'+q.x+'" cy="'+q.y+'" r="'+q.r.toFixed(1)+'"'+common;
  var a=SQ_K*q.r;                                  // 等面积边长
  return '<rect class="qmark" x="'+(q.x-a/2).toFixed(1)+'" y="'+(q.y-a/2).toFixed(1)+
         '" width="'+a.toFixed(1)+'" height="'+a.toFixed(1)+'" rx="2"'+common;
}
function wrapCJK(s,n){ s=String(s==null?'':s); var out=[],i; for(i=0;i<s.length;i+=n) out.push(s.slice(i,i+n)); return out; }

/* 贪心避让：默认标签放圆下方，撞到圆或已放标签就依次试 上/右/左 */
function placeLabels(pts,W,H){
  var placed=[];
  // 候选位：下/上/右/左 × 三档外扩；先近后远，先下后上，保证确定性
  var CAND=[]; [0,10,22].forEach(function(k){ [0,1,2,3].forEach(function(m){ CAND.push([m,k]); }); });
  function box(p,mode,k){ var w=(p.label||'').length*12+4,h=14,x,y;
    if(mode===0){ x=p.x-w/2; y=p.y+p.r+6+k; }
    else if(mode===1){ x=p.x-w/2; y=p.y-p.r-20-k; }
    else if(mode===2){ x=p.x+p.r+7+k; y=p.y-7; }
    else { x=p.x-p.r-7-k-w; y=p.y-7; }
    return {x:x,y:y,w:w,h:h}; }
  function hitsCircle(b){ return pts.some(function(q){
    var cx=Math.max(b.x,Math.min(q.x,b.x+b.w)), cy=Math.max(b.y,Math.min(q.y,b.y+b.h));
    return Math.hypot(q.x-cx,q.y-cy)<q.r+1; }); }
  function hitsPlaced(b){ return placed.some(function(o){
    return b.x<o.x+o.w+4&&o.x<b.x+b.w+4&&b.y<o.y+o.h+4&&o.y<b.y+b.h+4; }); }
  // 大圆先放（标签更重要且更难挪），小圆后放
  var order=pts.slice().sort(function(a,b){ return b.r-a.r; });
  order.forEach(function(p){ var best=null,i;
    for(i=0;i<CAND.length;i++){ var b=box(p,CAND[i][0],CAND[i][1]);
      if(b.x<4||b.x+b.w>W-4||b.y<12||b.y+b.h>H-4) continue;
      if(hitsCircle(b)||hitsPlaced(b)) continue; best=b; break; }
    if(!best) best=box(p,0,0);                        // 全撞则回落，CK-6g 体检会报出来
    placed.push(best); p._lab=best; });
  return pts;
}

/* 生成一张矛盾坐标 SVG。items 见 09 §8 契约；sub=true 用小画布（4.2 子坐标系） */
function cmapSVG(items,opts){
  opts=opts||{}; var sub=!!opts.sub, p=PAL();
  var W=900, H=sub?470:620, x0=100, x1=830, y0=70, y1=sub?390:520;
  var X=function(v){ return x0+num(v)/100*(x1-x0); }, Y=function(v){ return y1-num(v)/100*(y1-y0); };
  var pts=(items||[]).map(function(it,i){
    return { i:i, x:X(it.F), y:Y(it.D), r:Math.max(8,4.3*Math.sqrt(Math.max(0,num(it.odds)))),
             label:it.label||it.id||('#'+(i+1)), it:it }; });
  placeLabels(pts,W,H);
  var s='<svg class="cmap" viewBox="0 0 '+W+' '+H+'" role="img" aria-label="矛盾坐标图">';
  s+='<g stroke="'+p.grid+'" stroke-width="1">';
  [0.25,0.75].forEach(function(f){ s+='<line x1="'+x0+'" y1="'+(y1-(y1-y0)*f)+'" x2="'+x1+'" y2="'+(y1-(y1-y0)*f)+'"/>';
    s+='<line x1="'+(x0+(x1-x0)*f)+'" y1="'+y0+'" x2="'+(x0+(x1-x0)*f)+'" y2="'+y1+'"/>'; });
  s+='</g>';
  s+='<line x1="'+((x0+x1)/2)+'" y1="'+y0+'" x2="'+((x0+x1)/2)+'" y2="'+y1+'" stroke="'+p.muted+'" stroke-width="1" stroke-dasharray="6 5" opacity=".45"/>';
  s+='<line x1="'+x0+'" y1="'+((y0+y1)/2)+'" x2="'+x1+'" y2="'+((y0+y1)/2)+'" stroke="'+p.muted+'" stroke-width="1" stroke-dasharray="6 5" opacity=".45"/>';
  if(!sub){
    s+='<text x="'+(x0+12)+'" y="'+(y0+18)+'" font-size="11.5" font-weight="600" fill="'+p.muted+'">敞口区 · 吵得凶但验不了</text>';
    s+='<text x="'+(x0+12)+'" y="'+(y0+32)+'" font-size="10.5" fill="'+p.muted+'">控仓位 / 要折价，不进研究清单</text>';
    s+='<text x="'+(x1-12)+'" y="'+(y0+18)+'" font-size="11.5" font-weight="600" text-anchor="end" fill="'+p.good+'">对手盘区 · 吵得凶且能验</text>';
    s+='<text x="'+(x1-12)+'" y="'+(y0+32)+'" font-size="10.5" text-anchor="end" fill="'+p.muted+'">研究预算押这里</text>';
    s+='<text x="'+(x0+12)+'" y="'+(y1-20)+'" font-size="11.5" font-weight="600" fill="'+p.muted+'">盲区 · 没人吵也难验</text>';
    s+='<text x="'+(x1-12)+'" y="'+(y1-20)+'" font-size="11.5" font-weight="600" text-anchor="end" fill="'+p.accent+'">低成本区 · 没人吵但一查就有</text>';
    s+='<text x="'+(x1-12)+'" y="'+(y1-7)+'" font-size="10.5" text-anchor="end" fill="'+p.muted+'">虚线＝零覆盖，读财报即可；实心＝真已定价</text>';
  }
  s+='<line x1="'+x0+'" y1="'+y1+'" x2="'+x1+'" y2="'+y1+'" stroke="'+p.fg+'" stroke-width="1.3"/>';
  s+='<line x1="'+x0+'" y1="'+y0+'" x2="'+x0+'" y2="'+y1+'" stroke="'+p.fg+'" stroke-width="1.3"/>';
  s+='<text x="'+((x0+x1)/2)+'" y="'+(y1+42)+'" font-size="13" font-weight="600" text-anchor="middle" fill="'+p.fg+'">可证伪性　→　能不能拿到判定它的那个数</text>';
  s+='<text x="34" y="'+((y0+y1)/2)+'" font-size="13" font-weight="600" text-anchor="middle" fill="'+p.fg+'" transform="rotate(-90 34 '+((y0+y1)/2)+')">分歧度　→　各家口径的方差</text>';
  [[0,'0'],[50,'50'],[100,'100']].forEach(function(t){
    s+='<text x="'+X(t[0])+'" y="'+(y1+18)+'" font-size="10.5" text-anchor="middle" fill="'+p.muted+'">'+t[1]+'</text>';
    s+='<text x="'+(x0-12)+'" y="'+(Y(t[0])+4)+'" font-size="10.5" text-anchor="end" fill="'+p.muted+'">'+t[1]+'</text>'; });
  pts.forEach(function(q){ var it=q.it, c=cmLayColor(it.layer), zero=num(it.coverage,-1)===0;
    var fo=zero?'.13':'.62', sw=zero?'2.6':'1.4', dash=zero?' stroke-dasharray="6 3.5"':'';
    var link=it.narrative?('<a href="#nar-'+esc(it.narrative)+'">'):'', lend=it.narrative?'</a>':'';
    // ★形状=role（09 §8a，2026-08-14）：圆=主动矛盾 / 方=从动矛盾。
    //   等面积换算 a=√π·r≈1.772r —— 同赔率的圆与方看起来一样大，面积通道仍严格正比赔率。
    s+=link+cmShape(q,c,fo,sw,dash);
    s+='<text x="'+q.x+'" y="'+(q.y+(q.r>13?4.5:3.5))+'" font-size="'+(q.r>16?13:(q.r>11?11.5:10))+'" font-weight="700" text-anchor="middle" fill="'+(zero?c:'#fff')+'">'+esc(it.id||(q.i+1))+'</text>'+lend;
    if(q._lab) s+='<text class="qlab" x="'+(q._lab.x+q._lab.w/2)+'" y="'+(q._lab.y+11)+'" text-anchor="middle" fill="'+c+'">'+esc(q.label)+'</text>';
  });
  s+='<g>';           // 浮窗层放最后 → 画在所有圆之上
  pts.forEach(function(q){ var it=q.it, c=cmLayColor(it.layer);
    var lines=wrapCJK(it.detail||'',30).slice(0,2);
    var basis=wrapCJK('分歧口径：'+(it.dispersion_basis||'—'),31).slice(0,2);
    var bh=64+lines.length*17+basis.length*16, bw=400;
    var bx=q.x<(x0+x1)/2 ? Math.min(q.x+q.r+12, W-bw-8) : Math.max(q.x-q.r-12-bw, 8);
    var by=Math.max(6, Math.min(q.y-bh/2, H-bh-6));
    s+='<g class="hot"><circle class="hit" cx="'+q.x+'" cy="'+q.y+'" r="'+Math.max(q.r,11).toFixed(1)+'"/><g class="tip">';
    s+='<rect x="'+bx+'" y="'+by+'" width="'+bw+'" height="'+bh+'" rx="6" fill="'+p.fg+'" fill-opacity=".95"/>';
    var ty=by+22;
    s+='<text x="'+(bx+16)+'" y="'+ty+'" font-size="11.5" font-weight="700" fill="'+p.bg+'">'+esc(it.id?(it.id+' · '):'')+esc(it.one_liner||it.label||'')+'</text>'; ty+=21;
    lines.forEach(function(L){ s+='<text x="'+(bx+16)+'" y="'+ty+'" font-size="11.5" fill="'+p.bg+'" fill-opacity=".82">'+esc(L)+'</text>'; ty+=17; });
    ty+=7;
    s+='<text x="'+(bx+16)+'" y="'+ty+'" font-size="11.5" font-weight="700" fill="'+c+'">'+esc(it.layer||'—')+(it.dir?('　'+(it.dir==='down'?'▼下行风险':'▲上行驱动')):'')+'</text>';
    s+='<text x="'+(bx+186)+'" y="'+ty+'" font-size="11.5" fill="'+p.bg+'" fill-opacity=".82">赔率 '+num(it.odds)+'% · 可证伪 '+num(it.F)+' · 分歧 '+num(it.D)+'</text>'; ty+=17;
    basis.forEach(function(L){ s+='<text x="'+(bx+16)+'" y="'+ty+'" font-size="11" fill="'+p.bg+'" fill-opacity=".68">'+esc(L)+'</text>'; ty+=16; });
    s+='</g></g>'; });
  s+='</g></svg>';
  return s;
}

/* ★4.1.1 默认视图＝三坐标条（2026-08-17 石英股份读者反馈「三坐标图太大，影响观感，换一个可视化形式」）。
   气泡图 viewBox 900×620 铺满整栏会比一屏还高，而且赔率没算出来时全是最小圆，图上什么都读不出来。
   条形矩阵一行一条矛盾：可证伪 F / 分歧 D / 赔率 三根同尺度条，10 条也只占 ~260px；气泡图收进折叠块，
   保留给想看象限分布的人（CK-6 g 的几何体检仍对 SVG 跑）。通则写进 06 §3.0e：全景图不许比一屏高，条形/表格优先。 */
function cmapStrip(items,opts){
  opts=opts||{}; var p=PAL();
  var rows=(items||[]).slice().sort(function(a,b){ return Math.abs(num(b.odds))-Math.abs(num(a.odds)); });
  var maxO=Math.max(10,Math.max.apply(null,rows.map(function(it){ return Math.abs(num(it.odds)); }).concat([0])));
  var noOdds=rows.filter(function(it){ return it.odds==null||!isFinite(num(it.odds)); }).length;
  var h='<div class="cstrip'+(opts.sub?' sub':'')+'">'+
    '<div class="cx-row cx-head"><span class="cx-lab">矛盾（●主动 ■从动）</span><span class="cx-bar">可证伪 F</span><span class="cx-bar">分歧 D</span><span class="cx-bar">赔率 · 占现市值%</span></div>';
  rows.forEach(function(it){
    var zero=num(it.coverage,-1)===0, od=num(it.odds), hasO=(it.odds!=null&&isFinite(od));
    var lay=cmLayColor(it.layer);
    h+='<div class="cx-row'+(zero?' zero':'')+'">'+
      '<span class="cx-lab"><span class="cx-dot" style="background:'+lay+'"></span>'+(isPassive(it)?'■':'●')+' <b>'+esc(it.label||it.id||'')+'</b>'+
        (it.subtype?('<i>'+esc(it.subtype)+(it.clock?(' · '+esc(it.clock)):'')+'</i>'):'')+(zero?'<i class="cx-zero">零覆盖</i>':'')+'</span>'+
      '<span class="cx-bar"><i style="width:'+Math.max(0,Math.min(100,num(it.F)))+'%;background:'+p.s[0]+'"></i><b>'+num(it.F)+'</b></span>'+
      '<span class="cx-bar"><i style="width:'+Math.max(0,Math.min(100,num(it.D)))+'%;background:'+p.s[1]+'"></i><b>'+num(it.D)+'</b></span>'+
      '<span class="cx-bar o">'+(hasO
          ?('<i style="width:'+Math.round(Math.abs(od)/maxO*100)+'%;background:'+(od>=0?p.good:p.bad)+'"></i><b>'+(od>0?'+':'')+Math.round(od)+'%</b>')
          :'<b class="rd">未算（CK-6 c 不过）</b>')+'</span></div>'; });
  h+='</div>';
  if(noOdds) h+='<div class="nweak"><b class="rd">CK-6 c 不过：</b>'+noOdds+'/'+rows.length+' 条矛盾没有赔率数字。odds_basis 写了怎么算不等于算了——tornado 的 bar 或手算的上界必须落成 items[].odds 这个数，否则本图与 4.2.1 覆盖表都是空的。</div>';
  return h;
}

function cmapLegend(items){
  var used={}; (items||[]).forEach(function(it){ if(it.layer) used[it.layer]=1; });
  var keys=Object.keys(CMAP_LAYER).filter(function(k){ return used[k]; });
  var roles={}; (items||[]).forEach(function(it){ if(it.role) roles[it.role]=1; });
  var shapeLeg=Object.keys(roles).length
    ? '　│　<b>●</b> 主动矛盾，生成上行　<b>■</b> 从动矛盾，限制上行、决定节奏'
    : '　│　<span class="rd">未填 role，形状未启用，CK-6 T1 不过</span>';
  return '<div class="cmap-legend">所属层：'+keys.map(function(k){
      return '<span style="color:'+CMAP_LAYER[k]+'">■</span> '+k; }).join('　')+shapeLeg+
    '　│　<b>实心</b>＝市场有公开分歧　<b>虚线</b>＝零覆盖，没人发表所以方差接近零，但不等于没价值　│　面积 ∝ 赔率，占现市值%</div>';
}

function cmapTable(items){
  var rows=(items||[]).slice().sort(function(a,b){ return num(b.odds)-num(a.odds); });
  var h='<table class="cmap-tb"><tr><th>#</th><th>核心点</th><th>所属层</th><th>角色 · 子类 · 时钟</th>'+
        '<th class="n">可证伪</th><th class="n">分歧</th><th class="n">赔率</th><th>分歧口径（方差怎么来的）</th><th>验证</th></tr>';
  rows.forEach(function(it){ var zero=num(it.coverage,-1)===0;
    // 角色格：形状记号 + 子类 + 时钟；系统协同型额外显示当前绑定环（13 §2d，约束会漂移）
    var bind=(it.binding_now||{}).link;
    var roleCell=it.role
      ? '<span class="c-role '+(isPassive(it)?'psv':'act')+'">'+(isPassive(it)?'■':'●')+' '+esc(it.role)+'</span>'+
        (it.subtype?('<br><span class="muted" style="font-size:11px">'+esc(it.subtype)+
          (it.clock?(' · 时钟'+esc(it.clock)):'')+'</span>'):'')+
        (bind?('<br><span class="c-bind">当前卡：'+esc(bind)+'</span>'):'')
      : '<span class="muted">⚠️未填</span>';
    h+='<tr'+(zero?' class="zero"':'')+'><td>'+esc(it.id||'')+'</td><td><b>'+esc(it.label||'')+'</b>'+
      (it.hooked?('<br><span class="muted" style="font-size:11px">挂：'+esc(it.hooked)+'</span>'):'')+
      ((it.co_kill||[]).length?('<br><span class="c-cokill">⚠ 与 '+esc((it.co_kill||[]).join('/'))+' 同源失效</span>'):'')+'</td>'+
      '<td><span class="c-lay" style="background:'+cmLayColor(it.layer)+'">'+esc(it.layer||'—')+'</span></td>'+
      '<td>'+roleCell+'</td>'+
      '<td class="n">'+num(it.F)+'</td><td class="n">'+num(it.D)+'</td><td class="n">'+((it.odds==null||!isFinite(num(it.odds)))?'<span class="rd">未算</span>':(num(it.odds)+'%'))+'</td>'+
      '<td>'+(zero?'<b>零覆盖</b>：':'')+esc(it.dispersion_basis||'⚠️未填')+'</td>'+
      '<td>'+esc(it.verify||'—')+'</td></tr>'; });
  return h+'</table>';
}

/* 分型闸的页面提示（13 §0 总纲一 / 09 CK-6 T1）：主动/从动各≥1，只列一类＝这章没做完。
   只有主动＝不知道会被什么洗出去；只有从动＝不知道为什么值钱。 */
function roleGateNote(items){
  var a=0,p=0,miss=[];
  (items||[]).forEach(function(it){ if(it.role==='主动') a++; else if(it.role==='从动') p++; else miss.push(it.id||'?'); });
  var m=[];
  if(miss.length) m.push('<b>⚠️ CK-6 T1 不过：</b>'+miss.length+' 条未填 role（'+esc(miss.join('、'))+'）');
  else if(!a||!p) m.push('<b>⚠️ CK-6 T1 不过：</b>只列了'+(a?'主动':'从动')+'矛盾（主动 '+a+' / 从动 '+p+
    '）。只有主动＝不知道会被什么洗出去；只有从动＝不知道为什么值钱。');
  return m.length?('<div class="nweak" style="margin-top:8px">'+m.join('<br>')+'</div>'):'';
}

/* 4.4 核心矛盾深度研究：怎么理解 → 市面方案评估 → 落地方案 → 判定表 → 时间表 → 历史对标 */
var VD_CLS={'采用':'vd-use','备选':'vd-alt','弃用':'vd-drop'};
function vdOf(s){ s=String(s||''); for(var k in VD_CLS){ if(s.indexOf(k)===0) return {cls:VD_CLS[k],k:k}; } return {cls:'vd-alt',k:s||'—'}; }
/* 深度研究的六块用 ①–⑥ 而不是第四级小数：它们是同一条矛盾的分析步骤，
   不是导航层级；小数点打到四级只会把目录压垮（09 §0c）。 */
var DDN=['①','②','③','④','⑤','⑥'];
function ddSec(i,title){ return '<div class="dd-sec"><div class="h"><span class="dn">'+DDN[i]+'</span>'+esc(title)+'</div>'; }
function renderDeepDive(no,slotKey,slot,it,hd){
  var dd=(slot||{}).deepdive; if(!dd) return '';
  var u=dd.understanding||dd;
  var h=hd3(no,hd+' · '+(it.label||slot.id||''),
    '这一节回答：这条矛盾到底怎么跟。先讲清它是什么，再逐个评市面上的跟踪办法，然后定主方案、判定阈值和时点，最后拿历史同类案例对一遍。');
  h+='<div class="dd '+slotKey+'">';
  h+='<div class="dd-hd"><div class="k">'+esc(hd)+'</div><div class="t">'+esc(it.label||slot.id||'')+'</div>'+
     '<div class="m">赔率 '+num(it.odds)+'% 现市值 · 可证伪 '+num(it.F)+' · 分歧 '+num(it.D)+
     (it.layer?(' · '+esc(it.layer)+'层'):'')+
     (it.role?(' · '+esc(it.role)+(it.subtype?('／'+esc(it.subtype)):'')):'')+'</div></div><div class="dd-body">';
  h+=ddSec(0,'怎么理解这条矛盾');
  if(u.essence) h+='<div class="dd-ess"><em>'+esc(u.essence)+'</em></div>';
  if(u.mechanism) h+='<div class="dd-mech"><b>作用机制：</b>'+esc(u.mechanism)+'</div>';
  if(u.resolve_up||u.resolve_down){ h+='<div class="dd-2col">'+
    '<div class="dd-up"><b>向上解决的条件</b><br>'+esc(u.resolve_up||'—')+'</div>'+
    '<div class="dd-dn"><b>向下解决的条件</b><br>'+esc(u.resolve_down||'—')+'</div></div>'; }
  if(u.why_core) h+='<div class="dd-mech"><b>为什么是核心矛盾：</b>'+esc(u.why_core)+'</div>';
  if(u.common_mistake) h+='<div class="dd-miss"><b>最常犯的错：</b>'+esc(u.common_mistake)+'</div>';
  h+='</div>';
  var op=dd.options||[];
  if(op.length){ h+=ddSec(1,'市面上有哪些解决方案（'+op.length+' 个候选）')+
    '<table class="dd-tb"><tr><th>结论</th><th>方法</th><th>怎么做</th><th>可得性</th><th>时滞</th><th>成本</th><th>信噪比</th><th>能否证伪</th></tr>';
    op.forEach(function(o){ var v=vdOf(o.verdict);
      h+='<tr'+(v.k==='弃用'?' class="drop"':'')+'><td><span class="vd '+v.cls+'">'+esc(v.k)+'</span></td>'+
        '<td><b>'+esc(o.name||'')+'</b></td><td>'+esc(o.how||'')+'</td><td>'+esc(o.availability||'')+'</td>'+
        '<td>'+esc(o.lag||'')+'</td><td>'+esc(o.cost||'')+'</td><td>'+esc(o.snr||'')+'</td>'+
        '<td>'+esc(o.falsifiable||'')+'</td></tr>'; });
    h+='</table></div>'; }
  var pl=dd.plan||{};
  if(pl.primary||pl.fallback||pl.blind_spot){ h+=ddSec(2,'落地跟踪方案')+'<div class="dd-plan">'+
    '<div><div class="pl-hd">主方案</div>'+esc(pl.primary||'—')+'</div>'+
    '<div><div class="pl-hd">备选 · 主方案失效时</div>'+esc(pl.fallback||'—')+'</div>'+
    '<div class="blind"><div class="pl-hd">已知盲区 · 它仍然验不了什么</div>'+(pl.blind_spot?esc(pl.blind_spot):'<span class="rd">未填</span>')+'</div>'+
    '</div></div>'; }
  var rl=dd.ruling||[];
  if(rl.length){ h+=ddSec(3,'判定表 · 看到什么算解决')+
    '<table class="dd-tb"><tr><th>观测信号</th><th>阈值</th><th>判定</th></tr>';
    rl.forEach(function(r){ h+='<tr><td>'+esc(r.signal||'')+'</td><td><b>'+esc(r.threshold||'')+'</b></td><td>'+esc(r.means||'')+'</td></tr>'; });
    h+='</table></div>'; }
  var cal=dd.calendar||[];
  if(cal.length){ h+=ddSec(4,'未来 12 个月的判定时点')+'<div class="dd-cal">'+
    cal.map(function(c){ return '<span><b>'+esc(c.when||'')+'</b> '+esc(c.what||'')+'</span>'; }).join('')+'</div></div>'; }
  // ★历史对标（09 §6c）：锚查 13 §6 单维案例库，不许现编。diff 缺失＝这块只是装饰，D3 不过。
  var ag=dd.analog;
  if(ag){ h+=ddSec(5,'历史对标')+'<div class="dd-analog">'+
    '<div class="ag-hd"><b>'+esc(ag.case||'—')+'</b>'+(ag.pair?('<span class="ag-pair">'+esc(ag.pair)+'</span>'):'')+
      (ag.src?('<span class="ag-src">'+esc(ag.src)+'</span>'):'')+'</div>'+
    '<div class="ag-row"><span class="ag-k">当时</span>'+esc(ag.then||'—')+'</div>'+
    '<div class="ag-row"><span class="ag-k">结局</span>'+esc(ag.outcome||'—')+'</div>'+
    '<div class="ag-row"><span class="ag-k">当时的 tell</span>'+esc(ag.tell||'—')+'</div>'+
    '<div class="ag-row diff"><span class="ag-k">与本例的关键差异</span>'+
      (ag.diff?('<span class="hl">'+esc(ag.diff)+'</span>'):'<span class="rd">未填 diff。没有差异这一栏，对标只是装饰不是判据，CK-6 D3 不过。</span>')+
    '</div></div></div>'; }
  if(!(dd.plan||{}).blind_spot) h+='<div class="dd-sec"><span class="rd">未填 plan.blind_spot，也就是没写它仍然验不了什么。CK-6 D2 不过。</span></div>';
  return h+'</div></div>';
}

/* ===========================================================================
 * 4.2 场景（09 §5.5）—— 投资结论的大白话出口
 *   ①哪几个场景涨/跌 ②靠什么解锁(中期叙事+短期催化) ③赔率怎么算·R/M/V 各贡献多少
 * 场景 = 主动矛盾解方向 × 从动矛盾解方向的叉乘，必须 from 指名，不许自由创作。
 * ======================================================================== */

/* knobs 路径归一：兼容 `segments[0].assume.x`(hooked 写法) 与 `segments.0.assume.x`(滑块写法)，
   并把估值腿的 key 寻址 `valuation.<pkey>.params.x` / `valuation.<pkey>.weight`
   翻成引擎认的 `valuation.paradigms.<idx>...`。★按 key 不按下标——下标会随增删腿漂移。 */
function knobPath(model,path){
  var p=String(path||'').replace(/\[(\d+)\]/g,'.$1');
  var m=/^valuation\.([A-Za-z_]\w*)\.(.+)$/.exec(p);
  if(m){
    var pds=((model||{}).valuation||{}).paradigms||[], ix=-1;
    pds.forEach(function(pd,i){ if(pd&&pd.key===m[1]) ix=i; });
    if(ix<0) return null;                                   // 指到不存在的腿 → 由体检报出来
    return 'valuation.paradigms.'+ix+'.'+m[2];
  }
  return p;
}
/* 把一组 knobs 应用到 MODEL 的深拷贝上，跑引擎得市值。不触碰 live MODEL。 */
function scenarioRun(knobs){
  var m; try{ m=JSON.parse(JSON.stringify(MODEL)); }catch(e){ return null; }
  var bad=[];
  Object.keys(knobs||{}).forEach(function(k){
    var p=knobPath(m,k); if(p==null){ bad.push(k); return; }
    setPath(m,p,knobs[k]); });
  var pl,res; try{ pl=EONE.recomputePL(m); relinkStatic(pl,m); res=EONE.runValuation(m.valuation||{},pl); }
  catch(e){ return {err:e.message,bad:bad}; }
  return { mcap:(res.blend||{}).mcap, res:res, pl:pl, bad:bad };
}
/* 场景点击 → 把 knobs 写进 live MODEL、同步镜像滑块、整页重算（与 bindRangeInputs 同一套通道）。 */
function applyScenario(key){
  var sc=(((D.part4||{}).scenarios||{}).items||[]).filter(function(x){return x.key===key;})[0];
  if(!sc||!sc.knobs) return;
  Object.keys(sc.knobs).forEach(function(k){
    var p=knobPath(MODEL,k); if(p==null) return;
    setPath(MODEL,p,sc.knobs[k]);
    [].slice.call(document.querySelectorAll('input[data-path]')).forEach(function(o){
      if(o.dataset.path===p) o.value=sc.knobs[k]; });
    [].slice.call(document.querySelectorAll('[data-kv]')).forEach(function(kv){
      if(kv.getAttribute('data-kv')===p) kv.textContent=knobDisp(p,sc.knobs[k]); });
  });
  recompute();
  var a=el('sec-cscen'); if(a&&a.scrollIntoView) a.scrollIntoView({behavior:'smooth',block:'start'});
}

var RMV_C={r:'#c2703d',m:'#5b7f4b',v:'#47709e'};    // 与 CMAP_LAYER 的 收入/利润率/估值 同色
var RMV_N={r:'收入',m:'利润率',v:'估值'};
/* 累积瀑布条：从 0 出发依次叠 R→M→V，正向右负向左，末端打总计刻度。
   scale 全场景 + 第二章历史段共用（09 §5.5e），所以跨条、跨章直接可比。 */
function rmvBar(rmv,total,scale,opt){
  opt=opt||{}; var p=PAL();
  var W=560,H=opt.slim?30:40, x0=W/2, half=W/2-46, sc=half/(scale||1);
  var s='<svg class="rmvbar" viewBox="0 0 '+W+' '+H+'" role="img" aria-label="R/M/V 分解">';
  s+='<line x1="'+x0+'" y1="2" x2="'+x0+'" y2="'+(H-10)+'" stroke="'+p.muted+'" stroke-width="1" opacity=".55"/>';
  var cur=0, y=opt.slim?4:6, bh=opt.slim?13:17;
  ['r','m','v'].forEach(function(k){
    var v=num(rmv&&rmv[k+'_pp']), nx=cur+v;
    var xa=x0+Math.min(cur,nx)*sc, w=Math.abs(v)*sc;
    if(w>0.4) s+='<rect x="'+xa.toFixed(1)+'" y="'+y+'" width="'+w.toFixed(1)+'" height="'+bh+
      '" fill="'+RMV_C[k]+'" fill-opacity="'+(opt.ghost?'.28':'.82')+'"/>';
    if(w>26) s+='<text x="'+(xa+w/2).toFixed(1)+'" y="'+(y+bh-4)+'" font-size="10.5" text-anchor="middle" fill="#fff">'+
      RMV_N[k]+' '+(v>0?'+':'')+Math.round(v)+'</text>';
    cur=nx; });
  var tx=x0+num(total)*sc;
  s+='<line x1="'+tx.toFixed(1)+'" y1="'+(y-3)+'" x2="'+tx.toFixed(1)+'" y2="'+(y+bh+3)+'" stroke="'+p.fg+'" stroke-width="2"/>';
  s+='<text x="'+(tx+(num(total)>=0?6:-6)).toFixed(1)+'" y="'+(y+bh-3)+'" font-size="11" font-weight="700" text-anchor="'+
      (num(total)>=0?'start':'end')+'" fill="'+p.fg+'">'+(num(total)>0?'+':'')+Math.round(num(total))+'pp</text>';
  if(opt.tag) s+='<text x="4" y="'+(H-2)+'" font-size="10" fill="'+p.muted+'">'+esc(opt.tag)+'</text>';
  return s+'</svg>';
}
/* 第二章历史各阶段里 |V| 最大的那一段——用作场景 V 贡献的横比对照（09 §5.5e） */
function histTopPhase(){
  var ph=((D.part2||{}).phases)||[], best=null;
  ph.forEach(function(x){ var f=x.factor_quant; if(!f) return;
    if(!best||Math.abs(num(f.v_pp))>Math.abs(num(best.factor_quant.v_pp))) best=x; });
  return best;
}
var UNL_CLS={'已发生':'ul-ok','进行中':'ul-mid','未发生':'ul-no'};
/* 三级编号：编号左对齐成列 + 正文悬挂缩进。全章不许再出现无编号的裸块（09 §0c）。 */
function hd3(no,title,ask){ return '<h3 class="n3" id="s-'+esc(no)+'"><span class="no">'+esc(no)+'</span>'+esc(title)+'</h3>'+
  (ask?('<p class="ask">'+esc(ask)+'</p>'):''); }
function hd4(no,title){ return '<h4 class="n4"><span class="no">'+esc(no)+'</span>'+esc(title)+'</h4>'; }

/* 4.2.1 覆盖：进图的每条矛盾去了哪里（09 §5.5-0）。
   去向由场景的 from 反推，分析师只需给没进场景那几条填 no_scenario。 */
var CUT_WHY=['已定价','重述叙事','赔率虚高','与主线无因果'];
/* 去向只有三种。★没有「待研究」这一档：上了图的矛盾都过了 CK-6b（RAG 取证带数字）
   和 tornado 赔率，它已经研究过了。真正缺的是「横切」——不定义某个 Case，
   而是把所有 Case 的赔率整体推一档（筹码、摊薄、汇率、税率都属这类）。 */
function dispose(items,scs){
  var used={}; (scs||[]).forEach(function(s){ var f=s.from||{};
    if(f.active) (used[f.active]=used[f.active]||[]).push(s);
    if(f.passive) (used[f.passive]=used[f.passive]||[]).push(s); });
  return (items||[]).map(function(it){
    var ns=it.no_scenario||{};
    return { it:it, scs:used[it.id]||[],
      status: (used[it.id]||[]).length ? '已建 Case' : (ns.status||'未交代'),
      why: ns.why||'' }; });
}
function renderCoverage(items,scs){
  var d=dispose(items,scs);
  var nIn=d.length, nUse=d.filter(function(x){return x.status==='已建 Case';}).length;
  var nCut=d.filter(function(x){return x.status==='剪掉';}).length;
  var nTodo=d.filter(function(x){return x.status==='横切';}).length;
  var nGap=d.filter(function(x){return x.status==='未交代';}).length;
  /* ★2026-08-14 用户圈红：原来三层说同一件事——小标题一段方法论解释、漏斗条四个数、
     再一句 cov-lead 把那四个数用汉字复述一遍。漏斗条已经把话说完了，另两层删掉。
     小标题也不再写「这一节回答…」（CK-7 h1 反脚手架同款纪律）。 */
  var h=hd3('4.2.1','覆盖', '4.1 那 '+nIn+' 条矛盾各自的去向。');
  h+='<div class="fnl"><span class="fnl-i"><b>'+nIn+'</b>条进图</span><span class="fnl-a">›</span>'+
     '<span class="fnl-i ok"><b>'+nUse+'</b>条建了 Case</span><span class="fnl-a">›</span>'+
     '<span class="fnl-i todo"><b>'+nTodo+'</b>条横切全部 Case</span><span class="fnl-a">›</span>'+
     '<span class="fnl-i cut"><b>'+nCut+'</b>条剪掉</span>'+
     (nGap?('<span class="fnl-a">›</span><span class="fnl-i gap"><b class="rd">'+nGap+'</b>条未交代</span>'):'')+'</div>';
  if(nGap) h+='<p class="cov-lead"><span class="rd"><b>'+nGap+'</b> 条没交代去向</span>，读者分不清是评估过还是漏了。下表逐条点名。</p>';
  var ord={'未交代':0,'横切':1,'剪掉':2,'已建 Case':3};
  h+='<table class="cov-tb"><tr><th>矛盾</th><th>角色 · 子类</th><th class="n">赔率</th><th>去向</th><th>理由 / 落在哪个 Case</th></tr>';
  d.slice().sort(function(a,b){ return (ord[a.status]-ord[b.status])||(Math.abs(num(b.it.odds))-Math.abs(num(a.it.odds))); })
   .forEach(function(x){
    var it=x.it, cls={'已建 Case':'dp-ok','剪掉':'dp-cut','横切':'dp-todo','未交代':'dp-gap'}[x.status];
    var last=x.status==='已建 Case'
      ? x.scs.map(function(s){ return '<a href="#scen-'+esc(s.key||'')+'">'+esc(s.name||s.key||'')+'</a>'; }).join('、')
      : (x.why ? esc(x.why)
               : '<span class="rd">未交代去向。CK-6 V1 不过。</span>');
    h+='<tr class="'+cls+'"><td><b>'+esc(it.label||it.id||'')+'</b><span class="muted"> '+esc(it.id||'')+'</span></td>'+
       '<td>'+(it.role?('<span class="c-role '+(isPassive(it)?'psv':'act')+'">'+(isPassive(it)?'■':'●')+' '+esc(it.role)+'</span>'+
         (it.subtype?('<span class="muted"> · '+esc(it.subtype)+'</span>'):'')):'<span class="rd">未填</span>')+'</td>'+
       '<td class="n">'+((it.odds==null||!isFinite(num(it.odds)))?'<span class="rd">未算</span>':((num(it.odds)>0?'+':'')+Math.round(num(it.odds))+'%'))+'</td>'+
       '<td><span class="dp '+cls+'">'+esc(x.status)+'</span></td><td>'+last+'</td></tr>'; });
  return h+'</table>';
}

function renderScenarios(){
  var host=el('cmap-scen'); if(!host) return;
  var P4=D.part4||{}, S=P4.scenarios||{}, its=S.items||[];
  if(!its.length){ host.innerHTML='<p class="cap"><span class="rd">未填 <code>part4.scenarios</code></span>，CK-6 S1 不过。第四章要先给结果：哪几个 Case 涨跌、靠什么解锁、赔率与 R/M/V 怎么构成。</p>'; return; }
  var base=num(S.base_mcap_yi,num((MODEL.valuation||{}).current_mcap_yi,num((D.meta||{}).current_mcap_yi,0)));
  var hp=histTopPhase();
  var vals=[]; its.forEach(function(x){ var q=x.rmv||{};
    ['r_pp','m_pp','v_pp'].forEach(function(k){ vals.push(Math.abs(num(q[k]))); }); vals.push(Math.abs(num(x.odds))); });
  if(hp&&hp.factor_quant) ['r_pp','m_pp','v_pp'].forEach(function(k){ vals.push(Math.abs(num(hp.factor_quant[k]))); });
  var scale=Math.max(20,Math.ceil(Math.max.apply(null,vals.concat([1]))/10)*10);

  var ups=its.filter(function(x){return x.dir!=='down';}), dns=its.filter(function(x){return x.dir==='down';});
  var h='<p class="sec-ask">'+esc(S.note||'一条 Case ＝一条主动矛盾的解法配一条从动矛盾的解法。每条都能还原成第三章的一组参数，点「套用」就能让滑块跳过去重算。')+
    (S.asof?(' <span class="muted">（as-of '+esc(S.asof)+'）</span>'):'')+'</p>';
  if(!dns.length) h+='<div class="nweak"><b class="rd">CK-6 S1 不过：</b>没有下行 Case。只列上行不构成投资结论。</div>';
  if(its.length<3||its.length>5) h+='<div class="nweak"><b class="rd">CK-6 S1 不过：</b>Case '+its.length+' 条，应为 3–5 条。</div>';

  // ---- 4.2.1 覆盖（分母 + 全貌）----
  h+=renderCoverage(P4.items||[],its);
  h+=scenTable(its,'全部 '+its.length+' 条一览（上行 '+ups.length+' / 下行 '+dns.length+'）');
  h+=scenEVBlock(its);

  // ---- 4.2.2 上行 · 4.2.3 下行（各占一级，不再嵌套）----
  function block(no,title,ask,list){
    if(!list.length) return hd3(no,title,ask)+'<p class="cap"><span class="rd">一条都没有。</span>'+
      (no==='4.2.3'?'只列上行不构成投资结论，CK-6 S1 不过。':'')+'</p>';
    return hd3(no,title,ask)+list.slice()
      .sort(function(a,b){ return Math.abs(num(b.odds))-Math.abs(num(a.odds)); })
      .map(function(x){ return scenCard(x,base,scale,hp); }).join('');
  }
  h+=block('4.2.2','上行 Case（'+ups.length+' 条）',
    '这一节回答：往上走能到哪里，靠什么条件解锁，涨幅里哪一层出的力。',ups);
  h+=block('4.2.3','下行 Case（'+dns.length+' 条）',
    '这一节回答：往下走会到哪里，什么信号先出现，跌幅里哪一层先塌。',dns);

  // ---- 4.2.4 剪掉的与待研究的 ----
  var d=dispose(P4.items||[],its).filter(function(x){ return x.status!=='已建 Case'; });
  if(d.length){
    h+=hd3('4.2.4','横切项与剪掉的','这一节回答：上面没单独成 Case 的那几条去哪了。横切项不定义某个 Case，它把所有 Case 的赔率整体推一档；剪掉的写明按哪一类理由剪。');
    h+='<ul class="cut-list">'+d.map(function(x){
      return '<li><span class="dp '+(x.status==='横切'?'dp-todo':x.status==='剪掉'?'dp-cut':'dp-gap')+'">'+esc(x.status)+'</span>'+
        '<b>'+esc(x.it.label||x.it.id||'')+'</b>　'+
        (x.why?esc(x.why):'<span class="rd">未写理由（CK-6 V1 不过）</span>')+'</li>'; }).join('')+'</ul>';
  }

  host.innerHTML=h;
  if(!host.__scenBound){ host.__scenBound=1;
    host.addEventListener('click',function(e){ var b=e.target&&e.target.closest&&e.target.closest('.sc-apply');
      if(b&&b.getAttribute('data-scen')) applyScenario(b.getAttribute('data-scen')); }); }
}

/* ★2026-08-14 期望值与现价隐含概率（见 09 §4.6）。
   赔率没有概率就不是赔率，是情景标价——阳光 v3.1 五条 Case 两上三下、
   +77/+57/−16/−13/−18 摆在那里，读者合不出一个 EV 来。
   两个数一起看才有决策含义：我的 EV（我填的概率），以及市场现价隐含的上行概率。
   隐含概率只解一个自由参数 p_up：组内相对权重沿用我自己填的 prob 归一，
   所以它问的是「在我认可的上行/下行分布形状下，市场给上行留了几成」。 */
function scenEV(its){
  var ups=[], dns=[], sp=0, miss=0;
  its.forEach(function(x){ var p=x.prob; if(p==null||!isFinite(num(p))) miss++; else sp+=num(p);
    (x.dir==='down'?dns:ups).push(x); });
  var wmean=function(list){ var w=0,s=0; list.forEach(function(x){ var p=num(x.prob)||0; w+=p; s+=p*num(x.odds); });
    if(w>0) return s/w;                                    // 组内按填的概率加权
    if(!list.length) return null;
    return list.reduce(function(a,x){return a+num(x.odds);},0)/list.length; };  // 没填就等权
  var mu=wmean(ups), md=wmean(dns);
  var ev=miss?null:its.reduce(function(a,x){ return a+num(x.prob)*num(x.odds); },0);
  var pUp=(mu!=null&&md!=null&&(mu-md)!==0)?(-md/(mu-md)):null;   // p·mu+(1−p)·md=0
  var myUp=ups.reduce(function(a,x){ return a+(num(x.prob)||0); },0);
  return {ev:ev, sumP:sp, missing:miss, upMean:mu, dnMean:md,
          impliedUp:pUp==null?null:pUp*100, myUp:miss?null:myUp*100};
}
function scenEVBlock(its){
  var e=scenEV(its), pc=function(v){ return (v==null||!isFinite(v))?'—':(Math.round(v*10)/10)+'%'; };
  if(e.missing) return '<div class="nweak"><b class="rd">CK-6 S8 不过：</b>'+e.missing+'/'+its.length+
    ' 条 Case 没填 <code>prob</code>。赔率没有概率合不成期望值，读者拿不到 EV，只能拿到一排情景标价。'+
    (e.impliedUp!=null?('　（现价隐含上行概率仍可算：<b>'+pc(e.impliedUp)+'</b>，组内按等权）'):'')+'</div>';
  var gap=(e.myUp!=null&&e.impliedUp!=null)?(e.myUp-e.impliedUp):null;
  var sumBad=Math.abs(e.sumP-1)>0.02;
  return '<div class="ev-box">'+
    '<div class="ev-row"><span class="ev-k">我的期望值 EV</span><b class="ev-v" style="color:'+(num(e.ev)>=0?PAL().good:PAL().bad)+'">'+
      (num(e.ev)>=0?'+':'')+pc(e.ev)+'</b><span class="ev-n">Σ 概率×赔率，概率合计 '+pc(e.sumP*100)+
      (sumBad?'<b class="rd"> ⚠ 不等于 100%</b>':'')+'</span></div>'+
    '<div class="ev-row"><span class="ev-k">我给上行的概率</span><b class="ev-v">'+pc(e.myUp)+
      '</b><span class="ev-n">上行 Case 均值 '+pc(e.upMean)+'／下行均值 '+pc(e.dnMean)+'</span></div>'+
    '<div class="ev-row"><span class="ev-k">现价隐含上行概率</span><b class="ev-v">'+pc(e.impliedUp)+
      '</b><span class="ev-n">令 EV=0 反解：−下行均值 ÷（上行均值−下行均值）。组内相对权重沿用我填的概率，'+
      '所以它问的是「在我认可的分布形状下，市场给上行留了几成」</span></div>'+
    (gap==null?'':'<div class="ev-gap"><b>差 '+(gap>=0?'+':'')+(Math.round(gap*10)/10)+'pp</b> — '+
      (gap>0?'我比市场乐观这么多，这就是下注理由的全部量级；差不到 10pp 的话，这单没有边际。'
            :'我比市场悲观，现价已经把我的上行算进去了——按本页的分布，这里没有多头理由。')+'</div>')+
    '</div>';
}
function scenTable(its,cap){
  var rows=its.slice().sort(function(a,b){ return num(b.odds)-num(a.odds); });
  var hasP=its.some(function(x){ return x.prob!=null; });
  var h='<table class="scen-tb"><caption>'+esc(cap||'')+'</caption>'+
    '<tr><th>Case</th><th>方向</th>'+(hasP?'<th class="n">概率</th>':'')+'<th class="n">赔率（带）</th><th class="n">隐含市值</th><th>由哪两条矛盾解出</th><th>解锁进度</th></tr>';
  rows.forEach(function(x){
    var b=x.odds_band||[], up=x.dir!=='down', ul=x.unlock||[];
    var done=ul.filter(function(u){return u.status==='已发生';}).length;
    h+='<tr class="'+(up?'sc-up':'sc-dn')+'"><td><b><a href="#scen-'+esc(x.key||'')+'">'+esc(x.name||x.key||'')+'</a></b></td>'+
      '<td><span class="sc-dir '+(up?'up':'dn')+'">'+(up?'▲ 涨':'▼ 跌')+'</span></td>'+
      (hasP?('<td class="n">'+(x.prob==null?'<span class="rd">未填</span>':(Math.round(num(x.prob)*1000)/10)+'%')+
        (x.prob_basis?('<br><span class="muted" style="font-size:10.5px">'+esc(String(x.prob_basis).slice(0,28))+'</span>'):'')+'</td>'):'')+
      '<td class="n"><b>'+(num(x.odds)>0?'+':'')+Math.round(num(x.odds))+'%</b>'+
        (b.length===2?('<br><span class="muted" style="font-size:11px">'+Math.round(num(b[0]))+'~'+Math.round(num(b[1]))+'%</span>'):'')+'</td>'+
      '<td class="n">'+(isFinite(num(x.mcap_yi))?(yi(x.mcap_yi)+'亿'):'—')+'</td>'+
      '<td class="sc-from">'+scFrom(x)+'</td>'+
      '<td>'+(ul.length?('<b>'+done+'/'+ul.length+'</b> 已发生'+
        '<div class="ul-dots">'+ul.map(function(u){ return '<span class="'+(UNL_CLS[u.status]||'ul-no')+'" title="'+esc((u.cond||'')+' · '+(u.status||''))+'"></span>'; }).join('')+'</div>')
        :'<span class="rd">未填</span>')+'</td></tr>'; });
  return h+'</table>';
}
function scenCard(x,base,scale,hp){
  var up=x.dir!=='down', chk=scCheck(x,base);
  var h='<div class="scen-card '+(up?'up':'dn')+'" id="scen-'+esc(x.key||'')+'">';
  h+='<div class="sc-hd"><span class="sc-dir '+(up?'up':'dn')+'">'+(up?'▲':'▼')+'</span>'+
     '<span class="sc-ttl">'+esc(x.name||x.key||'')+'</span>'+
     '<span class="sc-odds '+(up?'up':'dn')+'">'+(num(x.odds)>0?'+':'')+Math.round(num(x.odds))+'%</span>'+
     (x.knobs?('<button class="sc-apply" data-scen="'+esc(x.key||'')+'">套用到第三章滑块</button>'):
              '<span class="rd">缺 knobs，S3 不过</span>')+'</div>';
  h+='<div class="sc-from2">'+scFrom(x)+'</div>';
  if(x.story) h+='<div class="sc-story"><b>中期叙事 · 按年看</b>'+esc(x.story)+'</div>';
  /* ★历史对照＝跨公司/跨叙事（2026-08-17 石英股份读者反馈「历史对照不是要和自己历史上对照，而是和历史上其他公司或者其他叙事对照」）。
     本股历史最强段的 R/M/V 同尺度条仍保留在下方（那是 S6 的量纲对照，改名不再叫「历史对照」）；
     这里要的是别家走过同一条路时发生了什么，锚查 13 §6 案例库或 RAG，diff 必填——没有 diff 的对标是装饰不是判据。 */
  var an=x.analog;
  h+='<div class="sc-analog"><b>历史对照 · 跨公司/跨叙事</b>'+
    (an&&(an.case||an.company)
      ?('<span class="an-case">'+esc(an.case||an.company||'')+(an.period?('（'+esc(an.period)+'）'):'')+'</span>'+
        (an.what?('<span class="an-what">'+esc(an.what)+'</span>'):'')+
        (an.diff?('<span class="an-diff">与本例的差异：'+esc(an.diff)+'</span>'):'<span class="rd">缺 diff——没有差异的对标是装饰不是判据（S9）</span>')+
        (an.src?('<span class="muted an-src">'+esc(an.src)+'</span>'):''))
      :'<span class="rd">缺 analog：这条 Case 在别的公司/叙事身上走过什么样的路、多久、多大幅度（S9 不过）</span>')+'</div>';
  var cs=x.catalysts||[];
  h+='<div class="sc-cat"><b>短期催化 · 按季度看</b>'+
    (cs.length?('<ul>'+cs.map(function(c){
      var miss=(!c.when||!c.watch)?' <span class="rd">缺日期或观测量</span>':'';
      return '<li><span class="cat-when">'+esc(c.when||'—')+'</span>'+esc(c.what||'')+
             (c.watch?('<span class="cat-watch">盯：'+esc(c.watch)+'</span>'):'')+
             (c.ref?('<span class="cat-ref">'+esc(c.ref)+'</span>'):'')+miss+'</li>'; }).join('')+'</ul>')
      :'<span class="rd">未填催化，S5 不过</span>')+'</div>';
  if((x.unlock||[]).length) h+='<div class="sc-unlock">'+x.unlock.map(function(u){
    return '<div class="ul-row"><span class="ul-tag '+(UNL_CLS[u.status]||'ul-no')+'">'+esc(u.status||'未发生')+'</span>'+
      esc(u.cond||'')+(u.ev?('<div class="ul-ev">'+esc(String(u.ev).slice(0,140))+'</div>'):'')+'</div>'; }).join('')+'</div>';
  h+='<div class="sc-rmv"><b>涨跌里哪一层出的力</b>'+rmvBar(x.rmv,x.odds,scale,{})+
     /* 尺子跟着数走：那一段若用的是 PB/PS，条上必须写出来，否则这里的 V 与 Case 的 V 会被当成一回事 */
     (hp?('<div class="sc-hist">'+rmvBar(hp.factor_quant,chgPct(hp.chg),scale,{ghost:true,slim:true,
        tag:'本股历史最强段（同尺度）：'+(hp.name||'')
           +(((hp.factor_quant||{}).ruler&&hp.factor_quant.ruler!=='PE')?('　尺子 '+hp.factor_quant.ruler+'（V 层非 PE，勿与其他段直比）'):'')})+'</div>'):'')+
     (x.rmv&&x.rmv.basis?('<div class="sc-basis">口径：'+esc(x.rmv.basis)+'</div>'):'')+
     (x.rmv_check?('<div class="sc-check">'+esc(x.rmv_check)+'</div>'):'')+
     (chk?('<div class="nweak" style="margin-top:8px">'+chk+'</div>'):'')+'</div>';
  return h+'</div>';
}
/* 场景的两条来源矛盾（09 §5.5b：必须 from 指名，否则就是自由创作） */
function scFrom(x){
  var f=x.from||{}, ids={}; ((D.part4||{}).items||[]).forEach(function(i){ ids[i.id]=i; });
  function one(id,dir,tag){
    if(!id) return '<span class="sc-warn">⚠ 缺'+tag+'</span>';
    var it=ids[id];
    return '<span class="sc-src'+(it?'':' bad')+'">'+(it&&isPassive(it)?'■':'●')+' '+
      esc(it?(it.label||id):(id+'(不存在)'))+(dir?('<i>'+esc(dir)+'</i>'):'')+'</span>'; }
  return one(f.active,f.active_dir,'主动')+'<span class="sc-x">×</span>'+one(f.passive,f.passive_dir,'从动');
}
/* 自查：knobs 跑引擎的市值 vs 填写的 mcap_yi/odds；R/M/V 之和 vs odds（09 §5.5d/§5.5e） */
function scCheck(x,base){
  var msgs=[];
  var q=x.rmv||{}, sum=num(q.r_pp)+num(q.m_pp)+num(q.v_pp);
  if(Math.abs(sum-num(x.odds))>3) msgs.push('<b>S4 不过：</b>R/M/V 之和 '+Math.round(sum)+'pp 对赔率 '+Math.round(num(x.odds))+'pp 差 '+Math.round(Math.abs(sum-num(x.odds)))+'pp（>3pp，起终点取数不一致）');
  if(x.knobs){ var r=scenarioRun(x.knobs);
    if(!r) msgs.push('<b>S3 不过：</b>knobs 跑不动引擎');
    else{
      if((r.bad||[]).length) msgs.push('<b>S3 不过：</b>knobs 指到不存在的路径 '+esc(r.bad.join('、')));
      if(r.err) msgs.push('<b>S3 不过：</b>引擎报错 '+esc(r.err));
      else if(isFinite(num(x.mcap_yi))&&num(x.mcap_yi)>0&&isFinite(r.mcap)){
        var d=Math.abs(r.mcap-num(x.mcap_yi))/num(x.mcap_yi);
        if(d>0.01) msgs.push('<b>S3 不过：</b>knobs 实跑市值 '+yi(r.mcap)+'亿 与填写的 '+yi(x.mcap_yi)+'亿 差 '+(Math.round(d*1000)/10)+'%（>1%）');
      }
      if(base>0&&isFinite(r.mcap)){ var o=(r.mcap/base-1)*100;
        if(Math.abs(o-num(x.odds))>1) msgs.push('<b>S3 不过：</b>knobs 实跑赔率 '+Math.round(o)+'% 与填写的 '+Math.round(num(x.odds))+'% 差 >1pp'); }
    } }
  return msgs.join('<br>');
}

var ST_CLS={'已证实':'st-ok','部分证实':'st-half','未证实':'st-no','已证伪':'st-bad'};
function renderContradictionMap(){
  var P4=D.part4; var wrap=el('p4-wrap'); if(!wrap) return;
  if(!P4||!((P4.items||[]).length)){ wrap.style.display='none'; return; }
  wrap.style.display='';
  el('p4-note').innerHTML=(P4.note||'本章不新增分析，只把前三章已有的东西按「还没定」重排一次序。锚的离散度算分歧，滑块弹性加取期敞口算赔率，催化和验证方式算可证伪性。')+
    (P4.asof?(' <span class="muted">（as-of '+esc(P4.asof)+'）</span>'):'')+cite(P4.cite);
  var nars=P4.narratives||[];
  // ---- 索引先建（4.1/4.2 要用），再按 4.1→4.4 顺序渲 ----
  var core=P4.core||{}, byId={}; (P4.items||[]).forEach(function(it){ byId[it.id]=it; });
  nars.forEach(function(n){ (n.subs||[]).forEach(function(it){ if(!byId[it.id]) byId[it.id]=it; }); });

  // 4.1 场景（09 §5.5）：结果先行——哪几个场景涨/跌、靠什么解锁、赔率与 R/M/V 构成
  renderScenarios();

  // ---- 4.2 核心矛盾（双槽位）：两条各占一级，不并排压成一格 ----
  function card(no,k,slot,hd,ask){ var it=byId[(slot||{}).id]||{};
    return hd3(no,hd,ask)+'<div class="core-card '+k+'">'+
      '<div class="cc-ttl">'+esc(it.label||(slot||{}).id||'未指定')+
      (it.odds!=null?(' <span class="muted" style="font-size:12.5px">赔率 '+num(it.odds)+'% · 可证伪 '+num(it.F)+' · 分歧 '+num(it.D)+
        (it.role?(' · '+esc(it.role)):'')+'</span>'):'')+'</div>'+
      '<div class="cc-why">'+((slot||{}).why?('<span class="hl">'+esc(slot.why)+'</span>'):'<span class="rd">未写为什么是它</span>')+'</div>'+
      '<div class="cc-act">动作：<b>'+((slot||{}).action?esc(slot.action):'<span class="rd">未写</span>')+'</b></div></div>'; }
  var same=core.pricing&&core.actionable&&core.pricing.id===core.actionable.id;
  el('cmap-core').innerHTML=
    card('4.3.1','pricing',core.pricing||{},'定价核心矛盾 · 为什么值这个价',
      '这一节回答：这只票现在的价格是被哪一条撑着。它通常验不了，所以动作是控仓位、要折价，不是研究。')+
    card('4.3.2','actionable',core.actionable||{},'可操作核心矛盾 · 这季度盯什么',
      '这一节回答：接下来一个季度，把研究预算花在哪。它必须是能在持有期内拿到数的那一条。')+
    (same?'<div class="nweak" style="margin-top:10px"><b class="rd">CK-6e 不过：</b>两个槽位指向同一条矛盾。实证表明赔率与可证伪性负相关，两条结构性地不应是同一条。</div>':'')+
    ((!core.pricing||!core.actionable)?'<div class="nweak" style="margin-top:10px"><b class="rd">CK-6e 不过：</b>双槽位缺一。</div>':'');

  // ---- 4.3 核心矛盾深度研究 ----
  var deepHost=el('cmap-deep');
  if(deepHost){
    var dhtml=renderDeepDive('4.4.1','pricing',core.pricing||{},byId[(core.pricing||{}).id]||{},'定价核心矛盾 · 深度研究')+
              renderDeepDive('4.4.2','actionable',core.actionable||{},byId[(core.actionable||{}).id]||{},'可操作核心矛盾 · 深度研究');
    deepHost.innerHTML=dhtml||'<p class="cap"><span class="rd">两条核心矛盾都没填 <code>core.*.deepdive</code></span>，CK-6 D1 不过。这一节要给：怎么理解、市面上有哪些解决方案、落地跟踪方案、判定表、判定时点、历史对标。</p>';
  }

  // ---- 4.1 矛盾坐标（2026-08-14 提到章首：4.2.1 覆盖表写「4.1 那 N 条」，图必须在它上面）----
  el('cmap-svg').innerHTML=hd3('4.1.1','三坐标 · 哪几条既有人吵又能验',
      '这一节回答：'+(P4.items||[]).length+' 条矛盾里，研究预算该押在哪个象限。可证伪高且分歧高＝对手盘区，值得押；分歧高但验不了，只能控仓位。')+
    cmapStrip(P4.items,{})+
    '<details class="fold cmap-fold"><summary>展开三坐标气泡图（横轴可证伪 · 纵轴分歧 · 面积∝赔率 · ●主动 ■从动）</summary>'+
    cmapSVG(P4.items,{})+cmapLegend(P4.items)+'</details>'+roleGateNote(P4.items);
  el('cmap-table').innerHTML=hd3('4.1.2','明细表 · 每条的分歧口径与验证方式',
      '这一节回答：图上每个记号背后，各家给的数是什么、极差多少、我打算怎么验。')+
    cmapTable(P4.items);

  // ---- 4.5 叙事链 · 次级矛盾：一条叙事一级编号 ----
  var host=el('cmap-narratives');
  host.innerHTML=nars.length?nars.map(function(n,ni){
    var no='4.5.'+(ni+1);
    var h='<div id="nar-'+esc(n.key||'')+'"></div>'+
      hd3(no,esc(n.name||n.key||'叙事'),
        '这一节回答：这条叙事从外部驱动到公司利润，每一环证实到什么程度，最先断的会是哪一环。');
    h+='<div class="nchain">'+(n.chain||[]).map(function(c){
        return '<div class="ns"><span class="no">'+num(c.step)+'</span>'+
          '<span class="st '+(ST_CLS[c.status]||'st-no')+'">'+esc(c.status||'未证实')+'</span>'+
          '<span>'+esc(c.claim||'')+(c.ev?('<br><span class="muted" style="font-size:11.5px">原句：'+esc(String(c.ev).slice(0,120))+'</span>'):'')+'</span></div>';
      }).join('')+'</div>';
    h+=n.weakest?('<div class="nweak"><b>最先断的一环：</b><span class="hl">'+esc(n.weakest)+'</span></div>')
                :'<div class="nweak"><b class="rd">未写最先断的一环，CK-6f 不过。</b></div>';
    if((n.subs||[]).length){
      /* ★2026-08-18 用户要求：4.5 不再画图。原来这里渲三坐标条 + 子坐标系气泡图，
         轴与 4.1 完全相同，但一条叙事内部只有 3–5 个点——坐标系画出来点太稀、
         两根轴的含义还要再解释一遍，读者拿不到任何 4.1 没给过的东西，纯占版面。
         次级矛盾本来就是**逐条要读的清单**，清单形态是表，不是散点。 */
      h+='<p class="ask">这条链上还没定的 '+n.subs.length+' 条，逐条列在下表；口径与 4.1.2 明细表相同。</p>';
      h+='<div class="panel" style="margin-top:8px">'+cmapTable(n.subs)+'</div>'; }
    return h; }).join(''):'<p class="cap"><span class="rd">未填 part4.narratives</span>，CK-6f 不过。</p>';

  tocPart4();
}

/* 第四章的三级标题是运行时渲的，静态 TOC 列不出来——渲完扫一遍补进左边栏。
   4.5.N 条数随叙事条数变，所以只能动态建，不能写死。 */
function tocPart4(){
  var toc=document.getElementById('toc'), wrap=el('p4-wrap');
  if(!toc||!wrap||!wrap.querySelectorAll||!toc.querySelectorAll) return;
  [].slice.call(toc.querySelectorAll('a[data-p4]')).forEach(function(n){ n.parentNode.removeChild(n); });
  var SEC=[['4.1','#sec-cmap'],['4.2','#sec-cscen'],['4.3','#sec-ccore'],['4.4','#sec-cdeep'],['4.5','#sec-cnar']];
  var groups={};
  [].slice.call(wrap.querySelectorAll('h3.n3')).forEach(function(h){
    var noEl=h.querySelector&&h.querySelector('.no'); if(!noEl) return;
    var no=(noEl.textContent||'').trim(); if(!no) return;
    var top=no.split('.').slice(0,2).join('.');
    var txt=(h.textContent||'').replace(no,'').trim();
    (groups[top]=groups[top]||[]).push({no:no,txt:txt,id:h.id||''});
  });
  SEC.forEach(function(p){
    var anchor=toc.querySelector('a[href="'+p[1]+'"]'); if(!anchor) return;
    var ref=anchor.nextSibling;
    (groups[p[0]]||[]).forEach(function(x){
      var a=document.createElement('a'); a.className='l3'; a.setAttribute('data-p4','1');
      a.href='#'+x.id;
      var t=x.txt.split('·')[0].trim();                 // 只留主干，副标题不进目录
      a.textContent=x.no+' '+(t.length>13?t.slice(0,13)+'…':t);
      toc.insertBefore(a,ref);
    });
  });
}

/* ==== 开篇章 · 一段话说清楚（references/10） ================================
 * 第四点三块（页面标题只能用这三个词，不许写「反算」）：
 *   利润兑现期限 —— 现价按正常 PE 兑现到了哪一年的利润（随假设滑块实时联动）
 *   估值范式上界 —— 再要弹性得换什么范式，各档能给到多少
 *   潜在催化     —— 切换范式要什么事发生，含向下路径 */
var SUMTAG={FACT:'tg-FACT',EST:'tg-EST',DNA:'tg-DNA'};
var LAD_ST={'成立':'st-live','待验':'st-wait','不成立':'st-no2'};

function backsolve(pl){
  var B=(D.summary||{}).backsolve||{}, v=MODEL.valuation||{}, M=D.meta||{};
  var mcap0=num(v.current_mcap_yi,num(M.current_mcap_yi,0));
  // 利润序列：优先第三章模型（→随滑块动），缺模型才用 backsolve.profits 手填
  var all=[],src='第三章模型（随滑块联动）';
  if(pl&&pl.byYear&&pl.byYear.length){        // ⚠️ 引擎字段名是 netProfit（不是 np），year 形如 '2027E'
    pl.byYear.forEach(function(r){ if(isFinite(r.netProfit)) all.push({year:parseInt(r.year,10),np:r.netProfit,f:!!r.isForecast}); }); }
  if(!all.length&&(B.profits||[]).length){ src='summary.backsolve.profits 手填';
    all=B.profits.map(function(p){ return {year:parseInt(p.year,10),np:num(p.np_yi),f:true}; }); }
  var pe=num(B.anchor_pe,num(((v.paradigms||[]).filter(function(p){return p.key==='pe';})[0]||{}).params&&
        ((v.paradigms||[]).filter(function(p){return p.key==='pe';})[0]).params.pe,0));
  var r=num(B.r,0.09);   // ★折现率统一 8–10% 档（2026-08-12），缺省取中值 9%
  var base=parseInt(String(B.base_year||M.asof||'').slice(0,4),10);
  if(!isFinite(base)){ var h=all.filter(function(x){return !x.f;}); base=h.length?h[h.length-1].year:(all[0]||{}).year; }
  var implied=(pe>0)?mcap0/pe:null;                       // 市场已经认下的利润体量
  // 落点主要在【预测】曲线上找。强周期股的历史峰值常高于 implied（京东方 2021 归母 258 亿
  // > implied 150 亿），若无差别扫全序列会被判回 2021 并同时报「超出预测期末年」，自相矛盾。
  var fc=all.filter(function(x){return x.f;}); if(!fc.length) fc=all;
  var hist=all.filter(function(x){return !x.f;});
  // ★2026-08-14：implied 低于预测首年时不再钳在首年——那是把「市场一分钱未来都没付」
  //   这个结论压成了模型伪影。阳光实测 implied 136.1 亿落在 2025 实际 134.6 与 2026E 141.8
  //   之间，引擎只能吐 2026.0，作者被迫手写一段 ⚠️ 文字解释。现在让它落进历史年。
  //   只回溯历史的【单调上行尾巴】，周期股的旧峰值不参与，原来那个顾虑仍然被挡住。
  var tail=[];
  for(var t=hist.length-1;t>=0;t--){ tail.unshift(hist[t]);
    if(t>0&&hist[t-1].np>hist[t].np) break; }              // 再往前利润更高＝进了旧周期，停
  var hit=null,pos=null,inHist=false,belowHist=null;
  if(implied!=null&&fc.length){
    if(implied<=fc[0].np){
      var seq=tail.concat([fc[0]]);                        // 历史上行尾巴 + 预测首年，连续插值
      if(seq.length<2||implied>=seq[seq.length-2].np){
        var a=seq[seq.length-2]||fc[0], b=fc[0], dd=b.np-a.np;
        if(seq.length<2||!isFinite(dd)||dd<=0){ hit=fc[0].year; pos=0; }
        else { var f0=(implied-a.np)/dd; hit=a.year+f0*(b.year-a.year); pos=-(1-f0); inHist=true; }
      } else if(implied<seq[0].np){
        hit=seq[0].year; pos=-(seq.length-1); inHist=true;
        belowHist=implied/seq[0].np-1;                     // 连历史上行段起点都够不到
      } else { for(var k=0;k<seq.length-1;k++){
          if(seq[k].np<=implied&&implied<seq[k+1].np){
            var dk=seq[k+1].np-seq[k].np, fk=dk?(implied-seq[k].np)/dk:0;
            hit=seq[k].year+fk*(seq[k+1].year-seq[k].year);
            pos=-(seq.length-1-k-fk); inHist=true; break; } } }
    }
    else if(implied>=fc[fc.length-1].np){ hit=fc[fc.length-1].year; pos=fc.length-1; }
    else { for(var i=0;i<fc.length-1;i++){
        if(fc[i].np<=implied&&implied<fc[i+1].np){
          var d=fc[i+1].np-fc[i].np, fr=d?(implied-fc[i].np)/d:0;
          pos=i+fr; hit=fc[i].year+fr*(fc[i+1].year-fc[i].year); break; } } }
  }
  var beyond=(implied!=null&&fc.length&&implied>fc[fc.length-1].np)
      ? (implied/fc[fc.length-1].np-1) : null;            // 超出预测期末年多少
  var rows=all.filter(function(x){return x.f;}).map(function(x){
    var n=Math.max(0,x.year-base), tgt=x.np*pe, dis=tgt/Math.pow(1+r,n);
    return {year:x.year,np:x.np,n:n,pe_now:x.np?mcap0/x.np:null,tgt:tgt,dis:dis,
            odds:mcap0?dis/mcap0-1:null}; });
  return {mcap0:mcap0,pe:pe,r:r,base:base,implied:implied,hit:hit,pos:pos,beyond:beyond,
          inHist:inHist,belowHist:belowHist,lastActual:hist.length?hist[hist.length-1]:null,
          all:all,rows:rows,src:src,note:B.note,basis:B.anchor_pe_basis};
}

var CN3=['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩'];
function sn(no,txt,lv){ return '<div class="sum-i'+lv+'"><span class="sum-no">'+no+'</span> '+txt+'</div>'; }
function tg(t){ return t?('<span class="sum-tg">【'+esc(t)+'】</span>'):''; }
function evs(a){ return (a||[]).map(function(id){ return '<sup class="evref" data-ev="'+esc(id)+'">['+esc(id)+']</sup>'; }).join(''); }

function renderSummary(pl){
  var SUM=D.summary||{}, wrap=el('sum-wrap'); if(!wrap) return;
  var has=(SUM.thesis||(SUM.pillars||[]).length||(SUM.company_type||[]).length);
  if(!has){ wrap.style.display='none'; return; }
  wrap.style.display='';
  // 开篇章导语（「本章不新增分析…」）＝元叙述，不渲；as-of 已在概览给过。
  var nt=el('sum-note'); if(nt){ nt.innerHTML=''; nt.style.display='none'; }

  // ---- 第一点 公司类型 ----
  // 新契约：每条＝一个结论(title) + 若干 (k,v) 子项；旧契约 {label,note} 仍兼容
  /* ★2026-08-14：旧契约 {label,note} 不再静默降级。阳光 v3.1 掉回散文块，
     14 个 (k,v) 子项 / 14 处 FACT-EST-DNA 分层 / 2 处 ev 全部归零，而 CK-7 只查「恰好 3 条」——
     3 个散文块和 3 个结构块一样过闸。丢的是 k 那一列的提问框架（10 §2.2）。 */
  var legacyCT=(SUM.company_type||[]).filter(function(x){ return !x.points&&(x.label||x.note); }).length;
  var t1=(SUM.company_type||[]).map(function(x,i){
    if(!x.points&&!x.title) return sn((i+1)+'.', '<span class="sum-key">'+esc(x.label||x)+'</span>'+
      (x.note?('——<span class="sum-note">'+esc(x.note)+'</span>'):''), 1);
    var h=sn((i+1)+'.', '<span class="sum-key">'+esc(x.title||x.label||'')+'</span>'+
      (x.verdict?('——'+esc(x.verdict)):''), 1);
    h+=(x.points||[]).map(function(pt,j){
      return sn('('+(j+1)+')', (pt.k?('<b>'+esc(pt.k)+'</b>　'):'')+esc(pt.v||pt)+
        (pt.tag?tg(pt.tag):'')+evs(pt.ev), 2); }).join('');
    return h; }).join('');
  el('sum-type').innerHTML=(t1?(t1+(legacyCT?('<div class="nweak"><b class="rd">CK-7 b1 不过：</b>'+
      legacyCT+'/'+(SUM.company_type||[]).length+' 条 <code>company_type</code> 用的是已废弃的旧契约 '+
      '<code>{label,note}</code>——散文块没有 (k,v) 子项，'+
      '「收入怎么来／壁垒在哪／单价涨的是价还是结构／什么情况下生意好但报表不好」这几问可以被绕过而看不出来，'+
      'FACT/EST/DNA 分层与 ev 原句也挂不上。改成 <code>{title,points:[{k,v,tag,ev}]}</code>，'+
      '跑 <code>node scripts/check_summary.js</code> 验（10 §2.2 / §7 b1）。</div>'):''))
    :'<p class="cap">⚠️ 未填 summary.company_type（CK-7 b1）</p>');

  // ---- 第二点 核心投资逻辑 ----
  var t2='<div class="sum-lead">'+esc(SUM.thesis||'⚠️ 未填 summary.thesis')+'</div>';
  function pts(list,lv){ return (list||[]).map(function(p,j){
      var no=(lv===2)?('('+(j+1)+')'):(CN3[j]||'·');
      var h=sn(no, esc(p.claim||p)+tg(p.tag)+evs(p.ev), lv);
      if((p.subs||[]).length) h+=p.subs.map(function(x,k){ return sn(CN3[k]||'·', esc(x), 3); }).join('');
      return h; }).join(''); }
  (SUM.pillars||[]).forEach(function(pi,i){
    t2+=sn((i+1)+'.', '<span class="sum-key">'+esc(pi.name||pi.key||'')+'</span>', 1);
    t2+=pts(pi.points,2);
    (pi.subs||[]).forEach(function(sb,si){
      t2+=sn('('+((pi.points||[]).length+si+1)+')', '<span class="sum-key">'+esc(sb.name||'')+'</span>', 2);
      t2+=pts(sb.points,3); });
  });
  if(!(SUM.pillars||[]).length) t2+='<p class="cap">⚠️ 未填 summary.pillars（需求/供给/公司 三层论证，CK-7 c1）</p>';
  el('sum-logic').innerHTML=t2;

  // ---- 第三点 算账 ----
  var A=SUM.accounting||{}, bs=backsolve(pl), t3='', n=0;
  if((A.mcap_split||[]).length){
    t3+=sn((++n)+'.', '当前市值 <span class="sum-key">'+yi(bs.mcap0)+' 亿</span>拆成几块：',1);
    t3+=A.mcap_split.map(function(m,j){ return sn('('+(j+1)+')',
      esc(m.part||'')+' <span class="sum-key">'+yi(m.yi)+' 亿</span>'+
      (m.basis?('——<span class="sum-note">'+esc(m.basis)+'</span>'):''), 2); }).join(''); }
  (A.steps||(A.scenarios?[{name:'情景分档',scenarios:A.scenarios}]:[])).forEach(function(st){
    t3+=sn((++n)+'.', '<span class="sum-key">'+esc(st.name||'情景分档')+'</span>'+
      (st.note?('——<span class="sum-note">'+esc(st.note)+'</span>'):''), 1);
    t3+=(st.scenarios||[]).map(function(sc,j){
      /* ★2026-08-14：stake 只认数字（持股比例）。阳光 v3.1 把它当标签用（填"储能"/"AIDC"），
         页面渲出 9 处「持股 —」；一旦不填 attrib_yi 就会 profit_yi×"储能"=NaN 静默错。
         想标「这一步算的是哪一段」用 segment 字段；stake 非数字时按 segment 兜底处理。 */
      var stk=isFinite(parseFloat(sc.stake))?num(sc.stake):null;
      var seg=sc.segment||((stk==null&&sc.stake!=null)?String(sc.stake):'');
      var att=(sc.attrib_yi!=null)?sc.attrib_yi:(stk!=null?num(sc.profit_yi)*stk:null);
      return sn('('+(j+1)+')', '<span class="sum-key">'+esc(sc.name||'')+'</span>：'+esc(sc.driver||'')+
        '，对应利润 <span class="sum-key">'+yi(sc.profit_yi)+' 亿</span>'+
        (att!=null?('（'+(stk!=null?('持股 '+pct(stk,0)+'，'):(seg?esc(seg)+'段，':''))+'归母 <span class="sum-key">'+yi(att)+' 亿</span>）'):''), 2); }).join(''); });
  if(A.conclusion) t3+=sn((++n)+'.', '<span class="sum-key">结论：</span>'+esc(A.conclusion), 1);
  // ★2026-08-16 price_assumes：现价把什么当成了既成事实（10 §4）——读者要知道自己在赌哪几件事
  if(A.price_assumes) t3+=sn((++n)+'.', '<span class="sum-key">现价已经当成既成事实的：</span>'+esc(A.price_assumes), 1);
  el('sum-acct').innerHTML=t3||'<p class="cap">⚠️ 未填 summary.accounting（CK-7 d）</p>';

  // ---- 第四点 a 利润兑现期限（活：随第三章滑块联动） ----
  var b1='';
  if(!bs.pe){ b1='<p class="cap">⚠️ 未给正常 PE 档（<code>summary.backsolve.anchor_pe</code> 或 part3 的 pe 范式），利润兑现期限无法计算。</p>'; }
  else{
    var k=0;
    b1+=sn((++k)+'.', '现价 <span class="sum-key">'+yi(bs.mcap0)+' 亿</span> ÷ 正常 <span class="sum-key">'+num(bs.pe)+
      '×</span> PE ＝ 市场已经认下 <span class="sum-key">'+yi(bs.implied)+' 亿</span>归母。',1);
    b1+=sn((++k)+'.', (bs.hit!=null
        ? ('把这 '+yi(bs.implied)+' 亿放到利润曲线上，落点在 <span class="sum-key">'+bs.hit.toFixed(1)+
           ' 年</span>——即<span class="sum-key">现价兑现的是 '+Math.round(bs.hit)+' 年的利润</span>。'
           /* ★2026-08-14：落点可以落进历史年。以前钳在预测首年，把「市场一分钱未来都没付」
              压成了模型伪影，作者只能在 anchor_pe_basis 里手写一段 ⚠️ 文字解释。 */
           +(bs.inHist?('<b class="sum-key">落点在历史段</b>：市场认下的利润还停在'
              +(bs.lastActual?(' '+bs.lastActual.year+' 年已经赚到的那个水平（'+yi(bs.lastActual.np)+' 亿）'):'历史区间内')
              +'，<b>一分钱未来都没付</b>。'
              +(bs.belowHist!=null?('而且还比历史上行段的起点低 '+pct(-bs.belowHist,0)+'——现价连过去几年已实现的利润都没认全。'):'')):''))
        : '利润序列不足，无法定位兑现年份。')+
      (bs.beyond!=null?('它已经<span class="sum-key">超出预测期末年 '+pct(bs.beyond,0)+
        '</span>，即模型给的全部预测利润都不够解释现价，缺口只能靠换范式或上修假设填。'):''),1);
    b1+=sn((++k)+'.', '逐年看：',1)+
      '<table class="sum-tb"><tr><th>兑现到</th><th>归母(亿)</th><th>现价隐含PE</th>'+
      '<th>该年目标市值(亿)</th><th>折现回今日(亿)</th><th>相对现价赔率</th></tr>'+
      bs.rows.map(function(x){ var isHit=(bs.hit!=null&&Math.round(bs.hit)===x.year);
        return '<tr class="'+(isHit?'hit':'')+'"><td>'+x.year+(isHit?'（现价在此）':'')+'</td><td>'+yi(x.np)+'</td>'+
          '<td>'+(x.pe_now!=null?(Math.round(x.pe_now*10)/10+'×'):'—')+'</td><td>'+yi(x.tgt)+'</td><td>'+yi(x.dis)+'</td>'+
          '<td>'+spct(x.odds,0)+'</td></tr>'; }).join('')+'</table>';
    b1+=sn((++k)+'.', '读法：现价隐含 PE 越靠后越低，就是越需要等；赔率转正的那一年之前，'+
      '<span class="sum-key">买入靠的是估值扩张而不是业绩</span>。',1);
    b1+='<div class="sum-fn">口径：PE 档依据——'+esc(bs.basis||'⚠️未写为什么用这个 PE')+
      '；利润序列来自'+esc(bs.src)+'；折现率 '+pct(bs.r,0)+'，基准年 '+bs.base+'。'+
      (bs.note?('<br>'+esc(bs.note)):'')+'</div>';
  }
  el('sum-bs1').innerHTML=b1;

  // ---- 第四点 b 估值范式上界 ----
  var B=SUM.backsolve||{}, live={};
  try{ (EONE.runValuation(MODEL.valuation||{},pl).rows||[]).forEach(function(rw){ live[rw.key]=rw.mcap; }); }catch(_){}
  // ★本节叫「上界」：**给不出正赔率的档整条不渲**（不是只删数字）——
  //   低于现价的范式说明的是「这档托不住现价」，属下行论证，归第四点c 的 kill/向下催化，
  //   放在这里只会稀释结论。被隐去的档只在末尾给一个计数，保证与第三章八范式对得上。
  var ladAll=(B.ladder||[]), t5='', hidden=[];
  var lad=ladAll.filter(function(L){
    var c=(L.mcap_yi!=null)?num(L.mcap_yi):(isFinite(live[L.key])?live[L.key]:null);
    var f=(L.mcap_if_yi!=null)?num(L.mcap_if_yi):null;
    var okc=(bs.mcap0&&c!=null&&c/bs.mcap0-1>=0), okf=(bs.mcap0&&f!=null&&f/bs.mcap0-1>=0);
    if(okc||okf) return true;
    hidden.push(L.name||L.key||''); return false; });
  lad.forEach(function(L,i){
    var cap=(L.mcap_yi!=null)?num(L.mcap_yi):(isFinite(live[L.key])?live[L.key]:null);
    var up=(bs.mcap0&&cap!=null)?(cap/bs.mcap0-1):null;
    var ifc=(L.mcap_if_yi!=null)?num(L.mcap_if_yi):null;
    var ifup=(bs.mcap0&&ifc!=null)?(ifc/bs.mcap0-1):null;
    t5+=sn((i+1)+'.', (L.tier?('<span class="sum-tier">第'+('一二三四五'[L.tier-1]||L.tier)+'档</span>'):'')+
      '<span class="sum-key">'+esc(L.name||L.key||'')+'</span>（'+esc(L.status||'待验')+
      (L.current?'·当前市场用的就是这档':'')+'）',1);
    var j=0;
    t5+=sn('('+(++j)+')', '适用前提：'+esc(L.precond||'⚠️未写'),2);
    if(cap!=null&&up!=null&&up>=0)
      t5+=sn('('+(++j)+')', '现参数下：<span class="sum-key">'+yi(cap)+' 亿</span>（较现价 '+spct(up,0)+'）',2);
    // 与现参数读数几乎相等时不重复渲一行（差<2% 没信息量，只是噪音）
    if(ifc!=null&&!(cap&&Math.abs(ifc/cap-1)<0.02)&&!(ifup!=null&&ifup<0))
      t5+=sn('('+(++j)+')', '前提成立后可到：<span class="sum-key">'+yi(ifc)+' 亿</span>'+
      (ifup!=null?('（较现价 '+spct(ifup,0)+'）'):'')+(L.if_basis?('——<span class="sum-note">'+esc(L.if_basis)+'</span>'):''),2);
    if(L.gap) t5+=sn('('+(++j)+')', '差什么：'+esc(L.gap),2);
    if(L.note) t5+=sn('('+(++j)+')', esc(L.note),2);
  });
  var fn5='<div class="sum-fn">本节只列<b>能够到现价以上</b>的范式，自上而下＝五档估值等级从低档到高档（第一档 PB/重置 → 第二档 静态/Forward PE → 第三档 PEG → 第四档 远期利润/PS → 第五档 终局/对标大哥）：越往下档位越高、前提越强，一旦证伪回撤也越快。'+
      '读数能挂上第三章范式的取实时联动值（随滑块动）。'+
      (hidden.length?('　（另有 '+hidden.length+' 档在现参数下低于现价、够不到上界，已隐去。）'):'')+'</div>';
  el('sum-bs2').innerHTML=(!ladAll.length)?'<p class="cap">⚠️ 未填 summary.backsolve.ladder（CK-7 e2）</p>'
    :(t5? (t5+fn5)
        : ('<div class="sum-i1"><span class="sum-no">1.</span> <span class="sum-key">当前参数下没有任何估值范式能给出高于现价的市值</span>'+
           '——'+esc(ladAll.length)+' 档全部落在现价之下。这不是"没算出来"，而是本身就是结论：'+
           '现价已经越过了所有可用范式在当前假设下的上沿，再往上只能靠上修假设或市场换一套定价逻辑。</div>'+fn5));

  // ---- 第四点 c 潜在催化 ----
  var sw=(B.switches||[]), t6='';
  sw.forEach(function(w,i){
    t6+=sn((i+1)+'.', '<span class="sum-key">'+esc(w.from||'')+' → '+esc(w.to||'')+'</span>'+
      (w.prob!=null?('（主观概率 '+pct(w.prob,0)+'）'):''),1);
    var j=0;
    t6+=sn('('+(++j)+')', '催化是什么：'+esc(w.catalyst||'⚠️未写'),2);
    t6+=sn('('+(++j)+')', '盯哪个指标：'+esc(w.watch||'⚠️未写'),2);
    t6+=sn('('+(++j)+')', '大概什么时候：'+esc(w.when||'⚠️未写'),2);
    if(w.elasticity) t6+=sn('('+(++j)+')', '切过去的弹性：'+esc(w.elasticity),2);
    if(w.kill) t6+=sn('('+(++j)+')', '反向：'+esc(w.kill),2);
  });
  el('sum-bs3').innerHTML=t6||'<p class="cap">⚠️ 未填 summary.backsolve.switches（CK-7 f1）</p>';
}

/* 文本版导出：与页面同一套编号（第一点…第四点 / 1. / (1) / ①），可直接粘进 IM / IC memo */
function summaryText(){
  var SUM=D.summary||{}, M=D.meta||{}, pl=EONE.recomputePL(MODEL), bs=backsolve(pl), L=[];
  var live={};   // 阶梯里没手填市值的档，取第三章范式的实时值（与页面同源）
  try{ (EONE.runValuation(MODEL.valuation||{},pl).rows||[]).forEach(function(rw){ live[rw.key]=rw.mcap; }); }catch(_){}
  var CN=['一','二','三','四'];
  function P(x){ L.push(x); }
  P((M.name||'')+' '+(M.ticker||'')+'　当前市值 '+yi(bs.mcap0)+' 亿'+(M.asof?('　as-of '+M.asof):''));
  var TC=SUM.type_card; if(TC){ var tb=(TC.core_lines&&TC.core_lines.length)?TC.core_lines:((TC.beta||{}).lines||[]).slice(0,3);
    P('公司类型：'+(TC.type||('未定（建议 '+(TC.suggest||'—')+'）'))+(TC.verdict?('　'+TC.verdict):(TC.basis?('　依据：'+TC.basis):'')));
    if(tb.length) P('  核心叙事线：'+tb.map(function(l){ return (l.name||'')+(l.tier?('·'+l.tier):'')+'（β '+(l.beta!=null?l.beta:'—')+' R² '+(l.r2!=null?l.r2:'—')+(l.share_pct!=null?('，占 '+l.share_pct+'%'+(l.rank?(' 排 '+l.rank+'/'+l.of):'')):'')+(l.turnover_pct!=null?('，换手 '+Math.round(l.turnover_pct)+' 分位'):'')+'）'; }).join('；'));
    var TP=(TC.beta||{}).posture; if(TP&&TP.label) P('  K 线方位：'+TP.label);
    var TS=TC.sigma||{}, tnm=TS.nm||{}, troe=TS.roe||{};
    P('  σ 面：预期净利率 '+(tnm.fwd!=null?(tnm.fwd+'%（历史 '+(tnm.pct_fwd!=null?tnm.pct_fwd:'—')+' 分位）'):'—')+'；ROE '+(troe.now!=null?(troe.now+'%（历史 '+(troe.pct!=null?troe.pct:'—')+' 分位）'):'—')+
      ['pe','ps','pb'].map(function(k){ var o=TS[k]||{}; return o.now==null?'':('；'+k.toUpperCase()+' '+o.now+'x（窗口 '+(o.pct!=null?o.pct:'—')+' 分位）'); }).join('')); }
  P('');

  P('第'+CN[0]+'点　公司类型');
  (SUM.company_type||[]).forEach(function(t,i){
    if(!t.points&&!t.title){ P('  '+(i+1)+'. '+(t.label||t)+(t.note?('——'+t.note):'')); return; }
    P('  '+(i+1)+'. '+(t.title||t.label||'')+(t.verdict?('——'+t.verdict):''));
    (t.points||[]).forEach(function(pt,j){ P('    ('+(j+1)+') '+(pt.k?(pt.k+'　'):'')+(pt.v||pt)+(pt.tag?('【'+pt.tag+'】'):'')); }); });
  P('');

  P('第'+CN[1]+'点　核心投资逻辑：'+(SUM.thesis||''));
  (SUM.pillars||[]).forEach(function(p,i){
    P('  '+(i+1)+'. '+(p.name||p.key||''));
    (p.points||[]).forEach(function(pt,j){
      P('    ('+(j+1)+') '+(pt.claim||pt)+(pt.tag?('【'+pt.tag+'】'):''));
      (pt.subs||[]).forEach(function(x,k){ P('        '+(k+1)+') '+x); }); });
    (p.subs||[]).forEach(function(sb,si){
      P('    ('+((p.points||[]).length+si+1)+') '+(sb.name||''));
      (sb.points||[]).forEach(function(pt,k){ P('        '+(k+1)+') '+(pt.claim||pt)+(pt.tag?('【'+pt.tag+'】'):'')); }); }); });
  P('');

  var A=SUM.accounting||{}, n=0;
  P('第'+CN[2]+'点　算账');
  if((A.mcap_split||[]).length){
    P('  '+(++n)+'. 当前市值 '+yi(bs.mcap0)+' 亿拆成几块：');
    A.mcap_split.forEach(function(m,i){ P('    ('+(i+1)+') '+m.part+' '+yi(m.yi)+' 亿'+(m.basis?('——'+m.basis):'')); }); }
  (A.steps||(A.scenarios?[{name:'情景分档',scenarios:A.scenarios}]:[])).forEach(function(st){
    P('  '+(++n)+'. '+(st.name||'情景分档')+(st.note?('——'+st.note):''));
    (st.scenarios||[]).forEach(function(sc,j){
      /* ★2026-08-14：stake 只认数字（持股比例）。阳光 v3.1 把它当标签用（填"储能"/"AIDC"），
         页面渲出 9 处「持股 —」；一旦不填 attrib_yi 就会 profit_yi×"储能"=NaN 静默错。
         想标「这一步算的是哪一段」用 segment 字段；stake 非数字时按 segment 兜底处理。 */
      var stk=isFinite(parseFloat(sc.stake))?num(sc.stake):null;
      var seg=sc.segment||((stk==null&&sc.stake!=null)?String(sc.stake):'');
      var att=(sc.attrib_yi!=null)?sc.attrib_yi:(stk!=null?num(sc.profit_yi)*stk:null);
      P('    ('+(j+1)+') '+sc.name+'：'+(sc.driver||'')+'，对应利润 '+yi(sc.profit_yi)+' 亿'+
        (att!=null?('（'+(stk!=null?('持股 '+pct(stk,0)+'，'):(seg?seg+'段，':''))+'归母 '+yi(att)+' 亿）'):'')); }); });
  if(A.conclusion) P('  '+(++n)+'. 结论：'+A.conclusion);
  if(A.price_assumes) P('  '+(++n)+'. 现价已经当成既成事实的：'+A.price_assumes);
  P('');

  P('第'+CN[3]+'点　利润兑现期限 · 估值范式上界 · 潜在催化');
  P('');
  P('  【利润兑现期限】');
  if(bs.pe){ var k=0;
    P('  '+(++k)+'. 现价 '+yi(bs.mcap0)+' 亿 ÷ 正常 '+num(bs.pe)+'× PE ＝ 市场已经认下 '+yi(bs.implied)+' 亿归母。');
    P('  '+(++k)+'. '+(bs.hit!=null
        ? ('把这 '+yi(bs.implied)+' 亿放到利润曲线上，落点在 '+bs.hit.toFixed(1)+' 年——即现价兑现的是 '+Math.round(bs.hit)+' 年的利润。'
           +(bs.inHist?('落点在历史段：市场认下的利润还停在'
              +(bs.lastActual?(' '+bs.lastActual.year+' 年已经赚到的那个水平（'+yi(bs.lastActual.np)+' 亿）'):'历史区间内')
              +'，一分钱未来都没付。'
              +(bs.belowHist!=null?('而且还比历史上行段的起点低 '+pct(-bs.belowHist,0)+'。'):'')):''))
        : '利润序列不足，无法定位兑现年份。')+
      (bs.beyond!=null?('它已经超出预测期末年 '+pct(bs.beyond,0)+'，即模型给的全部预测利润都不够解释现价，缺口只能靠换范式或上修假设填。'):''));
    P('  '+(++k)+'. 逐年看：');
    bs.rows.forEach(function(x,j){ P('    ('+(j+1)+') '+x.year+' 年：归母 '+yi(x.np)+' 亿，现价隐含 '+
      (x.pe_now!=null?(Math.round(x.pe_now*10)/10+'×'):'—')+'，该年目标市值 '+yi(x.tgt)+' 亿，折现回今日 '+yi(x.dis)+
      ' 亿，赔率 '+spct(x.odds,0)+(bs.hit!=null&&Math.round(bs.hit)===x.year?'　←现价在此':'')); });
    P('  '+(++k)+'. 读法：现价隐含 PE 越靠后越低，就是越需要等；赔率转正的那一年之前，买入靠的是估值扩张而不是业绩。');
    P('     口径：PE 档依据——'+(bs.basis||'—')+'；利润序列来自'+bs.src+'；折现率 '+pct(bs.r,0)+'，基准年 '+bs.base+'。');
  } else P('  （未给正常 PE 档，无法计算兑现期限）');
  P('');

  var B=SUM.backsolve||{};
  P('  【估值范式上界】（只列能够到现价以上的范式；自上而下＝从可验证到难证伪）');
  var _hid=[];
  var _lad=(B.ladder||[]).filter(function(x){
    var c=(x.mcap_yi!=null)?num(x.mcap_yi):(isFinite(live[x.key])?live[x.key]:null);
    var f=(x.mcap_if_yi!=null)?num(x.mcap_if_yi):null;
    var okc=(bs.mcap0&&c!=null&&c/bs.mcap0-1>=0), okf=(bs.mcap0&&f!=null&&f/bs.mcap0-1>=0);
    if(okc||okf) return true; _hid.push(x.name||x.key||''); return false; });
  if(!_lad.length&&(B.ladder||[]).length)
    P('  1. 当前参数下没有任何估值范式能给出高于现价的市值——'+(B.ladder||[]).length+' 档全部落在现价之下。');
  _lad.forEach(function(x,j){
    var cap=(x.mcap_yi!=null)?num(x.mcap_yi):(isFinite(live[x.key])?live[x.key]:null);
    P('  '+(j+1)+'. '+(x.name||x.key)+'（'+(x.status||'待验')+(x.current?'·当前市场用的就是这档':'')+'）');
    var i=0;
    P('    ('+(++i)+') 适用前提：'+(x.precond||'—'));
    var up=(bs.mcap0&&cap!=null)?(cap/bs.mcap0-1):null;
    if(cap!=null&&up!=null&&up>=0) P('    ('+(++i)+') 现参数下：'+yi(cap)+' 亿（较现价 '+spct(up,0)+'）');
    var ifup=(bs.mcap0&&x.mcap_if_yi!=null)?(num(x.mcap_if_yi)/bs.mcap0-1):null;
    if(x.mcap_if_yi!=null&&!(ifup!=null&&ifup<0)) P('    ('+(++i)+') 前提成立后可到：'+yi(x.mcap_if_yi)+' 亿'+
      (ifup!=null?('（较现价 '+spct(ifup,0)+'）'):'')+(x.if_basis?('——'+x.if_basis):''));
    if(x.gap) P('    ('+(++i)+') 差什么：'+x.gap);
    if(x.note) P('    ('+(++i)+') '+x.note); });
  if(_hid.length) P('     （另有 '+_hid.length+' 档在现参数下低于现价、够不到上界，已隐去）');
  P('');

  P('  【潜在催化】');
  (B.switches||[]).forEach(function(x,j){
    P('  '+(j+1)+'. '+(x.from||'')+' → '+(x.to||'')+(x.prob!=null?('（主观概率 '+pct(x.prob,0)+'）'):''));
    var i=0;
    P('    ('+(++i)+') 催化是什么：'+(x.catalyst||'—'));
    P('    ('+(++i)+') 盯哪个指标：'+(x.watch||'—'));
    P('    ('+(++i)+') 大概什么时候：'+(x.when||'—'));
    if(x.elasticity) P('    ('+(++i)+') 切过去的弹性：'+x.elasticity);
    if(x.kill) P('    ('+(++i)+') 反向：'+x.kill); });
  return L.join('\n');
}

// ---- boot ------------------------------------------------------------------
function boot(){ chartDefaults(); normalizeModel(); normalizePhaseChg();
  el('p3-note').innerHTML=(MODEL.note||'archetype 归型：'+esc(MODEL.archetype||'—')+'。历史列=财报实际，预测列=下方假设驱动，改假设即时联动利润表与估值。')+cite(MODEL.cite);
  renderKPI(); renderSnapshot(); renderTypeCard(); renderRevenue(); renderHolders(); renderFactions(); renderOwnership(); renderDupont(); renderCost(); renderCashCapex(); renderConsensus(); renderChipAge(); renderNarrativeCapacity(); renderPrice();
  renderNarrativeMap(); renderSegmentModels(); renumberPart3();
  bindRangeInputs();                         // 委托绑定：核心假设区 + 段内滑块（镜像同步）
  renderAssumptions(); recompute();          // 假设面板先建 DOM，recompute 才能把 λ 即时结果写进 #lam-out
  renderContradictionMap();                  // 第四章 矛盾地图（part4 缺则整章隐藏）
  renderFeedbackLog();
  var sumc=el('sum-copy'); if(sumc) sumc.addEventListener('click',function(){
    copyText(summaryText()); toast('已复制文本版总结（可直接粘进 IM / IC memo）'); });
  renderRefs(); setupPopover(); setupScrollspy(); setupTheme(); setupPrintExpand();
  el('btn-cost-rate').addEventListener('click',function(){costMode='rate';renderCost();});
  // 1.4b 现金流/CAPEX：单季 ↔ 滚动四季（无 ttm 腿时按钮已在渲染时隐藏）
  var _bq=el('btn-cash-q'), _bt=el('btn-cash-ttm');
  if(_bq) _bq.addEventListener('click',function(){cashMode='q';renderCashCapex();});
  if(_bt) _bt.addEventListener('click',function(){cashMode='ttm';renderCashCapex();});
  el('btn-cost-fall').addEventListener('click',function(){costMode='fall';renderCost();});
  // 1.5 一致预期：期间(季/年) × 指标(收入/净利/EPS) 切换
  [['btn-cons-q',function(){consPeriod='quarter';}],['btn-cons-y',function(){consPeriod='annual';}],
   ['btn-cons-rev',function(){consMetric='rev';}],['btn-cons-np',function(){consMetric='np';}],
   ['btn-cons-eps',function(){consMetric='eps';}]].forEach(function(x){
    var b=el(x[0]); if(b) b.addEventListener('click',function(){ x[1](); renderConsensus(); }); });
  // 1.6 码龄：时间序列 / 当前分布 切换
  [['btn-chip-ov','overview'],['btn-chip-age','age'],['btn-chip-pct','pct'],['btn-chip-attr','attr']].forEach(function(x){
    var b=el(x[0]); if(b) b.addEventListener('click',function(){ chipMode=x[1]; renderChipAge(); }); });
  // 2.1b 前瞻估值复合图：全部 / PE / PS / 收入预期 切换
  [['btn-fwd-all','all'],['btn-fwd-pe','pe'],['btn-fwd-ps','ps'],['btn-fwd-rev','rev'],['btn-fwd-ni','ni']].forEach(function(x){
    var b=el(x[0]); if(b) b.addEventListener('click',function(){ fwdMode=x[1];
      if(FWD_ARGS) renderFwdPE(FWD_ARGS.dates,FWD_ARGS.closes); }); });
  setTimeout(fixZero,150); setTimeout(function(){mdBold();},220);
  window.__EONE_APP__={ recompute:recompute, renderCost:renderCost, setCostMode:function(m){costMode=m;}, renderCashCapex:renderCashCapex, setCashMode:function(m){cashMode=m;}, rebuildAllCharts:rebuildAllCharts, openCatPop:openCatPop, closeCatPop:closeCatPop, MODEL:MODEL, CH:CH,
    toast:toast, copyText:copyText, renderFeedbackLog:renderFeedbackLog,
    renderAssumptions:renderAssumptions, applyOverseasBridge:applyOverseasBridge, knobDisp:knobDisp,
    renderSummary:renderSummary, summaryText:summaryText, backsolve:backsolve };  // 开篇章：兑现期限计算 + 文本导出
}
if(document.readyState!=='loading') boot(); else document.addEventListener('DOMContentLoaded',boot);
})();
