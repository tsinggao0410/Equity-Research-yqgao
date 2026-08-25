# 06 · HTML 设计系统 + Chart.js cookbook + 交付

> ★ **当前版本 = 咨询级重排（2026-07-21，BCG/Bain 风）——以此为准，下文若有旧描述以本块覆盖：**
> - **字体（硬约束）**：单一 per-script serif 栈 `"Times New Roman",Times,"KaiTi","楷体","STKaiti",serif` → 拉丁/数字=Times New Roman，中文=楷体（浏览器逐字回退）。数字统一 `font-variant-numeric:tabular-nums` + 右对齐。Chart.js 全局 `FONT` 同栈。系统字体（用户 Windows 本地有），无 web font/CDN。
> - **配色**：结构色 petrol-navy `--accent:#14384f`（标题/目录/表头/规则线）；8 路哑光数据色 `--s1..--s8`（navy/teal/gold/burgundy/slate/olive/steel/mauve）；涨跌=深绿 `--good:#1a6b4f` / 砖红 `--bad:#a1382f`；暖白纸底 `--bg:#fdfcf9`。light+dark 双主题（token 级，`prefers-color-scheme` + `data-theme`）。
> - **咨询排版**：h1 顶部 accent 双线+字距；h2 左 accent 竖条+底 hairline；卡片扁平化（无阴影、hairline 边、圆角 3-4px）；表头深色反白；KPI 分隔线网格；大量留白。
> - **直标数据（BCG 手法，已实现的全局 Chart.js 插件）**：`stackTotals`（营收堆积柱顶标合计）+ `endLabels`（ROE/毛利率/净利率 折线右端直标值）——`chartDefaults()` 里 `Chart.register(stackTotals,endLabels)`，按 `options.plugins.{stackTotals:{on:true}|endLabels:{series:[{di,fmt}]}}` 开启，带 `layout.padding.right` 防裁剪。
> - **时间序列铁律**：所有时序图/表 **时间作横轴、项目作纵轴**（营收/杜邦/费率/周线/分部/毛净利率 均已如此）；估值范式条形图是横截面排名（`indexAxis:'y'`），非时序，保留。

Phase 6（生成页面 / 改模板 / 改图表）必读。本文档 = **页面契约 + Chart.js 约定 + 交付验收**，描述已落地实现，不是重新发明。三份实现文件为准：

- 壳 + CSS：`C:/Users/youqi/.claude/skills/equity-onepager-interactive/templates/onepager_template.html`
- 渲染 + 交互：`C:/Users/youqi/.claude/skills/equity-onepager-interactive/templates/app.js`
- 计算引擎：`C:/Users/youqi/.claude/skills/equity-onepager-interactive/scripts/model_engine.js`
- 装配脚本：`C:/Users/youqi/.claude/skills/equity-onepager-interactive/scripts/build_page.py`

> 改任何图表 / 色板 / 交互前，先读对应 app.js 函数，别在 build 层或 CSS 里重复实现渲染逻辑。所有渲染在客户端，build 只做字符串注入。

---

## 1. 架构：5 段注入 → 单文件

`build_page.py` 把 5 段代码注入模板壳，产出一个自包含 `onepager.html`（Chart.js + 引擎 + app + 数据 + 反馈标注层全内联，离线可开）。

### 1.1 注入顺序（关键：先替元数据 token，再注 JS）
`build()` 分两步，**顺序不可换**：

1. **元数据 token 先替**（`str.replace`）：`{{TITLE}}` `{{NAME}}` `{{TICKER}}` `{{MARKET}}` `{{DATA}}`。
   - `{{DATA}}` = `json.dumps(model, ensure_ascii=False).replace("</","<\\/")`（`<\/` 转义防止 `</script>` 提前闭合）。
   - `{{MARKET}}` 经 `market_label()`：`A→A股 / HK→港股 / US→美股`。
   - 先替 token 的原因：**注入的 JS 里可能含 `{{...}}` 字面量**，若后注 JS 再替 token 会误伤。
2. **再注四段 JS 占位符**（HTML 注释形态，`str.replace`）：
   - `/*__CHARTJS__*/` ← `scripts/vendor/chart.umd.min.js`（Chart.js 4.4.9）
   - `/*__ENGINE__*/` ← `scripts/model_engine.js`（挂 `window.EONE`）
   - `/*__APP__*/` ← `templates/app.js`（挂 `window.__EONE_APP__`）
   - `/*__ANNOT__*/` ← `templates/annot.js`（反馈标注层，挂 `window.__EONE_FB__`；`--no-annot` 可置空出只读版）
   - 各占位符独立 `<script>`，`{{DATA}}` 在 app 之前那段 `window.__DATA__ = {{DATA}};`；annot 最后（依赖 DOM 与 `__DATA__.feedback`，与 app.js 解耦）。
   - `main()` 还会补 `feedback.report_id/rag_ws/autosync` 与 `meta.version` 缺省值；`--endpoint`/`--version` 可命令行覆盖（见 `08-feedback-loop.md`）。

### 1.2 运行时数据流
```
build_page.py ──inline──> onepager.html
                              │
   window.__DATA__ (page_model.json)  window.EONE (model_engine.js)
                              │            │
                          app.js boot() ── 全客户端渲染
```
- `app.js` 消费 `window.__DATA__`（= page_model）+ `window.EONE`（引擎），**零网络、零 DOM 依赖外部**。
- `D = window.__DATA__`；`MODEL = D.part3`（Part3 可被滑块就地改写的活模型切片）；`EONE = window.EONE`。

### 1.3 命令
```
python scripts/build_page.py --model _workspace/<ticker>/page_model.json --out _workspace/<ticker>/onepager.html
```
可选覆盖 `--template --chartjs --engine --app --annot`（默认取 skill 内标准路径）；`--no-annot` 出无标注只读版；`--endpoint <worker URL>` 把反馈云端烧进页面；`--version v3` 刷版本徽章。输出打印 `wrote <path> (NN KB)`。
上线到反馈平台用 `python scripts/deploy_page.py --ticker <代码> --model <page_model> [--endpoint …]`（见 `08`）。

