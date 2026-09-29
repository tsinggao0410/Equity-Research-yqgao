#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基金经理版渲染器回归测试:白话块 / 例子块、roadmap 路线图、glossary 词典与悬停释义、英文缩写首现检查、--pm 验收。
用法:python3 test_render_pm.py   (全部通过打印 OK,失败抛 AssertionError)"""
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from render_report_v32 import PM_DEFAULT, Renderer, pm_check  # noqa: E402

SKILL = HERE.parent
G = dict(PM_DEFAULT)

MD_OK = """# 测试公司(TEST.US)业务认知

> 2026-09-29 · 基金经理版 · 自测

## 零、一分钟看懂测试公司

> [!lead] **一句话:测试公司卖一种让机器互相说话的软件。**客户是工厂。

> [!plain] 打个比方:它像工厂里的翻译,把各台机器的方言翻成普通话。公司把这层叫 Ontology(本体)。工厂以前要派人挨台抄表,现在屏幕上直接看到每台机器的状态,还能一键下指令,指令会写回原来的系统去执行,不用再开会对表格。

> [!example] 举个例子:某车企用它之前,查一台设备停机原因要两天;用了之后,十分钟就能在屏幕上找到是哪个零件出了问题,并直接派单给维修班组。

> [!plain] 钱怎么来:客户按年付费,先试一个车间,见效后扩到全厂,所以收入主要靠老客户越用越多;成本大头是派驻现场的工程师。

> [!plain] 技术怎么变:从抄表、到联网、到让 AI 在屏幕上直接干活,每一步都在减少人工。细节见第二章。

> [!plain] 要盯的一件事:老客户每年多花多少钱。这是判断「先小后大」是否成立的唯一硬指标,每季度业绩稿里都能看到。

## 一、公司总览

正文提到 XYZ 但没解释,另有 ABC(自造缩写,一种测试用的接口)已括注,SaaS 在白名单里,TEST 在 allow 里。

## 二、技术白话:测试技术是怎么回事、往哪走

```roadmap
{"title":"图 2-1 技术路线:从抄表到 AI 干活","stages":[
 {"era":"2000s","name":"人工抄表","gist":"派人挨台记录。","solves":"有了记录","cost":"慢","who":"受益:无"},
 {"era":"2010s","name":"联网","gist":"机器自动上报。","solves":"不用抄表","cost":"数据孤岛","who":"受益:设备厂"},
 {"era":"2023 起","name":"AI 干活","gist":"AI 读数据、起草指令。","solves":"省人","cost":"依赖大模型","who":"受益:测试公司","now":true}],
 "fork":{"options":[{"name":"A","if":"本体难复制","signal":"留存率"}]},
 "source":"来源:自测"}
```

## 三、业务甲

> [!plain] 白话:业务甲就是把翻译软件卖给大工厂。

### 3.1 行业规模

Ontology 在本章第一次出现,应加悬停释义;第二次 Ontology 不加。

## 附录、术语小词典

```glossary
术语 | 白话解释 | 打个比方 | 对投资意味着什么
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
    # 1 白话块与例子块
    assert '<div class="plain"><p><span class="plab">白话</span><span class="nh">打个比方：</span>' in doc
    assert '<div class="plain eg"><p><span class="plab">举个例子</span>' in doc
    # 2 路线图计入示意图,now 徽标,分岔
    assert 'class="rstage now' in doc and "今天在这" in doc and 'class="rfork"' in doc
    assert st["diagrams"]["total"] >= 1 and pm["roadmaps"] == 1 and pm["tech"]["roadmaps"] == 1
    # 3 词典:行锚点、悬停释义每章只加一次、不进词典章本身
    assert 'id="gl-1"' in doc and pm["glossary_terms"] == 16
    assert doc.count('data-gl="gl-1"') == 2, doc.count('data-gl="gl-1"')   # 零章一次 + 三章一次
    assert '<div id="gltip"' in doc and "查看术语词典" in doc
    # 4 缩写:XYZ 未解释;ABC 括注算解释;SaaS 白名单;TEST 在 allow
    assert pm["unexplained"] == ["XYZ"], pm["unexplained"]
    # 5 零章指标
    d0 = pm["ch0"]
    assert d0["first"] and d0["has_analogy"] and d0["has_example"] and d0["plain"] == 5, d0
    assert pm["business_no_plain"] == [], pm["business_no_plain"]
    GS = dict(G, ch0_min=200)          # 自测文档零章较短
    assert pm_check(st, GS) == [], pm_check(st, GS)
    assert any("零章汉字" in x for x in pm_check(st, G))   # 默认下限 500 应报出
    # 6 反例:去掉业务章白话块、词典不够、零章不在最前、残留 TODO → 各自报出
    bad = MD_OK.replace("> [!plain] 白话:业务甲就是把翻译软件卖给大工厂。", "TODO 章首白话")
    bad = bad.replace("## 零、一分钟看懂测试公司", "## 零、一分钟看懂测试公司(放后面)", 1)
    bad = bad.replace("## 一、公司总览", "## 一、公司总览\n\n先放一段。", 1)
    head, rest = bad.split("## 零、", 1)
    ch0, tail = rest.split("## 一、", 1)
    bad = head + "## 一、" + tail.split("## 二、", 1)[0] + "## 零、" + ch0 + "## 二、" + tail.split("## 二、", 1)[1]
    doc2, st2 = render(bad)
    f = pm_check(st2, dict(GS, min_glossary=20))
    txt = ";".join(f)
    assert "不在最前" in txt and "缺 [!plain]" in txt and "术语词典 16 条 < 20" in txt and "TODO" in txt, f
    # 7 两份写法样例本身必须过 --pm
    for name, allow in (("pltr_plain_sample.md", ("Palantir", "PLTR")), ("cpo_tech_path_sample.md", ())):
        p = SKILL / "examples" / "pm" / name
        _d, st3 = Renderer(p).build(p.read_text(encoding="utf-8")) if not allow else render_file(p, allow)
        assert pm_check(st3, G) == [], (name, pm_check(st3, G))
        assert not st3["errors"], st3["errors"]
    print("OK 基金经理版:白话块 %d、路线图 %d、词典 %d 条、悬停释义 %d 处" % (pm["plain_blocks"], pm["roadmaps"], pm["glossary_terms"], pm["gloss_marked"]))


def render_file(p, allow):
    r = Renderer(p)
    r.pm_allow = list(allow)
    return r.build(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
