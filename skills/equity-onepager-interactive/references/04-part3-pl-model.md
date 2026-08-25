# 04 · Part3 — P&L 量×价建模规格（Phase4 ⚡强制）

> 进入 Phase4 前必读。目标：把公司拆成 N 个业务分部，**历史列=财报实际**、**预测列=分部 Q×P×毛利率驱动 + 费用率假设**，跑通用利润桥到净利/EPS，产出可即时联动的 `page_model.part3`。计算引擎已实现于 `C:/Users/youqi/.claude/skills/equity-onepager-interactive/scripts/model_engine.js`（`EONE.recomputePL` + `EONE.runValuation` + 8 范式 `EONE.PARADIGM[key]`），本文是**填数契约 + 引擎行为说明**，不重写引擎。
>
> 血脉来源：收入分部归型与量价推演借鉴 `product-qp-modeler`（14 archetype 的 Q/P/M）；利润桥、blue实际vs yellow假设的诚实分层、估值联动借鉴 `buyside-model-builder`（7 段引擎 + 通用利润桥 + INNIO 驱动）。**但本页引擎是压缩版**：每分部只是一条 `Q×P` 递推线（不做完整 backlog/装机/债务滚动）；需要 backlog roll / install-base roll 的深度建模走 `buyside-model-builder`，此处把滚动动态折进 `q_growth`。

---

## 1. archetype 归型（先归型再建模，归错=数学全错）

### 1.1 决策树（把 14/12 类压成一棵实用树）
先问 **单业务还是多业务**：多业务→拆 N 段，**每段独立归型独立跑 Q×P**（如 BYD=电池 PSC + 汽车 PSC + 电子 BDT + 半导体 CCE）。再对每段顺序判：

| # | 判据（命中即停） | 归型码 | 典型 | Q 的物理含义 / P 的物理含义 |
|---|---|---|---|---|
| 1 | 客户=几个大 OEM，产品是其平台的一颗 BOM 料 | **BDT** | 光模块/HBM/连接器/服务器电源/PCB/激光雷达 | Q=平台出货×单机用量×份额；P=代工晶圆成本+封测+设计摊销+代际/定制溢价 |
| 2 | 终端 TAM 清晰，靠渗透率拐点 <5%→30%+ 爬坡 | **PSC** | 电动车/电池/储能/光伏/机器人/AR-VR/热泵 | Q=TAM×S曲线渗透×单位用量×份额；P=Wright 学习曲线降价 |
| 3 | 客户当产线 capex 买（含半导体硅片/材料） | **CCE** | 半导体设备/**硅片**/锂电光伏设备/检测自动化 | Q=下游 capex×设备价值占比×国产化率×份额；P=核心件成本+集成+研发摊销+代际溢价−国产折价 |
| 4 | 订单/在手 backlog 驱动，多年可见度（backlog/年收>1.5yr） | **A/PJ** | 军工/造船/工程 EPC/航空/油服 | Q=期初 backlog×执行率 或 确认量；P=单项目合同价（本引擎用 q_growth 承载转化节奏） |
| 5 | 装机基数×attach/耗材（razor-blade，后市场/维保） | **C** | INNIO 服务/电梯维保/医疗设备耗材/打印耗材 | Q=期末装机基数；P=单位 attach 收入（$/GW、单机耗材额） |
| 6 | 价格盯交易所/期货，无生物周期 | **CC** | 铜/油气/化工 MDI-TDI/水泥/钢/航运 | Q=行业开工×自身产能×份额；P=边际成本+库存升贴水×期货曲线（强周期→做三档） |
| 7 | 消费重复购买 <1yr 周期 | **MC** | MCS 必选(海天/农夫/伊利)/MCD 可选周期(海底捞/安踏/泡泡玛特)/MCL 奢侈(茅台/LVMH) | Q=人口×渗透×人均频次×份额+新店；P=出厂价×渠道加成×CPI 传导+SKU 升级 |
| 8 | 真订阅（付费客户×ARPU×NRR） | **SS** | Salesforce/ServiceNow/用友 | Q=付费客户数；P=ARPU（×NRR 滚动） |
| 9 | GMV/TPV×take-rate 双边网络 | **NPL** | Visa/美团/拼多多/支付宝/Sea | Q=GMV 或 TPV；P=take-rate（最敏感变量，−50bp≈−10% 收入） |
| 10 | 内容/IP hit 驱动 | **MT** | Netflix/腾讯游戏/米哈游/泡泡玛特 | Q=内容上线×命中率×生命周期；P=单 SKU 价×生命周期×IP 溢价 |
| 11 | 生物生长周期 + 价格周期 | **AG** | 牧原/温氏/双汇/Tyson | Q=出栏量×均重（受 10 个月前能繁母猪锁定）；P=期货价+区域价差+季节性 |
| 12 | 临床/医保/集采驱动 | **PB** | 创新药/仿制/器械/IVD/疫苗/CXO | Q=患者池×渗透×给药频次×报销×份额；P=专利期价→集采(−70~90%)/医保谈判(−30~50%) |
| 13 | 资产负债表驱动（生息资产/AUM/保费×NIM-费率） | **FN** | 银行/保险/券商/东财 | Q=生息资产-AUM-保费；P=NIM-费率-承保利润率 |
| 14 | 预售→结转滞后 12–24 个月 | **RE** | 万科/保利/华润置地 | Q=结转面积；P=结转均价（收入≠当期销售） |
| 15 | 管制定价 + 长久期资产（RAB×准许 ROE） | **UT** | 长江电力/中国移动/NextEra | Q=装机-用户-容量×利用；P=管制电价-资费 |
| 16 | 都不符（兜底最弱） | **L** | — | Q=收入指数、P=[1]（退化为纯收入增速，尽量升级到上表） |

【Inference】归型码写进 `part3.archetype`（自由字符串，如 `"CCE"` 或 `"多业务:电池PSC+汽车PSC"`）；只影响**你往 q/p 填什么物理量、以及 q_growth/p_growth 怎么推**，**引擎数学对所有 archetype 统一**（见 §3）。

### 1.15 拆分穷尽性 + 分业务一量价硬闸门（★2026-07-21 用户反馈固化，先于建模执行）

