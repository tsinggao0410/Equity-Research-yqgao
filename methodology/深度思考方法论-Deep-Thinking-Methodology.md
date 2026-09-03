# 深度思考方法论 · Deep-Thinking Methodology

> **中英文对照 / Bilingual (ZH · EN)**
> 每节先中文，后英文；纪律与术语用双栏表并置。
> Each section gives the Chinese first, then the English. Disciplines and glossary are laid out in parallel columns.

**来源 · Source**　整理自《AI 投研的方法论与深度进展》（高有青，2026-08-19，v5 · 17 页），以及生成一页纸的那套 skill 里已固化的执行纪律（skill 本身未在本仓库公开，只保留它的成果与这份方法论）。本文是方法论的**文字版**；`methodology/` 下的 HTML / PDF 是同一份内容的现场版。
Compiled from *Methodology and Progress in AI-Assisted Equity Research* (2026-08-19, v5, 17 slides) and the operating disciplines hard-coded in the skill that generates the one-pagers (the skill itself is not published in this repository — only its output and this methodology are). This is the prose edition; the HTML / PDF in `methodology/` are the presentation edition of the same material.

---

## 全篇的一句话 · The One Sentence

> **投研的难点不是找数据，是把「我以为」降级成可核的算式、可改的假设格、可查数的触发线。**

> **The hard part of research is not finding data. It is demoting "I think" into a checkable formula, an editable assumption cell, and a trigger line you can go look up.**

推论：三种交付形态的区别只在一处 —— **谁被允许改哪一格。**
Corollary: the only thing that separates the three delivery formats is **who is allowed to change which cell.**

---

## 一 · 为什么现在要做这件事 / I. Why This, Why Now

### 1.1 生产资料的外置 · The externalization of the means of production

做研究的生产资料正在被外置。「收集、整合、比对公开信息」这段能力，从个人手里挪进了不到十家公司的云端，按次计费。把五代研究员的**自持度**（个人可携带的生产资料 ÷ 日常依赖的生产资料）排开看，它从来不是单调下降的，但这一代掉得最狠。

The means of production for research are being externalized. The capability to "collect, integrate and cross-check public information" has moved out of the individual's hands and into the clouds of fewer than ten companies, billed per call. Line up five generations of analysts by **self-custody ratio** (portable means of production ÷ means of production relied on daily) and the curve was never monotonic — but this generation's drop is the steepest.

| 时代 Era | 关键生产资料 Key means | 研究员形态 Analyst form | 自持度 Self-custody |
|---|---|---|---|
| 一 · 封建 800–1750 | 可耕土地、水利、磨坊 | 修道院抄书僧：书在围墙内，离开就再也读不到 | ~0% |
| 二 · 工业资本 1750–1920 | 蒸汽机、厂房、铁路 | City 的 statistician：账册、计算尺、笔记本自带，跳槽能打包带走 | **~55%（历史最高 all-time high）** |
| 三 · 福特主义 1920–1970 | 流水线、消费信贷 | 大行研究部 analyst：Rolodex 是自己的，差旅与订阅由雇主付 | ~35% |
| 四 · IT 全球化 1980–2020 | 芯片、软件、数据、平台 | 买方 analyst：Bloomberg、专家网络、数据库全在雇主账上 | ~25% |
| 五 · AI 2023— | 模型权重、训练级 GPU 集群、训练数据 | AI 时代 PM：能力按次租，权重是黑箱，价格与 rate limit 由对方定 | **~10%（被动值 passive default）** |

**SO WHAT.** 曲线不是单调下降 —— 每次生产资料更换的头 20–30 年都会给一次短暂反弹，然后新所有者用法律、科层、接口把它压回去。Era V 的 10% 是「不干预」的默认值；**主动干预能拉回 40–50%**。整套方法论要解决的就是这个干预怎么做。

**SO WHAT.** The curve is not a slide — each handover of the means of production grants a 20–30 year rebound before the new owner presses it back down with law, hierarchy and API terms. The 10% of Era V is the *do-nothing* default; **active intervention pulls it back to 40–50%.** Everything below is what that intervention looks like in practice.

