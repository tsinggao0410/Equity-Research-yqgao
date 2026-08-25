# 07 · 前置资料询问 + RAG 语料库（Phase 0.0 ⚡强制）

本 skill 的算账/建模要**扎实、可溯源、不编数**，所以先建一个标的专属 RAG 语料库，Part2 算账/催化 与 Part3 假设/估值 都从里面取证（带 `[doc_id]` 引用）。**复用你现有的 research-rag（`/Users/yqgao/Desktop/gyasset/research-rag`），不重造 RAG。**

---

## 0 · 铁律：每次执行本 skill，先问一句
> **「有没有前置资料压缩包？」**

拿到答复再决定走哪条建库路径。任何情况下都不要跳过这一问。

---

## 1 · 有 zip（用户给前置资料）
```
cd C:/Users/youqi/Desktop/gyasset/research-rag
python research_system.py --zip "<用户给的.zip>" --target "<标的 简称+代码>" --project "<ticker>"
```
- 管线（确定性，自动）：unzip→`build_index`（RAG + qwen3-vl 向量，content-hash 增量）→`extract_facts`（纪要/研报量价）→`model_extractor`（Excel 假设/segment/估值）→`normalize_facts`→`doctor`（fail-loud 过闸）。
- 落 `research-rag/workspaces/<ticker>/`（工作区隔离，多标的互不污染）。**记下 `RAG_WS = workspaces/<ticker>`。**
- 忽略它默认吐的 ORCHESTRATION/交接 prompt（那是给「出整份报告」的下游链用的）；本 skill 只要索引建好即可。
- 用户后续零散补料：`python rag_add.py <文件/目录/zip> --ws workspaces/<ticker>`（未变文件零 embedding）。

## 2 · 没 zip（自动找料）
```
python research_system.py --target "<标的>" --project "<ticker>" --sweep
```
- `--sweep` = **research-sweep 资料回路**：按固定渠道注册表并行扫描，写 `workspaces/<ticker>/SWEEP_PROMPT.md` 交接给一个采集 session；采集→反馈闸（给你看清单/可补充深挖）→确认后 `rag_add` 增量入库→`doctor` 过闸。
- **research-sweep 已覆盖用户要的三源之二**：
  - **飞书「作文实时2」群**：小作文渠道（scope 空格分隔、作文实时2），抓对应标的相关聊天记录/小作文。
  - **AlphaPai**：卖方研报召回 + 点评/段子（行业词二路）。
  - 外加：卖方研报/电话会与专家纪要（近 3 年批量枚举）/雪球/知乎/公众号/公告新闻/本地知识库/SemiAnalysis 等。
- **时间范围按复盘需要设采集问题**：Part2 股价复盘默认 ~3 年 → 采集问题覆盖近 3 年（催化事件、卖方目标价变迁、分部量价假设）；Part1/Part3 需更长历史时，纪要通道可拉近 3 年全量、财务靠 iFind（Phase1）。

### 2b · 只想直采「飞书作文实时2 + AlphaPai」两源（轻量备选，不走 full sweep）
若不想跑整套 research-sweep，可手动直采这两源再打包入库：
- **飞书群消息**（前置资料标准一环，★2026-08-03 lark-cli 接入固化）：用 `scripts/fetch_feishu_msgs.py`：
  ```bash
  python scripts/fetch_feishu_msgs.py --target "<标的简称 代码>"
  # 可选: --keywords "京东方,京东方A,000725" 加别称/代码
  #       --groups "作文实时2,科技大制造-成长小队" 扩展群（默认作文实时2）
  #       --start 2024-01-01 --end 2026-12-31 按复盘时间窗
  #       --list-groups 列出可选群
  ```
  依赖 `lark-cli`（npm 全局已装，用户身份授权含 `search:message` scope）。脚本按关键词逐群搜索 → 缺省落 `~/Desktop/research-materials/<公司名>-<代码>/feishu/`（`<群>_<词>.json/.md` + `_merged.md` 按 message_id 去重，含时间/发送者/原文/跳转链接）。关键词默认拆「简称+6位代码」，命中即入库素材。**数据一律进 research-materials，不落 skill 目录（_workspace 是软链，见 SKILL.md 顶部外迁说明）。**
- AlphaPai：`python /Users/yqgao/.claude/skills/alphapai-research/scripts/alphapai_client.py qa -q "<标的> 近3年 卖方目标价/算账/分部/量价假设/催化" --mode Think`（含 `recall` 召回研报/点评/段子；`start_time/end_time` 卡窗口）→ 存 `MD/JSON`。
- 入库：`python rag_add.py feishu/ --ws workspaces/<ticker>`（或打包 zip 走 §1 `--zip`）。

## 3 · 用户明确「无料且不建库」
声明「本次无 RAG 底稿，算账仅凭 live API（iFind/Comein/AlphaPai）」，跳过建库；页面对应数据标记降级（EST/DNA）。CK-RAG 记为「已声明无料」。

---