1. **拆分穷尽**：`Σ segments.rev = hist_actual.rev`（±0.5%）。**机房/物业/PCB/军工特种/租赁等「其他资产与杂项业务」必须显式单列一段承载**（残差段，assets_note 写明该段装了什么资产），不得静默丢弃、不得偷偷并进主业段；对应资产的折旧摊销进 `opex.da` 并在段卡注记。
   **★3.1 YoY 移到右侧列组（2026-08-14 用户要求）**：原来每个金额行下面单开一行 `　YoY`，
   一张表被 YoY 行灌了一倍高度，而且两行之间要来回对眼睛。改成**左值右比**两个列组：
   左边 N 个年份列给数值，一根竖分隔，右边 **N−1 个年份列**给同比（首年没有同比，列组天然少一年），
   两组各自带一行组标题。**比率行给的是 pp 不是 %**（毛利率从 36.5% 到 28.0% 是 −8.5pp 不是 −23%），
   由 `opt.yoyMode:'pp'` 指定：毛利率／净利率／隐含费率／拆分比例 λ 全走 pp，金额与量价走 %。
   **费用与成本行整列为负**，同比按绝对值算（「费用 YoY +20%」＝费用涨了 20%，不是跌）。
   **核心变化上色，A 股口径涨红跌绿**：金额行 |YoY|≥20% 上色、≥50% 再加粗；比率行 |Δ|≥2pp 上色、≥5pp 加粗。
   ⚠️ **不要复用 `.pos/.neg` 或 `p.good/p.bad`**——本页调色板 `--good` 是绿、`--bad` 是红，
   语义名与 A 股方向相反，照着语义名改必反；已另起 `.pl-up`（红）/`.pl-dn`（绿）/`.pl-hot`（加粗）三个类。
   表宽翻倍后 `#tbl-pl` 开横向滚动，序号列与项目列 `position:sticky` 粘住，滚到右边仍知道在看哪一行。

   **★3.1 利润表版式（2026-08-12 重排为人类阅读顺序，app.js `renderPL` 已实现，钩稽不放松）**：左侧**序号列**，五个总分块——`1 营业总收入(TOPLINE)`→`1.x 分部收入`(含量/价子行；母段 1.k + 子段 1.k.1/1.k.2)→`−营业成本`→`2 毛利汇总(=1−成本=Σ2.x)`→`2.x 分部毛利+YoY+毛利率`→`3 费用桥(3.1 销管/3.2 研发/3.3 减值)`→`4 利润链(EBIT→D&A→EBITDA→±营业外→税→少数股东)`→`5 归母净利润(+净利率/EPS)`。运行时双闸门：Σ1.x 对 1 差>0.5% 亮红；Σ2.x 对 2 差>5% 亮红（仅分部毛利可算年份）。**分部毛利率缺失的段在 2.x 显式渲「未拆」行，不静默省略**。
2. **分业务一必拆真量价**：**收入最大的分部禁止 `q=收入指数、p=[1,…]` 的 L 兜底**——必须给物理量（出货量/装机/GMV/客户数…按 §1.1 该 archetype 的物理含义）×价（ASP/单价/take-rate），来源=纪要/卖方模型/行业数据（RAG 优先），标 EST。拿不到就去找（`rag_query.py facts <标的> 出货量|ASP`、Comein 纪要、AlphaPai 质检），找遍仍无才允许降级且必须在 `model` 里声明——页面会对降级段自动打 ⚠️「未拆物理量价，仅收入外推」。
3. **每段必填 `segments[].model`（细分建模卡）**，页面据此自动生成分部模型章节。**★编号改制（2026-08-12）：分部不再各占一个 3.x**——**3.3（无 narrative_map 时 3.2）＝「分部建模与计算」总节（h2），每个分部是孙级小节 3.3.1 / 3.3.2 / …（h3）**；核心假设/加权估值固定 **3.4 / 3.5**（无叙事映射时 3.3 / 3.4），编号不随分部数漂移，TOC 渲三级缩进：

| model 字段 | 必填 | 内容 |
|---|---|---|
| `q_def` / `p_def` | ✓ | 量/价的物理定义（Q=什么物理量、P=什么价格口径；以收入指数代理时写明+待补什么数据） |
| `q_unit` / `p_unit` | 可选 | 单位短标签（渲进 3.1 利润表 量/价子行行名） |
| `logic` | ✓ | **建模方法**：驱动树（下游×用量×份额→量；结构/年降→价）+ 预测逻辑一句账（可信 HTML，`<br>`分行） |
| `assets_note` | ✓ | **资产/产能注记**：该段挂了哪些产线/机房/物业资产、资本开支载体、折旧去向 |
| `q_anchors[]` / `p_anchors[]` / `gm_anchors[]` | 主力分部✓ | 类比锚 `{label,v}`（v 小数）：**q/p 锚=增速**（行业增速/大哥增速/卖方一致预期/年降率）→ 渲成分部量价图**虚线锚**+假设滑块**▲刻度**；**gm 锚=毛利率水平值**（如可比公司GM 0.42）→ 只进滑块▲刻度+锚图例（量纲不同不进增速图）；历史3yCAGR/历史均值 由 app.js 自动加，不用手填 |
| `seg_val` | ✓ | **分部估值** `{method,profit_yi,mult,mcap_yi,note}`：该段自己挑锚（PE/对标/终局/EV-EBITDA），与 SOTP 行逐一对齐（主业 base 与期权行的映射写进 note） |
| `driver_focus` | ✓ | **当下逻辑驱动标注** `{strength:'core'|'support'|'weak', targets:[{param:'q'|'p'|'gm'|'rev', years:['2026E',…]}], note, verify, ev:['E2']}`：**全模型有且只有一段 `core`（当下逻辑最强的分部）**——章节标题挂「★当下逻辑最强」徽章、面板加框、TOC 加★；`targets` 指明逻辑作用在哪个参数（量/价/毛利率的YoY）×哪个时点（明年/后年），次级模型表对应单元格**黄底高亮**；`note` 一句话说清作用机制，`verify` 写兑现验证点（季度看什么变量），`ev` 挂原句证据 id。量价未拆段的 `q` 目标自动落到收入YoY行 |
| `driver_chain[]` | core 段✓ | **驱动链逐步算账**（§1.17）：`[{step,expr,val,tag,ev,note,out}]`——外部物理量 → 本段收入，一步一行 15px 大字，末步 `out:true` 高亮 |
| `calibers` | 有口径分歧必填 | **口径对账表**（§1.17）：`{subject,chosen,chosen_label,why,spread,ev,rows:[{caliber,raw,norm,conv,src,date,ev,status}]}`——同一个数不同口径差多少 / 选哪个 / 为什么 |
| `evidence[]` | core 段✓ | **RAG 原句卡**（§1.17）：`[{id,doc_id|file,page,date,type,src,confidence,quote,implication,used_in}]`——逐字原文 + 我的推论分层；`q_ev/p_ev` 与各处 `ev` 字段按 id 引用它。**取原文两条路**：有 `doc_id`→页面渲 `rag_query get_doc` 命令；embedding 配额挂掉导致工作区无 `catalog.jsonl`（get_doc 会失败）时填 `file`=原件相对路径→页面渲路径+复制按钮 |
| `fragile` | core 段建议 | **最脆的一格**：这段模型最先被打破的地方（哪个参数/哪条钳制），渲在段末小结红字 |
| `cite` | 建议 | 指向 references 的信源角标 |

