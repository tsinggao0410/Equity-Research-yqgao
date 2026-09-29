#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基金经理版渲染器回归测试:通俗解释 / 类比 / 例子块(页面不显示标签)、roadmap 路线图、glossary 词典与悬停释义、
「和同类 / 替代方案比」对比节检查、英文缩写首现检查、零章篇幅(导语 / 分节上限)与关键数据精确性、--pm 验收。
用法:python3 test_render_pm.py   (全部通过打印 OK,失败抛 AssertionError)"""
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from render_report_v32 import PM_DEFAULT, Renderer, pm_check  # noqa: E402

SKILL = HERE.parent
G = dict(PM_DEFAULT)

IMG = '![示意图:测试产品界面](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg== "来源:自测")'

MD_OK = """# 测试公司(TEST.US)业务认知

> 2026-09-29 · 基金经理版 · 自测

## 零、业务速览:测试公司

> [!lead] **测试公司卖一种让机器互相说话的软件。**客户是工厂。

```kpis
收入(2Q26) | 1.23 | 亿美元 | 同比 +20%
美国收入占比(FY2025) | 64 | % | 按收入
```

> 来源:自测

### 与普通 SaaS 的差异

表 0-1　测试公司和普通 SaaS 差在哪

| 比什么 | 普通 SaaS | 测试公司 |
|---|---|---|
| 管什么 | 一个部门 | 跨部门 |

> [!plain] 投资含义:跟踪老客户扩容。

### 工作原理

> [!analogy] 它像工厂里的翻译,把各台机器的方言翻成普通话。公司把这层叫 Ontology(本体)。工厂以前要派人挨台抄表,现在屏幕上直接看到每台机器的状态,还能一键下指令,指令会写回原来的系统去执行,不用再开会对表格。

![示意图:测试产品界面](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg== "来源:自测")

### 典型案例

> [!example] 某车企用它之前,查一台设备停机原因要两天;用了之后,十分钟就能在屏幕上找到是哪个零件出了问题,并直接派单给维修班组。

表 0-2　其他典型客户

| 客户 | 时间 | 用途 | 效果 |
|---|---|---|---|
| 甲厂 | 2025-08 | 排产 | 交期缩短 |
| 乙厂 | 2024-06 扩大合作 | 维修 | 停机减少 |

> 来源:自测

### 价值流向

客户按年付费,先试一个车间,见效后扩到全厂,所以收入主要靠老客户越用越多;成本大头是派驻现场的工程师。

### 跟踪指标

老客户每年多花多少钱。这是判断「先小后大」是否成立的唯一硬指标,每季度业绩稿里都能看到。

## 一、公司总览

正文提到 XYZ 但没解释,另有 ABC(自造缩写,一种测试用的接口)已括注,SaaS 在白名单里,TEST 在 allow 里。

## 二、技术与产品:原理、差异与演变

### 2.1 与替代方案的差异

表 2-1　三种方案对比

| 比什么 | 甲 | 乙 |
|---|---|---|
| 位置 | 远 | 近 |

```roadmap
{"title":"图 2-1 技术路线:从抄表到 AI 干活","stages":[
 {"era":"2000s","name":"人工抄表","gist":"派人挨台记录。","solves":"有了记录","cost":"慢","who":"受益:无"},
 {"era":"2010s","name":"联网","gist":"机器自动上报。","solves":"不用抄表","cost":"数据孤岛","who":"受益:设备厂"},
 {"era":"2023 起","name":"AI 干活","gist":"AI 读数据、起草指令。","solves":"省人","cost":"依赖大模型","who":"受益:测试公司","now":true}],
 "fork":{"options":[{"name":"A","if":"本体难复制","signal":"留存率"}]},
 "source":"来源:自测"}
```

## 三、业务甲

> [!plain] 业务甲就是把翻译软件卖给大工厂。

### 3.1 行业规模

Ontology 在本章第一次出现,应加悬停释义;第二次 Ontology 不加。

## 附录、术语小词典