## 4 · 查询（Phase 3/4/5 消费 RAG）
薄封装 `scripts/rag_query.py`（透传到 research-rag `skill/cli.py`，自动补 `--ws`）：
```
# 检索(dense qwen3-vl + BM25 + RRF + 时效)：
python scripts/rag_query.py <ticker> search "<标的> 卖方 目标价 算账 分部 催化" --ticker <代码> --as-of <日期> --top 8
# 结构化事实(量价/毛利率/假设/segment/目标价，跨源对账)：
python scripts/rag_query.py <ticker> facts <标的> 毛利率 --by-segment
python scripts/rag_query.py <ticker> facts <标的> 目标价
# 取原文/打开原件：
python scripts/rag_query.py <ticker> get_doc <doc_id> --text
python scripts/rag_query.py <ticker> open_artifact <doc_id>   # Excel→xlsx skill / PDF→pdf / PPT→看图
```
- **`--as-of <阶段末日期>` 防前视**：后验股价复盘按段取证时，只看该日期前发生的材料，杜绝用未来信息解释过去（**Part2 每阶段必用**）。
- **`--ticker`/`--type minutes|report|model|memo|presentation` 预过滤**是精度命脉；实体已归一（顺络/Sunlord/002138→002138.SZ）。
- **消费点**：
  - Phase3（Part2）：卖方算账/目标价/催化事件 → 落 `accounting.steps` 与催化 `driver`，命中原句带 `[doc_id p4]`。
  - Phase4（Part3）：量/价/毛利率/资本开支 假设锚 → `facts` 跨源对账后落 `segments.assume`，冲突标注。
  - Phase5（估值）：可比倍数/终局份额/卖方目标价 → 校准范式 params；隐含 vs 实测差>15% 回 RAG 查漏板块。
- 命中的每条证据进 `page_model.references[{n,text,tag}]`（text 带 doc_id/页码/原句 + 报告期），正文用 `[n]` 角标。**RAG 命中 = FACT/EST（视信源），AlphaPai 段子=EST。**

### 4b · 取证当场就抄进 `evidence`（★2026-07-25 用户反馈固化）
用户反馈：分部的 Driver「逻辑要说清，要 **link 到 RAG 库原句/原文**，并讲清**不同口径的区别与选择**」。所以 `search/facts` 每命中一条要**当场**记成结构化证据，别只抄结论数字：

```
python scripts/rag_query.py <ws> search "<标的> ASP 单价 口径 每套 每柜" --ticker <代码> --top 8
python scripts/rag_query.py <ws> get_doc <doc_id> --text        # ← 逐字拷原句，禁转述
```
→ 落 `part3.segments[i].model.evidence[]`：`{id:'E1',doc_id,page,date,type,src,confidence,quote(逐字),implication(我的推论),used_in:['q','p']}`（字段与渲染见 `04 §1.17`）。
- **一条原句同时支撑多处** → 在 `q_ev/p_ev`、`driver_chain[].ev`、`calibers.rows[].ev`、`driver_focus.ev` 里按 id 复用，不要重复抄原文。
- **多个 doc 给同一参数不同数** → 先建 `model.calibers` 对账表（每行挂各自 `ev`），归一后中枢才进公式；异常锚 `status:'rejected'` 留在表里写明为什么不用（`04 §1.17`）。
- **`--as-of` 依然是后验复盘的硬要求**（Part2）；Part3 假设取证不设 as-of，但 `evidence.date` 必写，页面按日期显示新鲜度。
- 页面会给每张证据卡自动生成 `rag_query.py <rag_ws> get_doc <doc_id> --text` 一键复制命令（`rag_ws` 来自 `feedback.rag_ws`，默认裸代码）——**所以 `doc_id` 必须是本工作区能直接 get 到的真 id**，不许编。

---

## 5 · 嵌入后端（重要）
- **operative = `qwen3-vl-embedding`（现在就能用）**：research-rag 现配（多模态，文本+图表同空间，2560 维，你 2026-06-30 benchmark 的赢家），key 在 `research-rag/config.yaml`，实测 200。§1/§2 建库默认走它，`rag_query.py` 直接用，无需额外配置。
- **`qwen3.7-text-embedding`（用户指定，待激活）**：其 key（`sk-sp-…`）是专属 MaaS 令牌，**在 public DashScope、dashscope-intl、现有 MaaS host 均 401**（2026-07-21 实测）——需**其专属 endpoint host**（形如 `llm-xxxx.cn-beijing.maas.aliyuncs.com`，如同 qwen3-vl 的 host）。host 未到手前用 qwen3-vl，不阻塞。
- **激活步骤（host 到手后，见 `scripts/rag_config.json`）**：
  1. 填 `rag_config.json.pending_qwen3_7_text.endpoint_host` + 确认 protocol（native text-embedding path 或 compatible-mode `/v1/embeddings`）。
  2. `research-rag/retrieve/embedder.py` 已是 provider-agnostic（读 env `RAG_EMB_HOST/RAG_EMB_KEY`，model 是函数参数）——增一个 `embed_text_qwen37` 后端 + 按 config/env 选后端。
  3. 建库时 `RAG_EMB_HOST=<host> RAG_EMB_KEY=<key> RAG_EMB_MODEL=qwen3.7-text-embedding python research_system.py ...`（qwen3.7-text 是纯文本，图表页不进向量空间）。
  4. onepager 工作区用新模型**重建索引**（dim 变→新 lancedb 表）；顺络等既有 qwen3-vl 工作区不受影响（工作区各自独立表）。

---

## 6 · 与 Phase 0 的衔接
Phase 0.0 建好 `RAG_WS` 后，Phase 0 继续解析 ticker/市场、取实测市值。之后每个需要「卖方口径/算账/假设/催化」的地方，**先 `rag_query.py` 取证再落数**，live API 仅补位与交叉验证。CK-RAG 检查：有库时 Part2/Part3 各有若干 `[doc_id]` 引用；无库时已声明降级。
