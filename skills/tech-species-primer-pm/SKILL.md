---
name: tech-species-primer-pm
description: "业务认知卡·基金经理版 v3.3-PM(在 v3.2 科普卡之上加一层白话;2026-09-29 按基金经理反馈改:一上来全是术语、技术和技术变化路径没人用通俗话讲、Palantir 看不懂在做什么)。给一家公司(A股/港股/美股/日股)、一块主题业务或一条产业链/技术物种,从 0 取证做「XX 业务认知」长报告,读者是懂财务估值、不懂技术的基金经理:最前面「零、一分钟看懂」(一句话/打个比方/举个例子/钱怎么来/技术怎么变/要盯的一件事 + 是什么不是什么表 + 钱怎么流图);技术白话章(问题/原理图/技术演进路线图含每代代价与下一步分岔/对公司意味着什么);每个业务章章首白话块;术语词典与正文悬停释义;外行复述评审。其余照 v3.2:六节业务章、图 55–70、表 ≥10、汉字 ≥10,000、单文件离线 HTML、不写估值。验收 --gate --pm。触发:基金经理版、给基金经理看、PM版、白话版、通俗版、讲人话、看不懂、太专业、术语太多、一分钟看懂、技术怎么演进、技术路线图、技术变化路径、用大白话讲清XX的业务、先帮我搞懂XX(读者没有技术背景)。与 tech-species-primer(v3.2)同装时,读者是基金经理或领导、或用户嫌卡片太专业,用本版。"
---

# 业务认知卡 · 基金经理版 v3.3-PM

> 本 skill 由 tech-species-primer v3.2.0 派生,**v3.2 的全部规格、脚本、数据纪律照旧有效**(`references/DESIGN_v32.md`),
> 本版只在上面加一层白话(`references/DESIGN_pm.md`,两者冲突时以 PM 为准)。写法细则、类比库、改写正反例在
> `references/plain_language_guide.md`;完整写法样例在 `examples/pm/`(Palantir 业务白话、CPO 技术路径)。

## 它做什么

读者是**基金经理**:懂财务报表、估值和行业比较,**不懂这门技术**;先花五分钟决定要不要往下读,读完要能向投委会或领导复述。
读完要能讲清:**卖什么、卖给谁、怎么赚钱、技术怎么一步步变过来、下一步往哪走、最该盯什么**。

基金经理对 v3.2 卡片的两条反馈(2026-09-29)与本版的对应改法:

| 反馈 | 本版改法 |
|---|---|
| 「一上来都是专业术语,没有基础背景的人比较难读明白;少了用通俗语言解释技术和技术变化路径的部分」 | 最前面加**零、一分钟看懂**;加**技术白话章**,核心是一张**技术路线图**(每一代解决了什么、代价、谁受益谁受损、下一步分岔);每个业务章章首加**白话块**;术语进**词典**并在正文**悬停即见解释**;`--pm` 验收查缩写首现有没有解释 |
| 「Palantir 没看明白公司业务,要用一段通俗易懂的话把业务讲清楚」 | 零章强制「一句话 + 打个比方 + 举个例子(真实客户前后对比)+ 钱怎么来」,另加「是什么、不是什么」表与「钱怎么流」图;样例见 `examples/pm/pltr_plain_sample.md` |

全卡分三层,读者可在任一层停下:**白话层**(零章 + 章首白话块 + 路线图,约 5 分钟)→ **结构层**(lead、图题、表)→ **证据层**(v3.2 的全部正文与来源口径)。
只建认知,不做估值、不给买卖建议。

| 对象 | 章节主干 |
|---|---|
| 公司卡 | **零、一分钟看懂** → 一、公司总览 → **二、技术白话** → 每个主业一章(lead + **白话块** + 六节)→ 专题章 → 非主业 → UE与经营效率 → 跟什么走 → 正在变什么 → 来源与口径 → **附录、术语小词典** |
| 主题卡 | 同上,零章与技术白话章只讲主题业务;非主题业务一章简述 |
| 产业链 / 技术物种卡 | **零、一分钟看懂** → **一、技术白话**(吸收 v3.2 的是什么 / 为什么是现在 / 路线之争)→ 产业链每一环一章(白话块 + 六节)→ 谁付钱 → 对现有产业链意味着什么 → 跟什么走 → 正在变什么 → 来源与口径 → **附录、术语小词典** |

技术不是看点的公司(品牌消费、渠道、金融),经用户同意可不设技术白话章(`--no-tech`),在相应业务章 x.3 开头写一段白话演进。

## 铁律(违反即返工)

1–12 条沿用 v3.2:

1. **从 0 开始**:旧卡、旧一页纸的结论、章题、数字不沿用;本地材料只作线索,每个数回原文核对。**用户已有文件只读。**
2. **数字回一手**:公司数回招股书 / 年报 / 10-K 原页,全卡写 **PDF 页码**;行业数写机构、报告日期、页码;缺的写「数据不可得」并写清查过哪些文件。
3. **先建统一数字底座**(`work/facts_spine.md`),全卡同一个数前后一致;多套口径并存时分开列,每张图写明用哪套。
4. **口径冲突并列**:图后 `> [!note] 口径分歧:…`,同时进来源与口径章的取舍表。
5. **不写**估值、目标价、评级、PE/PS、卖方盈利预测;卖方观点只能以〔卖方估计〕进叙述;含这些内容的研报原图整张不用。
6. **不照抄参考报告**:`--gate --ref` 的照抄检查必须 0 命中。
7. **图多但不堆**:目标 55–70 张,每张一句话说清它证明什么;同一信息不重复出图。
8. **图片进卡前用 Read 看一眼**;alt 带类别前缀;不收签约、剪彩、展会、合影照片。
9. **取数纪律**:Wind 一张卡最多 1 次、结果落盘;iFind 不用;FMP 只定点;AlphaPai 只用 `image`。
10. **隐私**:任何网络请求不带用户邮箱;EDGAR 用 `curl --noproxy '*'` 与非个人 User-Agent。
11. **写法**:中文为主;叙述为主,判断先行、证据跟上、推理看得见;段内加粗 1–3 处;标题即结论且不比数据说得满;不写空话;「锚定」改用「对照」。
12. **交付前验收**:`merge_card.py` 通过(退出码 0)→ 三路评审处理完 → `shots.py` 截图无 JS 报错、无坏图、手机宽无横向溢出。

基金经理版另加:

13. **白话先行**:零章在最前;每个业务章 lead 之后、第一个 `###` 之前有 `> [!plain] 白话:…`;每节第一句是白话结论。
14. **技术讲路径,不讲型号**:技术白话章必有 roadmap 路线图,每一代写清「解决了上一代什么麻烦、代价是什么、谁受益谁受损」,最后给下一步分岔与验证信号。
15. **术语不裸奔**:首现当场一句白话(不许用术语解释术语),每段新术语 ≤2 个;每章登记 `parts/NN_terms.md`,合成词典、正文悬停释义。
16. **类比与例子有纪律**:类比只放在零章、章首白话块、技术白话章 x.1,每处一个,说清边界;例子必须真实、前后对比、有出处,厂商宣称标〔厂商口径〕。白话不是营销腔,不许比数据说得满。

## 目录约定(new_card.py 建好)

```
R = ~/Desktop/research-materials/{公司}-{代码}/primer_pm/     (主题卡如 Nokia-NOK/primer_pm_DCI/)
  card.json(edition=pm, plain{…})  materials.md  questions.md  评审处理记录.md
  parts/00_一分钟看懂.md(骨架,主线最后写)  parts/02_技术白话.md(骨架)  parts/NN_章名.md
  parts/NN_facts.md(数字台账)  NN_gaps.md(口径冲突与缺口)  NN_terms.md(术语台账)
  images/cN_*.jpg|png|svg
  sources/{text,cninfo,reports,alphapai,market,peers,web}/
  work/{00_header.md, BRIEF.md, PLAN.md, facts_spine.md, reader_test.md, stats.json, test/, shots/, pdfimg/}
  {公司}-业务认知-基金经理版.md / .html      {公司}科普-基金经理版-YYMMDD.html(飞书用副本)
```
脚本都接受 `--root R`;在 R 里运行时自动找 card.json。下文 `$S` 指本 skill 目录。

## 流程

**第 0 步 · 立项与建目录**
- 实体消歧(上市主体、运营主体、口径主体、代码与币种);主题卡 / 产业链卡把范围写死。
- `python3 $S/scripts/new_card.py --root R --name 宏和科技 --code 603256.SH [--type company|theme|industry] [--no-tech]`
- 用户给了完整 prompt 就原文存 `work/PLAN.md`;没给就按 `references/kickoff_prompt_template.md` 写一份(含基金经理版要求),给用户过目再开工。
  写 PLAN 时先回答一个问题:**这家公司最容易被读者套错成哪一类生意?**(答案进零章「是什么、不是什么」表。)

**第 1 步 · 盘点材料,先落盘 `materials.md` 与 `questions.md`**(同 v3.2)
- 一手文件按市场取(`references/data_sources.md`);PDF 用 `scripts/pdf2txt.py` 转按页文本;招股书与年报的图用 `scripts/pdfimg_catalog.py`;研报原图 `scripts/ap_images.py`。
- 20–35 个必答问题里,**至少 5 个是白话层的问题**(「用一句话说它卖什么」「客户原来怎么解决这个问题」「技术每一代解决了什么」「最真实的一个客户例子是什么」「读者最容易误解成什么」),标到零章或技术白话章。
- 另找 **2–3 个真实客户案例**(官网案例、客户公告、业绩会、招股书)与**技术代际材料**(厂商发布、标准组织文件、研报的技术路线图),作为零章「举个例子」和路线图的证据。