**次级模型表（每分部一张，renderSegTables 自动渲）**：年为列（灰底=历史/米底=预测），行= 量/量YoY/价/价YoY/收入/收入YoY/分部毛利率（量价未拆段只出收入与毛利率行）；预测列随核心假设滑块联动；`driver_focus.targets` 命中格黄底+描边高亮——**用户口径：分部就该长成「几个次级 model 的表格」，一眼看到逻辑作用在哪一格**。

#### 1.15a ★零历史分部不要硬塞进 `segments[]`（2026-08-14 阳光电源 AIDC/SST 固化）

新业务（阳光的 SST/AIDC）历史收入为 0 时，直觉是单开一段。**别开**：
`model_engine.js` 的预测递推从 `last(hist.q)` 起步，`hist.q=0` 会让整段预测**恒为 0**；
`derive`+`splits` 虽支持 `share_hist:[0,0,0]`，但会把子段的量绑死在母段上，语义扭曲。

**可行且诚实的做法**：把新业务并进它**会计上真正归属**的那个分部，用 **p（分部收入 ÷ 该分部真实物理量）上行**承载，
再在 `driver_chain` 里**显式拆开** `p = 老业务 ASP + 新业务收入 ÷ 物理量`。
阳光把 SST 放进「光伏逆变器等电力电子转换设备」，p 从 0.2177 走到 0.2590 元/W（2028E），隐含 SST 收入 76.5 亿——
一眼可读，且 `q×p` 恒等于分部收入，不破 CK-3 的量价闭合。

`driver_chain` 里那两步长这样（阳光实跑）：
```
step3  逆变器自身 ASP        0.2155 元/W（年降 1%）
step4  SST/AIDC 收入 2026E   9.2 亿元
step5  复合单价 p = (逆变器收入+风电+SST) ÷ 光伏 GW   0.2221 元/W（+2.0%）
```
**不这么拆就会出事**：读者看到「逆变器 ASP 三年涨 19%」会以为是提价，实际是结构。
`p_def` 里必须写清 p 是复合口径，`fragile` 里点名「p 的上行全靠 SST，SST 不来 p 就回到年降」。

### 1.16 叙事 ↔ 分部映射（`part3.narrative_map`，★2026-07-21 用户反馈固化）

**公司披露的 segment 与现实世界的叙事/Driver 之间永远有 gap**（例：顺络的 AI 电感藏在披露口径「电源管理」里，钽电容藏在「汽车储能专用」里）——必须显式建一张映射表说清：**之前的叙事和现在的叙事各作用在模型的哪些分部、怎么作用（机制）、程度如何（强度）、什么时点兑现**。页面渲为 **3.2 节**（有 narrative_map 则分部模型/假设/估值编号自动顺延）。

```jsonc
"narrative_map":{
  "note":"一句话点破 公司口径 vs 叙事 的 gap 在哪(哪个叙事藏在哪个披露科目里)", "cite":[n],
  "eras":[
    {"era":"旧叙事 2023-2024","name":"消费复苏+国产替代","status":"已兑现·钝化",
     "impacts":[{"seg":"<segments.key>","param":"量|价|毛利率|量+价",
                 "timing":"2023-2025(已发生)|2026E-2027E","strength":1-3,   // ●○○ 弱 / ●●○ 中 / ●●● 强
                 "how":"作用机制一句账(原始材料推演口径,数字+信源)"}]},
    {"era":"现叙事 2025H2-(当前)","name":"…","status":"兑现早期|兑现中|证伪中", "impacts":[…]}
  ]}
```
填写纪律：每条 impact 的 `how` 必须是「机制+数字+信源」（不是空话）；`strength` 与 Phase3 阶段复盘、`driver_focus` 三处互洽（现叙事 ●●● 的分部 = driver_focus core/support 段）；旧叙事必须写`status`（已兑现/钝化/证伪），防止拿旧故事撑新估值。

4. **假设可视化铁律**：量增速/价增速的预测**必须有可类比的抓手**——每个主力分部至少 1 个外部锚（行业/大哥/卖方）+自动历史锚；光拍一个增速数字不给锚 = CK-3 不过。

5. **★核心模型表 + 修改方式不许丢（2026-08-12 用户打回固化）**。用户原话「为什么核心业务的建模丢失了，没有办法展示核心模型表和修改的方式」——两条硬保障：
   - **每个分部（尤其 core/最大分部）的次级模型表必渲**：`renderSegmentModels` 对 `segments[]` 逐段生成，`segments` 为空或某段缺失＝页面大红 datagap + CK-3 不过。注入层（§5.5 算量器）**只许追加面板，不许替换/删除该段的分部模型章节**——外部 driver 面板是模型表的上游输入，不是替代品。
   - **「修改的方式」在段内自足**：步骤④模型表下方内嵌 `✎ 改本段假设` 滑块组（`segInlineKnobs`，core 段默认展开、其余折叠），与 3.4 核心假设区**同一 data-path 镜像联动**（`bindRangeInputs` 文档级委托，改哪边都同步+recompute）。验收：在 3.3.x 段内拖滑块 → 该段模型表、3.1 利润表、估值区 DOM 同步动。

### 1.17 Driver 三件套：驱动链 + 口径对账 + RAG 原句（★2026-07-25 用户反馈固化）

**用户反馈原话口径**：分部里的 **Driver 字太小、逻辑没说清**——要么**字放大**，要么**把逻辑说到能追溯**：
「link 到先验给的 RAG 库原句或 RAG 原文，然后不同口径的区别和选择」。两条都做了：

**（a）字号纪律（模板已改，不要再调小）**：`.sm-body/.sm-logic` **14.5px**（正文 15.5px，几乎同级）、`.dc-step` 驱动链 **15px**、`.drv-note` 逻辑作用点 **14px**、`.cal-why` 口径选择理由 **14px**、`.ev-card blockquote` 原句 **14px**；只有「勾稽=Q×P×factor」这类机械说明降到 `.sm-mini` 12.5px。**Driver 是本节认知主体，不是脚注**。

