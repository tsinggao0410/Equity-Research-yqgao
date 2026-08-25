# 01 · 取数手册（Phase 1 ⚡强制）

Part1 四大图（营收拆分 / 十大股东+子公司 / 十年ROE杜邦 / 成本三费费率）的**精确取数命令 + 逐条解析陷阱 + A/港/美路由**。全部配方基于对 **立昂微 605358.SH**（半导体硅片，从大股东体系分家）的真实实测，另在 格力 000651.SZ 上二次验证。进入 Phase 1 前必读，Phase 2 映射时回查解析陷阱。

**铁律**：iFind 只做「结构化财务/股东」；**子公司永远走 qcc**（iFind 查子公司会静默命中股东数据，见 §5 反面示范）。所有数字落表时带 `(来源, 报告期)` + FACT/EST/DNA；缺则写「⚠️未查到」，**不编造**。

---

## 0 · 引擎怎么工作（承重）

每个 iFind 财务/股东工具吃**一条自然语言 `query` 字符串**，后端自己做「实体+指标+日期」解析，返回 `data.answer` = 一张 markdown 竖线表 + 尾部 `# 指标参数信息`（每列 报告期/单位/数据类型）+ footer。**"精确取数" = 把要素塞进 query**：(a) 证券实体，(b) 指标名，(c) 多年靠**年份区间短语**「2015年至2024年 各年度」→ 每财年一行，(d) 分部要给**维度词**（分产品/分行业/分地区）+「金额」。多年是被年份短语解锁的，**不是靠任何 flag**。

CLI→MCP 映射（server `hexin-ifind-ds-stock-mcp`，CLI key `stock`；news server `hexin-ifind-ds-news-mcp`）：
`fin`→get_stock_financials · `holders`→get_stock_shareholders · `info`→get_stock_info · `perf`→get_stock_performance · `events`→get_stock_events · `notice`→search_notice · `news`→search_news。

---

## 1 · fetch_ifind.py — Part1 一键取数（确定性，先跑这个）

**它做什么**：调现成 client（`C:/Users/youqi/.claude/skills/ifind-research/scripts/ifind_client.py`，不重复实现传输层）跑 **6 条 query**，把每张 markdown 表解析成结构化 JSON。**只做 FETCH**；分部标签跨年归一、维度选择、单位换算由 agent 在 Phase 2 人工做（因为 iFind 列名逐次漂移）。

**它跑的 6 条 query**（`yr = "<y0>年至<y1>年 各年度"`，`N = 中文名`）：

| key | subcmd | query（已实测措辞） |
|---|---|---|
| `segment_product` | fin | `N yr 分产品主营业务收入金额、占比及毛利率` |
| `segment_industry` | fin | `N yr 分行业主营业务收入金额、占比及毛利率` |
| `segment_region` | fin | `N yr 分地区主营业务收入金额及占比` |
| `dupont` | fin | `N yr 净资产收益率ROE、销售净利率、总资产周转率、权益乘数` |
| `cost` | fin | `N yr 营业总收入、营业总收入同比增长率、营业成本、销售费用、管理费用、研发费用、财务费用、毛利率、销售净利率、期间费用率` |
| `holders` | holders | `N yr 前十大股东及前十大流通股东名称、持股数量、持股比例、股份性质` |

**命令模板**（cwd = 本 skill 根目录）：
```
python scripts/fetch_ifind.py --name 立昂微 --ticker 605358.SH --y0 2015 --y1 2024 \
  --out _workspace/605358/ifind_tables.json
```
- `--y0` 取上市首年或近 10 年起点，`--y1` 取上一自然年（勿写本年，年报未出）。
- **输出**：`_workspace/<ticker>/ifind_tables.json`（`{name,ticker,y0,y1,tables:{6个key:{columns,rows,query}},errors:{}}`）+ `_workspace/<ticker>/raw/<key>.md`（每条原始应答，含 QUERY 行，供人工核对）。
- 脚本末尾会打印 `⚠️ gaps: ...` 列出空表的 key → 按 §3 fallback 补。
- 单条超时 150s；某 key 报 `timeout/unparsed/empty` 时不阻塞其余 5 条。

---

## 2 · 单数据集手动 CLI（补跑/核对用）

