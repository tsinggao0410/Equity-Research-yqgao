# -*- coding: utf-8 -*-
"""render_assets_v32.py — render_report_v32.py 的 CSS 与前端 JS(纯字符串,无外部依赖)。

视觉取自参考报告 ref_style.css(设计规格 DESIGN_v32 §5),另加:流程图 / 产业链结构图 / 读者标签 / 三图并排 /
图表目录 / 图片放大 / 窄屏目录按钮 / 打印样式。JS 的图表辅助函数(stack、lines、barOne、tipAxis 思路)取自参考报告
第二段 <script>,扩成按 chart 块 JSON 规格生成 ECharts option。
"""

CSS = r"""
:root{
  --bg:#f7f8fa; --panel:#ffffff; --ink:#1a2233; --sub:#5a6478; --line:#e4e8ef;
  --accent:#0f4c81; --accent-soft:#e8f0f8; --warn:#b45309; --warn-soft:#fef3e2;
  --good:#166534; --good-soft:#e7f4ec; --bad:#b91c1c; --bad-soft:#fdecec;
  --surface-1:#ffffff; --text-primary:#1a2233; --text-secondary:#5a6478;
  --series-1:#2a78d6; --series-2:#eb6834; --series-3:#1baf7a; --series-4:#eda100;
  --series-5:#e87ba4; --series-6:#008300; --series-7:#4a3aa7; --series-8:#e34948;
  --grid:#eef1f6; --axis:#9aa4b5; --hi:#eb6834; --hi-soft:#fff4ee; --box:#cfd8e4;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Microsoft YaHei","PingFang SC","Segoe UI",system-ui,sans-serif;
  font-size:15px;line-height:1.75;-webkit-font-smoothing:antialiased;}
.layout{display:flex;max-width:1460px;margin:0 auto;}
/* ── 侧边目录 ── */
nav.toc{width:262px;flex-shrink:0;position:sticky;top:0;height:100vh;overflow-y:auto;
  padding:26px 10px 40px 18px;border-right:1px solid var(--line);background:var(--panel);}
nav.toc .brand{font-weight:700;font-size:15px;color:var(--accent);margin-bottom:2px;line-height:1.5;}
nav.toc .date{font-size:12px;color:var(--sub);margin-bottom:16px;}
nav.toc a{display:block;padding:5px 10px;margin:1px 0;border-radius:6px;color:var(--sub);
  text-decoration:none;font-size:13px;line-height:1.5;}
nav.toc a:hover{background:var(--accent-soft);color:var(--accent);}
nav.toc a.l2{padding-left:22px;font-size:12.3px;}
nav.toc a.on{background:var(--accent-soft);color:var(--accent);font-weight:600;}
nav.toc .grp{font-size:11px;font-weight:700;color:#98a2b3;letter-spacing:1px;
  margin:14px 0 4px 10px;text-transform:uppercase;}
nav.toc .cnt{float:right;font-size:10.5px;color:#98a2b3;font-weight:400;margin-left:6px;}
/* ── 正文 ── */
main{flex:1;min-width:0;padding:34px 46px 90px;}
h1{font-size:27px;margin:0 0 6px;color:var(--accent);line-height:1.4;}
.meta{font-size:13px;color:var(--sub);border-left:3px solid var(--accent);
  background:var(--panel);padding:11px 15px;border-radius:0 8px 8px 0;margin:14px 0 8px;}
.meta p{margin:3px 0;line-height:1.65;}
.meta b.ml{color:var(--ink);font-weight:700;margin-right:2px;}
.meta b.ml::after{content:"：";}
h2{font-size:21px;margin:48px 0 14px;padding-bottom:8px;border-bottom:2px solid var(--accent);
  color:var(--accent);line-height:1.45;scroll-margin-top:12px;}
h3{font-size:17px;margin:28px 0 10px;color:var(--ink);line-height:1.5;
  padding-left:10px;border-left:4px solid var(--accent);scroll-margin-top:12px;}
h4{font-size:14.5px;margin:18px 0 6px;color:var(--accent);}
p{margin:8px 0;}
ul,ol{margin:8px 0;padding-left:24px;}
li{margin:5px 0;}
strong{color:#0d3a63;}
em{font-style:normal;color:var(--accent);}
code{font-family:"SF Mono",Menlo,Consolas,monospace;font-size:.88em;background:#eef1f6;padding:1px 5px;border-radius:4px;}
pre.code{background:#f1f4f8;border:1px solid var(--line);border-radius:8px;padding:10px 12px;overflow-x:auto;font-size:12.5px;line-height:1.55;}
hr{border:0;border-top:1px solid var(--line);margin:26px 0;}
a.ref{color:var(--accent);text-decoration:none;border-bottom:1px dotted var(--accent);}
.src,.srcline{color:var(--sub);font-size:12.3px;line-height:1.6;}
.srcline{margin:4px 0 14px;}
.rl{color:var(--sub);font-size:11.8px;font-weight:400;white-space:nowrap;}
/* 表格 */
.tblock{margin:14px 0;}
.tbl-wrap{overflow-x:auto;margin:14px 0;border:1px solid var(--line);border-radius:10px;background:var(--panel);}
.tblock .tbl-wrap{margin:0;}
.tblock .srcline{margin:6px 2px 0;}
table{border-collapse:collapse;width:100%;font-size:13.2px;line-height:1.55;}
th{background:var(--accent);color:#fff;padding:9px 11px;text-align:left;font-weight:600;white-space:nowrap;}
td{padding:7px 11px;border-top:1px solid var(--line);vertical-align:top;}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
th.n{text-align:right;}
td.c,th.c{text-align:center;}
tbody tr:nth-child(even){background:#fafbfd;}
tbody tr:hover{background:var(--accent-soft);}
tbody tr.tot{font-weight:700;background:#eef3f9;}
tbody tr.tot td{border-top:2px solid var(--accent);}
tbody tr.subrow td{color:var(--sub);font-size:12.5px;}
caption{caption-side:top;text-align:left;font-size:13px;font-weight:600;
  color:var(--accent);padding:9px 11px 4px;}
/* 徽章 */
.tag{display:inline-block;padding:1px 9px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap;line-height:1.6;}
.tag.warn{background:var(--warn-soft);color:var(--warn);}
.tag.good{background:var(--good-soft);color:var(--good);}
.tag.bad{background:var(--bad-soft);color:var(--bad);}
.tag.info{background:var(--accent-soft);color:var(--accent);}
.tag.hi{background:var(--hi-soft);color:#c2521f;}
/* 卡片 */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin:16px 0;}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px 17px;}
.card .no{font-size:12px;font-weight:700;color:var(--accent);letter-spacing:.5px;}
.card h4{margin:4px 0 8px;font-size:15px;color:var(--ink);}
.card p{font-size:13.4px;color:var(--sub);margin:0;}
/* KPI 磁贴 */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin:16px 0;}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 15px;}
.kpi .lab{font-size:12px;color:var(--sub);margin-bottom:3px;}
.kpi .val{font-size:22px;font-weight:700;color:var(--accent);line-height:1.25;font-variant-numeric:tabular-nums;}
.kpi .val .u{font-size:13px;font-weight:600;margin-left:2px;}
.kpi .sub{font-size:11.5px;color:var(--sub);margin-top:2px;}
.kpi .sub b.up{color:var(--good);font-weight:600;} .kpi .sub b.down{color:var(--bad);font-weight:600;}
/* 图表容器 */
figure{margin:18px 0;background:var(--panel);border:1px solid var(--line);
  border-radius:12px;padding:15px 16px 10px;scroll-margin-top:12px;}
figure .fig-t{font-size:14.5px;font-weight:700;color:var(--ink);margin-bottom:2px;line-height:1.5;}
figure .fig-s{font-size:12.3px;color:var(--sub);margin-bottom:8px;}
figure figcaption{font-size:11.8px;color:var(--sub);margin-top:6px;line-height:1.6;
  padding-top:6px;border-top:1px solid var(--line);}
figure figcaption .fig-note{display:block;margin-top:3px;}
figure figcaption,.fig-s,.fig-hint,.note,main p,main li,.srcline{overflow-wrap:anywhere;}
.chart{width:100%;height:380px;overflow:hidden;}  /* tooltip 已 confine;裁掉旧位置残留,防窄屏横向滚动 */
.chart.tall{height:460px;}
.chart.short{height:300px;}
.chart-err{padding:30px;color:var(--bad);font-size:13px;}
/* 研报原图 / 官方图 */
figure.shot{padding:13px 14px 10px;}
figure.shot .fig-t{font-size:14px;margin-bottom:6px;}
figure.shot .kind{margin-right:6px;vertical-align:1px;font-size:11px;padding:0 7px;}
.shot img{width:100%;height:auto;display:block;margin:0 auto;border:1px solid var(--line);border-radius:6px;cursor:zoom-in;background:#fff;}
/* 原图不再铺满正文宽:按原始像素显示(不放大发虚),最高 480px,看不清点开放大 */
figure.shot>img{width:auto;max-width:100% !important;max-height:440px;height:auto;}
.two-up figure.shot>img{width:100%;height:340px;max-height:none;object-fit:contain;border:0;}
.fig-hint{font-size:12.3px;color:var(--ink);background:#f6f8fb;border-radius:6px;padding:6px 10px;margin-top:8px;line-height:1.6;}
.fig-hint::before{content:"读图:";font-weight:700;color:var(--accent);}
a.xref{color:var(--accent);text-decoration:none;border-bottom:1px dotted rgba(15,76,129,.45);}
a.xref:hover{border-bottom-style:solid;}
#backbtn{display:none;position:fixed;left:50%;transform:translateX(-50%);bottom:18px;z-index:41;border:0;border-radius:999px;
  background:#1a2233;color:#fff;font-size:13px;font-weight:600;padding:9px 18px;box-shadow:0 4px 14px rgba(0,0,0,.25);cursor:pointer;}
#backbtn.on{display:block;}
.shot .svgwrap{overflow-x:auto;}
.shot .svgwrap svg{max-width:100%;height:auto;display:block;margin:0 auto;}
.shot figcaption{margin-top:7px;}
.miss{border:2px dashed var(--bad);color:var(--bad);background:var(--bad-soft);padding:26px;border-radius:8px;text-align:center;font-size:13px;}
/* 并排 */
.two-up,.three-up{display:grid;gap:14px;margin:18px 0;align-items:start;}
.two-up{grid-template-columns:repeat(2,minmax(0,1fr));}
.three-up{grid-template-columns:repeat(3,minmax(0,1fr));}
.two-up>*,.three-up>*{margin:0;min-width:0;}
.two-up>figure,.three-up>figure{display:flex;flex-direction:column;}
.two-up>figure>*,.three-up>figure>*{min-width:0;max-width:100%;}
.half{max-width:660px;margin:18px 0;}
.half>*{margin:0;}
.three-up .chart{height:300px;}
.three-up .shot img{height:230px;object-fit:contain;}
.two-up .fstep .lb{font-size:13px;}
/* 提示块 */
.note{background:var(--warn-soft);border-left:3px solid var(--warn);padding:10px 14px;
  border-radius:0 8px 8px 0;margin:14px 0;font-size:13.4px;}
.note p{margin:4px 0;}
.note.info{background:var(--accent-soft);border-left-color:var(--accent);}
.note.good{background:var(--good-soft);border-left-color:var(--good);}
.note.bad{background:var(--bad-soft);border-left-color:var(--bad);}
.note .nh{font-weight:700;}
/* 基金经理版:通俗解释块 / 类比块 / 例子块(不显示任何标签,只用底色区分层次) */
.plain{background:#f6f7fb;border-left:3px solid #b9c5da;padding:10px 16px;border-radius:0 10px 10px 0;
  margin:12px 0 16px;font-size:14.8px;line-height:1.85;}
.plain.an{background:#f7f5fc;border-left-color:#c6bde6;}
.plain.eg{background:#f2f8f6;border-left-color:#a7cfc3;}
.plain p{margin:5px 0;}
.plain .nh{font-weight:700;}
/* 基金经理版:零章速览版式(摘要面板 + 编号卡片网格) */
.brief-hero{background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:12px;
  padding:18px 22px 14px;margin:16px 0 18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
.brief-hero p.lead,.brief-hero div.lead{background:none;border:0;padding:0;margin:0 0 4px;font-size:16px;line-height:1.85;color:var(--ink);}
.brief-hero p.lead strong,.brief-hero div.lead strong{color:var(--accent);}
.brief-hero .kpis{margin:14px 0 2px;gap:0;border-top:1px solid var(--line);padding-top:12px;
  grid-template-columns:repeat(auto-fit,minmax(150px,1fr));}
.brief-hero .kpi{border:0;border-radius:0;background:none;padding:2px 14px;border-left:1px solid var(--line);}
.brief-hero .kpi:first-child{border-left:0;padding-left:0;}
.brief-hero .kpi .val{font-size:18.5px;}
.brief-hero .srcline{margin-top:8px;}
.brief{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:4px 0 8px;}
.bcard{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 18px 12px;min-width:0;
  box-shadow:0 1px 2px rgba(16,24,40,.04);}
.bcard.wide{grid-column:1 / -1;}
.bcard h3{margin:0 0 10px;padding:0 0 9px;border-left:0;border-bottom:1px solid var(--line);font-size:15.5px;color:var(--ink);
  display:flex;align-items:center;gap:9px;}
.bcard h3 .bno{font-size:11.5px;font-weight:700;color:var(--accent);background:var(--accent-soft);border-radius:6px;
  padding:1px 7px;letter-spacing:.5px;font-variant-numeric:tabular-nums;}
.bbody{font-size:14.3px;line-height:1.8;}
.bbody>p:first-child{margin-top:0;}
.bbody .plain,.bbody .plain.an,.bbody .plain.eg{background:none;border:0;padding:0;margin:0 0 6px;font-size:14.3px;line-height:1.8;border-radius:0;}
.bbody .plain.eg{color:var(--ink);}
.bbody figure{border:0;box-shadow:none;padding:0;margin:12px 0 2px;background:none;}
.bbody .tblock{margin:10px 0 4px;}
.bbody .tl{margin:8px 0 4px 4px;}
.bbody .srcline{margin:4px 0 0;}
@media (max-width:1000px){ .brief{grid-template-columns:minmax(0,1fr);} .brief-hero .kpi{border-left:0;padding-left:0;} }
/* 基金经理版:技术演进路线图 */
.rm{display:grid;grid-template-columns:repeat(var(--n),minmax(0,1fr));column-gap:26px;margin:8px 0 6px;}
.rstage{position:relative;background:#fff;border:1px solid var(--box);border-radius:10px;padding:9px 11px 10px;min-width:0;}
.rstage::after{content:"";position:absolute;right:-19px;top:26px;width:10px;height:10px;
  border-top:2px solid var(--accent);border-right:2px solid var(--accent);transform:rotate(45deg);}
.rstage.last::after{display:none;}
.rstage.now{border-color:var(--hi);background:var(--hi-soft);box-shadow:0 0 0 1px var(--hi) inset;}
.rstage.future{border-style:dashed;background:#fafbfd;}
.rstage.hot .rname{color:#c2521f;}
.rera{font-size:11.5px;font-weight:700;color:var(--accent);letter-spacing:.4px;line-height:1.5;}
.rnow,.rfut{display:inline-block;margin-left:6px;font-size:10.5px;padding:0 7px;border-radius:999px;background:var(--hi);
  color:#fff;vertical-align:1px;line-height:1.7;}
.rfut{background:var(--axis);}
.rname{font-size:14px;font-weight:700;color:var(--ink);line-height:1.45;margin:2px 0 4px;}
.rgist{font-size:12.9px;color:var(--ink);line-height:1.6;margin-bottom:4px;}
.rrow{font-size:12.3px;color:var(--sub);line-height:1.55;margin-top:5px;}
.rl2{display:block;font-size:10.8px;font-weight:700;color:var(--axis);letter-spacing:.4px;}
.rfork{margin-top:14px;border-top:2px dashed var(--line);padding-top:10px;}
.rfl{font-size:12px;font-weight:700;color:var(--sub);margin-bottom:8px;}
.rfo{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 14px;}
.ropt{border:1px dashed var(--box);border-radius:9px;padding:8px 11px;background:#fbfcfe;min-width:0;}
/* 基金经理版:术语词典与悬停释义 */
.gloss td.glt{font-weight:700;color:var(--accent);min-width:6.5em;}
.gloss tr:target{background:var(--hi-soft);}
.gl{border-bottom:1px dashed #6d5bd0;cursor:help;}
.gl:focus{outline:none;background:#f0edff;border-radius:2px;}
#gltip{position:fixed;z-index:60;max-width:min(340px,86vw);background:#fff;border:1px solid var(--line);border-radius:9px;
  box-shadow:0 8px 26px rgba(20,30,50,.18);padding:9px 12px;font-size:13px;line-height:1.65;color:var(--ink);display:none;}
#gltip.on{display:block;}
#gltip a{display:inline-block;margin-top:4px;color:var(--accent);font-size:12px;}
/* 表格视图 */
details.dv{margin:10px 0 0;border:1px solid var(--line);border-radius:8px;background:#fbfcfe;}
details.dv>summary{cursor:pointer;padding:7px 12px;font-size:12.5px;color:var(--accent);
  font-weight:600;list-style:none;}
details.dv>summary::-webkit-details-marker{display:none;}
details.dv>summary::before{content:"▸ ";}
details.dv[open]>summary::before{content:"▾ ";}
details.dv .tbl-wrap{margin:0 10px 10px;}
/* 时间轴 */
.tl{position:relative;margin:16px 0 16px 6px;padding-left:22px;border-left:2px solid var(--accent-soft);}
figure .tl{margin:10px 0 6px 8px;}
.tl .ev{position:relative;margin:0 0 15px;}
.tl .ev:last-child{margin-bottom:4px;}
.tl .ev::before{content:"";position:absolute;left:-29px;top:7px;width:10px;height:10px;
  border-radius:50%;background:var(--accent);border:2px solid var(--panel);}
.tl .ev.hot::before{background:var(--series-2);}
.tl .yr{font-weight:700;color:var(--accent);font-size:13.5px;margin-right:4px;}
.tl .ev.hot .yr{color:#c2521f;}
.tl .tx{font-size:13.6px;}
/* 章首导语 */
p.lead,div.lead{background:var(--accent-soft);border-left:3px solid var(--accent);
  padding:11px 15px;border-radius:0 8px 8px 0;margin:12px 0 18px;font-size:14.2px;}
div.lead p{margin:3px 0;}
/* 流程图 */
.flow{display:flex;flex-direction:column;gap:14px;margin:8px 0 6px;}
.flow-lane{display:grid;grid-template-columns:var(--lw,92px) minmax(0,1fr);gap:12px;align-items:stretch;}
.flow-lane.nolane{grid-template-columns:minmax(0,1fr);}
.lane-name{background:var(--accent-soft);color:var(--accent);font-weight:700;font-size:12.5px;line-height:1.45;
  border-radius:8px;display:flex;align-items:center;justify-content:center;text-align:center;padding:8px 6px;}
.flow-rows{display:flex;flex-direction:column;gap:26px;}
.flow-steps{display:grid;grid-template-columns:repeat(var(--n),minmax(0,1fr));column-gap:24px;row-gap:6px;}
.fphase{font-size:11.5px;font-weight:700;color:var(--sub);text-align:center;letter-spacing:.5px;
  border-bottom:2px solid var(--line);padding-bottom:2px;margin-bottom:2px;}
.fphase.hot{color:#c2521f;border-bottom-color:var(--hi);}
.fstep{position:relative;background:#fff;border:1px solid var(--box);border-radius:10px;padding:8px 10px 9px;min-height:70px;}
.fstep::after{content:"";position:absolute;right:-17px;top:50%;width:9px;height:9px;
  border-top:2px solid var(--accent);border-right:2px solid var(--accent);transform:translateY(-50%) rotate(45deg);}
.fstep.last::after{display:none;}
.fstep.wrap::after{right:50%;top:auto;bottom:-19px;transform:translateX(50%) rotate(135deg);}
.fstep .no{font-size:10.5px;font-weight:700;color:var(--accent);letter-spacing:.6px;line-height:1.3;}
.fstep .lb{font-size:13.6px;font-weight:700;color:var(--ink);line-height:1.45;margin-top:1px;}
.fstep .sb{font-size:12.2px;color:var(--sub);line-height:1.5;margin-top:3px;}
.fstep .nt{font-size:11.6px;color:var(--warn);line-height:1.45;margin-top:4px;}
.fstep .tag{font-size:10.5px;padding:0 6px;margin-left:4px;vertical-align:1px;}
.fstep.hot{border-color:var(--hi);background:var(--hi-soft);box-shadow:0 0 0 1px var(--hi) inset;}
.fstep.muted{border-style:dashed;background:#fafbfd;}
.fstep.strong{background:var(--accent);border-color:var(--accent);}
.fstep.strong .lb,.fstep.strong .no{color:#fff;} .fstep.strong .sb{color:#d5e3f1;}
.flow-legend{font-size:11.8px;color:var(--sub);margin-top:8px;}
.fpad{min-height:0;}
.flow-legend .tag{font-size:10.5px;padding:0 6px;margin:0 3px 0 10px;}
/* 产品谱系(多张实物图合成一张) */
figure.lineupfig .lineup{display:flex;flex-wrap:wrap;gap:12px 14px;margin:4px 0 2px;}
.lu-g{flex:0 0 calc(var(--n) * (100% + 14px) / var(--c) - 14px);min-width:0;display:flex;flex-direction:column;}
.lu-items{display:grid;grid-template-columns:repeat(var(--n),minmax(0,1fr));gap:10px 14px;flex:1;}
.lu-grp{font-size:12px;font-weight:700;color:var(--sub);letter-spacing:.5px;text-align:center;
  border-bottom:2px solid var(--line);padding:0 0 3px;margin-bottom:8px;line-height:1.5;}
.lu-grp.hot{color:#c2521f;border-bottom-color:var(--hi);}
.lu-item{border:1px solid var(--line);border-radius:9px;padding:8px 8px 9px;background:#fff;text-align:center;min-width:0;}
.lu-item.hot{border-color:var(--hi);box-shadow:0 0 0 1px var(--hi) inset;}
.shot .lu-item img{height:var(--ih,140px);width:100%;object-fit:contain;border:0;border-radius:4px;}
.lu-item .lb{font-size:13px;font-weight:700;color:var(--ink);line-height:1.4;margin-top:6px;}
.lu-item .sb{font-size:11.8px;color:var(--sub);line-height:1.45;margin-top:2px;}
.lu-item .miss{padding:12px;font-size:12px;}
/* 产业链 / 商业模式结构图 */
.chain{display:grid;align-items:stretch;margin:8px 0 6px;}
.ccol{min-width:0;display:flex;flex-direction:column;}
.chead{font-size:12px;font-weight:700;color:var(--sub);letter-spacing:.5px;text-align:center;
  padding:3px 0 5px;border-bottom:2px solid var(--line);margin-bottom:9px;line-height:1.45;}
.ccol.me .chead{color:#c2521f;border-bottom-color:var(--hi);}
.cnodes{display:flex;flex-direction:column;gap:8px;flex:1;justify-content:center;}
.cnode{border:1px solid var(--box);border-radius:9px;padding:7px 10px 8px;background:#fff;}
.cnode .lb{font-size:13.2px;font-weight:700;line-height:1.45;color:var(--ink);}
.cnode .sb{font-size:12px;color:var(--sub);line-height:1.5;margin-top:2px;}
.cnode .nt{font-size:11.5px;color:var(--warn);margin-top:3px;line-height:1.4;}
.cnode.strong{background:var(--accent);border-color:var(--accent);}
.cnode.strong .lb{color:#fff;} .cnode.strong .sb{color:#d5e3f1;} .cnode.strong .nt{color:#ffd9b8;}
.cnode.hot{border-color:var(--hi);background:var(--hi-soft);}
.cnode.muted{border-style:dashed;background:#fafbfd;}
.carrow{display:flex;flex-direction:column;align-items:stretch;justify-content:center;gap:5px;padding:26px 2px 0;}
.carrow .lk{font-size:11.2px;color:var(--accent);text-align:center;line-height:1.35;}
.carrow .lk.back{color:var(--good);}
.carrow .ln{position:relative;height:2px;background:var(--accent);margin:0 5px;}
.carrow .ln::after{content:"";position:absolute;right:-2px;top:-4px;width:8px;height:8px;
  border-top:2px solid var(--accent);border-right:2px solid var(--accent);transform:rotate(45deg);}
.carrow .ln.back{background:none;border-top:2px dashed var(--good);height:0;}
.carrow .ln.back::after{right:auto;left:-2px;top:-6px;border-color:var(--good);transform:rotate(-135deg);}
/* 图表目录 */
details.figidx{margin:12px 0;border:1px solid var(--line);border-radius:10px;background:var(--panel);padding:8px 16px;}
details.figidx>summary{cursor:pointer;font-size:13.5px;font-weight:600;color:var(--accent);padding:4px 0;}
.figidx .fgch{font-size:12.5px;font-weight:700;color:var(--ink);margin:12px 0 4px;}
.figidx ol{list-style:none;margin:0;padding:0;columns:2;column-gap:28px;}
.figidx li{font-size:12.6px;line-height:1.55;margin:0 0 4px;break-inside:avoid;}
.figidx li a{color:var(--ink);text-decoration:none;}
.figidx li a:hover{color:var(--accent);text-decoration:underline;}
.figidx .k{display:inline-block;min-width:44px;font-size:10.5px;font-weight:700;color:var(--sub);}
.figidx .k.ch{color:var(--series-1);} .figidx .k.im{color:#c2521f;} .figidx .k.dg{color:var(--good);} .figidx .k.tb{color:var(--accent);}
.footer{margin-top:60px;padding-top:16px;border-top:1px solid var(--line);color:var(--sub);font-size:12.5px;}
.footer p{margin:6px 0;}
/* 图片放大 */
#lb{position:fixed;inset:0;background:rgba(15,25,40,.82);display:none;align-items:center;justify-content:center;z-index:50;cursor:zoom-out;padding:24px;}
#lb.on{display:flex;}
#lb img{max-width:96vw;max-height:94vh;background:#fff;border-radius:6px;box-shadow:0 10px 40px rgba(0,0,0,.35);}
/* 窄屏目录按钮 */
#tocbtn{display:none;position:fixed;right:16px;bottom:18px;z-index:40;border:0;border-radius:999px;
  background:var(--accent);color:#fff;font-size:13px;font-weight:600;padding:9px 16px;box-shadow:0 4px 14px rgba(15,76,129,.35);cursor:pointer;}
@media (max-width:1180px){ .three-up{grid-template-columns:repeat(2,minmax(0,1fr));} }
@media (max-width:1000px){ .lineup.c4 .lu-g,.lineup.c5 .lu-g,.lineup.c6 .lu-g{flex-basis:100%;} .lineup .lu-items{grid-template-columns:repeat(3,minmax(0,1fr));} }
@media (max-width:1000px){
  nav.toc{display:none;} main{padding:22px 16px 60px;}
  .two-up,.three-up{grid-template-columns:minmax(0,1fr);}
  .half{max-width:none;}
  .two-up figure.shot>img{height:auto;max-height:360px;width:auto;max-width:100%;}
  #tocbtn{display:block;}
  body.tocopen nav.toc{display:block;position:fixed;left:0;top:0;bottom:0;z-index:45;box-shadow:4px 0 24px rgba(0,0,0,.18);}
  .figidx ol{columns:1;}
}
@media (max-width:760px){
  h1{font-size:23px;} h2{font-size:19px;}
  .flow-lane{grid-template-columns:minmax(0,1fr);}
  .flow-steps{grid-template-columns:minmax(0,1fr) !important;row-gap:22px;}
  .fphase,.fpad{display:none;}
  .fstep::after,.fstep.wrap::after{right:50%;top:auto;bottom:-17px;transform:translateX(50%) rotate(135deg);}
  .chain{grid-template-columns:minmax(0,1fr) !important;row-gap:4px;}
  .carrow{padding:4px 0;flex-direction:row;justify-content:center;gap:10px;}
  .carrow .ln{width:2px;height:22px;margin:0;}
  .carrow .ln::after{right:-4px;top:auto;bottom:-2px;transform:rotate(135deg);}
  .carrow .ln.back{display:none;}
  .lineup .lu-g{flex-basis:100%;} .lineup .lu-items{grid-template-columns:repeat(2,minmax(0,1fr));}
  .rm{grid-template-columns:minmax(0,1fr) !important;row-gap:24px;}
  .rstage::after{right:50%;top:auto;bottom:-19px;transform:translateX(50%) rotate(135deg);}
}
@media print{
  @page{size:A4;margin:12mm;}
  nav.toc,#tocbtn,#lb,#backbtn,#gltip{display:none !important;}
  .gl{border-bottom:0;}
  body{background:#fff;font-size:12.5px;}
  .layout{display:block;max-width:none;}
  main{padding:0;}
  figure,.shot,.card,.kpi,.tblock,.note,.plain,.tl,.two-up,.three-up,.flow,.chain,.lineup,.rm,.bcard,.brief-hero{break-inside:avoid;}
  h2,h3{break-after:avoid;}
  details.dv:not([open]){display:none;}
  /* 兜底:resize 没赶上纸面宽度时整图等比缩进纸面,不裁切(.chart 高度不能改 auto,ECharts resize 要读它) */
  .chart>div{width:100% !important;}
  .chart canvas{max-width:100% !important;height:auto !important;}
  details.figidx{display:none;}
  tbody tr:hover{background:inherit;}
}
"""