---

## 2. 页面契约（DOM 挂点 + 色板 + 排版 + 目录 + 角标）

### 2.1 色板（CSS 自定义属性，light + dark 双块）
定义在模板 `<style>` `:root`，dark 由 `@media (prefers-color-scheme: dark)` + `:root[data-theme="dark"]`（主题按钮翻转 `data-theme` 强制覆盖）。**颜色一律走 `var(--x)`，markup 里不硬编码。**

| 变量 | light | 语义 |
|---|---|---|
| `--accent` | `#0b5fff` | 主强调（h2 左边框、角标、目标市值、按钮） |
| `--fg / --bg / --muted / --line` | `#1a1d23 / #fff / #6a7180 / #e4e7ec` | 文字/底/次要/描边 |
| `--card / --panel` | `#f7f8fa / #fcfcfb` | 卡片底/面板底 |
| `--hl` | `#fff7d6` | 角标 hover + 参考文献 `:target/.flash` 暖高亮 |
| `--good / --bad` | `#127a4a / #c8302f` | 正/负 |
| `--grid / --baseline` | `#e6e8ec / #c3c2b7` | 图网格/零线 |
| `--s1..--s8` | `#0b5fff #1baf7a #eda100 #00a3a3 #7a5af5 #e34948 #e87ba4 #eb6834` | 8 series（图表分部/多线） |
| `--hist / --fcst` | `#f4f6f9 / #fffaf0` | 表格历史列底/预测列底 |

**buyside 单元格语义色**（利润表配色，镜像 buyside-model-builder）：
- `--cell-actual` `#0b3fd6` 蓝 = 财报实际（锁定，class `.c-actual`）
- `--cell-assume-bg/fg` `#fff4c2 / #8a5b00` 黄 = 可调假设（`input.assume` / `.c-assume` / `.numbox`）
- `--cell-calc` `#1a1d23` 黑 = 公式推导（`.c-calc`）
- `--cell-link` `#0a7a3f` 绿 = 跨表勾稽（`.c-link`）

dark 块给出全部对应值（如 `--accent:#6ea2ff`、`--s1:#6ea2ff`）。app.js 通过 `cv(name)=getComputedStyle(root).getPropertyValue(name)` + `PAL()` 读取，**主题切换后必须 rebuild 全图**（见 §3.6）。

### 2.2 字体
- **模板实际在用**（`:root --serif`）：`"Times New Roman",Times,"KaiTi","楷体","STKaiti",serif` —— per-script 逐字回退（拉丁走 TNR、CJK 回退楷体），`body{font:15.5px/1.72}`，`font-feature-settings:"tnum" 1`。无楷体环境可换回 sans 栈 `-apple-system,"Segoe UI","Microsoft YaHei","PingFang SC",system-ui,sans-serif`。
- **★字号纪律（2026-07-25 用户反馈固化）**：认知主体（Driver/建模逻辑/口径/原句）**不许当脚注排** ——
  `.sm-body/.sm-logic` 14.5px · `.dc-step`(驱动链) 15px · `.drv-note`(逻辑作用点) 14px · `.cal-why`(口径选择理由) 14px · `#evpop blockquote`(RAG 原句·浮层) 14.5px · `.sm-step-hd b`(步骤标题) 15px · `.se-line`(段末小结) 14px · `.nm-era td.small`(叙事作用机制) 13.5px；只有「勾稽=Q×P×factor」这类机械说明降到 `.sm-mini` 12.5px。改模板时**不要把这些调回 12px**（原病症：分部 Driver 12.5px，用户反馈看不清且逻辑没说透）。
- 数字/等宽：`.mono/.num{font-variant-numeric:tabular-nums}`（本模板等宽走 serif 栈的 tnum，不引 mono 字体）。所有数值单元格、滑块读数、numbox 用 tnum。
- Chart.js 字体在 `chartDefaults()` 设为 `system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif`，`size 11.5`。

### 2.3 左侧固定目录 + scrollspy
- `#toc{position:fixed;left:0;width:272px;height:100vh;overflow-y:auto}`，`main{margin-left:272px;max-width:1560px}`（★2026-08-12 正文加宽 1120→1560；以模板实际值 **272px** 为准）。
- 两级：`a.l1`（章）/ `a.l2`（节，`padding-left:22px`）。顶部 `.brand` = `{{NAME}}` + `{{TICKER}}·{{MARKET}}`。
- **scrollspy**：`setupScrollspy()` 用 `IntersectionObserver({rootMargin:'0px 0px -78% 0px'})`，命中章节给对应 `#toc a` 加 `.active`（accent 色）。
- 响应式：`@media (max-width:1120px)` 隐藏 `#toc` + `#themeBtn`，main 居中。

### 2.4 h2 签名头 + 面板/卡片
- `h1`：23px/800，`border-bottom:2px solid var(--line)`。
- `h2`：18px/700，**`border-left:4px solid var(--accent); padding-left:10px`**（招牌节头）。
- 组件类：`.panel`（面板）、`.stat-row/.stat`（KPI 磁贴，`.v` 22px/750，`.pos/.neg` 染色）、`.callout`（左边条，`.warn`→`--s3` / `.risk`→`--s6`）、`.chart-block`（图卡：`.c-title` + `.c-sub` + `.chart-wrap`，**canvas 高度由 `.chart-wrap` 内联 `style="height:NNNpx"` 锁定**，配 `maintainAspectRatio:false`）。

### 2.5 `[n]` 顺序角标 + 弹窗（REFS）
- markup 由 `cite(n)` 生成：`<sup class="cite" data-n="N"><a>[N]</a></sup>`（`n` 可传数组→多角标相邻堆叠）。
- 点击角标 → `setupPopover()` 弹 `#pop` 卡（内容来自 `REFS[n]` 字典，`renderRefs()` 从 `D.references` 填充）；卡内「↧ 跳到参考文献」→ smooth scroll 到 `#ref-N` 并给 `<li>` 加 `.flash`（`--hl` 暖闪 2.2s）；ESC / 点外部关闭。
- 参考文献：`<ol id="refs">`，每条 `<li><span class="ref-num" id="ref-N">[N]</span> 文本 <span class="dtag FACT|EST|DNA">…</span></li>`。数据原子标：`FACT`(≥2 源可验) / `EST`(测算或卖方) / `DNA`(判断)，`.dtag` 描边染色（FACT→good / EST→s3 / DNA→bad）。
- `#ref-intro` 固定交互说明串（renderRefs 里写死）。