当某 key 缺或要改措辞时，直接调 client（**必须在 ifind-research 目录跑**，否则找不到 config/token）：
```
cd C:/Users/youqi/.claude/skills/ifind-research
python scripts/ifind_client.py fin "立昂微 2015年至2024年 各年度 分产品主营业务收入金额、占比及毛利率"
python scripts/ifind_client.py fin "立昂微 2015年至2024年 各年度 分行业主营业务收入金额、占比、毛利率"
python scripts/ifind_client.py fin "立昂微 2015年至2024年 各年度 分地区主营业务收入金额及占比"
python scripts/ifind_client.py fin "立昂微 2015年至2024年 各年度 净资产收益率ROE、销售净利率、总资产周转率、权益乘数"
python scripts/ifind_client.py fin "立昂微 2015年至2024年 各年度 营业总收入、营业成本、销售费用、管理费用、研发费用、财务费用、期间费用率"
python scripts/ifind_client.py holders "立昂微 2020-12-31、2021-12-31、2022-12-31、2023-12-31、2024-12-31 各报告期 前十大股东及前十大流通股东名称、持股数量、持股比例、股份性质"
```
- 加 `--json` 出原始 JSON（用尾部 `指标参数信息` 判 金额/占比、单位）。逃生口：`python scripts/ifind_client.py call stock get_stock_financials -p query="..."`。
- 解析：读 `resp['data']['answer']` 的竖线表；`# 指标参数信息` / `# 行情衍生指标` 之后全部丢弃（fetch_ifind.py 的 `parse_md_table` 已按首个 `#` 截断）。

### 各数据集 query 造句要点（实测）
- **分部收入**：维度由 query 里的词决定——`分产品`→按产品、`分行业`→按行业、`分地区`→按地区；**一次一维度**，三个 cut 跑三次；一句话同时写「分产品、分行业、分地区」会**默认只回按地区**。必带「**金额**」拿绝对额；不写「金额」回的是`数据类型:占比`（≈100 的百分数）。可「金额」+「占比」同求。返回列：`营业收入-主营业务(元)` + top-5 每项的 `项目名称/项目收入/项目成本/项目毛利/项目毛利率(按产品)(排名:第N名)`。
- **总营收+YoY**：同 `fin` 会带 `营业总收入`+`营业总收入(同比增长率)`+`营业收入`+`营业收入(同比增长率)`+单季度版。
- **股东**：多期就把报告期显式列进 query（`2020-12-31、2021-12-31、…`）或写「2010年至2024年 各年年报」。返回 `前十大股东持股比例合计(%)`、`前十大股东持股数量合计(股)` + 各 rank 1–10 的 `股东名称/持股数量(股)/持股比例(%)/持股股份性质(流通A股/受限流通股)/股东性质(境内非国有法人/境外法人/国有法人/境内自然人/国家/其他)`；加「前十大流通股东」额外拿流通口径（`流通股东持股市值(元)` 等）。
- **杜邦**：`净资产收益率ROE、销售净利率、总资产周转率、权益乘数` 一次到手，恒等式 ROE=净利率×周转率×权益乘数≈成立，口径干净无需技巧。
- **成本/费率**：见 §3 的 cost 陷阱（列不稳）。

---

## 3 · 解析陷阱（逐条·均已实测·Phase 2 映射时逐条对照）

1. **分部只 top-5，标签逐年按排名漂移**【Fact】。分部工具只回排名第 1–5 项，>5 条产品线的尾部被并入「其他业务」，无法取第 6+。且公司自报口径**逐年变**（立昂微 硅片某年#1、另年#2；格力 2020「空调」→2024「消费电器」）→ 分部**非跨年标签稳定**，堆积/瀑布图必须**跨年名称归一化映射**，尾部统一并「其他」。

2. **分部收入单位是「元」→ /1e8 转亿**【Fact】。`营业收入-主营业务(元)`、`项目收入` 均为**元**（如 消费电器 148,559,931,838.58 元）；page_model 统一用**亿元**，落表前 `/1e8`。

3. **数值带「万/亿」后缀需解析**【Fact】。部分单元格是 `12.3亿`/`4560万` 文本，不是纯数字；映射时先剥后缀换算再入表，勿直接 `float()`。

