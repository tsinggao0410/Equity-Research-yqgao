# A2 Palantir(PLTR.US)客户与合同数字底座

> 取数日:2026-09-29。只做取数与核对,不写分析。
> **等级**:FACT = 公司业绩稿 / 10-Q / 10-K / 政府公告;**FACT·会** = 公司业绩电话会上管理层原话(第三方逐字稿);REPORT = 媒体或第三方整理转述。
> **取数路径说明**:本环境挡住 sec.gov、investors.palantir.com、usaspending.gov、businesswire、yahoo 等,WebFetch 全部被挡。WebSearch 用了约 27 次后,会话额度(200 次,与并行 agent 共用)就用完了。之后改从 GitHub 上公开的镜像文本取数,包括他人抽取的 SEC 8-K 业绩稿与投资者演示文本、10-K 片段和电话会逐字稿;读取走 GitHub 代码搜索 + raw.githubusercontent.com。标 FACT 的数,原文件就是公司或政府文件,但**本次没有直接打开 SEC 或政府原页面**,内容来自镜像文本或检索摘要,每条都写明了实际读取渠道。
> 单位:美元(除注明);「亿」= 1 亿美元。合同金额中,**上限(ceiling)≠ 已拨付(obligated)≠ 收入**。

---

## ① 季度客户与合同指标(1Q23–2Q26)

### 表 A-1 客户数(家,TTM 口径:过去 12 个月确认过收入的组织;大型政府机构的各分支单独计)

| 季度(发布日) | 客户总数 | 商业客户数 | 美国商业客户数 |
|---|---|---|---|
| 1Q23(2023-05-08) | 391 [S15] | 数据不可得 | 155 [S23] |
| 2Q23(2023-08-07) | 421 [S16][S24] | 数据不可得 | 161(+35% YoY,+4% QoQ)[S24](161 这个绝对值来自 2Q23 业绩稿的检索摘要,增速来自电话会;155 × 1.04 ≈ 161,两者吻合)|
| 3Q23(2023-11-02) | 453 [S16][S25] | 数据不可得 | 181(+37%,+12% QoQ)[S25] |
| 4Q23(2024-02-05) | 497 [S26] | 数据不可得 | 221(+55%,+22% QoQ)[S26] |
| 1Q24(2024-05-06) | 554 [S27] | 427 [S14] | 262(+69%,+19% QoQ)[S27] |
| 2Q24(2024-08-05) | 593 [S28] | 467 [S14] | 295(+83%,+13% QoQ)[S35] |
| 3Q24(2024-11-04) | 629 [S29] | 498 [S14] | 321(+77%,+9% QoQ)[S29] |
| 4Q24(2025-02-03) | 711 [S18][S30] | 571 [S14] | 382(+73%,+19% QoQ)[S30] |
| 1Q25(2025-05-05) | 769 [S17][S31] | 622(+46% YoY)[S14] | 432(+65%,+13% QoQ)[S31] |
| 2Q25(2025-08-04) | 849 [S17][S32] | 692 [S3](REPORT) | 485(+64%,+12% QoQ)[S32] |
| 3Q25(2025-11-03) | 911 [S17][S33] | 数据不可得(公司只给增速)| 530(+65%,+9% QoQ)[S33] |
| 4Q25(2026-02-02) | 954 [S34] | 数据不可得(公司给 +37% YoY)[S10] | 571(+49%,+8% QoQ)[S10][S34] |
| 1Q26(2026-05-04) | 1,007 [S9] | 数据不可得 | 615(+42%,+8% QoQ)[S8](REPORT) |
| 2Q26(2026-08-03) | 1,049(+24%)[S1][S2] | 870(+26%,上年同期 692)[S3](REPORT) | 653(+35%,+6% QoQ)[S4][S3](REPORT) |

注:① 1Q24–1Q25 的商业客户数取自 1Q25 投资者演示的图表 OCR 读数[S14],已用演示里标注的环比增速逐期勾稽(427→467 +9%、→498 +7%、→571 +15%、→622 +9%,与图上标注一致),读数可信,但仍属图表读数。② 你给的线索「美国商业客户 26Q1 615、26Q2 653」与 REPORT 来源一致;653 × 1/1.06 ≈ 616、485 × 1.35 ≈ 655,可以互相印证,但 Q1/Q2 26 业绩稿原文未能直接打开。

### 表 A-2 签约额(TCV,合同全生命周期潜在价值,含未行权期权)

| 季度 | 总 TCV | 美国商业 TCV | 备注 |
|---|---|---|---|
| 1Q23 | 数据不可得(见 ⑥)| 数据不可得(见 ⑥)| 商业 TCV 1.76 亿(+70%)[S23] |
| 2Q23 | 6.42 亿(+62% QoQ)[S24] | 数据不可得 | |
| 3Q23 | 8.30 亿(+29% QoQ)[S25] | 2.52 亿(按美元加权期限口径 +55% YoY)[S25] | |
| 4Q23 | 11.5 亿(+192% YoY,+38% QoQ)[S26] | 3.43 亿(按美元加权期限口径 +107% YoY)[S26][S37] | 商业 TCV 6.99 亿 [S26] |
| 1Q24 | 9.04 亿(+128%)[S27] | 2.86 亿(+131%)[S27] | 商业 TCV 5.05 亿 [S27] |
| 2Q24 | 9.46 亿(+47%)[S28] | 2.62 亿(+152%)[S28] | 商业 TCV 3.77 亿 [S28] |
| 3Q24 | 11 亿(+33%,+16% QoQ)[S29] | 2.97 亿(+13% QoQ)[S29] | 商业 TCV 6.12 亿 [S29] |
| 4Q24 | 17.9 亿(+56%,+63% QoQ)[S30] | 8.03 亿(+134%,+170% QoQ)[S30] | 商业 TCV 9.95 亿 [S30] |
| 1Q25 | 15 亿(+66%)[S31] | 8.10 亿(+183%)[S13] | |
| 2Q25 | 22.7 亿(+140%)[S12] | 8.43 亿(+222%)[S12] | 商业 TCV 11 亿;ACV 6.84 亿 [S32] |
| 3Q25 | 27.6 亿(+151%)[S11] | 13.1 亿(+342%)[S11] | 商业 TCV 14 亿 [S33] |
| 4Q25 | 42.62 亿(+138%)[S10] | 13.44 亿(+67%)[S10] | 商业 TCV 26 亿;国际商业 TCV 13 亿(长期续约)[S34];FY25 总 TCV 108 亿(+128%)[S10] |
| 1Q26 | 24.1 亿(+61%)[S7] | 11.76 亿(+45%)[S7][S8] | |
| 2Q26 | 33.73 亿(+49%)[S1][S5] | 21.32 亿(+153%)[S1][S6] | 与线索 21.32 亿一致 |

