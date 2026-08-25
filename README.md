# 首次覆盖库 · Initiation-of-Coverage Library

> **投研的难点不是找数据，是把「我以为」降级成可核的算式、可改的假设格、可查数的触发线。**
> *The hard part of research is not finding data. It is demoting "I think" into a checkable formula, an editable assumption cell, and a trigger line you can go look up.*

40 家公司的**首次覆盖**，每一份都把结论拆到**核心矛盾的逻辑推演**为止 —— 不只是「这家公司是干什么的」，而是「**还没定的那件事是什么、谁在赌哪一边、什么时候能验、赔率多少**」。
40 **initiations of coverage**, each carried through to the **core-contradiction reasoning** — not "what does this company do," but "**what is still undecided, who is betting which way, when can it be settled, and at what odds.**"

配上生成它们的 skill、方法论（中英文对照）与两份模型样本。
Shipped with the skill that generates them, the methodology (bilingual), and two sample models.

---

## 目录 · Contents

```
onepagers/          40 份首次覆盖，按行业分 A–F 六组，组内保留 01–40 时间编号
  ├── A-半导体与电子/          8   芯片设计 / 光芯片 / 电子特气 / 半导体材料 / 光学 / 电子布 / 面板
  ├── B-AI算力与软件/          4   AI 软件平台 / 数据中心 IDC
  ├── C-新能源与电力设备/       6   逆变器 / 锂电正极 / 风电整机
  ├── D-资源与化工材料/        12   钨·硬质合金 / 黄金 / 锂钾 / 铬盐 / 含氟材料 / 添加剂 / 陶瓷材料
  ├── E-汽车与高端制造/         5   整车 / 手工具 / 陶瓷机械与海外建材
  ├── F-消费医药与金融/         5   量贩零食 / 电商代运营 / 医疗耗材 / CXO / 券商
  └── INDEX.md                  ← 全库索引：分组总览 + 六张分组表 + 重复覆盖 + 版本时间线
methodology/        深度思考方法论（中英文对照）+ 现场版 17 页 deck（HTML/PDF）+ 演示动线
skills/             equity-onepager-interactive —— 生成上面每一份的 skill，全量
models/             顺络电子 002138 买方模型、三期限研究总纲
```

**先看这两个 · Start here**

| | |
|---|---|
| [`onepagers/INDEX.md`](onepagers/INDEX.md) | 全库索引 —— 按行业找标的，或按编号读方法演进 |
| [`methodology/深度思考方法论-Deep-Thinking-Methodology.md`](methodology/深度思考方法论-Deep-Thinking-Methodology.md) | 七条纪律、四把拆解工具、三个出口、边界（中英对照） |

---

## 两条轴：行业 × 时间 · Two axes

**横着读 —— 行业（A–F）.** 同一组里的公司共享上下游、共享一套产业变量。看完 D 组的钨与黄金，再看 C 组的正极与风电，问的是同一类问题：**这轮涨价是需求给的还是供给给的，能维持几个季度。**

**Read across — by industry (A–F).** Names in one group share a value chain and a set of industry variables. The question repeats: **is this price move demand-side or supply-side, and how many quarters does it hold.**

**竖着读 —— 编号（01–40）.** 编号是**时间序**，也就是方法本身的版本演进：v1 雏形 → v3 → v3.5 → v4.x → v5.0。同一标的被覆盖多次时（中钨高新 ×6、赛力斯 ×3、PLTR ×3、锦浪 ×2、宏和 ×2、湖南裕能 ×2），前后对读就是**核心矛盾的演化轨迹** —— 矛盾有没有被证伪、赔率往哪一侧移、估值锚有没有换尺子。

**Read down — by number (01–40).** The numbering is chronological, and therefore the version history of the method. Where one name is covered repeatedly, successive files trace **how its core contradiction evolved** — falsified or not, odds moving which way, valuation ruler changed or not.

---

## 一份首次覆盖包含什么 · What each initiation contains

**单文件、自包含、可交互的 HTML** —— 双击就开，无外链、无服务器、离线可用，约 1 MB。五章，从后往前读也成立：

A **single-file, self-contained, interactive HTML** — double-click to open, no external links, no server, offline, ~1 MB. Five chapters, readable in either direction:

| 章 Chapter | 回答什么 What it answers | 不许违反的那一条 The rule that cannot be broken |
|---|---|---|
| **开篇总结** Summary | 什么类型的公司、赌的是什么、期望值多少、最先断哪一环 | 四问每问要有算式，不许出现「本节将介绍」这类脚手架 |
| **① 基本面图谱** Fundamentals | 钱从哪来、谁在持有、成本结构、卖方预期兑现得怎么样 | 数据商回填的合成区间必须探测出来剔掉，否则兑现率全是假的 |
| **② 股价复盘** Price review | 三年怎么走的、每一段究竟在为什么定价 | K 线不过校验（最高价 ≥ max(开,收)、不是只有收盘价）就拒绝落盘 |
| **③ 量×价建模** Q×P model | 收入是几件 × 几块钱、改一个假设全表怎么跳 | 最大的分部禁止用「收入指数 × 1」兜底，必须给物理量 |
| **④ 矛盾地图** Contradiction map | **还没定的事，按赔率 × 分歧 × 可证伪排一次序** | **赔率跑引擎、概率手写**；分歧度逐条取证，不许估 |

第四章是**首次覆盖真正的落点**：11 条左右的矛盾摆进三坐标 —— 横轴**可证伪性**（12 个月内能不能拿到判定它的那个数）、纵轴**分歧度**（各家口径的方差）、记号面积正比**赔率**。核心矛盾走**双槽位**：**定价核心**（赔率最大、分歧最高，但常常验不了，只能控仓位）与**可操作核心**（可证伪性最高、有明确定案日期）。最后收在四个数：**期望值 EV ／ 我给的上行概率 ／ 现价隐含上行概率 ／ 两者之差** —— 差是负的就说明市场比我乐观，方向该反过来。

Chapter ④ is where an initiation actually lands: ~11 contradictions plotted on three axes — **falsifiability** (can you get the settling number within 12 months), **dispersion** (variance across sources), and **odds** (marker area). The core splits into a **pricing core** (biggest odds, unfalsifiable, size it down) and an **actionable core** (highest falsifiability, dated resolution). It resolves to four numbers: **EV / my probability of upside / the probability the current price implies / the difference.**

核心信条：**人对图表的认知效率远高于纯文字** —— 每个 section 以图/表起手，正文只做 caption ＋ callout ＋ 角标。
Core tenet: **charts beat prose** — every section leads with a chart or table; prose is reduced to captions, callouts and footnote markers.

---

## 怎么打开 · How to open

这些 HTML 在 GitHub 网页上点开只会看到源码。三种看法：
Clicking an HTML file on github.com shows source, not the page. Three ways:

1. **整包下载** —— 仓库页右上角绿色 **Code → Download ZIP**，解压后进 `onepagers/<行业目录>/`，双击任意一份。最可靠，完全离线。
2. **克隆** `git clone https://github.com/tsinggao0410/Equity-Research-yqgao.git`
3. **GitHub Pages**（需仓库公开 + Settings → Pages 选好分支）：
   `https://tsinggao0410.github.io/Equity-Research-yqgao/onepagers/<行业目录>/<文件名>`

---

## 用这个 skill · Using the skill

```bash
cp -r skills/equity-onepager-interactive ~/.claude/skills/
```

然后说「**帮我把 XX 做成一页纸**」或「**快速了解一下 XX 这家公司**」即可触发。
Then say *"make me a one-pager on X"* or *"help me get up to speed on company X."*

**运行前需要自备的东西 · What you must supply:**

- `scripts/fmp_config.json` 里的 `api_key` **已在公开发布时移除**，请设环境变量 `FMP_API_KEY` 或本地填回。
  The FMP `api_key` **was removed before publishing**. Set `FMP_API_KEY` or fill it back in locally.
- 数据源 client（iFind / AlphaPai / qcc / research-rag）按 `SKILL.md` 顶部说明配置；港美股腿走 `fetch_fundamentals_hkus.py`（东财 + SEC EDGAR），不需要 iFind。
- 本机只有 `python3`：文档里所有 `python scripts/xxx.py` 一律用 `python3` 跑。

---

## 免责声明 · Disclaimer

本仓库是**个人研究过程的记录**，公开出来是为了让方法论可被检验、被指错。所有覆盖都带**发布时点**（见文件名日期），其中的数据、假设与结论**均未随时间更新**，且大量参数是作者当时的主观取值。

This repository is a **record of a personal research process**, published so the methodology can be checked and contradicted. Every file carries the date it was produced; **nothing has been updated since**, and many parameters are the author's subjective choices at that moment.

**不构成投资建议。** 覆盖中出现的目标市值、赔率、期望值与概率，按第四条纪律，**概率一律由人手写** —— 写错了责任在人。请自行核对每一格。

**This is not investment advice.** Target valuations, odds, expected values and probabilities rest on hand-written probabilities per Discipline #4. Verify every cell yourself.