**第 2 步 · 数字底座 `work/facts_spine.md`**(同 v3.2,`references/facts_spine_template.md`)

**第 3 步 · 改 `work/BRIEF.md`**(new_card.py 已按 `references/BRIEF_template.md` 填好路径,含基金经理版 §2b 与 §5b)
- 补 §0 读者目标、§1 材料表、§3 业务章清单;样例 `examples/dekeli/BRIEF.md`。

**第 4 步 · 按章并行写 `parts/`**
- workflow(用户说 ultracode 或同意时)或 Agent 子代理,每章一个 agent;任务里写:章号与章名、必读 BRIEF 与 `references/plain_language_guide.md`、
  本章 questions 编号、图数 / 表数 / 字数目标、必放图类,以及**章首白话块与 `NN_terms.md`**。
- **技术白话章单独一个 agent**,按 `assets/templates/ch_tech_plain.md` 与 DESIGN_pm §3 写,必读两份 `examples/pm/` 样例的第二章。
- 子代理回主线 ≤300 字(章号、图数、表数、字数、白话块数、登记术语数、错误数、主要缺口)。

**第 5 步 · 主线写零章「一分钟看懂」**(所有业务章与技术白话章落盘之后)
- 按 `assets/templates/ch00_plain.md` 与 DESIGN_pm §2 写 `parts/00_一分钟看懂.md`:一句话 / 打个比方 / 举个例子 / 钱怎么来 / 技术怎么变 / 要盯的一件事 + 表 0-1 + 图 0-1。
- 数字只从底座取、取整;例子用第 1 步找到的真实案例;写完删掉所有 TODO。

**第 6 步 · 合并渲染与验收**
- 按最终章节改 `card.json` 的 `nav`、`ref_bg`、`plain.allow`(公司英文名、代码);`work/00_header.md` 的口径与底稿两行写实。
- `python3 $S/scripts/merge_card.py --root R` → 合并(自动由 `NN_terms.md` 合成术语词典)、渲染、`--gate --pm`。看汇总行、
  「基金经理版:」一行与未达标项,补缺直到退出码 0。只看输出尾部,不打印整份 HTML。

**第 7 步 · 三路评审**(`references/review_protocol.md`)
- 评审 A(版式、深度、重复出图)、评审 B(抽 50+ 个数回原文,专查口径混用)同 v3.2;
- **评审 C(外行复述)**:子代理扮演不懂技术的基金经理,只读白话层,复述五件事并列出卡住的词句;记录写 `work/reader_test.md`。复述有「错」或卡住的词 >5 个,改白话层后重评。
- 按意见修正(改前备份 `_bak_rN/`),重跑第 6 步;写 `评审处理记录.md`(结果表 / 评审 A / 评审 B / 评审 C / 仍有的局限)。

**第 8 步 · 截图验版式**
- `python3 $S/scripts/shots.py --root R`,Read 逐张看;另看一张零章首屏、一张路线图、一张术语悬停。验收同 v3.2。

**第 9 步 · 交付**
- 文件:MD、HTML、materials.md、评审处理记录.md(含评审 C 的复述结果)。
- `merge_card.py --feishu` 另存「{公司}科普-基金经理版-YYMMDD.html」,经用户同意后传飞书云空间根目录。
- 一句话报:图数(交互 / 图片 / 自绘)、表数、汉字数(渲染器口径与纯叙述)、白话块数、词典条数、评审 C 结论、数据缺口。

## 已有 v3.2 卡片改成基金经理版(例:Palantir)

v3.2 卡片的证据层(数字、图表、来源口径)可以保留,只补白话层,不必从 0 重做:

1. 复制原卡目录为新目录(原目录只读),card.json 加 `"edition": "pm"` 与 `plain`(照 new_card.py 的默认值,`allow` 填公司英文名与代码),
   `out_stem` / `feishu_name` 改成基金经理版命名;parts 章号整体后移,空出 `00`(零章)和 `02`(技术白话章)。
2. 各业务章:lead 之后加 `> [!plain] 白话:…`;x.3 历史演变的时间轴前加两三句白话;把本章术语登记到 `NN_terms.md`(原 9.x 名词表拆进来)。
3. 技术白话章:一个 agent 按 `assets/templates/ch_tech_plain.md` 写,路线图的每一代从原卡 x.3 / x.4 的事实里取,补写代价与受损方。
4. 零章:主线最后写。Palantir 直接对照 `examples/pm/pltr_plain_sample.md` 的零章(一句话 / 数字沙盘的比方 / 空客 A350 例子 / 钱怎么来 / 四代平台 / 是什么不是什么表 / 钱怎么流图),数字换成原卡底座里的值。
5. `merge_card.py`(`--gate --pm`)→ 评审 C(外行复述)→ 截图 → 交付。评审 A、B 只需复核新增部分与改动过的数。