JS = r"""
(function () {
  'use strict';
  var P = ['#2a78d6','#eb6834','#1baf7a','#eda100','#e87ba4','#008300','#4a3aa7','#e34948'];
  var HI = '#eb6834', GREY = '#b9c3d1', FC = '#9dc0e8';
  var INK = '#1a2233', SUB = '#5a6478', GRID = '#eef1f6', AXIS = '#9aa4b5', SURF = '#ffffff';
  var FONT = '"Microsoft YaHei","PingFang SC","Segoe UI",system-ui,sans-serif';
  var SPECS = [];
  try { SPECS = JSON.parse(document.getElementById('chart-specs').textContent || '[]'); }
  catch (e) { console.error('chart-specs 解析失败', e); }
  var BYID = {};
  SPECS.forEach(function (s) { BYID[s.dom] = s; });

  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function nil(v) { return v === null || v === undefined || v === '' || v === '-' || (typeof v === 'number' && isNaN(v)); }
  function decs(v) { var s = String(v); var i = s.indexOf('.'); return (i < 0 || s.indexOf('e') >= 0) ? 0 : s.length - i - 1; }
  function fmt(v, d) {
    if (nil(v)) return '—';
    if (typeof v !== 'number') return String(v);
    var dd = (d === undefined || d === null) ? Math.min(decs(v), 3) : d;
    var s = v.toFixed(dd), neg = s.charAt(0) === '-';
    if (neg) s = s.slice(1);
    var pr = s.split('.');
    pr[0] = pr[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return (neg ? '-' : '') + pr.join('.');
  }
  function tight(u) { return !u || /^(%|‰|pct|pp|x|倍|×)/.test(u); }
  function wu(v, u, d) { var s = fmt(v, d); if (s === '—' || !u) return s; return s + (tight(u) ? '' : ' ') + u; }
  function dz(v) { return nil(v) ? '-' : v; }

  var tipBox = { confine: true, backgroundColor: 'rgba(255,255,255,.97)', borderColor: '#d8dfe9', borderWidth: 1,
    padding: [8, 11], textStyle: { color: INK, fontSize: 12.5, fontFamily: FONT },
    extraCssText: 'box-shadow:0 4px 16px rgba(20,35,60,.13);border-radius:8px;' };
  function mark(c) { return '<span style="display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:6px;background:' + c + '"></span>'; }
  function row(c, n, v) {
    return '<div style="display:flex;justify-content:space-between;gap:18px;line-height:1.7">' +
      '<span>' + mark(c) + esc(n) + '</span><b style="font-variant-numeric:tabular-nums">' + v + '</b></div>';
  }
  function isFc(s, i) { return s.fc !== null && s.fc !== undefined && s.fc >= 0 && i >= s.fc; }

  function catAxis(s, horiz) {
    var cats = s.categories, fc = s.fc;
    var lab = { color: SUB, fontSize: 11.5, rotate: s.rotate || 0, hideOverlap: true,
      interval: (s.interval !== undefined && s.interval !== null) ? s.interval : (cats.length > 16 ? 'auto' : 0) };
    if (fc !== null && fc !== undefined && fc >= 0) {
      lab.formatter = function (v) { var i = cats.indexOf(v); return (i >= fc) ? '{f|' + v + '}' : v; };
      lab.rich = { f: { color: AXIS, fontSize: 11.5 } };
    }
    return { type: 'category', data: cats, boundaryGap: true, inverse: !!horiz,
      axisLine: { lineStyle: { color: AXIS } }, axisTick: { show: false }, axisLabel: lab,
      name: horiz ? '' : (s.x_name || ''), nameTextStyle: { color: SUB, fontSize: 11 } };
  }
  function valAxis(name, unit, mn, mx, second) {
    var ax = { type: 'value', name: name || '', nameTextStyle: { color: SUB, fontSize: 11 },
      axisLine: { show: false }, axisTick: { show: false }, scale: false,
      axisLabel: { color: SUB, fontSize: 11, formatter: (unit === '%') ? '{value}%' : function (v) { return fmt(v); } },
      splitLine: { show: !second, lineStyle: { color: GRID } } };
    if (mn !== null && mn !== undefined) ax.min = mn;
    if (mx !== null && mx !== undefined) ax.max = mx;
    return ax;
  }

  /* 颜色分配:显式 color > colors 数组 > 本公司高亮(第二色) > 固定色板顺序(高亮时跳过第二色) > 其他灰 */
  function seriesColors(s) {
    var out = [], pal = P.slice(), hiName = s.hi_series;
    if (hiName !== null && hiName !== undefined) pal = P.filter(function (c) { return c !== HI; });
    var k = 0;
    s.series.forEach(function (se, i) {
      var c;
      if (se.color) c = se.color;
      else if (s.colors && s.colors[i]) c = s.colors[i];
      else if (hiName !== null && hiName !== undefined && se.name === hiName) c = HI;
      else if (hiName !== null && hiName !== undefined && s.others_grey) c = GREY;
      else if (/^(其他|其余|其它)/.test(se.name) && s.series.length > 2) c = GREY;
      else { c = pal[k % pal.length]; k++; }
      out.push(c);
    });
    return out;
  }
  /* 单序列柱:逐类目颜色 */
  function catColor(s, i, base) {
    var name = s.categories[i];
    if (s.cat_colors && s.cat_colors[i]) return s.cat_colors[i];
    var hi = s.hi_cats || [];
    if (hi.indexOf(i) >= 0) return HI;
    if (isFc(s, i)) return FC;
    if (hi.length && (s.others_grey || /^(其他|其余|其它)|合计$/.test(name))) return GREY;
    if (!hi.length && /^(其他|其余|其它)/.test(name)) return GREY;
    return base;
  }

  /* 参考线走 markLine;分段/预测底色默认由 applyBands 用 graphic 按整类目宽度画(markArea 在类目轴上只能从类目中心画到中心),
     applyBands 失败时才退回 markArea */
  function markHelper(s, horiz) {
    var areas = [], lines = [];
    (s._bandFallback ? (s.bands || []) : []).forEach(function (b, k) {
      var a = {}, z = {};
      a[horiz ? 'yAxis' : 'xAxis'] = s.categories[b.s]; z[horiz ? 'yAxis' : 'xAxis'] = s.categories[b.e];
      a.name = b.label || '';
      a.itemStyle = { color: b.fc ? 'rgba(157,192,232,0.14)' : (k % 2 ? 'rgba(15,76,129,0.035)' : 'rgba(15,76,129,0.06)') };
      areas.push([a, z]);
    });
    (s.marklines || []).forEach(function (m) {
      var o = { label: { formatter: m.label || '', color: SUB, fontSize: 10.5, position: m.pos || 'insideStartTop' },
        lineStyle: { type: 'dashed', color: m.color || '#8a94a6', width: 1 } };
      if (m.y !== undefined && m.y !== null) o[horiz ? 'xAxis' : 'yAxis'] = m.y;
      else if (m.x !== undefined && m.x !== null) { o[horiz ? 'yAxis' : 'xAxis'] = m.x; o.label.position = 'end'; }
      lines.push(o);
    });
    if (!areas.length && !lines.length) return null;
    var h = { name: '__mark', type: 'line', data: s.categories.map(function () { return '-'; }), silent: true,
      symbol: 'none', lineStyle: { opacity: 0 }, tooltip: { show: false }, z: 0 };
    if (areas.length) h.markArea = { silent: true, data: areas,
      label: { show: true, position: horiz ? 'insideRight' : 'insideTop', color: '#7d889b', fontSize: 10.5 } };
    if (lines.length) h.markLine = { silent: true, symbol: 'none', data: lines };
    if (s.y2) h.yAxisIndex = 0;
    return h;
  }

  function applyBands(ch, s) {
    var bands = s.bands || [];
    if (!bands.length || s.type === 'pie' || s._bandFallback) return;
    var horiz = s.type === 'barh';
    var m = ch.getModel();
    var ax = m.getComponent(horiz ? 'yAxis' : 'xAxis', 0).axis;
    var g = m.getComponent('grid', 0).coordinateSystem.getRect();
    var bw = ax.getBandWidth(), els = [];
    bands.forEach(function (b, k) {
      var p0 = ax.toGlobalCoord(ax.dataToCoord(b.s)), p1 = ax.toGlobalCoord(ax.dataToCoord(b.e));
      var a = Math.min(p0, p1) - bw / 2, z = Math.max(p0, p1) + bw / 2;
      var fill = b.fc ? 'rgba(157,192,232,0.16)' : (k % 2 ? 'rgba(15,76,129,0.035)' : 'rgba(15,76,129,0.06)');
      els.push({ type: 'rect', silent: true, z: -1,
        shape: horiz ? { x: g.x, y: a, width: g.width, height: z - a } : { x: a, y: g.y, width: z - a, height: g.height },
        style: { fill: fill } });
      if (b.label) els.push({ type: 'text', silent: true, z: -1,
        x: horiz ? g.x + g.width - 4 : (a + z) / 2, y: horiz ? a + 3 : g.y - 3,
        style: { text: b.label, fill: '#7d889b', fontSize: 10.5, fontFamily: FONT,
          align: horiz ? 'right' : 'center', verticalAlign: horiz ? 'top' : 'bottom' } });
    });
    ch.setOption({ graphic: { elements: els } }, { replaceMerge: ['graphic'] });
  }

  function labelCfg(s, se, pos, u, d, skipIdx) {
    var mode = (se.labels !== undefined && se.labels !== null) ? se.labels : s.labels;
    if (!mode) return { show: false };
    var last = -1;
    se.data.forEach(function (v, i) { if (!nil(v)) last = i; });
    return { show: true, position: pos, color: SUB, fontSize: 10.5,
      formatter: function (p) {
        if (mode === 'last' && p.dataIndex !== last) return '';
        if (skipIdx !== undefined && skipIdx !== null && p.dataIndex === skipIdx) return '';
        var v = se.data[p.dataIndex]; if (nil(v)) return '';
        return fmt(v, se.digits !== undefined ? se.digits : s.digits) + (u === '%' ? '%' : '');
      } };
  }

  /* 折线:按断点(口径变化)切段,预测段虚线;同名同色,图例合一 */
  function lineSeries(s, se, color, i, isArea) {
    var n = s.categories.length, cuts = [0].concat(s.breaks || []).concat([n]);
    cuts = cuts.filter(function (v, k, a) { return a.indexOf(v) === k; }).sort(function (a, b) { return a - b; });
    var out = [], fc = (s.fc !== null && s.fc !== undefined && s.fc >= 0) ? s.fc : n;
    var u = se.unit || (se.yAxisIndex ? s.y2_unit : s.unit);
    var hiW = (s.hi_series !== undefined && s.hi_series !== null && se.name === s.hi_series) ? 3.2 : 2;
    function piece(a, b, dashed, skip) {
      var data = s.categories.map(function (_, k) { return (k >= a && k < b) ? dz(se.data[k]) : '-'; });
      var o = { name: se.name, type: 'line', data: data, symbol: 'circle', symbolSize: hiW > 2 ? 8 : 7,
        connectNulls: false, smooth: !!s.smooth,
        lineStyle: { width: hiW, color: color, type: dashed ? 'dashed' : 'solid' },
        itemStyle: { color: dashed ? '#fff' : color, borderColor: color, borderWidth: 2 },
        emphasis: { focus: 'series' }, z: (hiW > 2 ? 5 : 3) - (dashed ? 1 : 0),  /* 预测虚线段压在实线段下,衔接点保持实心 */
        label: labelCfg(s, se, 'top', u, null, skip), labelLayout: { hideOverlap: true } };
      if (se.yAxisIndex) o.yAxisIndex = se.yAxisIndex;
      if (isArea) o.areaStyle = { color: color, opacity: dashed ? 0.06 : 0.12 };
      if (se.stack) o.stack = se.stack;
      return o;
    }
    for (var k = 0; k < cuts.length - 1; k++) {
      var a = cuts[k], b = cuts[k + 1];
      if (fc <= a) out.push(piece(a, b, true));
      else if (fc < b) { out.push(piece(a, fc, false)); out.push(piece(fc - 1, b, true, fc - 1)); }
      else out.push(piece(a, b, false));
    }
    return out;
  }

  function barSeries(s, se, color, i, stacked, isTop, horiz) {
    var single = s.series.length === 1 || s.type === 'bar' || s.type === 'barh';
    var u = se.unit || (se.yAxisIndex ? s.y2_unit : s.unit);
    var rad = horiz ? [0, 4, 4, 0] : [4, 4, 0, 0];
    var data = se.data.map(function (v, k) {
      var it = { value: dz(v) };
      if (!nil(v) && typeof v === 'number' && v < 0 && !stacked) it.label = { position: horiz ? 'left' : 'bottom' };  /* 负值标签放到柱子外端 */
      if (single && s.series.length === 1) it.itemStyle = { color: catColor(s, k, color) };
      else if (isFc(s, k)) it.itemStyle = { opacity: 0.45 };
      return it;
    });
    var o = { name: se.name, type: 'bar', data: data, barMaxWidth: s.bar_width || (stacked ? 44 : (s.series.length > 1 ? 26 : 34)),
      itemStyle: { color: color, borderColor: stacked ? SURF : undefined, borderWidth: stacked ? 1 : 0,
        borderRadius: stacked ? (isTop ? rad : 0) : rad },
      emphasis: { focus: 'series' }, labelLayout: { hideOverlap: true } };
    if (stacked) o.stack = se.stack || 'total';
    if (se.yAxisIndex) o.yAxisIndex = se.yAxisIndex;
    var showLab = (se.labels !== undefined && se.labels !== null) ? se.labels : s.labels;
    if (s.series.length === 1 && (s.type === 'bar' || s.type === 'barh') && showLab === undefined) showLab = true;
    if (showLab && !stacked) {
      o.label = { show: true, position: horiz ? 'right' : 'top', color: INK, fontSize: 11, fontWeight: 600,
        formatter: function (p) { var v = se.data[p.dataIndex]; return nil(v) ? '' : fmt(v, se.digits !== undefined ? se.digits : s.digits) + (u === '%' ? '%' : (s.label_unit ? u : '')); } };
    } else if (showLab && stacked) {
      o.label = { show: true, position: 'inside', color: '#fff', fontSize: 10,
        formatter: function (p) {
          var v = s.pct ? s.pctData[i][p.dataIndex] : se.data[p.dataIndex];
          if (nil(v)) return '';
          var tot = s.pct ? 100 : s.maxTotal;
          if (Math.abs(v) < tot * 0.06) return '';
          return fmt(v, s.pct ? 0 : (se.digits !== undefined ? se.digits : s.digits)) + (s.pct ? '%' : '');
        } };
    }
    return o;
  }

  function build(s) {
    var t = s.type, horiz = (t === 'barh');
    var colors = seriesColors(s);
    var multi = s.series.length > 1;
    var opt = {
      textStyle: { fontFamily: FONT, color: INK },
      animationDuration: 450,
      grid: { left: 10, right: horiz ? 64 : (s.y2 ? 12 : 18), top: 42, bottom: 8, containLabel: true },
      legend: { type: 'scroll', top: 2, itemWidth: 10, itemHeight: 10, itemGap: 14, icon: 'roundRect',
        textStyle: { color: SUB, fontSize: 12 } }
    };
    if (t === 'pie') {
      var d = s.categories.map(function (c, k) {
        return { name: c, value: s.series[0].data[k], itemStyle: { color: (s.cat_colors && s.cat_colors[k]) || ((s.hi_cats || []).indexOf(k) >= 0 ? HI : P[k % P.length]) } };
      });
      opt.legend.data = s.categories;
      opt.tooltip = Object.assign({ trigger: 'item', formatter: function (p) {
        return '<div style="font-weight:700;margin-bottom:3px">' + esc(p.name) + '</div>' +
          row(p.color, s.series[0].name, wu(p.value, s.unit, s.digits)) + row('#fff', '占比', fmt(p.percent, 1) + '%'); } }, tipBox);
      opt.series = [{ type: 'pie', name: s.series[0].name, radius: ['42%', '68%'], center: ['50%', '56%'],
        avoidLabelOverlap: true, itemStyle: { borderColor: SURF, borderWidth: 2, borderRadius: 4 },
        label: { color: INK, fontSize: 11.5, formatter: function (p) { return p.name + '\n' + fmt(p.percent, 1) + '%'; } },
        labelLine: { length: 10, length2: 8 }, data: d }];
      return opt;
    }
    var series = [], legendNames = [];
    if (t === 'waterfall') {
      var se0 = s.series[0], run = 0, base = [], up = [], down = [], tot = [], cum = [];
      se0.data.forEach(function (v, k) {
        var isT = (s.totals || []).indexOf(k) >= 0;
        if (nil(v)) { base.push('-'); up.push('-'); down.push('-'); tot.push('-'); cum.push(run); return; }
        if (isT) { base.push(0); tot.push(v); up.push('-'); down.push('-'); run = v; }
        else if (v >= 0) { base.push(run); up.push(v); down.push('-'); tot.push('-'); run += v; }
        else { run += v; base.push(run); down.push(-v); up.push('-'); tot.push('-'); }
        cum.push(run);
      });
      s._cum = cum;
      var lab = function (arr, sign) { return { show: true, position: 'top', color: INK, fontSize: 10.5, fontWeight: 600,
        formatter: function (p) { var v = se0.data[p.dataIndex]; return nil(v) ? '' : (sign && v > 0 ? '+' : '') + fmt(v, s.digits); } }; };
      series.push({ name: '__base', type: 'bar', stack: 'wf', data: base, itemStyle: { color: 'transparent' }, emphasis: { disabled: true }, tooltip: { show: false }, barMaxWidth: 44 });
      series.push({ name: s.wf_names[0], type: 'bar', stack: 'wf', data: tot, itemStyle: { color: P[0], borderRadius: [4, 4, 0, 0] }, label: lab(tot, false), barMaxWidth: 44 });
      series.push({ name: s.wf_names[1], type: 'bar', stack: 'wf', data: up, itemStyle: { color: P[2], borderRadius: [4, 4, 0, 0] }, label: lab(up, true), barMaxWidth: 44 });
      series.push({ name: s.wf_names[2], type: 'bar', stack: 'wf', data: down, itemStyle: { color: P[7], borderRadius: [4, 4, 0, 0] }, label: lab(down, true), barMaxWidth: 44 });
      legendNames = s.wf_names.slice();
      opt.xAxis = catAxis(s, false);
      opt.yAxis = valAxis(s.y_name, s.unit, s.y_min, s.y_max);
      opt.series = series;
      opt.legend.data = legendNames;
      opt.tooltip = Object.assign({ trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: function (ps) {
        var i = ps[0].dataIndex, v = se0.data[i], isT = (s.totals || []).indexOf(i) >= 0;
        return '<div style="font-weight:700;margin-bottom:3px">' + esc(s.categories[i]) + '</div>' +
          row(isT ? P[0] : (v >= 0 ? P[2] : P[7]), isT ? s.wf_names[0] : '变动', (isT || v < 0 ? '' : '+') + wu(v, s.unit, s.digits)) +
          (isT ? '' : row('#fff', '累计', wu(cum[i], s.unit, s.digits))); } }, tipBox);
      var mh0 = markHelper(s, false); if (mh0) opt.series.push(mh0);
      return opt;
    }
    /* 百分比堆积 */
    if (t === 'stack') {
      var n = s.categories.length, tots = [];
      for (var k = 0; k < n; k++) { var sm = 0; s.series.forEach(function (se) { var v = se.data[k]; if (!nil(v) && typeof v === 'number') sm += v; }); tots.push(sm); }
      s._tots = tots; s.maxTotal = Math.max.apply(null, tots.map(Math.abs).concat([1]));
      if (s.pct) s.pctData = s.series.map(function (se) { return se.data.map(function (v, k) { return (nil(v) || !tots[k]) ? null : +(v / tots[k] * 100).toFixed(2); }); });
    }
    s.series.forEach(function (se, i) {
      var st = se.type || (t === 'line' || t === 'area' ? 'line' : 'bar');
      if (t === 'combo' && !se.type) st = 'bar';
      if (legendNames.indexOf(se.name) < 0) legendNames.push(se.name);
      if (st === 'line') {
        lineSeries(s, se, colors[i], i, t === 'area' || se.area || s.area).forEach(function (o) { series.push(o); });
      } else {
        var stacked = (t === 'stack') || (t === 'combo' && (se.stack || s.stack));
        var top = stacked && (i === s.series.length - 1 || (t === 'combo' && !(s.series.slice(i + 1).some(function (x) { return (x.type || 'bar') === 'bar'; }))));
        var o = barSeries(s, se, colors[i], i, stacked, top, horiz);
        if (t === 'stack' && s.pct) o.data = s.pctData[i].map(function (v, k) { var it = { value: dz(v) }; if (isFc(s, k)) it.itemStyle = { opacity: 0.45 }; return it; });
        series.push(o);
      }
    });
    if (t === 'stack' && s.total_label && !s.pct) {
      /* 柱顶合计:同一 stack 里叠一根 0 高度透明柱,标签放在它顶上(即整根堆积柱顶上),某段为 null 也不丢 */
      series.push({ name: '__total', type: 'bar', stack: 'total', data: s._tots.map(function () { return 0; }),
        barMaxWidth: s.bar_width || 44, itemStyle: { color: 'transparent' }, silent: true, tooltip: { show: false },
        emphasis: { disabled: true },
        label: { show: true, position: 'top', color: INK, fontSize: 11, fontWeight: 700,
          formatter: function (p) { var v = (s.total_values && !nil(s.total_values[p.dataIndex])) ? s.total_values[p.dataIndex] : s._tots[p.dataIndex]; return v ? fmt(+v.toFixed(3), s.digits) : ''; } } });
    }
    var mh = markHelper(s, horiz); if (mh) series.push(mh);
    var u0 = s.pct ? '%' : s.unit;
    if (horiz) { opt.yAxis = catAxis(s, true); opt.xAxis = valAxis(s.y_name, u0, s.y_min, s.y_max); }
    else {
      opt.xAxis = catAxis(s, false);
      opt.yAxis = [valAxis(s.y_name, u0, s.pct ? 0 : s.y_min, s.pct ? 100 : s.y_max)];
      if (s.y2) opt.yAxis.push(valAxis(s.y2_name, s.y2_unit, s.y2_min, s.y2_max, true));
    }
    opt.series = series;
    opt.legend.data = legendNames;
    if (!multi || s.legend === false) { opt.legend.show = false; opt.grid.top = (s.y_name && !horiz) ? 30 : 18; }
    opt.tooltip = Object.assign({ trigger: 'axis', confine: true,
      axisPointer: { type: (t === 'line' || t === 'area') ? 'line' : 'shadow', lineStyle: { color: AXIS } },
      formatter: function (ps) {
        if (!ps || !ps.length) return '';
        var i = ps[0].dataIndex, h = '<div style="font-weight:700;margin-bottom:3px">' + esc(s.categories[i]) +
          (isFc(s, i) ? ' <span style="color:#9aa4b5;font-weight:400">' + esc(s.fc_label || '预测') + '</span>' : '') + '</div>';
        var body = '';
        s.series.forEach(function (se, k) {
          var u = se.unit || (se.yAxisIndex ? s.y2_unit : s.unit), dg = se.digits !== undefined ? se.digits : s.digits;
          var c = colors[k];
          if (s.series.length === 1 && (t === 'bar' || t === 'barh')) c = catColor(s, i, colors[0]);
          var v = se.data[i], txt = wu(v, u, dg);
          if (t === 'stack' && s.pct) txt = fmt(s.pctData[k][i], 1) + '%<span style="color:#9aa4b5;font-weight:400">（' + wu(v, u, dg) + '）</span>';
          body += row(c, se.name, txt);
        });
        if (t === 'stack' && s.series.length > 1 && !s.no_total) body += '<div style="border-top:1px solid #e4e8ef;margin-top:3px;padding-top:2px">' + row('#fff', '合计', wu((s.total_values && !nil(s.total_values[i])) ? s.total_values[i] : s._tots[i], s.unit, s.digits)) + '</div>';
        return h + body;
      } }, tipBox);
    return opt;
  }

  var made = [], total = SPECS.length, printing = false;
  window.__charts = { total: total, made: 0, errors: 0 };
  function init(el) {
    if (!el || el.__done) return;
    el.__done = true;
    var s = BYID[el.id];
    if (!s) return;
    try {
      var ch = echarts.init(el, null, { renderer: 'canvas' });
      var opt = build(s);
      if (printing) opt.animation = false;   /* 打印时新建的图不播动画,免得截到半截柱子 */
      ch.setOption(opt);
      ch.__spec = s;
      try { applyBands(ch, s); }
      catch (e2) { s._bandFallback = true; ch.setOption(build(s), true); }
      made.push(ch);
      window.__charts.made = made.length;
    } catch (e) {
      window.__charts.errors++;
      el.innerHTML = '<div class="chart-err">图表渲染失败:' + esc(e && e.message || e) + '</div>';
      console.error('chart ' + el.id, e);
    }
  }
  var els = Array.prototype.slice.call(document.querySelectorAll('.chart[id]'));
  function initAll() { els.forEach(init); }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) { if (en.isIntersecting) { init(en.target); io.unobserve(en.target); } });
    }, { rootMargin: '900px 0px' });
    els.forEach(function (el) { io.observe(el); });
    var q = els.slice(), idle = function () {
      var el = q.shift(); if (!el) return;
      init(el); setTimeout(idle, 16);
    };
    window.addEventListener('load', function () { setTimeout(idle, 250); });
  } else { initAll(); }
  var rt = null;
  /* 尺寸变化:先收起悬停提示(防止旧位置的 tooltip 撑出横向滚动),再重排 */
  window.addEventListener('resize', function () {
    made.forEach(function (c) { c.dispatchAction({ type: 'hideTip' }); });
    clearTimeout(rt); rt = setTimeout(function () { made.forEach(function (c) { c.resize(); try { applyBands(c, c.__spec); } catch (e) {} }); }, 120); });
  function reflow() {
    made.forEach(function (c) {
      c.dispatchAction({ type: 'hideTip' });
      c.resize({ animation: { duration: 0 } });
      try { applyBands(c, c.__spec); } catch (e) {}
    });
  }
  /* 打印:matchMedia('print') 变化时版面已是打印版面,此时 resize 才能拿到纸面宽度(beforeprint 时仍是屏幕宽度) */
  function toPrint(on) { printing = on; if (on) initAll(); reflow(); }
  window.addEventListener('beforeprint', function () { toPrint(true); });
  window.addEventListener('afterprint', function () { toPrint(false); });
  if (window.matchMedia) {
    var mqp = window.matchMedia('print'), onmq = function (e) { toPrint(!!e.matches); };
    if (mqp.addEventListener) mqp.addEventListener('change', onmq); else if (mqp.addListener) mqp.addListener(onmq);
  }

  /* 目录:当前节高亮 */
  var links = {}, heads = [];
  Array.prototype.forEach.call(document.querySelectorAll('nav.toc a[href^="#"]'), function (a) { links[a.getAttribute('href').slice(1)] = a; });
  Array.prototype.forEach.call(document.querySelectorAll('main h2[id], main h3[id]'), function (h) { if (links[h.id]) heads.push(h); });
  var cur = null;
  function spy() {
    var y = window.innerHeight * 0.3, pick = null;
    for (var k = 0; k < heads.length; k++) { if (heads[k].getBoundingClientRect().top <= y) pick = heads[k]; else break; }
    if (!pick && heads.length) pick = heads[0];
    if (pick && pick !== cur) {
      if (cur && links[cur.id]) links[cur.id].classList.remove('on');
      cur = pick; var a = links[cur.id]; a.classList.add('on');
      var nav = document.querySelector('nav.toc');
      if (nav && nav.scrollHeight > nav.clientHeight) {
        var r = a.getBoundingClientRect(), nr = nav.getBoundingClientRect();
        if (r.top < nr.top + 40 || r.bottom > nr.bottom - 40) nav.scrollTop += (r.top - nr.top) - nav.clientHeight / 3;
      }
    }
  }
  var st = null;
  window.addEventListener('scroll', function () { if (st) return; st = setTimeout(function () { st = null; spy(); }, 80); }, { passive: true });
  spy();

  /* 窄屏目录按钮 */
  var btn = document.getElementById('tocbtn');
  if (btn) btn.addEventListener('click', function () { document.body.classList.toggle('tocopen'); });
  Array.prototype.forEach.call(document.querySelectorAll('nav.toc a'), function (a) {
    a.addEventListener('click', function () { document.body.classList.remove('tocopen'); });
  });

  /* 正文交叉引用:点「图 x-y」「见 x.y」跳过去,底部出现「返回原处」 */
  var back = document.getElementById('backbtn'), backY = null;
  Array.prototype.forEach.call(document.querySelectorAll('a.xref'), function (a) {
    a.addEventListener('click', function () {
      backY = window.pageYOffset;
      if (back) back.classList.add('on');
      var id = a.getAttribute('href').slice(1), el = document.getElementById(id);
      if (el && el.tagName === 'FIGURE') { el.style.boxShadow = '0 0 0 3px rgba(235,104,52,.45)'; setTimeout(function () { el.style.boxShadow = ''; }, 1600); }
    });
  });
  if (back) back.addEventListener('click', function () {
    if (backY !== null) window.scrollTo({ top: backY, behavior: 'smooth' });
    back.classList.remove('on'); backY = null;
  });
  /* 并排图:图题区(图题 + 副题)等高,图区上下对齐 */
  function eqHeads() {
    Array.prototype.forEach.call(document.querySelectorAll('.two-up,.three-up'), function (g) {
      var hs = Array.prototype.slice.call(g.querySelectorAll(':scope > figure > .fig-h'));
      hs.forEach(function (h) { h.style.minHeight = ''; });
      if (hs.length < 2) return;
      var top0 = hs[0].parentNode.offsetTop, same = hs.every(function (h) { return Math.abs(h.parentNode.offsetTop - top0) < 4; });
      if (!same) return;
      var mx = Math.max.apply(null, hs.map(function (h) { return h.offsetHeight; }));
      hs.forEach(function (h) { h.style.minHeight = mx + 'px'; });
    });
  }
  eqHeads();
  window.addEventListener('load', eqHeads);
  var eqT = null;
  window.addEventListener('resize', function () { clearTimeout(eqT); eqT = setTimeout(eqHeads, 150); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(eqHeads);

  /* 图片点击放大 */
  var lb = document.getElementById('lb'), lbi = lb ? lb.querySelector('img') : null;
  Array.prototype.forEach.call(document.querySelectorAll('.shot img'), function (im) {
    im.addEventListener('click', function () { if (!lb) return; lbi.src = im.src; lbi.alt = im.alt; lb.classList.add('on'); });
  });
  if (lb) {
    lb.addEventListener('click', function () { lb.classList.remove('on'); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') lb.classList.remove('on'); });
  }
})();
"""