---

## 2.9 ★2026-08-12 增量组件速查（改模板时别撞名）
- **1.2 `#factions-preipo`**（`renderPreIPO`）：融资轮次 chips 时间线（`.preipo-rd`）+ archetype 徽章（`.preipo-arch`，四型色见 app.js `PREIPO_ARCH`）+ PE 退出进度条（`.preipo-meter`）。
- **2.1 催化标记**：scatter 透明只当命中区，●▲★ 由 `catlab` 插件手绘（`drawCatMk`；Chart.js 无五角星 pointStyle 所以手绘）；浮窗 `#catpop` 悬停开（`CATPOP` 状态机：hover/pin/over+260ms 延时），`.cp-links` 超链接行、`.cp-detail` 9 维默认展开。
- **2.1b `#fwdpe-block`**（`renderFwdPE`）：与 K 线同 labels 的 category 轴保证左右对齐；FY1 实线/FY2 虚线+`fill:'-1'` 带、中位参考线、◆锚点 scatter；数据不齐 `display:none` 整块藏。
- **2.2 `.fq`**（阶段列内 R/M/V 分解条）：`.fq-track` 中线=0、左右伸条，宽度按全阶段共用 `fqMax` 归一——**别改成各列自适应，同尺度是它存在的意义**。
- **2.3 `.cat-fold`**：`<details>` 原生折叠，默认收起。
- **3.1 `#tbl-pl`**：`.rowno` 序号列 + `.pl-sechd` 分块行（费用桥/利润链 header 行 colspan）。
- **3.3.x**：总节 h2 `#sec-segs` + 每分部 `h3.seg-h3`；TOC 三级 `#toc a.l3`；段内 `.seg-edit`（✎ 改本段假设，core 默认 open）滑块与 3.4 同 data-path，靠 `bindRangeInputs`（document 级委托）镜像同步——**新增任何滑块只要带 `data-path` 就自动接入，别再各自 addEventListener**。
- **3.5 加权估值**：`#val-tier-strip` 五档等级带（`TIER_INFO`）+ 卡片 `.tier-badge`；卡序=`tierOf()` 第一档→第五档，data-vout/data-w/data-vd 仍用原始 paradigms 下标（light 刷新不受排序影响）。

## 3. Chart.js cookbook（app.js 已实现的约定，文档化）

### 3.0 全局 defaults（`chartDefaults()`，任何 `new Chart` 前调一次）
```js
Chart.defaults.color = PAL().muted;   Chart.defaults.borderColor = PAL().grid;
Chart.defaults.font.family = 'system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif';
Chart.defaults.font.size = 11.5;      Chart.defaults.animation = false;   // 静态报告，禁动画
```
共享工厂：
- `TT()` = 白卡（主题感知）tooltip：`{backgroundColor:p.bg,borderColor:p.grid,borderWidth:1,titleColor:p.fg,bodyColor:p.fg,displayColors:false,padding:10}`。多序列叠加时 `Object.assign(TT(),{displayColors:true,...})`。
- `legPts()` = 点样式图例 `usePointStyle,boxWidth:9,boxHeight:9`（柱/散点）；`legLine()` = 线样式图例 `pointStyle:'line',boxWidth:18,boxHeight:2`（多折线）。
- `mkChart(id,cfg)` = 销毁旧实例（`CH[id].destroy()`）再建，注册进 `CH`。**改图必经此，勿直接 new。**
- 系列取色一律 `PAL().s[i%8]`；正负用 `p.good/p.bad`。缺数据不画图，写 `<span class="datagap">⚠️ 未查到 …</span>`（不编造）。

### 3.0b ★读数纪律（2026-08-16 赛力斯 v3.2 七条读者反馈固化）——**查的是「读者会读成什么」，不是「这个数算对没有」**

七条反馈里有五条不是算错了，是**数字对但读者读错了**，而且五条同一个病根：
前三章所有的闸都在查数值正确性，**没有一条在查读数歧义**。四条硬规矩，`node scripts/check_charts.js --model <page_model>` 是它的机器闸（CK-8）：

**① 一个字段只能有一种读法。** 有多种可能读法的字段（小数还是百分数 / 总市值还是自由流通 / 倍盈利还是倍收入），要么在契约里钉死，要么在页面上把口径写在读者眼睛必经之处——两者都不做就是等着被读错。
- 病例：`part2.phases[].chg` 契约是展示串 `"+244.8%"`，赛力斯 build 落成裸小数 `-0.4776`。页面直接印出来，读者分不清 47.76% 还是 0.48%；同时 `rmvBar(hp.factor_quant, num(hp.chg))` 拿它当**百分点**去和 rmv 的 `_pp` 比，量纲错 100 倍。
- 治法：渲染层 `chgTxt()`（展示串）/ `chgPct()`（百分数，给算术）**两个出口分开**——「印出来的串」和「参与算术的数」量纲不同，混用就是下一次 100 倍。兜底是止血，契约仍要求给串（CK-8 a）。

**② 有多口径的数字列必须有表头，且表头写死口径与单位。**
- 病例：1.7 个股表那一列是问财「自由流通市值」，比亚迪 2,184 亿，**整张表没有 `<thead>`**。读者按裸数字当「市值」读，而比亚迪总市值 7,642 亿——看上去就是拉错了 3.5 倍。实测数据一次没错（问财返回 218,385,102,814.9 元，分毫不差）。工业富联 13,135 亿 / 2,129 亿差 6.2 倍、长城汽车 1,135 / 170 差 6.7 倍，这种表少一行表头就是在制造错误结论。
- 治法：`<thead>` 写「自由流通市值｜亿元 · 容量口径」＋「总市值｜亿元」**两列并排**，让两个口径互相解释（CK-8 c）。