### 表 A-3 大额交易笔数(当季签约,按单笔 TCV)

| 季度 | ≥100 万 | ≥500 万 | ≥1,000 万 |
|---|---|---|---|
| 1Q23 | 数据不可得 | 数据不可得 | 数据不可得 |
| 2Q23 | 数据不可得 | 数据不可得 | 数据不可得 |
| 3Q23 | 80 [S25] | 29 [S25] | 12 [S25] |
| 4Q23 | 103 [S26] | 数据不可得 | 数据不可得 |
| 1Q24 | 数据不可得 | 数据不可得 | 数据不可得 |
| 2Q24 | 数据不可得 | 数据不可得 | 27 [S35][S28] |
| 3Q24 | 104 [S29] | 数据不可得 | 数据不可得 |
| 4Q24 | 129 [S36](REPORT)| 数据不可得 | 32 [S30] |
| 1Q25 | 139 [S13] | 51 [S13] | 31 [S13] |
| 2Q25 | 157 [S12] | 66 [S12] | 42 [S12] |
| 3Q25 | 204 [S11] | 91 [S11] | 53 [S11] |
| 4Q25 | 180 [S10] | 84 [S10] | 61 [S10] |
| 1Q26 | 206 [S7] | 72 [S7] | 47 [S7] |
| 2Q26 | 220 [S1][S5][S6] | 98 [S1][S5][S6] | 73 [S1][S5][S6] |

补充:3Q25 其中美国商业 ≥100 万 83 笔、≥500 万 40 笔、≥1,000 万 21 笔 [S33]。1Q24 电话会称「美国商业 1Q24 签 136 笔 vs 1Q23 70 笔」,但没写金额门槛,不入表 [S27]。

### 表 A-4 净收入留存率、RPO、剩余交易价值(RDV)

NDR(公司口径)=(本期 TTM 中来自上期 TTM 客户的收入)/(这些客户上期 TTM 收入),不含近 12 个月新获客户 [S10]。
RPO = 不可撤销、已签约未确认收入(不含 ≤12 个月合同;政府合同多有便利终止条款,所以 RPO 以商业为主)[S10][S26]。
RDV = 期末合同剩余总价值,假设全部期权行权、不终止 [S10]。

| 季度 | NDR | RPO 合计 | 其中短期 / 长期 RPO | 总 RDV | 美国商业 RDV |
|---|---|---|---|---|---|
| 参考 4Q22 | 115% [S22] | 9.73 亿 [S22] | — | 37 亿 [S22] | — |
| 1Q23 | 数据不可得 | 数据不可得 | — | 数据不可得 | 数据不可得 |
| 2Q23 | 数据不可得 | 9.68 亿 [S24] | — | 34 亿 [S24] | 数据不可得 |
| 3Q23 | 107% [S25] | 9.88 亿 [S25] | — | 37 亿 [S25] | 仅增速:剔除战略商业合同后 +23% YoY / +27% QoQ [S25] |
| 4Q23 | 108% [S26] | 12 亿(+28% YoY)[S26] | — | 39 亿(+5% QoQ)[S26] | 仅增速:+32% YoY / +28% QoQ [S26] |
| 1Q24 | 111% [S27] | 13 亿(+39%)[S27] | — | 41 亿(+22%)[S27] | 仅增速:+74% / +14% [S27] |
| 2Q24 | 114% [S28] | 13.7 亿 [S12] | 6.8 亿 / 6.9 亿 [S12] | 43 亿(+26%)[S28] | 仅增速:+103% / +11% [S28][S35] |
| 3Q24 | 118% [S29] | 15.7 亿 [S11] | 8.4 亿 / 7.3 亿 [S11] | 45 亿(+22%)[S29] | 仅增速:+73% / +7% [S29] |
| 4Q24 | 120% [S30] | 17.3 亿 [S10] | 9.0 亿 / 8.3 亿 [S10] | 54.3 亿(+40%,+20% QoQ)[S30] | 仅增速:+99% / +47% [S30] |
| 1Q25 | 124% [S13] | 19.0 亿 [S10] | 10.0 亿 / 9.0 亿 [S10] | 59.7 亿(+45%)[S31] | 23.2 亿(+127%)[S13] |
| 2Q25 | 128% [S12] | 24.2 亿 [S10] | 14.0 亿 / 10.2 亿 [S10] | 71 亿(+65%)[S32] | 27.9 亿(+145%)[S12] |
| 3Q25 | 134% [S11] | 26.0 亿 [S10] | 14.6 亿 / 11.4 亿 [S10] | 86 亿(+91%)[S33] | 36.3 亿(+199%)[S11] |
| 4Q25 | 139% [S10] | 42.1 亿(+144%)[S10][S34] | 25.9 亿 / 16.2 亿 [S10] | 112 亿(+105%,+29% QoQ)[S34] | 43.8 亿(+145%)[S10] |
| 1Q26 | 150% [S8](REPORT)| 约 45 亿(REPORT,电话会要点)[S55] | 数据不可得 | 118 亿(+98%,+6% QoQ)[S8][S55](REPORT) | 49.2 亿(+112%)[S7][S8] |
| 2Q26 | 157%(+700bp QoQ)[S4](REPORT)| 数据不可得 | 数据不可得 | 131 亿(+83%)[S4](REPORT) | 62.38 亿(+124%,+27% QoQ)[S1][S6] |

注:2Q26 业绩稿 Ex.99.1 要点里没有 NDR 这一行,157% 出自电话会 [S6][S4]。FY2025 10-K 称另有约 123 亿未拨款的 IDIQ 上限**不计入** RDV(REPORT 转引)[S41][S42]。

### 表 A-5 前 20 大客户平均收入(过去 12 个月,百万美元)

| 期间 | 数值 | 来源 |
|---|---|---|
| 2019 | 24.8 | FY2020 年报 [S20] |
| 2020 | 33.2 | FY2021 10-K [S19][S20] |
| 2021 | 43.6(+31%)| FY2021 10-K [S19] |
| 2022 | 约 49(+13%,电话会四舍五入)| [S22] |
| 2023 | 54.6(10-K)/ 55(电话会,+11%)| [S18][S26] |
| 2024 | 64.6(10-K)/ 65(电话会,+18%)| [S18][S30] |
| 2025 | 94(电话会,+45%)/ 93.9(10-K,REPORT 转引)| [S34][S42] |
| 季度 TTM | 2Q23 53、3Q23 54、1Q24 55、2Q24 57、3Q24 60、1Q25 70、2Q25 75、3Q25 83、2Q26 124(+67%,REPORT)| [S24][S25][S27][S28][S29][S31][S32][S33][S3] |

