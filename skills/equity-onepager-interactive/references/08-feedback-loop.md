# 08 · 反馈闭环 / 认知螺旋（Phase 8-9 ⚡强制）

> 用户口径（2026-07-25 固化）：**认知是螺旋上升的，一份静态报告搞不完**。所以一页纸不是「交付即结束」，而是
> **上线 → 读者在页面上标注疑问 → 统一回收 → 我逐条改稿/答复/标待补 → 出 v_n+1（页顶带「本版反馈回应」）**
> 的循环。本文件是这条循环的协议 + 命令 + 纪律。进入 Phase 8（上线）与 Phase 9（回灌）前必读。

---

## 1 · 三种运行形态（按用户是否要公网协作选）

| 形态 | 怎么跑 | 标注怎么回来 | 适用 |
|---|---|---|---|
| **A 纯本地**（零基建，默认） | `build_page.py` 出 HTML，本地打开（**放项目目录内**，见 06 §5.2） | 读者点「复制反馈摘要」粘进对话 / 「导出 JSON」发我 → `feedback_pull.py --from-file` | 自己看、单人迭代 |
| **B 云端平台**（推荐，一次性 3 分钟建） | `deploy_page.py --ticker … --endpoint …` → Cloudflare Worker 托管 | 读者点「同步到云端」→ 我 `feedback_pull.py` 直接拉 | 多人/多设备/手机上翻；跨轮台账 |
| **C Artifact 只读** | `build_page.py --mode artifact` 发 Artifact | ❌ 不收标注（Artifact 无后端）——只作展示 | 单纯分享一眼看 |

**A 与 B 同一套代码**：标注层（`templates/annot.js`）总是内联进页面；有 `feedback.endpoint` 就多一条「同步到云端」的路，没有就只走导出/复制。`build_page.py --no-annot` 可出纯只读版（对外交付时用）。

---

## 2 · 一次性部署（形态 B，只做一次）

```
cd C:/Users/youqi/.claude/skills/equity-onepager-interactive/feedback/worker
wrangler login                                  # 浏览器授权一次
wrangler kv namespace create ANNOT              # 复制返回的 id
# → 把 id 填进 wrangler.toml 的 [[kv_namespaces]].id
wrangler secret put FB_ADMIN_TOKEN              # 随手编一串长口令(只有我拉标注要用)
wrangler deploy
curl https://onepager-feedback.<子域>.workers.dev/api/health     # {"ok":true,"kv":true,"admin_token_set":true}
```
拿到 base URL 后写进 `scripts/feedback_config.json`（`deploy_page.py --endpoint` 会自动写），token 建议放环境变量 `FB_ADMIN_TOKEN` 不落盘。

**安全边界**：页面里**不含 token**——读者只能 `POST /api/ann`（写），`GET` 拉全量必须带 token。所以读者互相看不到对方草稿式标注；「答复」通过我重出 v_n+1 的 `feedback.resolved` 广播给所有人。

---

## 3 · 每轮循环的 4 条命令（Phase 8 → 9）

```
# ① 上线（Phase 8）——endpoint 烧进页面，读者才能一键同步
python scripts/deploy_page.py --ticker 688629 --model _workspace/688629/page_model.json \
    --endpoint https://onepager-feedback.<子域>.workers.dev

# ② 回收（Phase 9 起手）——云端拉 / 或读本地导出
python scripts/feedback_pull.py --ticker 688629 --only-new
python scripts/feedback_pull.py --ticker 688629 --from-file "<页面导出的 feedback_*.json>"
#   → _workspace/688629/feedback/round_<n>.md            按模块分组的 triage + 改稿清单
#   → _workspace/688629/feedback/round_<n>_resolutions.json   回应骨架(我填 answer/action)
#   → _workspace/688629/feedback/annotations.json        跨轮台账(status 流转)

# ③ 我按 round_<n>.md 逐条改 page_model.json，并把答复填进 resolutions → 写回 + 版本 +1
python scripts/feedback_resolve.py --ticker 688629 --round 2 --bump v3 \
    --changelog "v3：口径对账补齐、份额下调至 28%、每卡用量挂公司口径原句"

# ④ 重出 + 重新上线（读者刷新即见页顶「本版反馈回应」+ 被改模块绿边）
python scripts/deploy_page.py --ticker 688629 --model _workspace/688629/page_model.json --version v3
```