## 结构与门槛速查

- **v3.2 门槛不变**(`references/DESIGN_v32.md` §3/§6):图 ≥55(交互 ≥30、原图 / 流程 / 示意等 ≥20)、表 ≥10、汉字 ≥10,000(**术语词典不计入**)、业务章六节与必放图、每张图表有来源行、照抄检查 0 命中。
- **基金经理版门槛**(`--pm`,DESIGN_pm §5):零章在最前、汉字 500–1,800、有打个比方与举个例子、英文缩写 ≤3;技术白话章有 roadmap;每个业务章章首有白话块;词典 ≥15 条;首现无解释的英文缩写 ≤3;无残留 TODO。门槛在 card.json `plain` 里改(下调须用户同意)。
- **新 MD 语法**:`> [!plain] 打个比方:…`、`> [!example] 举个例子:…`、```` ```roadmap {JSON} ````、```` ```glossary 术语 | 白话解释 | 打个比方 | 对投资意味着什么 ````;样例在 `assets/fixture/fixture.md` 末节与 `examples/pm/`。
- 专题章、技术白话章的 h3 不用「行业规模 / 竞争格局 / 具体产品 / 核心竞争」(否则按业务章验收)。

## 上下文预算(主线 ≤18%)

- 主线只做:读规格、写 PLAN / materials / questions / BRIEF、建底座、编排子代理、**写零章**、合并渲染、汇总评审、交付。取证、下载、写章、看图、评审全放子代理。
- 主线不读大文件全文:参考版式 HTML、`examples/sungrow/card_v32.md`、PDF、按页文本、渲染后 HTML,只 grep / head。`examples/pm/` 两份样例各约 1 万字节,可以全读。
- 接近 18% 时按「底座 → 各章落盘 → 零章 → 合并 → gate 通过 → 飞书」的顺序保。

## 文件地图

| 路径 | 用途 |
|---|---|
| `references/DESIGN_pm.md` | **基金经理版增量规格**:反馈与诊断、零章、技术白话章、全卡白话纪律、`--pm` 验收、评审 C |
| `references/plain_language_guide.md` | **白话写法指南**:三条总原则、句子级规则、零章与路线图怎么写、类比库、改写前后对照、自检清单 |
| `references/DESIGN_v32.md` | v3.2 设计规格正本:结构、篇幅与图表密度、MD 写法、视觉规范、质量门槛 |
| `references/BRIEF_template.md` | 章节 agent 共用简报模板(含基金经理版写法与术语台账) |
| `references/kickoff_prompt_template.md` | 单卡计划模板(基金经理版);`examples/prompts/` 六份 v3.2 真实启动 prompt |
| `references/review_protocol.md` | 三路评审(A 版式深度 / B 数字核对 / C 外行复述)、截图、评审处理记录 |
| `references/pitfalls.md` | 踩过的坑(含 2026-09-29 基金经理反馈) |
| `references/facts_spine_template.md` / `data_sources.md` / `visuals_tools.md` / `legacy_handoff.md` / `glossary_jp_zh.json` | 同 v3.2 |
| `assets/templates/ch00_plain.md` / `ch_tech_plain.md` | 零章与技术白话章骨架(new_card.py 复制到 parts/) |
| `examples/pm/pltr_plain_sample.md` | **写法样例:Palantir 业务白话**(零章、技术白话章、业务章章首、词典),可直接渲染 |
| `examples/pm/cpo_tech_path_sample.md` | **写法样例:CPO 技术路径**(产业链卡的零章、技术白话章、词典),可直接渲染 |
| `scripts/render_report_v32.py` + `render_assets_v32.py` | 渲染器(新增 plain / example 块、roadmap、glossary、悬停释义、`--pm` 验收) |
| `scripts/merge_card.py` | 合并 parts → 渲染 → `--gate --pm`;由 `NN_terms.md` 自动合成术语词典;`--feishu` 另存飞书副本 |
| `scripts/new_card.py` | 第 0 步建目录(edition=pm、零章与技术白话章骨架、reader_test.md) |
| `scripts/test_render_pm.py` / `test_render_r3.py` | 基金经理版 / v3.2 渲染器回归测试 |
| `scripts/pack_skill.py` | 打包成 `tech-species-primer-pm.skill` 并自测 |
| 其余 `scripts/`、`assets/`、`examples/` | 同 v3.2(取数、取图、截图、自绘工具、参考版式、样卡) |

## 依赖

Python 3 + PyMuPDF(fitz)、Pillow、requests;截图与自测要 playwright + chromium。渲染器只用标准库 + Pillow,离线可跑;悬停释义是内联 JS,无外部请求。
