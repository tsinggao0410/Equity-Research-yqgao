---
name: equity-onepager-interactive
description: "公司认知一页纸·图表交互版:给定A股/港美股标的,产出单文件自包含HTML——①基本面图谱(营收拆分/股东派系+上市前融资史/股权树/ROE杜邦/成本费率/券商预期区间vs实际披露/筹码龄结构/可交易容量:容量×换手强度分位×我的份额三量齐读) ②股价复盘(真实OHLC K线+催化悬停浮窗+Forward PE带+阶段R/M/V分解+形态判定+叙事篮子与申万行业同期对照给M实测锚;概念篮子按诞生日硬闸,不许用事后定义的成分回测早期阶段) ③P&L量×价建模(分部量价拆分+驱动链算账+口径对账+RAG原句证据;估值锚年须反算隐含份额与TAM对表)+可调假设滑块+多范式加权估值(五档:对标大哥/PE/PEG/SOTP/PB-ROE/EV-EBITDA/终局份额) ④矛盾地图(Scenario预测:哪几个Case涨跌×怎么解锁×赔率×概率→期望值EV与现价隐含上行概率;Case=主动矛盾×从动矛盾叉乘、knobs实跑引擎;双槽位核心矛盾+三坐标+叙事链) ⑤开篇总结(公司类型走k/v结构化+核心逻辑+算账+利润兑现期限·估值范式上界·潜在催化)+反馈闭环。iFind+FMP+qcc+韭研+问财+akshare申万+AlphaPai备源。触发:公司认知一页纸、快速了解这家公司、把XX做成一页纸、XX值不值得研究、基本面图谱、营收拆分、杜邦分解、股价复盘、P&L建模、分部模型、驱动链、口径对账、隐含份额、加权估值、五档估值、一致预期、beat、miss、筹码龄、可交易容量、叙事容量、换手强度、韭研、问财、产业链篮子、篮子超额、行业对照、Forward PE、RMV分解、矛盾地图、核心矛盾、主动矛盾、从动矛盾、赔率坐标、分歧度、可证伪性、叙事拆解、Scenario预测、涨跌Case、场景赔率、期望值、隐含概率、利润兑现期限、估值范式上界、潜在催化、报告反馈、v2/v3版本。即使用户只说「帮我看看XX公司/给我做张XX的图」也应触发。"
---

# equity-onepager-interactive — 公司+行业认知一页纸（图表为主·可交互）

给定一家公司，**以最快速度建立认知**：产出一张**图表为主、文字为辅、单文件自包含、可交互**的 HTML 一页纸。核心信条：人对图表的认知效率远高于纯文字 —— **每个 section 以图/表/可视件起手，正文只做 caption + callout + [n]角标**；框架黑话（R/M/V、archetype、STP、Forward…）不进正文，翻成买方白话。

产物四大部分：① 基本面图谱（4 图）② 近三年股价复盘（阶段+算账+催化）③ P&L 建模 + 多范式加权估值（可调假设、可调权重、即时联动）④ **矛盾地图**（赔率×分歧×可证伪坐标 + 叙事链拆解 + 双槽位核心矛盾）——前三章给「是什么」，第四章给「下一步盯什么、押哪一条」。

> ⚠️ 不要一次性加载所有 references。SKILL.md 是常驻路由；references/ 按 Phase 进入时才读；下方标 `⚡强制` 的在进入对应模块前必读。

---

## 目录结构（三层资源，按需加载）
```
equity-onepager-interactive/
├── SKILL.md                       ← 本文件：路由 + Phase0.0→9 流程 + CK 闸门 + 数据路由 + page_model 契约
├── references/
│   ├── 01-data-recipes.md         ← ⚡强制(Phase1) 每数据集精确取数命令 + A/港/美路由 + 解析陷阱
│   ├── 02-part1-fundamentals.md   ← Phase1-2 4 张图的数据形状/分部标签跨年归一/杜邦恒等式/费率瀑布/股东子公司
│   ├── 03-part2-price-review.md   ← ⚡强制(Phase3) 阶段划分+Forward算账PE三档+G1-G5五大催化剂→9维→R/M/V+K线图契约
│   ├── 04-part3-pl-model.md       ← ⚡强制(Phase4) archetype→收入STP、通用利润桥、**Driver三件套(§1.17)**、recompute() 引擎规格
│   ├── 05-valuation-paradigms.md  ← Phase5 8 范式公式 + 加权融合 + 分歧区间规则
│   ├── 06-html-design-system.md   ← Phase6 页面契约、Chart.js cookbook、色板、字号纪律、角标/目录
│   ├── 07-rag-corpus.md           ← ⚡强制(Phase0.0) 前置资料询问 + 建/查 RAG 语料库 + **取证当场落 evidence(§4b)**
│   ├── 08-feedback-loop.md        ← ⚡强制(Phase8-9) 上线反馈平台 + 标注回收 + 五类型→修复动作 + 认知螺旋 v_n+1
│   ├── 09-contradiction-map.md    ← ⚡强制(Phase5.5) **第四章 矛盾地图**：★4.1场景(涨跌/解锁/赔率×RMV·knobs存档) + 4.2双槽位 + 4.3深度研究(含历史对标) + 4.4三坐标(赔率/分歧/可证伪·分歧必走RAG取证) + 4.5叙事链下钻
│   ├── 10-summary-backsolve.md    ← ⚡强制(Phase6.5) **开篇章 一段话说清楚**：四点纯文字编号(类型/核心逻辑/算账/利润兑现期限·估值范式上界·潜在催化)；**§2 k 层钩子登记表**(生意本身/盘子/股性 三块必答+选答，每条＝该问的/去哪挖/合格形状)＝公司类型的提问框架；§7 CK-7 闸门表；附录 A 变更史
│   ├── 11-consensus-boxplot.md    ← (Phase1.5) **1.5 券商预期区间·兑现记录**：箱线图口径/★合成区间探测/EPS股本口径/薄样本闸/背离信号→第四章D
│   ├── 12-chip-age.md             ← (Phase1.6) **1.6 历史码龄**：换手率衰减模型推导/自由流通修正/长短码读法/已知局限
│   ├── 13-contradiction-typology.md ← ⚡强制(Phase5.5·查表用) **矛盾分型学**：主动十型(四族)/从动九型(★排除链判定顺序·纪律型是残差)/纪律升格三条件/系统协同型stack漂移/配对地雷表/单维案例库
│   └── 14-narrative-capacity.md   ← (Phase1.7) **1.7 可交易容量与波动位置**：韭研叙事vs问财题材/容量×换手强度×我的份额三量齐读/概念选取三闸/六个坑/★2.2 篮子对照给 M 实测锚
├── scripts/
│   ├── fetch_ifind.py             ← 拉 Part1 四数据集(fin/holders)→ifind_tables.json（确定性；**内置市场闸,非A股直接拦截**）
│   ├── fetch_quarterly.py         ← ★1.4 季度毛利率分解 + 1.4b 季度现金流/CAPEX 两块(iFind **`单季度.*` 原生指标**,非累计差分)；**强制 `单季度.` 前缀防取到同名累计列**；折旧只在中报/年报披露→**不摊平不插值**(单季不画/TTM 只给 Q2·Q4)；`--self-test` 不连网自检、`--from-raw` 离线复跑
│   ├── fetch_fundamentals_hkus.py ← ★港美股 Part1 替身(东财三表/分析指标+SEC EDGAR分部+杜邦/费率/市值锚+币种口径闸)
│   ├── fetch_earnings.py          ← ★Part2 披露日节点(业绩预告+定期报告实际公告日;AKShare东财逐报告期;--with-forecast 拉预告)
│   ├── fetch_fmp_consensus.py     ← ★1.5 券商预期区间箱线图(历史+未来一条轴;箱=Low–High,▬均值,○财报前预期,★实际)+兑现统计;**内置合成区间探测/EPS股本口径闸**
│   ├── fetch_chip_age.py          ← ★1.6 历史码龄(换手率衰减模型:短/中/长码占比时序+年龄分布+平均成本/获利盘;**自由流通修正闸**)
│   ├── check_consensus.js         ← ★1.5/1.6 headless 冒烟验收(39 项:箱体自洽/合成区间/EPS下线/码龄总和=100%/缺数据降级)
│   ├── fmp_config.json            ← FMP api_key/base_url(环境变量 FMP_API_KEY 优先)+inline判定带+薄样本阈值
│   ├── fetch_stock_profile.py     ← ★开篇章第一点「股性画像」(市值分层/涨停次数/波动·换手·beta；玩家结构配 factions_ts 判定)
│   ├── fetch_kline.py             ← ⚡Part2 周线真实OHLC(AKShare qfq日频→周聚合,腾讯备援;内置自洽校验,禁手填K线)
│   ├── fetch_fwd_pe.py            ← ★2.1b Forward PE 带(A股):东财reportapi逐份券商研报(相对年EPS字段)→时点一致预期→NTM混合;勿用akshare研报接口(相对年字段被错标成固定年份列)
│   ├── build_page.py              ← page_model.json → onepager.html（内联 Chart.js+引擎+app+标注层；--endpoint/--version/--no-annot）
│   ├── model_engine.js            ← 客户端计算引擎(P&L recompute + 8 估值范式 + 加权融合)；被 build 内联
│   ├── rag_query.py               ← 薄封装:对某标的工作区跑 research-rag search/facts（带 --as-of 防前视）
│   ├── rag_config.json            ← 嵌入后端配置(operative=qwen3-vl；qwen3.7-text 待 endpoint host)
│   ├── narrative_probe.py         ← ⚠️已退役(2026-08-14,JSON 解析缺陷)。方法论仍用(09 §7b),执行改直调 AlphaPai qa
│   ├── check_part3.js             ← ★第三章结构闸(04 §4.1/§4.2):A 反算隐含份额(seg_val 锚年 vs driver_chain 覆盖) + B L兜底段进 SOTP 上限
│   ├── check_summary.js           ← ★开篇章 CK-7 契约闸(10 §7,独立于第四章;`--hooks` 打印钩子登记表;`--json` 供评测):必答钩子覆盖(hook id 优先/k 关键词回退)+title 结论句+周期/成长·真β/假β/σ 判定句+pillars 链 c2–c5+算账差额行/price_assumes+ladder tier/mcap_if_yi+switches prob 对第四章+main_scenario+反算/脚手架扫描
│   ├── summary_hooks.json         ← ★开篇章 k 层钩子登记表(10 §2 的机器版：id/必答条件/k 回退正则/去哪挖)——改钩子只改这里 + 10 §2
│   ├── type_card.py               ← ★概览「公司类型卡」数据层(10 §2.8,2026-08-17)：真β/假β/σ/叙事-题材 建议 + β 面(1.7 篮子 β·R²/龙头中军后排/K 线方位) + σ 面(预期净利率·ROE 历史分位,Fwd PE/PS/PB 窗口分位)→ summary.type_card；作者定 type/verdict
│   ├── phase_valuation.py         ← ★★2.2 估值算账**双口径**(TTM×Forward)计算,写 valuations[].calibers；Forward 那栏给恒等式分解(市值≡前瞻盈利×前瞻PE)
│   ├── check_charts.js            ← ★★图表契约闸 CK-8(06 §3.0b/3.0c/3.0d,17项):查的是**读者会读成什么**而不是数算对没有——chg是带%的串/1.7双口径列/PE·PS不共轴/柱线分型/不许自称箱线图/**2.2估值算账双口径齐+散文读数对得上口径+schema降级哨兵**
│   ├── tornado.js                 ← ★Phase5.5 矛盾赔率:参数弹性龙卷风(锚区间摆动)+取期敞口+**弹性传导率披露**(--json 进 part4)
│   ├── ck5_gate.py                ← ★矛盾定型闸:V主导涨幅占比三档 + 现价在静态范式区间的分位(>100%强制判范式切换) + 数据体检
│   ├── narrative_capacity/        ← (Phase1.7) 叙事·题材容量工具包(无需API key,Playwright拦XHR)：jiuyan/wencai/roster/relevance/concept_capacity/dispersion/vol_percentile + **onepager_module.py 直写 page_model** + **bench_index.py 同期对照锚(沪深300+申万二级行业,给被诞生日硬闸掉的阶段补锚)**
│   ├── check_part4.js             ← ★CK-6 自动验收(headless,64项):S1-S8 场景(**knobs 实跑引擎对赔率**/dir与odds符号/带子夹住点估计) + T1-T7 分型(枚举/各≥1/排除链/纪律型三条件/stack) + D1-D3 深度研究(blind_spot/analog.diff) + 契约 a–f + 几何 g(圆方等面积/重叠/标签碰撞)
│   ├── deploy_page.py             ← ★上线反馈平台(stage 进 site/<ticker>/ + 生成索引 + wrangler deploy；洁净闸)
│   ├── feedback_pull.py           ← ★回收标注(云端 or 页面导出 json)→ round_<n>.md triage + resolutions 骨架 + 台账
│   ├── feedback_resolve.py        ← ★回应写回 page_model(resolved/open) + 版本+1 + 云端 status（空答复闸）
│   ├── feedback_config.json       ← endpoint/token（token 建议走环境变量 FB_ADMIN_TOKEN 不落盘）
│   └── vendor/chart.umd.min.js    ← Chart.js 4.4.9（内联，离线可开）
├── templates/
│   ├── onepager_template.html     ← 页面壳 + CSS + DOM 挂点 + 占位 token + data-fbk 锚点
│   ├── app.js                     ← 渲染 + 交互（消费 window.__DATA__ + window.EONE）；被 build 内联
│   └── annot.js                   ← ★反馈标注层(划词/整块标注→localStorage→同步/导出；挂 window.__EONE_FB__)
├── feedback/worker/               ← ★反馈平台(Cloudflare Worker + KV + 静态站)：src/index.js · wrangler.toml · site/
└── examples/INDEX.md              ← 案例索引（立昂微 605358 种子）
```
复用现有 client（绝对路径调用，勿重复实现传输层）：iFind=`~/.claude/skills/ifind-research/scripts/ifind_client.py`；AlphaPai=`~/.claude/skills/alphapai-research/scripts/alphapai_client.py`；Comein=`~/.claude/skills/comein-research/scripts/comein_client.py`（⚠️ 本机未安装，2026-08-16 自检确认；当备源写但别当它在）；qcc=`mcp__qcc-company__*`。
> **环境注记（2026-08-08 校正）**：本机为 macOS，路径不再是 `C:/Users/youqi/...`；且**只有 `python3`，没有 `python`**——本文档里所有 `python scripts/xxx.py` 在本机一律用 `python3` 执行。

每次运行的工作目录：`_workspace/<ticker>/`（含 `raw/` 原始应答、`ifind_tables.json`、`page_model.json`、`onepager.html`、`source_audit.jsonl`）。

> **★2026-08-03 数据目录外迁（重要）**：`_workspace/` 是软链 → `~/Desktop/research-materials/`（按「公司名-代码」归档，如 `京东方A-000725/`），skill 文件夹内不落任何采集/产物数据（飞书消息、研报、纪要、点评、onepager 产物都进 `research-materials/<公司名>-<代码>/`）。ticker 软链别名（`000725 → 京东方A-000725`）保证 `_workspace/<ticker>/` 旧引用照常工作。采集脚本 `fetch_feishu_msgs.py` 缺省输出到 `research-materials/<公司名>-<代码>/feishu/`。**不要在 skill 目录内 mkdir 数据文件。**

---

## 工作流（Phase 0.0 → 9；Phase 8-9 = 上线收标注 + 认知螺旋回灌）

**Phase 0.0 · 前置资料询问 + 建 RAG 语料库.** 读 `references/07-rag-corpus.md`（⚡）。**每次执行本 skill，先问用户一句：「有没有前置资料压缩包？」** 然后建标的专属 RAG 工作区（复用 research-rag，不重造）：
- **有 zip** → `cd /Users/yqgao/Desktop/gyasset/research-rag && python research_system.py --zip "<用户zip>" --target "<标的 简称+代码>" --project "<ticker>"`（unzip→build_index qwen3-vl→facts→doctor 过闸，落 `workspaces/<ticker>/`）。
- **没 zip** → `python research_system.py --target "<标的>" --project "<ticker>" --sweep`：research-sweep 自动找料（**含飞书「作文实时2」群 + AlphaPai 卖方点评/段子** + 卖方研报/纪要），按 `SWEEP_PROMPT.md` 采集→打包→增量入库→doctor。时间范围按复盘所需（Part2 默认 ~3 年）设采集问题。
- **飞书群消息直采（★2026-08-03 lark-cli 接入固化，前置资料标准一环）**：轻量路径用 `python scripts/fetch_feishu_msgs.py --target "<标的简称 代码>" [--groups 群] [--start/--end]` 在飞书投研群（默认「作文实时2」）按标的关键词搜消息 → 落 `feishu/_merged.md`（去重含原文/链接）→ `python rag_add.py feishu/ --ws workspaces/<ticker>` 入库。详见 `references/07-rag-corpus.md §2b`。
- 记下工作区路径 `RAG_WS = research-rag/workspaces/<ticker>`，供 Phase3/4/5 取证。嵌入后端见 §嵌入说明（operative=qwen3-vl；qwen3.7-text 待 endpoint）。若用户明确「无料且不建库」→声明「本次无 RAG 底稿，算账仅凭 live API」，跳过建库但页面数据标记降级。