**（b）`driver_chain[]` 驱动链——把「一段散文逻辑」变成「一串可核的算式」**
```jsonc
"driver_chain":[
 {"step":"① 上游芯片出货","expr":"昇腾 910 系列 2026E 出货 100 万张 × 910C 占比 62%","val":"62 万张","tag":"EST","ev":["E2"]},
 {"step":"② 每卡用量","expr":"每张加速卡配套 1.4 套（机内互连+背板）","val":"87 万套","tag":"EST","ev":["E1"],
  "note":"用量口径＝每卡份，与 ASP 分母一致；换每柜口径必须同步换 ASP"},
 {"step":"③ 份额","expr":"× 华丰份额 28%（二供）","val":"24.4 万套","tag":"EST","ev":["E2"]},
 {"step":"④ 混合 ASP","expr":"× 1,800 元/套（每卡口径归一后中枢）","val":"4.39 亿","tag":"EST","ev":["E1"]},
 {"step":"⑤ 需求盘→确认收入","expr":"需求盘 4.39 亿 + 非核心 11.2 亿；产能上限 18.0 亿 → min(需求,产能)","val":"15.6 亿","out":true,
  "note":"钳制未激活；拉到 130 万张则触顶，此时改需求侧参数不动收入"}]
```
纪律：**每步都要有 `val`**（读者能顺着数字往下核）；数字来自纪要/研报的步骤必须挂 `ev`；末步 `out:true`（渲成 accent 底）；有 min/clamp 钳制的段在末步 `note` 里写明钳制状态（呼应 §5.5「正确地不动必须可见原因」）。

**（c）`calibers` 口径取舍——回答「同一个数为什么有好几个值、你用哪个」**
★2026-07-25 第三轮反馈：原来的 6 列宽表格「很丑、不符合人类认知的顺序和逻辑」——**表格已废弃**，改渲**决策卡**，顺序＝读者真实提问顺序：
`① 这是哪个数（subject + N 种口径）→ ② 差多少（刻度条把倍差画出来）→ ③ 我用哪个·为什么·用错的代价（结论先给）→ ④ N 种口径各自的账（采用在前，弃用视觉降级）`

```jsonc
"calibers":{"subject":"国产化率（本模型第 ③ 步）","unit":"%","chosen_label":"品类内金额口径（分母＝该品类中国盘金额）",
 "spread":"10% ~ >65%（差 6.5 倍，全部来自分母范围与计量单位，不是谁对谁错）","ev":["E2","E3"],
 "why":"本模型第 ② 步分母是「五品类盘金额」＝WFE×占比，所以第 ③ 步必须同为品类内金额口径…",
 "cost_if_wrong":"用全口径 10% → 装备收入压到 ~100 亿量级（实际 476 亿）；用数量口径 65% → 推到 700 亿以上。不是看多看空，是量纲错。",
 "rows":[
  {"caliber":"品类内金额口径（本模型采用）","raw":"刻蚀 46%/薄膜 45%/炉管 40%/湿法 50%/注入 35%（2026E）","norm":"同左（基准口径）",
   "v":46,"v_lo":35,"v_hi":50,"short":"品类内金额 35–50%",     // ← 刻度条用
   "conv":"2025A 由东吴品类实拆反算校准…","src":"自算（东吴实拆÷品类盘）","date":"2026-04-21","ev":"E4","status":"chosen"},
  {"caliber":"全口径：国产设备供应量 ÷ 中国设备总采购开支","raw":"~10%","norm":"不可用","v":10,"short":"全口径 10%",
   "conv":"分母含光刻/量检测/CMP 等华创不做的品类 → 量纲不同","src":"专家纪要 0711","date":"2026-07-11","ev":"E2","status":"rejected"},
  {"caliber":"数量口径：新建厂国产设备采购台数占比","raw":">65%（华虹九B 预期）","norm":"不可用","v":65,"short":"数量口径 >65%",
   "conv":"分子分母都是台数、不含单价；且只对单一新建厂","src":"代工厂调研 0720","date":"2026-07-20","ev":"E3","status":"rejected"}]}
```
渲染规则（`calScaleHTML`/`calHTML` 已实现，填数时按此预期）：
- **刻度条**需 ≥2 行有 `v`；`v_lo/v_hi` 同时给则画区间带（如采用口径跨品类 35–50%）；两端**差 >10 倍自动切对数轴**；顶部 `short` 作刻度标签（**`short` 里已含数字就不再重复渲一行数值**）；底部居中渲「跨口径差 N×」红字＝这块的**冲击点**。
- **差 <1.5 倍不画条**，改渲一行「✓ 这些口径彼此互证：A vs B（差 x%），任一层都能当锚」——1.1× 的条是噪音（002371 的出货台数表即此形态：整机反推 2,400 vs 月产年化 2,400–2,700）。
- 无 `v` 的行照常进明细（如「腔体数口径」无可比数值），只在卡里说明为什么不能用；`status` 决定视觉：`chosen`（绿旗＋白底＋「＝本模型基准口径」）/ `ref`（灰旗）/ `rejected`（灰化＋原始数删除线＋「不可直接入模」）。
- `status:'chosen'` 的行自动排最前；`why` 缺失打红闸；`cost_if_wrong` 是「用错会怎样」，**要写成量级后果**（收入从 476 亿飘到 100 或 700 亿），不要写"会不准确"这种废话。
- 触发条件不变：**同一参数在不同材料里出现 ≥2 个不同数**（每套/每卡/每柜、全口径/品类内/数量口径、含税/不含税、并表/权益…）→ 必须建卡。

**（d）`evidence[]` RAG 原句卡——把结论 link 回原文**
```jsonc
"evidence":[{"id":"E1","doc_id":"minutes_20260514_zx_ai","page":"p4","date":"2026-05-14","type":"minutes",
  "src":"中信电子 昇腾链专家电话会","confidence":"high","used_in":["q","p"],
  "quote":"910C 单卡对应的高速线模组价值量按整机柜摊到每卡约 1,700–1,900 元，若按每柜口径报价则是 5.5 万上下，两者说的是同一件事，只是分母不同。",
  "implication":"每卡口径 ASP 中枢取 1,800 元；专家的『每柜 5.5 万』÷32 卡=1,719 元与之互证，不是独立第二锚。"}]
```
- **`quote` 必须逐字**（从 `rag_query.py get_doc <doc_id> --text` 拷，不许转述、不许润色）；`implication` 是**我的推演**，页面上标「→ 推论（我的推演，非原文）」与原句物理分离——**原文与推论不许混在一句里**。
- `type`：minutes/report/model/memo/news/expert/company/data；`confidence`：high/mid/low（单一渠道未交叉 = mid 起）。
- 引用方式：`q_def`→`q_ev`、`p_def`→`p_ev`、`driver_chain[].ev`、`calibers.rows[].ev`、`calibers.why→ev`、`driver_focus.ev`——都写 evidence 的 `id`，页面渲成可点 `[E1]` 角标（点开→展开原句卡+滚动闪烁）。id 没登记会渲成红色 `[Ex]`，CK-3 视为缺证。
- 页面自动给每张卡生成**取原文命令** `python scripts/rag_query.py <rag_ws> get_doc <doc_id> --text`（一键复制）——读者/未来的我都能回到原件；`rag_ws` 取 `feedback.rag_ws`（默认 = 裸代码）。
**（e）阅读动线：段内 1→6 编号 + 段末小结（★2026-07-25 第二轮反馈固化）**
用户反馈原话：「**缺乏顺序和标注的逻辑（顺序感）**……东一块西一块的，我既不知道该从哪里开始看，不清楚阅读的顺序，也不知道看到哪里才算结束。」所以分部章节不再是并列的块堆，而是**一条有编号的动线**（`renderSegmentModels` 自动排）：