**③ 量纲不同不许共用一根轴，轴标题必须带量纲而不是带单位。**
- 病例：2.1b 里 Forward PE 与 Forward PS 同挂右轴 `y`，轴标题写「倍数」。「倍」只是读音相同：一个除盈利、一个除收入。赛力斯 PE 中位 25x、PS 中位 1.27x，差 19 倍，同轴一画 PS 被压成贴着 0 的直线——读者拿到的是「PS 常年不动」这个**假读数**。
- 治法：`y`＝「Forward PE（倍·盈利）」、`yS`＝「Forward PS（倍·收入）」两根右轴；一屏最多三根 y 轴，超了就把腿拆到分模式里（「价格+两把尺子」只留价格/PE/PS，亿元量级的收入·归母预期单独看）。图注逐轴点名谁读哪根（CK-8 e）。

**④ 图形分型 > 文字解释：结果量走柱，分解项/过程量走线。** 文字治不了图形误认——读者按**最像的图形**去认，不按图注去认。
- 1.3 杜邦：ROE 走柱（被解释的那个数），净利率/周转率/权益乘数走线（把它拆开的三个因子）。
- 1.4 成本：毛利率、净利率走并排双柱（结果），四条费用率走线（过程）；**同为「占营业总收入 %」就必须共用一根左轴**，两根柱之间的落差直接读成四费+税金吃掉的那一段。
- 1.5 一致预期：画的是**全距误差线**不是箱线图，图上不会有箱体。光在折叠块里写「这不是箱线图」不管用（赛力斯那版写了，读者照样反馈「箱线图是错的，没有箱体」）——**图例要画成图形本身**：`.cons-legend` 里那七个 `<svg>` 样标长什么样，图上就是什么样，其中「全距」那枚直接画成工字并标注「无箱体」。

### 3.0c ★版式纪律：一个容器只服务一种阅读（2026-08-16 读者反馈「排版过于长，宽度不够」固化）

2.2 阶段面板的实测病灶：6 段并排 → 每列被压到 **150–195px 宽却 2,741px 高**（长宽比 1:15），
光「估值算账」一节就是 805 字在 180px 里折成 976px。**这不是字太多，是把两种阅读塞进了同一个容器**：

| 阅读方式 | 要什么 | 放哪 |
|---|---|---|
| 对齐 K 线**横向扫读** | **窄而齐**——一眼看完一段、跨列比长短 | 上层「对齐条带」（`.ph-cols`，按 span 比例对齐 K 线，列＝可点 tab） |
| 读懂一段的**算账** | **宽而连贯**——算式、双口径两栏、Step A/B/C 都要横向空间 | 下层「详情区」（`#phase-detail`，**整页宽**，只渲选中段） |

**宽度是零和的，一个容器同时满足不了两种阅读。** 判据很简单：
**如果一个块的高度是宽度的 5 倍以上，它就放错容器了。**

拆完实测：条带列 **2,741px → 357px**（7.7×），整节 2,750px → **1,018px**，
详情区拿到 1,064px 宽、双栏各 509px，双口径子栏各 244px。