**Phase 0 · 解析与路由.** 确认 ticker + 市场（A/HK/US）。**A股**→结构化管线全开（iFind）；**港美股**→iFind 结构化 `fin/holders` 不解析（返回「查询结果为空」且不报错），走 `fetch_fundamentals_hkus.py` 这条腿 + 年报公告 `search_notice`/AlphaPai 补，页面受限项标注「数据受限/口径来自年报」。用 `mcp__qcc-company__get_company_by_query` 锚定法定名（供 Phase2 子公司；**仅大陆主体**）。取实测市值/现价/总股本（A股 iFind `fin` 估值列 或 ashare-data-sources；港美股由 `fetch_fundamentals_hkus.py` 的 `meta` 给，**并先过 `meta.currency_check`**）。建 `_workspace/<ticker>/`。
**★港美股必须先定币种（2026-08-02 固化）**：`page_model.meta` 的 `currency`/`fx`/`fx_asof` 三字段在港美股上**必填**——财报币种、交易币种、页面展示币种三者可能互不相同（实测腾讯 00700：财报人民币、交易港元，自算 PE 19.2 vs 接口 PE-TTM 16.43 差 17%）。脚本的 `meta.currency_check` 会算这个比值并在偏离>15% 时报 gap；**未查清前不得把 `mcap_yi` 喂进估值范式**，否则赔率会整体错一个汇率。

**Phase 1 · 拉 Part1 数据.** 读 `references/01-data-recipes.md`（⚡）。**A 股**跑：
```
python scripts/fetch_ifind.py --name <中文名> --ticker <代码> --y0 <上市年或近10年> --y1 <上年> \
  --out _workspace/<ticker>/ifind_tables.json
```
得 6 张解析表（segment_product/industry/region、dupont、cost、holders）+ `raw/*.md`。缺口自动列出→按 01 的 fallback 补（Comein/AKShare/qcc）。
**★`--y0` 一律传上市首年**（不是「近 10 年」）：1.4 已改成毛利率分解堆积柱、横轴**上市以来**（02 §1.4），
费率结构的范式切换（研发从管理拆出、补贴退坡、财务费用转负）多发生在上市早期，砍成近十年只剩一段平台期。
`cost_structure.listing_year` 必填，CK-8 d4/d4b 拿它核对起点。上市日期走 `fetch_stock_profile.py` 或 iFind `info`。

**★季度腿（1.4 + 1.4b，A 股一条命令直写 page_model）**：
```
python3 scripts/fetch_quarterly.py --name <中文名> --ticker <代码> \
  --y0 <上市年> --y1 <本年> --listing-year <上市年> \
  --model _workspace/<ticker>/page_model.json --write
```
产出 `part1.cost_structure_q`（1.4 逐季毛利率分解）+ `part1.cash_capex`（1.4b 逐季现金流/CAPEX/折旧）。
**全部取 iFind `单季度.*` 原生指标，不是自己拿累计差分。**
两条实测钉死的纪律（**改口径前先跑 `--self-test`**，不连网）：
① **同一张返回表里累计列与单季列同名并存**（`销售费用` vs `单季度.销售费用`），
   脚本强制 `单季度.` 前缀，匹配不到宁可留空——退回累计列就是把 Q4 的全年累计当单季画上去；
② **折旧摊销一年只有中报、年报两个披露点**（A 股季报不含现金流量表补充资料），
   **单季折旧在报表上不存在** → **不摊平、不插值**：单季视图不画它，
   TTM 视图只在 **Q2/Q4** 给点（由披露的累计数精确凑出），`da_disclosure[]` 落原始披露段。
无数据时整节隐藏并从目录摘链，不留空图。`--from-raw <raw目录>` 可离线复跑不重复消耗额度。

**港股/美股**改跑（`fetch_ifind.py` 遇非 A 股会直接拦截并打印这条命令）：
```
python scripts/fetch_fundamentals_hkus.py --ticker <AAPL|00700> --market <US|HK> \
  --y0 <近10年> --y1 <本年> --out _workspace/<ticker>/fundamentals.json
```
产出 `tables.{income,balance,cashflow,indicators,dupont,cost_structure,revenue,consensus,pe_history,...}` + `meta`（币种/股本/市值/PE + `currency_check`）+ **`gaps[]`**。
**`gaps[]` 是本步真正的交付物之一，Phase2 前必须逐条处理**——它把「结构性拿不到」（派系图/股权树/港股分部）与「本次没取到」（某科目缺列）分开列，缺口写进页面标注而不是静默略过。
覆盖差异（实测锚：AAPL / 00700）：美股杜邦四项齐、分部走 SEC 10-K R-file 拿到 产品线/报告分部/地区 三个切面；港股三表回溯到 2001 但**无分部结构化源**，另有惊喜项 `consensus`——etnet 给**逐家机构**的纯利/EPS/目标价/评级/更新日期（实测腾讯 19 家），脚本已顺手算好 `dispersion`（家数/极差/形态），**直接就是第四章 `dispersion_basis` 的原料，这一格港股比 A 股好取**。

**Phase 1.5 · 券商预期区间 + 兑现记录 + 未来延展（A/HK/US 通吃，一条命令）.** 读 `references/11-consensus-boxplot.md`。
前四小节讲「已经发生的」，第三章讲「我认为会发生的」，中间缺一层：**市场认为会发生的、以及市场过去猜得准不准**。跑：
```
python3 scripts/fetch_fmp_consensus.py --ticker <裸代码|NVDA> --market <A|HK|US> \
  --page-currency <page_model.meta.currency> \
  --kline _workspace/<ticker>/kline_weekly.json \
  --out _workspace/<ticker>/fmp_consensus.json
```
产物**整份**塞进 `page_model.part1.consensus`。页面渲成**一条连续时间轴**：左已披露（箱=券商 Low–High，▬=区间均值，○=财报前一致预期，★=实际披露值），右未来预期（箱 + ▬ + ◆=第三章模型值，随滑块动）。收入/净利润/EPS 三口径 × 季度/年度可切。
**五条硬纪律（2026-08-08 多智能体审计后固化，每条都有实测反例）**：
1. **箱体是全距不是四分位**——FMP 只给 Low/Avg/High，`box_caliber` 必须渲，**不许删**。
2. **★ 合成区间必须探测并剔除**：FMP 对早年缺失分歧会**回填固定比例的假区间**——002371 FY2015–22 的 `lo/avg` 恒为 0.9448、`hi/avg` 恒为 1.0593（覆盖家数在 8~17 间跳、比值纹丝不动）；**AAPL FY1998–2023 长达 26 年恒为 0.80/1.20**。脚本 `mark_synthetic_bands()` 探测式识别（连续≥3 期比值相同），**per-ticker，绝不写死年份**；这些期排除出**全部**兑现统计、页面画灰标「合成区间」。不剔除的话 002371 净利润 `avg_range_pos` 会是 −0.46，剔除后翻转为 **+0.53**、区间命中率 54.5%→100%。
3. **EPS 历史兑现整体下线**：FMP 预期 EPS 用固定/漂移的隐含股本（300750 的 Low/High 钉死 4540M 而 Avg 漂 4384~5160M），实际 EPS 用当年报告加权股本，**分母不同源**；相减会得出「净利 miss 但 EPS beat」的矛盾（002371 FY2016 −12.7% vs +48.5%）。**已披露期不画 EPS 实际值、不进统计**；未来期 EPS 区间保留供 forward PE。看兑现记录**只看收入与净利润**。
4. **财报前一致预期按营收值配对，不按日期就近**：A 股年报与一季报公告只差两三周，日期就近会让 26Q1 抢走年报行（实测把真 miss 判成 **beat +132%**）。
5. **股价反应只做季度且必须在 K 线窗口内**：年报期末（12-31）距实际公布（次年 3-4 月）差 3 个月，用期末当锚点必错；窗口外的期一律跳过（否则全部落到第一根 K 线，产出一串一模一样的假涨跌幅——实测 002371 的 21Q4/22Q1/22Q4 都被算成 −8.0%）。
下游弹药：**第四章 `part4.items[].D`** 直接用非合成期的 `spread`；**第二章阶段归因**用 `divergence`（beat 不涨 / miss 不跌）反查那一段股价交易的到底是不是财报。

**Phase 1.6 · 筹码龄结构（长钱 vs 中短钱）.** 读 `references/12-chip-age.md`。**仅 A 股/港股**。
**口径以用户既有的《沪深300+中证500 全生命周期筹码结构》为唯一标准 = 同花顺「筹码龄分析」复刻（档位 2/10/100 · 系数 1.0），不自创口径。** 跑：
```
python3 scripts/fetch_chip_age.py --ticker <裸代码> --market <A|HK> \
  --out _workspace/<ticker>/chip_age.json [--ifind-check]
python3 scripts/fetch_chip_age.py --calibrate 002138     # 改模型后必须重跑对表
```
**四条硬纪律**：
1. **档位 2/10/100，不是别的**：超短 [0,2) · 短 [2,10) · 中 [10,100) · 长 [100,∞)。同花顺均龄中点 1/6/55/365 正好是各档算术中点（可反推验证切法）。对表锚：002138 @2026-07-24 = 31.75（客户端 31.74），本脚本 32.00，偏差 0.8%。
2. **必须拆结构层**：一条总均龄分不开「结构」（长/中短此消彼长）与「总量」（两档一起变老）两种成因——参考页实测 20% 的票两项方向相反，单看总均龄必然误判。所以要出**长钱均龄 + 中短均龄**（分档内逐批加权），不能只给占比。
3. **展示纪律**：红绿为 K 线独占；均龄族暖色/占比族冷色/分位灰虚线；**均龄轴走对数**（中短 10–70 与长线 100–520 差一个数量级，线性轴会把中短压成直线）；三条均龄各占一根右轴、**比形状不比高低**；周线展示、日度计算。
4. **λ=1 的不可识别性必须声明**：分档换手率由价量不可识别（一个方程三个未知数）。λ 由 1.0 压到 0.3 的水平漂移÷波幅：中短均龄 12% < 占比 18% < 真实均龄 64% < **长线均龄 82%**，但 |Δρ| 中位仅 0.03–0.10 → **水平值只当口径参考，方向/斜率/拐点/相关性才可直接采信**。另：长线档无主动买入路径，占比上升永远是被动的；真长钱进场是两段式（先中短占比抬升，100 日后长线接棒）。

**★ 反脚手架（1.5/1.6 通用）**：口径、模型、边界这类「我怎么做的」**一律收进默认折叠的「口径与方法」块**，正文只留图例与结论——同 CK-7 j 条纪律。

**Phase 1.7 · 可交易容量与波动位置（叙事／题材篮子）.** 读 `references/14-narrative-capacity.md`。**仅 A 股**（依赖韭研产业链与问财概念）。一条命令直写 page_model：
```bash
cd scripts/narrative_capacity
python3 bench_index.py --list 光伏                    # 先查申万二级行业名，别凭印象猜
python3 onepager_module.py --name <公司简称> --model _workspace/<ticker>/page_model.json \
        --bench <申万二级行业名,逗号分隔> --write     # ★--bench 必传，见下条
```
**不需要 API key**，走本机 Chrome 拦网站自己的 XHR（首次需 `pip install playwright && playwright install chromium`）。产出两块：`part1.narrative_capacity`（1.7 节）与 `part2.phases[].basket_beta`（2.2 阶段列内的篮子对照）。
**第一性原理：股价＝资金÷筹码**——叙事决定钱往哪去、容量决定钱摊多薄、我的份额决定我分到多少。所以**三个量必须凑齐才写进报告**：换手强度＋三年分位（钱来了没有）、自由流通容量（摊多薄）、篮子内排名与占比（我能分到多少）。**单看容量没有决策含义**，而且**容量大≠空间大，正好相反**：容量大是吸收力强、单位资金推力小，真正有赔率的形态是**失配——叙事级别高但篮子小**。实测巨星科技：储能换手强度第 76 分位（钱确实来了），但它排第 98/895、只占 0.2%，钱来了也买不到它——这一句直接解释了阶段⑤储能篮子 +8.4% 而个股 −23.1%。
**先看韭研叙事（人工梳理、点名成分、20–30 只），没有再退回问财题材（机器打标、覆盖全 A）**；两者同口径可横比，量级差就是「故事讲给谁听」与「钱实际能进多少」的差别。**★`basket_beta` 是这个模块真正的价值**：第二章 R/M/V 里的 M（板块/贝塔）原来只能估，现在有实测锚——篮子已剔除本股（否则个股权重大时超额被自己稀释），某段 M 贡献大而超额≈0 就说明那段涨的是整个篮子不是这家公司，该段 `logic` 必须写明。
**★★但叙事篮子有诞生日，股价历史没有（2026-08-14 阳光电源抓出的结论级错误，14 §7b-0/§7b-1）**：韭研标题里的 `(260709)` 是建链日，**建链日晚于阶段起点的篮子整行剔除**——那个概念当时不存在，成分是照着已经涨完的那批票圈出来的，算出的超额是伪读数（这比幸存者偏差更硬：不是输家掉出名单，是整个类别事后定义）。阳光实测阶段①② 11 条篮子全部事后定义，阶段④ 报告里那句「AI 电力四条篮子超额 −46.4pp」四条当时一条都不存在。硬闸后早期阶段会整段没有对照，所以 **`--bench` 必传**：申万二级行业指数分类持续维护、成分非事后圈定，是真·同期锚（`bench_index.py`，走 akshare `index_hist_sw`；东财行业板块在本机被远端掐，别用）。**补锚不是补图，要回头改 `logic`**——阳光阶段⑥ 用污染篮子读出「叙事有效但这只票没被选中」，用光伏设备 −26.7% 读出「行业整体在跌、本股额外多跌 15pp」，两句话的仓位含义完全不同。
坑与口径（科学计数法/假 page 参数/问句 200 字上限/覆盖<60% 不给分位）见 14 §5–§6。

**Phase 2 · 映射 Part1 + 派系/股权.** 读 `references/02-part1-fundamentals.md`。人工映射解析表→`page_model.part1`：
- **最新财务快照**（★概览必出）：iFind `fin` 取**最新单季**收入/归母/毛利率/净利率 + YoY/QoQ（单季度列），及 **TTM 年化**收入/归母 → `snapshot`。用户强调「单独捞出来重点看最近」。
- **营收**：分部收入 **元→亿元**（`/1e8`），处理 `万/亿` 后缀；**跨年标签归一化**（同一业务逐年排名会变）；只有 top-5，尾部并「其他」；补总营收+YoY。**上市过久→只取近 8–10 年**。★**业务/客户里程碑**：从年报大事记/公告逐年挑，落 `revenue.milestones[{year,cust:[红],biz:[蓝]}]`，页面在营收图下**按年份对齐标注**（不是平铺 tag）。
- **杜邦**：直接取 ROE/净利率/周转率/权益乘数（口径干净）。
- **成本/费率**：iFind 常只给 销售/研发 费率 + (管理+研发)/营收；管理费率=合计−研发；财务费用率缺→再查或 `⚠️未查到`。
- **股东 + 派系时间序列（★）**：解析 holders top-10（性质）+ 前十大合计→concentration；**按 nature+研究把每季分派系**→`shareholders.factions_ts`（**近5年逐季**时间序列：原始股东(个人法人)/国资/公募(偏基本面定价)/游资·量化(**查历史有无炒作、两轮催化期脉冲**)/ETF·被动/北向·外资/社保·险资/散户），页面出**逐季堆积图看派系迁移**（历史沿革+时间横向比较）；只留 `faction_analysis` **一行定价权结论**（不再出派系明细卡）。逐季用 iFind `holders`/`events` 按报告期取十大股东性质→映射派系%。**★上市前融资史 + 派系类型（2026-08-12，见 02 §1.2b）**：招股书「资本沿革/Pre-IPO Investments」章节取融资轮次（RAG/`search_notice`/ipo-prospectus-scanner，qcc 工商变更交叉）→`shareholders.pre_ipo`（rounds 时间线 + IPO 时创始人/PE 持股 + PE 当前持股→退出进度条）+ **archetype 四选一判定**（founder 产业坐庄 / pe_diluted PE退出 / soe 国资 / dispersed 无实控人，判定带数字），渲在派系堆积图上方；查不到整块不填并声明，不许拿传闻凑。
- **股权结构树（★）**：qcc（先 `get_company_by_query` 锚法定名）→ `get_actual_controller`+`get_beneficial_owners`(实控人+一致行动人+控股平台) + `get_external_investments`(子公司+持股%) + `get_branches`/`get_company_profile`(区位/主业) → `ownership`（controllers→platform→上市公司→`sub_groups` 子公司**按业务分类**:非核心/核心零部件/软件…）。**永不用 iFind 查子公司**（静默命中股东数据）。