`feedback_resolve.py` 有**空答复闸**：任何一条 `answer` 为空直接拒绝写回——**每条标注必须有归宿**。

---

## 4 · 标注五类型 → 修复动作（与 `feedback_pull.py` 内表一致，不许自由发挥）

| 类型 | 读者含义 | 我必须做的事 | 落到 page_model 哪里 |
|---|---|---|---|
| ❓ **没看懂** q | 逻辑/术语没跟上 | 把这段拆成 `driver_chain` 分步（每步 expr→val），或改写 `model.logic`；术语进 `references` | `segments[].model.driver_chain` / `.logic` |
| ⚠️ **数据存疑** d | 数字或口径不对 | 回一手源复核（RAG 原句 / iFind 原值）；**口径打架 → 建 `model.calibers` 对账表**；假设错 → 改 `assume` 并说明 | `.calibers` / `.assume` / `hist_actual` |
| 🔍 **要原文** s | 要看背后的纪要/研报 | `rag_query.py get_doc` 取逐字原句 → 落 `model.evidence`，正文挂 `[Ex]` 角标 | `segments[].model.evidence[]` |
| 💡 **建议补** i | 想加情景/对标/分部 | 采纳则改模型 + changelog 写清；不采纳**也要答**为什么不采纳 | 相应模块 / `changelog` |
| ✅ **认可** o | 关键段留痕 | 不改稿（不进改稿清单），但保留台账 | — |

**升级纪律**：同一 `path` 上重复出现 ≥2 条 d/q → 说明这块**结构性讲不清**，不是补句话能解决的：该段必须重做 driver_chain + calibers（不是在正文加解释）。

---

## 5 · `page_model.feedback` 契约

```jsonc
"feedback":{
  "report_id":"688629",          // localStorage / KV 的分区键；跨版本保持不变(标注才能跨轮累积)
  "endpoint":"https://onepager-feedback.xxx.workers.dev",   // 空=纯本地模式
  "autosync":true,               // 读者存标注后 ~1.5s 自动同步(仍可手点)
  "rag_ws":"688629",             // 证据卡里「取原文命令」用的 RAG 工作区名
  "resolved":[{"id","path","sec_title","on_ver","reader","ask","answer",
               "action":"fixed|answered"}],   // fixed=本版已改(模块打绿边) / answered=已答复
  "open":[{"id","path","sec_title","on_ver","ask","why_pending"}]   // 待补数据(诚实留白,页面标黄)
}
"meta":{ "version":"v3", "updated":"2026-07-25", "changelog":"本版一句话变更" }
```
`build_page.py` 会自动补 `report_id/rag_ws/autosync` 与 `meta.version`（缺省 v1），`--endpoint/--version` 可命令行覆盖。

---

## 6 · `data-fbk` 锚点：标注 → JSON 路径（这条链是闭环的命脉）

标注不是「贴在某段文字上」，而是**锚到 page_model 的字段路径**——我拿到 triage 就知道改哪一格，不用猜。

| 模块 | `data-fbk` 路径 | 来源 |
|---|---|---|
| 1.1 营收 / 1.2 股东·派系·股权 / 1.3 杜邦 / 1.4 费率 | `part1.revenue` `part1.shareholders(.factions_ts)` `part1.ownership` `part1.dupont` `part1.cost_structure` | 模板静态 |
| 2.1 K线 / 2.3 催化清单 | `part2.weekly` `part2.catalysts` | 模板静态 |
| 2.2 阶段列（每列一个） | `part2.phases[i]` | `renderPhasePanel` |
| 3.1 利润表 | `part3.hist_actual` | 模板静态 |
| 叙事↔分部映射（每 era） | `part3.narrative_map.eras[i]` | `renderNarrativeMap` |
| 分部模型面板 / 建模逻辑 / 驱动链 / 口径表 / 证据区 / 次级模型表 | `part3.segments[i]` `…[i].model.logic` `…driver_chain` `…calibers[c]` `…evidence` `…[i].assume` | `renderSegmentModels` |
| 假设滑块组（每分部） | `part3.segments[i].assume` | `renderAssumptions` |
| 估值范式卡（每张） | `part3.valuation.paradigms[i]` | `renderValuation` |