- 「禁止纵向堆卡」那条老规矩管的是**①对齐扫读那一层**，不是②——②本来就该是全宽正文，不冲突。
- 条带里只放扫读得动的：名/涨跌/期间/主要矛盾（`-webkit-line-clamp:3` + `title` 存全文）/
  R/M/V 条/**双口径数字摘要**（只给 Δ 与主因徽章）。`factor_quant.basis`（60–150 字的口径说明）
  必须搬进详情区——`fqHTML(ph, compact)` 的 `compact` 就是干这个的。
- **打印必须补回被折叠的内容**：详情区只渲选中段，其余段在 `<details class="phd-all">` 里。
  纯 CSS 撬不开 `<details>`（未展开时内容被浏览器内部隐藏），所以 `setupPrintExpand()` 在
  `beforeprint` / `matchMedia('print')` 里加 `open` 属性，`afterprint` 还原，屏幕上的选中态不受影响。

### 3.0d ★字段分两类：可信 HTML vs 走 esc()（CK-8 i）

- **可信 HTML（原样注入）**：`valuations[].body`、`valuations[].consensus` —— 可以写 `<br>/<b>/<sup class=cite>`。
- **走 `esc()`（防注入）**：`phases[].logic`/`core_conflict`/`narrative`/`factor_signature`、
  `factor_quant.basis`、`feedback.*.answer` —— **往这些字段写 `<b>` 会原样印出尖括号**。
  要加粗用 `**…**`，页面有 ** → `<b>` 的兜底渲染器（§ app.js 顶部）。
  赛力斯从 v3.2 起就在漏，一直到改版式才暴露——因为窄列里折行太多，没人逐字读。机器闸 CK-8 i。

### 3.0e ★观感纪律：一屏、对比度、可折叠（2026-08-17 石英股份 v3.2 八条读者反馈固化）

石英 v3.2 八条读者反馈里五条不是数据问题，是**观感**：图太大、字看不见、模块收不起来、权重看着不归一、赔率格空着。
病根同上一轮：闸都在查数值，没有一条在查「读者的眼睛落到页面上会怎样」。补四条通则：

| 通则 | 判据 | 落地 |
|---|---|---|
| **① 全景图不许比一屏高** | 单张图渲染高度 ≤ 60vh；一张图承载 >8 个对象时**条形/表格优先，气泡/散点折叠** | 4.1.1 默认视图＝三坐标条 `cmapStrip`（一行一条矛盾，F/D/赔率三根同尺度条），气泡 SVG 进 `<details class="cmap-fold">` 且 `.cmap{max-width:760px}`；子坐标系同款 |
| **② 表头默认值必须是安全的（不是逐表补前景色）** | 全局 `thead th` ＝ **浅底 `--elev` + 深字 `--fg` + accent 下框线**。要深底白字的表，必须在**同一条规则里**同时写 `background` 与 `color:#fff` | 见下方「② 的病史」 |
| **③ 次级复合图一律可折叠** | 非主图（2.1b 前瞻估值复合图、1.5/1.6/1.7 的方法块）用 `<details>`；默认开或关按信息密度定，**折叠里有 Chart.js 时挂 `toggle→resize`**（file:// 下 ResizeObserver 偶尔不触发） | 2.1b `#fwdpe-block` 改 `<details open>`，`bindFwdFold()` 兜底重绘；按钮不放进 `<summary>`（点按钮会触发折叠） |
| **④ 派生量的显示口径要与算法一致** | 加权算法里归一了的量，页面就印归一后的值；一根滑块动、所有相关读数同步刷 | 估值卡印**有效权重**（`wnorm`，Σ=100%）+ 括号给滑块原始值，light 刷新遍历全部卡片；hero 区加「权重已归一」一句（读者「彼此的权重需要有影响啊，加权的权重=1」） |
| **⑤ 空值不许渲成 0** | 契约要求的数字缺失时渲红字「未算」并点名闸门，不许 `num(null)=0` 静默印成 `0%` | 4.2.1 覆盖表 / 4.1.2 明细表的赔率格：`odds==null` → 「未算（CK-6 c 不过）」；`check_part4.js` 加 odds 数字闸 |
| **⑦ 堆积面积图的 fill 必须指向上一层** | Chart.js 里 `fill:true` ＝ 填到**零轴**，每层各自铺到 0，N 层全叠在一起糊成一片（半透明更助长这个误认）——那不是堆积图，是 N 张独立面积图摞着。正解：第一层 `fill:'origin'`、其余 `fill:'-1'`，背景色**不透明** | 1.4 毛利率分解（2026-08-18 用户：「堆积堆积，不是叠在一起的吗」）；`y:{stacked:true}` 只管**数值**堆叠，管不了填充目标，两件事要分开设 |
| **⑥ 单位写在表头上，不写在图注里** | 有金额列的表，**表头本身**要带单位串（`.th-unit`）；行名里的量/价单位另计。cap／图注里的单位不算数 | 3.1 分组行写「金额　单位 亿元　·　比率行＝%」、项目列头写「金额单位 亿元」、h2 后缀 `#pl-unit`；币种取 `meta.currency` 走 `MONEYU()` |

**② 的病史（为什么这条从「补前景色」改成「改默认值」）**：
旧默认是 `thead th{background:var(--accent); color:#fff}`。3.1 的年份表头带 `.col-hist/.col-fcst` 浅底、
项目列带 `.rowlbl` panel 底、分组行 `.pl-grp` 无类——**底色被覆盖、白字留着＝看不见**。
2026-08-17 那一轮按「覆盖底色的规则必须同时指定前景色」补了 `#tbl-pl thead th{color:var(--fg)}`，
**这是补丁不是修复**：它只保住了当时那一张表，下一张新表照样复发，同一条读者反馈因此重复了四次
（「表头字体改成黑色，我已经说过很多很多次了」）。2026-08-18 改的是**默认值本身**——
浅底深字之后，覆盖底色**不可能**再产生不可读表头，新表不必记得补任何东西。
纪律因此反转：**深底白字才是特例，要显式申报**（同一条规则里 `background` 与 `color:#fff` 成对出现）。

### 3.1 营收堆积柱 + YoY 双轴 + 事件 pin（`renderRevenue`）
- 分部：N 个 `type:'bar', stack:'rev', backgroundColor:p.s[i%8], yAxisID:'y'`；YoY：`type:'line', borderColor:p.bad, yAxisID:'y1', pointRadius:0`。
- 左轴 `y` stacked（`callback:v=>v+'亿'`），右轴 `y1`（`drawOnChartArea:false`, `v=>v+'%'`），x `stacked`。
- **事件 pin**（自定义插件 `revpins`，`afterDatasetsDraw`）：在 `events[].year` 对应柱顶画 accent 实心圆 + 白色序号，下引 accent 虚线到轴底。序号列表写进 `#rev-sub`。

### 3.2 ROE 杜邦**柱+线**复合双轴（`renderDupont`）★2026-08-16 由全折线改为复合
- **ROE 走柱**（`type:'bar'`，左轴 `y`(%)，`order:9` 压在线下面，负值自动换 `p.bad`，柱顶挂 `barLabels`）——它是被解释的那个数；
  净利率(s2 线，左轴 `y`)、总资产周转率(s3 线, `borderDash:[5,4]`)、权益乘数(s5 线, `[2,3]`) 走右轴 `y1`(`v=>v+'×'`)——它们是把 ROE 拆开的三个因子。**结构不同的序列用虚线区分**。
- 顶层必须给 `type:'bar'`（同 3.4 的坑）；轴标题写「ROE(柱) / 净利率(线)　%」，把图形分型写进轴标题本身。
- `legLine()` + `displayColors:true` tooltip，label 按序列名格式化（比率 `pct`，倍数 `v+'×'`）。

### 3.3 毛/净利率**双柱** + 费率线（`renderCost`，`costMode==='rate'`）——★2026-08-16 单轴复合，右轴取消
- **毛利率、净利率走并排双柱**（各 `barPercentage:0.42, categoryPercentage:0.82`，负值换 `p.bad`）——它们是结果；四条费用率（销售 s2/管理 s3/研发 s5/财务 s8 虚线）走线——它们是过程。
- **全部共用左轴 `y`**：两者量纲同为「占营业总收入 %」，同量纲分两把尺子读起来要来回换算（旧版把毛利率推到右轴、净利率留左轴，就是这个毛病）。两根柱之间的落差 = 四费+税金+其他非经常项吃掉的那一段，caption 里点破。
- 旧版的顾虑「毛利率 20–60% 会压扁 0–10% 的费率线」在改柱之后不成立：柱和线是不同图形，视觉上不再抢同一条读数通道。若某标的费率极低（<2%）导致线贴底，用 `barPercentage` 收窄柱、不要退回双轴。
- 顶层必须给 `type:'bar'`。`y` 非 stacked。

### 3.4 利润瀑布（`renderCost`，`costMode==='fall'`，float bar）
- **chart 配置必须给顶层 `type:'bar'`**——费率模式每个 dataset 自带 type:'line'，瀑布模式的浮动条 dataset 没有 type，漏了顶层 type Chart.js 直接抛错渲空（2026-07-21 用户报『瀑布图没做出来』的根因，已修）。`barLabels` 对 `[from,to]` 数组值显示差额。
- 单 dataset，每点 = `[from,to]` 浮动条；`steps` = 营收→营业成本→毛利→销售/管理/研发/财务→营业利润(近似)。
- 着色：起点 `tot`→s1，小计 `sub`→s4，扣减 `neg`→bad，增项→good。`run` 累加驱动 `[from,to]`。
- **绝对额缺失时用费率反推**（`op_cost = rev*(1-gm)`，各费用 `= rev*rate`）。值标签走 `barLabels` 插件（`opts.on` 开关，`di` 指定 dataset）。
- 分部/费率 ⇄ 瀑布 由 `.seg-btn`（`#btn-cost-rate` / `#btn-cost-fall`）切 `costMode` 重渲。

### 3.5 K线蜡烛 + MA + 催化 scatter + 阶段 band（`renderPrice`）—— 股价复盘旗舰图
- **K 线**：自定义插件 `candles`（`beforeDatasetsDraw` 画影线+实体，涨红 `#e34948`/跌绿 `#1a9e75`）——**没有价格折线 dataset**；datasets = MA5/10/20/60 四条线（`MA_LIST`/`MA_COL`，由 closes `movAvg` 自算）+ 催化 scatter。
- **催化散点**：`type:'scatter'`，dataset 下标 = `CAT_DI = maDs.length`（**由 MA 数量推得，严禁硬编码 4**——`catlab` 插件与 tooltip 都用 CAT_DI）。逐点 `backgroundColor = CODE_COLOR[c.code]`（R/M/V 复合码着色），`data:[{x:snapIdx,y:price,_c:catalyst}]`。
  - `CODE_COLOR = {R,M,V,RM,RV,MV,RMV}`；`CAT_COLOR/CAT_LABEL = G1–G5 五大催化剂`（badge 底/字；旧 D/E/S/O/L 已废弃）。
- **snapToWeek**：`snapIdx(dates,d)` = 取 ≤ 该日期的最近周索引（否则散点堆右侧）；page_model 若已给 `c.snapIdx` 直接用。
- **`#号 label`**：插件 `catlab`（`afterDatasetsDraw`）在散点上方画 `#id`（着复合码色）。
- **阶段 band**：插件 `phbands`（`beforeDraw`）按 `phases[].startIdx/endIdx` 画交替灰底 + `hexA(ph.color,'10')` 半透明带（**必须走 hexA**，硬拼 `color+'12'` 遇 3 位 hex 会变黑块，见 §3.6b）+ 顶部居中阶段名/涨幅。
- **对数轴**：`useLog = (高低价 max/min)>1.8` 时 `y.type='logarithmic'`，ticks 只显白名单档位（`[10,15,20,…600]`）。y 轴 `position:'right'`，x 轴 `type:'category'`（催化用 snapIdx 落 category 索引，切 time scale 会破 band/label 数学）。
- **tooltip**：`filter` 剔除 scatter 行（index 模式下 scatter 按元素序号会错配到别的周）；title 两行 = `#id name · date` + `开高低收`；body = 各 MA 值。催化详情走 **▲ 点击 `openCatPop` 弹卡**（G 徽章+driver+二阶 9 维）。图例走 `#price-legend`（K线涨跌 + MA + G1–G5 + 复合码）。

### 3.5b Part3 章节结构（动态编号）：3.1 利润表(STP) → **3.2 叙事↔分部映射(有 narrative_map 则渲)** → 分部模型 ×N → 假设 → 估值
- `NBASE()` = narrative_map 有内容时 3、否则 2；分部=3.(si+NBASE)，假设=3.(N+NBASE)，估值=3.(N+NBASE+1)。
- `renderNarrativeMap()`（`#nmap-sec`）：每个 era 一块面板（era 标签[当前叙事高亮]+名称+status），impacts 表 = 作用分部/参数/时点/强度(●●●)/作用机制；`nm.note` 渲 callout（点破公司口径 vs 叙事 gap）。
- `renderSegmentModels()`（boot/rebuild 时建 DOM）：向 `#seg-models` 注入每分部一节 `h2#sec-seg-<i>`（带 `drvBadge`）+ `.seg-model` 面板（core 段 `.seg-core` 描边），面板内部＝**编号动线**（`04 §1.17e`）：`.readpath` 顺序条 → `.sm-step#seg<i>-s<k>`×N（每步 `.sm-step-n` 圆号 + 标题 + `.sm-step-hint` 一句话说明这步在干什么）→ `.seg-end` 段末小结（活数字 `data-segsum-rev|yoy|val` 由 renderSegTables 刷新 + `.se-next` 指向下一段）。步骤顺序固定：1 建模方法 → 2 `.drv-chain` → 3 `.cal-box` → 4 `#segtbl-<i>` → 5 `#chart-segqp-<i>` → 6 `.sm-val` 分部估值；缺 2/3 自动跳过并重排编号。**两栏 `.sm-grid` 已废弃**（估值改为末步全宽）。core 段缺 driver_chain/evidence 渲红 `.datagap`。
- **口径取舍决策卡**（`calHTML`+`calScaleHTML`）：`.cal-box` = `.cal-hd`(subject+N种口径+spread) → `.cal-scale`(`.cs-labs`标签层 / `.cs-track`轨 / `.cs-dot`点·`.cs-band`区间带 / `.cs-foot`两端值+红字「跨口径差 N×」；>10 倍加 `.logmode` 条纹) 或 `.cal-agree`(差<1.5 倍时的互证一行) → `.cal-pick`(结论卡：采用/为什么/用错的代价) → `.cal-alts`(候选 `.cal-alt.chosen|ref|rejected` 卡片列表)。**已无 `<table>`**——宽表格是第三轮反馈的痛点。
- 章级动线 `#p3-path`（`renumberPart3()` 渲）：「本章怎么读 1 3.1 利润表 → … → 加权估值 = 终点」+ 一行读法提示。
- **原句浮层** `#evmask`+`#evpop`（`setupEvidence()` 文档级委托，只绑一次）：`.ev-chip` / 正文 `sup.evc[data-ev="<si>::<Ex>"]` 点击 → `openEvPop(key)` 渲浮层（sticky 头 + 「逐字原文」blockquote + 「我的推论（非原文）」+ sticky 底：复制取原文命令/原件路径 + `‹ n/N ›` 段内翻页）；Esc/点遮罩/✕ 关，←/→ 翻页。**正文不再 inline 展开原句**（版面被原文撑长是第二轮反馈的痛点）。未登记 id 渲 `sup.evc.miss`（红色虚下划线）+ toast 提示。`button[data-cp]` 复制走 `copyText`（clipboard API，file:// 回退 execCommand），toast 文案按 `data-cpwhat` 区分。
- `renderSegTables(pl)`（recompute 每次调用，表随滑块联动）：年为列，行=量/量YoY/价/价YoY/收入/收入YoY/毛利率；`driver_focus.targets` 命中格加 `.drv-hit`（黄底+accent描边）；表下 `.drv-note` 列出「逻辑作用点：参数@时点——机制」。
- `renumberPart3()`：改写 `#sec-assume`/`#sec-val` 标题编号，TOC 插 `a[data-nmap]` + 每分部 `a[data-seg]`（core 段带★）。
- 3.1 利润表 `renderPL` 加细：每分部 收入 + 量/价子行（仅真量价段，行名带 `model.q_unit/p_unit`）+ 分部毛利率子行；桥行 −销售及管理费用(承载=sga_rate口径)、−研发、＋D&A(资产折旧注记)、±营业外·−净利息(预测列)、−税(历史列 plug)、−少数股东损益(预测列) 按非零条件渲出；表底带**拆分穷尽性运行时警示**（历史年 Σ分部 vs 财报差>0.5% 亮红）。
- leader 估值卡：`pd.key==='leader'` 时卡顶渲 `.leader-line`（对标大哥点名+口径；缺 `leader_name` 红 ⚠️ `.missing`）。

### 3.6 Part3 分部堆积 + 毛净利率线 + 估值横条（`renderPLCharts` / `renderValuation`）
- `chart-plrev`：分部收入堆积柱（`p.s[i%8]`, `stack:'r'`），数据 = 引擎 recompute 后的 `pl.seg[].rev`。
- `chart-plmargin`：毛利率(s1)/净利率(bad 虚线) 双线。
- `chart-valbars`：各范式隐含市值**横条**（`indexAxis:'y'`），`mcap>=cur?good:s1` 着色；**当前市值虚线**由插件 `curline`（`afterDraw`）画 bad 竖虚线 + 「当前 NNN亿」标注。label = `范式名 (权重%)`。

### 3.6b K线 OHLC 闸门 + hexA（`renderPrice` 内，务必保留）
- **OHLC 完整度闸门**：≥10% 蜡烛缺真实 o/h/l（或 h==l）→ `#price-sub` 前插红 `datagap` 警示「必须用 scripts/fetch_kline.py 重拉」。c 回退兜底仅防崩，不是合格交付（CK-2 拦）。
- **hexA(color,alpha)**：hex+alpha 后缀安全拼接——3 位 hex（`#888`）先展开 6 位再拼，否则 `'#888'+'10'` 是非法 canvas fillStyle，阶段带会画成不透明黑块（实测踩过）。阶段带 `phbands` 已走 hexA；新插件拼 alpha 一律用它。

### 3.6c 分部量价锚图（`renderSegQPCharts`，3.2+ 每分部一张 `chart-segqp-<i>`）
- 柱=量增速(s1)/价增速(s4)：**历史列实色（由 hist.q/p 逐年 YoY 算出），预测列同色+'66' 半透明（= assume.q_growth/p_growth）**；量价未拆段只出「收入增速(量价未拆)」单柱系。
- 虚线=类比锚：`model.q_anchors/p_anchors`（≤4 条，s3/s5/s6/s7 轮色，`[6,4]` 虚线），label=「锚·量·行业CAGR +30%」。y 轴 %。
- 假设滑块联动：`recompute()` 内调 `renderSegQPCharts(pl)`，拖滑块预测柱即时动。

### 3.7 后台标签 0 宽补丁（务必保留）
非激活标签页里 Chart 会渲染 0px 宽。`fixZero()`：轮询 `Chart.instances` 中 `!c.width` 的实例 `c.resize()`，`tries<30` 每 400ms 重试，`boot()` 里 `setTimeout(fixZero,150)`。

### 3.8 主题切换重建（Chart 缓存色，必须重建）
`setupTheme()`：按钮翻 `data-theme` → `setTimeout(rebuildAllCharts,30)`。`rebuildAllCharts()` 重跑 `chartDefaults()` + 所有 render*。**新增图必须挂进 `rebuildAllCharts`**，否则切主题后该图仍是旧色。

---

## 4. 交互（活链：改假设 → 重算 → 表/图/估值联动）

### 4.1 假设滑块（`renderAssumptions`）——★带类比锚
- `knobRange(path,label,val,min,max,step,disp,anchors)` → `<input type=range data-path="segments.0.assume.q_growth.1">` + 读数 `span[data-kv]` + **滑轨 ▲ 锚刻度**（`.atick`，按 `(v-min)/(max-min)` 定位，title=锚名+值）。
- 锚来源：**历史3yCAGR 自动算**（`cagr(hist.q,3)`/`cagr(hist.p,3)`/毛利率历史均值）+ `segments[].model.q_anchors/p_anchors/gm_anchors` 外部锚（行业/大哥/卖方）。每段 knob-grid 上方渲 `.a-legend` 锚图例行（量锚/价锚/毛利率锚 各列 label+值）。
- `oninput` 链：`setPath(MODEL, path, +value)` → 更新读数 → **`recompute()`**（含 `renderSegQPCharts`，分部锚图预测柱同步动）。
- 假设单位：量增速/价增速用小数（`spct` 显示），毛利率/费率/税率用小数（`pct` 显示）。分部各预测年一组（量增速/价增速/毛利率），另加费用块（销售/研发费率、所得税率，预测期常数）。

### 4.2 recompute() 主循环
```js
function recompute(){ var pl = EONE.recomputePL(MODEL);
  renderPL(pl); renderPLCharts(pl); renderValuation(pl); }
```
- `EONE.recomputePL(part3)` → `pl{years,H,seg,byYear[{rev,gp,gm,ebit,ebitda,netProfit,netMargin,eps}],revYoY}`（`H`=历史列数，用于 `col-hist/col-fcst` 与 `c-actual/c-calc` 分色）。
- 利润表 `renderPL`：历史列 `.c-actual`(蓝)、预测列 `.c-calc`(黑)、负值 `.neg`；YoY/毛利率/净利率行 class `yoy`（小字灰）；分部收入 `subrow`，合计/归母 `totrow`。

### 4.3 权重滑块 + 参数 numbox（`renderValuation`）
- 权重：`input[data-wpath=ri]` → `v.paradigms[ri].weight = +value` → **`renderValuation(pl)`**（仅重渲估值，权重自动归一）。**★卡片印的是有效权重 `wnorm`（Σ=100%）**，括号里给滑块原始值；拖任一根，`light` 路径遍历全部卡片刷新 `[data-w]`（2026-08-17，§3.0e ④）。
- 参数：`input.numbox[data-pi][data-pp]`（白名单标量，`PARAM_LABEL` 映射；SOTP 分部倍数特判）→ `setPath(paradigm.params, pp, +value)` → **`recompute()`**（因 PE/PEG/EV-EBITDA 可 `link:true` 联动 Forward 净利，必须全链重算）。
- `EONE.runValuation(v,pl)` → `{rows,active,blend{mcap,target,odds},range{min,max,median,dispersion,verdict},currentMcap,shares}`。
  - `blend.odds = blend.mcap/current − 1`（**赔率 = 目标市值/当前市值 − 1**，全 skill 统一口径）。
  - `verdict` 离散度闸门：`<20%` ok(可点估计) / `20–50%` warn(看区间) / `>50%` risk(不出单值)。hero 卡 `#valuation-blend` 展示加权目标/目标价/赔率/当前锚 + 区间 callout。

### 4.4 调试钩子
`boot()` 末尾挂 `window.__EONE_APP__ = {recompute, renderCost, setCostMode, rebuildAllCharts, openCatPop, MODEL, CH, toast, copyText, renderFeedbackLog}`。控制台可 `__EONE_APP__.MODEL.segments[0].assume.gm=[0.3]; __EONE_APP__.recompute()` 手动验活链、或 `__EONE_APP__.CH['chart-price']` 拿实例。
标注层挂 `window.__EONE_FB__ = {items(), sync(), summaryMD(), exportJSON(), open(), restore()}` —— 验收标注功能就调它（`__EONE_FB__.items().length`、`__EONE_FB__.summaryMD()`）。

### 4.5 反馈标注层（`annot.js`，详见 `08-feedback-loop.md`）
- DOM：`#fb-fab`(右下浮钮+计数) `#fb-drawer`(右抽屉清单) `#fb-selbar`(划词类型条) `#fb-toast` `#fb-answers`(页顶「本版反馈回应」，`renderFeedbackLog()` 渲)。
- 锚点：任何带 `data-fbk="<page_model JSON 路径>"` 的元素都自动获得 ✎ pin + 成为标注归属；`MutationObserver`(main, 260ms debounce) 在 app.js 重渲后补 pin 与恢复 `mark.fb-hl` 高亮。**新增模块只需加 `data-fbk`，标注层零改动**。
- 状态：`localStorage['eone_fb::<report_id>']`；`feedback.endpoint` 存在时 POST `/api/ann` 同步；`feedback.resolved[].path` 命中的模块打 `.fb-fixed` 绿边。
- **不挡路三件套（务必保留）**：`#fb-drawer:not(.open){pointer-events:none}`；抽屉开时 `body.fbd` → `.fb-pin{right:auto;left:2px}`（避免右侧 392px 压住所有 ✎）；文档级 click 里「点正文任意处收抽屉且不 preventDefault」。原文浮层遮罩 `#evmask{pointer-events:none}`（纯视觉，关闭走 click-outside）——**新增任何浮层都照此办**，否则用户读到的是「点不开后续模块」。
- 版本徽章：`meta.version/updated` 渲成 `#sec-kpi` 上的 `.ver-chip`（认知螺旋第几轮）。

---

## 5. 交付 / 验收

### 5.1 生成 + 本地自查
```
python scripts/build_page.py --model _workspace/<ticker>/page_model.json --out _workspace/<ticker>/onepager.html
```
产物**自包含单文件**，本地双击 `onepager.html` 即在浏览器活渲染（Chart.js/引擎/数据全内联，离线可开）。

**扰动验收（CK-3 活链证明）**：打开后拖任一假设滑块 → 利润表数字 + 分部图 + 估值 hero 头条必须同时变化；拖权重滑块 → 加权目标市值/赔率变。不动 = 链断，查 `data-path` 与 `setPath`。

### 5.2 ⚠️ 本环境 preview 限制
本环境 preview 对**项目文件夹外**的文件只出**静态快照（不执行 JS）**——即图表/交互全不渲染，只见空壳。要活渲染三选一：
1. 把 `onepager.html` 放进项目目录内再 preview（**改了模板/annot.js 重建后加 `?v=<新串>` 破 file:// 缓存**，否则跑的还是旧 JS——2026-07-25 实测踩过）；或
2. **反馈平台上线**（推荐，能收标注）：`python scripts/deploy_page.py --ticker <代码> --model <page_model> [--endpoint <worker URL>]` → Cloudflare Worker 托管 `https://…workers.dev/<代码>/`，见 `08-feedback-loop.md`；或
3. **用 Artifact 发布**（只读分享，不收标注）：页面自包含、无外部请求（Chart.js 内联、无 CDN/web font/远程图），CSP 友好，发布后得可分享 URL 且 JS 正常执行。发布前把参考文献里的本地 `C:\…` 路径与 `[Fxxxx]` 底稿 id 视需要脱敏（内部 RAG traceability，非公网链接）。
