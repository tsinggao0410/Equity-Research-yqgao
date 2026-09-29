# 下游交接 JSON(可选,沿用 v2.4.2 契约)

> v3.2 的交付物是「业务认知」MD + 单文件 HTML。只有当用户要把这张卡接进 Chain Pipeline 或其他 skill(equity-onepager、
> supply-chain-mapper、industry-model 等)时,才另外写下面两个 JSON 之一。字段契约与 v2.4.2 完全一致,下游不用改。
> - 产业链 / 技术物种卡 → `comprehension.json`(chain-bus P0,附录 A),写出:`python3 <skill>/scripts/handoff/comprehension_writer.py`
> - 公司卡 / 主题卡 → `business_primer.json`(附录 B),写出:`python3 <skill>/scripts/handoff/business_primer_writer.py`
> 写 JSON 的内容一律取自已定稿的 v3.2 卡与数字底座,不另起炉灶;JSON 里的数与卡里的数必须一致。
> 附录 B 里提到的 `render_primer_html.py`、读者版九章、`visuals[]` 的 v2 用法只是字段来历,v3.2 不再用那套渲染器。

### 下游接口(comprehension.json 的消费方 + 终局报告)

> ★ 本卡是 **chain-bus P0 产物**(CONTRACT §5 `comprehension.json`),写到
> `_chain_workspace/<narrative_id>/P0_comprehension/comprehension.json`。
> 字段名/单位/结构**严格冻结**——下游靠 join key 直读,不再各 skill 各说各话。

| 下游 | 读本卡的什么(冻结字段) |
|---|---|
| supply-chain-mapper(P1) | `bom_seed[]`(M1 专属环节,直接当**种子节点**)+ `routes[]`(M3 路线分叉,按 N 条并行链展开)+ `chains_count`(复用诊断→几条链) |
| demand-decoder(P2) | `necessity_tiers`(M2 的 A_rigid..F_sentiment 六档)+ 场景表(M5)→ 分场景 TAM;`swing_variable` → 需求情景的外部变量 |
| supply-decoder(P3) | `maturity_redzone`(M6)→ binding constraint 首选 **(未焊——phases.py P3 inputs 无 P0 条目, 仅编排器 notes 提示, SD 侧无读取指令)** |
| valuation-paradigm-decoder(P4) | `cognitive_position`(M7)→ 判断市场 price 的是成长还是变量 β **(未焊——同上, VPD 侧无读取指令)** |
| **chain-final-analysis(P6) 终局报告** | ★ `one_line_cognition` / `routes` / `swing_variable` / `maturity_redzone` **原样进报告第二节"五分钟读懂(认知)"**;`glossary[]` **原样进第九节"速查"名词表**。认知与报告口径就此锁死——本卡写什么,报告第二节就是什么。 |

**Mode B 下游接口(`business_primer.json`,schema 见附录 B;不是 chain-bus 契约,不进 P0 校验闸):**

| 下游 | 读本卡的什么 |
|---|---|
| equity-onepager-interactive | `product_lines[]` → `part3.segments[]`(每档一个分部:`name` / `q_def`=台数口径 / `p_def`=ASP 口径 / `driver`=驱动链);`customers` → `revenue.customers[]`;`demand_drivers.primary` → 周期坐标的主变量;`glossary[]` → 正文白话翻译表;`entity.reporting_scope` → 全篇口径主体 |
| equity-playbook-analysis | `business_model.value_capture` + `unit_economics[]` → 开篇「现金流引擎 / 利润引擎」 |
| industry-model | `landscape.competitors[]` + `share_by_tier[]` → 格局台账的实名玩家种子;`tech_primer.standards_timeline[]` → 拐点三件套的「政策」触发器 |
| buyside-model-builder | `product_lines[]` 的 量×价 → STP 原型(产品线 量×价);`business_model.cost_structure[]` → 成本假设 |
| valuation-paradigm-decoder | `analog` + `changes_and_debates` → 范式候选与市场在 price 什么 |
| hf-pitch-memo / pitchbook-deck | `one_line_business` + `glossary[]` → memo 开篇与速查 |
| supply-chain-mapper | `tech_primer.bom_skeleton[]`(自制/外购已标)→ 种子节点 |
| cyclical-equity-tracker | `demand_drivers.primary` → 商品/下游整机链的挂钩变量 |
| tech-species-primer Mode A | `changes_and_debates.structural_shifts[]` 里 `is_new_species:true` 的条目 → 起一张 A 卡 |