4. **cost 查询列不稳定**【Fact】。实测常返回 `销售费用/营业总收入(%)`（销售费率）+ `研发费用/营业总收入(%)`（研发费率）+ 一个 `(管理+研发)/营业总收入` 合计率，**常缺 管理费用绝对值 与 财务费用**。处理：
   - **管理费率 = 合计率 − 研发费率**（[Inference]，标出算法）。
   - **财务费用率若缺 → 再查一次**（单独 `fin "N yr 财务费用、财务费用率"`）**或标「⚠️未查到」**，不猜。
   - 毛利率优先取「销售毛利率」列。
   - 管理费用绝对值缺就用 `管理费用` 本列；`管理费用明细-合计` 多为空，别依赖。

5. **研发费用 2018/2019 前多为空**【Fact】。多数 A 股 ~2018/2019 才把研发从管理费用拆出，早年 `研发费用` 单元格空**是披露所限不是 bug**；财务史深度约到 2007，老股（如格力 IPO 1996）非真·上市首年，早年稀疏。

6. **报告期格式必须 `2024-12-31`**【Fact】。财务/股东日期用报告期格式（`2024-12-31` / 「2024年年报」），不是「2024」也不是「近十年」自由文本；自由文本可能少返回期数 → 显式列报告期或用「2015年至2024年 各年度」。

7. **token 过期 → 重置**。401/403 时 `python scripts/ifind_client.py config --set-token "<JWE>"`（token 在 `C:/Users/youqi/.claude/skills/ifind-research/config.json`，~729 字符无 Bearer 前缀；`IFIND_MCP_TOKEN` 环境变量可覆盖）。

8. **客户端自动剥代理**。client 已 strip `HTTP(S)_PROXY`（国内须直连，走代理会 flaky）；无需手动处理，但别在外层强设代理。

9. **尾部噪声**。每条应答表后跟大段 `指标参数信息` JSON + `行情衍生指标日期提示`，解析时全丢，只留竖线表。

10. **港美股不解析**。`fin/holders` 明确只认 A 股；港美股见 §4 降级。

---

## 4 · A / 港 / 美路由 + 每数据集 主源→备源

**Phase 0 先定市场**。A 股：结构化管线全开。**港股/美股**：iFind `fin/holders/分部` **不解析**（返回「查询结果为空」且不报错，`fetch_ifind.py` 已内置市场闸拦截）→ 走 **§4b 的 `fetch_fundamentals_hkus.py`** 拿结构化基本面，年报公告 `search_notice` + AlphaPai 补文本片段，页面对应图标注「数据受限/口径来自年报」。`search_notice` 是 iFind 侧**唯一触达非 A 股主体的入口**。用结构化 `fin/holders` 前先确认是 A 股代码。

| 数据集 | 主源 | 备源 |
|---|---|---|
| **周线股价(真OHLC,Part2)** | **`scripts/fetch_kline.py`**：AKShare 东财 qfq 日频→周聚合，内置 h/l 自洽+非c-only 校验，不过闸拒绝落盘 | 腾讯 `ifzq.gtimg.cn` qfq 周K（脚本自动切换）/ iFind `performance` / Yahoo(港美) |
| 分部收入+YoY | iFind `fin`（分产品/行业/地区各调一次） | Comein `get_main_business_segments` / AKShare `ak.stock_zygc_em` |
| 历史十大股东 | iFind `holders` | Comein `shareholder_details` / qcc `get_shareholder_info`（工商登记股东，与年报十大流通股东时序会有差） |
| **子公司(持股/主业/区位)** | **qcc**（§5，主场非备胎） | 年报「主要控股参股公司」via iFind `notice` / AlphaPai |
| 10yr ROE+杜邦 | iFind `fin` | Comein `get_financial_snapshot` / AKShare `ak.stock_financial_abstract` |
| 成本/费率（**1.4 毛利率分解，上市以来**） | iFind `fin`（cost 查询已含**税金及附加、所得税费用**——恒等式要同分母的这两项，缺了会把「其他轧差」塞子撑大）；`--y0` 传**上市首年** | 成本明细(料/工/费)→Comein 年报附注/AlphaPai（结构化源无此项） |
| **逐季 毛利率分解（1.4）+ 现金流/CAPEX/折旧（1.4b）** | **`scripts/fetch_quarterly.py`**（iFind **`单季度.*` 原生指标**，一条命令直写 `part1.cost_structure_q` + `part1.cash_capex`）→ 详见 `references/02 §1.4 / §1.4b` | 港美股走 `fetch_fundamentals_hkus.py` 的三表腿自行接同样的键；A 股无备胎 |
| 一致预期/业务定性 | AlphaPai（标【Estimate】） | Comein 纪要原话（带纪要日期） |
| **一致预期分布（1.5 箱线图）** | **`scripts/fetch_fmp_consensus.py`**（FMP `analyst-estimates`：逐期 Low/Avg/High + 覆盖家数；**A/港/美股全覆盖**）→ 详见 `references/11-consensus-boxplot.md` | 港股 etnet 逐家机构（`fetch_fundamentals_hkus.py` 的 `consensus`，**有逐家数才画得出真四分位箱**）/ AlphaPai |
| **beat/miss 兑现记录（1.5）** | **同上脚本**（FMP `earnings`：逐期实际 vs 一致预期；`--kline` 叠财报后 1 周/4 周股价反应） | iFind `fin` 实际值 + 卖方预期手工比对 |

