# 02 · Part1 基本面图谱 — iFind 解析表 → page_model.part1 映射手册

> ★ **2026-07-22 强化：Part1 新增 4 个模块（对齐英维克幻灯片范式），以此块为准：**
> **① 最新财务快照（概览必出）** `part1.snapshot`：iFind `fin` 取**最新单季**收入/归母/毛利率/净利率 + **YoY/QoQ**，及 **TTM 年化**收入/归母。用户强调「单独捞出来、重点看最近状况」。渲 `renderSnapshot`（概览高亮条）。字段 `{latest_q:{period,rev,rev_yoy[小数],rev_qoq,np,np_yoy,np_qoq,gm[小数],nm},ttm:{rev,np,rev_yoy}}`。
> **② 业务/客户里程碑（营收图下·年份对齐）** `revenue.milestones:[{year,cust:["红=客户"],biz:["蓝=业务"]}]`。**必须按年份对齐标注**（在对应年份下方，不是平铺几个 tag——这是用户明确纠正点）。从年报大事记/公告逐年挑：客户导入/一供/进供应商名录=cust；产品/并购/募投/上市=biz。上市过久→营收只取近 8–10 年，早期客户折进 `rev-sub` 说明。渲 `renderMilestones`（年列 grid，宽度对齐营收柱）。
> **③ 股东派系 · 近5年逐季时间序列 + ★上市前融资史（2026-08-12 加）** `shareholders.factions_ts:{periods:["YYYYQn"],series:[{faction,color,values:[百分数,每期]}]}` + `faction_analysis`（一行）。按 nature+研究**逐季**分派系：**原始股东(个人法人) / 国资 / 公募(偏基本面价值定价) / 游资·量化(查历史有无炒作、两轮催化期脉冲) / ETF·被动 / 北向·外资 / 社保·险资 / 散户**（散户=100−其余，保证每期和=100）。逐季用 iFind `holders`/`events` 按报告期取十大股东性质→映射派系%。渲 `renderFactions`（**逐季堆积柱**：历史沿革+时间横向比较）。**只留百分比图 + `faction_analysis` 一行定价权结论——不再出派系明细卡**（用户明确精简）。**★另加 `shareholders.pre_ipo`（融资轮次时间线 + 派系类型判定，渲在堆积图上方，见 §1.2b）**——派系序列只从上市起算看不出「这批股东怎么进来的」，把 IPO 前的稀释史接上。
> **④ 股权结构树** `ownership:{controllers:[{name,role,pct}],platform:{name,pct},direct:[{name,pct}],float_pct,sub_groups:[{group,color,note,subs:[{name,stake,business,location}]}]}`。qcc `get_actual_controller`+`get_beneficial_owners`(实控人+一致行动人+控股平台) + `get_external_investments`(子公司+持股) + `get_branches`/`get_company_profile`(区位/主业)。**子公司按业务分类**（非核心业务 / 核心零部件制造 / 软件系统…，各组 `color` 区分）。渲 `renderOwnership`（实控人→平台→上市公司→分组子公司 树）。**子公司数据不再单列 sub-grid，全部并入 ownership.sub_groups**。
> 派系 pct 与 ownership stake/pct 均为**百分数**(46=46%)；snapshot 的 *_yoy/_qoq/gm/nm 为**小数**(0.30)。

**何时读**：Phase 2（映射）。上游 `fetch_ifind.py` 已把 6 张 iFind 应答解析成 `ifind_tables.json`；本文件教你把它**人工映射**成 `page_model.part1` 的（现 8 块）图数据。取数命令/路由陷阱在 `01-data-recipes.md`，本文件只管**形状转换**。

> 为什么要人工：iFind 是 NL 引擎，列名逐次漂移、分部标签逐年按排名换位、单位是「元」带「万/亿」后缀——这些确定性脚本做不了，必须映射时判断。四张图对应 app.js 的 `renderRevenue / renderHolders / renderDupont / renderCost`，**字段名对不上就画不出**，故每节末尾给「app.js 消费字段清单」，务必逐字对齐。

---

## 0 · 输入与全局约定

**输入文件**：`C:\Users\youqi\Desktop\gyasset\...\_workspace\<ticker>\ifind_tables.json`
结构：`{name, ticker, y0, y1, tables:{...}, errors:{...}}`；原始应答在同目录 `raw\*.md`。