---


## 附录 A:comprehension.json handoff schema —— ★ 冻结(CONTRACT §5 P0,Mode A)

> **铁律(单位/字段冻结):** 顶层必出这 12 个字段 + `_meta`,字段名一字不改。
> 下游(P1/P2/P6 已焊;P3/P4 未焊)与插件中央校验闸都按本 schema 直读。要加字段 →
> append `_shared/CONTRACT_NOTES.md` 提议,**不要私自发明**。
> 写出方式见下方"写出工具",不要手搓 JSON 漏字段。
> **null 逃生门(唯一):** 早期物种(eVTOL/人形)渗透率不可知 → `penetration_pct` 显式写
> `null`(= DATA NOT AVAILABLE);**禁止编数字、禁止删 key**。其余数值字段无此逃生门。

```jsonc
{
  "_meta": {
    "narrative_id": "sodium-battery-20260604",
    "phase": "P0",
    "schema_version": "chain-bus/1.0",      // 全链统一
    "units": {"mkt_cap": "yi_cny", "profit": "yi_cny", "tam": "yi_cny"},
    "join_keys": ["segment_sid"],            // P0 喂 P1 的种子,环节级
    "source_skill": "tech-species-primer",
    "written_at": "ISO8601"
  },
  "species_name": "钠离子电池",
  "one_line_cognition": "用钠盐替代锂的二次电池——本质是碳酸锂价格的看涨期权(锂越贵越划算),不是能量密度路线。",  // ★ 原样进报告第二节
  "routes": [                                // ★ 原样进报告第二节;喂 P1 按 N 条链展开
    {"id": "R1", "name": "聚阴离子", "status": "分叉", "penetration_pct": 8,
     "strength": "长循环/宽温", "weakness": "能量密度低", "best_scene": "储能", "players": ["众钠","珈钠"]},
    {"id": "R2", "name": "层状氧化物", "status": "主线", "penetration_pct": 12,
     "strength": "能量密度高", "weakness": "循环短/怕空气", "best_scene": "动力/两轮", "players": ["宁德","中科海钠"]}
  ],
  "chains_count": 2,                          // ★ int;几条并行链(复用诊断结论)
  "necessity_tiers": {                        // ★ 六档 A-F(对齐 CONTRACT §5);无则 []
    "A_rigid":   ["低温/极寒储能","高功率快充"],      // 真刚需,抗变量波动
    "B_roi":     ["储能/两轮/A00 平替(锂价>12-15万才划算)"],  // ROI/外部变量依赖的平替
    "C_armsrace":[],                          // 军备竞赛驱动
    "D_policy":  ["资源安全/国产替代政策导向"],          // 政策驱动
    "E_finance": [],                          // 融资/补贴驱动
    "F_sentiment":["主题炒作部分"]              // 情绪驱动(易反转)
  },
  "swing_variable": {                         // ★ 原样进报告第二节"价格上游/为什么这次不一样"
    "name": "碳酸锂价格", "direction": "+",     // direction ∈ {"+","-"} 禁 null;方向必须数据 derive(铁律1)
    "why": "锂越贵→钠电省得越多→叙事越强(实跑发现是正向,非先验的反向)",
    "is_volatile": true,
    "sensitivity": [                           // ★ 非空 ≥2 档;每档 level/edge/source 三件套(writer 硬闸)
      {"level":"20万","edge":"+24%","source":"鑫椤锂电+SMM 成本模型 2026-05"},
      {"level":"10万","edge":"+12%","source":"同上"},
      {"level":"5万","edge":"+5%(证伪)","source":"同上"}
    ],
    "current": "~18-20万(2026-05)"
  },
  // 双变量物种(如光伏↔硅料+电价): 主导变量放 swing_variable, 次变量放可选 swing_variable_2(同结构)
  "contradictions": [                         // ★ 铁律2 输出位(writer 硬闸: 必出非空)
    {"claim_a": "国内口径: 钠电当前比锂电贵", "claim_b": "英文口径: 便宜 35%",
     "source_a": "国内卖方测算 2026-04", "source_b": "BNEF 2026-03",
     "resolution": "两者都对——当前成本 vs 理论成本之差; 采分档表述"}
    // 主动找过但确无矛盾 → [{"none_found": true, "searched": "找过哪些源/关键词"}]
  ],
  "maturity_redzone": {                       // ★ 原样进报告第二节;喂 P3 binding constraint
    "stage": "二次爬坡(锂价驱动)",
    "bottleneck": "硬碳负极良率/配套未跟上 + 能量密度物理天花板"
  },
  "model_reuse_diagnosis": "制造产线🟡部分复用(锂电产线改造)/关键材料🔴不可复用(硬碳负极+钠盐)/终端型号🟡部分(储能可平移,动力需重认证)→ 2 条并行链,仅上游(硬碳/电解液/铝箔)交汇",  // ★ 3 层结论(铁律4)
  "cognitive_position": "S曲线渗透爬升早期 / Gartner 二次爬坡;bull=锂价高位+真量产+资源安全,bear=成本优势是锂价影子锂跌即证伪;历史类比 钒电池(永远的利基)、固态电池(抢风口)",  // ★ 喂 P4
  "bom_seed": ["硬碳负极","钠盐正极(分路线)","铝箔集流体","NaPF6电解液","BMS"],  // ★ 喂 P1 当种子节点(M1 专属环节)
  "glossary": [                              // ★ 原样进报告第九节"速查"
    {"term": "硬碳负极", "plain": "钠电专属负极材料,锂电用石墨,两者不通用"},
    {"term": "聚阴离子", "plain": "一种钠电正极技术路线,循环寿命长但能量密度低,主打储能"}
  ]
}
```