| **历史码龄（1.6 筹码年龄）** | **`scripts/fetch_chip_age.py`**（AKShare 新浪 `stock_zh_a_daily` 日频换手率 → 衰减模型；**仅 A/港股**）→ 详见 `references/12-chip-age.md` | 东财 `stock_zh_a_hist`（**换手率是百分数，与新浪的小数口径不同，别混**）；iFind 作逐点校验闸 `--ifind-check` |

> **1.5 口径红线**（细节见 `11 §0`，每条都有实测反例）：① 箱体是**全距不是四分位**，口径声明不许删；② **FMP 早年区间有一大截是合成的**（002371 FY15–22 恒 0.9448/1.0593；AAPL 26 年恒 0.80/1.20），必须探测剔除，否则结论整个反过来；③ **EPS 历史兑现已下线**（预期与实际分母不同源，会出现「净利 miss 但 EPS beat」），只看收入与净利润；④ A 股年度厚（24–29 家）、**季度极薄（1–4 家）**，薄样本画虚线；⑤ **报告币种≠交易币种**（腾讯报 CNY 交易 HKD）。

> **1.4/1.4b 口径红线**（细节见 `02 §1.4`/`§1.4b`，全部 2026-08-18 实测 688256 钉死）：
> ① **两块都逐季、都走 iFind `单季度.*` 原生指标，不要自己拿累计差分**。
> ② **最贵的坑**：同一张返回表里累计列与单季列**同名并存**（`销售费用` vs `单季度.销售费用`），
> 匹配错就是把 Q4 的全年累计当单季画上去。脚本强制 `单季度.` 前缀，CK-8 d5 查 `src`。
> ③ **1.4 横轴按上市以来**，`listing_year` 必填（CK-8 d4b）；纵轴按最近 8 季稳健截断，被截季度图注点名。
> ④ **「税费」＝税金及附加＋所得税费用，占营业总收入**，不是实际税率（税÷税前利润）——恒等式要求同分母。
> ⑤ **折旧摊销一年只有中报、年报两个披露点**（A 股季报不含现金流量表补充资料），
> **单季折旧在报表上不存在**：单季视图不画它，TTM 视图只在 Q2/Q4 给点（由披露累计数精确凑出）。
> **不摊平、不插值**——CK-8 d6/d6b 会拦。

> **1.6 口径红线**（细节见 `12`）：① **必须给 `--locked-pct`**——换手率分母是总流通股本，控股股东锁仓盘被塞进随机换手池会让模型输出逻辑上不成立的结果（002371 不修正得「长码 2.6%」，而客观 ≥50% 锁仓五年未动）；② **不用 iFind 自然语言接口取数**（返回序列有空值/跳跃/截断，而模型是连乘，断一天整条链就错），iFind 只作校验闸；③ 长码占比**只能当下界读**。

港美股年报片段模板：
```
cd C:/Users/youqi/.claude/skills/ifind-research
python scripts/ifind_client.py notice "<公司> <年度>年度报告 主要控股参股公司 主营业务" --start yyyy-MM-dd --end yyyy-MM-dd --size 5
```

