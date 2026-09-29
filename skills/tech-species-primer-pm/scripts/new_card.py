#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""建一张基金经理版业务认知卡(v3.3-PM,在 v3.2 之上加通俗层)的工作目录(第 0 步)。已存在的文件一律不覆盖。

用法:
  python3 new_card.py --root ~/Desktop/research-materials/宏和科技-603256/primer_v32 \
      --name 宏和科技 --code 603256.SH [--type company|theme|industry] [--date 2026-09-26] \
      [--title "宏和科技(603256.SH)业务认知"] [--business 三,四,五] [--no-tech]

产出:
  card.json                 元数据:name/code/type/title/date/out_stem/feishu_name/nav/gate/ref_bg/edition/plain(merge_card.py 读)
  materials.md / questions.md  骨架(第 1 步由主线填)
  work/00_header.md         h1 + meta 盒骨架(口径、底稿两行由主线按实际改)
  work/BRIEF.md             由 references/BRIEF_template.md 填好路径占位符,主线再按本卡改 §0 读者目标、§1 材料表
  work/facts_spine.md       数字底座骨架(六块)
  work/reader_test.md       外行复述评审(评审 C)的记录骨架
  parts/00_一分钟看懂.md、parts/02_技术是怎么回事.md   零章与技术章骨架(照 assets/templates/,写完删掉 TODO 行)
  parts/ images/ sources/{text,cninfo,reports,alphapai,market,peers,web}/ work/{test,shots,pdfimg}/
主题卡(公司里的一块业务)用 --type theme,产业链或技术物种卡用 --type industry;title 默认按类型生成。
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _card import SKILL  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--name", required=True, help="公司或主题简称,用于文件名,如 宏和科技 / 诺基亚DCI / CPO")
ap.add_argument("--code", default="", help="证券代码,如 603256.SH / 09992.HK / PLTR.US;产业链卡可空")
ap.add_argument("--type", default="company", choices=["company", "theme", "industry"])
ap.add_argument("--date", default=dt.date.today().isoformat())
ap.add_argument("--title")
ap.add_argument("--business", default="三、四、五", help="业务章中文序号,写进 BRIEF §3(零章、一总览、二技术章之后)")
ap.add_argument("--no-tech", action="store_true", help="不要技术章(消费品等技术不是看点的公司;须用户同意)")
a = ap.parse_args()

R = Path(a.root).expanduser().resolve()
title = a.title or ("%s(%s)业务认知" % (a.name, a.code) if a.code else "%s业务认知" % a.name)
yymmdd = a.date[2:4] + a.date[5:7] + a.date[8:10]
for d in ["parts", "images", "sources/text", "sources/cninfo", "sources/reports", "sources/alphapai", "sources/market",
          "sources/peers", "sources/web", "work/test", "work/shots", "work/pdfimg"]:
    (R / d).mkdir(parents=True, exist_ok=True)


def put(rel, text):
    p = R / rel
    if p.exists():
        print("exists, skip:", rel)
        return
    p.write_text(text, encoding="utf-8")
    print("wrote", rel)


