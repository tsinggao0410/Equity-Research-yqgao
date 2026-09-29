# Palantir(PLTR.US)业务认知 · 基金经理版 · 材料清单(materials.md)

> 2026-09-29。本卡在云端环境制作,网络策略拒绝访问 sec.gov、investors.palantir.com、palantir.com、usaspending.gov、行情站与研报站,**一手文件无法直接下载**。取数方式与局限如下,正式交付前应在可访问 SEC 的环境里逐项回原文核对页码。

## 1 取数方式

| 类 | 来源 | 方式 | 局限 |
|---|---|---|---|
| 财务、分部、客户与合同指标 | 10-K FY2020–FY2025、10-Q 1Q23–2Q26、季度业绩稿与股东信 | WebSearch 检索结果(多为 SEC 与公司业绩稿的转述)交叉核对;用户已有一页纸(底层为 SEC XBRL 与 FMP)作线索 | 无法取得 PDF 页码,来源写文件与章节或发布日期 |
| 政府合同 | 美国陆军、国防部合同公告,NHS England、北约公告 | WebSearch | USAspending 年度拨付取不到原始数据 |
| 行业与竞品 | 国防预算文件、北约年报、Gartner / IDC 新闻稿、竞品年报与业绩稿 | WebSearch | 机构报告全文取不到,只用公开新闻稿数值 |
| 治理 | DEF 14A、Form 4(媒体汇总) | WebSearch | Form 4 逐笔明细取不到 |
| 图片 | 官网、招股书、研报原图 | 均无法访问 | 产品与架构图一律自绘结构示意,标「示意」 |

## 2 分项数据文件

- `work/data/A1_financials.md`:年度与季度财务、分部、股本、指引
- `work/data/A2_customers_contracts.md`:客户数、TCV、NDR、RPO、重大合同、企业案例
- `work/data/A3_industry_peers.md`:国防预算、北约、IT 与 AI 市场、竞品财务、云厂商智能体
- `work/data/A4_governance_history_products.md`:时间轴、三类股、减持、SBC、产品与交付、争议、员工
- 用户已有一页纸(只读):`onepagers/B-AI算力与软件/37-PalantirTechnologies-PLTR-v3.5-260821.html`,内嵌数据只作线索,结论与估值不用

## 3 章节依据

按 10-K 的客户类型(政府 / 商业)× 地域(美国 / 国际)披露定章:美国政府、美国商业、国际业务(国际政府与国际商业合并:两者合计 2025 年收入 11.56 亿美元,国际商业不单独披露客户数,拆开写证据不足)。大客户与合同单列一章(政府收入集中、合同上限与已拨付需要逐条区分)。