1Q26 数据不可得。

### 表 A-6 训练营(AIP Bootcamp)公开说法

| 时点 | 说法 | 来源 |
|---|---|---|
| 2023-10 | 设定目标:一年内完成 500 场 AIP 训练营 | [S26] |
| 2024-02-05 | 「已完成 560 余场训练营,覆盖 465 家组织」;Karp:「两年前做了 92 个试点,去年(主要是下半年)做了 500 多场训练营」 | [S26] |
| 2024-05-06 | 「累计已有 915 家以上组织参加训练营」 | [S27] |
| 2024 年以后 | 公司不再给累计场次或组织数,只举个案(如「训练营后 5 周转 5 年期 2,600 万 ACV 合同」)| [S31][S32] |

---

## ② 重大合同表(上限与已拨付分列)

> 上限 = 合同 / IDIQ / BPA 可下单的最高额;已拨付 = 政府已承诺的资金(USAspending 口径);二者都**不是**收入。拨付数多为第三方从 USAspending 整理而来,标 REPORT。

### 表 B-1 美国国防

| 客户 / 机构 | 合同 | 签约 / 公告日期 | 上限(ceiling)| 已拨付 / 首期(obligated)| 期限 | 内容 | 来源 |
|---|---|---|---|---|---|---|---|
| 美国陆军 | 企业服务协议(Enterprise Agreement / ESA,IDIQ W519TC25D0039)| 2025-07-31 授予;2025-08-01 陆军公告 | 100 亿 | 授予时约 1,000 万(REPORT);截至 2026-03 已拨 3.828 亿,共 19 张任务单:含 CDAO Maven 2.276 亿、Army Vantage SaaS 1.034 亿、FORSCOM 5,200 万、WS360 1,510 万(REPORT)| 10 年 | 把 75 份合同(15 份主承包 + 60 份相关 / 分包)并成一份;单一来源(FAR 6.302-1)| [S32][S38][S42] |
| 国防部 CDAO | Maven Smart System 原型 / 生产合同(IDIQ W911QX24D0012)| 2024-05-29 | 4.8 亿 | 首期订单 1.53 亿 | 5 年(至 2029)| 把 AI 目标识别与指挥控制扩到各作战司令部和联合参谋部;固定价格,按订单拨款 | [S28][S39][S41] |
| 国防部 CDAO | Maven 上限上调(修改 P00005)| 2025-05-20(电话会 2025-08-04 披露)| +7.95 亿 → 约 12.75 亿(常写作「13 亿」)| 截至约 2026-03 累计已拨 2.927 亿,约占上限 23%(REPORT)| 至 2029 | 为作战司令部需求扩容的软件许可 | [S32][S40][S42] |
| 国防部 | Maven 列为正式「项目档案」(Program of Record)| 2026-08-25 报道 | FY27 预算申请 23 亿 / 5 年(与联合火力网 Joint Fires Network 合并列项,不全属 Palantir)| 数据不可得 | FY27 起 5 年 | 从原型转为长期预算项目 | [S45][S47](REPORT)|
| 国防部 CDAO | Open DAGIR | 2024 年二季度 | 3,300 万(合同额)| 数据不可得 | 数据不可得 | 第三方在 Maven 上开发应用 | [S28] |
| 美国陆军 | TITAN(战术情报目标接入节点)第 3 阶段原型(OTA)| 2024-03-06 | 1.784 亿 | 数据不可得 | 数据不可得 | 10 套原型(5 Advanced + 5 Basic),软件公司首次当硬件项目主承包 | [S27](FACT·会 称「超过 1.78 亿」)[S44] |
| 美国陆军 | TITAN 首批生产订单 | 2026-09-01 | 两张交付订单合计 1.92 亿:Palantir 1.27 亿,Anduril 6,500 万(经陆军 EA 下单)| 数据不可得 | 交付期 18 个月 | 8 套生产型(4 Advanced + 4 Basic);FY27 预计追加订单 | [S44](REPORT)|
| 美国陆军 | Army Vantage(陆军数据平台)| 首份 2019;2024-12 延期 | 2019 原始合同金额:数据不可得;2024 延期金额:数据不可得 | 经 EA 下的 Vantage SaaS 任务单 1.034 亿(REPORT)| 2024 延期「最长 4 年」| 陆军数据平台;2025-10 陆军发备忘录要求全军向 Vantage 集中 | [S30][S33][S42] |
| 美国陆军 | AI/ML 能力扩展 | 2023-09(电话会 2023-11-02 称「数周前」)| 2.5 亿 | 数据不可得 | 3 年 | 支持作战司令部、各军种、情报界和特种部队测试和扩展 AI/ML | [S25] |
| 美国特种作战司令部(SOCOM)| 多年期合同 | 2023 年二季度 | 4.63 亿 | 数据不可得 | 多年(具体年限不可得)| 数据不可得 | [S24] |
| 美国空军与太空军 | 新合同 | 2023 年二季度 | 1.1 亿(合计)| 数据不可得 | 数据不可得 | 数据不可得 | [S24] |
| 太空军太空系统司令部(SSC)| 交付订单 | 2025 年二季度 | 2.18 亿(订单额)| 数据不可得 | 数据不可得 | 支持太空与空中作战的多域同步作战 | [S32] |
| 美国海军 | ShipOS(造船供应链)| 2025 年四季度(电话会 2026-02-02 披露)| 最高 4.48 亿 | 数据不可得 | 数据不可得 | Foundry/AIP 部署到潜艇工业基础(通用动力电船公司、朴茨茅斯海军船厂等);潜艇排产由「数周」降到「1 小时内」 | [S34][S10] |
| 国防部(副部长 Feinberg 备忘录)| 非合同,内部指令 | 2026-08-13 报道 | 截至 2027-03-31 最高 2.439 亿;另要求为 2027-04-01 至 2028-12-28 找追加用途 | 不适用 | — | 国防工业基础效率;**尚非正式授标** | [S46](REPORT)|

### 表 B-2 美国联邦民事机构