> 自持度为定性刻度，非可审计统计量；Era V 的 10% 是「不干预」情形下的估计值，把握不高。
> Self-custody is a qualitative scale, not an auditable statistic. The Era V figure of 10% is a low-confidence estimate of the no-intervention case.

### 1.2 第三次圈地 · The third enclosure

前两次圈地至少还有法可依 —— 议会立法、WTO 谈判桌上的知识产权章节；这一次目前只靠平台自己写的服务条款，连一部统一的法律框架都还没有。

The first two enclosures at least had law behind them — Acts of Parliament, the IP chapter at the WTO table. This one runs on terms of service the platforms write themselves; there is not yet a unified legal framework at all.

| 圈的是什么 What is enclosed | 被圈走的东西 What is taken | 对做研究的人意味着什么 What it means for an analyst |
|---|---|---|
| 第一次 · 土地（16–19 世纪，英国） | 公地：森林、牧场、沼泽、河流，几百年来村庄共有 | 小农被驱离到法律意义上的无地状态 |
| 第二次 · 知识（TRIPS 1994 起） | 医学配方、音乐、软件、基因序列、传统医药 | 印度 neem 树被美国公司申请专利，打了十多年官司才部分推翻 |
| 第三次 · 认知（ChatGPT 2022 起） | 互联网、图书、论坛、代码仓库、用户对话 → 不到 10 家公司的专有权重 | **「我能读到别人不读的材料」这条差价直接归零** —— AI 读得比你细，而且不累 |

时间轴压掉了一个数量级：**350 年 → 30 年 → 3.5 年**（第三次为已过时长，全程 10–15 年为低把握估计）。同构的地方在结构不在比喻：历史贡献被私有化后，再以租金形式向原贡献者收费 —— Stack Overflow 回答者贡献二十年内容，现在每月付 20 美元订阅，才能用上由自己创造的知识。

The timeline compressed by an order of magnitude: **350 years → 30 years → 3.5 years** (the third figure is elapsed time; 10–15 years to run its course is a low-confidence estimate). The isomorphism is structural, not metaphorical: historical contribution is privatized, then rented back to the contributors. Stack Overflow answerers built twenty years of content and now pay $20/month to use knowledge they created.

### 1.3 窗口期只有一件事可做 · The only move in the window

「收集 + 整合公开信息」最先贬值，因为它正好是 AI 做得最好的一段。剩下**四件短期安全**：

The "collect + integrate public information" layer devalues first, precisely because it is what AI does best. Four things stay safe in the near term:

| 短期安全的四件 Four things still safe | 为什么 Why |
|---|---|
| 产业链实地 Field work along the value chain | AI 没腿 — AI has no legs |
| 长周期框架 Long-cycle frameworks | AI 没长期记忆 — AI has no long-term memory |
| 主动 kill 自己的 thesis Actively killing your own thesis | AI 只会附和 — AI only agrees with you |
| 跨行业迁移 Cross-industry transfer | 成本已被压到 6–12 个月 — the cost has collapsed to 6–12 months |

但**「安全」不等于「自动保住」**。要把这四件变成资产，只有一个条件：**判断必须落成格，不能留在散文里 —— 散文改不动，格可以改。**

But **"safe" is not "kept automatically."** Turning those four into assets has exactly one precondition: **judgment must land in a cell, not stay in prose — prose cannot be edited, cells can.**

---

## 二 · 七条纪律 / II. Seven Disciplines

这七条不是设计出来的，**全是踩过一次错才写进去的**。SKILL.md 里每条都注明固化日期与实测标的；写不出「改完差多少」的，那条其实没被验证过。

None of these were designed up front. **Every one was written down after being burned once.** Each carries a hard-coding date and the ticker it was proven on in SKILL.md; a rule that cannot state "how much the number moved after the fix" has not actually been validated.