| # | 步骤 | 缺省行为 |
|---|---|---|
| 1 | 怎么建模：量价物理定义 + 驱动逻辑（`q_def/p_def/logic/assets_note`） | 恒在 |
| 2 | 驱动链：外部物理量 → 本段收入（`driver_chain`） | 无则跳过；core 段无则打红 |
| 3 | 口径取舍（`calibers`） | 无则跳过（编号自动前移） |
| 4 | 次级模型表（随滑块联动 + 黄底命中格 + **★段内 ✎ 改假设滑块**，core 段默认展开） | 恒在 |
| 5 | 量价增速 vs 类比锚图 | 恒在 |
| 6 | 分部估值（`seg_val`，与 SOTP 对齐） | 恒在 |
| ✓ | **段末小结**：算出来什么（首预测年收入/YoY/分部估值，**活数字**）· 往后盯什么（`driver_focus.verify`）· 最脆的一格（`fragile`）· 原句 chips · **→ 下一段/下一节** | 恒在 |

- 面板顶部渲「阅读顺序」chips 条（可点跳 `#seg<si>-s<k>`）；章级另有 `#p3-path`「本章怎么读 1→N，加权估值=终点」。
- **同一句话不出现两遍**：`driver_focus.note` 只写机制，跟踪项写 `verify`（只渲在小结），别在 note 里再抄一遍。
- 小结里的收入/YoY/分部估值走 `data-segsum-*` 由 `renderSegTables` 每次 recompute 刷新——**不许写死**（拖完滑块小结挂旧账＝CK-3 不过）。

**（f）原句一律走浮层，不占正文版面（同上轮反馈）**：用户原话「原文可以浮在另外一个表面上……不然无限往下拉原文的长度会很难受，可以做成超链接、小浮窗的形式」。实现：正文只留 `[Ex]` 角标与 chips（一行），点击 → `#evpop` 浮层（mask + 居中卡 + 内部滚动），层内分「逐字原文 / 我的推论」两个标签块、`‹ ›` 在本段证据间翻页、底部一键复制取原文命令或原件路径，Esc/点遮罩/✕ 关闭，←/→ 翻页。**不要再把原句 inline 展开在正文流里。**

- **无 RAG 库时**：evidence 仍要写（`doc_id`/`file` 都留空 → 页面标「⚠️ 无 doc_id/原件路径(非 RAG 来源)」，`src` 写清 iFind/AlphaPai/公告 + 日期），别因为没建库就退回「无出处论断」。
- **★索引没建成的工作区（embedding 403）**：`rag_query get_doc` 依赖 `index/catalog.jsonl`，而该文件在 build_index 的嵌入步之后才写——配额挂掉时它不存在，get_doc 必失败（002371 实测）。这种工作区一律填 `file`（如 `data/src/2026-07-11_….md` 或 `data/normalized/<id>/content.md`），页面给路径+复制按钮；充值重建索引后再补 `doc_id`。

### 1.2 收入搭法 ≠ 估值方法（硬规则，进 Phase5 前锁死）
- 默认 EV/EBITDA 只给 **BDT/PSC/CCE/CC/C/MC/UT 类工业股**。
- **FN 金融** → PB-ROE（银行 EV 无定义，禁 EV/EBITDA）；**RE 地产** → PB/NAV 折价；**亏损期 SaaS/早期** → EV/S 或用未来盈利年的 PE-link（EBITDA 可能为负，EV/EBITDA 无意义）。
- [Risk] 给亏损/金融/地产套 EV/EBITDA 是典型错误，Phase5 权重必置 0 或不列该范式。

---

## 2. 通用利润桥（历史=实际，预测=公式）

所有 archetype 共用同一条桥；多分部时**每段各自 GM 算毛利再汇总**，费用/税在合计层。桥的顺序（引擎 §3 严格照此走）：

```
Rev（分部 Q×P×factor 汇总）
 − COGS  = −Rev × (1 − 毛利率)
 = 毛利 GP
 − SG&A  = −Rev × 销售费用率
 − R&D   = −Rev × 研发费用率
 (+ 其他经营损益 other_op)
 = EBIT
 + D&A   = EBITDA
 (+ 其他非经营 other_nonop) − 净利息 net_interest
 = 税前 pretax
 − 税     = −pretax × 税率
 (− 少数股东损益 = −pretax × minority_rate)
 = 净利 → EPS = 净利 / 总股本 shares_yi
```

### 2.1 hist_actual / opex 字段来源（iFind fin 为主，Phase1 `fetch_ifind.py` 产物里取）
> **单位/口径铁律**：金额=亿元；`hist_actual.gross_margin/sga_rate/rnd_rate` 与 `opex.*_rate/tax_rate` 用**小数**（0.24），segment `hist.gm`/`assume.gm` 也用小数；`part1` 里的占比/毛利率是百分数值（23.9），此处不同，别混。

| part3 字段 | 单位 | 来源（iFind） | 说明 |
|---|---|---|---|
| `hist_actual.rev[]` | 亿 | 营业总收入 /1e8 | 与 part1 总营收对齐 |
| `hist_actual.gross_margin[]` | 小数 | 销售毛利率 /100 | 优先「销售毛利率」 |
| `hist_actual.sga_rate[]` | 小数 | 销售费用率 /100（**建议填 销售+管理 合并率**） | 引擎按单一费率承载；页面 3.1 该桥行标签为「−销售及管理费用(承载=sga_rate口径)」——填了什么口径 note 里写清，预测 `opex.sga_rate` 同口径对齐 |
| `hist_actual.rnd_rate[]` | 小数 | 研发费用率 /100 | 2018/2019 前多为空→标 `⚠️未查到`，不编造 |
| `hist_actual.ebit[]` | 亿 | 营业利润/EBIT /1e8 | 缺→引擎用 `gp−sga−rnd` 兜底 |
| `hist_actual.da[]` | 亿 | 现金流量表 折旧+摊销 /1e8 | 缺→引擎按 0（则 EBITDA=EBIT，偏低，标注） |
| `hist_actual.ebitda[]` | 亿 | 披露或 ebit+da | 缺→引擎用 `ebit+da` |
| `hist_actual.net_profit[]` | 亿 | 归母净利润 /1e8 | 历史净利直接采信此值 |

