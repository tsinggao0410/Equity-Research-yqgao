# 05 国际业务 · 口径冲突与数据缺口

## ① 口径冲突

| 项目 | 来源 A | 来源 B | 本章取舍 | 理由 |
|---|---|---|---|---|
| 2Q26 国际商业同比 | 公司称 +26%(Q2 2026 业绩稿) | 作者计算 +24.8%(1.81 ÷ 1.45 − 1) | lead 用公司口径 +26%;图 5-8 用计算值并在图注并列公司口径 | 美国商业只披露到百万美元,国际商业 2Q26 区间 1.809–1.819(A1 ⑤-8),计算值有取整误差 |
| 2Q26 国际政府同比 | 公司称 +42% | 作者计算 +42.5% | 同上 | 同上 |
| 1Q25 国际商业同比 | 媒体转述「−5%,首次同比下降」(TechMarketView 2025-05-06) | 作者计算 −4.7%(1.42 ÷ 1.49 − 1) | 正文用 −4.7% | 与底座季度值一致;两者只差取整 |
| 北约欧洲成员国与加拿大国防开支 | 现价:2024 >4,850 亿、2025 约 6,080 亿、2026E 6,340 亿美元 | 2021 不变价:2025 年 5,710 亿(2025-08 报告)/ 5,740 亿(2026-03 年报修订) | 图 5-1 只用现价三点,不变价写进图注(取修订后的 5,740 亿) | 一条横轴只放一种价格口径;2024 为「超过」的下限 |
| NHS 联邦数据平台进度 | 2024-11:87 家急症信托 + 28 个 ICB 签约(公开报道汇总) | 2025-09:150 家接入、77 家上线并报告成效(Digital Health 引 NHSE);2026-01:110 家上线或在交付(议会书面答复,检索摘要);2026-05 末:167 家签署加入备忘录、139 家上线、137 家报告成效(NHSE uptake 页面) | 图 5-13 用 2024-11 / 2025-09 / 2026-05 三期;2026-01 的「上线或在交付」口径不同,不入图 | 各期「签约 / 接入 / 上线」定义不同,图注说明;2024-11 只计急症信托 |
| 德国联邦国防军表态 | heise(2025)、harici 转述 | cio.de、cybernews(提到 2026 年夏测试本土厂商) | 正文不写年份 | 原文日期未取得 |

## ② 数据缺口

| 缺什么 | 查过哪些文件与检索 |
|---|---|
| 国际政府、国际商业的客户数与 TCV 分项(除 4Q25 国际商业 TCV 13 亿外) | A2 表 A-1、A-2;Q1–Q4 2025 业绩稿全文(`sources/text/PLTR_FQ*_2025_release.txt`,grep international):公司不单独披露 |
| 英国以外国家的收入(日本、德国、法国等) | A1 表 A1-1;10-K 只披露美国、英国、其他:数据不可得 |
| 英国季度收入 | 10-Q 地区收入本次未取得:数据不可得 |
| 北约欧洲成员国与加拿大 2014–2023 逐年国防开支(同一价格口径) | A3 ⑦-7;本章检索「NATO Europe and Canada defence expenditure 2014 … current prices」只得到 2015 不变价的第三方图表,且 2023 值明显异常(704),未采用:数据不可得 |
| 2015–2021 年达到 2% 的国家数 | A3 2b 只有 2014、2022–2025:数据不可得 |
| 北约 MSS NATO 合同金额 | A2 表 B-3、A5 §4(NCIA 公告称金额未披露):数据不可得 |
| 英国国防部企业协议所含产品 | 英国 Find a Tender 记录经 A2 转引,未打开:数据不可得 |
| NHS 联邦数据平台已计费金额 / 已确认收入 | NHSE 合同说明页(A2 S48)未打开;公司不单独披露:数据不可得 |
| 欧洲本土对手(ChapsVision 以外)与系统集成商的收入、份额,SAP 的相关产品收入 | 未检索到可比口径;表 5-1 只比做法,不编数 |
| 瑞士军方内部报告的日期与原文 | 本章检索只得到 TechRepublic、techdirt 转述:日期未取得 |
| 汇率对国际收入的量化影响、外币收入占比 | 10-K Item 7A 检索摘要只称合同以美元为主、未套期、汇兑损益不重大:数据不可得 |
| 国际业务员工数 | 只有「2025 年末员工 28% 在美国以外」(A5 §1,Revelio Labs 引 10-K,REPORT),正文未用 |
| Skywise 连接的航司数 | 检索结果有「70 余家」「80 余家」两说,年份不明,未用;SVG 未写用户数 |

