# 投研成果库 · Equity Research Library

> **投研的难点不是找数据，是把「我以为」降级成可核的算式、可改的假设格、可查数的触发线。**
> *The hard part of research is not finding data. It is demoting "I think" into a checkable formula, an editable assumption cell, and a trigger line you can go look up.*

三类成果，时间尺度不同，问的是同一件事的三段。
Three kinds of output on three time scales — three cuts at the same question.

| | 问什么 · What it asks | 份数 |
|---|---|---|
| **首次覆盖** Initiation | 这家公司**还没定**的那件事是什么、谁在赌哪一边、什么时候能验、赔率多少 | 40 |
| **日度复盘** Daily review | 今天的**定价权归谁**、哪些是锚驱动的 beta、哪些是真 alpha | 2 |
| **投资备忘录** Memorandum | 所以**我买多少、看到哪、错了亏多少** | 2 |

配上方法论（中英文对照）与两份买方模型样本。
Shipped with the methodology (bilingual) and two buy-side model samples.

---

## 目录 · Contents

```
onepagers/          40 份首次覆盖，按行业分 A–F 六组
  ├── A-半导体与电子/          8   芯片设计 / 光芯片 / 电子特气 / 半导体材料 / 光学 / 电子布 / 面板
  ├── B-AI算力与软件/          4   AI 软件平台 / 数据中心 IDC
  ├── C-新能源与电力设备/       6   逆变器 / 锂电正极 / 风电整机
  ├── D-资源与化工材料/        12   钨·硬质合金 / 黄金 / 锂钾 / 铬盐 / 含氟材料 / 添加剂 / 陶瓷材料
  ├── E-汽车与高端制造/         5   整车 / 手工具 / 陶瓷机械与海外建材
  ├── F-消费医药与金融/         5   量贩零食 / 电商代运营 / 医疗耗材 / CXO / 券商
  └── INDEX.md                  ← 全库索引
reviews/            日度复盘 —— 盘后跑，看定价权归谁
  ├── A股收盘复盘/              九章结构，判断带证据编号，次日验证点写死价位
  ├── 美股隔夜复盘/              MD / HTML / PDF 三版，先归因到锚再看残差 alpha
  └── INDEX.md
memos/              投资备忘录 —— 写给决策，第一页就把仓位与赔率写完
  ├── 长盈通-688143.SH             做多 · 叙事期权仓位
  ├── 寿司郎FoodLife-3563.T        做多 · 试仓
  └── INDEX.md
methodology/        深度思考方法论（中英文对照）+ 现场版 17 页 deck（HTML/PDF）
models/             顺络电子 002138 买方模型、三期限研究总纲
```

**先看这几个 · Start here**

| | |
|---|---|
| [`onepagers/INDEX.md`](onepagers/INDEX.md) | 首次覆盖全库索引 —— 按行业找标的 |
| [`memos/INDEX.md`](memos/INDEX.md) | 两份备忘录的评级、目标、赔率与「分歧在哪一格」 |
| [`reviews/INDEX.md`](reviews/INDEX.md) | 两份复盘的当日结论与方法约束 |
| [`methodology/深度思考方法论-Deep-Thinking-Methodology.md`](methodology/深度思考方法论-Deep-Thinking-Methodology.md) | 七条纪律、四把拆解工具、三个出口、边界（中英对照） |

---

## 首次覆盖 · Initiations

**单文件、自包含、可交互的 HTML** —— 双击就开，无外链、无服务器、离线可用，约 1 MB。五章，从后往前读也成立：

A **single-file, self-contained, interactive HTML** — double-click to open, no external links, no server, offline, ~1 MB. Five chapters, readable in either direction:

| 章 Chapter | 回答什么 What it answers | 口径 Standard |
|---|---|---|
| **开篇总结** Summary | 什么类型的公司、赌的是什么、期望值多少、最先断哪一环 | 四问逐问落到算式 |
| **① 基本面图谱** Fundamentals | 钱从哪来、谁在持有、成本结构、卖方预期兑现得怎么样 | 剔除数据商回填的合成区间后再算兑现率 |
| **② 股价复盘** Price review | 三年怎么走的、每一段究竟在为什么定价 | 真实 OHLC，过极值校验 |
| **③ 量×价建模** Q×P model | 收入是几件 × 几块钱、改一个假设全表怎么跳 | 每个分部给到物理量，不用收入指数兜底 |
| **④ 矛盾地图** Contradiction map | **还没定的事，按赔率 × 分歧 × 可证伪排一次序** | **赔率由模型算、概率由人手写**；分歧度逐条取证 |