| `opex` 字段（预测期）| 单位 | 填法 |
|---|---|---|
| `sga_rate` | 小数 | 历史销售费用率外推；**可填标量或长度-1 数组广播为常数**，或长度-F 逐年 |
| `rnd_rate` | 小数 | 同上 |
| `tax_rate` | 小数 | 有效税率历史均值（如 0.15）；标量广播 |
| `da[]` | 亿 | 折旧摊销预测（长度-F 或标量）|
| `net_interest[]` | 亿 | 净利息，**正数=净支出**（财务费用近似）|
| `other_op[]` (可选) | 亿 | 其他经营损益 |
| `other_nonop[]` (可选) | 亿 | 其他非经营损益 |
| `minority_rate[]` (可选) | 小数 | 少数股东损益/税前；并表非全资高占比时填，否则省略 |

> 广播与滑块层：引擎 `at()` 支持 标量/长度-1/长度-F 三种写法；app.js `boot()` 里 `normalizeModel()` 会把 **opex 标量物化成 `[x]`**、把 **assume.q_growth/p_growth/gm 补齐到 F 长**（尾值延展）——所以三种写法都安全，但建议 assume 直接写满 F 个值（滑块逐年编辑，语义最清晰）。

[Risk] **历史「税」行是 plug**：引擎历史列 `pretax=ebit`、`tax=ebit−net_profit`，即历史那一行「税」实际是 `营业利润−归母净利` 的合并差（含真税+利息+少数股东+非经营），**不是纯所得税**。展示时不要把历史「税」读成有效税率；有效税率看预测列或财报原值。

---

## 3. recompute() 引擎规格（`EONE.recomputePL(part3)`）

**入参** = `page_model.part3` 整块。**返回** `{ years, H, F, seg, byYear, fcstStart, revYoY }`。改任一 `assume.*` / `opex.*` → 重跑 recompute → 表 + 图 + 估值（linked 范式）全联动。

### 3.1 分部 Q×P×factor 自校准（核心机制）
对每个 `segments[i]`：
1. **自校准 unit_factor**：`factor = mean( hist.rev[k] / (hist.q[k]×hist.p[k]) )`，只对 `q,p,rev` 三者都有限且 `q×p≠0` 的历史年取平均；一个都算不出→用 `s.unit_rev_factor` 或 1。
2. **预测递推**：`qPrev=last(hist.q)`、`pPrev=last(hist.p)`；对预测年 i：
   `q_i = qPrev×(1+q_growth[i])`，`p_i = pPrev×(1+p_growth[i])`，`rev_i = q_i×p_i×factor`，然后 `qPrev=q_i,pPrev=p_i`（逐年复利）。
3. `gm_i = assume.gm[i]`（缺→用 `last(hist.gm)`）；`gp = rev×gm` 每年。

【Fact】**q/p 单位随意**：因 factor 吸收单位换算，只要历史 `rev/(q·p)` 各年稳定，q 填「万片/GW/客户数/GMV」、p 填「元-片/$-GW/ARPU/take-rate」都行，甚至 q 用指数、p 用水平值都可——**只有增长率 q_growth/p_growth 进预测**。[Risk] 若历史 `rev/(q·p)` 各年不稳（factor 方差大），说明 q/p 口径漂移，§4 自洽校验会挂，需换更干净的量价数据。q 或 p 某年缺 → 该年被跳过不参与 factor 平均。

### 3.2 byYear 逐年（历史 trust actual，预测 from drivers）
`H=hist_years.length`、`F=forecast_years.length`。对第 t 年（`isForecast = t≥H`，`fi=t−H`）：

- **历史列 (t<H)**：`rev = hist_actual.rev[t]`（缺→Σ 分部 rev[t]）；`gm = hist_actual.gross_margin[t]`（缺→Σgp/rev）；`gp=rev×gm`；`sga=rev×sga_rate[t]`、`rnd=rev×rnd_rate[t]`（仅展示用）；`ebit=hist_actual.ebit[t]`（缺→gp−sga−rnd）；`da=hist_actual.da[t]`（缺→0）；`ebitda=hist_actual.ebitda[t]`（缺→ebit+da）；`netProfit=hist_actual.net_profit[t]`（缺→ebit×(1−tax_rate[0]默认0.15)）；`tax=ebit−netProfit`（plug）。
- **预测列 (t≥H)**：`rev=Σ分部 rev[t]`；`gp=Σ分部 gp[t]`；`gm=gp/rev`；`sga=rev×at(opex.sga_rate,fi)`；`rnd=rev×at(opex.rnd_rate,fi)`；`ebit=gp−sga−rnd+at(opex.other_op,fi)`；`da=at(opex.da,fi)`；`ebitda=ebit+da`；`pretax=ebit+at(opex.other_nonop,fi)−at(opex.net_interest,fi)`；`tax=pretax×at(opex.tax_rate,fi)`；`minority=pretax×at(opex.minority_rate,fi)`；`netProfit=pretax−tax−minority`。
- 每行附：`ebitMargin=ebit/rev`、`netMargin=netProfit/rev`、`eps=netProfit/shares_yi`、`year`、`isForecast`。

**`at(arr,i,def)` 广播规则**：`null`→def；标量数字→该数；空数组→def；长度-1→`arr[0]`（常数广播）；否则 `arr[min(i,len−1)]`（越界取末元素）。所以每个 opex 率支持**标量 / 长度-1 / 长度-F** 三种写法。

示例（时间作列、维度作行，说明性）：

| 维度＼年 | 2022A | 2023A | 2024A | 2025E | 2026E | 2027E |
|---|---|---|---|---|---|---|
| 收入(亿) | 24.2 | 25.1 | 27.0 | 31.5 | 36.8 | 42.0 |
| 毛利率 | 0.32 | 0.30 | 0.31 | 0.33 | 0.34 | 0.35 |
| EBIT(亿) | 4.1 | 3.6 | 4.2 | 5.6 | 7.1 | 8.6 |
| 净利(亿) | 3.0 | 2.4 | 3.2 | 4.3 | 5.6 | 6.9 |
| EPS(元) | — | — | — | — | — | — |
| 来源 | 财报实际 | 财报实际 | 财报实际 | 引擎公式 | 引擎公式 | 引擎公式 |

---

## 4. 自洽校验（CK-3，交付前必过）

1. **量×价对分部收入 ±0.5%**：历史年逐段查 `hist.q[k]×hist.p[k]×factor ≈ hist.rev[k]`；等价于查 factor 各年离散度小。离散大→q/p 口径漂移，换数据。
2. **Σ分部收入对总收入 ±0.5%**：历史年 `Σ segments.rev[t] ≈ hist_actual.rev[t]`。引擎历史优先用 `hist_actual.rev`，若两者差>0.5% 说明分部拆分不闭合，补「其他」段或修分部。
3. **合计毛利对财报 ±5%**：预测起点年 `gp/rev` 应接续历史毛利率趋势，跳变>5pp 必须有催化解释（集采/涨价/产能爬坡），否则[Risk]。
4. **扰动测试（证明活链）**：拖任一 `q_growth/p_growth/gm/opex 率` 滑块 → recompute → `byYear` 预测 rev/净利必动 → `runValuation`（`link:true` 范式）→ blend 目标市值必动。**若拧假设目标价不动=链断/范式未 link**，修。
5. **Driver 可追溯（§1.17，2026-07-25 加）**：`core` 段有 `driver_chain`（每步带 val，关键步带 ev）+ `evidence`（逐字 quote）；凡同一参数存在 ≥2 个口径的数 → 有 `calibers` 表且 `why` 说清选择与互证关系；页面上无红色未登记 `[Ex]` 角标、无「缺 driver_chain / 缺 evidence」红提示。**读页面验收**：`document.querySelectorAll('.drv-chain,.cal-box,.ev-card').length` 与 `#seg-models .datagap` 对点。