**Phase 3 · Part2 股价复盘.** 读 `references/03-part2-price-review.md`（⚡）。**周线 OHLC 一律跑 `python scripts/fetch_kline.py --ticker <裸代码> --market A|HK|US --weeks 160 --out _workspace/<ticker>/kline_weekly.json`**（AKShare 东财 qfq 日频→周聚合，主源；腾讯 ifzq.gtimg.cn qfq 周K 备援；脚本内置 h≥max(o,c)/l≤min(o,c)/非c-only 校验，不过闸拒绝落盘）——**K 线绝不手填/编造/只给收盘**，c-only 假蜡烛页面会打红色警示且 CK-2 不过。产物 `weekly` 直接进 `page_model.part2.weekly`。**页面画 K 线（涨红跌绿）+ MA5/10/20/60 均线**（MA 由 closes 自动算），**不要折线图**。划 3–6 阶段（每段≥6周、单一 regime、有转折）；每阶段写 **主要矛盾(core_conflict)+分析逻辑(logic)**+主/次因子(R/M/V)+估值锚+**Forward 算账(PE 三档)**+**★`factor_quant` 涨幅量化分解**（R/M/V 各贡献多少 pp，对数三因子，03 §2f-q——页面在阶段列内渲三根同尺度条，跨阶段直接比）；标 15–25 个催化（每个 **G1-G5 五大催化剂**(G1数据高增长/G2接大订单/G3有大佬站台/G4传播出圈/G5公司有诉求) 1-3 码→9维扫描→R/M/V 复合码→≤40字 summary + **`links[]` 原始材料超链接**），**催化标记=悬停浮窗**（形状=R/M/V 主因子●▲★、颜色=五大催化剂、#n=该类型第 n 次出现；悬停即弹卡且 9 维默认展开，点击=钉住；浮窗只给链接不放原文）；**2.1b Forward PE 带**A 股必跑 `python3 scripts/fetch_fwd_pe.py --ticker <码> --market A --kline <kline_weekly.json> --out <fwd_pe.json>`（逐份券商研报重建**时点一致预期**+NTM 混合，产物整份塞 `part2.fwd_pe`，03 §4g），再按 §4g 把卖方目标市值/盈利预测取证成 ◆ 锚点合并进去（港美股/未跑脚本时页面退回 FMP 财年近似并红字标注）；**2.3 催化清单默认收起**。**算账/催化优先从 RAG 取证**：`python scripts/rag_query.py search "<标的> 卖方 目标价 算账 催化 分部" --ws <RAG_WS> --as-of <阶段末日期>`（`--as-of` 防前视，后验复盘必用）+ `rag_query.py facts <标的> <指标> --ws <RAG_WS>`；命中的纪要/研报原句带 `[doc_id p4]` 引用进 分析逻辑/催化 driver，缺则 Comein/iFind 补，AlphaPai 质检。
**横向面板（对齐宁德/英维克范式，纵向堆卡已废弃）**：2.2 是**一列一阶段的横向面板**（左→右对齐 K 线，宽∝时长）——每列＝该段 主要矛盾+主/次因子+估值锚+**分析逻辑**+**估值算账**（`valuations[]` 与 `phases[]` 同序：稳态市值→Step A 分部毛利→Step B 合计对财报±5%→Step C 费用桥→归母→PE 档理由→隐含/Forward→ΔPE vs 上段+consensus 质检）。写 `page_model.part2`。

**Phase 4 · Part3 P&L 建模.** 读 `references/04-part3-pl-model.md`（⚡）。按 archetype 拆分部；**历史列=财报实际**(hist_actual，来自 iFind)，**预测列=分部 量×价×毛利率 驱动 + 费用率假设**；通用利润桥→净利/EPS。写 `page_model.part3.segments/opex/hist_actual`。**三条硬规则（2026-07-21 用户反馈固化）**：
- **拆分穷尽**：Σ分部收入=总收入；机房/物业/PCB/军工等**其他资产与杂项业务必须显式单列一段承载**（残差段），不得静默丢弃；对应资产的折旧进 D&A 注记。
- **分业务一必拆真量价**：最大分部**禁止** `q=收入指数,p=1` 的 L 兜底——必须给物理量（出货量/装机/客户数）×价（ASP/单价），从纪要/卖方模型/行业数据取，标 EST；其余分部若降级须在 `model` 里声明（页面会自动打 ⚠️）。
- **每分部必填 `segments[].model`**（细分建模卡）：`q_def/p_def`（量价物理定义）、`logic`（驱动树+预测逻辑，可信HTML）、`assets_note`（资产/产能注记）、`q_anchors/p_anchors/gm_anchors`（类比锚，供 3.2+ 锚线图与假设滑块 ▲ 刻度）、`seg_val`（分部估值：method/profit_yi/mult/note）——页面自动生成 **3.2..3.(N+1) 分部模型章节**（含量价锚图），核心假设/估值顺延为 3.(N+2)/3.(N+3)。
- **★Driver 三件套（2026-07-25 用户反馈固化，见 04 §1.17）**：用户口径「Driver 字太小 + 逻辑没说清 → 要 link 到 RAG 原句、要讲清不同口径的区别与选择」。模板已把 Driver 区字号提到 14.5–15px（**别再调回 12px**，06 §2.2 字号纪律），内容侧三件套：
  ① **`driver_chain[]`**（core 段必填）＝外部物理量→本段收入的**逐步算账链**，每步 `{step,expr,val,tag,ev,note}`、末步 `out:true`——把散文逻辑变成一串可核的算式；
  ② **`calibers`**（同一参数出现 ≥2 个口径的数时必填）＝**口径取舍决策卡**（宽表格已废弃，04 §1.17c）：`① subject + N 种口径 → ② 刻度条（v/v_lo/v_hi/short 把「差几倍」画出来，>10 倍走对数轴，<1.5 倍改渲「互证」一行）→ ③ 用哪个(chosen_label) + 为什么(why) + 用错的代价(cost_if_wrong，写成量级后果) → ④ 候选明细（采用在前，弃用灰化+删除线+「不可直接入模」）`；
  ④ **阅读动线（★2026-07-25 第二轮反馈）**：分部章节＝**有编号的顺序**，不是块堆——`renderSegmentModels` 自动排 `1 怎么建模 → 2 驱动链 → 3 口径取舍 → 4 模型表 → 5 量价锚图 → 6 分部估值 → ✓ 段末小结`（缺 2/3 自动跳过重排编号），面板顶「阅读顺序」条可跳转，章级另有「本章怎么读 1→N · 加权估值=终点」；段末小结＝算出来什么(活数字)/往后盯什么(verify)/最脆的一格(fragile)/原句 chips/→下一段，**明确终点**。
  ⑤ **原句走浮层不占版面**：正文只留 `[Ex]` 角标与一行 chips，点击 → 居中浮层（mask+逐字原文/我的推论两层标签+段内 `‹ ›` 翻页+一键复制取原文命令/原件路径，Esc/点遮罩关）。**不许再把原句 inline 展开**。
  ③ **`evidence[]`**（core 段必填）＝**RAG 原句卡** `{id:'E1',doc_id,page,date,type,src,confidence,quote(逐字),implication(我的推论),used_in}`——原文与推论物理分离，正文 `q_ev/p_ev/driver_chain[].ev/calibers.rows[].ev/driver_focus.ev` 按 id 挂 `[E1]` 可点角标，页面自动给「取原文命令」`rag_query.py <ws> get_doc <doc_id> --text` 一键复制。
**预测假设(量/价/毛利率增速)优先从 RAG 的卖方模型/纪要取锚**：`rag_query.py facts <标的> 出货量|ASP|毛利率|资本开支 --ws <RAG_WS>` + `search "<标的> 产能 稼动率 扩产 单价 假设"`；跨源对账后落 assume 与 anchors，冲突标注。自洽校验：合计毛利对财报 ±5%，量×价对分部收入 ±0.5%。
**★外部物理驱动型分业务一（2026-07-22 华丰 688629 固化）**：分业务一的 q 由外部物理量驱动（AI 芯片出货→连接器套数、装机→耗材、车型销量→单车价值量…）且标准 `q_growth` 滑块承载不了「多型号出货×配比×份额×ASP-mix」结构时，按 **04 §5.5 建 driver 注入层**——算量器面板（参数逐年数组全可调）+`确认收入=min(需求盘,产能)` 钳制+首跑 writeback+估值活链 relinkAll+钳制黄警示；预设按钮=卖方分歧具象化（把收入分歧翻成 2-3 个参数差）；专家纪要口径（每套/每卡/每柜）先建对账表归一再进公式。案例锚：examples 华丰 688629。

**Phase 5 · 多范式估值.** 读 `references/05-valuation-paradigms.md`。为 8 范式填参（对标大哥/PE/PEG/SOTP + PB-ROE/EV-EBITDA/终局份额/反推隐含[诊断,权重0]）；**★五档估值等级系统（2026-08-12，05 §0.5）**：卡片/横条按 第一档(PB/重置)→第二档(静态/Fwd PE)→第三档(PEG)→第四档(N+2 PE/PS/单位利润·SOTP)→第五档(终局/五年规划/对标大哥) 排列（app 自动归档+徽章+等级带含升档赔率 二20-50%/三30-50%/四50-100%/五100-300%）；**折现率 r 硬边界 0.08–0.10**（成熟 0.08/成长 0.09/极早期 0.10，旧 12–18% 弃用，不确定性走 N 或档位表达）；**对标大哥必须点名**：`leader` params 必填 `leader_name`（公司全名+代码，如「村田制作所 6981.T」）+ `basis` 口径（**默认 `revenue`：本司稳态收入/大哥收入 = 收入占比 → ×大哥市值 = 市值占比**；利润占比作 double-check，双轨背离>30% 必须解释）——未点名页面打红 ⚠️ 且 CK-4 不过；PE/PEG/EV-EBITDA 设 `link:true` 让 Forward 值联动 P&L 模型。设默认权重（预设 历史40/可比30/增速匹配30 → 映射到 PE/对标/PEG，其余小权重）。**对标大哥/可比倍数/终局份额/卖方目标价从 RAG 取证**：`rag_query.py search "<标的> 可比公司 估值 目标价 PE PS 份额 TAM" --ws <RAG_WS>` + `facts <标的> 目标价`；用命中的卖方一致预期/可比锚校准 params，隐含市值 vs 实测差>15% 时回 RAG 查是否漏板块。写 `page_model.part3.valuation`。
**★Forward 利润取期 + 静态范式活链（05 §9.5，2026-07-22 固化）**：交互深模型 `forecast_years` 建 **5 年**并在估值区加取期选择器（按钮切 pe/peg/evebitda 的 `year_offset`，PE 折现 `n`=年距同步，SOTP/终局/大哥恒锚各自语义年**不跟随**，附「现市值÷该年归母=Yx」隐含读数+「远年利润配低 PE 档」纪律提示）；凡页面提供"改假设→看估值"交互，sotp/leader/endgame 三条静态腿必须在改动回路里活链写回（引擎不支持 link），分部估值卡 DOM 同步。

**Phase 5.5 · 第四章 矛盾地图.** 读 `references/09-contradiction-map.md`（⚡）。前三章给的是「是什么」，**第四章给「下一步盯什么、押哪一条」**——不新增分析，只把前三章已有的东西按「未定」重排一次序。三步：
1. **赔率跑脚本，不许手估**：`node scripts/tornado.js --model _workspace/<ticker>/page_model.json --json` → 参数弹性 bar（在各参数**自己的锚离散区间**内摆动）+ **取期敞口** + **弹性传导率**。引擎不活链静态腿（05 §9.5 的 relinkAll 只在页面 JS 层），bar 是**下界**，须按 `上界≈下界÷传导率` 读（002371 传导率 50%、688521 仅 20%）。**取期敞口通常压倒参数弹性**（实测 49% vs 15%、90% vs 45%），所以必有一条「市场定价期限」类矛盾归估值层。
2. **分歧度必须走 research-rag 逐条取证**（本章最硬纪律）：`python scripts/rag_query.py <ticker> search "<标的> <该矛盾关键词> 预测 假设 口径" --top 6` → `dispersion_basis` 写清 **①每家给的数（机构+日期+原样数字）②极差 ③形态（双峰/单峰宽/零覆盖）**，逐字原句落 `items[].ev[]`。**`coverage:0`（无人发表→方差≈0）是最高价值信号**，页面画虚线圈；AlphaPai 在这一步只当**覆盖密度测量仪**，提问必须带「若无请直接回答"没有"，不要推测」。**RAG 常会推翻你的假设，那正是它的价值**（实测把「产能零覆盖」推翻成「长江证券覆盖且结论相反＝真双峰」）。
2b. **★叙事链必须过 AlphaPai 探针再落 `subs[]`**（09 §7b，2026-07-31 用户反馈固化）。用户原话「次级叙事拆解得不够好」——根因是 `subs[]` 靠自己想只会写出**我已经知道的那几环**，而本地 RAG 只覆盖用户给的那一包料（688825 实测 555 篇里**零篇外资研报、几乎没有正式盈利预测表**）。AlphaPai 读过全市场，是**卖方共识测量仪**：
   **⚠️ `scripts/narrative_probe.py` 已退役（2026-08-14 阳光实跑确认，三条探针全挂在 JSON 解析上）。改为直调 AlphaPai `qa`**（`alphapai-research` skill 的 `alphapai_client.py`），把下面三条提示词纪律写进一个自包含问题即可，效果与原探针等价；方法论（三种探针的问法、rival_numbers 的用法、provisional 复核纪律）全部照旧，见 09 §7b。
   三条提示词纪律：**①观点必须带数字**（问题感知检索靠数字定位盈利预测表，写"估值合理吗"只会捞回定性话）；**②`--concern` 塞关键前提清单**（第二个检索入口）；**③模板结尾写死零覆盖闸**（"若无请直接回答没有，不要用行业常识补齐"）。
   **★真正的产出不是它的结论，是从 `references[]` 抽出的 `rival_numbers[]`**（机构+日期+原样数字+逐字原句+URL）——那是 `dispersion_basis` 的原料，可直接进 `ev[].quote`。产物一律 `provisional:true`，**逐条回 rag_query/page_model 复核后才准进图**；**它推翻你的假设时别护着模型**（688825 实测：查出"新增产能很多在体外"，直接把"少数股东占比随产能摊薄下降"从基准假设降级成待验证路径；阳光实测：抓回摩根士丹利 SST 渗透率 15%/单价 1.3 元/W/美国收入 10.1 亿，与内资东吴"远期 160 亿利润"**差 4–40 倍，模型据此下修 40%**）。召回 <3 家具名机构时只取 `rival_numbers`，丢弃 answer 正文（幻觉高发区）。**它也会老实答"没有"**（阳光三项零覆盖：CSP 自建电源比例／之江实验室订单规模／阳光在 NV 800V 架构中的份额），零覆盖闸是有效的；**但历史叙述会串日期**（把 2026-04 的年报爆雷说成 2025-04），时间线一律回 K 线/公告核。
