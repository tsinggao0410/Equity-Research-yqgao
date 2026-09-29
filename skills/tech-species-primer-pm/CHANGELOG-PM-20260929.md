# tech-species-primer-pm · v3.3-PM(2026-09-29)

由 tech-species-primer v3.2.0(用户 2026-09-29 上传的 .skill 包)派生,v3.2 的规格、脚本与数据纪律全部保留,在上面加一层白话。

## 起因:基金经理反馈

1. 「主要是少一些用简要通俗的语言来解释技术和技术变化路径的部分,一上来都是专业术语,没有基础背景的人可能比较难读明白。」
2. 「Palantir 那家公司也是一样,没看明白公司业务。」希望在报告里用一段通俗易懂的方式把业务讲清楚。

## 改了什么

| 类 | 改动 | 文件 |
|---|---|---|
| 结构 | 新增**零、一分钟看懂**(一句话 / 打个比方 / 举个例子 / 钱怎么来 / 技术怎么变 / 要盯的一件事 + 是什么不是什么表 + 钱怎么流图),放在最前 | `references/DESIGN_pm.md` §2,`assets/templates/ch00_plain.md` |
| 结构 | 新增**技术白话章**(问题 / 原理图 / 演进路线图 / 分岔与验证信号 / 对公司意味着什么) | DESIGN_pm §3,`assets/templates/ch_tech_plain.md` |
| 结构 | 每个业务章 lead 之后加**章首白话块**;新增**附录、术语小词典**(由各章 `NN_terms.md` 自动合成) | DESIGN_pm §4,`scripts/merge_card.py` |
| 渲染器 | `> [!plain]` 白话块、`> [!example]` 例子块;` ```roadmap ` 技术演进路线图(每代解决了什么 / 代价 / 谁受益谁受损,当前主力与未量产标记,下一步分岔);` ```glossary ` 术语词典;正文每章首次出现的词典术语**悬停 / 点按显示白话解释**(离线 JS) | `scripts/render_report_v32.py`、`render_assets_v32.py` |
| 验收 | `--pm`:零章在最前、500–1,800 字、有比方与例子、缩写 ≤3;技术白话章有路线图;业务章章首有白话块;词典 ≥15 条;首现无解释缩写 ≤3;无残留 TODO。术语词典不计入 10,000 字门槛 | 渲染器 `pm_check`,card.json `plain` |
| 评审 | 新增**评审 C:外行复述**(扮演不懂技术的基金经理,只读白话层,复述五件事,列卡住的词句;不过就改、换人重评) | `references/review_protocol.md` §3,`work/reader_test.md` |
| 写法 | 白话写法指南:三条总原则、句子级规则、零章与路线图怎么写、25 条类比库(带边界)、四组改写前后对照、自检清单 | `references/plain_language_guide.md` |
| 样例 | Palantir 业务白话样例、CPO 技术路径样例,均可渲染并通过 `--pm` | `examples/pm/` |
| 流程 | 新卡:零章由主线在所有章写完后最后写;技术白话章单独一个 agent;已有 v3.2 卡片可只补白话层升级 | `SKILL.md` |
| 命名 | skill 名 `tech-species-primer-pm`;产出 `{公司}-业务认知-基金经理版`;飞书副本 `{公司}科普-基金经理版-YYMMDD` | `scripts/new_card.py`、`pack_skill.py` |
| 测试 | `scripts/test_render_pm.py`(新语法、悬停释义、缩写首现检查、验收正反例、两份样例过 `--pm`);`pack_skill.py` 自测纳入 | `scripts/` |