---

## 4b · 港股/美股取数腿 — `fetch_fundamentals_hkus.py`（2026-08-02 实测固化）

**它是 `fetch_ifind.py` 在港美股上的替身**，一条命令拿全 Part1 能拿的部分，并把拿不到的**显式列进 `gaps[]`**。

```
python scripts/fetch_fundamentals_hkus.py --ticker AAPL  --market US --y0 2016 --y1 2026 \
    --out _workspace/AAPL/fundamentals.json
python scripts/fetch_fundamentals_hkus.py --ticker 00700 --market HK --y0 2016 --y1 2026 \
    --out _workspace/00700/fundamentals.json
```
可选：`--sec-filings N`（回溯几份 10-K 取分部，默认 3≈覆盖 5–7 年）、`--no-segments`（跳过 SEC）。
环境变量 `SEC_UA` 设自己的 UA/邮箱（SEC 要求标识来源）。

**产出结构**（口径与 A 股线一致；绝对额一律 `*_yi`＝当地币种亿元）
`meta`（币种/现价/股本/市值/自算PE/`currency_check`）· `tables.{income,balance,cashflow,indicators,dupont,cost_structure,revenue,consensus,valuation_cmp,scale_cmp,profile,pe_history}` · **`gaps[]`** · `sources{}`。

### 各数据集实测结论（锚：AAPL / 00700）

| 数据集 | 美股 | 港股 |
|---|---|---|
| 三表 | 东财 `stock_financial_us_report_em`，**2000 起 26 期** | 东财 `stock_financial_hk_report_em`，**2001 起 25 期** |
| 分析指标 | 26 期，`TOTAL_ASSETS_TR` 直给 → 杜邦四项齐 | 仅 9 期(2017起)，**不给周转率** → `ROA/净利率` 反推 [Inference] |
| 权益乘数 | `总资产/归属于母公司股东权益` 实算 [FACT] | `总资产/股东权益` 实算 [FACT]（实测闭合度 0.94–1.05；退化到 `1/(1−资产负债率)` 时只有 0.85–0.97） |
| 分部收入 | SEC 10-K R-file，AAPL 拿到 product 5 / reportable 5 / region 3 | **无结构化源** |
| 一致预期 | 无 → AlphaPai `roadShow_us` | etnet 逐家机构（腾讯 19 家）+ 脚本算好 `dispersion` |

### 五条必须内化的口径纪律

1. **收入取哪一行**。港股利润表并存 `营业额`(主营) 与 `营运收入`(含其他营业收入)——腾讯 2025 是 7,436.89 亿 vs 7,517.66 亿，差 1.1%。脚本默认取 `营业额` 并把选择写进 `cost_structure.rev_item` 与 gaps，**页面 caliber 必须写明**，勿与 A 股「营业总收入」混用。美股取 `主营收入`。

2. **美股没有销售/管理二分**。多数美股按 SG&A 合并披露，东财只落一行 `营销费用`——实测 AAPL 2025 该行 6.63% 即 Selling 19,524M + G&A 8,077M 合计。脚本给 `sga_rate`(合并) + `sga_split_available`(False 时页面只渲一条 SG&A)。**套 A 股的销售费率/管理费率去解读会得出假结论**。

3. **东财会保留公司早年才披露的科目名**，按名直取会拿到一列 None 且不报错（AAPL『其他营业费用』2021 年后消失）。`series()` 已改为跳过「区间内全空」的候选——自己写别的取数时也照此办理。

4. **SEC 分部不要走 XBRL `companyconcept`**：它只回合并口径无维度（实测 AAPL FY24 只有 391,035M 一个数）。正解是 `FilingSummary.xml` → 取 ShortName 带 `(Details)` 的 R-file → 解析表（单元格行＝成员上下文，多元格行＝科目+数值；`$ in Millions` 在标题行）。成员名跨年报会换写法（`Americas` ↔ `Americas | Operating segments`），**必须归一**，否则渲成两条各缺一半的重复分部线；跨年报合并时**老 filing 只补早年空档，不覆盖新 filing 的重述值**。