`tables` 六个 key（每个 = `{columns:[], rows:[], query}`）：

| key | 喂给 | 主要列（会漂移，以实测为准） |
|---|---|---|
| `segment_product` | 1.1 营收 | `营业收入-主营业务(元)` + 每个 top-5 一组 `项目名称/项目收入/项目成本/项目毛利/项目毛利率 (按产品)(排名:第N名)` |
| `segment_industry` | 1.1 备选口径 | 同上，按行业 |
| `segment_region` | 1.1 备选口径 | 同上，按地区 |
| `dupont` | 1.3 杜邦 | `权益乘数`/`净资产收益率ROE(...)`/`总资产周转率(次)`/`销售净利率(%)` |
| `cost` | 1.1 total+YoY / 1.4 成本 | `营业总收入`/`营业总收入(同比增长率)`/`营业成本`/`销售费用`/`管理费用`/`研发费用`/`财务费用`/`毛利率`/`销售净利率`/各 `X费用/营业总收入(%)` |
| `holders` | 1.2 股东 | `前十大股东持股比例合计(%)` + rank1–10 `股东名称/持股数量/持股比例/股份性质/股东性质` |

**全局转换规则**（每张图都要）：
- **单位**：分部/营收/费用绝对值是**元** → `/1e8` 转**亿元**，保留 1 位小数。先剥「万」「亿」中文后缀再算（`1.2亿`→`120000000`，`3800万`→`38000000`）。占比/毛利率/费率/ROE 是**百分数值**（如 `23.9` 表 23.9%），**照抄不除 100**（app.js 内部再 `/100`）。持股数量是**股** → `/1e8` 转**亿股**。
- **报告期 → 年标签**：`2024-12-31` / `2024年年报` → `"2024"`（字符串），跨表用同一套年份键对齐。
- **原子标注**：iFind 财报数取 **FACT**；customers/business_tags/events 若来自 AlphaPai/年报口径描述取 **EST（【Estimate】）**；子公司 qcc 数取 **FACT**。缺值一律写 `⚠️未查到`，**不编造、不外推**。
- **cite**：每张图的 `cite:[n]` 指向 `references[]` 里的信源条目（iFind 财报/qcc/AlphaPai），报告期写清。

**★概览区（`#sec-kpi`）三件套**：KPI 条 → 最新财务快照（`part1.snapshot`，单季 + TTM）→ **类型卡**（`summary.type_card`，2026-08-17 石英股份读者反馈新增）。
类型卡＝真β/假β/σ/叙事-题材 + 类型对应的核心参数（β 类：核心叙事线+龙头/中军/后排+K 线方位；σ 类：预期利润率/ROE 历史分位 + PE/PS/PB 分位），
数据层 `python3 scripts/type_card.py --model <page_model> --profile <stock_profile> --write` 从 1.7/1.3/1.4/1.5/2.1b 合成，作者定 `type`——写法与闸门见 **10 §2.8**（它属开篇章，Phase 6.5 最后写，但渲在概览）。

---

## 1.1 营收：分部堆积柱 + 总营收 YoY 双轴 + 历史节点

### 取哪些数
1. **分部**：默认用 `segment_product`（分产品）。逐年行里读 5 组 `(项目名称, 项目收入元, 项目毛利率)`。分行业/分地区仅当产品口径缺失或更能说明公司时替代（口径写进 `caliber`）。
2. **总营收 + YoY**：**从 `cost` 表取**，不是从分部表加总——`营业总收入(元)`→`total[]`（亿），`营业总收入(同比增长率)`→`yoy[]`（%）。
3. **客户/业务标签/节点**：分部表**没有**，来自 AlphaPai 一页纸或年报（见下）。

### 跨年标签归一化（本节最难，务必做「标签映射字典」）
分部表**只返回 top-5**，且**同一业务逐年按排名换位**（如立昂微「半导体硅片」某年 #1、某年 #2），公司自报名称也会微调。直接按「第N名」堆柱会导致同一条业务在不同年份跳色/错位。做法：

1. 通读各年 5 个 `项目名称`，人工归纳出一套**跨年稳定的 canonical 业务集**。
   立昂微示例：`半导体硅片 / 功率器件芯片 / 化合物半导体射频芯片 / 其他`。
