# 章节 agent 共用须知(Palantir 基金经理版完整卡)

R = /home/user/Equity-Research-yqgao/primers/Palantir-PLTR/primer_pm ;S = /home/user/Equity-Research-yqgao/skills/tech-species-primer-pm

## 先读(按顺序)
1. `R/work/BRIEF.md` 全文(§1 环境限制、§2 写法、§2b 基金经理版写法、§3 版式、§3b 章节分工、§4 自测、§5 数字台账、§5b 术语台账、§6 缺口、§7 返回格式)。
2. `R/work/facts_spine.md` 全文(统一数字底座,**全卡同一个数只用这里的值**);细节查 `R/work/data/A1_financials.md`、`A2_customers_contracts.md`、`A3_industry_peers.md`、`A4_governance_history_products.md`、`A5_supplement.md`;2025 年四季业绩稿全文在 `R/sources/text/PLTR_FQ*_2025_release.txt`(单行长文本,用 grep -o 取片段)。
3. `S/references/DESIGN_pm.md` §4;`S/references/plain_language_guide.md` §2、§5、§6、§7。
4. 语法:`S/assets/fixture/fixture.md`;chart JSON 字段见 `S/scripts/render_report_v32.py` 文件头 docstring。
5. 写法样例(同一家公司):`S/examples/pm/pltr_plain_sample.md`(零章与技术章;句子不要照抄,数字以底座为准)。
6. v3.2 完整样例:`S/examples/sungrow/card_v32.md`(约 22 万字节,只 grep 或分段读;学章首 lead、表题、图题、来源行、六节写法、篇幅)。
7. 语言规范:`/root/.claude/skills/synced/d9b7e5bf-9d6c-4599-8bd0-d0305cc7c2bc_e1529c38-6160-4d4f-a126-a8aee1101b8c/buyside-voice/references/voice-rules.md`(破折号全章 ≤2、判断性警句只放结论位、禁词、FACT / 估算 / 判断三档语气)。

## 纪律
- 数字只从底座和 data 文件取;每个数登记进 `R/parts/NN_facts.md`(| 数字 | 含义 | 来源文件 | 章节或日期 | 原文摘录 |)。底座没有的数可以 WebSearch 补(先 ToolSearch 加载 `select:WebSearch`;额度有限,本章最多约 15 次,先用已有数据),搜不到写「数据不可得」,记进 `NN_gaps.md`。**不编数、不估算冒充实际。**
- 来源行写文件与章节或发布日期,例:「来源:Palantir 10-K FY2025 分部附注;Q2 2026 业绩稿(2026-08-03)」。**不编 PDF 页码。**第三方整理的数标〔公开报道〕。
- 不写估值、目标价、评级、PE/PS、市值、卖方盈利预测;用户一页纸里的结论与估值一律不用。
- 页面不写「白话」「一句话:」「打个比方:」等标签;不写口语化问句(见 plain_language_guide §6);判断先行、证据平叙;每段加粗 1–3 处。
- 数字写精确值并注明期间与口径(GAAP / 调整后);合同上限 ≠ 已拨付 ≠ 收入。
- 图片:只能自绘 SVG(风格见 BRIEF §1:白底,深蓝 #1f3a5f 主结构、灰 #9aa1ab 边框、只一处砖红 #a4532e;直角;字号 ≥11px;宽 720–960;不虚构界面文字与数据),存 `R/images/cN_*.svg`,MD 里 `![示意图:图 N-M 标题](images/cN_xxx.svg "来源:作者依据 XX 公开材料绘制;结构示意")`。画完截图用 Read 看一眼:
  ```
  python3 - <<'PY'
  import asyncio
  from playwright.async_api import async_playwright
  async def m():
      async with async_playwright() as p:
          b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
          pg=await b.new_page(viewport={'width':960,'height':520}); await pg.goto('file:///ABS/PATH.svg'); await pg.screenshot(path='/ABS/PATH.png'); await b.close()
  asyncio.run(m())
  PY
  ```
- 图号:章号 N 为阿拉伯数字(一 = 1 … 十一 = 11),图 N-1、表 N-1 起;chart `id` 以 `cN_` 开头,全卡唯一;每张 chart 有 `source`。
- 图表归属(避免跨章重复出图,别章的图写「见图 N-M」):
  - 一章:四分部年度收入结构、季度总收入与同比、美国与国际对比、年度收入与 GAAP 净利润、商业模式结构图、发展时间轴、客户类型。
  - 三章:美国政府季度 / 年度收入、国防拨款与国防部 IT / AI 预算、美国政府收入与国防拨款之比。
  - 四章:美国商业季度收入、美国商业客户数与户均收入、美国商业 TCV 与 RDV、软件与 AI 市场规模、竞品增速对比、企业案例。
  - 五章:国际政府 / 国际商业季度与年度收入、英国与其他地区收入、北约与欧洲国防开支、达到 2% 的国家数、NHS 联邦数据平台接入进度。
  - 六章:客户总数、总 TCV、NDR、RPO 与 RDV、大额交易笔数、前 20 大客户平均收入、重大合同上限与已拨付、联邦合同年度拨付。
  - 七章:三类股控制结构、创始人与高管减持、SBC 占收入比与稀释股数、指数纳入时间轴。
  - 九章:毛利率与分部贡献利润率、季度费用率、调整后营业利润率与 Rule of 40、六张经营效率图、人均收入。
  - 十章:持续决议与政府停摆、大模型价格下降、企业 AI 采用调查、云成本、汇率与利率(利息收入)。
- 不改别的章文件、不改用户已有文件(onepagers/ 只读)、不在任何请求里放用户邮箱。
- 写完按 BRIEF §4 自测渲染,错误为 0;删掉 `R/_t_NN.md`。
- 返回 ≤300 字(BRIEF §7)。