card = {
    "name": a.name, "code": a.code, "type": a.type, "title": title, "date": a.date,
    "out_stem": "%s-业务认知-基金经理版" % a.name, "feishu_name": "%s科普-基金经理版-%s" % (a.name, yymmdd),
    "nav": {"00": "先看这里", "03": "主要业务", "06": "客户与治理", "09": "经营与跟踪", "12": "附录"},
    "gate": {"min_cjk": 10000},
    "ref_bg": [],
    "edition": "pm",
    "plain": {"min_glossary": 15, "max_unexplained": 3, "ch0_min": 500, "ch0_max": 2200, "ch0_max_acr": 3,
              "tech": not a.no_tech, "allow": [x for x in [a.code.split(".")[0] if a.code and not a.code[0].isdigit() else ""] if x]},
    "_note": "nav 键是两位章号(该章前开始新的目录分组),按最终章节改;gate 可加 min_figs/min_charts/min_visuals/min_tables "
             "(默认 55/30/20/10,只在用户同意时下调);ref_bg 填年报、招股书按页文本(相对 R),照抄检查时当公共语料。"
             "edition=pm 时 merge_card 加 --pm 验收;plain.allow 填公司英文名、代码等不算术语的词;plain.tech=false 须用户同意。",
}
put("card.json", json.dumps(card, ensure_ascii=False, indent=1) + "\n")
put("work/00_header.md", """# %s

> %s · 基金经理版 · 供内部投研使用 · 本卡不写估值、目标价与评级
>
> 口径:公司数据以招股书、年报、半年报原页为准(页码均为 PDF 页码);分部口径说明……;行业数据取 ……,逐图注明来源。
>
> 底稿:(机构 深度/点评(日期)……、纪要来源)。
""" % (title, a.date))
put("materials.md", """# %s · 材料清单(materials.md)

> 盘点日期:%s(Asia/Shanghai)。新取文件存于 `sources/`;用户已有文件只读引用,未改动。页数为 PDF 页数;文本为 PyMuPDF 按页抽取(`sources/text/*.txt`,页标记 `=== pN ===`)。

## 1 一手:招股、问询、定期报告、公告
| 文件 | 页数 | 日期 | 来源 URL | 取得日期 |
|---|---:|---|---|---|

## 2 行情与财务(Wind 最多 1 次,写调用日期与字段;行情走免费源)

## 3 行业数据(机构 / 报告 / 页码 / 口径)

## 4 同行与对照

## 5 研报原图(AlphaPai image,检索词与候选数)

## 6 官方图(招股书 → 年报 → 官网 → 研报原图 → 自绘)

## 7 分类与口径对齐(分部 / 产品两套口径怎么对齐;对不齐的年份写明)

## 8 章节结构与理由(主要业务怎么分章、专题章为何单列)
""" % (title, a.date))
put("questions.md", """# %s · 必答问题清单(questions.md)

> %s。先列 20–35 个问题,再按问题取证;每题写明落在哪一章、需要哪类图/表、主要证据来源。

| # | 问题 | 章 | 图 / 表 | 主要证据 |
|---|---|---|---|---|
| Q1 | | 一 | | |
""" % (title, a.date))
put("work/facts_spine.md", """# %s 全卡统一数字底座(facts spine)

> 建于 %s。**全卡同一个数必须与本表一致**;本表以外的数由各章回原文取,并在 parts/NN_facts.md 登记。
> 金额单位:亿元人民币(除注明外);页码为 PDF 页码。取数路径:(Wind/年报…)→ 逐项回原页核对(见「页码」列)。
> 模板与写法见 skill 的 references/facts_spine_template.md;样例 examples/dekeli/facts_spine.md。

## A. 利润表与现金流(合并口径)
## B. 分产品 / 分部(⚠ 多套口径并存时分开列,写明哪张图用哪套)
## C. 分地区
## D. 客户集中度
## E. 资产负债与营运资本
## F. 产能、产量、销量与单价
## G. 股本、市值与治理
""" % (title, a.date))
put("work/reader_test.md", """# %s · 外行复述评审记录(评审 C)

> 评审人设:懂财务报表和估值、不懂这门技术的基金经理;只读零章、各章 lead 与通俗解释块、技术章。
> 协议见 skill 的 references/review_protocol.md §3。

## 1 复述(评审人不看原文,用自己的话写)
- 这家公司卖什么:
- 卖给谁、谁付钱:
- 怎么赚钱、钱从哪来:
- 和最常被拿来比的同类产品 / 替代技术差在哪:
- 技术怎么变过来、下一步往哪走:
- 最该盯的一件事:

## 2 卡住的地方(逐条:位置 / 原文 / 为什么没看懂;含像模板标签、打断阅读的排版)

## 3 复述与原意的偏差(主线对照原文判定:对 / 偏 / 错)

## 4 处理(改了什么、改在哪)
""" % title)
for rel, tpl_name in (("parts/00_一分钟看懂.md", "ch00_plain.md"), ("parts/02_技术是怎么回事.md", "ch_tech_plain.md")):
    if rel.startswith("parts/02") and a.no_tech:
        continue
    tp = SKILL / "assets" / "templates" / tpl_name
    if tp.exists():
        put(rel, tp.read_text(encoding="utf-8").replace("{NAME}", a.name))
tpl = (SKILL / "references" / "BRIEF_template.md").read_text(encoding="utf-8")
brief = (tpl.replace("{TITLE}", title).replace("{ROOT}", str(R)).replace("{SKILL}", str(SKILL))
         .replace("{BUSINESS_CHAPTERS}", a.business))
put("work/BRIEF.md", brief)
print("\n卡根目录:", R)
print("下一步:填 materials.md / questions.md → 建 work/facts_spine.md → 改 work/BRIEF.md §0/§1/§3 → 按章并行写 parts/"
      "(各章另写 NN_terms.md 术语台账)→ 业务章写完后主线重写零章 → merge_card.py(--gate --pm)→ 评审 A/B/C")