5. **币种三口径（最贵的坑）**。财报币种 / 交易币种 / 页面展示币种可互不相同。实测腾讯：自算 PE 19.2（港元市值 ÷ 人民币净利）vs 接口 PE-TTM 16.43，差 17%。`meta.currency_check` 会算这个比值并在偏离 >15% 时报 gap；**查清 fx 前不得把 `mcap_yi` 喂估值范式**，否则整张估值表和赔率错一个汇率。另注意：`scale_cmp.总市值` 与 收盘×股本 对不上、其 `营业总收入` 疑似单季；亿牛 PE 历史实测停更在 2022，**不能用来算「当前 PE 历史分位」**（脚本会按 stale 年数自动降级并报 gap）。

### 港美股结构性缺口（不是 bug，页面必须显式降级）
- **十大股东/派系逐季堆积图**：港美股无 A 股口径的逐季十大流通股东。美股→13F（滞后 45 天、口径不同）；港股→CCASS/披露易（无零鉴权 API）。
- **股权结构树**：qcc 仅覆盖中国大陆主体，境外母公司/子公司不解析；若有大陆运营主体可单独查那一层并注明只是局部。
- **港股分部收入**：只能年报「分部资料」附注 PDF / AlphaPai 纪要人工抄。**CK-3 的 Σ分部=总收入不因此放行**——分部是 Part3 建模地基。

---

## 4.5 · 周线 K 线永远走 fetch_kline.py（真实 OHLC，禁手填）

```
python scripts/fetch_kline.py --ticker 002138 --market A --weeks 160 \
  --out _workspace/002138/kline_weekly.json
```
- 主源 AKShare `stock_zh_a_hist(qfq)` 日频→周聚合（开=周首开/高=周内高/低=周内低/收=周末收）；A股裸代码、港股 5 位、美股尽力。akshare 失败自动切腾讯 `web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=<sym>,week,,,N,qfq`。
- 内置校验（不过闸**拒绝落盘**）：`h≥max(o,c)`、`l≤min(o,c)`、o/h/l/c 齐全、平线蜡烛≤10%、周数≥100。
- 产物 `weekly:[{d,o,h,l,c,v}]` 整体进 `page_model.part2.weekly`；**重拉后必须按日期 join 保 snapIdx/startIdx 下标对齐**（详见 03 §4a）。
- [反面示范·实测踩过] 只填 `{d,c}` 让蜡烛用收盘兜底 → 全是一字线假 K 线，用户直接打回；页面现已内置红警示 + CK-2 拦截。

## 4.6 · ★年报是量价模型的真物理量金矿，而且卖方零覆盖（2026-08-14 阳光电源固化）

`fetch_ifind.py` 拉到的是财务与分部**金额**；**物理量在年报正文的三张固定表里**，
接口给不了，必须自己翻 PDF。阳光实测三处，每一处都直接决定 Part3 能不能拆真量价：

| 年报表名 | 给什么 | 直接用在哪 |
|---|---|---|
| **公司实物销售收入是否大于劳务收入** | **销售量 / 生产量 / 库存量**（阳光光伏逆变器销售量 GW：2023 130 / 2024 147 / 2025 143） | 分部 `hist.q` 的唯一真物理量来源，`p` = 分部收入 ÷ 它 |
| **光伏电站的相关情况**（或该行业的项目明细表） | 逐项列集中式/分布式**当期确收 MW**，加总即该分部的 q（阳光 2025 = 5.395GW） | 电站/工程类分部的 q；除收入得 3.07 元/W，可与年报自述的分布式均价 2.74 元/W 交叉验证 |
| **营业成本构成（分行业）** | 分行业**原材料金额**（阳光储能原材料 202.17 亿 ÷ 储能营业成本 236.82 亿 = 85.4%） | 上游价格敏感性的**分母**——碳酸锂每涨 1 万元/吨传导多少，靠这个才算得出来 |

**这三处的价值在于卖方几乎不碰**：阳光 380 篇语料里，**库存量 61GW（≈43% 年销量）无一篇提及**。
`driver_chain` 里凡是 `tag:"FACT"` 的物理量步骤，优先从这三张表取；取到了就在 `evidence[]` 里
用 `file` 指年报路径 + 表名（不是 `doc_id`，年报通常不在 RAG 库里）。

## 4.7 · ★本机系统代理会掐死国内行情腿 → 一律走 noproxy launcher