[Risk] 校验通过只证明**结构自洽**，不证明**假设对**：q_growth 拍脑袋、毛利率外推乐观仍能过校验。假设合理性靠 (来源,报告期) + FACT/EST/DNA 标注 + Phase5 离散度交叉验证兜底。

### 4.1 ★反算隐含份额闸（2026-08-14 阳光电源实跑固化 · `node scripts/check_part3.js --model <page_model>`）

**病灶：举证全在 T+1，估值全押 T+3。** 阳光 v3.1 五个分部的 `seg_val` 全是「2028E 分摊利润 × 倍数」，
SOTP 4,353 亿是 ladder 里离现价 +78% 的那一档；而 `driver_chain` 最远只算到 2026，
`q_anchors` 五个锚（公司指引 60–65GWh / 东吴 65 / 国金 51.4）全是 2026 的。
2027E–2030E 的 `q_growth` 是裸参数：储能 0.35/0.28/0.22/0.18 一路推到 2030 年 149GWh，
对应全球份额多少，全页没有一个字。**58 项 check_part4 全过，这个洞一条都没碰到。**

**规则**：凡 `seg_val` 的锚年超出 `driver_chain` 覆盖的最远年份，该段必须给 `model.anchor_check`。
不要求把驱动链逐年重算到锚年（那是 core 段才值得的工），**只要求外推的终点落地成一个可证伪的份额数字**。

```json
"anchor_check": {
  "year": "2028E",
  "tam": {"v": 992, "unit": "GWh",
          "basis": "东吴 2026E 全球 588GWh 起，按 +35%/+25% 递减外推（2025 实际 317GWh、+74%）",
          "tag": "EST", "ev": "E1"},
  "implied_share_pct": 10.4,
  "ref_share_pct": 10.2,
  "ref_basis": "driver_chain step3：2026E 出货 60GWh ÷ 全球 588GWh",
  "verdict": "持平",                       // 扩张 / 持平 / 收缩，三选一
  "why": "外推到 2028 隐含份额 10.4%，与 2026 的 10.2% 基本持平——本页并没有假设阳光在抢份额，
          只假设它跟住一个还在翻倍的市场。这句话比 q_growth 的 35%/28% 好证伪：
          只要盯全球装机与公司出货两个数就能验。",
  "cost_if_wrong": "份额掉到 8%（宁德/特斯拉海外集成产能释放）→ 2028E 出货 79GWh 而非 104GWh，
                    储能分摊利润从 132.8 亿降到约 101 亿，SOTP 少 500 亿、第四档从 +78% 收到 +58%。",
  "share_gain_from": null                  // verdict=扩张 时必填：从谁手里抢
}
```

**闸门（A 组，checker 自动跑）**：
- **A2** 锚年未被驱动链覆盖 → 必须有 `anchor_check`，且 `year` 对上 `seg_val` 的锚年
- **A3** `tam.v` 有值且 `tam.basis` 写明怎么来的（不许只丢一个数）
- **A4** **隐含份额与模型自洽**：checker 自己按 `hist.q` 末值 × Π(1+q_growth) 递推到锚年，
  除以 `tam.v`，与 `implied_share_pct` 差 >0.5pp 即不过——防「份额是另算的、跟模型对不上」
- **A5/A6** `verdict` 三选一；`why` ≥20 字且带数字
- **A7** `verdict` 与 `implied − ref` 的漂移方向一致（默认容差 ±3pp，`--tol-pp` 可调）
- **A8** 判「扩张」的必须填 `share_gain_from`——**份额是零和的，说得出从谁手里抢才算数**
- **A9** `cost_if_wrong` 带量级

**这一格的价值不在于把数改对，在于把「外推」翻译成一句能证伪的话。**
阳光那句「隐含份额 10.4%，与 2026 的 10.2% 持平」比五个 q_growth 参数有用得多：
它把三年的外推压成一个可以逐季跟踪的比值，而且当场说清了这页**没有**假设份额扩张。

### 4.2 ★L 兜底段进 SOTP 的上限（B 组）

`driver_chain` 与 `calibers` 皆空的段（＝没有量价拆分、只有增速外推），
其 `seg_val.mcap_yi` 在 Σseg_val 里的占比**不得超过它最新一年的收入占比 + 3pp**，
且 `logic` 里必须明说兜底（出现 兜底/未披露/不可得/降级 任一词）。

阳光 gen 1.3% vs 收入 1.5%、other 3.8% vs 3.2%，恰好合规——但结构上原来没有任何东西把守：
一个 30% 收入占比、连量价都拆不出来的段，照样可以配一个高倍数把 SOTP 顶上去。
CK-3 原有的「最大分部禁 L 兜底」只管最大的那一段，管不到这个。

---

## 5. 估值联动（`EONE.runValuation(part3.valuation, pl)`，Phase5 详见 references/05）

`pl` = recompute 输出，让 forward 净利/EBITDA **从 P&L 模型链取**（活链）。8 范式 `EONE.PARADIGM[key](params, pl, ctx)` 各返回 `{mcap(亿), detail, ok}`：

- `link:true` + `year_offset`（0-based 预测年，默认末年）→ 从 `pl` 取该预测年 `netProfit`(pe/peg) 或 `ebitda`(evebitda)；不 link 且给了静态 `fwd_profit_yi/ebitda_yi` 则用静态值。**要联动就设 `link:true`**。
- 8 范式默认/公式：`leader`(fs/lc×lm×调整÷折现)、`pe`(prof×pe÷(1+r)^n)、`peg`(prof×peg×g)、`sotp`(Σ profit×mult+net_cash)、`pbroe`(equity×roe/coe)、`evebitda`(ebitda×mult−net_debt)、`endgame`(tam×share×net_margin×pe÷折现)、`implied`(诊断，权重0，反推市场隐含净利/收入)。
- `runValuation` 汇总：只对**非诊断、weight>0、有限、ok** 的范式做**权重归一加权** blend；`range.dispersion=(max−min)/max`，`<0.20` 可点估计 / `0.20–0.50` 看区间 / `>0.50` 冲突不出单值；每范式 `odds=mcap/current_mcap−1`（口径：赔率=目标市值/当前市值−1）。
- `valuation` 顶层读 `shares_yi`、`current_mcap_yi`（算 target/odds）；`net_cash_yi` 是信息位，实际净现金/净债务各范式从自己 `params.net_cash_yi/net_debt_yi` 取。

