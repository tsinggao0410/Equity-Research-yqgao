/* =============================================================================
 * equity-onepager-interactive · annot.js —— 反馈标注层（认知螺旋的入口）
 *
 * 读者在页面上「划词/点块」标注疑问 → 存本机 localStorage → 一键同步云端(或导出)
 *   → 我用 scripts/feedback_pull.py 拉回汇总 → 改 page_model → 重出 v_n+1
 *   → 新版页面顶部渲「本版反馈回应」，被改动的模块打绿边。
 *
 * 契约（page_model）：
 *   feedback:{ report_id, endpoint, autosync, rag_ws, resolved:[], open:[] }
 *   meta:{ version, updated, changelog }
 * 无 feedback.endpoint → 纯本地模式（导出/复制摘要仍可用，file:// 直接可跑）。
 * 依赖：无。与 app.js 解耦（只读 window.__DATA__ + DOM 上的 [data-fbk] 锚点）。
 * ========================================================================== */
(function(){
'use strict';
var D=window.__DATA__||{}, FB=D.feedback||{}, META=D.meta||{};
var RID=FB.report_id||((META.ticker||'unknown')+'');
var VER=META.version||'v1';
var KEY='eone_fb::'+RID;
var RKEY='eone_fb_reader';
var TYPES=[
  {k:'q',ic:'❓',lb:'没看懂',hint:'这段逻辑/术语没看懂，要我讲清楚'},
  {k:'d',ic:'⚠️',lb:'数据存疑',hint:'这个数字/口径我怀疑，要核'},
  {k:'s',ic:'🔍',lb:'要原文',hint:'要看这条结论背后的纪要/研报原句'},
  {k:'i',ic:'💡',lb:'建议补',hint:'建议补一个角度/情景/对标'},
  {k:'o',ic:'✅',lb:'认可',hint:'这段是关键，标记留痕'}
];
var TMAP={}; TYPES.forEach(function(t){TMAP[t.k]=t;});
var items=[], selRange=null;

// ---- utils -----------------------------------------------------------------
function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
function el(id){ return document.getElementById(id); }
function uid(){ return 'A'+Date.now().toString(36)+Math.random().toString(36).slice(2,6); }
function nowISO(){ var d=new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')
  +' '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0'); }
function toast(m,ms){ var t=el('fb-toast'); if(!t) return; t.textContent=m; t.style.display='block';
  clearTimeout(toast._t); toast._t=setTimeout(function(){t.style.display='none';},ms||1900); }
function copyText(t){ try{ if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(t); return true; } }catch(_){}
  var ta=document.createElement('textarea'); ta.value=t; ta.style.position='fixed'; ta.style.opacity='0';
  document.body.appendChild(ta); ta.select(); var ok=false; try{ok=document.execCommand('copy');}catch(_){}
  document.body.removeChild(ta); return ok; }
function dl(name,text,mime){ var b=new Blob([text],{type:mime||'application/json;charset=utf-8'});
  var u=URL.createObjectURL(b), a=document.createElement('a'); a.href=u; a.download=name;
  document.body.appendChild(a); a.click(); document.body.removeChild(a); setTimeout(function(){URL.revokeObjectURL(u);},400); }
function cssq(s){ return String(s).replace(/"/g,'\\"'); }

// ---- store -----------------------------------------------------------------
function load(){ try{ items=JSON.parse(localStorage.getItem(KEY)||'[]')||[]; }catch(_){ items=[]; } }
function save(){ try{ localStorage.setItem(KEY,JSON.stringify(items)); }catch(_){ toast('本地存储写入失败(隐私模式?)'); }
  paintCount(); if(FB.autosync&&FB.endpoint) queueSync(); }
function reader(){ var i=el('fb-reader'); var v=(i&&i.value||'').trim();
  if(!v){ try{ v=localStorage.getItem(RKEY)||''; }catch(_){} if(i&&v) i.value=v; }
  return v; }

// ---- anchor 定位：把标注挂到 page_model 的 JSON 路径上（我改稿时直达字段） -----
function anchorOf(node){
  var e=node&&node.nodeType===3?node.parentNode:node;
  var host=e&&e.closest?e.closest('[data-fbk]'):null;
  var sec=null, h=e;
  while(h&&h!==document.body){                        // 往前找最近的 h1/h2 当章节名
    var prev=h.previousElementSibling;
    while(prev){ if(/^H[123]$/.test(prev.tagName)){ sec=prev; break; } prev=prev.previousElementSibling; }
    if(sec) break; h=h.parentElement;
  }
  var st=sec?(sec.textContent||'').replace(/★\s*当下逻辑最强|逻辑支线|弱驱动/g,'').replace(/\s+/g,' ').trim().slice(0,44):'';
  return { path: host?host.getAttribute('data-fbk'):'', sec: sec?sec.id:'', sec_title: st };
}

// ---- 创建标注 ---------------------------------------------------------------
function addFromSelection(type){
  var sel=window.getSelection(); if(!sel||!sel.rangeCount) return;
  var r=selRange||sel.getRangeAt(0); var q=(r.toString()||'').replace(/\s+/g,' ').trim();
  if(!q){ return; }
  var a=anchorOf(r.startContainer);
  var it={ id:uid(), type:type, quote:q.slice(0,300), note:'', path:a.path, sec:a.sec, sec_title:a.sec_title,
           ver:VER, reader:reader(), created:nowISO(), synced:false };
  items.push(it); save(); markRange(r,it); sel.removeAllRanges(); hideSelbar();
  renderList(true); openDrawer(); focusNote(it.id); touchAnchor(it.path);
}
function addFromBlock(host,type){
  var a={ path:host.getAttribute('data-fbk'), sec:'', sec_title:'' };
  var an=anchorOf(host); a.sec=an.sec; a.sec_title=an.sec_title;
  var txt=(host.textContent||'').replace(/✎ 标注本块/g,'').replace(/\s+/g,' ').trim();
  txt=txt.slice(0,96)+(txt.length>96?'…':'');
  var it={ id:uid(), type:type, quote:'【整块】'+txt, note:'', path:a.path, sec:a.sec, sec_title:a.sec_title,
           ver:VER, reader:reader(), created:nowISO(), synced:false };
  items.push(it); save(); renderList(true); openDrawer(); focusNote(it.id); touchAnchor(it.path);
}
function touchAnchor(path){ if(!path) return; var n=document.querySelector('[data-fbk="'+cssq(path)+'"]'); if(n) n.classList.add('fb-touched'); }

// ---- 高亮（划词处留痕，重渲后按 quote 复原；失败则只留清单） ----------------
function markRange(r,it){
  try{ var m=document.createElement('mark'); m.className='fb-hl'; m.setAttribute('data-fbid',it.id);
    m.title=TMAP[it.type].lb+'（点击查看/编辑）'; r.surroundContents(m); appendMark(m,it); return true;
  }catch(_){ return false; }
}
function appendMark(m,it){ var s=document.createElement('sup'); s.className='fb-mark'; s.setAttribute('data-fbid',it.id);
  s.textContent=TMAP[it.type].ic; m.appendChild(s); }
function restoreMarks(){
  items.forEach(function(it){
    if(!it.quote||it.quote.indexOf('【整块】')===0) return;
    if(document.querySelector('mark.fb-hl[data-fbid="'+cssq(it.id)+'"]')) return;
    var scope=it.path?document.querySelector('[data-fbk="'+cssq(it.path)+'"]'):null;
    scope=scope||(it.sec?document.getElementById(it.sec):null);
    scope=scope||document.querySelector('main'); if(!scope) return;
    var needle=it.quote.slice(0,60);
    var w=document.createTreeWalker(scope,NodeFilter.SHOW_TEXT,null), n;
    while((n=w.nextNode())){
      if(n.parentNode&&n.parentNode.closest&&n.parentNode.closest('mark.fb-hl')) continue;
      var i=n.nodeValue.indexOf(needle); if(i<0) continue;
      try{ var r=document.createRange(); r.setStart(n,i); r.setEnd(n,Math.min(n.nodeValue.length,i+needle.length));
        var m=document.createElement('mark'); m.className='fb-hl'; m.setAttribute('data-fbid',it.id);
        m.title=TMAP[it.type].lb+'（点击查看/编辑）'; r.surroundContents(m); appendMark(m,it); }catch(_){}
      break;
    }
    if(it.path) touchAnchor(it.path);
  });
}

// ---- 划词工具条 -------------------------------------------------------------
function showSelbar(){
  var sel=window.getSelection(); if(!sel||!sel.rangeCount) return hideSelbar();
  var q=(sel.toString()||'').trim(); if(q.length<2) return hideSelbar();
  var r=sel.getRangeAt(0);
  if(!r.startContainer||!(r.startContainer.parentNode&&r.startContainer.parentNode.closest)) return hideSelbar();
  if(r.startContainer.parentNode.closest('#fb-drawer,#toc,#fb-selbar')) return hideSelbar();
  selRange=r.cloneRange();
  var bar=el('fb-selbar'); fillBar(bar,'sel',null);   // 每次按当前模式重建按钮(否则会残留整块模式的按钮)
  var rc=r.getBoundingClientRect();
  bar.style.display='flex';
  var x=window.scrollX+rc.left, y=window.scrollY+rc.top-bar.offsetHeight-8;
  if(y<window.scrollY+4) y=window.scrollY+rc.bottom+8;
  bar.style.left=Math.max(6,Math.min(x,window.scrollX+document.documentElement.clientWidth-bar.offsetWidth-10))+'px';
  bar.style.top=y+'px';
}
function hideSelbar(){ var b=el('fb-selbar'); if(b) b.style.display='none'; selRange=null; }
// 工具条两种模式共用一套按钮 + 一次性事件委托：mode='sel'(划词) / 'blk'(整块)
var barBound=false, blockHost=null;
function fillBar(bar,mode,host){
  blockHost=(mode==='blk')?host:null;
  bar.setAttribute('data-mode',mode);
  bar.innerHTML=TYPES.map(function(t){ return '<button data-t="'+t.k+'" title="'+esc(t.hint)+'">'+t.ic+' '+t.lb+'</button>'; }).join('');
  if(!barBound){ barBound=true;
    bar.addEventListener('mousedown',function(e){ e.preventDefault(); });   // 别掐断 selection
    bar.addEventListener('click',function(e){ var b=e.target.closest('button[data-t]'); if(!b) return;
      if(bar.getAttribute('data-mode')==='blk'&&blockHost){ addFromBlock(blockHost,b.getAttribute('data-t')); hideSelbar(); }
      else addFromSelection(b.getAttribute('data-t')); });
  }
}

// ---- 整块 ✎ pin ------------------------------------------------------------
function injectPins(root){
  (root||document).querySelectorAll('[data-fbk]').forEach(function(h){
    if(h.querySelector(':scope>.fb-pin')) return;
    var b=document.createElement('span'); b.className='fb-pin'; b.textContent='✎ 标注本块';
    b.title='对整块提问（路径 '+h.getAttribute('data-fbk')+'）';
    b.addEventListener('click',function(e){ e.stopPropagation(); openBlockMenu(h,b); });
    h.appendChild(b);
  });
}
function openBlockMenu(host,pin){
  var bar=el('fb-selbar'); fillBar(bar,'blk',host);
  bar.style.display='flex';
  var rc=pin.getBoundingClientRect();
  bar.style.left=Math.max(6,window.scrollX+rc.right-bar.offsetWidth)+'px';
  bar.style.top=(window.scrollY+rc.bottom+6)+'px';
}

// ---- 抽屉清单 --------------------------------------------------------------
function paintCount(){ var c=el('fb-count'); if(c) c.textContent=items.length; }
function renderList(keepOpen){
  var host=el('fb-list'); if(!host) return;
  if(!items.length){ host.innerHTML='<div class="small muted" style="padding:14px 2px;line-height:1.8">还没有标注。<br>· <b>选中</b>任意正文/表格文字 → 选类型<br>· 或悬停任一模块点右上 <b>✎ 标注本块</b><br>· 快捷键 <b>Alt+A</b> 开关本面板</div>'; paintCount(); return; }
  var bySec={}; items.forEach(function(it){ var k=it.sec_title||'其他'; (bySec[k]=bySec[k]||[]).push(it); });
  host.innerHTML=Object.keys(bySec).map(function(k){
    return '<div class="fbi-sec" style="margin:10px 0 2px;font-weight:700;color:var(--accent)">'+esc(k)+'</div>'
      +bySec[k].map(function(it){ var t=TMAP[it.type]||TMAP.q;
        return '<div class="fb-item t-'+it.type+'" data-id="'+esc(it.id)+'">'
          +'<div class="fbi-hd"><span class="fbi-t">'+t.ic+' '+t.lb+'</span><span class="fbi-sec">'+esc(it.created)+(it.synced?' · 已同步':'')+'</span></div>'
          +'<div class="fbi-q">'+esc(it.quote)+'</div>'
          +(it.path?('<div class="fbi-path">'+esc(it.path)+'</div>'):'')
          +'<textarea data-note="'+esc(it.id)+'" placeholder="补充：具体哪里不懂 / 你的怀疑是什么 / 想看什么口径">'+esc(it.note)+'</textarea>'
          +'<div class="fbi-act"><span data-jump="'+esc(it.id)+'">↧ 定位</span><span data-del="'+esc(it.id)+'">✕ 删除</span></div>'
          +'</div>'; }).join('');
  }).join('');
  paintCount(); paintStat();
  if(keepOpen!==true&&!el('fb-drawer').classList.contains('open')) return;
}
function paintStat(){ var s=el('fb-stat'); if(!s) return;
  var un=items.filter(function(i){return !i.synced;}).length;
  s.innerHTML='共 '+items.length+' 条 · 未同步 '+un+' 条 · 报告 '+esc(RID)+' '+esc(VER)
    +(FB.endpoint?('<br>云端：'+esc(FB.endpoint)):'<br>纯本地模式（未配 endpoint）：用「复制反馈摘要」粘给我，或「导出 JSON」发我。');
}
function focusNote(id){ setTimeout(function(){ var t=document.querySelector('textarea[data-note="'+cssq(id)+'"]');
  if(t){ t.focus(); t.scrollIntoView({block:'center'}); } },60); }
function openDrawer(){ el('fb-drawer').classList.add('open'); document.body.classList.add('fbd'); }
function closeDrawer(){ el('fb-drawer').classList.remove('open'); document.body.classList.remove('fbd'); }
function drawerOpen(){ var d=el('fb-drawer'); return !!(d&&d.classList.contains('open')); }
function evpopOpen(){ var p=el('evpop'); return !!(p&&p.style.display==='block'); }

// ---- 云端同步 --------------------------------------------------------------
var syncT=null;
function queueSync(){ clearTimeout(syncT); syncT=setTimeout(function(){ sync(true); },1500); }
function sync(quiet){
  if(!FB.endpoint){ if(!quiet) toast('未配置云端 endpoint —— 用「复制反馈摘要」或「导出 JSON」'); return; }
  var pend=items.filter(function(i){return !i.synced;});
  if(!pend.length){ if(!quiet) toast('没有待同步的标注'); return; }
  var body={ report_id:RID, ver:VER, reader:reader(), name:META.name||'', ticker:META.ticker||'', items:pend };
  fetch(String(FB.endpoint).replace(/\/$/,'')+'/api/ann',{ method:'POST',
    headers:{'content-type':'application/json'}, body:JSON.stringify(body) })
  .then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.json(); })
  .then(function(j){ var ok=(j&&j.saved!=null)?j.saved:pend.length;
    pend.forEach(function(i){ i.synced=true; });
    try{ localStorage.setItem(KEY,JSON.stringify(items)); }catch(_){}
    renderList(true); toast('已同步 '+ok+' 条到云端'); })
  .catch(function(e){ toast('同步失败：'+e.message+'（可先导出 JSON）',3200); });
}

// ---- 导出 / 摘要 -----------------------------------------------------------
function summaryMD(){
  var L=['# 报告反馈 · '+(META.name||'')+' '+(META.ticker||''),
         '', '- 报告版本：'+VER+(META.updated?(' ('+META.updated+')'):''), '- 提交人：'+(reader()||'(未署名)'),
         '- 提交时间：'+nowISO(), '- 条目数：'+items.length, ''];
  var bySec={}; items.forEach(function(it){ var k=it.sec_title||'其他'; (bySec[k]=bySec[k]||[]).push(it); });
  Object.keys(bySec).forEach(function(k){ L.push('## '+k);
    bySec[k].forEach(function(it){ var t=TMAP[it.type]||TMAP.q;
      L.push('- **['+t.lb+']** `'+it.id+'`'+(it.path?(' path=`'+it.path+'`'):''));
      L.push('  - 原文：「'+it.quote+'」');
      if(it.note) L.push('  - 疑问/意见：'+it.note);
    }); L.push(''); });
  L.push('> 处理方式：把本段贴回对话，或让我跑 `python scripts/feedback_pull.py --ticker <代码> --from-file <导出的json>`。');
  return L.join('\n');
}
function exportJSON(){
  dl('feedback_'+RID+'_'+VER+'_'+Date.now()+'.json',
     JSON.stringify({report_id:RID,ver:VER,name:META.name,ticker:META.ticker,reader:reader(),
                     exported:nowISO(),items:items},null,1));
  toast('已导出 JSON（发我或用 feedback_pull.py --from-file 读）',2600);
}

// ---- 事件绑定 --------------------------------------------------------------
function bind(){
  el('fb-fab').addEventListener('click',function(){ var d=el('fb-drawer');
    d.classList.contains('open')?closeDrawer():(renderList(true),openDrawer()); });
  el('fb-close').addEventListener('click',closeDrawer);
  el('fb-sync').addEventListener('click',function(){ sync(false); });
  el('fb-copy').addEventListener('click',function(){ if(!items.length) return toast('还没有标注');
    copyText(summaryMD())?toast('反馈摘要已复制 —— 直接粘到对话里发我',2600):toast('复制失败，请用导出 JSON'); });
  el('fb-export').addEventListener('click',function(){ if(!items.length) return toast('还没有标注'); exportJSON(); });
  el('fb-clear').addEventListener('click',function(){ if(!items.length) return;
    if(!confirm('清空本机 '+items.length+' 条标注？（云端已同步的不受影响）')) return;
    items=[]; save(); document.querySelectorAll('mark.fb-hl').forEach(function(m){ var p=m.parentNode;
      while(m.firstChild){ if(m.firstChild.className==='fb-mark'){ m.removeChild(m.firstChild); continue; } p.insertBefore(m.firstChild,m); }
      p.removeChild(m); });
    document.querySelectorAll('.fb-touched').forEach(function(n){n.classList.remove('fb-touched');});
    renderList(true); toast('已清空本地标注'); });
  var ri=el('fb-reader');
  ri.addEventListener('change',function(){ try{ localStorage.setItem(RKEY,ri.value.trim()); }catch(_){} });
  el('fb-list').addEventListener('input',function(e){ var t=e.target.closest('textarea[data-note]'); if(!t) return;
    var id=t.getAttribute('data-note'); var it=items.filter(function(i){return i.id===id;})[0]; if(!it) return;
    it.note=t.value; it.synced=false; clearTimeout(t.__t); t.__t=setTimeout(save,400); });
  el('fb-list').addEventListener('click',function(e){
    var d=e.target.closest('[data-del]');
    if(d){ var id=d.getAttribute('data-del'); items=items.filter(function(i){return i.id!==id;}); save();
      var mk=document.querySelector('mark.fb-hl[data-fbid="'+cssq(id)+'"]');
      if(mk){ var p=mk.parentNode; while(mk.firstChild){ if(mk.firstChild.className==='fb-mark'){mk.removeChild(mk.firstChild);continue;} p.insertBefore(mk.firstChild,mk);} p.removeChild(mk); }
      renderList(true); return; }
    var j=e.target.closest('[data-jump]');
    if(j){ var jid=j.getAttribute('data-jump'); var it=items.filter(function(i){return i.id===jid;})[0]; if(!it) return;
      var tgt=document.querySelector('mark.fb-hl[data-fbid="'+cssq(jid)+'"]')
        ||(it.path?document.querySelector('[data-fbk="'+cssq(it.path)+'"]'):null)
        ||(it.sec?document.getElementById(it.sec):null);
      if(tgt){ tgt.scrollIntoView({behavior:'smooth',block:'center'}); }
      else toast('该模块已重构，定位不到（路径 '+(it.path||it.sec||'—')+'）'); } });
  document.addEventListener('mouseup',function(e){ if(e.target.closest&&e.target.closest('#fb-selbar,#fb-drawer')) return;
    setTimeout(showSelbar,10); });
  document.addEventListener('keydown',function(e){
    if(e.altKey&&(e.key==='a'||e.key==='A')){ e.preventDefault(); var d=el('fb-drawer');
      d.classList.contains('open')?closeDrawer():(renderList(true),openDrawer()); }
    if(e.key==='Escape'){ hideSelbar(); if(!evpopOpen()) closeDrawer(); } });   // Esc: 工具条→抽屉(原文浮层由 app.js 先接)
  document.addEventListener('click',function(e){
    var mk=e.target.closest('mark.fb-hl'); if(mk){ renderList(true); openDrawer(); focusNote(mk.getAttribute('data-fbid')); return; }
    if(!e.target.closest('#fb-selbar')) hideSelbar();
    // ★抽屉是浮层不是布局：点正文任意处即收起。不 preventDefault → 同一下点击照样打开目标模块
    // （原病症：标注后抽屉常开，右侧 392px 连同各块右上角的 ✎ pin 一起被压住，"点不开后续模块"）
    if(drawerOpen() && !e.target.closest('#fb-drawer,#fb-fab,#fb-selbar,#evpop,#evmask,.fb-pin,mark.fb-hl')) closeDrawer(); });
}

// ---- 重渲染跟随（app.js 改假设会重建 DOM → 补 pin、补高亮） -----------------
function watch(){
  var deb=null;
  var mo=new MutationObserver(function(){ clearTimeout(deb); deb=setTimeout(function(){
    injectPins(document); restoreMarks(); }, 260); });
  var m=document.querySelector('main'); if(m) mo.observe(m,{childList:true,subtree:true});
}

function boot(){
  if(!el('fb-drawer')||!el('fb-fab')) return;            // 模板未含反馈层 → 静默跳过
  load(); reader(); bind(); injectPins(document); restoreMarks(); renderList(true); paintStat();
  window.__EONE_FB__={ items:function(){return items;}, sync:sync, summaryMD:summaryMD,
                       exportJSON:exportJSON, open:openDrawer, restore:restoreMarks };
  watch();
}
if(document.readyState!=='loading') boot(); else document.addEventListener('DOMContentLoaded',boot);
})();