2c. **★每条矛盾定 `role`/`subtype`/`clock`，查 `references/13-contradiction-typology.md`（⚡查表用）**。`role` 是**主动**（生成上行）还是**从动**（限制上行、决定节奏），与 `layer`、`dir` 都正交——页面上 **● 圆＝主动、■ 方＝从动**。三条硬纪律：**①两类各 ≥1**（只有主动＝不知道会被什么洗出去；只有从动＝不知道为什么值钱）；**②主导＝持有期内时钟最短的那条，不是最重要的那条**（`clock(从动) < 持有期 < clock(主动)` → 你按主动定持有期、市场按从动交易，必被洗；但周期复苏型主动矛盾时钟以季度计，会出现时钟倒置，所以是**查表比大小**不是"从动永远主导"）；**③从动矛盾必须走排除链**（13 §2a 前置闸→物理→系统协同→要素/禀赋→制度→资本→弹性→纪律），走过的步骤留痕 `ruled_out[]`。**纪律型是靠反事实定义的残差类别，只能最后判**，且要过升格三条件（可盈利/可认证-限定在持有期内/仍不扩且有厂商原话）——**它也是唯一一型 `coverage:0` 是危险信号而非价值信号的**。系统协同型带 `stack[]`+`binding_now`，因为**约束会漂移**，跟踪对象是「当前卡哪一环」而不是某个固定指标。

