# equity-onepager-interactive · 迁移包
打包时间：2026-08-14　　用途：**本人 Mac → 本人另一台 Mac**

> ⚠️ 本包**含明文凭据**（`scripts/fmp_config.json` 的 FMP api_key）。
> 传输走 AirDrop / 本地拷贝 / 加密外置盘，别走网盘、邮件、聊天工具。**迁完把 zip 删掉。**

---

## 一、装 skill 本体

```bash
mkdir -p ~/.claude/skills && cd ~/.claude/skills
unzip ~/Desktop/equity-onepager-interactive-2026-08-14-migrate.zip
```

装完即可用，**不需要补任何 key**——FMP key 已在包内，rag/feedback 的设计上就不落盘（见第四节）。

## 二、还要单独搬的：`_workspace`（不在包内）

skill 里的 `_workspace` 是一个**符号链接**，指向语料与产物目录，本机是：

    ~/.claude/skills/equity-onepager-interactive/_workspace → ~/Desktop/research-materials

那里有 **45 个标的目录、约 498 MB**（券商研报、专家纪要、page_model、成品页），是第三方材料
不是 skill 本体，所以没打进 zip。**新机上必须自己搬 + 重建软链，否则所有 Phase 都找不到工作区。**

```bash
# 1) 先把语料目录整个拷到新机（外置盘或 rsync 走局域网）
rsync -av --exclude '_trash' --exclude '_incoming_kws' \
  ~/Desktop/research-materials/ <新机>:~/Desktop/research-materials/

# 2) 新机上重建软链
ln -s ~/Desktop/research-materials \
      ~/.claude/skills/equity-onepager-interactive/_workspace
```

`_trash/`（59 MB）和 `_incoming_kws/`（58 MB）建议不搬，上面的命令已排除。
只搬在跟的标的可以再挑；占用最大的是 英科医疗-300677 / 巨星科技-002444 各 ~91 MB、~73 MB。

> 目录里有「裸代码」和「中文名-代码」两套同名目录（如 `300677` 与 `英科医疗-300677`），
> 大小一样，搬之前值得先确认是不是重复占了一倍空间。

## 三、外部依赖（新机要先装）

```bash
python3 -m pip install akshare pandas openpyxl        # Python 3.11
node -v                                               # 必需，见下
```

**Node 现在是必需项不是可选**——CK-6 的 S3 闸要加载 `model_engine.js` 真跑一遍 P&L 引擎。

同级 skill 也要一起搬（各自独立打包）：
`ifind-research`、`comein-research`、`equity-research-industrial-chain`(AlphaPai client)、
`research-rag`（前置语料库）。qcc 系列 MCP 走 MCP 配置，不在 skill 目录里。

## 四、凭据现状（新机上不用手动补）

| 文件 | 状态 |
|---|---|
| `scripts/fmp_config.json` | **明文 key 已随包**。也支持环境变量 `FMP_API_KEY`（优先级更高） |
| `scripts/rag_config.json` | `operative` 段不含 key——它 shell 到 `research-rag/skill/cli.py`，key 在 `research-rag/config.yaml`，**跟着 research-rag 一起搬即可**。`pending_qwen3_7_text.api_key` 早已是占位符且状态 BLOCKED，不影响主流程 |
| `scripts/feedback_config.json` | 设计上就是空的：endpoint 走 `deploy_page.py --endpoint`，token 走环境变量 `FB_ADMIN_TOKEN` |
| iFind / AlphaPai / Comein token | 不在本 skill 内，在各自 skill 的 config 里 |

`feedback/worker/wrangler.toml` 里的 KV namespace id 是占位符——新机首次部署反馈平台要重跑
`wrangler kv namespace create ANNOT` 与 `wrangler secret put FB_ADMIN_TOKEN`（文件头有步骤）。

## 五、本次内容更新（2026-08-14）：第四章重做

第四章现在按「结果 → 该盯谁 → 怎么盯 → 全景 → 链条」排：