**加新锚点**：在渲染该块的 HTML 上加 `data-fbk="<json 路径>"` 即可——`annot.js` 的 `MutationObserver` 会自动补 ✎ pin，无需改标注层。
**路径失效**（改稿把模块重构掉了）：`resolved[].path` 指不到 DOM 时页面只是不打绿边、点「跳到对应模块」给提示，不报错；答复里补一句「该模块已并入 X」即可。

---

## 7 · 坑（实测）

- **file:// 缓存**：改完 `annot.js`/模板重建 HTML 后，浏览器可能仍跑旧版 → 用 `?v=<变化的串>` 强制重取，或换文件名。验收前先确认 `document.scripts` 里有你刚加的函数名。
- **本环境 preview 只对项目目录内的文件执行 JS**（06 §5.2）——验收标注层必须把 HTML 拷进 `Desktop/gyasset/...` 再开。
- **localStorage 按 `report_id` 分区**：同一标的的 v1/v2/v3 页面共享标注（正是我们要的：跨版本累积）；换 `report_id` = 清空历史。
- **KV 最终一致**：读者刚同步完我立刻 pull，偶发拉不到最新几条 —— 隔几秒重拉。
- **不要把 token 烧进页面**：页面只 POST；`GET /api/ann` 的 token 只存本机 config / 环境变量。
- **`--only-new` 依赖 status 流转**：`feedback_resolve.py` 会把处理过的条目在云端置 `resolved/triaged`，所以下轮 `--only-new` 才干净；若跳过 resolve 直接改稿，下轮会重复拉同一批。
- **★浮层/抽屉绝不能吃点击（2026-07-25 用户实测「点击标注之后点不开后续的模块」）**：三条硬规则——① 标注抽屉是浮层不是布局：**点正文任意处即收起，且不 `preventDefault`**（同一下点击照样打开目标模块）；Esc 也收；收起态 `#fb-drawer:not(.open){pointer-events:none}`。② 抽屉开着时给 `body.fbd`，CSS 把各块右上角的 `.fb-pin` 挪到**左上**——否则右侧 392px 连同所有 ✎ 一起被压住，正是本次症状。③ 原文浮层遮罩 `#evmask{pointer-events:none}`：只做视觉压暗，关闭靠文档级 click-outside，避免「第一下只关遮罩、点不到目标」的两次点击。任何新增浮层照此办。
- **看着像没反应 ≠ 没生效**：1.4 费率/瀑布切换曾只换图不换标题与按钮高亮（`renderCost` 里一行死代码），实测被读成「点不开」——**凡切换类交互必须有可见状态反馈**（标题 / 按钮 `.on` / 计数，至少变一项）。
- **读者不署名**很常见 → triage 里 `reader` 空不影响；但多人协作时提醒填一次（抽屉顶部输入框，存本机）。

---

## 8 · CK-5 闸门（Phase 8-9 交付前）

- **CK-5a 上线可标注 + 不挡路**：页面右下有「✎ 标注/疑问」；划词出类型条；模块悬停出 ✎；点一次能在 `localStorage` 落条目且计数 +1；云端模式「同步到云端」返回成功计数（`/api/health` 先绿）。**且抽屉/浮层不吃点击**：抽屉开着时点任一可交互模块（`[Ex]`、chips、`[n]` 角标、预设按钮、阅读路径 chip）→ 同一下既收抽屉又触发目标；收起态 `pointer-events:none`；`#evmask` 为 `pointer-events:none`。逐项读 DOM 验收，别只看肉眼。
- **CK-5b 锚点完整**：`document.querySelectorAll('[data-fbk]').length` ≥ 15，且分部模型/阶段列/估值卡/假设组都在（照 §6 表点检）。
- **CK-5c 回应闭环**：上一轮每条标注在 `feedback.resolved` 或 `feedback.open` 里各有归宿（无空 `answer`）；页顶「本版反馈回应」条数 = 处理数 + 待补数；`action:'fixed'` 的 path 在页面上打了绿边。
- **CK-5d 版本可追**：`meta.version` 已 +1、`meta.updated` 是今天、`changelog` 一句话说清本版改了什么；旧版结论若被推翻，在对应模块正文里写明「原 v_n 口径为 X，本版改为 Y，因 Z」——**不许静默改数**。