| 客户 / 机构 | 合同 | 签约 / 公告日期 | 上限 | 已拨付 / 首期 | 期限 | 内容 | 来源 |
|---|---|---|---|---|---|---|---|
| 移民与海关执法局(ICE)| 调查案件管理系统 ICM(70CTD022FR0000170)| 2022 | **口径冲突**:1.393 亿 vs 1.45 亿(均 REPORT)| 数据不可得 | 至 2026-04,拟单一来源续签 | 刑事和民事调查案卷管理 | [S43][S42] |
| ICE | ImmigrationOS(移民全流程操作系统),为 ICM 订单的修改 | 2025-04(Axios 2025-05-01 报道)| 3,000 万 | 数据不可得 | 原型 2025-09-25 交付;完整能力 2027-09 | 执法目标排序、自主离境追踪、移民全流程管理;单一来源 | [S43][S42](REPORT)|
| ICE | ImmigrationOS 许可与运维任务单 | 2025-09-25 | 2,990 万 | 数据不可得 | 数据不可得 | 许可续期、运维和适应性维护 | [S43](REPORT)|
| ICE | 2026 年 BPA 下的两张调用单(70CTD026FC0000012 / …0018)| 2026 | 当前授标额 8,627 万 / 4,585 万(后者待核)| 数据不可得 | 数据不可得 | 数据不可得 | [S41](REPORT)|
| 国土安全部(DHS)| 部门级 BPA(70RTAC26A00000001)| 2026-02(日期冲突:2-12 vs 2-19)| 10 亿 | 截至 2026-03 已拨 1,870 万(1.9%)| 至 2031 | CBP、ICE、USCIS、特勤局等可直接下单,无需另行竞标 | [S42][S50](REPORT)|
| 疾控中心(CDC)| 公共卫生数据基础设施 | 数据不可得 | 4.43 亿 | 数据不可得 | 5 年 | 公共卫生数据现代化 | [S42](REPORT)|
| 卫生与公众服务部(HHS)| Foundry 平台 BPA(75P00122A00010)| 2022 | 9,000 万 | 4,820 万(SHARE BPA 口径,REPORT)| 5 年 | NIH/CDC/FDA 共用 | [S42](REPORT)|
| 国立卫生研究院(NIH/NCATS)| 3 份单一来源 IDIQ | 2021 / 2022 / 2023 | 5,950 万 + 6,500 万 + 6,940 万 = 1.939 亿 | 2023 那份已用 100% | 数据不可得 | N3C 新冠数据飞地等科研平台 | [S42](REPORT)|
| ARPA-H | AI/ML 合同 | 2024-06 | 1,900 万 | 数据不可得 | 2 年 | 数据不可得 | [S42](REPORT)|
| 国务院 | 企业数据管理平台 BPA ×2 | 2022-09 / 2025-09 | 9,960 万 + 4.10 亿 = 5.096 亿 | 9,880 万(10 张任务单)| 数据不可得 | 企业数据管理平台 | [S42](REPORT)|
| 国税局(IRS)| 线索案件分析 BPA ×2 | 2018 / 2023 | 1.571 亿 + 1.0 亿 = 2.571 亿 | 1.96 亿(26 张任务单)| 新 BPA 至 2028 | SNAP、刑事调查运维、企业数据平台 | [S42](REPORT)|
| 退伍军人事务部(VA)| 数据不可得 | 2026 | 3.854 亿(SAM 线索,**未与实际授标核对**)| 数据不可得 | 数据不可得 | 数据不可得 | [S41](REPORT,待核)|
| USCIS | VOWS(婚姻移民欺诈审查平台)第 0 阶段 | 2025-10 | 不足 10 万 | 数据不可得 | 分 3 阶段 | 婚姻类移民申请审查 | [S42](REPORT)|

### 表 B-3 国际政府

| 客户 / 机构 | 合同 | 签约 / 公告日期 | 上限 | 已拨付 / 首期 | 期限 | 内容 | 来源 |
|---|---|---|---|---|---|---|---|
| 英国 NHS England | 联邦数据平台(FDP)| 2023-11 | 3.30 亿英镑(按用量计费合同中的「分配额」,是上限而非保底)| 数据不可得 | 7 年(最长);报道称 2027-02 有中途解约条款 | 整合医院与区域数据,用于排程、候床和积压管理;截至 2024-11 已有 87 家急症信托和 28 个综合护理委员会签约使用 | [S26][S30][S41][S48][S54] |
| 英国国防部(MOD)| 企业协议(后续协议)| 2025-12-30 | 2.406 亿英镑(不含增值税)| 数据不可得 | 3 年,2026-04 起(REPORT)| 单一来源 | [S41][S49][S50][S54](REPORT)|
| 英国国防部 | 2025 年「战略合作」(常被引用的 15 亿英镑投资 / 7.5 亿英镑机会)| 2025-09(待核)| 数据不可得 | 数据不可得 | 数据不可得 | 数据不可得 | 本次未取到任何可核对出处,见 ⑥ |
| 北约(NATO NCIA)| Maven Smart System NATO | 2025 年一季度签约(电话会 2025-05-05 披露);北约公告约 2025-04-14(待核)| 金额未披露:数据不可得 | 数据不可得 | 数据不可得 | 作为北约 32 个成员国的 AI 指挥控制系统 | [S31] |

### 表 B-4 商业大单(管理层在电话会披露,客户匿名;数字为 TCV 或 ACV)

| 时点 | 客户描述 | 金额与期限 | 来源 |
|---|---|---|---|
| 4Q23 | 最大租车公司之一、最大电信公司之一、最大药企之一 | 各超过 2,500 万 | [S26] |
| 4Q23 | 美国消费品控股公司 | 5 年 1,900 万 | [S26] |
| 4Q24 | 美国最大连锁药房之一 | TCV 6,700 万 | [S30] |
| 4Q24 | 美国电信公司 | TCV 4,000 万(扩容)| [S30] |
| 1Q25 | 大型医疗公司 | 5 年,ACV 2,600 万 | [S31] |
| 1Q25 | 全球银行 | 3 年,ACV 1,900 万 | [S31] |
| 2Q25 | 医疗公司 | TCV 8,800 万 | [S32] |
| 4Q25 | 医疗公司 | 9,600 万 | [S34] |
| 4Q22 | 日本损保控股(Sompo)| 5 年 5,000 万(扩容)| [S22] |

2Q26 的「跨国科技公司 3 年 3.7 亿」等只有单一弱来源,没有入表,见 ⑥。

---

## ③ 美国联邦政府对 Palantir 的年度合同拨付(USAspending 口径)

> 本环境打不开 usaspending.gov。以下全部是第三方从 USAspending 整理后的转述(REPORT),**没有独立核验**,口径是否包含分包也不明。

| 财年(10 月–次年 9 月)| 拨付额 | 来源 |
|---|---|---|
| FY2019 | 数据不可得 | — |
| FY2020 | 数据不可得 | — |
| FY2021 | 数据不可得 | — |
| FY2022 | 3.768 亿 | [S42](与 FY2025 对比时给出;并称 FY22–25 三年 CAGR 39.4%,与 3.768→10.21 自洽)|
| FY2023 | 数据不可得 | — |
| FY2024 | 5.412 亿 | [S42] |
| FY2025 | 10.21 亿(+88.6%)| [S42] |
| FY2026 截至约 2026-03 | 2.86 亿 / 4.33 亿(两次查询日期不同,数值不一)| [S42] |