第四章是**首次覆盖真正的落点**：11 条左右的矛盾摆进三坐标 —— 横轴**可证伪性**（12 个月内能不能拿到判定它的那个数）、纵轴**分歧度**（各家口径的方差）、记号面积正比**赔率**。核心矛盾走**双槽位**：**定价核心**（赔率最大、分歧最高，但常常验不了，只能控仓位）与**可操作核心**（可证伪性最高、有明确定案日期）。最后收在四个数：**期望值 EV ／ 我给的上行概率 ／ 现价隐含上行概率 ／ 两者之差** —— 差是负的就说明市场比我乐观，方向该反过来。

Chapter ④ is where an initiation actually lands: ~11 contradictions plotted on three axes — **falsifiability** (can you get the settling number within 12 months), **dispersion** (variance across sources), and **odds** (marker area). The core splits into a **pricing core** (biggest odds, unfalsifiable, size it down) and an **actionable core** (highest falsifiability, dated resolution). It resolves to four numbers: **EV / my probability of upside / the probability the current price implies / the difference.**

**按行业读 · Read across.** 同一组里的公司共享上下游、共享一套产业变量。看完 D 组的钨与黄金，再看 C 组的正极与风电，问的是同一类问题：**这轮涨价是需求给的还是供给给的，能维持几个季度。**

Names in one group share a value chain and a set of industry variables. The question repeats: **is this price move demand-side or supply-side, and how many quarters does it hold.**

核心信条：**人对图表的认知效率远高于纯文字** —— 每个 section 以图/表起手，正文只做 caption ＋ callout ＋ 角标。
Core tenet: **charts beat prose** — every section leads with a chart or table; prose is reduced to captions, callouts and footnote markers.

---

## 日度复盘 · Daily reviews

两条独立的盘后线。**A股收盘复盘**下午收盘后跑，答「今天的定价权归谁」：三行结论先说清「已确认什么／并不代表什么／答案集中在哪」，每个判断带证据编号，次日验证点写死价位与条件，第二天能直接对答案。**美股隔夜复盘**次日开盘前跑，先把个股波动拆成「跟随板块锚的 beta」与「簇内真正的 alpha」，避免把一次费半普跌讲成 20 个独立故事，再叠预测市场的概率位移。

Two independent post-close lines. The **A-share close review** asks who won the day's pricing power — every call carries an exhibit reference, and next-day checkpoints are written as hard price levels. The **US overnight review** separates anchor-driven beta from genuine alpha before layering on prediction-market probability shifts.

---

## 投资备忘录 · Memoranda

不铺陈公司介绍，**第一页就把仓位、目标价、熊市价、赔率和「我和市场差在哪一格」写完**，后面全是附录，用来支撑第一页的每一个数。六节固定骨架，两份可以横着对读。重心是第四节：分歧必须收敛到**一两个可数的物理量**，不许停在「我更看好」。

No company backgrounder — **position, target, bear case, odds and the single cell where I differ from consensus all land on page one**; everything after is appendix backing those numbers. A fixed six-section skeleton makes the two comparable side by side. Section 4 carries the weight: the disagreement must reduce to one or two countable physical quantities.

---

## 怎么打开 · How to open

这些 HTML 在 GitHub 网页上点开只会看到源码。三种看法：
Clicking an HTML file on github.com shows source, not the page. Three ways:

1. **整包下载** —— 仓库页右上角绿色 **Code → Download ZIP**，解压后进 `onepagers/<行业目录>/` 或 `reviews/<复盘目录>/`，双击任意一份。最可靠，完全离线。
2. **克隆** `git clone https://github.com/tsinggao0410/Equity-Research-yqgao.git`
3. **GitHub Pages**（需仓库公开 + Settings → Pages 选好分支）：
   `https://tsinggao0410.github.io/Equity-Research-yqgao/onepagers/<行业目录>/<文件名>`

`memos/` 下是 PDF，`reviews/美股隔夜复盘/` 另有 `.md` 与 `.pdf` —— 这几类在 GitHub 网页上可以直接看，不用下载。
The PDFs under `memos/`, and the `.md` / `.pdf` under `reviews/`, render directly on github.com — no download needed.

---

## 免责声明 · Disclaimer

本仓库是**个人研究记录**，公开出来是为了让方法可被检验、被指错。覆盖、复盘与备忘录都带**发布时点**（见文件名日期），其中的数据、假设与结论**均未随时间更新**，且大量参数是作者当时的主观取值。

This repository is a **personal research record**, published so the method can be checked and contradicted. Every file carries the date it was produced; **nothing has been updated since**, and many parameters are the author's subjective choices at that moment.

**不构成投资建议。** 文中出现的目标市值、目标价、赔率、期望值与概率，按第四条纪律，**概率一律由人手写** —— 写错了责任在人。请自行核对每一格。

**This is not investment advice.** Target valuations, odds, expected values and probabilities rest on hand-written probabilities per Discipline #4. Verify every cell yourself.