macOS 的 `_scproxy` 会把系统代理注入 `requests`/`urllib`，新浪/akshare/申万那几条腿直接超时或
返回 WAF 页；腾讯 gtimg 备援在本机是**永久 501**，指望不上。所有取行情/指数的脚本一律经
`noproxy_run.py` 起（它在 urllib / requests / 环境变量三层把代理关掉，并给 requests 挂 8 次重试）：

```bash
python3 noproxy_run.py <目标脚本.py> [目标脚本的参数...]
```

脚本随包发：`scripts/noproxy_run.py`（也可整份拷到任意工作区）。
**症状识别**：脚本报 `RemoteDisconnected` / `Connection aborted` / 返回 HTML 而不是 JSON，
先怀疑代理，别急着换数据源。（东财 `stock_board_industry_*` 即使加了 noproxy 在本机仍被远端掐，
那条腿是真不可用，行业指数走申万 `index_hist_sw`。）

## 5 · 子公司永远走 qcc（持股% / 区位 / 主业）

**反面示范（实测失败·别踩）**：`ifind_client.py info "立昂微 主要控股子公司及参股公司名称、持股比例、主营业务、注册地"` **静默映射到十大股东数据**（返回 股东/流通股东 列），**无报错**。A 股 stock server 没有 子公司/对外投资 指标（`get_stock_info` 只有 证券基本信息+工商注册+主营简介）。**任何情况不用 iFind 查子公司**。

**正解 = qcc-company MCP（仅中国大陆主体）**，三步：
1. **先锚法定名**：`mcp__qcc-company__get_company_by_query(keyword="立昂微")` → 拿 18 位统一社会信用代码/完整登记名。**铁律**：股票简称/缺完整企业后缀的名（立昂微、宁德时代…）**必须先过 get_company_by_query**，绝不把简称直接喂下游工具（会命中错误子公司主体）。
2. **持股%**：`mcp__qcc-company__get_external_investments(keyword=<法定名/USCC>)` → 对外投资/参股子公司清单 + **持股比例** + 被投主体名 + 状态（**不含主营业务文本**）。
3. **区位**：`mcp__qcc-company__get_branches(keyword=...)` → 分支机构 + **注册地/地址**（注意这是分公司分支，非股权子公司，与 external_investments 互补）。
4. **每家主业**：对每个被投主体链 `mcp__qcc-company__get_company_profile`，或用 iFind `notice` 语义搜年报「主要控股参股公司」表拿「主营业务+注册地+持股比例」文本片段。

映射进 `page_model.part1.ownership.sub_groups:[{group,color,subs:[{name,stake%,business,location}]}]`（按业务分组；**旧键 `part1.subsidiaries` 已废弃，app.js 不渲染，填了=静默丢失**）。qcc 覆盖**中国大陆主体**，港美子公司不解析 → 走年报公告/AlphaPai 补，缺则「⚠️未查到」。

---

## 6 · Phase 1 交付前自查

- [ ] `ifind_tables.json` 六 key 到手；`errors` 为空或已按 §3/§4 fallback 补。
- [ ] 分部三维度（产品/行业/地区）各一张；已知只 top-5、标签待 Phase 2 归一。
- [ ] cost 表已识别缺列（管理费用绝对值/财务费用率），记下反推或待补项。
- [ ] 历史≥5 年（可行则拉到上市首年）；报告期格式无误。
- [ ] 子公司**未**用 iFind；已 qcc 三步（锚名→持股→区位→主业）。
- [ ] 港美股已判定并标注降级；否则确认为 A 股代码。港美股另加四项：`fundamentals.json` 到手；**`gaps[]` 逐条已有归宿**（写进页面标注或交付话术，不是静默略过）；`meta.currency_check` 为 OK 或已写明口径结论；收入口径（港股`营业额`vs`营运收入`／美股 SG&A 合并）已在页面 caliber 注明。
- [ ] 每张表落数带 `(来源:iFind/qcc, 报告期)` + FACT/EST/DNA；缺口写「⚠️未查到」。

> 提醒：本手册只管**取数与解析**；估值/赔率在 Phase 5，口径统一 `赔率 = 目标市值/当前市值 − 1`。时间序列表一律「**时间作列、维度作行**」。