```glossary
术语 | 是什么 | 可以理解成 | 对投资意味着什么
Ontology / 本体 | 按现实里的东西重新摆数据 | 带按钮的地图 | 最难被复制的部分
""" + "\n".join("术语%d | 解释%d | 比方%d | 意义%d" % (k, k, k, k) for k in range(2, 17)) + """
```
"""


def render(md, allow=("TEST",)):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t.md"
        p.write_text(md, encoding="utf-8")
        r = Renderer(p)
        r.pm_allow = list(allow)
        return r.build(md)


def main():
    doc, st = render(MD_OK)
    pm = st["pm"]
    # 1 通俗解释 / 类比 / 例子块:按块类型排版,页面上不出现「白话」「打个比方」「举个例子」这类标签字样
    assert '<div class="plain an"><p>它像工厂里的翻译' in doc
    assert '<div class="plain eg"><p>某车企用它之前' in doc
    assert '<div class="plain"><p>业务甲就是' in doc
    assert "plab" not in doc and ">白话<" not in doc and ">举个例子<" not in doc
    # 2 路线图计入示意图,now 徽标,分岔
    assert 'class="rstage now' in doc and "当前主流" in doc and 'class="rfork"' in doc
    # 2b 零章速览版式:导语与关键数据 + 编号分节(单栏,以留白分隔)
    assert '<div class="brief-hero">' in doc and '<div class="brief">' in doc and '<span class="bno">01</span>' in doc
    assert '<div class="plain imp"><p><span class="nh">投资含义:</span>' in doc or '<div class="plain imp"><p><span class="nh">投资含义：</span>' in doc
    assert doc.count('<section class="bcard') == 5 and doc.count('<section class="bcard wide">') >= 2   # 差异表、产品图整行
    assert st["diagrams"]["total"] >= 1 and pm["roadmaps"] == 1 and pm["tech"]["roadmaps"] == 1
    # 3 词典:行锚点、悬停释义每章只加一次、不进词典章本身
    assert 'id="gl-1"' in doc and pm["glossary_terms"] == 16
    assert doc.count('data-gl="gl-1"') == 2, doc.count('data-gl="gl-1"')   # 零章一次 + 三章一次
    assert '<div id="gltip"' in doc and "查看术语词典" in doc
    # 4 缩写:XYZ 未解释;ABC 括注算解释;SaaS 白名单;TEST 在 allow
    assert pm["unexplained"] == ["XYZ"], pm["unexplained"]
    # 5 零章指标
    d0 = pm["ch0"]
    assert d0["first"] and d0["has_analogy"] and d0["has_example"] and d0["compare"] and d0["plain"] == 3, d0
    assert d0["kpis"] == 2 and d0["kpi_vague"] == [] and 0 < d0["lead"] <= G["ch0_lead_max"], d0
    assert d0["cases"] == 3, d0["cases"]                      # 1 个详写案例 + 表里 2 个
    assert '<td class="dt">2025-08</td>' in doc and '<td>2024-06 扩大合作</td>' in doc, "年月日期应按文本列(不右对齐、不折行)"
    assert all(n <= G["ch0_sec_max"] for _h, n in d0["secs"]), d0["secs"]
    assert d0["compare_first"] and d0["images"] == 1, d0
    assert pm["tech"]["compare"] and pm["tech"]["roadmaps"] == 1, pm["tech"]
    assert pm["business_no_plain"] == [], pm["business_no_plain"]
    GS = dict(G, ch0_min=200)          # 自测文档零章较短
    assert pm_check(st, GS) == [], pm_check(st, GS)
    assert any("零章汉字" in x for x in pm_check(st, G))   # 默认下限 400 应报出
    # 5f 精炼与准确(第五轮反馈):关键数据写「约」或不写期间、缺关键数据、小节超长、导语超长 → 各自报出
    vague = MD_OK.replace("收入(2Q26) | 1.23 | 亿美元 | 同比 +20%", "收入 | 约 1.2 | 亿美元 | 常年水平")
    f = ";".join(pm_check(render(vague)[1], GS))
    assert "关键数据需写精确值并注明期间" in f and "收入" in f, f
    nokpi = MD_OK.split("```kpis")[0] + MD_OK.split("> 来源:自测\n", 1)[1]
    f = ";".join(pm_check(render(nokpi)[1], GS))
    assert "零章缺关键数据" in f, f
    few = MD_OK.replace("| 乙厂 | 2024-06 扩大合作 | 维修 | 停机减少 |\n", "")
    f = ";".join(pm_check(render(few)[1], GS))
    assert "零章典型案例 2 个 < 3" in f, f
    long = MD_OK.replace("客户按年付费,先试一个车间", "客户按年付费。" + "这一段写得太长,细节应该留给正文。" * 12 + "先试一个车间")
    long = long.replace("客户是工厂。", "客户是工厂。" + "导语也写长了。" * 14)
    f = ";".join(pm_check(render(long)[1], GS))
    assert "零章小节正文超过 160 字" in f and "价值流向" in f and "零章导语" in f, f
    # 5b 对比节:零章或技术章去掉「和 XX 比」的节 / 表 → 报出
    nocmp = MD_OK.replace("### 与普通 SaaS 的差异", "### 其他").replace("### 2.1 与替代方案的差异", "### 2.1 其他")
    f = ";".join(pm_check(render(nocmp)[1], GS))
    assert "零章缺「与 XX 的差异」" in f and "技术章缺「与替代方案的差异」" in f, f
    # 5c 标签外露:段首写「打个比方:」、标题含「白话」→ 报出
    leak = MD_OK.replace("> [!analogy] 它像工厂里的翻译", "> [!analogy] 打个比方:它像工厂里的翻译").replace(
        "## 二、技术与产品:原理、差异与演变", "## 二、技术白话:原理、差异与演变")
    f = ";".join(pm_check(render(leak)[1], GS))
    assert "写作标签 2 处" in f, f
    # 5e 先比后讲:差异节不在首位、零章没有产品图 → 报出
    moved = MD_OK.replace(IMG, "")
    k1 = moved.index("### 与普通 SaaS 的差异"); k2 = moved.index("### 工作原理"); k3 = moved.index("### 典型案例")
    moved = moved[:k1] + moved[k2:k3] + moved[k1:k2] + moved[k3:]
    f = ";".join(pm_check(render(moved)[1], GS))
    assert "第一个小节应是「与 XX" in f and "零章缺产品图" in f, f
    # 5d 口语化小标题(第三轮反馈):「钱怎么来」「最该盯的一件事」→ 报出
    col = MD_OK.replace("### 价值流向\n", "### 钱怎么来\n").replace("### 跟踪指标\n", "### 最该盯的一件事\n")
    f = ";".join(pm_check(render(col)[1], GS))
    assert "口语化表述 2 种" in f, f
    # 6 反例:去掉业务章白话块、词典不够、零章不在最前、残留 TODO → 各自报出
    bad = MD_OK.replace("> [!plain] 业务甲就是把翻译软件卖给大工厂。", "TODO 章首说明")
    bad = bad.replace("## 零、业务速览:测试公司", "## 零、业务速览:测试公司(放后面)", 1)
    bad = bad.replace("## 一、公司总览", "## 一、公司总览\n\n先放一段。", 1)
    head, rest = bad.split("## 零、", 1)
    ch0, tail = rest.split("## 一、", 1)
    bad = head + "## 一、" + tail.split("## 二、", 1)[0] + "## 零、" + ch0 + "## 二、" + tail.split("## 二、", 1)[1]
    doc2, st2 = render(bad)
    f = pm_check(st2, dict(GS, min_glossary=20))
    txt = ";".join(f)
    assert "不在最前" in txt and "缺通俗解释块" in txt and "术语词典 16 条 < 20" in txt and "TODO" in txt, f
    # 6b 三列词典(术语 | 含义 | 投资相关性):表头不出现「可以理解为」
    g3 = MD_OK.split("```glossary")[0] + "```glossary\n术语 | 含义 | 投资相关性\nOntology / 本体 | 按业务对象重组数据 | 替换成本高\n```\n"
    doc3, st3g = render(g3)
    assert "<th>投资相关性</th>" in doc3 and "<th>可以理解为</th>" not in doc3 and st3g["pm"]["glossary_terms"] == 1
    # 7 两份写法样例本身必须过 --pm
    for name, allow in (("pltr_plain_sample.md", ("Palantir", "PLTR")), ("cpo_tech_path_sample.md", ())):
        p = SKILL / "examples" / "pm" / name
        _d, st3 = Renderer(p).build(p.read_text(encoding="utf-8")) if not allow else render_file(p, allow)
        assert pm_check(st3, G) == [], (name, pm_check(st3, G))
        assert not st3["errors"], st3["errors"]
    print("OK 基金经理版:解释块 %d、路线图 %d、词典 %d 条、悬停释义 %d 处" % (pm["plain_blocks"], pm["roadmaps"], pm["glossary_terms"], pm["gloss_marked"]))


def render_file(p, allow):
    r = Renderer(p)
    r.pm_allow = list(allow)
    return r.build(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