| # | 纪律 Discipline | 反面教材 The failure it came from |
|---|---|---|
| 1 | **判断落成格，不落散文。** Judgment lands in a cell, not in prose. | 「HBM 叙事推动股价翻倍」只能点头；「+115% ＝ R +23.5 ／ M 0.0 ／ V +91.7」可以被指着说「你这个 V 用错了尺子」。 “The HBM narrative doubled the stock” invites a nod. “+115% = R +23.5 / M 0.0 / V +91.7” invites someone to point at the V and say you used the wrong ruler. |
| 2 | **每根滑块底下必须挂锚；不挂锚的假设是信仰。** Every slider carries anchors; an unanchored assumption is faith. | 一格价增速挂六个锚（历史 3yCAGR +17%、客户模型 +121%、卖方 +10%、专家 +27%、长协底价隐含 +61%、环比年化 +60%）。取 +65% 是一个选择，**六个来源全留在页面上**。 One price-growth cell carries six anchors. Taking +65% is a choice; all six sources stay visible on the page. |
| 3 | **尺子换了必须写明，跨段不许混用两把尺子。** Declare every change of ruler; never compare two segments measured differently. | 归母跨零时 `ln(PE₁/PE₀)` 无定义，必须退到 P/S 并逐段写出降级链（`ruler` / `ruler_why` 两个字段）。闸门 CK-8 g5 专查这条。 When earnings cross zero the log-PE term is undefined; degrade to P/S and record the chain in two fields. Gate CK-8 g5 exists only to catch this. |
| 4 | **赔率归引擎，概率归人。** Odds to the engine, probability to the human. | 每条 Scenario 是一组滑块参数存档，涨跌幅由引擎跑出来、**不许手写**，质检闸会拿这组参数真跑一遍去对。但概率是手写的 —— **全页唯一不接受自动化的一格。** Each scenario is a saved set of slider parameters; the return is computed, never typed, and the gate re-runs it to check. The probabilities are hand-written — the one cell on the page that refuses automation. |
| 5 | **拆不出来就照实标 [待补]，不假装拆得出。** If it will not decompose, mark it *pending* — do not fake it. | 「其他（技术授权与杂项）」拆不出量价就写成收入指数代理并标 [待补]。**四段里三段有物理量、第四段诚实认输，比四段都编一个量出来更可信。** Three of four segments carry physical volumes and the fourth admits defeat — more credible than inventing a volume for all four. |
| 6 | **对账行是交付物的一部分，不是草稿。** The reconciliation row ships with the deliverable. | Σ 分部 vs 全模型差 **0.000%**；Excel 末行「引擎总收入 − 披露营收」八列全落在 **±0.009 百万元**。勾稽差直接写进表里，不藏。 Segment sum vs full model: 0.000%. The Excel bottom row lands within ±0.009mn across all eight columns. Reconciliation gaps get written into the table, not hidden. |
| 7 | **形式闸管不住经济含义。** Formal gates cannot police economic meaning. | 一份 58 项全过、份额闸五段全不过，结论级错误照样在。闸门自己也会跑不通（`check_consensus` 在美股口径下直接崩）。**真正拦下结论级错误的，到目前还是人。** One report passed all 58 formal checks, failed all five share-implied checks, and still shipped a conclusion-level error. Gates themselves break. What actually stops conclusion-level errors is still a person. |

---

## 三 · 拆解的四把工具 / III. Four Instruments of Decomposition

### 3.1 R / M / V —— 把涨跌拆成三层，三层相加闭合到区间涨跌

Split a price move into **R**evenue, **M**argin and **V**aluation-multiple layers by log decomposition; the three must sum back to the actual segment return. Not an estimate — a closure.

切段的标准是**同一个 regime**，不是「涨了一波」：每段至少六周，且必须有一个转折点把它和上一段分开。每段要写四样 —— 主要矛盾、分析逻辑、主/次因子、**当时的估值锚**。最后一项最容易漏，漏了就没法回答「这一段市场在按什么给价」。

