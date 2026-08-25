# equity-onepager-interactive · 2026-08-16/17 修订（开篇章从源头重写 + 石英股份八条反馈泛化）

## 一、开篇章「一段话说清楚」从源头重写（references/10）

**病灶**：8/8 v2.1 之后 10 号文档没有再被重写过，只被打了五处补丁（§2a / §5.3a / §5.8 / §5.9 硬塞在 §5 编号列表中间、§5.3b 追加在 §7 之后），
同一段事故叙事在 10 / SKILL.md CK-7 / check_summary.js 头注三处重复；`k` 列的提问框架散在四处、从没有一张登记表。

**改法（不打补丁，重写）**：
- `references/10-summary-backsolve.md` 重排为 §0 定位 → §1 契约 → **§2 钩子体系** → §3 链条 → §4 算账 → §5 第四点 → §6 纪律 → §7 CK-7 → §8 坑 → 附录 A 变更史（事故每条一行）。
- **§2 钩子登记表**（`scripts/summary_hooks.json` 机器版）：生意本身 7 必答 + 6 选答 / 盘子 3 必答 + 2 条件必答（A股 派系类型与公司诉求、有 1.7 时 可交易容量）+ 含义 + 1 选答 / 股性 5 必答 + 1 条件必答（主因子 ≥2/3 同一时 历史行情由什么驱动）+ 3 选答；每条＝该问的 / 去哪挖 / 合格形状 / 不合格样例。
- 契约新增 `points[].hook`（登记表 id）、`main_scenario`、`accounting.price_assumes`（现价把什么当成既成事实）、`type_card`（见二 A）。
- **密度纪律「少而狠」**：每条 v 一件事，FACT ≤100 字 / EST·DNA ≤150 字（闸门 +10% 容差），选答每块 ≤2，三块合计目标 3,000、硬上限 4,000。
- `scripts/check_summary.js` 重写：按登记表查必答覆盖（hook id 优先 / k 关键词回退，旧模型不用改）+ title 结论句 + b6/b7 判定句 + b9 密度 + c5 最先断的一环 + d1 差额行 + d2 price_assumes + g main_scenario + h1 反算/脚手架扫描 + t1/t2 类型卡；`--hooks` 打印登记表，`--json` 供评测。
- SKILL.md Phase 6.5 / CK-7 压成路由 + 硬指标，事故叙事退出 SKILL.md。
- 隔离测（赛力斯 / 阳光，旧版 vs 新版 10 各写一次开篇）：新版 12/12 断言，旧版 8/12；少而狠后公司类型 23 条 / ~2,850 字（此前 24 条 / ~4,400 字）。

## 二、石英股份 603688 v3.2 八条读者反馈 → 泛化为 skill 级规则

| # | 反馈 | 病根（泛化） | 落到 |
|---|---|---|---|
| 1 | 概览要加公司类型（真β/假β/σ/叙事-题材）+ 类型对应的核心参数（β：叙事线+龙头中军后排+K 线方位；σ：预期利润率/ROE/PE/PS/PB 分位） | 数据 1.7/1.3/1.4/1.5/2.1b 早算完了，散在四章里，没在读者第一眼合成一张卡（又一次「烂在图里」） | **`scripts/type_card.py`** 合成 `summary.type_card` 数字层；`renderTypeCard()` 渲在概览快照下；作者定 `type/verdict`，与股性 beta_kind 同一个词；10 §2.8、02 §0、CK-7 t1/t2 |
| 2 | 三坐标图太大，换一种可视化 | 全景图 viewBox 900×620 铺满整栏比一屏还高；赔率没算出来时全是最小圆 | 4.1.1 默认视图＝**三坐标条 `cmapStrip`**（一行一条矛盾，F/D/赔率三根同尺度条），气泡 SVG 进折叠块且宽度封顶 760px；子坐标系同款；06 §3.0e ① |
| 3 | 「历史对照」不是和自己历史对照，是和别的公司/叙事对照 | scenCard 只画本股历史最强段的 R/M/V 同尺度条并叫它「历史对照」 | 改名「本股历史最强段（同尺度）」；每条 Case 新增 **`analog{case,period,what,diff,src}`**（跨公司/跨叙事，diff 必填）；09 §5.5h、CK-6 **S9** |
| 4 | 赔率都没算出来 | `items[].odds` 十条全 null，`odds_basis` 写得像算过；闸门只查 odds_basis 不查 odds | check_part4 新增「odds 是数字」闸；覆盖表/明细表 `null` 渲红字「未算」不渲 0%；09 §8/§9c |
| 5 | 权重彼此要有影响，加权的权重＝1 | 引擎一直归一（`wnorm`），卡片印的是滑块原始值且拖一根其余不动 | 卡片印**有效权重**（Σ=100%）+ 括号原始值，light 刷新遍历全部卡片；hero 区加「权重已归一」；05 §9、06 §3.0e ④、CK-4 |
| 6/7 | 3.1 表头字体看不见 | 全局 `thead th` 白字+accent 底，被 `.col-hist/.col-fcst/.rowlbl` 浅底覆盖，白字留着 | `#tbl-pl thead th{color:var(--fg)}` 一组规则；通则「覆盖表头底色必须同时指定前景色」06 §3.0e ② |
| 8 | 2.1b 做成可展开可收起 | 次级复合图没有折叠 | `#fwdpe-block` 改 `<details open>`（按钮移出 summary），`bindFwdFold()` toggle→resize 兜底；通则「次级复合图一律可折叠」06 §3.0e ③ |

通则汇总写在 **06 §3.0e**（一屏 / 对比度 / 可折叠 / 派生量显示口径与算法一致 / 空值不渲 0），SKILL.md CK-8 通则段引用。

## 三、文件清单

新增：`scripts/summary_hooks.json`、`scripts/type_card.py`、`CHANGELOG-20260817.md`
重写：`references/10-summary-backsolve.md`、`scripts/check_summary.js`
修改：`SKILL.md`（目录树 / Phase 6.5 / CK-4 / CK-6 / CK-7 / CK-8 通则）、`templates/app.js`（renderTypeCard / cmapStrip / analog / wLabel / bindFwdFold / 未算渲染 / price_assumes / summaryText）、`templates/onepager_template.html`（类型卡 DOM+CSS / 三坐标条 CSS / 表头对比度 / 2.1b details / analog CSS）、`scripts/check_part4.js`（S9 + odds 数字闸）、`references/02/05/06/09`

## 四、验收

- 语法：app.js / check_summary.js / check_part4.js / check_charts.js `node --check` 全过；type_card.py / build_page.py `py_compile` 全过。
- 真实模型回归：石英 603688（写入类型卡后 build + Playwright 渲染：类型卡可见、三坐标条 11 行 261px、气泡折叠、3.1 表头深色字、2.1b 为 details、权重 5/8/10/28/22/14/13 Σ=100、覆盖表「未算」红字、无 JS 报错）；赛力斯 601127（σ 型类型卡渲染、check_summary 43/43、check_charts 17/17）。
- 旧报告跑新闸会挂在新增项上（type_card / analog / odds 数字 / 密度）——那是闸在正确地报旧契约。