2. 建**映射字典** raw名 → canonical名（含同义/改名/口径合并）：

   | canonical | 命中的逐年 raw 项目名称（示例） |
   |---|---|
   | 半导体硅片 | 半导体硅片、硅片、抛光片及外延片 |
   | 功率器件芯片 | 功率器件、半导体功率器件芯片 |
   | 化合物半导体射频芯片 | 化合物半导体、砷化镓射频芯片 |
   | 其他 | 其他业务、其他（含 top-5 之外的尾部残差） |

3. **尾部并「其他」**：每年 5 项里未落入前几个 canonical 桶的、以及 top-5 之外丢失的部分（`营业总收入 − Σ已归类分部`），统一进「其他」。这样每年各 canonical 桶都有值（缺则 0/null），堆积柱跨年颜色稳定。
4. `segments[]` 顺序 = canonical 顺序（决定堆叠层序与配色 index），**逐年 values 对齐 years**。

### 历史节点 events（人工挑 2–4 个）
从 IPO / 重大并购 / 关键客户导入 / 分拆 / 政策落地里挑 2–4 个**营收曲线上讲得通拐点**的，`{year, label}`。`year` 必须**命中 `years[]` 里的字符串**（app.js 用 `years.indexOf(ev.year)` 定位，对不上则不画）。label ≤ ~14 字。来源标 EST/年报。

### 输出（part1.revenue）— 时间作列、维度作行 便于核对
```jsonc
"revenue":{
  "years":["2020","2021","2022","2023","2024"],
  "caliber":"按产品（分部口径，仅披露 top-5，尾部并『其他』）",
  "segments":[
    {"name":"半导体硅片","values":[12.1,18.6,22.4,20.9,23.8]},
    {"name":"功率器件芯片","values":[3.2,4.1,5.0,4.6,5.3]},
    {"name":"化合物半导体射频芯片","values":[0.4,0.7,1.1,1.0,1.2]},
    {"name":"其他","values":[0.9,1.2,1.4,1.3,1.5]}
  ],
  "total":[16.6,24.6,29.9,27.8,31.8],          // 从 cost 表 营业总收入/1e8
  "yoy":[18.5,48.2,21.5,-7.0,14.4],            // 从 cost 表 同比增长率(%)
  "customers":["中芯国际","华虹","士兰微"],       // AlphaPai/年报, 标 EST
  "business_tags":["6-12吋硅片","功率IDM","射频GaAs"],
  "events":[{"year":"2020","label":"科创板 IPO"},{"year":"2023","label":"临港12吋投产"}],
  "cite":[1]
}
```
**自查**：每年 `Σsegments.values ≈ total`（分部只 top-5，允许「其他」吸收残差，但不应为负）。