3. **落 `part4` 四块**：
   **★`scenarios`（4.1，09 §5.5）**——投资结论的大白话出口，回答 ①哪几个场景让股价涨/跌 ②靠什么解锁 ③赔率怎么算、R/M/V 各贡献多少。**场景＝某条主动矛盾的解方向 × 某条从动矛盾的解方向的叉乘，`from` 必须指名两条真实矛盾 id，不许自由创作**；3–5 条且**至少一条下行**；解锁分两层——`story` 中期叙事（年级，主动矛盾的相位迁移）＋ `catalysts[]` 短期催化（季度级，从动矛盾当前绑定环的判定事件，每条带 `when`+`watch`，优先 `ref` 引用第二章催化）；给 `unlock[].status` 解锁进度，**并且必填 `prob`+`prob_basis`（★2026-08-14 改，原来写的是「不给概率」——赔率没有概率就不是赔率，是情景标价，读者合不出 EV；见 CK-6 S8 与 09 §5.5g）**。**赔率不许手写：每条场景是第三章模型的一组 `knobs` 存档**（P&L 路径 + 估值腿**按 paradigm key 寻址**；范式切换＝改 `weight`，不动估值腿结构），跑引擎得 `mcap_yi`/`odds`，**下行场景同样必填 knobs**；页面点场景名即把滑块跳过去实时重算。`rmv` 沿用 03 §2f-q 对数三因子且 Σ 对 odds 差 ≤3pp，`rmv_check` 与第二章 `factor_quant` 同尺度对照（V 超历史最强段须说明靠什么范式切换支撑）。开篇总结的主线用 `summary.main_scenario` 对上某个 `key`。
   `items[]`（8–12 条，每条 label 5–8 字 + 一句话 + 30–50 字详述 + 五层归类 + **role/subtype/clock** + F/D/赔率）、
   `narratives[]`（叙事逻辑链每步标已证实/未证实 + **最先断的一环** + `subs[]` 次级矛盾→页面单独渲子坐标系，从主图气泡超链接跳入；**每条叙事的 `subs[]` 至少 1 条来自探针**）、
   **`core` 双槽位**（`pricing` 定价核心矛盾=低可证伪区赔率最大的，动作是控仓位/画敞口；`actionable` 可操作核心矛盾=高可证伪区赔率最大且过证伪的，动作是读财报/季度跟踪）。**两条结构性地不是同一条，只给一条 CK-6 不过。**每个槽位必带 `deepdive`（09 §6b：怎么理解/市面方案/落地方案含 `blind_spot`/判定表/时点/**`analog` 历史对标**）——**对标锚查 13 §6 案例库不许现编，`diff` 必填，没有 diff 的对标是装饰不是判据**。

4. **跑闸**：`node scripts/check_part4.js --model _workspace/<ticker>/page_model.json`（64 项，退出码 0=全过）。**其中 S3 会拿你的 `knobs` 真跑一遍引擎去对 `mcap_yi`/`odds`**，对不上直接不过——场景写不实是这一章最容易出的错；**S8 会反解现价隐含上行概率并与你填的 prob 比**。
   **另跑第三章结构闸**：`node scripts/check_part3.js --model _workspace/<ticker>/page_model.json`（A 反算隐含份额 / B L兜底段进 SOTP 上限，04 §4.1/§4.2）。**两个闸是正交的**——阳光 v3.1 check_part4 58 项全过，check_part3 的 A 组五段全不过（seg_val 全押 2028E 而驱动链只到 2026）。形式闸过了不等于经济含义站得住。

> ⚠️ **进图前每个数字必须回 RAG 或 page_model 复核**——agent 输出不是信源。实测踩过：上一轮 agent 给的合同负债数与 RAG 里三家（14.88／19.15／42.03 亿）没有一个对得上。同一指标多口径不是错误是**发现**，转成口径型矛盾走 `calibers` 决策卡。

**Phase 6.5 · 开篇章「一段话说清楚」.** 读 `references/10-summary-backsolve.md`（⚡，钩子登记表在 §2，闸门表在 §7）。**位置在正文最前（概览之后、第一章之前），但必须最后写**——四章都定稿了才写得出这段话。数据键 `page_model.summary`（不编号，与「概览/参考文献」同级）；形态＝纯文字 + 编号（第一点…第四点 / `1.` / `(1)` / `①`），不加视觉件；「反算」是内部叫法不外泄。四点：
1. **第一点 公司类型 ＝ 钩子体系**：固定三块 生意本身 / 盘子 / 股性，每块 `title` 是结论句 + `points:[{hook,k,v,tag,ev}]`。**`k` 那一列是提问框架不是排版**——按 10 §2 登记表逐条回答必答钩子（块①：行业 / 主要产品 / 收入在哪一刻确认被谁挟持 / 壁垒在链条哪一步 / 单价涨的是价还是结构 / 什么情况下生意好但报表不好 / 周期还是成长；块②：市值分层 / 行业地位 / 筹码锁定 / 派系类型与公司诉求(A股) / 可交易容量与我的份额(有 1.7 时) / 含义；块③：涨停频率 / 波动特征 / 玩家结构 / 真β·假β·σ / 判定与交易含义 / 历史行情由什么驱动(主因子同一时)），选答钩子按标的挑、不许硬凑；答案九成在 page_model 里（driver_chain / calibers / driver_focus.verify / factions_ts / chip_age / narrative_capacity / basket_beta / part4.weakest），**不为钩子重跑管线**，答不上来按 10 §2.6 动线回前三章挖→RAG→AlphaPai(🔎 钩子)→标 EST/DNA 并明说把握不高。**股性那条先跑** `python3 scripts/fetch_stock_profile.py --ticker <码> --market A --years 3 --out _workspace/<码>/stock_profile.json`。**再跑** `python3 scripts/type_card.py --model _workspace/<码>/page_model.json --profile _workspace/<码>/stock_profile.json --write` 合成**概览类型卡**数字层（10 §2.8）：作者按 beta_kind 的判定填 `type`（真β/假β/σ/叙事-题材）+ 一句 `verdict`（这类票怎么拿），β 类渲核心叙事线+龙头/中军/后排+K 线方位，σ 类渲预期净利率·ROE 历史分位+PE/PS/PB 分位——渲在概览快照下方，读者第一眼就知道「拿它当什么交易」。knowhow 判据＝同行业照抄成立就重写；全章 ≥2 个 DNA、≥1 处挂 ev；**密度少而狠**：每条 v 只说一件事（FACT ≤100 字 / EST·DNA ≤150 字）、选答每块 ≤2 条、三块合计 ≤4,000 字（目标 3,000）——深度下沉到第三章，开篇只留结论+关键数字+「所以你会怎么看错」。
2. **第二点 核心投资逻辑**：`thesis` ≤30 字含机制；`pillars` 是一条链不是证据清单（10 §3）：行业盘口径 → 份额 → **自算落点**（盘×份额＝公司自己的数）→ **撞上的约束** → 互证/下钻，另加 **主叙事最先断的一环**（搬 `part4.narratives[].weakest`）与公司当下的张力。
3. **第三点 算账**：`mcap_split`（含「超出 SOTP / 多给的部分」那一行）+ `steps` 三档 driver（`stake` 数字 / `segment` 标签）+ `conclusion` + **`price_assumes`**（现价把什么当成既成事实）。
4. **第四点**（10 §5）：**利润兑现期限**（活的：`现市值 ÷ anchor_pe` → 在历史上行尾巴+预测序列上插值定位年份，`inHist`/`beyond` 页面自己说话，拖假设滑块整表即时刷新）· **估值范式上界**（`ladder` 五档 tier 排序、每档两个数字、前提未成立档必填 `mcap_if_yi`、只列够到现价的档）· **潜在催化**（`switches` 范式跃迁四格 + `prob` 数字 + 至少一条向下，升档 prob 合计对第四章上行 Case ±10pp）；`main_scenario` 对上第四章某条 Case。
5. **跑闸**：`node scripts/check_summary.js --model _workspace/<ticker>/page_model.json`（CK-7，独立于第四章；`--hooks` 看登记表）+ `node scripts/check_charts.js --model <同一份>`（CK-8）。文本版「⧉ 复制为文本版」（`summaryText()`）与页面同一契约，改契约同步改它。

**Phase 6 · 生成页面.** 读 `references/06-html-design-system.md`（改模板/图表时）。跑：
```
python scripts/build_page.py --model _workspace/<ticker>/page_model.json --out _workspace/<ticker>/onepager.html
```
自包含单文件（Chart.js+引擎+app+反馈标注层 内联）。`--endpoint <worker URL>` 烧反馈云端、`--version v3` 刷版本徽章、`--no-annot` 出无标注只读版。

**Phase 7 · 验收(CK) + 交付.** 见下方 CK 闸门。本地打开 onepager.html 自查（放项目目录内才执行 JS；**改过模板/annot.js 要加 `?v=新串` 破 file:// 缓存**）；如需云端可视/分享，走 Phase 8 反馈平台，或 Artifact 发布（只读、不收标注）。附一句话结论 + 数据缺口清单。

**Phase 8 · 上线 + 开放标注.** 读 `references/08-feedback-loop.md`（⚡）。**认知是螺旋上升的，一份静态报告搞不完**——交付即开放反馈：
```
python scripts/deploy_page.py --ticker <代码> --model _workspace/<ticker>/page_model.json \
    --endpoint https://onepager-feedback.<子域>.workers.dev        # endpoint 首次给一次即记住
```
读者在页面上**划词或点模块 ✎** 标五类疑问（❓没看懂/⚠️数据存疑/🔍要原文/💡建议补/✅认可）→ 标注锚到 **page_model 的 JSON 路径**（`data-fbk`）→ 「同步到云端」或「导出 JSON / 复制反馈摘要」。首次需按 `feedback/worker/wrangler.toml` 顶部三步建 KV+secret（一次性 3 分钟）；不想建云端就用纯本地模式（导出/复制粘回对话）。交付话术要**明确告诉用户怎么标注**（划词 → 选类型 → 同步）。

**Phase 9 · 回灌 → v_n+1（认知螺旋）.** 同读 `08`。
```
python scripts/feedback_pull.py --ticker <代码> --only-new       # 或 --from-file <页面导出的 json>
# → feedback/round_<n>.md（按模块分组 triage + 改稿清单）+ round_<n>_resolutions.json（回应骨架）
# 我按 triage 逐条改 page_model（口径类→建 calibers；要原文→补 evidence；没看懂→拆 driver_chain）
python scripts/feedback_resolve.py --ticker <代码> --round <n> --bump v<下一版> --changelog "一句话变更"
python scripts/deploy_page.py --ticker <代码> --model _workspace/<ticker>/page_model.json --version v<下一版>
```
**每条标注必须有归宿**：改了(`fixed`) / 答了(`answered`) / 明确待补(`pending`，写清等什么数据、何时回填)——`feedback_resolve.py` 有空答复闸。新版页顶自动渲「本版反馈回应」+ 被改模块打绿边，读者刷新即见。同一 `path` 反复被标 ≥2 条 = 该模块结构性讲不清，**重做 driver_chain + calibers**，不是加一句解释。

---

## 上游交接：来自行业 TAM 专项

若该标的所在行业刚做过 `industry-tam-buy-side-research` 专项，**先问用户要那份报告**，并直接引用它已算好的三样，不要重跑：**分段量价时序**、**费用层回归（固定/变动拆分）**、**行业锚参数**（如单柜 $/kW、环节毛利率）。

对齐三件事再开工：①分段口径（只取归属该行业的那一段，不是全公司收入）；②单价口径（全链条售价 vs 部件单价，单位写死）；③行业锚与公司值的偏离原因（例：公司 ¥2,600/kW 低于行业 ¥3,080/kW，因境内占比高，不是模型错）。

TAM 报告里标出的**最大单点假设**（如液冷占分部收入比例）在本页必须做成**可调滑块**，不得写死。
反向禁令：本页的单公司数据**不可**用来反推行业 TAM。契约全文见 `industry-tam-buy-side-research/references/handoff-to-equity-onepager.md`。

---

## 数据路由（A股优先·港美股尽力）
| 数据集 | 主源 | 备源 |
|---|---|---|
| 分部收入+YoY | iFind `fin`(分产品/行业/地区各调一次) | Comein `get_main_business_segments` / AKShare `stock_zygc_em` |
| 历史十大股东 | iFind `holders` | Comein `shareholder_details` / qcc `get_shareholder_info` |
| 子公司(持股/主业/区位) | **qcc** `get_external_investments`+`get_branches`+`get_company_profile` | 年报「主要控股参股公司」via iFind `notice` / AlphaPai |
| 10yr ROE+杜邦 | iFind `fin` | Comein `get_financial_snapshot` / AKShare |
| 成本/费率 | iFind `fin` | 成本明细(料工费)→Comein 年报附注/AlphaPai |
| 周线股价(真OHLC) | **`scripts/fetch_kline.py`**(AKShare 东财qfq日频→周聚合,内置校验) | 腾讯 ifzq.gtimg.cn qfq周K(脚本自动切换) / iFind `performance` / Yahoo(港美) |
| 一致预期/业务定性 | AlphaPai(标【Estimate】) | Comein 纪要原话 |
| **一致预期分布(箱线图)** | **`scripts/fetch_fmp_consensus.py`**(FMP `analyst-estimates`：逐期 Low/Avg/High + 覆盖家数，**A股`.SS/.SZ`+港股`.HK`+美股全覆盖**，实测 300750 年度 24-29 家) | 港股 etnet 逐家机构(`fetch_fundamentals_hkus.py` 的 `consensus`，**有逐家数据才画得出真四分位箱**) / AlphaPai |
| **beat/miss 兑现记录** | **`scripts/fetch_fmp_consensus.py`**(FMP `earnings`：逐期 epsActual vs epsEstimated；`--kline` 叠财报后1周/4周股价反应) | iFind `fin` 实际值 + 卖方预期手工比对 |
| **★时点一致预期(Forward PE带)** | **`scripts/fetch_fwd_pe.py`**(东财 `reportapi` 逐份研报的**相对年** predictThisYear/NextYear/NextTwoYearEps＋publishDate→逐周重建；**仅A股**；⚠️勿用 akshare 研报接口,相对年字段被错标成固定年份列) | 页面 fallback=FMP 财年快照近似(有前视,红字标注) / 港美股待接 FMP `price-target` |

### 港美股专用路由（2026-08-02 实测，锚：AAPL / 00700）
**入口一律 `scripts/fetch_fundamentals_hkus.py`**；iFind `fin/holders` 对港美股返回「查询结果为空」**且不报错**，已被 `fetch_ifind.py` 的市场闸拦截。

| 数据集 | 美股 | 港股 |
|---|---|---|
| 周线 OHLC | ✅ akshare sina `stock_us_daily` | ✅ 东财挂→腾讯 `hk00700` qfq 周K 自动接管（实测走的备援） |
| 三表 | ✅ 东财 `stock_financial_us_report_em`（**2000 年起 26 期**） | ✅ 东财 `stock_financial_hk_report_em`（**2001 年起 25 期**） |
| 杜邦 | ✅ `..._us_analysis_indicator_em` 直给 `TOTAL_ASSETS_TR`，四项齐 | ⚠️ 仅 9 期(2017起)且不给周转率 → `ROA/净利率` 反推 [Inference] |
| 权益乘数 | ✅ 资产负债表 `总资产/归属于母公司股东权益` 实算 | ✅ 资产负债表 `总资产/股东权益` 实算（口径对了闭合度 0.94–1.05） |
| **分部收入** | ⚠️ **SEC EDGAR 10-K R-file**（`FilingSummary.xml`→Details 表）：实测 AAPL 拿到 product 5项/reportable 5项/region 3项。**XBRL `companyconcept` 只回合并口径无维度，别指望它** | ❌ **无结构化源** → 年报「分部资料」附注 PDF / AlphaPai 纪要人工抄 |
| 费率 | ⚠️ SG&A 多合并披露（AAPL『营销费用』6.63%＝Selling+G&A 合计）→ 页面渲**一条 SG&A**，不套 A 股销售/管理二分；财务费用常缺 | ✅ 销售及分销/行政开支可拆；❌ 研发多并入行政开支不单列 |
| 收入口径 | `主营收入` | ⚠️ `营业额`(主营) vs `营运收入`(含其他营业收入) 两行并存，caliber 必须写明 |
| 市值/股本 | ⚠️ `stock_us_spot_em` 实测连挂 → 走 现价×加权股数(损益表直给) | ⚠️ `scale_cmp.总市值` 与 收盘×股本 对不上、`营业总收入` 疑似单季 → 只当参考 |
| 估值倍数 | 自算 PE（现价×股数/归母） | ✅ `stock_hk_valuation_comparison_em` PE-TTM/PB/PS/PCF+行业排名；⚠️ 亿牛 PE 历史实测**停更在 2022**，不能算「当前历史分位」 |
| 一致预期 | ❌ akshare 无 → AlphaPai `roadShow_us` / 卖方 | ✅✅ etnet **逐家机构**纯利/EPS/目标价/评级/日期（腾讯 19 家）+ 脚本自动算 `dispersion` → 直供第四章 |
| 十大股东/派系 | ❌ 结构性无（13F 滞后45天口径不同） | ❌ 结构性无（CCASS/披露易无零鉴权 API） |
| 子公司股权树 | ❌ qcc 不解析境外主体 | ❌ 同左（有大陆运营主体可查那一层，注明只是局部） |
| 纪要/RAG 取证 | ✅ AlphaPai `roadShow_us` | ✅ AlphaPai `roadShow`（明确含港股） |

---

## page_model.json 契约（build_page.py 的输入 / app.js 的消费对象）
> 完整字段与图表映射见 `references/06-html-design-system.md`；此处为骨架。所有金额单位=亿元；比率：营收占比/毛利率等用「百分数值」(如 23.9 表 23.9%)，**但 part3.segments.assume.gm 与 part3.opex.*_rate/tax_rate 用小数**(0.24)。
```jsonc
{
 "meta":{name,ticker,market,asof,currency,unit,current_mcap_yi,current_price,shares_yi,pe_ttm,positioning,note,note_cite:[n],
   version:"v1",updated:"YYYY-MM-DD",changelog,                  // ★认知螺旋轮次(渲成标题旁 .ver-chip);build_page 缺省补 v1
   currency_reported,fx,fx_asof,fx_note},                        // ★港美股必填(2026-08-02):财报币种/汇率/汇率日期/换算说明
                                                                 //   currency=页面展示币种; currency_reported=财报币种(可不同,如腾讯报RMB交易HKD)
                                                                 //   所有 *_yi 必须是**同一币种**;混币会让赔率整体错一个汇率(见 fetch_fundamentals_hkus.py 的 meta.currency_check)
 "part1":{
   "snapshot":{latest_q:{period,rev[亿],rev_yoy[小数],rev_qoq[小数],np[亿],np_yoy[小数],np_qoq[小数],gm[小数],nm[小数]},ttm:{rev[亿],np[亿],rev_yoy[小数]},note,cite:[n]},  // 最新财务快照(单季+TTM年化),渲在概览
   "revenue":{years:[],caliber,segments:[{name,values:[亿]}],total:[],yoy:[%],customers:[],business_tags:[],
      milestones:[{year,cust:["客户里程碑"],biz:["业务里程碑"]}],  // ★年份对齐标注(红客户/蓝业务),渲在营收图下
      events:[{year,label}],cite:[n]},
   "shareholders":{periods:[],concentration:[前十大合计%],top:[{period,holders:[{name,pct%,shares_yi,nature}]}],
      factions_ts:{periods:["YYYYQn"],series:[{faction,color,values:[百分数,每期]}]}, faction_analysis, faction_cite:[n], cite:[n],  // ★派系近5年逐季堆积(时间横向比较)+一行定价权结论(不再出派系明细卡)
      pre_ipo:{rounds:[{date,round,investors:[],post_val_yi,founder_pct,note}],   // ★上市前融资史(2026-08-12,见02 §1.2b):轮次时间线(招股书资本沿革=FACT)
        ipo_founder_pct,pe_ipo_pct,pe_now_pct,                   //   IPO时创始人/PE合计 vs 当前→页面渲PE退出进度条
        archetype:'founder'|'pe_diluted'|'soe'|'dispersed',archetype_note,cite:[n]}},  // 派系类型判定(产业坐庄/PE退出/国资/无实控人),渲堆积图上方
   "ownership":{controllers:[{name,role,pct[百分数]}],platform:{name,pct},direct:[{name,pct}],float_pct,   // ★股权结构树(实控人→平台→上市公司→子公司)
      sub_groups:[{group,color,note,subs:[{name,stake[百分数],business,location}]}]},  // 子公司按业务分组(非核心/核心零部件/软件…)
   "dupont":{years:[],roe:[%],net_margin:[%],asset_turnover:[次],equity_multiplier:[倍],cite:[n]},
   "cost_structure_q":{                                           // ★1.4 逐季毛利率分解（02 §1.4）；整份由 scripts/fetch_quarterly.py 产出
      quarters:['2020Q1',…],listing_year:2020,                    // ★上市首季起；listing_year 必填，CK-8 d4/d4b 核对
      gross_margin:[%],                                           // ＝堆积**面积上沿**，不单画成层
      net_margin:[%],                                             // ＝最底层
      sell_exp_rate:[%],admin_exp_rate:[%],rnd_exp_rate:[%],fin_exp_rate:[%],
      tax_rate:[%],                                               // ★税金及附加＋所得税费用，**占营收**，不是实际税率
      rev_yi:[亿],src:'iFind 单季度.* 原生指标（非累计差分）',        // src 里必须有「单季度」，CK-8 d5 查它
      caliber,cite:[n]},                                          // 「其他」＝页面反算 gm−(净利率+四费+税费)，不落数据层
   "cash_capex":{                                                 // ★1.4b 逐季；同一脚本产出，不手改数
      quarters:['2020Q1',…],ocf:[亿],np:[亿],capex:[亿],            // 单季，iFind 单季度.* 原生；**没有单季 da**（报表上不存在）
      ttm:{quarters,ocf,np,capex,da:[亿|null]},                    // ★TTM 的 da **只在 Q2/Q4 有值**，由披露累计数精确凑出
      da_disclosure:[{period:'2025H1',yi,covers:[…],src}],         // 折旧的原始披露段（未摊平），图注直接印
      unit:'亿元',caliber,da_note,src,gaps:[],cite:[n]},            // 无 quarters → 整节隐藏+摘目录链
   "consensus":{                                                  // ★1.5 一致预期分布+兑现记录；**整份由 scripts/fetch_fmp_consensus.py 产出，直接塞进来，不要手改数**
      asof,src,reported_currency,page_currency,currency_warn,     // currency_warn 非空→页面渲红条(腾讯报CNY交易HKD这类)
      box_caliber,                                                // ★口径声明(全距≠四分位)，页面必渲，删了 CK-1.5 不过
      quarters:[{date,label:'26Q3',is_future,coverage:'ok'|'thin'|'none',suspect,   // suspect=FMP远端脏数据(收入涨EPS跌)，页面标⚠
         rev:{lo,avg,hi,n,coverage,spread},np:{…},ebitda:{…},eps:{…}}],            // 金额=亿(**原报告币种**)；eps=每股原值；spread=全距/均值→第四章 D 直接用
      years:[{…同上,label:'FY2026'…}],                            // **年度口径才与第三章模型可比**(模型年频)→页面画 ◆
      surprises:[{date,label,eps_act,eps_est,eps_surp[%],rev_act[亿],rev_est[亿],rev_surp[%],
         verdict:'beat'|'miss'|'inline',px_1w[%],px_4w[%],        // px_* 需 --kline；缺则不叠，不许估
         divergence:'beat_but_down'|'miss_but_up'}],              // ★利好不涨/利空不跌 → 回查第二章该阶段主要矛盾
      surprises_forward:[{…actual 尚未披露的期…}],
      surprise_stats:{n,beat,miss,inline,beat_rate[%],avg_surp,median_surp,streak,streak_dir,inline_band_pct},
      targets:{high,low,consensus,median},                        // FMP 仅美股有；A/港股实测为 null，页面自动省略
      grades:{strongBuy,buy,hold,sell,strongSell,consensus},grades_hist:[{date,sb,b,h,s,ss}],
      quarters:[{…}],years:[{…}],                                 // 每个 band 另有 synthetic(FMP合成区间)/degenerate(宽度<1%)/hist_disabled(EPS)
      stats:{annual:{rev,np,eps},quarter:{…}},                    // 每个含 beat_rate/in_range_rate/vs_pre{n,avg,median}/vs_avg{…}/
                                                                  //   avg_range_pos(**仅区间内样本**)/n_above_hi/n_below_lo/synthetic_excluded/degenerate_excluded
      gaps:[]},                                                   // 缺口清单，Phase7 交付时随页面一起交
   "chip_age":{                                                   // ★1.6 历史码龄；整份由 scripts/fetch_chip_age.py 产出
      asof,window:[起,止],n_days,src,model,caliber,ifind_check:{ok,note},
      basis:'free_float'|'total_float',basis_note,                // ★给了 --locked-pct 才是 free_float；否则长码严重低估
      free_float_ratio,locked_pct,                                // 锁仓块单列，不并进序列（并进去会把长码压成平线、抹掉信号）
      current:{d,close,short,mid,long,resid,avg_age,avg_cost,profit_pct,buckets:[{label,from_days,to_days,pct}]},
      extremes:{long_min:{d,pct,close},long_max:{…}},             // 长码占比极值→常对应底部/顶部区域
      series:[{d,close,short,mid,long,resid,avg_age,avg_cost,profit_pct}],   // 短+中+长 恒=100%
      gaps:[]}
 },
 "part2":{window,weekly:[{d,o,h,l,c,v}],
   earnings:[{date,period,type:'业绩预告'|'一季报'|'中报'|'三季报'|'年报',short:'预'|'Q1'|'H1'|'Q3'|'年'}],earnings_note,  // ★2.1 图底披露日节点(scripts/fetch_earnings.py 拉真实公告日;虚线对齐K线+chip,与顶部催化▲不遮挡)
                                                              // 为什么要全量标：催化清单只收「涨跌显著」的财报，而**利好不涨本身是信号**(002371 阶段①业绩连超预期而股价−31%)                        // ★K线OHLC 必须齐(fetch_kline.py 真数据);c-only 页面打红警示+CK-2不过;MA5/10/20/60由closes自动算;涨红跌绿
   phases:[{name,period,from,to,chg,color,startIdx,endIdx,narrative,main_factor,sub_factor,anchor,
            core_conflict,logic,                                 // ★主要矛盾+分析逻辑(横向列必填)
            factor_quant:{r_pp,m_pp,v_pp,basis},                 // ★2026-08-12 每段必填:涨幅量化分解到R/M/V(百分点,对数三因子,03 §2f-q);全阶段同尺度渲条,跨列可比
            factor_signature:"基本面对、标签错",                  // ★2026-08-14 每段必填:≤20字形态判定(03 §2f-s)。main_factor 单选会把结论压没——阳光六段全是V
            basket_beta:{stock_chg,rows:[{kind,name,born,chg,chg_w,excess}],   // ★由 onepager_module.py 写入,不手改(14 §7b)
                         dropped:[{name,born,chg_if_forced,why}],              //   概念诞生日晚于阶段起点→硬闸剔除,只交代不给数
                         bench:[{kind,name,code,chg,excess,error}],usable,note},//   同期锚:申万二级行业+沪深300
            accounting:{headline,steps:[],pe_tiers}}],           // 2.2 阶段分解=横向列(左→右对齐K线,宽∝startIdx→endIdx)
   valuations:[{label,color,cap,pe,body,consensus}],             // 与phases同序;算账并入2.2每列; body=StepA分部毛利→StepB合计对财报→StepC费用桥→归母→PE档→隐含/Forward→ΔPE; source[F]财报/[E]测算/[R]研报/[N]纪要
   catalysts:[{id,date,snapIdx,price,weekChg,name,codes:[G1..G5],code:R/M/V,driver,rationale,summary,   // codes=五大催化剂(数据键G码,页面展示原始类型名不露代号;负面/流动性节点codes:[]); rationale=★原始材料逻辑推演(原文→推论,带信源,只渲2.3清单↳行)
            links:[{label,url}],                                 // ★浮窗/清单「原始材料」超链接(0-3条,2026-08-12;浮窗不出原文只给链接)
            dims:{"1.1":"✓..","3.1":"—",...9维},lead}],         // ★标记=悬停浮窗(9维默认展开,点击钉住);形状=R/M/V主因子(●▲★),颜色=五大催化剂,#n=该类型第n次出现
   fwd_pe:{enabled,note,series:[{d,pe,pe1,ntm_eps,ps,pb,pe_gap,n,thin,basis}],caliber,src,loss_metric:'ps'|'pb',reports_n,orgs_n,weeks_covered,weeks_substituted,report_points:[],  // ★2.1b(2026-08-12):A股由 fetch_fwd_pe.py 整份产出=逐份券商研报重建的时点一致预期(NTM);负利润/无覆盖周切 trailing PS/PB 替代线(左轴,全窗口连续);缺series页面退回FMP财年近似并红字标注
     anchors:[{date,pe|mcap_yi+profit_yi,label,src,url}]},        //   ◆卖方锚点手工RAG取证,合并进同一对象勿覆盖series
   conclusions:[],cite:[n]},
 "part3":{archetype,note,shares_yi,hist_years:[],forecast_years:[],
   hist_actual:{rev:[],gross_margin:[小数],sga_rate:[小数],rnd_rate:[小数],ebit:[],da:[],ebitda:[],net_profit:[]},
   narrative_map:{note,cite:[n],eras:[{era,name,status,impacts:[{seg:key,param,timing,strength:1-3,how}]}]},  // ★叙事↔分部映射(3.2节,见04 §1.16):旧/现叙事作用在哪些分部/参数/时点/强度;有则后续编号顺延
   segments:[{key,name,hist:{q:[],p:[],rev:[],gm:[小数]},assume:{q_growth:[小数],p_growth:[小数],gm:[小数]},
      model:{q_def,p_def,q_unit,p_unit,logic(可信HTML),assets_note,q_ev:['E1'],p_ev:[],   // ★细分建模卡→页面 3.3.x 孙级小节(2026-08-12编号改制:3.3=分部建模与计算总节,分部=3.3.1..3.3.N;无narrative_map时3.2.x;假设/估值固定3.4/3.5;字号 14.5px,见06 §2.2)
             q_anchors:[{label,v小数}],p_anchors:[],gm_anchors:[],             // ★类比锚:锚线进分部量价图+假设滑块▲刻度(历史3yCAGR自动算)
             driver_chain:[{step,expr,val,tag,ev:['E2'],note,out}],            // ★驱动链:外部物理量→本段收入逐步算账(core段必填;末步 out:true;04 §1.17)
             calibers:{subject,unit,chosen_label,why,cost_if_wrong,spread,ev,rows:[{caliber,raw,norm,conv,src,date,ev,status:'chosen'|'ref'|'rejected',v,v_lo,v_hi,short}]},  // ★口径取舍决策卡(①哪个数→②刻度条画出差几倍→③用哪个·为什么·用错代价→④候选明细);v/short供刻度条,差<1.5倍改渲互证一行;有口径分歧必填,可写数组=多参数多卡
             evidence:[{id:'E1',doc_id,page,date,type,src,confidence,quote(逐字原文),implication(我的推论),used_in}],  // ★RAG原句卡(core段必填);各处 ev 按 id 引用→[E1]可点角标+一键取原文命令
             driver_focus:{strength:'core'|'support'|'weak',targets:[{param:'q'|'p'|'gm'|'rev',years:[]}],note,verify,ev},  // ★当下逻辑最强段(全模型唯一core)+作用参数×时点;次级模型表命中格黄底高亮;note只写机制,跟踪项写verify(只渲段末小结,不重复)
             fragile,                                                          // ★最脆的一格(这段最先被打破的地方)→渲段末小结红字
             seg_val:{method,profit_yi,mult,mcap_yi,note},                     // ★分部估值(与SOTP行对齐)
             anchor_check:{year,tam:{v,unit,basis,tag,ev},implied_share_pct,ref_share_pct,ref_basis,
                           verdict:'扩张|持平|收缩',why,cost_if_wrong,share_gain_from},  // ★2026-08-14 seg_val 锚年超出 driver_chain 覆盖时必填(04 §4.1);check_part3.js A 组会自己递推 q 对表
             cite:[n]}}],
   opex:{sga_rate:[小数]|标量,rnd_rate,tax_rate,da:[亿],net_interest:[亿]},
   valuation:{current_mcap_yi,shares_yi,net_cash_yi,paradigms:[{key,name,weight,params:{...}}]}},
 "part4":{note,asof,                                              // ★第四章 矛盾地图(09)：前三章给"是什么"，本章给"下一步盯什么"
   items:[{id,label(5-8字·画在圈边),one_liner(浮窗首行),detail(30-50字·必带数字),
      layer:'叙事'|'估值'|'收入'|'利润率'|'费用率',                  // → 决定圆颜色；P&L三层必填 hooked
      hooked:"segments[0].assume.q_growth",                       // 挂到哪个可调参数；挂不上的只能归叙事/估值
      F(可证伪性0-100),D(分歧度0-100=各家口径方差),odds(赔率%现市值),
      dir:'up'|'down', coverage(覆盖家数;0→虚线圈),
      dispersion_basis,                                           // ★必填:谁给了什么数+极差+形态(双峰/单峰宽/零覆盖)
      odds_basis,                                                 // ★必填:tornado bar(按传导率修正为上界)/取期敞口/手算
      verify, ev:[{quote(逐字),src(机构+日期),doc_id}], narrative}],  // narrative→4.1气泡超链接跳4.2子坐标系
   narratives:[{key,name,
      chain:[{step,claim(带数字),status:'已证实'|'部分证实'|'未证实'|'已证伪',ev}],  // 外部驱动→公司收入的逐环推演
      weakest,                                                    // ★整条链最先断的一环+为什么(红字)
      subs:[{…同 items…}]}],                                      // 次级矛盾→页面单独渲子坐标系
   core:{pricing:{id,why,action},actionable:{id,why,action}}},    // ★双槽位:定价核心矛盾 vs 可操作核心矛盾,必须两条且不同条
 "summary":{note,asof,cite,                                       // ★开篇章「一段话说清楚」(references/10)；渲在正文最前、不编号；缺键=整章自动隐藏
   company_type:[{label,note}],                                   // 3-5条,每条要有**估值含义**(非形容词)
   thesis,                                                        // 一句话≤30字且**含机制**
   pillars:[{key:'demand'|'supply'|'company'|'risk',name,
      points:[{claim(带数字),tag:FACT|EST|DNA,ev:['E1'],subs:[]}],subs:[{name,points:[]}]}],
   accounting:{mcap_split:[{part,yi,basis}],                      // 当前市值拆成几块各对应什么
      steps:[{name,note,scenarios:[{name:'乐观|中性|悲观',driver(怎么算出来的),profit_yi,
        stake(★持股比例·数字,不是分段标签),segment(★这一步算哪一段,字符串),attrib_yi}]}],  // attrib_yi 缺省则 profit_yi×stake
      conclusion},                                                // 远期利润体量→市值空间
   backsolve:{anchor_pe,anchor_pe_basis,r,base_year,note,
      profits:[{year,np_yi}],                                     // 仅无第三章模型时手填;有模型走模型(随滑块活)
      ladder:[{key,tier:1-5,name,precond,status:'成立'|'待验'|'不成立',current,
               mcap_yi,mcap_if_yi,if_basis,gap,note}],            // ★前提未成立的档必填 mcap_if_yi,否则低估空间;tier=五档估值等级(05 §0.5),排序第一档→第五档
      switches:[{from,to,prob,catalyst,watch,when,elasticity,kill}]}},  // ★至少一条向下
 "references":[{n,text,tag:FACT|EST|DNA}],
 "feedback":{report_id,endpoint,autosync,rag_ws,                  // ★反馈闭环(08):report_id 跨版本不变→标注跨轮累积;endpoint 空=纯本地
   resolved:[{id,path,sec_title,on_ver,reader,ask,answer,action:'fixed'|'answered'}],  // 本版已改(打绿边)/已答复 → 渲页顶「本版反馈回应」
   open:[{id,path,sec_title,on_ver,ask,why_pending}]}             // 待补数据(诚实留白,标黄)
}
```
估值 params 关键字段（`references/05` 详）：pe`{link,year_offset,pe,r,n}` peg`{link,g,peg}` sotp`{segments:[{name,profit_yi,mult}],net_cash_yi}` leader`{leader_name★必填,basis:'revenue'默认,leader_current,leader_mcap,follower_steady,adj,r,n}` evebitda`{link,mult,net_debt_yi}` endgame`{tam_yi,share,net_margin,pe,r,n}` pbroe`{roe,coe,equity_yi}` implied`{pe_mid,net_margin}`。

---

## CK 闸门（交付前逐条过）
- **CK-RAG** Phase0.0 已问「有无前置资料」；已建 `workspaces/<ticker>/`（--zip 或 --sweep）且 doctor 过闸，或用户明确声明无料（页面标降级）。Part2 算账/催化 与 Part3 假设/估值 至少各有若干条带 `[doc_id]` 的 RAG 引用（有库时）。
- **CK-0** ticker+市场解析；A股必有 iFind；历史≥5yr（可行则拉到上市首年）。**港美股**：必有 `fundamentals.json`（`fetch_fundamentals_hkus.py` 产出），且 `meta.currency`/`fx`/`fx_asof` 已填、`meta.currency_check.verdict` 为 OK 或**已在页面写明口径结论**——带 ⚠️ 的 `mcap_yi` 不得进估值范式。
- **CK-1** Part1 数据集到手；分部标签已跨年归一；**★4 个必出模块**：最新财务快照(单季+TTM) · 营收图下按年份对齐的业务/客户里程碑 · **股东派系近5年逐季堆积图**+一行定价权结论 · 股权结构树(实控人→平台→上市公司→分类子公司)；**★1.2 上市前融资史（2026-08-12）**：`shareholders.pre_ipo` 已填（轮次=招股书资本沿革 FACT + archetype 判定带数字 + pe_diluted 型给退出进度）或页面显式声明「未收录」——不许静默省略、不许传闻凑数；缺口写 `⚠️未查到`（**不编造**）。
  **★1.4 逐季毛利率分解（2026-08-18 用户定稿，02 §1.4）**：走 `part1.cost_structure_q`，图＝**堆积面积图**（非柱状）——
  **七层：净利率 ＋ 四费 ＋ 税费 ＋ 其他**（「其他」是一个桶，装完剩下的全部），**面积上沿＝毛利率，毛利率不单画成层**；
  横轴**逐季、上市首季起**且 `listing_year` 已填；纵轴按最近 8 季稳健截断且图注**点名被截季度**；
  图注必须写「税费＝税金及附加＋所得税费用，占营收，不是实际税率」。
  **★1.4b（新增）**：`part1.cash_capex` 由 `fetch_quarterly.py` **整份写入**；同量纲共用一根左轴；
  **折旧摊销不许被摊平**——单季数组无 `da`、TTM 的 `da` 只在 Q2/Q4、`da_disclosure` 落原始披露段；默认 TTM 视图；三格读数在；无数据整节隐藏。
  **★港美股降级条款（2026-08-02）**：「派系逐季堆积图」与「股权结构树」两格在港美股**结构性不存在**（无 A 股口径的逐季十大流通股东；qcc 不解析境外主体），不作为不过闸理由，但必须**显式降级而非静默省略**——该格改渲可得的替代物（美股 13F 机构持仓 / 港股披露易主要股东；拿不到就留空位）并在图上打「数据受限：<原因>」标注，同时 `fundamentals.json` 的 `gaps[]` 每条在页面或交付话术里都有归宿。港股分部收入缺失时，Part1 营收图只出总额+YoY 并标注，**但 CK-3 的「Σ分部=总收入」不放行**——分部是 Part3 建模地基，只能人工从年报附注补齐后再往下走。
- **CK-1.6 筹码龄结构（Phase1.6，见 12）** **a** `part1.chip_age` 由 `fetch_chip_age.py` 整份塞入；**b** 四档合计 =100%±0.6pp；**c** 档位为 **2/10/100**、同花顺均龄中点 1/6/55/365（改模型后 `--calibrate 002138` 必须重跑，对表锚 31.75）；**d** **结构层齐**——长钱均龄与中短均龄都出（只给占比不过闸）；**e** p720 筹码温度计已出；**f** 长线两条流量（老化流入 a₁₀₀ / 换手流出 h·L）已出且归因图做过平滑；**g** 「只看均龄」为**三轴对数**；**h** 配色遵守「红绿留给 K 线、均龄暖色、占比冷色」；**i** 方法论在折叠块内、**不占正文**；**j** 折叠块内保留 λ=1 不可识别性与「水平值不可跨股比、只信方向」的声明；**k** 取数腿全挂时整节不出，不用估算冒充。
- **CK-1.7 可交易容量（Phase1.7，见 14 §8）** **a** `part1.narrative_capacity` 由 `onepager_module.py` **整份写入**（不手改数）；**b** 每条篮子**三量齐全**——自由流通容量、换手强度＋三年分位、本股排名＋占比，**缺一不进页面**；**c** 伞形篮子（成分 >500）已剔除或标注，`n_declared` 与实际成分数对得上；**d** 分位行标明篮子口径（自由流通前 60 只）与容量行不同源，且成分权重回溯套用的**幸存者偏差**已在图注写明；**e** `coverage<60%` 的篮子输出「数据不可得」，不给分位数字；**f** 叙事与题材至少各一条，两者都没有时整节隐藏、不留空图；**g** `part2.phases[].basket_beta` 与 `phases` 同序、篮子**已剔除本股**、`note` 保留口径说明；**h** 正文不许把「容量大」写成「空间大」，不许只摆容量数字不给份额与换手强度；**★i 概念诞生日硬闸（2026-08-14，14 §7b-0）**——`rows[]` **逐条**满足 `born ≤ 阶段起点`，晚于起点或建链日不可核的一律落 `dropped[]` 只交代不给数（阳光实测：阶段①② 11 条全部事后定义，阶段④ 那句「AI 电力四条篮子超额 −46.4pp」四条当时一条都不存在）；`usable=false` 的阶段**整块不渲**且 `phases[].logic` 里不得出现任何篮子数字；**★j 同期锚已挂（14 §7b-1）**——`--bench` 传申万二级行业名（`python3 bench_index.py --list <词>` 查名，别猜），`bench[]` 每段至少一条 `chg` 非空、拿不到出 `error` 不出数，行业锚与概念篮子**分两组渲不混表**；**★l 龙头/中军/后排 + K 线方位（2026-08-14 用户要求，14 §7a-2，`tiering.py`）**——`peers[]` 逐只带 `tier`+`tier_basis`+`posture`+`posture_why`。**龙头＝窗口累计超额前 20% 且 β≥1 且超额为正**（「超额为正」不能省：整条线都跌时前 20% 分位仍是负的，那种情况下**「这条线没有龙头」本身就是结论**）；中军＝自由流通前 1/3 且非龙头；其余后排。**不许拿自由流通市值排名当龙头**——那是规模属性（阳光在 8 条 AI 电力篮子里市值全排第 1、页面原来全标龙头，而按超额它每条都是中军；英伟达电源方案那条龙头 +88%~+104%、阳光 −18%，「钱去了别人那儿」是篮子超额 −46.6pp 给不出来的）。展示名单按层挑（龙头/中军/后排各 ≤4/4/3），不按市值前 N 挑，本股强制进。**方位口径照抄 `kline-reviewer` skill**（`moving-averages.md` 的多头/空头/粘合<3%/发散>20%或P90 + `state-judgment.md` 的周线×日线 9 态矩阵），另加 6 个 modifier 承载「短端有序但被长端压着」（→ 底部反抽·未站上季线 / 主升中回调·季线未破），并进「混乱」就把话说没了。**两件事都只吃 `.klinecache` 已有日线，零额外请求**；**★k 补锚后回头改过 `logic`**——`bench` 与 `rows` 符号相反或量级差 >2 倍的阶段，`logic` 必须同时摆两个数并说清取哪个（阳光阶段⑥：污染篮子读「叙事有效但这只票没被选中」，光伏设备 −26.7% 读「行业整体在跌、本股额外多跌 15pp」，仓位含义完全不同）。
- **CK-1.5 券商预期区间 · 兑现记录（Phase1.5，见 11）** **a** `part1.consensus` 由 `fetch_fmp_consensus.py` **整份**塞入（不手改数），`asof` 是本轮取数日；**b** **柱=实际披露值、竖线=券商预测区间**（不是箱线图，也不许叫箱线图——FMP 只给 Low/Avg/High，无任何分位数字段、无逐家明细，画不出箱体；剔除合成区间后季度覆盖常只有 2–8 家，n<5 算四分位无统计意义）。折叠块内必须写明这条及原因；**b2 ★合成区间已探测并画灰**（`synthetic` 期排除出全部兑现统计，页面标「合成区间」；统计条写明剔除期数）——FMP 回填的固定比例假区间若混进统计，结论会整个反过来；**b3 EPS 已披露期不画实际值、不进统计**（预期与实际分母不同源），页面给出下线原因而非静默空白，未来期 EPS 区间保留；**c** `coverage!=='ok'` 的期页面为**虚线箱 + `⚠ n=`**，且这些期**不得**被引用进第三章假设或第四章 D；**d** 传了 `--page-currency` 且 `currency_warn` 非空时页面已渲红条（腾讯 0700.HK 报 CNY 交易 HKD 是常态坑）；**e** beat/miss 图的 `inline` 判定带已写明（默认 ±2%，**不许把 +0.3% 叫 beat**）；**f** 有 `--kline` 时股价反应折线已叠加且 `divergence`（beat 不涨/miss 不跌）在统计条点名——**这几期必须回第二章对应阶段核对主要矛盾**，只画不解释不算过；**g** `suspect` 标记的期（FMP 远端「收入涨 EPS 跌」脏数据）页面打 ⚠️ 且**不进 forward PE**；**h** 无数据时整节自动隐藏，**不得留空图或编造分布**。
- **CK-2** 周线≥~120 周 **真实 OHLC→K线+MA5/10/20/60**（非折线；**必须出自 `fetch_kline.py` 且过其内置校验**——h≥max(o,c)、l≤min(o,c)、非 c-only；页面无「OHLC 不完整」红警示）；阶段 3–6 渲成**横向面板**（每列 主要矛盾+分析逻辑+**★factor_quant R/M/V 量化分解条(同尺度,Σ对段涨幅差≤3pp)**+**★factor_signature 形态判定**+**篮子/行业对照条**+估值算账 Step A/B/C→PE→隐含→ΔPE，左→右对齐 K线）；**★factor_signature（2026-08-14 阳光固化，03 §2f-s）**：`main_factor` 取 |pp| 最大者、而 PE 波动天然压倒 R/M，阳光**六段 main_factor 全是 V**、判别力等于零（阶段② R+75/M+61/V−173 被压成一个「V」，「基本面对、标签错」这个真结论只活在文字里）；所以每段再填一句 ≤20 字形态（基本面对标签错 / 换尺子不换数字 / 三因子同负 / 量升利跌 / 双击双杀），且**≥4/6 段同一 main_factor 时这件事本身就是结论**，必须写进开篇「核心投资逻辑」（阳光 6/6 是 V → 第三章量价小数点对解释股价的边际贡献很低，真正决定赔率的是第四章 PARADIGM 那条从动矛盾）；催化 15–25 均标 **G1-G5 五大催化剂**+R/M/V；**★标记语义（2026-08-12）**：形状=主因子●▲★、颜色=五大催化剂原色、#n=该类型第 n 次出现；**悬停出浮窗且 9 维默认展开、原始材料走 `links[]` 超链接不出原文、点击可钉住**；**★2.1b Forward PE 带**：A 股必须出自 `fetch_fwd_pe.py`（时点一致预期 series，图注无「近似口径」红字；覆盖薄段虚线+悬浮家数）；**负利润/无覆盖周有 PS/PB 替代线（左轴）**，PE 段+替代段合计=全窗口连续、两段零重叠；◆卖方锚全带 src；港美股允许 FMP 近似但红字标注必须在；数据全无整块隐藏，不许锚点插值冒充曲线；**★2.3 清单默认收起**（`<details>`）；**图底标出全部披露日节点**（`fetch_earnings.py` 拉真实公告日→`part2.earnings`；催化清单只收涨跌显著的财报，而**利好不涨本身是信号**，所以没动的那几次也必须看得见；⚠️**未经核验的字段不得上图**——本轮净利润同比因取数配对错位一年已剥离，只标日期）；**每条催化带 `rationale` 原始材料逻辑推演**（原文→推论,带信源,材料可信度分层,渲 2.3 清单↳行）且页面**只显原始类型名不露 G 代号**。
- **CK-3** P&L 自洽（量×价对分部收入 ±0.5%、合计毛利对财报 ±5%）；**拆分穷尽**（Σ分部=总收入，机房/物业等其他资产显式单列段）；**分业务一有真实量价拆分**（最大分部禁 L 兜底，页面无该段 ⚠️ 警示）；**分部模型章节逐段渲出**（建模方法+**次级模型表**(量/价/收入/毛利率×YoY,年为列,随滑块联动)+量价锚图+分部估值，无 datagap）；**driver_focus 全模型唯一 `core` 段**（★徽章+TOC★+命中格黄底,作用参数×时点标清）；**★阅读动线**（04 §1.17e）：每分部渲出「阅读顺序」条 + 连续编号步骤（1..6）+ 段末小结（含活数字 `data-segsum-*`、`verify`、`fragile`、→下一段），章级 `#p3-path` 出「本章怎么读…加权估值=终点」；**原句只在浮层**（正文无 inline 原句卡，`.ev-card` 计数=0）；同一跟踪句不在 note 与小结重复。**★Driver 三件套（04 §1.17）**：core 段有 `driver_chain`（逐步算账,每步带 val,关键步挂 ev）+ `evidence`（逐字 quote + 推论分层,doc_id 真实可 get）；凡同一参数有 ≥2 个口径的数 → 有 `calibers` **决策卡**（刻度条+结论先给+候选明细，`.cal-box table` 计数必须=0）且 `why`/`cost_if_wrong` 说清选择与用错的量级后果；页面上**无红色未登记 `[Ex]` 角标、无「缺 driver_chain/缺 evidence」提示**；Driver 区字号未被调回小字（`.sm-body`14.5/`.dc-step`15/`.drv-note`14px，06 §2.2）；**narrative_map 叙事↔分部映射必出**（3.2节：旧/现叙事各自作用的分部/参数/时点/强度+公司口径 gap 说明,与阶段复盘、driver_focus 三处互洽）；**1.4 利润瀑布可切换且渲出完整链**（营收→成本→毛利→四费→营业利润）；**1.4 毛利率读右轴**、费用率/净利率读左轴；**假设滑块带类比锚**（▲ 刻度+锚图例，至少 历史3yCAGR 自动锚 + 1 个外部锚/主力分部）；**扰动测试（★2026-07-22 升级）**：拖任一假设滑块/自定义 driver 参数→利润表与**估值区 DOM 数字**（加权目标/赔率/分部估值卡）必动——**读页面文本验收，非引擎返回值**；SOTP/大哥/终局三条静态腿已活链写回（04 §5.5）；min/clamp 钳制激活时页面有醒目警示（"正确地不动"必须可见原因）；**★3.1 YoY 右侧列组（2026-08-14 用户要求，04 §1.15）**：YoY 从「每行下面单开一行」搬到「每行右边一组列」——左边 N 个年份列给数值、一根竖分隔、右边 **N−1 个年份列**给同比（首年无同比，列组少一年），两组各带组标题；**比率行给 pp 不给 %**（毛利率 36.5%→28.0% 是 −8.5pp 不是 −23%，`yoyMode:'pp'`：毛利率/净利率/隐含费率/λ）；费用成本行整列为负，同比按绝对值算；**核心变化上色走 A 股口径涨红跌绿**（金额 |YoY|≥20% 上色、≥50% 加粗；比率 |Δ|≥2pp 上色、≥5pp 加粗）。⚠️**不许复用 `.pos/.neg` 或 `p.good/p.bad`**——本页 `--good` 是绿、`--bad` 是红，语义名与 A 股方向相反，照名改必反；用 `.pl-up`/`.pl-dn`/`.pl-hot`。表宽翻倍后 `#tbl-pl` 开横向滚动、序号与项目两列 sticky 粘住。**★3.1 新版式（2026-08-12）**：序号列 + TOPLINE→分部收入(1.x)→毛利汇总/分部毛利(2.x 含YoY/毛利率)→费用桥(3.x)→利润链(4.x)→归母(5) 总分结构，Σ1.x/Σ2.x 双闸门无红警；**★编号改制**：3.3(无叙事映射 3.2)=分部建模与计算总节、分部=孙级 3.3.x、假设/估值固定 3.4/3.5，TOC 三级对应；**★核心模型表不许丢**：每分部（尤其 core）次级模型表渲出且**段内 ✎ 改假设滑块可用**（与核心假设区镜像联动——在 3.3.x 段内拖杆，3.1 表与估值区 DOM 必动），注入层只许追加不许替换分部章节。
  **★★CK-3 A/B 组结构闸（2026-08-14 阳光固化，`node scripts/check_part3.js --model <page_model>`，见 04 §4.1/§4.2）**：**A 反算隐含份额**——凡 `seg_val` 锚年超出 `driver_chain` 覆盖的最远年份（阳光实测：5 段 seg_val 全押 2028E，驱动链最远只到 2026，**举证全在 T+1、估值全押 T+3**，而 58 项 check_part4 一条都没碰到），该段必须给 `model.anchor_check`：`tam{v,unit,basis}` + `implied_share_pct` + `ref_share_pct` + `verdict`(扩张/持平/收缩) + `why`(≥20字带数字) + `cost_if_wrong`(带量级)；checker 会**自己按 `hist.q` 末值 ×Π(1+q_growth) 递推到锚年再除 TAM**，与填写的隐含份额差 >0.5pp 即不过；`verdict` 须与 `implied−ref` 的漂移方向一致（容差 ±3pp）；**判「扩张」的必须填 `share_gain_from`——份额是零和的，说得出从谁手里抢才算数**。要点是把外推翻译成一句能逐季跟踪的话（阳光：「隐含份额 10.4%、与 2026 的 10.2% 持平，本页并没有假设它在抢份额」），不是逐年重算驱动链。**B L兜底段进 SOTP 的上限**——`driver_chain` 与 `calibers` 皆空的段，其 `seg_val` 占 Σseg_val 的比例 ≤ 其收入占比 +3pp，且 `logic` 里明说兜底；原有「最大分部禁 L 兜底」只管最大那段，管不到一个 30% 收入占比却配高倍数把 SOTP 顶起来的段。
- **CK-4** 估值离散度规则执行（<20%点估计/20-50%区间/>50%冲突不出单值）；**★估值卡印有效权重 `wnorm`（Σ=100%）+ 括号给滑块原始值，拖任一根全部卡片同步刷新（2026-08-17 石英「加权的权重=1」，05 §9 / 06 §3.0e ④）**；加权目标 vs 实测市值 的预期差>15% 已解释；**★五档等级（2026-08-12，05 §0.5）**：卡片/横条按 第一档→第五档 排列、每卡档位徽章、等级带渲出且标当前主锚档；第五档（终局/对标大哥）权重合计 >50% 时页面有解释；**★折现率**：全部范式 `r`∈[0.08,0.10]（越界=不过），`switches.elasticity` 用升档赔率区间标定；**对标大哥已点名**（leader_name 公司名+代码，basis 默认收入占比→市值占比，卡片无红 ⚠️；收入/利润双轨背离>30% 已解释）；**有 Forward 取期选择器时**（05 §9.5）：切换年份→PE/PEG/EV-EBITDA 卡名与加权目标联动、折现 n=年距、隐含读数刷新；SOTP/终局/大哥不跟随（时间语义锚）；选择器下有"远年利润配低 PE 档"纪律提示。
- **CK-6 第四章 矛盾地图（Phase5.5，见 09 §9；`node scripts/check_part4.js` 共 64 项）**
  **S 场景（4.1）** **S1** 3–5 条且**至少一条下行**；**S2** `from` 指名真实矛盾 id 且两端分属主动/从动；**S3** **每条都有 `knobs`（含下行）且实跑引擎与 `mcap_yi`/`odds` 自洽（±1%/±1pp）**、估值腿按 paradigm key 不按下标、`dir` 与 odds 符号一致、`odds_band` 夹住点估计；**S4** ΣR/M/V 对 odds 差 ≤3pp 且 `rmv.basis` 写明降级链；**S5** 催化 ≥1 且 `when`+`watch` 齐；**S6** `rmv_check` 已与第二章 `factor_quant` 对照；**S7** `summary.main_scenario` 对上某个场景 key；**★S8 概率与期望值（2026-08-14 阳光固化，09 §5.5g）**——每条 `prob`+`prob_basis`(≥10字)、`Σprob=100%±2pp`、`prob∈[0,1]`，页面渲三个数：**我的 EV（Σprob×odds）· 我给上行的概率 · 现价隐含上行概率（令 EV=0 反解 p_up＝−下行均值÷(上行均值−下行均值)，组内权重沿用自填 prob）**；**落点是后两个的差**——阳光实测 EV +20.9%、我给 45%、现价隐含 19.4%、差 +25.6pp，这 26 个点就是下注理由的全部量级；差 <10pp 时必须填 `scenarios.thin_edge_why` 说清为什么还下注。填 prob 三条纪律：串联条件要连乘（三步各 60% 非独立 → 给 20% 不是 60%）、三条下行加起来 <40% 要回头查是不是漏了「什么都不发生」这条路径、概率排序要与 `unlock[]` 已发生条数对齐。**★S9 历史对照＝跨公司/跨叙事（2026-08-17 石英股份读者反馈，09 §5.5h）**：每条 Case 有 `analog{case,period,what,diff}`，`case` 是别家公司/别的叙事（不含本股名）、`diff` ≥15 字；本股历史最强段的 R/M/V 同尺度条保留但改名，不再叫「历史对照」。
  **T 分型（见 13）** **T1** role 合法、**主动/从动各 ≥1**、subtype 在本 role 枚举内；**T2** 偏离子类默认时钟须写 `clock_override_why`；**T3** 从动型有 `ruled_out[]` 排除链；**T4** 纪律型 `coverage>0`+`ev[]`+升格三条件齐全带证据（`certifiable` 须限定持有期）；**T5** 系统协同型 `stack[]`≥2 且 `binding_now` 在 stack 内；**T6** 制度/权利型填 `sub_right`；**T7** `co_kill` 互指且 `odds_basis` 说明已扣重复。
  **D 深度研究** **D1** 双槽位 `deepdive` 的 understanding/plan/ruling 齐；**D2** `plan.blind_spot` 非空；**D3** `analog.diff` 非空。
  **a** 矛盾 8–12 条，每条 `label` 5–8 字 + `one_liner` 一句 + `detail` 30–50 字带数字，已去重（实测 20% 候选是同源重复）；**b** 每条 `dispersion_basis` **有具体数字**（谁给了什么数+极差+形态），至少半数挂 `ev[]` 逐字原句，写不出方差来源的一律标 `coverage:0` 并说明检索过什么词；**c** 每条 `odds_basis` 说清出处，参数类必须来自 `tornado.js` 且**按传导率修正为上界**，`[FALLBACK]` 区间的 bar 不得当赔率；**★`odds` 必须是数字**（可为 0 不可为 null，2026-08-17 石英 v3.2 十条全空→覆盖表与三坐标图全空）；**d** P&L 三层条目必填 `hooked`（挂到具体可调参数），挂不上的归叙事/估值（「主要矛盾是国产替代」这类不进图）；**e** `core.pricing` 与 `core.actionable` **两条都在且不是同一条**，各自 `why`+`action` 齐全；**f** 每条叙事有 `chain[]`（每步带 status）+`weakest`+`subs[]`，主图气泡→叙事锚点超链接可点；**★f2/f3/f4 叙事链可读性（2026-08-18 用户「4.5 说的内容很 ai，即使没用禁词也读不动」，09 §7a-2）**——**禁词表治不了这件事**，三条结构闸代替词表：每环 `claim` **必须含数字**（没有数字的一环换个标的照抄也成立）且 **≤60 字**（超了就不是一环是一段）、每条链 **≤6 环**、标「已证实」的环必须挂 `ev` 原句、`weakest` 必须**点名第几环**；**★4.5 不出图**（09 §7a）——次级矛盾只渲明细表，子坐标系与三坐标条已撤，CK-6g 因此改成「全页只有 4.1 那一张 `<svg class="cmap">`」，4.5 里再出现即报错；**g** 图面体检（09 §10a）：气泡两两不重叠、标签不压气泡不互压、浮窗不越界不溢出底板、浮窗层是 SVG 最后子元素、默认 opacity=0；**★4.1.1 默认视图是三坐标条 `cmapStrip`（一行一条矛盾，F/D/赔率三根同尺度条），气泡 SVG 在折叠块里且宽度封顶 760px（2026-08-17 石英「图太大」，06 §3.0e ①）**；**面积严格正比赔率**（主动＝圆 `r=4.3√odds`／从动＝等面积方 `a=√π·r≈1.772r`，禁用压缩标度）、**方块数＝从动矛盾条数**、浮窗**纯 CSS `:hover`**（file:// 不跑 JS）。
- **★CK-8 图表读数闸（`node scripts/check_charts.js --model <page_model>` 共 10 项，见 06 §3.0b）** —— 2026-08-16 赛力斯 v3.2 读者七条反馈固化。**七条里五条不是算错了，是数字对但读者读错了**，而病根同一个：**前三章所有的闸都在查数值正确性，没有一条在查读数歧义**。CK-8 补的就是后半句。**a/a2** `part2.phases[].chg` 是带 % 的展示串不是裸小数（落成 -0.4776 会双错：页面印「0.4776」读者分不清 47.76% 还是 0.48%；第四章历史对照条把它当**百分点**和 rmv 的 `_pp` 比，量纲错 100 倍。app.js 的 `chgTxt()`/`chgPct()` 是兜底，兜底是止血不是契约）；**b** `basket_beta` 的个股腿与 `rows`/`bench` 同为百分数（2026-08-15 已踩过一次，超额整列错 100 倍）；**c** 1.7 个股表 `peers[]` 同时给 `float_yi` 与 `mktcap_yi`，页面渲 `<thead>` 双口径并排——读者反馈「市值拉取有错误」时，**数字一分不差**（问财返回 218,385,102,814.9 元，复跑核对过），错的是整张表没有表头，比亚迪自由流通 2,184 亿被当成市值读，而总市值 7,642 亿，看上去就是拉错 3.5 倍；**d** 1.3 复合图的结果量柱腿在（`dupont.roe`）；**★d2–d5 1.4 逐季毛利率分解堆积面积图（2026-08-18 用户定稿）**——走 `cost_structure_q` 而非年度块、`quarters` 是 YYYYQn、上沿(`gross_margin`)与底层(`net_margin`)齐、五层(四费+税费)最多缺 1、「其他」桶体检（**常年盈利的公司**才当硬闸：盈利公司还有六成毛利落在没被解释的桶里基本就是单季指标取错成累计列）、`listing_year` 已填且起点贴着上市首年、**`src` 必须点名走的是 `单季度.*` 原生指标**（同名累计列并存，取错就是把 Q4 全年当单季画）；**★d6/d6b/d6c 1.4b 折旧不许被摊平**——单季数组里不许有 `da`（A 股季报不含现金流量表补充资料，单季折旧在报表上不存在）、TTM 的 `da` 只许落在 Q2/Q4（那两个点由披露累计数精确凑出）、`da_disclosure` 原始披露段必须在；**e/e2** 2.1b 的 Forward PE 与 Forward PS **不共轴**（「倍」只是读音相同，一个除盈利一个除收入；赛力斯 25x vs 1.27x 差 19 倍，同轴一画 PS 被压成直线，读者拿到「PS 常年不动」这个假读数），缺失值处理已写进口径；**f** 1.5 的 `box_caliber` 里若出现「箱线图」必须是在**否定**它；**★g/g2/g3/g4 2.2 估值算账必须两把尺子各算一遍（2026-08-16 读者反馈固化，03 §4e-2）**——`valuations[i].calibers.{ttm,fwd}` 由 `python3 scripts/phase_valuation.py --model <m> [--q-series <q>] --write` 生成，**分子共用同一个市值**（差异只可能来自分母才可比）、TTM 分母**按公告日可见**不按期末日（否则前视）、算不出的那一栏必须给 `na` 理由（「当时没有这把尺子」本身就是那一段的定价机制）；**`fwd.decomp` 是恒等式不是估计**（市值 ≡ 前瞻盈利 × 前瞻PE），两口径打架时**以它为准**——TTM 的 E 装的是过去四个季度已经赚到的钱，拐点上天然滞后；**g4** 散文里带 PE/`P/S` 标签的「A→Bx」必须对得上某一个口径（±20%）；**★g5/g5b/g5c 尺子选择闸（2026-08-18 用户改制，03 §2f-q2）**——**底部没有利润、或市场按第一档估值（PB/重置成本）定价的段，不许再用 PE 做 R/M/V 的 V 层**。`ln(PE₁/PE₀)` 在 E→0 时不是「很大」是**没有定义**，硬算的结果每次长一个样：**V 吃掉整段涨幅、R 与 M 挤成两根看不见的短条**，读者读成「这一段全是估值在动」，而真相是「这一段根本没有盈利这把尺子」——两句话的仓位含义相反。触发（起终点任一端）：归母≤0 / |净利率|<2% / PE>150x 或 <0 / 该段范式属第一档。降级链 PE→PS（收入仍是锚）→PB（净资产才是底），`factor_quant.ruler` 必填且换尺子时 `ruler_why` 必填，`m_pp` 归零要在 `basis` 里写明「利润率层无定义已并入 V」（不写就与「利润率恰好没变」无法区分）。`phase_valuation.py` 把探测结论落在 `calibers.ruler_suggest` 里直接抄。**跨段换尺子必须让读者看见**：三根 R/M/V 条的意义建立在「同尺度可跨列比」上，PB 段的 V 与 PE 段的 V 不是同一个量——页面已渲尺子徽章＋条带下黄条＋场景卡历史对照条上的尺子标注。**★j 版式闸（可选，`--html <built.html>`）**：j1 全局 `thead th` 不是白字（浅底深字，覆盖底色也不会看不见）；j2 3.1 表头写了单位 `.th-unit`。**实测救回的结论级错误**：赛力斯 v3.2 阶段⑥ 只用 TTM 算，得「PE 40.9→15.5x，尺子换了，这才是跌 70% 的机制」，并把「PE 失效→改用 PS」一路写进 `summary.thesis` 与第四章从动矛盾；前瞻恒等式说的完全相反——**−69.0% ＝ 前瞻盈利 −71.3% × 前瞻PE +8.0%**，FY+1 一致预期 100.2→28.8 亿而前瞻 PE 至今 31.1x 有定义且不降反升，**杀的是盈利预期、范式还没切**。同段还查出散文与结构字段打架（阶段① `factor_quant.basis` 写 P/S 2.70→1.18x 是对的，散文写 1.6→0.6x 是把 Forward 的数贴了 TTM 的标签）；**★i 走 esc() 的字段里不许有 HTML**（`phases[].logic`/`core_conflict`/`factor_quant.basis`/`feedback.*.answer` 写 `<b>` 会原样印出尖括号，加粗用 `**`；赛力斯从 v3.2 起就在漏，改版式才暴露——窄列折行太多没人逐字读）；**★h schema 降级哨兵**——规范要求的**结构项**一旦被写进自由文本，「写了」与「没写」在机器看来就一样了。本条不查内容只查「该是结构的地方还不是结构」，已巡：`company_type`（掉回 `{label,note}`）、`narrative_capacity.peers`（退化成字符串）、`phases[].factor_quant`（退化成字符串）、`phases[].basket_beta`（无 rows/bench）、`summary.accounting.steps`（无 scenarios/driver）。
  **通则（写死进 06 §3.0b）**：① 一个字段只能有一种读法，多口径的要么契约钉死要么口径写在眼睛必经之处；② 有多口径的数字列必须有表头且表头写死口径与单位；③ 量纲不同不许共轴、轴标题带**量纲**不带单位、一屏最多三根 y 轴；④ **图形分型 > 文字解释**——结果量走柱、分解项走线，读者按最像的图形去认不按图注去认（1.5 旧版已在折叠块写了「这不是箱线图」，读者照样反馈找不到箱体；治法是把图例画成图形本身，见 `.cons-legend` 的七个 SVG 样标）。**★观感通则（2026-08-17 石英股份八条读者反馈，06 §3.0e）**：⑤ 全景图不许比一屏高（条形/表格优先，气泡折叠）；⑥ **表头默认值本身必须安全**——全局 `thead th` ＝ 浅底 `--elev` + 深字 `--fg` + accent 下框线；要深底白字的表得在同一条规则里成对写 `background` 与 `color:#fff`。旧默认是深底白字、逐表补 `color` 是补丁，**同一条读者反馈（「3.1 表头字体改成黑色」）因此复发四次**，2026-08-18 改的是默认值；⑩ **有金额列的表，单位写在表头上**（`.th-unit`，3.1 已写「单位 亿元／比率行＝%」），写在 cap 或图注里不算数——表能横向滚，滚两屏 cap 早出视野了；⑦ 次级复合图一律可折叠（2.1b 已改 `<details>`，折叠里的 Chart.js 挂 toggle→resize）；⑧ 派生量显示口径与算法一致（权重印归一值）；⑨ 空值渲红字「未算」不渲 0。
- **CK-5 反馈闭环（Phase8-9，见 08 §8）** **a** 页面标注可用（右下 ✎ 浮钮 / 划词类型条 / 模块 ✎ pin；点一次能落 localStorage 且计数+1；云端模式 `/api/health` 绿 + 「同步到云端」返回成功计数）；**b** `[data-fbk]` 锚点 ≥15 且覆盖 分部模型/阶段列/估值卡/假设组；**c** 上一轮每条标注都有归宿（`feedback.resolved`/`open`，无空 answer），页顶「本版反馈回应」条数对得上，`action:'fixed'` 的 path 打了绿边；**d** `meta.version` 已+1、`updated`=今天、`changelog` 一句话；**结论被推翻时正文写明「原 v_n 为 X→本版 Y，因 Z」，不许静默改数**。
- **CK-7 开篇章「一段话说清楚」（Phase6.5，见 10 §7；`node scripts/check_summary.js --model <page_model>`，独立于第四章——`check_part4.js` 在 `part4` 缺失时整份提前退出）** **a1** `thesis` ≤30 字（a2 人工：含机制）；**b1** `company_type` 恰好 3 块、新契约 `{title,points:[{hook,k,v,tag,ev}]}`（旧 `{label,note}` 散文块＝不过）；**b2** 三块按序 生意本身/盘子/股性 且 `title` 是结论句；**★b3 必答钩子逐条覆盖**（10 §2 登记表 / `scripts/summary_hooks.json`；含条件必答：A股 派系类型与公司诉求、有 1.7 时 可交易容量、六段主因子 ≥2/3 同一时 历史行情由什么驱动；`hook` id 优先、缺则 k 关键词回退）；**b4** 每子项 k/v 齐、v ≥15 字、tag ∈ FACT/EST/DNA；**b5** 全章 ≥2 个 DNA、≥1 处挂 ev；**b6** 周期还是成长落成判定句（收入/利润曲线分开、决定哪把尺子）；**b7** 真β/假β/σ 落成判定句且带推论（能不能对冲/跟哪条线）；b8 人工：knowhow 判据（同行业照抄成立＝不合格）、股性数字出自 `fetch_stock_profile.py`；**b9** 密度：每条 v FACT ≤100 字 / EST·DNA ≤150 字、选答每块 ≤2 条、三块 v 合计 ≤4,000 字；**★t1/t2 概览类型卡（2026-08-17 石英股份读者反馈，10 §2.8）**：`summary.type_card` 已填、`type` ∈ 真β/假β/σ/叙事-题材、`verdict` ≥10 字，β 类给核心叙事线(≥1 条带定位)+K 线方位、σ 类给净利率/ROE 分位+PE/PS/PB 分位，且 `type` 与股性块 beta_kind 同一个词；**c1** `pillars` ≥3 组覆盖需求/供给/公司、每条带数字+tag；**c2** ≥1 条显式算式把行业盘推成公司自己的数；**c3** ≥1 条点出链撞上的约束（分型名不算）；**c4** ≥1 处 subs 下钻或两路径互证；**c5** 第四章有 `weakest` 时开篇点名了最先断的一环；**d1** `mcap_split` ≥3 行且含「超出/多给」差额行、`steps` ≥1 步且三档 scenarios 带 driver；**d2** `conclusion` ≥40 字、`price_assumes` 非空；**d3** `stake` 数字（分段标签走 `segment`）、`attrib_yi` 缺省时可乘；**e1** `anchor_pe`+`anchor_pe_basis` ≥20 字、`r ∈ [0.08,0.10]`、无「落点被截」手写找补（`inHist` 页面自己说话）；**e2** `ladder` ≥4 档、`tier` 1–5 齐、`current` 已标、前提未成立档有 `mcap_if_yi`（够不到现价的档页面自动不渲，数据层写全）；**f1** `switches` ≥2 条四格齐且至少一条向下；**f2** `prob ∈ (0,1]`；**f3** 升档 prob 合计 ≈ 第四章上行 Case ±10pp；**g** `main_scenario` 对上 `part4.scenarios.items[].key`；**h1** 用户可见文本无「反算」、无脚手架关键词（`申万|通行分层|个交易日|本模型|本案|本页|本表|见第[一二三四]章|实跑|不手估|拖动.*滑块`）；h2 人工：全章无与前四章冲突的数字、文本版与页面一致（`__EONE_APP__.summaryText()`）、拖任一假设滑块 → 兑现年份/隐含PE/赔率三处同步变（读页面文本验收）。
- **引用纪律（全程）**：每个数字带 (来源, 报告期) + FACT/EST/DNA；【Estimate】含卖方/自算/AlphaPai；黑话不入正文；`赔率=目标市值/当前市值−1` 统一口径。

---

## 关键陷阱（务必内化，`references/01` 有详解）
- 分部收入**只返回 top-5**，公司口径标签**逐年按排名漂移**→跨年归一映射，尾部并「其他」。分部一次一维度（分产品/行业/地区各调一次；一句话全给默认按地区）；查绝对额必带「金额」。
- iFind 数值带 `万/亿` 后缀、分部收入是**元**→统一转亿元；成本查询列不稳定（可能缺 管理/财务费用绝对值）→按费率反推或再查。
- **研发费用 2018/2019 前多为空**（早期未拆出）；财务史深度约到 2007，老股非真·上市首年。
- **子公司永远走 qcc**（iFind 会静默命中股东数据）；qcc 先 `get_company_by_query` 锚定法定名，仅覆盖中国大陆主体。
- Chart.js：催化散点 x 必须 snapToWeek（≤日期最近周五，否则堆右侧）；涨幅>1.8x 走对数轴；canvas 高度由 `.chart-wrap` 锁定；事件点=按类别 scatter overlay + 自定义 canvas 插件画 #号/阶段带（不用 annotation 插件）。
- iFind 财务日期须**报告期格式**(2024-12-31)；token 过期→`ifind_client.py config --set-token`；客户端自动剥代理。
- **港美股：iFind `fin/holders` 返回「查询结果为空」而不是报错**（实测 00700），六张表会全空且只在末尾打一行 ⚠️ gaps → `fetch_ifind.py` 已内置市场闸直接拦截并给出替代命令；`search_notice` 仍是 iFind 侧唯一触达非 A 股主体的入口。
- **港美股币种三口径**（财报币种 / 交易币种 / 页面展示币种）可互不相同，实测腾讯自算 PE 19.2 vs 接口 PE-TTM 16.43 差 17% 就是港元市值除人民币净利。`meta.currency_check` 会算这个比值；**偏离>15% 未查清前，市值锚不许进估值范式**。
- **美股别用 SEC XBRL `companyconcept` 找分部**：它只回合并口径无维度（实测 AAPL FY24 只有 391,035M 一个数）。分部走 `FilingSummary.xml` → 名字带 `(Details)` 的 R-file 表。成员名跨年报会换写法（`Americas` ↔ `Americas | Operating segments`），不归一会渲成两条各缺一半的重复分部线。
- **东财会保留公司早年才披露的科目名**：直接按名取会得到一列 None 且不报错（实测 AAPL『其他营业费用』2021 年后消失）→ `series()` 已改为跳过「区间内全空」的候选。美股 SG&A 多为合并披露，别套 A 股销售/管理二分。
- **file:// 缓存**：改过模板/`app.js`/`annot.js` 重建后，浏览器可能仍跑旧 JS → preview 时 URL 加 `?v=<新串>`；验收前先确认 `document.scripts` 里有你新加的函数名（2026-07-25 实测踩过）。
- **★后台窗格每次 `navigate` 都会把 viewport 打回 0×0**（2026-08-14 实测）：`innerWidth=0` → 所有 canvas `width=0`、像素采样全 0，看着像图全挂了。**顺序必须是 `resize_window` → `location.reload()`，且每次重新导航后都要再来一遍**（不是只做一次）。rAF 挂起导致悬停/截图失效时，改为直调 handler + canvas 像素采样。
- **★沙箱下起不了本地 http 服务时的验收退路**（2026-08-14 实测：`os.getcwd()`／读文件均 `Operation not permitted`）：**用 node 从真 `app.js` 里按函数名抠出渲染函数体，`new Function` 注入 `num/esc/PAL` 三个垫片直接跑**，比 jsdom 轻、且跑的是**真代码不是复制品**。本轮 `bbHTML` / `scenEV` / `backsolve` 三处都是这么验收的，能覆盖分支（空数据、缺字段、极值）。
- **反馈平台 token 不进页面**：页面只 `POST /api/ann`；拉标注的 `FB_ADMIN_TOKEN` 只存本机 config/环境变量。`--only-new` 依赖 `feedback_resolve.py` 回写 status，跳过 resolve 直接改稿会导致下轮重复拉。

---

## 嵌入说明（RAG 语料库向量后端）
- **operative（现在就能用）= `qwen3-vl-embedding`**：research-rag 现配，多模态（文本+图表同空间，2560维），key 在 `research-rag/config.yaml`，已实测 200。Phase0.0 建库默认走它。
- **`qwen3.7-text-embedding`（用户指定，待激活）**：其 key 为专属 MaaS 令牌（`sk-sp-…`），在 public DashScope 与现有 MaaS host 均 401，**需其专属 endpoint host**（形如 `llm-xxxx.cn-beijing.maas.aliyuncs.com`）。host 到手后：填 `scripts/rag_config.json` → 给 research-rag embedder 增 text 后端（见 `references/07`）→ onepager 工作区用它重建索引。未到手前用 qwen3-vl，不阻塞。

## 加载顺序规则
1. 恒读本 SKILL.md。**2. Phase0.0 前读 `07-rag-corpus.md`(⚡) 并先问用户有无前置资料。** 3. Phase1 前读 `01-data-recipes.md`(⚡)。4. Phase2 读 `02`。5. Phase3 前读 `03`(⚡)。6. Phase4 前读 `04`(⚡)。7. Phase5 读 `05`。**7.5 Phase5.5（第四章 矛盾地图）前读 `09-contradiction-map.md`(⚡)，定 role/subtype 时查 `13-contradiction-typology.md`(⚡查表)。** **7.2 Phase1.7（1.7 可交易容量）前读 `14-narrative-capacity.md`。** **7.15 Phase1.5（券商预期区间）前读 `11-consensus-boxplot.md`；Phase1.6（筹码龄）前读 `12-chip-age.md`。** **7.8 Phase6.5（开篇章 一段话说清楚）前读 `10-summary-backsolve.md`(⚡)——它虽渲在最前，但必须四章定稿后才写。** 8. 改模板/图表时读 `06`。9. Phase8/9（上线+反馈回灌）前读 `08-feedback-loop.md`(⚡)。10. 需要案例锚形态时读 `examples/INDEX.md`（无同类案例则声明「无锚」，按规范自推，勿强行套用）。
**11. ★写任何用户可见的正文之前，读 `buyside-voice/references/voice-rules.md`（语言规范全生态唯一出处，本 skill 不留副本）。**路径两处都要试**，别只试一处就当没有：`~/.claude/skills/buyside-voice/…` 或 `~/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/*/*/skills/buyside-voice/…`——本机实测 buyside-voice **只在后者**，硬写前者会静默失败（2026-08-16 自检查出）。** 硬指标：禁词 0 命中、`——` 全篇 ≤8 且每千字 ≤1、判断性警句 ≤8 且只在结论位、自造概念 ≤2 且首现先给一句大白话、全篇 ≥1 处明说「这条把握不高」。**唯一豁免是逐字引用**（`ev[].quote`、`chain[].ev`、纪要原文）——那是信源，一个字都不许为了过闸去改。质检跑 `python3 <buyside-voice>/scripts/voice_scan.py <文件>`（`<buyside-voice>` 同上，两处路径都试）；第四章的额外约定见 `09` §0。