The segmentation criterion is *one regime*, not *one rally*: minimum six weeks, and a turning point must separate it from the prior segment. Each segment records four things — the governing contradiction, the reasoning, primary/secondary factors, and **the valuation anchor in force at the time.** The last is the one people skip; skip it and you cannot answer what the market was pricing on.

**实测样例（美光 MU.O，三年六段）· Worked example:**

| 阶段 Phase | 涨跌 | R 收入 | M 利润率 | V 倍数 | 尺子 | 这一段真正在为什么定价 |
|---|---|---|---|---|---|---|
| ① 周期底部 · 亏损收敛 | +8% | −40.2 | 0.0 | +48.6 | P/S | 两端归母跨零，退到收入口径 |
| ② HBM 叙事启动 | +115% | +23.5 | 0.0 | +91.7 | P/S | 涨的全是倍数，业绩还在亏 |
| ③ 常规存储过剩 · 杀估值 | **−54%** | **+36.0** | 0.0 | −89.7 | P/S | **收入一路上修而股价腰斩** |
| ④ 供需反转确认 | +104% | +11.1 | +30.7 | +62.4 | PE | 三层同向 |
| ⑤ 超级周期主升 | +765% | +344.1 | +394.0 | **+27.2** | PE | 倍数只贡献 27pp，**市场从没给过它成长股倍数** |
| ⑥ 见顶争议 · 利好不涨 | −22% | 0.0 | 0.0 | −22.5 | PE | 段内无新财报，跌幅 100% 来自 PE 25.5→19.8x |

**怎么用.** 读到「涨了 115%」不够，要读到「其中 91.7pp 是倍数」—— 下一次同样的催化会不会再涨，取决于**倍数还有没有空间**。第 ③ 行是全表最值钱的一行：只看基本面的人在这一段会一路加仓。

**How to use it.** "Up 115%" is not a reading; "91.7pp of it was multiple" is. Whether the same catalyst works again depends on whether the multiple has room left. Row ③ is the most valuable line in the table: anyone reading fundamentals alone would have added all the way down.

### 3.2 量 × 价 × 利润率 —— 收入必须是几件 × 几块钱

Revenue must resolve to *units × price*, not a growth rate. The largest segment is **forbidden** from falling back on "revenue index × 1"; it must carry a physical quantity.

改的**不是公司收入，是行业量、价、份额**。黄底那几格全部是能跟人吵的数 —— 机柜多少万台、单机柜多少颗、行业盘子多大、我们占几成 —— 而不是「收入增速给 20% 还是 25%」这种吵不动的数。

You do not edit company revenue; you edit **industry volume, price and share.** The editable cells are the ones people can argue about — how many racks, how many parts per rack, how big the industry pool, what share is ours — not "20% or 25% revenue growth," which nobody can argue about.

一条链五格，每格有数，每格右边挂来源与冲突，**信息分层写进表里：FACT（业绩会）＞ 专家 ＞ 卖方 ＞ 段子**。
Five cells to a chain, each with a number, each with its source and its conflicts attached, and the **evidence tier written into the table: FACT (earnings call) > expert > sell-side > chatter.**

估值锚年还必须**反算隐含份额**去和外部 TAM 对表。锚在 2027 却没把 2027 的量反算成市场份额，就是真缺口 —— 闸把它挂在那里，不让你糊过去。
The valuation anchor year must additionally be **back-solved into implied market share** and checked against an external TAM. Anchoring on 2027 without converting 2027 volume into a share is a real gap, and the gate leaves it flagged rather than letting it pass.

### 3.3 多范式加权 —— 同一份利润，七把尺子各算一遍

Value the same earnings stream under seven paradigms, weight them, and **report the range, not the median.**

有分歧就看区间。两条读数**方向相反**的腿最值钱 —— 全表唯一说「贵了」的和唯一说「便宜了」的，两者之差正是市场在为某一段业务付的溢价。

Where the paradigms disagree, read the spread. The two legs pointing in *opposite* directions are the valuable ones: the only one saying "expensive" and the only one saying "cheap," and the gap between them is exactly what the market is paying for one particular segment.