其他口径:
- Defense One(2026-08-13)引 GovTribe:「2024 年以来获拨付 32 亿,约一半为非竞争性合同」[S46](REPORT)。
- 「2025 年国防合同拨付近翻倍至 9.705 亿」[S42](REPORT,口径为日历年还是财年不明)。
- Treasury/IRS:FY2024 2,490 万 → FY2025 7,200 万 [S42](REPORT)。

按机构拆分(累计拨付,非年度;REPORT)[S42]:

| 机构 | 累计拨付 | 备注 |
|---|---|---|
| 国防部(DoD)| 23.1 亿–24.35 亿(两次查询)| 同源又称其中陆军 23.8 亿、空军 6.42 亿、海军 7,900 万,三者加总超过 DoD 合计,**自相矛盾**,不宜直接用 |
| HHS | 4.05 亿 | |
| DHS | 2.95 亿–3.20 亿 | 其中 ICE 3 亿以上(FALCON、ICM)|
| 司法部(DOJ)| 2.09 亿 | |
| 财政部 / IRS | 1.95 亿–1.96 亿 | |

---

## ④ 客户集中度

| 指标 | 数值 | 期间 / 口径 | 来源 |
|---|---|---|---|
| 最大单一客户收入占比 | 数据不可得(镜像里没找到相关表述)| — | — |
| 前 20 大客户收入占比 | 公司不披露百分比;**作者计算**:20 × 平均收入 ÷ 总收入 → FY2024 20×64.6/2,865.5 ≈ 45.1%;FY2025 20×93.9/4,475.4 ≈ 42.0%;2Q26 TTM 20×124/(1,181+1,407+1,633+1,935)≈ 40.3% | TTM | 分子 [S18][S42][S3];分母 [S10][S11][S7][S1] |
| 政府收入占比 | FY2021 58%(10-K)| 年度 | [S19] |
| | FY2023 政府 12.2 亿 / 商业「超过 10 亿」→ 约 55%(作者计算,商业口径不精确)| 年度 | [S26] |
| | FY2024 政府 15.7 亿 / 总收入 28.655 亿 → 54.8%(作者计算)| 年度 | [S30][S10] |
| | FY2025 政府 24.02 亿 / 总收入 44.754 亿 → 53.7%(作者计算;10-K 表述为 54%,REPORT 转引)| 年度 | [S34][S10][S42] |
| 美国政府收入 | FY2023 9.21 亿;FY2024 12 亿;FY2025 18.55 亿;2Q26 单季 8.09 亿(+90%)| 年度 / 季度 | [S26][S30][S10][S6] |
| 美国收入占比 | 2021 57%;2024 66%;2025 74.2%(作者计算 33.20/44.75)| 年度 | [S19][S18][S10] |
| 战略商业合同(SPAC 投资类客户)收入 | FY2024 5,229 万;FY2025 1,526 万;4Q25 209 万 | 年度 / 季度 | [S10] |
| RDV 以外的 IDIQ 上限 | 约 123 亿未拨款 IDIQ 上限不计入 RDV(FY2025 10-K)| 2025-12-31 | [S41][S42](REPORT 转引 [S21])|

---

## ⑤ 企业客户典型案例(效果数字均为客户或公司口径,经电话会转述)

