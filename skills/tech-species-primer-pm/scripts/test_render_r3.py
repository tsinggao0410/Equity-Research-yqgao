#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三轮评审的渲染器回归测试:有序列表起始编号、全角标点、交叉引用、KPI 副注着色、meta 盒分行、读图提示。
用法:python3 test_render_r3.py   (全部通过打印 OK,失败抛 AssertionError)"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_report_v32 import Renderer, cjk_punct  # noqa: E402

MD = """# 测试公司(000001.SZ)业务认知

> 2026-09-24 · 买方内部研究
> 口径:年报为准,行业用第三方。
> 底稿:东吴深度(2026-07-17)。

## 一、总览

```kpis
营业收入 | 100 | 亿元 | +14.55%;2026H1 30 亿元,−28.99%
```

### 1.1 测试节

正文引用图 1-1、见 1.1 与表 1-1,另有 p10 图 15 不应链接。

1. 第一条
2. 第二条

```chart
{"id":"a","title":"图 1-1 测试:收入(亿元)","type":"bar","categories":["甲(乙)","丙"],"series":[{"name":"收入","data":[1,2]}],"source":"来源:测试"}
```

表 1-1　测试表

| 项 | 值 |
|---|---|
| 第 1 名(125.4GW,23.8%) | 1,234 |

4. **第四条**:接着上文编号
5. 第五条

![研报原图:图 1-2 英文原图](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg== "来源:高盛 p2")
> 读图:横轴为年份,纵轴为千瓦。
"""


def main():
    # 1 全角标点
    assert cjk_punct("东吴深度(2026-07-17)p12,中国") == "东吴深度（2026-07-17）p12，中国"
    assert cjk_punct("营收 1,234 亿元") == "营收 1,234 亿元", cjk_punct("营收 1,234 亿元")
    assert cjk_punct("PowerTitan 3.0(Flex / Plus)") == "PowerTitan 3.0(Flex / Plus)"
    assert cjk_punct("[见 7.4](#s7-4),中") == "[见 7.4](#s7-4)，中"
    assert cjk_punct("{{good:好}}") == "{{good:好}}"
    assert cjk_punct("时间 10:30 开会") == "时间 10:30 开会"
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t.md"
        p.write_text(MD, encoding="utf-8")
        doc, st = Renderer(p).build(MD)
    # 2 有序列表起始编号
    assert '<ol start="4">' in doc, "第二段有序列表应从 4 起"
    assert doc.count("<ol>") >= 1
    # 3 交叉引用:图 / 节 / 表都链接,别家报告的「图 15」不链接,图题自身不链接
    assert '<a class="xref" href="#f1-1">图 1-1</a>' in doc
    assert '<a class="xref" href="#s1-1">1.1</a>' in doc
    assert '<a class="xref" href="#t1-1">表 1-1</a>' in doc
    assert 'href="#f15' not in doc and "p10 图 15" in doc
    assert 'id="f1-1"' in doc and 'id="t1-1"' in doc and 'id="s1-1"' in doc
    # 4 表格单元格全角、千分位不动
    assert "第 1 名（125.4GW，23.8%）" in doc and "1,234" in doc
    # 5 KPI 副注分段着色
    assert '<b class="up">+14.55%</b>' in doc and '<b class="down">−28.99%</b>' in doc
    # 6 meta 盒分行、标签加粗
    assert '<b class="ml">口径</b>' in doc and '<b class="ml">底稿</b>' in doc
    # 7 读图提示进图框
    assert '<div class="fig-hint">读图：横轴为年份，纵轴为千瓦。</div>' in doc or 'class="fig-hint"' in doc
    # 8 图内类目也转全角
    assert "甲（乙）" in doc
    print("OK", st["xrefs"], "处交叉引用")


if __name__ == "__main__":
    main()