**弃用的口径也留在表里**：周期股禁用 PEG，权重置 0 但**不删** —— 写明为什么不能用，比悄悄拿掉更可核。
**Retired paradigms stay on the page**: PEG is banned for cyclicals, so its weight goes to 0 — but it is not deleted. Stating why a ruler is invalid is more auditable than quietly removing it.

市值还要**拆成三段来读**：已被实际业绩＋指引锁定的部分 ／ 净现金 ／ 剩下的那部分 —— 最后一段付的是「**这个利润能维持多久**」。
Market cap is read in three slices: the part already locked by reported results plus guidance, net cash, and the remainder — and the remainder is what you are paying for **how long this earnings level lasts.**

### 3.4 矛盾地图 —— 赔率 × 分歧度 × 可证伪性

The contradiction map plots every open question on three axes: **odds** (marker area), **dispersion** across sources (vertical), and **falsifiability** — can you get the number that settles it within 12 months (horizontal). Dispersion is sourced item by item; estimating it is not allowed.

**双槽位**：核心矛盾分两个 —— **定价核心**（赔率最大、分歧最高，但常常验不了，只能控仓位）与**可操作核心**（可证伪性最高，有明确的定案日期）。把两者摆在一起，才不会拿一个验不了的理由去下一个需要日期的注。

**Two slots**: the core contradiction splits into the **pricing core** (biggest odds, highest dispersion — usually unfalsifiable, so it can only be sized down) and the **actionable core** (highest falsifiability, with a dated resolution). Holding both prevents betting on an unverifiable reason when the trade needs a date.

最后收在四个数 —— **期望值 EV ／ 我给的上行概率 ／ 现价隐含上行概率 ／ 两者之差**。差是负的，意思是**市场比我乐观**；真要下注，方向应该反过来。这四个数由手写的概率决定，不是模型算出来的。

It resolves to four numbers: **EV / my probability of upside / the probability the current price implies / the difference.** A negative difference means the market is more optimistic than you are — and the trade, if any, runs the other way. Those four numbers rest on hand-written probabilities, not on model output.

---

## 四 · 三个出口 / IV. Three Outlets

三种交付不是三份文件，是**同一套数据的三个出口**。同一条纪律、同一份 `page_model`，变的只有**读者的权限**。

Three deliverables are not three documents. They are three outlets on the same data, under the same disciplines, from the same `page_model`. The only variable is **what the reader is allowed to change.**

| | **一页纸 · 给自己**<br>One-pager — for yourself | **deck · 给别人看**<br>Deck — for an audience | **Excel · 给要改数的人**<br>Model — for someone who will edit |
|---|---|---|---|
| 读者能做什么 Reader can | 拖滑块，四个分部与七条估值腿同时重算 | 什么也不能改 | 只改黄底格，其余全是公式或链接 |
| 假设怎么改 Assumptions | 拖滑块，滑轨下 ▲ 是并排的锚位 | 改不了，**所以整张量价表必须印在页上** | 只改黄底格 |
| 口径分歧 Definitional conflicts | 决策卡 ＋ 点角标弹出逐字原句 | 附录整张搬，**弃用口径灰化留着** | 每行右侧挂来源与冲突，注明不可入模的那条 |
| 对账在哪 Reconciliation | Σ 分部 vs 全模型，差 0.000% | 量价表末行，八年逐年对账 | 末行勾稽 ±0.009 |
| 体积 Size | ~1.0 MB 单文件 HTML | ~365 KB 单文件 HTML | ~97 KB xlsx |

**硬规则 · The hard rule.** deck 的读者没有滑块可拖 —— **看不到表就等于没有模型**。所以凡是一页纸里「拖一下就能看到」的东西，在 deck 里必须**整张印出来**，不许折叠成「模型显示……」。

A deck reader has no slider. **No table means no model.** Anything the one-pager reveals by dragging must be printed in full in the deck — never collapsed into "the model indicates…".