| 节 | 内容 | 数据键 |
|---|---|---|
| **4.1 场景**（新） | 哪几个场景让股价涨/跌 · 靠什么解锁（中期叙事＋短期催化）· 赔率与 R/M/V 构成 | `part4.scenarios` |
| 4.2 核心矛盾（双槽位） | 定价核心矛盾 vs 可操作核心矛盾 | `part4.core` |
| 4.3 核心矛盾深度研究 | 怎么理解 → 市面方案 → 落地方案 → 判定表 → 时点 → **历史对标** | `core.*.deepdive` |
| 4.4 矛盾坐标 · 全景 | 三坐标气泡图 + 明细表 | `part4.items` |
| 4.5 叙事链 · 次级矛盾 | 逻辑链 status + 最先断的一环 + 子坐标系 | `part4.narratives` |

四件实质变化：

1. **场景不是自由创作**——场景 ＝ 某条主动矛盾的解方向 × 某条从动矛盾的解方向，`from` 必须
   指名两条真实矛盾 id；3–5 条且**至少一条下行**。
2. **赔率不许手写**——每条场景是第三章模型的一组 `knobs` 参数存档（估值腿按 paradigm key
   寻址，范式切换＝改 `weight`）。页面上点场景名即把滑块跳过去实时重算；
   **验收脚本会拿 knobs 真跑一遍 P&L 引擎去对 `mcap_yi`/`odds`**，对不上直接不过。
3. **矛盾分型（新 `references/13`）**——每条矛盾定 `role`（主动＝生成上行／从动＝限制上行、
   决定节奏）＋ `subtype`（主动十型／从动九型）＋ `clock`。页面上 **● 圆＝主动、■ 方＝从动**
   （等面积，面积仍严格正比赔率）。硬闸：两类各 ≥1。从动型必须走排除链，**纪律型是残差类别**，
   只能在排除掉物理/系统协同/要素/禀赋/制度/资本/弹性之后才允许判，且要过升格三条件。
4. **历史对标查表不生成**——`core.*.deepdive.analog` 的锚来自 13 §6 单维案例库，`diff`（与本例
   的关键差异）必填；没有 diff 的对标是装饰不是判据。

验收从 33 项扩到 **55 项**（S1–S8 场景 · T1–T7 分型 · D1–D3 深度研究 · 原 a–g）：

```bash
node scripts/check_part4.js --model _workspace/<ticker>/page_model.json
```

出包前跑过 26 项反向测试（逐条注入错误），每条都被对应闸门抓住。

## 六、包里有什么

- `SKILL.md`            路由 + Phase 0.0→9 流程 + CK 闸门 + page_model 契约
- `references/`         **13 篇**分册（01 取数配方 … 09 矛盾地图 · 10 开篇章 · 11 预期区间 ·
                        12 筹码龄 · **13 矛盾分型学**）
- `templates/`          页面壳 + app.js 渲染 + annot.js 标注层
- `scripts/`            取数与构建（fetch_ifind / fetch_fundamentals_hkus / fetch_kline /
                        fetch_stock_profile / fetch_earnings / fetch_fmp_consensus / fetch_fwd_pe /
                        fetch_chip_age / build_page / deploy_page / feedback_* / narrative_probe /
                        model_engine.js / tornado.js / ck5_gate.py / check_part4.js / check_consensus.js）
- `feedback/worker/`    反馈平台（Cloudflare Worker + KV + 静态站）
- `examples/INDEX.md`   案例索引

**没打进来的**：
- `_workspace/`（符号链接，498 MB 语料 → 见第二节单独搬）
- `feedback/worker/site/<ticker>/`：已部署报告的旧副本，换机恢复后有**误发风险**；
  首次跑 `deploy_page.py` 会自动重建
- `*.bak` / `*.bak-*`（app.js 有三代备份共 520 KB）/ `__pycache__` / `.DS_Store`

⚠️ 上一版包里的 `_workspace/002371` 案例锚**本机目录现已为空**，这次没有案例锚随包——
新机第一次跑第四章没有形态参照，按 `references/09` + `13` 的契约自推。

## 七、装完自检

```bash
cd ~/.claude/skills/equity-onepager-interactive
node --check templates/app.js && node --check scripts/check_part4.js
ls -l _workspace/                                    # 软链通不通
python3 -c "import akshare,pandas,openpyxl; print('deps ok')"
node scripts/check_part4.js --model _workspace/<任一标的>/page_model.json
```

手边没有 page_model 时，拿一份不含 `part4` 的 JSON 跑应当**退出码 0** 并打印
「part4 缺失或为空 → 第四章将整章隐藏」——说明脚本链路是通的。