### 字段速查(11 必出字段 → 哪来 → 喂谁)

| 字段 | 来自模块 | 类型 | 下游消费 |
|---|---|---|---|
| `species_name` | M1 | str | 全链标识 |
| `one_line_cognition` | 一句话认知 | str | ★ 报告第二节打头 |
| `routes[]` | M3 | list(id/name/status/penetration_pct…) | ★ 报告第二节 + P1 分链 |
| `chains_count` | 复用诊断 | **int** | P1 几条链 |
| `necessity_tiers` | M2(三档→六档映射) | dict(A_rigid..F_sentiment,值为 list) | P2 分场景 TAM |
| `swing_variable` | M2 | dict(name/direction/why/is_volatile/**sensitivity≥2档带source**) | ★ 报告第二节 + 全链敏感性锚 |
| `contradictions[]` | M2/全卡(铁律2) | list({claim_a,claim_b,source_a,source_b,resolution} 或 none_found) | 报告"矛盾点亮" + 审计 |
| `maturity_redzone` | M6 | dict(stage/bottleneck) | ★ 报告第二节 + P3 约束(未焊) |
| `model_reuse_diagnosis` | 复用诊断 | str(3 层) | P1/下游建模硬约束 |
| `cognitive_position` | M7 | str | P4 判成长 vs β |
| `bom_seed[]` | M1 | list(str) | ★ P1 种子节点 |
| `glossary[]` | 全卡 | list({term,plain}) | ★ 报告第九节速查 |

### 熟行业"指针卡"最小字段
跳过认知层但仍要交 P0 时(熟行业),**最小必出**:`species_name` / `one_line_cognition` / `routes[]`(至少 1 条)/ `chains_count` + `_meta`;其余字段由 writer `--pointer` 自动补空占位(不删 key,保证下游 `.get()` 不炸)。
writer 会在 `_meta.card_type` 写 `"pointer"`(全字段卡为 `"full"`)——**中央闸按 card_type 对指针卡放行/降 warn**(闸侧由 chain-pipeline 插件实现)。本清单与 `comprehension_writer.py` 的 `POINTER_REQUIRED` 一字对齐,改一处必改两处。

### 写出工具(不要手搓 JSON)
认知卡填完后,用本 skill 自带脚本一次性 **校验+写出** P0 产物(缺字段/类型错直接报错,避免漏字段):

```bash
# 把上面填好的卡存成 _tmp_card.json(顶层 11 字段),然后:
python3 <skill>/scripts/handoff/comprehension_writer.py _tmp_card.json \
  --narrative-id sodium-battery-20260604 \
  --out _chain_workspace/sodium-battery-20260604/P0_comprehension/comprehension.json
# 校验通过 → 写出带 _meta 的 chain-bus P0 产物;失败 → 打印缺哪个字段
```

> **接入说明**:本卡是 chain-bus P0 产物。orchestrated 运行由 cp.py 推进;独立运行时下游(P1 supply-chain-mapper)直接 Read `P0_comprehension/comprehension.json` 取 `routes/bom_seed/chains_count`。orchestrated 运行由 chain-pipeline 插件中央校验器 `<plugin>/scripts/schemas/validate_bus.py` 把总闸;本 skill 的 `comprehension_writer.py` 做出口自检(铁律 1/2/7 的 count 型硬闸:sensitivity ≥2 档带 source、direction 禁 null、contradictions 非空),不硬绑 pipeline_gate.py,保持可独立运行。


---

## 附录 B:business_primer.json handoff schema(Mode B;非 chain-bus 契约,版本 business-primer/1.1)

> 顶层 **16 个字段 + `_meta`**(v2.1 加 `visuals[]`;v2.4 加 `moat[]`;`visuals_missing[]` 可选),字段名一字不改;下游(onepager / industry-model / model-builder)靠字段名直读。
> 数值缺失显式写 `null`(= DATA NOT AVAILABLE),**禁止编数、禁止删 key**。金额单位 `yi_cny`(亿元),ASP 单位 `cny_per_unit`,占比为整数/小数百分数(35.5 = 35.5%)。
> 写出用 `scripts/business_primer_writer.py`,不要手搓——缺字段/类型错直接报错。

```jsonc
{
  "_meta": {"subject_id": "yuchai-cyd-20260915", "mode": "B", "card_type": "business",
            "subject_type": "company",            // "company" | "industry"
            "schema_version": "business-primer/1.1", "source_skill": "tech-species-primer",
            "units": {"revenue": "yi_cny", "asp": "cny_per_unit", "pct": "percent"},
            "data_as_of": "FY2025 (20-F 2026-02-27)", "written_at": "ISO8601"},
  "entity": {                                    // B-1(铁律 11)
    "input_name": "玉柴国际", "listed_name": "China Yuchai International Ltd (NYSE: CYD)",
    "operating_entity": "广西玉柴机器股份有限公司 (GYMCL)", "ownership_pct": 76.4,
    "reporting_scope": "CYD 并表 = GYMCL 及其子公司(含 MGP 船电、玉柴芯蓝新能源);不含玉柴集团其他公司与联营 Y&C",
    "disambiguation": [ {"name": "玉柴集团", "relation": "GYMCL 母公司(国企)", "data_trap": "集团口径 55–60 万台 ≠ 上市口径 46.1 万台"} ]
  },
  "one_line_business": "…",                      // B0 ★ 进 memo 开篇
  "analog": {"company": "潍柴动力", "same": ["…"], "different": ["…"]},   // B0
  "product_lines": [                             // B1(铁律 8/9)★ 喂 onepager segments[]
    {"id": "H", "name": "重型柴油/燃气机", "tier_rule": "排量 >7.0L(20-F 定义)",
     "spec_band": "7.7–13L / 350–570PS", "representative_models": ["YCK08","YCK11","YCK13","YCK15N"],
     "applications": ["重卡","牵引车","大客","工程机械"],
     "units": 110043, "revenue_yi": 97.56, "asp_cny": 88653, "asp_formula": "9,755,682 千元 ÷ 110,043 台",
     "rev_share_pct": 39.6, "unit_share_pct": 23.9, "gm_pct": null,
     "competitors": ["潍柴","康明斯(东康/福康)","解放动力"],
     "q_def": "重型机销售台数(20-F 分档)", "p_def": "分档收入÷台数(EST)",
     "driver": "重卡销量 × 玉柴配套率 × 燃气机占比(拉 ASP)"}
  ],
  "tech_primer": {                               // B2(铁律 12)
    "how_it_works": "≤5 行白话",
    "key_params": [ {"param": "排量(L)", "meaning": "…", "why_buyer_cares": "…", "pl_hook": "p"} ],   // pl_hook ∈ q|p|gm|opex|capex|wc|none
    "standards_timeline": [ {"standard": "国六b", "effective": "2023-07-01", "status": "已生效", "effect_on_qp": "切换前抢装、切换后透支;新机型涨价窗口"} ],
    "bom_skeleton": [ {"part": "缸体/缸盖/曲轴/凸轮轴", "make_or_buy": "自制", "supplier": "自铸 >40 万件/年", "value_share_pct": null} ],  // make_or_buy ∈ 自制|外购|混合
    "process_hurdles": [ {"hurdle": "缸体自铸良率", "now": "…", "who_is_better": "…", "stuck_on": "…"} ],   // v2.4(铁律 20): 做出来难在哪
    "moat": "以「对手追上需要__」收尾"
  },
  "moat": [                                      // B2.5(铁律 19)★ v2.4 必出, ≥2 层, 强度由证据推出, 不许全 "强"
    {"layer": "OEM 配套目录位次", "type": "客户认证",      // type ∈ 资源牌照|工艺良率|客户认证|规模成本|转换成本|网络效应|数据|渠道|其他
     "strength": "中",                            // ∈ 强|中|弱
     "evidence": "进一家重卡 OEM 配套目录要 18–24 个月台架与路试, 前五客户占 35.5% 已锁定 (20-F Customers 段)",
     "kill_condition": "OEM 自产发动机装机率过半, 或国六后再无新平台开发",
     "horizon": "3 年内难变", "competitor_attempt": "康明斯 2023 借合资厂切入解放重卡, 份额 3 年只到 …",
     "sources": ["S1", "S7"]}
  ],
  "customers": {                                 // B3(铁律 10)
    "matrix": [ {"application": "重卡", "lines": {"L": "无", "M": "少量", "H": "真实配套"}} ],
    "direct": [ {"name": "一汽解放", "tier": "H", "evidence": "EST 中文新闻 2025"} ],
    "end_users": ["物流车队","个体司机","基建承包商"],
    "decider": "OEM 定配套目录;终端在目录内选发动机品牌",
    "top1_pct": 17.1, "top5_pct": 35.5, "customer_is_competitor": true,
    "export_path": "直接出口 1.6% 收入;>25% 国内销量随 OEM 整机出海(公司估,EST)"
  },
  "business_model": {                            // B4
    "revenue_streams": [ {"stream": "整机配套 OEM(轻+中+重)", "share_pct": 72.9, "gm_band": null, "growth": "…"} ],
    "pricing_power": "…", "cost_structure": [ {"item": "废钢/生铁", "share_pct": null, "note": "…"} ],
    "working_capital": "应收票据 104 亿 vs 应付票据 111 亿 vs 存货 56 亿 → …",
    "capex_intensity": "产能 63.3 万 / 产量 38.8 万 → 利用率 61%(EST)",
    "unit_economics": [ {"line": "H", "asp_cny": 88653, "gm_pct": null, "gross_per_unit_cny": null} ],
    "value_capture": "一句话 DNA"
  },
  "landscape": {                                 // B5
    "market_size": "多缸柴油机 413.2 万台(2025,中内协)",
    "share_by_tier": [ {"tier": "商用车柴油机", "company_pct": 11.7, "leader": "潍柴", "leader_pct": null, "source": "中内协 via 东财 2026-01"} ],
    "competitors": [ {"name": "潍柴动力", "position": "重卡为主 + 自家整车(重汽/陕汽)", "main_tier": "H", "relation": "对手"} ],
    "competitive_axes": ["排放合规","可靠性口碑","OEM 配套关系","售后网络","价格"]
  },
  "demand_drivers": {                            // B6(铁律 1 同款)
    "primary": {"name": "国内重卡销量(柴油+燃气)", "affects": "q", "direction": "+",
                "sensitivity": [ {"level": "…", "edge": "…", "source": "…"} ], "current": "…"},
    "secondary": [ {"name": "排放标准切换", "affects": "q/p", "direction": "+", "note": "切换前抢装、切换后透支"} ],
    "history": [ {"round": "国五→国六 2019–2021", "ignite": "…", "peak": "2021H1", "trigger": "…", "vs_now": "…"} ]
  },
  "contradictions": [ {"claim_a": "…", "claim_b": "…", "source_a": "…", "source_b": "…", "resolution": "…"} ],  // 铁律 2;确无矛盾 → [{"none_found": true, "searched": "…"}]
  "changes_and_debates": {                       // B7
    "structural_shifts": [ {"shift": "…", "stage": "真量产|试点|PPT", "evidence": "…", "affects_lines": ["H"], "timeline": "…", "is_new_species": false} ],
    "bull": "…", "bear": "…", "core_disagreement": "…", "cognitive_position": "…"
  },
  "segment_separability": {                      // 🔑 诊断
    "lines_count": 4, "diagnosis": "3 层结论一句话",
    "table": [ {"line": "轻/中/重 道路机", "plant": "🟢", "customers": "🟡", "cycle": "🔴", "disclosure": "🟢"} ]
  },
  "glossary": [ {"term": "排量", "plain": "…"} ],
  "visuals": [                                   // 🖼 视觉素材层(铁律 13)★ v2.1 必出;role=structure 至少一条
    {"id": "V01", "file": "images/structure_business_logic.svg", "role": "structure",   // role ∈ product|structure|process|application|plant|data|other
     "source_type": "self_drawn",                 // ∈ official_site|ir_page|ir_deck_or_report_pdf|annual_report|self_drawn|industry_assoc
     "source_url": null, "page_url": null, "caption": "上游自制/外购 → 四条产品线 → 直接客户 → 终端", "module": "B0", "product_line_id": null,
     "how_obtained": "官网/IR 无结构图 → draw_structure.py 自绘", "accessed": "2026-09-15", "mark": "DNA"},
    {"id": "V02", "file": "images/H_YCK15N_gas_engine.jpg", "role": "product", "source_type": "official_site",
     "source_url": "https://www.yuchaidiesel.com/upload/images/2024/06/22/658a22b5….png", "page_url": "https://www.yuchaidiesel.com/product/pro-detail-1577.htm",
     "caption": "重型 H 代表机型 YCK15N 燃气机 570PS", "module": "B1", "product_line_id": "H", "how_obtained": "浏览器 BROWSER_SNIPPET → --img-list", "accessed": "2026-09-15", "mark": "FACT"}
  ],
  "visuals_missing": [ {"what": "IR deck May 2026 Presentation 官方收入拆分/战略图", "why": "investor.cyilimited.com Akamai 挡 curl/fetch 403,需真实浏览器下载"} ],  // 没拿到的写这里,不要硬凑
  "sources": [ {"id": "S1", "title": "CYD 20-F FY2025", "url": "…", "accessed": "2026-09-15"} ]
}
```

### 字段速查(16 必出字段 → 哪来 → 喂谁)

| 字段 | 来自模块 | 类型 | 下游消费 |
|---|---|---|---|
| `entity` | B-1 | dict(listed_name/operating_entity/reporting_scope/disambiguation[]) | 全篇口径主体;onepager 股权树 |
| `one_line_business` | B0 | str | memo 开篇 |
| `analog` | B0 | dict(company/same[]/different[]) | valuation-paradigm-decoder |
| `product_lines[]` | B1 | list(id/name/tier_rule/applications[]/units/revenue_yi/asp_cny/asp_formula/rev_share_pct/q_def/p_def/driver…) | ★ onepager `segments[]`;model-builder STP |
| `tech_primer` | B2 | dict(how_it_works/key_params[]/standards_timeline[]/bom_skeleton[]/process_hurdles[]/moat) | glossary 白话;supply-chain-mapper 种子;industry-model 拐点 |
| `moat[]` ★v2.4 | B2.5(铁律 19) | list({layer,type,strength ∈ 强/中/弱,evidence,kill_condition,horizon,competitor_attempt,sources[]}) ≥2 | 第四章壁垒台账;hf-pitch-memo「为什么是它」;onepager 可证伪性坐标 |
| `customers` | B3 | dict(matrix[]/direct[]/end_users[]/decider/top1_pct/top5_pct/customer_is_competitor/export_path) | onepager `revenue.customers[]` |
| `business_model` | B4 | dict(revenue_streams[]/pricing_power/cost_structure[]/working_capital/capex_intensity/unit_economics[]/value_capture) | onepager 利润桥;playbook 引擎;sotp |
| `landscape` | B5 | dict(market_size/share_by_tier[]/competitors[]/competitive_axes[]) | industry-model 台账种子 |
| `demand_drivers` | B6 | dict(primary{name/affects/direction/sensitivity≥2 带 source}/secondary[]/history[]) | onepager 周期坐标;cyclical tracker |
| `contradictions[]` | 全卡(铁律 2/11) | list | 审计 + 报告「矛盾点亮」 |
| `changes_and_debates` | B7 | dict(structural_shifts[]/bull/bear/core_disagreement/cognitive_position) | VPD;矛盾地图;`is_new_species` → Mode A |
| `segment_separability` | 🔑 | dict(lines_count **int**/diagnosis/table[]) | onepager 分几个分部 |
| `glossary[]` | B2/全卡 | list({term,plain}) ≥5 | memo / onepager 速查 |
| `visuals[]` | 🖼 视觉素材层 | list({id,file,role,source_type,source_url,caption,module,product_line_id,how_obtained,accessed,mark}) ≥1,`role=structure` ≥1 | onepager 第二章产品图/结构图;pitchbook-deck 产品页;`render_primer_html.py` |
| `sources[]` | 全卡 | list({id,title,url,accessed}) ≥3 | 溯源 |

### 写出工具(不要手搓 JSON)

```bash
python3 <skill>/scripts/handoff/business_primer_writer.py _tmp_business_card.json \
  --subject-id yuchai-cyd-20260915 --subject-type company \
  --out ~/Desktop/research-materials/玉柴国际-CYD/primer/business_primer.json
# 校验通过 → 写出带 _meta 的产物;失败 → 逐条打印缺哪个字段 / 哪个闸没过
```