deck 结构上是**倒过来**的：第 1 页就是结论与盈亏比，第 2 页就是 kill criteria，然后才展开五章；附录紧跟正文，不堆在最后。kill criteria 五条全部**可查数、可证伪**，且第一次校准的日期要写出来。

The deck is inverted: page 1 is the conclusion and the payoff ratio, page 2 is the kill criteria, and only then do the five chapters open. Appendices sit next to the section they support. All five kill criteria must be queryable and falsifiable, with the date of first calibration stated.

Excel 里 **颜色即口径**：蓝＝硬编码实际值，黑＝本表公式，绿＝跨表链接到行业假设，黄底＝可改假设。历史列全蓝、预测列全绿，一眼看得出边界在哪一列。**模型能不能被别人接手，看的不是公式多复杂，是打开就知道哪一格能改、改了会动到哪里。**

In the model, **color is the definition**: blue = hard-coded actuals, black = in-sheet formula, green = cross-sheet link to industry assumptions, yellow fill = editable assumption. History columns all blue, forecast columns all green — the boundary is visible at a glance. **Whether a model can be handed over depends not on formula complexity but on whether, on opening it, you can see which cell is editable and what it moves.**

---

## 五 · 边界 / V. The Boundary

| 已经稳定接住的 Reliably handed over | 接不住，也不该交出去的 Not handed over — and should not be |
|---|---|
| **取数与对账.** 多源交叉，勾稽差直接写进表里，不藏 | **口径取舍.** 同一个数几家给几个值，选哪个是**判断不是查询** |
| **算账.** 赔率、隐含份额、费用桥、三档情景，改一个参数全表重算 | **概率.** Scenario 的概率是手写的，**写错了责任在人** |
| **形式质检.** 四个 checker、逐项跑一遍 | **经济含义.** **闸门全过不等于结论对** |
| **格式化产出.** 同一份研究出三个出口 | **人脉与时序.** 约到谁、什么时候信、什么时候翻脸 |

两条说清楚的边界 · Two boundaries stated plainly：

1. **形式闸管不住经济含义.** 一份 58 项全过、份额闸五段全不过，结论级错误照样在。
   A report can pass all 58 formal checks, fail every share-implied check, and still carry a conclusion-level error.
2. **闸门自己也会误报，也会跑不通.** `check_consensus` 在美股口径下直接崩（无对应数据集）。这类结构性缺口只能**照实降级写**，不能拿 A 股的图硬套。
   Gates themselves misfire and break. Structural gaps get written down as explicit degradations — you do not force an A-share chart onto a US-listed name.

**真正拦下结论级错误的，到目前还是人。**
**What actually stops a conclusion-level error is, so far, still a person.**

---

## 六 · 认知螺旋 / VI. The Cognitive Spiral

一份报告不是终点，是 v_n。上线收标注 → 标注按五种类型分诊 → 每一类对应一个修复动作 → 写回 `page_model` 并版本 +1 → v_{n+1}。**没有回收标注的报告，等于没有被证伪过。**

A report is not a terminus; it is v_n. Ship it → collect annotations → triage them into five types → each type maps to a fixed repair action → write back into `page_model`, increment the version → v_{n+1}. **A report whose annotations were never collected has never been falsified.**

同理，纪律本身也走这条螺旋：每条纪律注明**固化日期**与**实测标的**，并且必须能回答「改完差多少」。做不到的，那条纪律其实没被验证过，只是听起来对。

The disciplines run the same spiral: each carries a hard-coding date and the ticker it was proven on, and must be able to answer *how much the number moved after the fix.* One that cannot has not been validated — it merely sounds right.

---

## 术语对照 · Glossary