# 基金经理版:术语悬停释义(正文里 .gl 术语;悬停 / 聚焦 / 点按显示,定位夹在视口内;不依赖任何外部资源)
GL_JS = r"""
(function () {
  var tip = document.getElementById('gltip');
  if (!tip) return;
  var cur = null, hideT = null;
  function show(el) {
    clearTimeout(hideT);
    cur = el;
    tip.innerHTML = '';
    var t = document.createElement('div');
    t.textContent = el.getAttribute('data-tip') || '';
    tip.appendChild(t);
    var id = el.getAttribute('data-gl');
    if (id && document.getElementById(id)) {
      var a = document.createElement('a');
      a.href = '#' + id; a.textContent = '查看术语词典 →';
      tip.appendChild(a);
    }
    tip.classList.add('on');
    var r = el.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    var x = Math.min(Math.max(8, r.left), window.innerWidth - w - 8);
    var y = r.bottom + 6;
    if (y + h > window.innerHeight - 8) y = Math.max(8, r.top - h - 6);
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }
  function hide() { tip.classList.remove('on'); cur = null; }
  function later() { clearTimeout(hideT); hideT = setTimeout(function () { if (!tip.matches(':hover')) hide(); }, 160); }
  Array.prototype.forEach.call(document.querySelectorAll('.gl'), function (el) {
    el.addEventListener('mouseenter', function () { show(el); });
    el.addEventListener('mouseleave', later);
    el.addEventListener('focus', function () { show(el); });
    el.addEventListener('blur', later);
    el.addEventListener('click', function (e) {
      e.stopPropagation();
      if (cur === el && tip.classList.contains('on')) hide(); else show(el);
    });
  });
  tip.addEventListener('mouseleave', later);
  document.addEventListener('click', function (e) { if (!tip.contains(e.target)) hide(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') hide(); });
  window.addEventListener('scroll', function () { if (cur) hide(); }, { passive: true });
})();
"""