| 客户 | 年份(披露时点)| 用途 | 效果 | 来源 |
|---|---|---|---|---|
| BP | 2023(2023-05-08)| Foundry 用于油气生产运营 | 生产成本约降 60%,从每桶 14 美元降到 6 美元以下(BP 口径)| [S23] |
| 坦帕总医院(Tampa General)| 2023(2023-08-07);2024(2024-08-05)| 病人调度与床位分配;2024 年签 7 年扩容,用 AIP 做护理协同系统 | 病人等候时间 −28%,床位分配管理耗时 −83%;平均住院日 −30% | [S24][S28] |
| HCA | 2023(2023-08-07)| 护士排班 | 每月排班从 10–20 小时降到 1 小时 | [S24] |
| 克利夫兰诊所 | 2023(2023-08-07);2024(2024-05-06)| 病人转院接收;签 10 年扩容 | 上线 4 个月接收转院病人 +8.5% | [S24][S27] |
| 切尔西-威斯敏斯特 NHS 信托 | 2023(2024-02-05)| 手术积压管理 | 住院候诊名单 −28%;因术前评估遗漏导致的当日取消手术减半 | [S26] |
| 劳氏(Lowe's)| 2024(2024-05-06)| 客服 AI(1,000 余名坐席)| 逾期任务 −75%;4 个月落地,上线 3 周内 1,000 名用户 | [S27] |
| 通用磨坊(General Mills)| 2024(2024-05-06)| 供应链(只覆盖部分网络)| 年均节省约 1,400 万美元(客户高管原话)| [S27] |
| Associated Materials | 2024(2024-11-04)| 9 个月上线 10 余个业务用例 | 准时足额交付率从 40% 升到 90% | [S29] |
| Trinity Rail | 2024(2024-11-04)| 3 个月做出可用工作流 | 利润影响 3,000 万美元 | [S29] |
| Anduril | 2024(2025-02-03)| 供应短缺预警(Warp Speed)| 预判和响应供应短缺的效率最高提升 200 倍(Anduril CIO 口径)| [S30] |
| 松下能源北美 | 2024(2025-02-03)| AIP 维修助手 | 服务 350 名技师,工厂日产 550 万颗电池;降低停机(无量化)| [S30] |
| 力拓(Rio Tinto)| 2024(2025-02-03)| 续约 4 年;非结构化数据 | 协调 53 列无人驾驶列车,每列 240 节车厢(规模描述,非改善幅度)| [S30] |
| 沃尔格林(Walgreens)| 2025(2025-05-05)| 门店端 AI 工作流 | 8 个月覆盖 4,000 家门店,相当于每天 3,840 亿个决策自动化(客户高管口径)| [S31] |
| 花旗(Citibank)| 2025(2025-08-04)| 客户开户 KYC | 从 9 天缩到「几秒」| [S32] |
| 房利美(Fannie Mae)| 2025(2025-08-04)| 抵押贷款欺诈识别 | 从 2 个月缩到「几秒」| [S32] |
| Nebraska Medicine | 2025(2025-08-04)| 出院流程 | 出院休息区利用率 +2,100%,相当于多出一个病区 | [S32] |
| 李尔(Lear)| 2025(2026-02-02)| 全公司推广 AIP;2025 签 5 年续约 | 从 100 名用户、4 个用例扩到 16,000 名用户、280 个用例 | [S34][S32] |
| 泰森食品(Tyson Foods)| 2022(2023-02-13)| Foundry 20 个用例 | 创造 2 亿美元价值 | [S22] |
| 美国海军 / 通用动力电船 | 2025(2026-02-02)| ShipOS 潜艇排产 | 潜艇计划排产从数周降到 1 小时内;物料审查从数小时降到数分钟 | [S10] |
| 美国陆军第 18 空降军 | 2024(2024-11-04)| Maven 目标选定 | 目标选定小组从伊拉克战争时的约 2,000 人降到约 20 人 | [S29] |
| 空客(Airbus)| — | 管理层只提到「帮助 A350 和单通道机型增产」| 效果数字:数据不可得 | [S25] |
| Wendy's / 联合健康 | — | — | 数据不可得(本次镜像文本里没有)| — |

---

## ⑥ 取不到的数据与待核事项

1. **1Q23–2Q23 的交易笔数、NDR、1Q23 的 RDV/RPO**:电话会镜像里没有,业绩稿原文打不开。1Q23 总 TCV 在一次 WebSearch 摘要里写作「3.97 亿(+60%)」,与 2Q23「6.42 亿、环比 +62%」反推的约 3.96 亿吻合,但没见到原文,**未入表**。1Q23 美国商业 TCV 摘要写「1.24 亿(+170%)」,与 1Q24「2.86 亿、+131%」反推值吻合,同样未入表。
2. **4Q23–3Q24 的 ≥500 万 / ≥1,000 万笔数、1Q24 与 2Q24 的 ≥100 万笔数**:当季业绩稿只写了部分数(例如 2Q24 只写「27 笔 ≥1,000 万」),完整三档在投资者演示里,本次拿不到。
3. **商业客户数**:1Q23–4Q23、3Q25、4Q25、1Q26 缺绝对值。4Q25 只有「+37% YoY」,按 571 × 1.37 ≈ 782 可以反推,仅供核对,未入表。
4. **2Q26 RPO、1Q26 前 20 大客户平均收入**:数据不可得。
5. **2Q24 之前的美国商业 RDV 绝对值**:公司只给增速。
6. **合同金额缺口**:Army Vantage 2019 原始合同额和 2024-12 延期金额(常见说法 4.007 亿 / 6.19 亿,本次没取到出处);英国国防部 2025-09「战略合作」金额;北约 MSS NATO 合同额;SOCOM、ShipOS、太空军等各合同的已拨付额;CDC 4.43 亿合同的签约日期。
7. **ICE ICM 合同额口径冲突**:1.393 亿 [S43] vs 1.45 亿 [S42],两者都是第三方整理。DHS BPA 日期冲突:2026-02-12 [S42] vs 2026-02-19 [S50]。
8. **USAspending 年度拨付**:FY2019–FY2021、FY2023 缺;已有数值全部来自同一个第三方整理(S42),而且该来源的 DoD 分项自相矛盾,建议在网络可达时直接查 usaspending.gov(UEI FSY4LVSBGWB7)复核。
9. **最大单一客户收入占比**:10-K 相关段落本次读不到。
10. **单一弱来源,未入表**:2Q26「跨国科技公司试点转 3 年 3.7 亿合同」「非营利医疗系统 3 年 3,700 万」「全球资产管理公司 3 年 3,500 万」「Agent Camp 5 个月转 1,500 万」只出现在一篇 GitHub 自动新闻稿(vincentzli/clawnews),没有第二来源。
11. **已知线索的核对结论**:1,049(+24%)✔;商业 870 ✔(REPORT);美国商业 TCV 21.32 亿(+153%)✔;NDR 157% ✔(电话会 / REPORT,Ex.99.1 要点里没有);220 / 98 / 73 ✔;RDV 131 亿 ✔(REPORT);美国商业 615 / 653 ✔(REPORT,可相互勾稽);2025 前 20 大平均 9,390 万 ✔(电话会 9,400 万,FACT·会;10-K 9,390 万为 REPORT 转引)。

---

## ⑦ 来源清单

| 编号 | 标题 | URL | 日期 | 等级 / 读取渠道 |
|---|---|---|---|---|
| S1 | Palantir Q2 2026 业绩稿(8-K Ex.99.1)| https://www.sec.gov/Archives/edgar/data/0001321655/000132165526000039/a2026q2ex991pressrelease.htm | 2026-08-03 | FACT;经 WebSearch 摘要与 S6 转录读取 |
| S2 | Palantir 10-Q(截至 2026-06-30)| https://www.sec.gov/Archives/edgar/data/0001321655/000132165526000041/pltr-20260630.htm | 2026-08 | FACT;检索摘要 |
| S3 | Zacks:Can Palantir's Customer Surge Sustain Its AI-Driven Growth Momentum? | https://www.zacks.com/stock/news/2983398/can-palantir-s-customer-surge-sustain-its-ai-driven-growth-momentum | 2026-08 | REPORT |
| S4 | Nasdaq:Palantir Technologies Q2 Earnings Call Highlights | https://www.nasdaq.com/articles/palantir-technologies-q2-earnings-call-highlights | 2026-08 | REPORT |
| S5 | Pulse2:Palantir Closes 220 Deals Worth At Least $1 Million As Revenue Jumps 93% For Q2 2026 | https://pulse2.com/palantir-closes-220-deals-worth-at-least-1-million-as-revenue-jumps-93-for-q2-2026/ | 2026-08-03 | REPORT |
| S6 | InvestmentVault:PLTR — Q2 2026 Earnings IR Verification(对照 Ex.99.1 逐项核对的笔记)| https://github.com/jameswong2011/InvestmentVault/blob/main/Research/2026-08-12%20-%20PLTR%20-%20Q2%202026%20Earnings%20IR%20Verification.md | 2026-08-12 | REPORT(转录 FACT)|
| S7 | Palantir Q1 2026 业绩稿(8-K Ex.99.1;BusinessWire 转载)| https://www.sec.gov/Archives/edgar/data/0001321655/000132165526000026/a2026q1ex991pressrelease.htm ;https://finance.yahoo.com/markets/stocks/articles/palantir-reports-q1-2026-u-200500041.html | 2026-05-04 | FACT;原文摘录经 GitHub ghsaboias/ai-newsletter(pipeline/output/ai/2026-05-05/research.json)与检索摘要读取 |
| S8 | TIKR:Palantir Q1 2026 Earnings: U.S. Revenue Crosses 100% Growth for the First Time | https://tikr.com/blog/palantir-q1-2026-earnings-u-s-revenue-crosses-100-growth-for-the-first-time | 2026-05 | REPORT |
| S9 | Palantir 10-Q(截至 2026-03-31)| https://www.sec.gov/Archives/edgar/data/0001321655/000132165526000028/pltr-20260331.htm | 2026-05 | FACT;检索摘要 |
| S10 | Palantir Q4 2025 业绩稿 + Q4 2025 Business Update(演示)| https://www.sec.gov/Archives/edgar/data/1321655/000132165526000004/a2025q4ex991earningsrelease.htm ;镜像 https://github.com/bencrowe0/citibank-arp/blob/master/outputs/p2_palantir/extracted/PLTR_FQ4_2025.txt | 2026-02-02 | FACT;镜像全文 |
| S11 | Palantir Q3 2025 业绩稿 + 演示 | https://www.sec.gov/Archives/edgar/data/1321655/000132165525000130/a2025q3ex991earningsrelease.htm ;镜像 …/PLTR_FQ3_2025.txt(同上仓库)| 2025-11-03 | FACT;镜像全文 |
| S12 | Palantir Q2 2025 业绩稿 + 演示 | https://www.sec.gov/Archives/edgar/data/1321655/000132165525000105/a2025q2ex991pressrelease.htm ;镜像 …/PLTR_FQ2_2025.txt | 2025-08-04 | FACT;镜像全文 |
| S13 | Palantir Q1 2025 业绩稿 + 演示 | https://www.sec.gov/Archives/edgar/data/1321655/000132165525000063/a2025q1ex991pressrelease.htm ;镜像 …/PLTR_FQ1_2025.txt | 2025-05-05 | FACT;镜像全文 |
| S14 | Palantir Q1 2025 Investor Presentation(图表 OCR)| https://investors.palantir.com/files/Palantir%20-%20Q1%202025%20Investor%20Presentation.pdf ;镜像 https://github.com/EpsiRho/Team-Shield/blob/main/Docs/FileText/Paddle/palantir.json | 2025-05-05 | FACT(OCR 读数,已按环比勾稽)|
| S15 | Palantir 10-Q(截至 2023-03-31)| https://www.sec.gov/Archives/edgar/data/1321655/000132165523000044/pltr-20230331.htm | 2023-05 | FACT;检索摘要 |
| S16 | Palantir 10-Q(2023-06-30;2023-09-30)| https://www.sec.gov/Archives/edgar/data/1321655/000132165523000090/pltr-20230630.htm ;https://www.sec.gov/Archives/edgar/data/1321655/000132165523000118/pltr-20230930.htm | 2023-08 / 2023-11 | FACT;检索摘要 |
| S17 | Palantir 10-Q(2025-03-31;2025-06-30;2025-09-30)| https://www.sec.gov/Archives/edgar/data/1321655/000132165525000066/pltr-20250331.htm ;https://www.sec.gov/Archives/edgar/data/1321655/000132165525000106/pltr-20250630.htm ;https://www.sec.gov/Archives/edgar/data/1321655/000132165525000131/pltr-20250930.htm | 2025 | FACT;检索摘要 |
| S18 | Palantir 10-K FY2024(Item 1 文本)| https://www.sec.gov/Archives/edgar/data/1321655/000132165525000022/pltr-20241231.htm ;镜像 https://github.com/hakangulmez/THESIS_REPO/blob/main/text_data/10k_extracts_pre_agentic_2025q2/PLTR/item1/PLTR_2025-02-18.txt | 2025-02-18 | FACT;镜像 |
| S19 | Palantir 10-K FY2021(Item 1 / Item 7 文本)| 镜像 https://github.com/hakangulmez/THESIS_REPO/tree/main/text_data/10k_extracts/PLTR ;EDGAR 目录 https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001321655&type=10-K | 2022-02-24 | FACT;镜像 |
| S20 | Palantir FY2020 年报文本(前 20 大客户 2019/2020)| 镜像 https://github.com/jecxk/AI_document_processing/blob/main/ba-documind/data/raw/ba_public_derived/finance/ba-pub-01953_public_company_annual_report_review.txt | 2021 | FACT;镜像 |
| S21 | Palantir 10-K FY2025 | https://www.sec.gov/Archives/edgar/data/1321655/000132165526000011/pltr-20251231.htm | 2026-02-17 | FACT;本次未能读取,只经 S41/S42 转引 |
| S22 | Palantir Q4 2022 业绩电话会逐字稿 | 镜像 https://github.com/Ngafney/garda-spring26/blob/main/amir/transcripts/palantir-technologies/2022/Q4/PLTR_2023-02-14_Q4.txt | 2023-02-13 | FACT·会 |
| S23 | Palantir Q1 2023 业绩电话会 | https://www.fool.com/earnings/call-transcripts/2023/05/09/palantir-technologies-pltr-q1-2023-earnings-call-t/ ;镜像 …/2023/Q1/PLTR_2023-05-09_Q1.txt(同 S22 仓库,节选)| 2023-05-08 | FACT·会 |
| S24 | Palantir Q2 2023 业绩电话会 | https://www.fool.com/earnings/call-transcripts/2023/08/07/palantir-technologies-pltr-q2-2023-earnings-call-t/ ;镜像 …/2023/Q2/PLTR_2023-08-08_Q2.txt | 2023-08-07 | FACT·会 |
| S25 | Palantir Q3 2023 业绩电话会 | https://www.fool.com/earnings/call-transcripts/2023/11/02/palantir-technologies-pltr-q3-2023-earnings-call-t/ ;镜像 …/2023/Q3/PLTR_2023-11-02_Q3.txt | 2023-11-02 | FACT·会 |
| S26 | Palantir Q4 2023 业绩电话会 | https://www.fool.com/earnings/call-transcripts/2024/02/05/palantir-technologies-pltr-q4-2023-earnings-call-t/ ;镜像 https://github.com/ItachiUchiha729/NLP_Earning_Call_Analysis/blob/main/ECT/PLTR_Q4-2023.txt | 2024-02-05 | FACT·会 |
| S27 | Palantir Q1 2024 业绩电话会 | https://www.nasdaq.com/articles/palantir-technologies-pltr-q1-2024-earnings-call-transcript ;镜像 …/ECT/PLTR_Q1-2024.txt | 2024-05-06 | FACT·会 |
| S28 | Palantir Q2 2024 业绩电话会 | https://www.fool.com/earnings/call-transcripts/2024/08/05/palantir-technologies-pltr-q2-2024-earnings-call-t/ ;镜像 …/ECT/PLTR_Q2-2024.txt | 2024-08-05 | FACT·会 |
| S29 | Palantir Q3 2024 业绩电话会 | https://www.fool.com/earnings/call-transcripts/2024/11/04/palantir-technologies-pltr-q3-2024-earnings-call-t/ ;镜像 …/ECT/PLTR_Q3-2024.txt | 2024-11-04 | FACT·会 |
| S30 | Palantir Q4 2024 业绩电话会 | 镜像 …/ECT/PLTR_Q4-2024.txt(ItachiUchiha729 仓库)| 2025-02-03 | FACT·会 |
| S31 | Palantir Q1 2025 业绩电话会 | 镜像 …/ECT/PLTR_Q1-2025.txt | 2025-05-05 | FACT·会 |
| S32 | Palantir Q2 2025 业绩电话会 | 镜像 …/ECT/PLTR_Q2-2025.txt | 2025-08-04 | FACT·会 |
| S33 | Palantir Q3 2025 业绩电话会 | https://www.fool.com/earnings/call-transcripts/2025/11/04/palantir-pltr-q3-2025-earnings-call-transcript/ ;镜像 …/ECT/PLTR_Q3-2025.txt | 2025-11-03 | FACT·会 |
| S34 | Palantir Q4 2025 业绩电话会 | 镜像 …/ECT/PLTR_Q4-2025.txt;另见 https://github.com/Ngafney/garda-spring26/blob/main/amir/transcripts/palantir/2025/Q4/PLTR_2026-02-02_Q4.txt | 2026-02-02 | FACT·会 |
| S35 | Palantir Q2 2024 业绩稿(8-K,结构化解析)| https://www.sec.gov/Archives/edgar/data/1321655/000132165524000133/ ;镜像 https://github.com/VPAeternus/Aeternus/blob/main/tradingagents/research/fundamental/Growth/earnings_8k_sec_parser/local_extractions_2024Q3_secparser/PLTR/PLTR_2024-08-05_000132165524000133.json | 2024-08-05 | FACT;镜像 |
| S36 | Newsoid news-ai 汇编(Q4 2024 业绩日新闻,129 笔 ≥100 万)| https://github.com/Newsoid/news-ai/blob/main/2025-02/2025-02-03.json | 2025-02-03 | REPORT |
| S37 | Palantir Q4 2023 业绩稿(8-K Ex.99.1)| https://www.sec.gov/Archives/edgar/data/1321655/000132165524000010/a2023q4ex991earningsrelease.htm | 2024-02-05 | FACT;检索摘要 |
| S38 | 美国陆军:U.S. Army awards Enterprise Service Agreement to enhance military readiness and drive operational efficiency | https://www.army.mil/article/287506/u_s_army_awards_enterprise_service_agreement_to_enhance_military_readiness_and_drive_operational_efficiency | 2025-08-01 | FACT(政府公告);URL 经 S41 转引,本次未打开 |
| S39 | 美国国防部合同公告(Maven,2024-05-29)| https://www.defense.gov/News/Contracts/Contract/Article/3790490/ | 2024-05-29 | FACT(政府公告);URL 经 S41 转引,未打开 |
| S40 | 美国国防部合同公告(Maven 修改 P00005)| https://www.defense.gov/News/Contracts/Contract/Article/4194643/ | 2025-05-20 | FACT(政府公告);URL 经 S41 转引,未打开 |
| S41 | StarIntel:Palantir Technologies: Contracts, Lobbying and Influence Network(含合同表和原始出处清单)| https://github.com/lost-rob0t/starintel-gpt-auto-dig/blob/main/reports/palantir-deep-dive-2026-07-25.md ;https://github.com/lost-rob0t/starintel-gpt-auto-dig/blob/main/roam/research/palantir/PALANTIR-RESEARCH-010-contracts.org | 2026-07-25 | REPORT |
| S42 | Ithildin dossier:palantir-technologies(USAspending 衍生条目,多数自标「unverified」)| https://github.com/tcole333/ithildin/blob/main/content/dossiers/palantir-technologies.json | 2026-03(最新条目)| REPORT |
| S43 | detention-pipeline:Palantir ImmigrationOS 与 ICE 合同笔记(引 Axios 2025-05-01、USAspending 70CTD022FR0000170)| https://github.com/markramm/detention-pipeline/blob/main/kb/industry/contracts/palantir-immigrationos-2025.md ;https://github.com/markramm/detention-pipeline/blob/main/kb/industry/contractors/palantir-technologies.md ;原报道 https://www.axios.com/local/denver/2025/05/01/palantir-deportations-ice-immigration-trump | 2025–2026 | REPORT |
| S44 | GovConWire:Palantir, Anduril Win $192M in Army TITAN Production Orders(经 InvestmentVault 转录)| https://www.govconwire.com/articles/palantir-anduril-army-titan-192m-production-orders ;转录 https://github.com/jameswong2011/InvestmentVault/blob/main/Research/2026-09-03%20-%20PLTR%20-%20Army%20TITAN%20192m%20Production%20Orders%20-%20news.md | 2026-09-02 | REPORT |
| S45 | Motley Fool:Palantir's Maven is now an official Pentagon program of record(经 InvestmentVault 转录)| https://www.fool.com/investing/2026/08/25/palantirs-maven-is-now-an-official-pentagon-progra/ | 2026-08-25 | REPORT |
| S46 | Defense One:Pentagon memo directs Palantir spend(经 InvestmentVault 转录)| https://www.defenseone.com/business/2026/08/pentagon-palantir-no-bid/415400/ | 2026-08-13 | REPORT |
| S47 | 24/7 Wall St.:A Judge Just Called This Pentagon AI Ban Illegal: Why Palantir Could Rally(经 InvestmentVault 转录)| https://247wallst.com/investing/2026/08/29/a-judge-just-called-this-pentagon-ai-ban-illegal-why-palantir-could-rally/ | 2026-08-29 | REPORT |
| S48 | NHS England:Federated Data Platform — contract explainer | https://www.england.nhs.uk/digitaltechnology/nhs-federated-data-platform/security-privacy/contract-explainer/ | 2023– | FACT(政府页面);URL 经 S41 转引,未打开 |
| S49 | 英国 Find a Tender:MOD–Palantir 企业协议记录 | https://www.find-tender.service.gov.uk/procurement/ocds-h6vhtk-05f7e9 | 2025-12-30 | FACT(政府公告);URL 经 S41 转引,未打开 |
| S50 | epiplexity-investment:PLTR Catalyst Map | https://github.com/realitydeslab/epiplexity-investment/blob/main/reports/PLTR/catalyst-map.md | 2026-03-06 | REPORT |
| S54 | InvestmentVault:Theses/PLTR - Palantir(英国 MOD 单一来源、NHS 2027-02 解约条款等)| https://github.com/jameswong2011/InvestmentVault/blob/main/Theses/PLTR%20-%20Palantir.md | 2026-09 | REPORT |
| S55 | Yahoo Finance:Palantir Technologies Q1 Earnings Call Highlights | https://finance.yahoo.com/markets/stocks/articles/palantir-technologies-q1-earnings-call-231307733.html | 2026-05 | REPORT;检索摘要 |

(S51–S53 编号未使用。)