### app.js 消费字段清单（renderRevenue，逐字对齐）
`years`(必) · `segments[].{name,values}`(必，堆积柱) · `yoy`(右轴线，标签「总营收YoY」) · `events[].{year,label}`(顶部 #号 pin) · `caliber`/`customers`/`business_tags`/`cite`(caption 与 tag 区)。`total` 供核对/Part3 复用，图上不直接画。缺 `years` → 整图显示「⚠️ 未查到 营收拆分数据」。

---

## 1.2 股东：前十大合计时序 + 最新期 top-10 表 + 子公司卡

### 股东（来自 holders 表）
- `periods[]`：各报告期年标签。
- `concentration[]`：`前十大股东持股比例合计(%)` 逐期。**若该列缺**，app.js 会用 `top[]` 各期 holders 的 pct 求和兜底，但**优先直接填**。
- `top[]`：每期一条 `{period, holders:[{name, pct, shares_yi, nature}]}`。
  - `pct` = 持股比例（%，照抄）；`shares_yi` = 持股数量/1e8（亿股）；`nature` = **股份性质**（流通A股/受限流通股）**或股东性质**（国有法人/境外法人/境内自然人…），二选一填最有信息量的（表里「性质」列）。
  - 表格只渲染**最新期**（`top` 最后一条），但 `top` 建议存全期供追溯；`concentration` 必须全期（画时序线）。

### ★1.2b 上市前融资史 + 派系类型（2026-08-12 用户需求固化）→ 落 `shareholders.pre_ipo`

**为什么**：派系逐季堆积图从上市起算，回答不了「原始股东是产业资本还是财务投资人、解禁后会不会走」。把上市前融资过程接进来，并给一个**派系原型判定**，读者一眼知道这票的筹码基因。

**取数路径（按市场）**：
- **A股**：招股说明书「发行人股本演变／历次增资及股权转让」章节＝唯一权威源——RAG 有招股书直接 `rag_query.py search "<标的> 增资 股权转让 投后估值 引入投资者"`；没有则 iFind `search_notice` 拉招股书/上市公告书，或走 `ipo-prospectus-scanner` skill 的资本沿革输出。qcc 工商股东变更记录作交叉（仅大陆主体）。
- **港股**：招股书「History, Reorganisation and Corporate Structure」+「Pre-IPO Investments」章节（PHIP PDF）。
- **美股**：S-1/F-1 的 Principal Stockholders + 融资历史；Crunchbase 类数据只作 EST 交叉，不单独采信。
- 解禁后退出进度（`pe_now_pct`）：A股用最新期十大股东里 PE/VC 主体合计 + 减持公告；查不全标 EST 并在 note 写口径。

**派系类型 `archetype` 四选一（判定规则带数字，写进 `archetype_note`）**：
| archetype | 名称（页面徽章） | 判定（满足多条按 控制权>稀释度 优先） |
|---|---|---|
| `founder` | 创始人/家族控盘 · 产业坐庄型 | IPO 时创始人/家族+一致行动人 ≥40%，上市前外部融资 ≤2 轮且合计 <15%，当前实控人 ≥30% |
| `pe_diluted` | 上市前股权稀释重 · PE 逐步退出型 | 上市前 ≥3 轮融资 或 IPO 时 PE/VC 合计 ≥25%，创始人 <30%；重点跟退出进度（解禁→减持→退干净） |
| `soe` | 国资控股型 | 实控人为国资委/地方国资/央企集团 |
| `dispersed` | 无实控人 · 股权分散型 | 第一大股东 <20% 且无一致行动协议 |

**输出（shareholders.pre_ipo；渲 `renderPreIPO`：类型徽章+轮次时间线+PE退出进度条）**：
```jsonc
"pre_ipo":{
  "rounds":[{"date":"2018-06","round":"B轮","investors":["红杉","高瓴"],"post_val_yi":30,"founder_pct":52.1,"note":"引入战投"}],
  "ipo_founder_pct":38.2,               // IPO 时创始人/家族合计（%）
  "pe_ipo_pct":24.5, "pe_now_pct":6.1,  // PE/VC 合计：IPO 时 vs 当前 → 页面算退出进度条（已退 75%）
  "archetype":"pe_diluted",
  "archetype_note":"上市前 4 轮融资稀释 34pp，IPO 时创始人 38%；PE 合计 24.5%→现 6.1%，解禁两年退出 75%[FACT 招股书+2026Q2 十大股东]",
  "cite":[2]
}
```
纪律：轮次数据全部 FACT（招股书页码进 references）；`pe_now_pct` 允许 EST 但写口径；**查不到就整块不填**（页面渲一行小字「未收录上市前融资史」），不许拿媒体传闻凑轮次。`faction_analysis` 定价权结论要与 archetype 呼应（pe_diluted 型必须回答「还剩多少没退、解禁日历」）。港美股无逐季派系图时，pre_ipo 时间线照出（招股书是结构性可得的），正好补位。

### 子公司（永远走 qcc，绝不用 iFind）→ 落 `ownership.sub_groups`（★勿再填 `part1.subsidiaries`，该键已废弃无渲染）
iFind 查子公司会**静默命中股东数据**。用 qcc 三件套（先 `mcp__qcc-company__get_company_by_query` 锚**法定全名**，再）：
- `get_external_investments` → 参股/控股名单 + **持股比例** `stake`。
- `get_branches` → 分支机构 **注册地** `location`。
- 逐家 `get_company_profile` → **主营业务** `business`（external_investments 不含主业文本）。
仅覆盖中国大陆主体；港美股/境外子公司→年报「主要控股参股公司」via iFind `notice` 或 AlphaPai 补，标 EST。挑 6–10 家**营收/利润相关度高**的，不堆壳公司，**按业务分组**填进 `part1.ownership.sub_groups`（字段与渲染见顶部 ★④，`renderOwnership` 消费；字段名是 `stake` 不是 `stake_pct`）。

### 输出（part1.shareholders；子公司→ part1.ownership.sub_groups 见 ★④）
```jsonc
"shareholders":{
  "periods":["2021","2022","2023","2024"],
  "concentration":[62.3,61.8,60.5,59.1],
  "top":[
    {"period":"2024","holders":[
      {"name":"立昂控股","pct":28.4,"shares_yi":1.71,"nature":"境内非国有法人"},
      {"name":"香港中央结算","pct":4.2,"shares_yi":0.25,"nature":"境外法人"}
      /* …共10 */ ]}
  ],
  "cite":[2]
},
"ownership":{ /* 见顶部★④: controllers/platform/direct/float_pct + */
  "sub_groups":[{"group":"核心制造","color":"#1f4e79","subs":[
    {"name":"立昂东芯","stake":100,"business":"化合物半导体外延与芯片","location":"江苏无锡"},
    {"name":"立昂微电子(临港)","stake":85,"business":"12吋大硅片","location":"上海临港"}]}]
}
```

### app.js 消费字段清单（renderHolders + renderPreIPO + renderOwnership）
`shareholders.pre_ipo.{rounds[],ipo_founder_pct,pe_ipo_pct,pe_now_pct,archetype,archetype_note}`(融资时间线+类型徽章+退出进度条，renderPreIPO；缺整块→一行小字提示)。
`shareholders.periods` + `concentration`(时序线；缺则由 top 求和) · `shareholders.top[last].holders[].{name,pct,shares_yi,nature}`(最新期表，renderHolders) · `ownership.sub_groups[].subs[].{name,stake,business,location}`(股权树子公司分组卡，renderOwnership；`stake` 为百分数值)。**app.js 不读 `part1.subsidiaries`——填了=数据静默丢失**。ownership 缺 → 「⚠️ 未生成 股权结构」。

---

## 1.3 杜邦：ROE 分解四线双轴

直接取 `dupont` 表四列，**无需换算**（口径已干净）：
- `roe[]` ← 净资产收益率ROE(%)，`net_margin[]` ← 销售净利率(%) → **左轴（%）**。
- `asset_turnover[]` ← 总资产周转率(次)，`equity_multiplier[]` ← 权益乘数(倍) → **右轴（× 刻度）**，app.js 用虚线画。

**恒等式说明**（写进 caption 或 callout）：`ROE = 净利率 × 总资产周转率 × 权益乘数`。[Inference] iFind 的 ROE 常为**扣非/加权**口径，而净利率/周转率/乘数可能取一般口径，故三者相乘与 ROE **会有小幅出入，可接受**，不必强行对平。给读者提示：**「周转率(次)/权益乘数(倍)读右轴，ROE/净利率读左轴」**。

```jsonc
"dupont":{
  "years":["2015","…","2024"],
  "roe":[12.4,…,9.8], "net_margin":[10.1,…,14.2],
  "asset_turnover":[0.62,…,0.41], "equity_multiplier":[1.85,…,1.62],
  "cite":[3]
}
```
**app.js 清单**（renderDupont）：`years/roe/net_margin/asset_turnover/equity_multiplier`。缺 `years` → 「⚠️ 未查到 ROE/杜邦数据」。**扰动无关**（Part1 静态）。研发费用 2018/2019 前多为空不影响本图。

---

## 1.4 毛利率分解 · 逐季 · 堆积面积图（上市以来）

> ★★ **2026-08-18 用户定稿，两版之前的「年度双柱＋四线复合图」与中间那版「年度堆积柱」都已作废，勿回退。**

**只问一个问题**：这一季赚到的毛利，最后有多少落进股东口袋，其余被谁拿走了。

```
毛利率 ＝ 净利率 ＋ 销售 ＋ 管理 ＋ 研发 ＋ 财务费用率 ＋ 税费 ＋ 其他
```

- **七层，不多不少**。`税费` ＝ 税金及附加 ＋ 所得税费用（同分母合成一层）；
  `其他` 是**一个桶**，把剩下的全部装进去——减值损失、其他收益（政府补助）、投资收益、
  公允价值变动、营业外收支、少数股东损益。按恒等式反算，所以恒等式**永远严格成立**。
- **毛利率不画成层**，它是**堆积面积的上沿**。
- **必须是面积图不是柱状图**：Chart.js 的堆积折线是**代数累加**（负值照样进 running total），
  上沿恒等于各层之和＝毛利率；堆积柱则把正负段分到零轴两侧，视觉顶 ≠ 总和，
  亏损期公司还要额外画一根记号才读得对。面积图不需要那根记号。
- **必须逐季不是逐年**：费率的结构变化（研发爬坡、补贴退坡、规模摊薄）是季度级发生的，
  年度序列会把拐点抹成一条斜线。
- **纵轴稳健截断**：分母是单季营收，上市初期收入极小的公司会把量域拉到 ±1500%
  （寒武纪 2020Q1 营收 0.12 亿、堆积峰值 938%），最近八季的真实结构被压成贴零轴的一条线。
  页面按**最近 8 季**的堆积上下沿定轴（×1.2 留白），更早的极端季度出界，
  并在图注**逐一点名被截掉的是谁、极值多少**；悬停仍给真值，信息没丢。

### 取数：一条命令，走 iFind 原生单季指标

```bash
python3 scripts/fetch_quarterly.py --name <简称> --ticker <码.SH> \
    --y0 <上市年> --y1 <本年> --listing-year <上市年> \
    --model _workspace/<码>/page_model.json --write
python3 scripts/fetch_quarterly.py --self-test                    # 改口径前先跑，不连网
python3 scripts/fetch_quarterly.py --from-raw _workspace/<码>/raw --model … --write   # 离线复跑
```

**2026-08-18 实测 iFind（688256）把「哪些是真有的」查清楚了**：
`单季度.营业总收入 / 营业成本 / 销售·管理·研发·财务费用 / 税金及附加 / 所得税费用 / 归属母公司净利润`
**每季都有原生值**——**不要自己拿累计差分**。

> ⚠️ **取数陷阱**：同一张返回表里 iFind **同时给出**累计列与单季列且同名
> （`销售费用` 与 `单季度.销售费用` 并存）。脚本对季度字段**强制要求 `单季度.` 前缀**，
> 匹配不到宁可留空也不退回累计列——退回去就是把 Q4 的全年累计当单季画上去。
> 机器闸 CK-8 **d5** 查 `src` 里有没有「单季度」。

### 输出（part1.cost_structure_q）
```jsonc
"cost_structure_q":{
  "quarters":["2020Q1",…,"2026Q2"],     // ★上市首季起
  "listing_year":2020,                  // ★必填，CK-8 d4/d4b 核对起点
  "gross_margin":[%],                   // ＝面积上沿，不单画成层
  "net_margin":[%],                     // ＝最底层
  "sell_exp_rate":[%],"admin_exp_rate":[%],"rnd_exp_rate":[%],"fin_exp_rate":[%],
  "tax_rate":[%],                       // ★税金及附加＋所得税费用，**占营收**，不是实际税率
  "rev_yi":[亿],                         // 单季营收，tooltip 与利润瀑布用
  "src":"iFind 单季度.* 原生指标（非累计差分）",   // CK-8 d5 查这一句
  "caliber":"…", "cite":[n]
}
```
**「其他」不落数据层**，由页面反算 `毛利率 − (净利率＋四费＋税费)`。
第二模式「利润瀑布」取**最新一季**，金额＝单季营收 × 各费率还原。
机器闸：CK-8 **d2**（走季度块）**d2a**（YYYYQn）**d2b**（上沿/底层在）**d2c**（五层齐）
**d3**（「其他」桶体检，常年盈利公司才当硬闸）**d4/d4b**（上市首季起）**d5**（单季原生）。

---

## 1.4b 利润 vs 经营现金流 · 资本开支 · 折旧

> ★ 2026-08-18 新增，同日按「不要随便搞」重做取数口径。编号沿用 2.1b 的老规矩，1.5/1.6/1.7 不后移。

1.4 讲「利润率怎么来的」，1.4b 讲**利润是不是真钱、钱又去了哪**：
① 经营现金流 vs 归母净利润＝利润含金量；② CAPEX vs 折旧＝在扩张还是在维持
（铺下去的产能两三年后以折旧回来压毛利率，接回 1.4）。

**四条线的真实频率不一样，这是本节最要紧的一条**（实测 688256）：

| 线 | iFind 指标 | 频率 |
|---|---|---|
| 经营活动现金流净额 | `单季度.经营活动产生的现金流量净额` | **每季** |
| 归母净利润 | `单季度.归属于母公司所有者的净利润` | **每季** |
| CAPEX | `单季度.购建固定资产、无形资产和其他长期资产支付的现金` | **每季** |
| 折旧与摊销 | `当期计提折旧与摊销` | **只有 0630 / 1231** |

**A 股季报不含现金流量表补充资料，单季折旧在报表上不存在。** 所以**不摊平、不插值**：

- **单季视图只画三条**。折旧不画——半年值摆在单季轴上会被读大一倍，
  那比"估算"更糟，因为它长得像真值。图注给出为什么。
- **滚动四季(TTM)视图才画折旧**，且**只在 Q2 / Q4 有点**：
  `TTM@Q4 = 当年年报累计`，`TTM@Q2 = 本年中报累计 + 上年(年报累计 − 中报累计)`——
  两个都由披露的累计数**精确**凑出。Q1/Q3 没有对应的累计切点，留 `null`。
- **默认落在 TTM 视图**：两个读数（含金量、扩张强度）本来就是滚动概念，单季比值全是噪声。
- `da_disclosure[]` 落**原始披露段**（H1 累计本身 / 全年累计 − 中报累计），图注直接印出来。

**页面读数三格**（一律走 TTM）：利润含金量 `OCF÷归母`（>1 有现金支撑，长期 <0.7 说明利润被应收/存货占住）、
扩张强度 `CAPEX÷折旧`（≈1 只是维持，>1.5 在铺产能）、经营自由现金流 `OCF−CAPEX`。

### 输出（part1.cash_capex）
```jsonc
"cash_capex":{
  "quarters":["2020Q1",…], "ocf":[亿],"np":[亿],"capex":[亿],   // 单季，iFind 单季度.* 原生
  "ttm":{"quarters":[…],"ocf":[],"np":[],"capex":[],
         "da":[亿|null]},                                      // ★只在 Q2/Q4 有值
  "da_disclosure":[{"period":"2025H1","yi":1.461,"covers":["2025Q1","2025Q2"],"src":"中报 现金流量表补充资料（累计）"},…],
  "unit":"亿元","caliber":"…","da_note":"…为什么折旧不是逐季的…","src":"…","gaps":[],"cite":[n]
}
```
**注意 `cash_capex` 里没有单季 `da` 数组**——有值就说明又有人把它摊平了，CK-8 **d6** 会拦；
**d6b** 查 TTM 的 da 是不是只落在 Q2/Q4；**d6c** 查 `da_disclosure` 在不在。
无 `quarters` → 整节隐藏并从目录摘链。港美股脚本会拦（走 `fetch_fundamentals_hkus.py` 的三表腿自行接同样的键）。

---

## 2 · 映射完成后自查（对齐 CK-1）
- [ ] 五张图数据齐（1.1/1.2/1.3/1.4/1.4b）；缺项写 `⚠️未查到`，未编造。
- [ ] 分部标签**已跨年归一**（映射字典建好、尾部并「其他」、每年桶对齐 years）。
- [ ] 单位换算正确：分部/营收/费用 元→亿、持股 股→亿股；占比/费率/ROE 保持百分数值（未除 100）。
- [ ] `revenue.total`/`yoy` 来自 **cost 表**（非分部加总）；`Σsegments ≈ total`。
- [ ] `events[].year` 全部命中 `revenue.years`；`dupont` 四线口径出入已用 caption 说明。
- [ ] `admin_exp_rate` 是**纯管理**（必要时已减研发）；子公司**走 qcc**、法定名已锚定。
- [ ] **1.4 走 `cost_structure_q` 季度块**、起点＝上市首季、`listing_year` 已填、`src` 写明单季原生指标（CK-8 d2–d5）。
- [ ] **1.4b `cash_capex` 已跑 `fetch_quarterly.py`**（整份写入不手改数）：单季无 `da`、TTM 的 da 只在 Q2/Q4、`da_disclosure` 在（CK-8 d6）。
- [ ] **pre_ipo 已填或显式声明查不到**：轮次来自招股书资本沿革(FACT)、archetype 判定带数字、pe_diluted 型给了退出进度（§1.2b）。
- [ ] 每图 `cite` 指向 references；财报数标 FACT，定性/客户标 EST。

**下一步**：Part2 读 `03-part2-price-review.md`（⚡）。