## ③ 底座勘误

无。本章所用底座数字与 A1–A5 原值一致。

## 本章检索来源(WebSearch,共 13 次;一手页面未能打开,均为检索摘要)

| 编号 | 标题 | URL | 日期 |
|---|---|---|---|
| W1 | NHS England:NHS Federated Data Platform uptake and benefits | https://www.england.nhs.uk/digitaltechnology/nhs-federated-data-platform/impact/fdp-uptake-and-benefits/ | 2026-06-12 更新 |
| W2 | Medact:FDP Roll-out Report;UK Parliament 书面答复(2026-02-11) | https://www.medact.org/2026/resources/fdp-palantir-roll-out-report/ ;https://lordsbusiness.parliament.uk/ItemOfBusiness?itemOfBusinessId=166875&sectionId=50&businessPaperDate=2026-02-11 | 2026 |
| W3 | Digital Health:Palantir awarded £23m deal to continue work on NHS Covid-19 Data Store | https://digitalhealth.net/2020/12/palantir-awarded-23m-deal-to-continue-work-on-nhs-covid-19-data-store | 2020-12 |
| W4 | TechMarketView:European headwinds temper Palantir's impressive Q1 | https://www.techmarketview.com/ukhotviews/archive/2025/05/06/european-headwinds-temper-palantirs-impressive-q1 | 2025-05-06 |
| W5 | heise:Palantir under pressure – European alternatives come into focus;netzpolitik.org(2024) | https://heise.de/-10646928 ;https://netzpolitik.org/2024/automatisierte-datenanalyse-bei-der-polizei-bundeslaender-nicht-scharf-auf-palantir/ | 2024–2025 |
| W6 | cio.de:Veto gegen Palantir – Bundeswehr verbannt US-Software aus KI-Cloud;cybernews | https://www.cio.de/article/4164117/veto-gegen-palantir-bundeswehr-verbannt-us-software-aus-ki-cloud.html | 日期未取得 |
| W7 | TechRepublic:UK Urged to Review Palantir Contracts(瑞士军方报告) | https://www.techrepublic.com/article/news-uk-government-palantir-contracts/ | 日期未取得 |
| W8 | Sifted:ChapsVision to replace Palantir in major contract with French intelligence agency | https://sifted.eu/articles/chapsvision-to-replace-palantir-in-major-contract-with-french-intelligence-agency | 2026-06 |
| W9 | Palantir 10-K FY2024 Item 7A(检索摘要) | https://www.sec.gov/Archives/edgar/data/1321655/000132165525000022/pltr-20241231.htm | 2025-02 |
| W10 | AeroMorning:Palantir and Airbus extend strategic collaboration | https://aeromorning.com/en/palantir-and-airbus-extend-strategic-collaboration/ | 2026-02 |
| W11 | Digital Health:Good Law Project sues NHSE over heavily redacted Palantir FDP contract;The Register(2024-03-25);UKAuthority | https://www.digitalhealth.net/2024/02/good-law-project-sues-nhse-over-heavily-redacted-palantir-fdp-contract/ ;https://www.theregister.com/2024/03/25/nhs_palantir_contract_republished/ | 2024-02 / 2024-03 |