---

## 5.5 · 自定义 driver 注入层（外部物理驱动→分部 q/p，★2026-07-22 华丰 688629 固化）

**何时用**：分业务一的 q 由**外部物理世界**驱动（AI 芯片出货→连接器套数、装机量→耗材、车型销量→单车价值量…），标准 `q_growth` 滑块表达不了「多型号出货×配比×份额×ASP-mix」的结构时——建独立算量器面板。**不改 skill 模板/引擎**，用注入层实现（模板：`_workspace/688629/inject_ascend.py`）。

**注入模式（五步）**：
1. 参数进 `page_model.part3.<driver名>` 自定义块：年份×{各型号出货量、配比 u、份额 s、ASP×形态、库存系数、非核心收入、产能上限}——**全部数组化=逐年可调**；build 后随 `__DATA__` 内联进页面，注入脚本零外部依赖。
2. 注入脚本(python)把 `<script>` append 到 onepager.html：读 `window.__DATA__.part3.<driver名>` 渲面板（input 矩阵+预设按钮组），插在分业务一的分部模型章节 panel 之后。
3. driver 公式骨架：`需求盘=Σ_type(N_type×u_type×s_type×ASP_type)×(1+库存系数)+非核心收入`；`确认收入=min(需求盘,产能)`；`混合ASP=Σr/Σh`、`q=确认收入/混合ASP` → 反解 `q_growth/p_growth` 写回 `segments[0].assume`（写回也同步刷新核心假设区对应滑块的 value/kv 文本）。
4. **首跑立即 writeback**——driver 面板成为唯一事实源，次级模型表/图/估值全部与 driver 一致。
5. 预设按钮=卖方分歧具象化（Base/乐观卖方式/保守卖方式/Bear）——把卖方收入分歧翻成 2-3 个参数差（产能 vs 需求盘），这是算量器的核心认知价值。

**勾稽铁律（★用户实测打回后固化，缺一即翻车）**：
- **relinkAll() 必须实现**：引擎里 SOTP/leader/endgame 的 params 是静态值（不支持 link）、`renderSegmentModels`（分部估值卡）只在 boot 渲一次——每次改动后必须把 `sotp.segments[].profit_yi`(=取锚年归母×各段毛利占比)、`leader.follower_steady`(=稳态年收入)、`endgame.net_margin`(=终局年净利率) 写回 params，并直接改 `.sm-val` DOM，再 `APP.recompute()` 单次重渲。否则加权估值 ~55% 权重是死腿，用户拖杆赔率不动。
- **核心假设区滑块也要挂钩**：`#assumptions` 容器加 debounced(~90ms) input listener → relinkAll+recompute（app.js 内部滑块只调闭包 recompute，不会触发注入层活链）。
- **min/clamp 钳制激活时必须渲醒目警示**：判定用 `demand>capacity`（勿把 conf/demand 当利用率），黄框写明「需求侧参数此时不改变确认收入，请调产能行或切预设」——否则"正确地不动"看起来像坏了。
- **验收标准=读估值区 DOM 文本**（`#valuation-blend` textContent 改动前后对比），不是引擎返回值——引擎通了、DOM 死着，是实测翻车点。
- 面板底部写清**勾稽范围**：哪些联动（PE/PEG/EV-EBITDA link + SOTP/大哥/终局活链 + 分部估值卡）、哪些仍手调（各范式倍数/估值权重/终局 TAM/分部毛利率）。
- **专家口径先归一再进公式**：纪要间"每套/每卡/每柜"三层价格口径常互相打架 8-10 倍——建「专家口径对账表」（各锚数字×口径×日期×[doc_id]）放分部模型章节，参数默认值取归一后中枢，异常锚在 anchors 里标注而非丢弃。

---

## 6. 填 part3 实操清单（从 Phase1 数据落地）

1. `hist_years` = 近 5–10 年（与 part1 对齐，可行则拉到上市首年）；`forecast_years` = 未来 3 年（如 `["2025E","2026E","2027E"]`）。`shares_yi` = 总股本(亿股)，同时填 `valuation.shares_yi`。
2. `segments[]`：从 `part1.revenue.segments`（已跨年归一、尾部并「其他」——**穷尽性与其他资产段见 §1.15**）取全部分部，每段：
   - `key/name`；`hist.rev[]` = part1 分部收入（亿，同口径）；
   - `hist.q[]`/`hist.p[]` = 按 §1.1 该 archetype 的物理量价（纪要/年报/AlphaPai/行业数据，标【Estimate】）；**分业务一（最大分部）必须真量价，禁 L 兜底（§1.15）**；
   - `hist.gm[]` = 分部毛利率（小数，若披露；缺→留空，引擎用合计毛利兜底）；
   - `assume.q_growth[]`/`p_growth[]`/`gm[]` = 预测知识（标 EST；可标量广播）；
   - `model` = **细分建模卡（§1.15 表，必填）**：q_def/p_def/logic/assets_note/anchors/seg_val/cite；
     **＋ Driver 三件套（§1.17）**：`driver_chain`（core 段必填，逐步算账带 val/ev）、`calibers`（有口径分歧必填，差多少/选哪个/为什么）、`evidence`（core 段必填，RAG 逐字原句 + 推论分层）；取证时**顺手把 doc_id/页码/原句抄进 evidence**，别只抄结论数字（回头再找原文的成本远高于当场记）；
   - 【降级·仅限非最大分部】拿不到量价 → `q=[分部收入指数]、p=[1,1,...]`，退化为纯收入增速（=L 兜底），`model` 里声明，页面自动标注「量价未拆·仅收入外推」。
3. `hist_actual` / `opex`：按 §2.1 表从 `fetch_ifind` 的 cost/dupont 表 + 现金流量表取；缺字段写 `⚠️未查到` 不编造（引擎有兜底但会失真，须标注）。
4. `valuation.paradigms`：见 references/05；PE/PEG/EV-EBITDA 设 `link:true` 让 Forward 值随 P&L 联动；`implied` 权重 0 仅诊断。
5. 跑 §4 四项自洽校验 → 过闸 → 交 Phase5/Phase6。

> 引擎节点测试（可选，node 直跑）：`node -e "const E=require('C:/Users/youqi/.claude/skills/equity-onepager-interactive/scripts/model_engine.js'); const pl=E.recomputePL(require('./page_model.json').part3); console.log(pl.byYear.map(r=>[r.year,Math.round(r.rev),Math.round(r.netProfit)]));"` —— 看历史列是否等于财报实际、预测列是否随假设动。