| 中文 | English | 说明 Note |
|---|---|---|
| 自持度 | Self-custody ratio | 个人可携带的生产资料 ÷ 日常依赖的生产资料 |
| 第三次圈地 | The third enclosure | 土地 → 知识 → 认知 |
| R / M / V | Revenue / Margin / Multiple | 对数分解，单位百分点 (pp)，三层相加闭合到区间涨跌 |
| 尺子 | Ruler | PE / P/S / EV-EBITDA 等分解口径；换了必须写明 |
| 锚位 | Anchor | 假设格底下并排摆出的外部来源；不挂锚的假设是信仰 |
| 量 × 价 | Volume × Price | 收入必须是几件 × 几块钱，不是增速 |
| 隐含份额反算 | Implied-share back-solve | 把锚年的量反算成市场份额，与外部 TAM 对表 |
| 矛盾地图 | Contradiction map | 赔率 × 分歧度 × 可证伪性 三坐标 |
| 主动矛盾 / 从动矛盾 | Active / passive contradiction | 前者生成上行，后者限制上行、决定节奏 |
| 双槽位 | Two-slot core | 定价核心 vs 可操作核心 |
| 可证伪性 | Falsifiability | 12 个月内能不能拿到判定它的那个数 |
| 分歧度 | Dispersion | 各家口径的方差，逐条取证不许估 |
| 赔率 | Odds | 由引擎跑出来，不许手写 |
| 期望值 EV | Expected value | 由手写概率加权，全页唯一不接受自动化的一格 |
| 现价隐含上行概率 | Price-implied probability of upside | 与我给的概率之差即为下注方向 |
| 勾稽 / 对账 | Reconciliation | Σ 分部 vs 全模型；差额写进表里，不藏 |
| 闸门 / checker | Gate / checker | 形式质检；全过 ≠ 结论对 |
| kill criteria | Kill criteria | 可查数、可证伪，且写明第一次校准的日期 |
| 认知螺旋 | Cognitive spiral | v_n → 收标注 → 分诊 → 写回 → v_{n+1} |
| FACT ＞ 专家 ＞ 卖方 ＞ 段子 | FACT > expert > sell-side > chatter | 信息分层，写进表里而不是留在脑子里 |

---

## 常见提问 · FAQ

| 会被问 Asked | 一句话答 Answer |
|---|---|
| 这些纪律怎么来的？<br>Where did the disciplines come from? | 全是踩过一次错才写进去的。每条注明固化日期与实测标的；**写不出「改完差多少」的，那条其实没被验证过。**<br>Every one came from being burned once. A rule that cannot state how much the number moved after the fix has not been validated. |
| 跑一份要多久？<br>How long does one take? | 一页纸的文件时间戳跨度中位 **2.3 小时**（8 例，1.1–3.4h），含自己看和改的时间。<br>Median wall-clock 2.3 hours across 8 samples (1.1–3.4h), including reading and editing time. |
| 数据会不会编？<br>Could the data be fabricated? | 三条：多源交叉、勾稽差写进表里、checker 拦形式错。**但形式闸管不住经济含义** —— 见第五节。<br>Three defenses; but formal gates cannot police economic meaning — see §V. |
| 闸全过是不是就没问题？<br>All gates green means clean? | 恰恰相反。挂着的项往往是**真缺口不是误报** —— 闸把它挂在那里，没让我糊过去。<br>The opposite. Flagged items are usually real gaps, not false positives — the gate keeps them visible instead of letting them through. |
| 能不能给别人用？<br>Can others use it? | 一页纸和 deck 是单文件 HTML，双击就开、离线可用；Excel 是普通 xlsx。三份加起来约 1.5 MB，邮件能发。**skill 本身要装。**<br>One-pager and deck are single-file HTML, offline-capable. The model is a plain xlsx. ~1.5 MB together. The skill itself must be installed. |

---

## 回到第一页那句话 · Back to the First Slide

这套东西不解决「AI 会不会取代研究员」，它解决的是另一件事：

This does not answer *whether AI replaces analysts.* It answers a different question:

> **当生产资料被外置，你至少要保证「怎么算的」这部分留在自己手里。**
> **When the means of production are externalized, you must at minimum keep *how it was computed* in your own hands.**

**滑块、口径卡、闸门、勾稽行 —— 是同一件事的四个形态。**
**The slider, the definition card, the gate and the reconciliation row are four shapes of the same thing.**
