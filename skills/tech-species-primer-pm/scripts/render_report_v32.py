#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_report_v32.py — 业务认知卡 v3.2 渲染器:把按设计规格 DESIGN_v32 §4 写的 Markdown 渲成**单文件自包含 HTML**,
视觉与交互按 §5(取自用户 2026-09-24 给的参考报告:左侧吸顶目录、meta 盒、KPI 磁贴、深蓝表头、圆角图表面板、
ECharts 交互图 + 表格视图、研报原图面板、提示块、时间轴)。ECharts 5.5.1 内联(vendor/echarts-5.5.1.min.js,
Apache-2.0 头注释保留),图片 base64 内嵌,离线可开、无任何外部请求。

用法
    python3 render_report_v32.py 卡.md --out 卡.html [--date 2026-09-24] [--stats stats.json]
                                 [--gate] [--lax] [--offline] [--max-px 1600] [--no-fig-index]
    --gate      按设计规格 §3/§6 的图表密度下限验收(图 ≥55、交互图 ≥30、原图/实物/流程/示意 ≥20、表 ≥10、
                汉字 ≥10,000、每个主要业务章有流程图与产品谱系图),不达标退出码 3。门槛可用 --min-figs 等改。
    --lax       缺图 / 图表 JSON 错误只警告,不以退出码 2 结束。
    --offline   不下载 http(s) 图片(遇到即报错)。
    --pm        基金经理版验收(DESIGN_pm.md §5):零章「一分钟看懂」在最前且篇幅合适、有类比与真实例子、有「和同类 / 替代方案
                有什么不同」对比节与表;技术章有路线图(roadmap 块)与对比节;每个主要业务章在第一个 ### 之前有 [!plain] 块;
                术语词典条目够数;正文英文缩写首现有白话解释(括注 / 进词典)。与 --gate 同用;门槛用 --pm-* 改。
退出码:0 正常;2 有错误(缺图、JSON 错、外链残留);3 --gate / --pm 未达标。

MD 写法(DESIGN_v32 §4,另加 flow / chain / lineup / cards 四种图块)
    # 公司(代码)业务认知            → h1;紧跟的第一个普通引用块 → meta 盒(每行一段)
    ## 一、公司总览                   → 章(目录一级);`## 标题 {#id}` 可指定锚点
    ### 2.1 行业规模                  → 节(目录二级,目录里去掉编号)
    <!-- nav: 三大主业 -->            → 从下一章起目录分组名(不写则自动:总览 / N 大主业 / 经营与跟踪 / 附录)
    > [!lead] …  > [!note] …  > [!info] …  > [!good] …  > [!bad] …
    > 来源:…                         → 紧跟在图 / 表 / 原图后面时并入该图的来源行,否则单独一行 12.3px 灰字
    ```kpis   标签 | 数值 | 单位 | 副注```
    ```chart  {JSON}```               → ECharts;type = stack/bar/barh/group/line/area/combo/pie/waterfall
    ```timeline  年份 | 事件 | hot```  可加 `title: 图 1-6 …` / `subtitle:` / `source:` 行,加了标题就是一张图
    ```flow   {JSON}```               → 生产 / 工艺 / 交付流程图(泳道、阶段、自制外协标签)
    ```chain  {JSON}```               → 产业链与商业模式结构图(列 + 货流 / 钱流箭头;legend:false 或自定义图例文字)
    ```lineup {JSON}```               → 产品谱系:多张实物图按功率段 / 容量排成一张(items[{img,label,sub,group,hot}], cols)
    ```cards  ① 标题 | 正文```        → 编号卡片
    ```footer  MD 段落```             → 替换默认页脚声明
    ![研报原图:标题](images/x.jpg "来源:东吴证券深度(2026-07-17)p30 表 12")   → .shot 面板
    :::two-up … :::   :::three-up … :::   → 两图 / 三图并排
    表 n　标题 + MD 表                 → 表题;数字列自动右对齐;首格「合计 / 总计 / …合计」行加粗
    〔卖方估计〕〔管理层口径〕〔第三方统计〕〔作者计算〕 → 小号灰字读者标签;{{good:文字}} → 彩色小标签

基金经理版另加(DESIGN_pm.md §4)
    > [!plain] …  > [!analogy] …  > [!example] …
                                      → 通俗解释块 / 类比块 / 真实例子块:浅底色段落,页面上不显示任何标签字样
                                         (类比与例子用块类型标记,验收按块类型识别,正文不必写「打个比方:」「举个例子:」)
    ```roadmap {JSON}```              → 技术演进路线图:stages[{era, name, gist, solves, cost, who, now, future, hot}],
                                         rows(改行名,默认 解决了什么 / 代价 / 谁受益谁受损),fork{label, options[{name, if, signal}]},
                                         title / subtitle / source / note;计入示意图(diagrams / roadmap)
    ```glossary  术语 | 是什么 | 可以理解成 | 对投资意味着什么```
                                      → 术语词典表(行锚点 gl-N);术语可写别名「Ontology / 本体」。正文里每章第一次出现的
                                         词典术语自动加虚线下划线,悬停 / 点按显示白话解释(离线 JS,不改原文)

chart JSON 字段(除 type/categories/series 外均可省略)
    id, title, subtitle, type, categories, series[{name, data|values, type, yAxisIndex, unit, color, stack,
    labels, digits, area}], unit, y_name, y2_name, y2_unit, y_min, y_max, y2_min, y2_max, height(数值或
    tall/short), highlight(类目名 / 下标 / 系列名 / 列表), others_grey, colors, forecast_from(类目名或下标),
    segments[{from, to, label, connect}], breaks[{between:[a,b]}], marklines[{y|x, label, pos}], labels(true/"last"),
    percent(百分比堆积), total_label(堆积柱顶标合计), totals(瀑布图总额下标), legend(false 隐藏), rotate,
    bar_width, digits, smooth, source, note, table(默认 true), table_head, table_rows[[标签, 值…]], table_share。
    pie 也可写 data:[{name, value}]。null 显示「—」。
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import html
import io
import json
import mimetypes
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from render_assets_v32 import CSS, GL_JS, JS  # noqa: E402

GENERATOR = "tech-species-primer-pm 3.3.0 render_report_v32(基金经理版)"
ECHARTS_PATH = HERE / "vendor" / "echarts-5.5.1.min.js"
CHART_TYPES = ("stack", "bar", "barh", "group", "line", "area", "combo", "pie", "waterfall")
GATE_DEFAULT = dict(figs=55, charts=30, visuals=20, tables=10, cjk=10000)
IMG_KINDS = [  # (alt 前缀, 统计类, 标签文字, 标签色)
    ("研报原图", "ref", "研报原图", "info"),
    ("官方图", "official", "官方图", "good"),
    ("招股书原图", "official", "招股书", "good"),
    ("招股书", "official", "招股书", "good"),
    ("年报原图", "official", "年报原图", "good"),
    ("年报", "official", "年报", "good"),
    ("官网", "official", "官网", "good"),
    ("实物图", "product", "实物图", "hi"),
    ("产品图", "product", "产品图", "hi"),
    ("流程图", "diagram", "流程图", "warn"),
    ("示意图", "diagram", "示意图", "warn"),
    ("结构图", "diagram", "结构图", "warn"),
    ("作者自绘", "diagram", "作者自绘", "warn"),
    ("自绘", "diagram", "自绘", "warn"),
]
MUST_HAVE = [  # 每个主要业务章必须有的图(设计规格 §3「必放类别」):(名称, 图题 / alt 关键词, 是否硬门槛, 允许的图类)
    # 交互数据图(charts)不算:图题里碰巧有「生产」「产品」的柱状图不能冒充流程图 / 产品图
    ("生产或交付流程图", r"流程|工艺|工序|制造|产线|生产|交付|集成步骤", True, ("diagrams", "images")),
    ("产品谱系或实物图", r"谱系|产品线|全系列|型号|实物|产品矩阵|产品家族|产品图|产品", True, ("images",)),
    ("原理或拓扑示意图", r"原理|拓扑|架构|结构拆解|系统构成|示意", False, ("diagrams", "images")),
    ("应用场景图", r"场景|应用|所处环节|在.{0,6}中的位置", False, ("diagrams", "images")),
]
# ---- 基金经理版(PM)验收:DESIGN_pm.md §5
PM_DEFAULT = dict(min_glossary=15, max_unexplained=3, ch0_min=500, ch0_max=2200, ch0_max_acr=3, tech=True)
CH0_RE = re.compile(r"一分钟看懂|大白话|白话速览")
TECH_RE = re.compile(r"技术白话|是怎么回事|怎么回事|往哪走|技术路径|技术演进")
CMP_RE = re.compile(r"区别|差在哪|不同|对比|比较|替代方案|相比|比一比")      # 「和同类 / 替代方案比」节
ANALOGY_H3 = re.compile(r"像什么|比方|类比|比喻")
EXAMPLE_H3 = re.compile(r"例子|案例|实例")
# 页面上不许出现的「写作标签」:段首「白话:」「打个比方:」这类前缀,章节标题里的「白话」
LABEL_LEAK = re.compile(r"^\s*(?:\*\*)?(白话|大白话|打个比方|打个比喻|举个例子|一句话|钱怎么来|技术怎么变|要盯的一件事)\s*[:：]")
GLOSS_CH_RE = re.compile(r"词典|名词表|术语表")
GLOSS_FENCE = re.compile(r"^\s*```glossary[^\n]*\n(.*?)^\s*```", re.S | re.M)
# 两个以上大写字母的英文词当「缩写 / 术语」(CPO、SiC、FDE、AIP、PowerTitan);单位、财务通用词与读者都认得的词不算
ACR_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z]*[A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9+\-]*)(?![A-Za-z0-9_])")
ACR_ALLOW = set("""AI IT CEO CFO COO CTO CIO GDP IPO GAAP ESG ETF USD RMB HKD EUR JPY US USA UK EU HK A股 H股 PE PB PS ROE ROA
FY YoY QoQ MoM TTM EPS EBIT EBITDA KPI CAGR OEM ODM PC TV APP App PPT PDF Excel OK VS PK CPI PPI PMI SaaS LLC Inc Ltd
GW GWh MW MWh kW kWh TW TWh GHz MHz Gbps Tbps GB TB PB MB KB mAh Ah nm mm um μm cm km kg HK$ US$ RMB¥ H1 H2 Q1 Q2 Q3 Q4
2H 1H CN JP KR TW DE FR IR PR CRM ERP HR B2B B2C C2M DTC GPU CPU iPhone iPad
OpenAI AWS IBM SAP NVIDIA AMD TSMC ASML HP HPE BYD CATL LG SK TODO XX XXX""".split())

CAPTION_RE = re.compile(r"^表\s*[0-9一二三四五六七八九十]+(?:[-–—.．][0-9]+)?[\s　:：]")
IMG_RE = re.compile(r'^!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+"([^"]*)")?\s*\)$')
RL_RE = re.compile(r"〔([^〔〕]{1,16})〕")
TAG_RE = re.compile(r"\{\{(good|warn|bad|info|hi):([^{}]{1,40})\}\}")
CN_NUM = "零一二三四五六七八九十"


def cn_num(n: int) -> str:
    if n <= 10:
        return CN_NUM[n]
    if n < 20:
        return "十" + (CN_NUM[n - 10] if n > 10 else "")
    return CN_NUM[n // 10] + "十" + (CN_NUM[n % 10] if n % 10 else "")


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def cjk_count(s: str) -> int:
    return len(re.findall(r"[一-鿿]", s))


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def lenient_json(text: str):
    t = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    t = re.sub(r",(\s*[}\]])", r"\1", t)
    return json.loads(t)


# ---------------------------------------------------------------- 全角标点
IDEO = "\u3400-\u9fff"
CJK_PUN = "\u3000-\u303f\uff01-\uff0f\uff1a-\uff1f\uff3b-\uff40\uff5b-\uff65「」『』《》〔〕、。，；：（）"
_IS_CJK = re.compile("[%s%s]" % (IDEO, CJK_PUN))
_IS_IDEO = re.compile("[%s]" % IDEO)


def _nb(s, i, step):
    """从 i 往 step 方向找第一个非空白、非 * 的字符。"""
    while 0 <= i < len(s):
        if s[i] not in " \t*":
            return s[i]
        i += step
    return ""


def cjk_punct(s: str) -> str:
    """与汉字相邻的半角 , ; : ( ) 转全角(第三轮评审):跳过数字千分位、时间比值、Markdown 链接地址、{{tag:}}。"""
    if not s or not _IS_IDEO.search(s):
        return s
    hold: list = []

    def _h(m):
        hold.append(m.group(0))
        return "\x02%d\x03" % (len(hold) - 1)
    s = re.sub(r"\]\([^)\s]+\)", _h, s)
    s = re.sub(r"\{\{\w+:", _h, s)
    s = re.sub(r"https?://\S+", _h, s)
    # 括号:由内向外成对处理
    pat = re.compile(r"\(([^()]*)\)")
    while True:
        m = pat.search(s)
        if not m:
            break
        a, b = m.start(), m.end()
        inner = m.group(1)
        conv = (bool(_IS_IDEO.search(inner)) or bool(_IS_CJK.match(_nb(s, a - 1, -1) or "a")) or bool(_IS_CJK.match(_nb(s, b, 1) or "a"))
                or bool(_IS_IDEO.search(s[max(0, a - 8):a])))
        s = s[:a] + ("\x04" if conv else "\x06") + inner + ("\x05" if conv else "\x07") + s[b:]
    s = s.replace("\x04", "（").replace("\x05", "）").replace("\x06", "(").replace("\x07", ")")
    out = []
    for i, ch in enumerate(s):
        if ch in ",;:":
            p, n = _nb(s, i - 1, -1), _nb(s, i + 1, 1)
            if ch == "," and p.isdigit() and n.isdigit() and i + 1 < len(s) and s[i + 1].isdigit():
                out.append(ch)
                continue
            if ch == ":" and p.isdigit() and n.isdigit():
                out.append(ch)
                continue
            near = bool(_IS_CJK.match(p or "a")) or bool(_IS_CJK.match(n or "a"))
            if not near and ch != ":":
                near = ((bool(_IS_IDEO.search(s[max(0, i - 16):i])) or i <= 8)
                        and (bool(_IS_CJK.search(s[i + 1:i + 17])) or len(s) - i <= 8))
            if near:
                out.append({",": "，", ";": "；", ":": "："}[ch])
                continue
        out.append(ch)
    s = "".join(out)
    s = re.sub(r"[ \t]+(?=[，；：（])", "", s)
    s = re.sub(r"(?<=[，；：])[ \t]+", "", s)
    s = re.sub(r"（[ \t]+", "（", s)
    s = re.sub(r"[ \t]+）", "）", s)
    s = re.sub(r"(?<=）)[ \t]+(?=[%s])" % IDEO, "", s)
    return re.sub("\x02(\\d+)\x03", lambda m: hold[int(m.group(1))], s)


XREF_FIG = re.compile(r"(?<![A-Za-z0-9_\-.])图(\s?)(\d{1,2})-(\d{1,2})(?![\d\-])")
XREF_TAB = re.compile(r"(?<![A-Za-z0-9_\-.])表(\s?)(\d{1,2})-(\d{1,2})(?![\d\-])")
XREF_SEC = re.compile(r"(?<![常可所罕少意看预遇])见(\s?)(\d)\.(\d{1,2})(?![\d.–-])")


def xrefs(s: str) -> str:
    s = XREF_FIG.sub(lambda m: '<a class="xref" href="#f%s-%s">图%s%s-%s</a>' % (m.group(2), m.group(3), m.group(1), m.group(2), m.group(3)), s)
    s = XREF_TAB.sub(lambda m: '<a class="xref" href="#t%s-%s">表%s%s-%s</a>' % (m.group(2), m.group(3), m.group(1), m.group(2), m.group(3)), s)
    s = XREF_SEC.sub(lambda m: '见%s<a class="xref" href="#s%s-%s">%s.%s</a>' % (m.group(1), m.group(2), m.group(3), m.group(2), m.group(3)), s)
    return s


# ---------------------------------------------------------------- 行内
def inline(s: str, xref: bool = True) -> str:
    codes: list = []

    def _hold(m):
        codes.append(m.group(1))
        return "%d" % (len(codes) - 1)
    s = re.sub(r"`([^`]+)`", _hold, s)
    s = cjk_punct(s)
    s = html.escape(s, quote=False)
    s = re.sub(r"&lt;(/?(?:br|b|i|u|sup|sub|mark|strong|em)\s*/?)&gt;", r"<\1>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?![\s*])(.+?)(?<![\s*])\*(?![\w*])", r"<em>\1</em>", s)

    def _link(m):
        txt, url = m.group(1), m.group(2)
        ext = url.startswith("http")
        return '<a class="ref" href="%s"%s>%s</a>' % (esc(html.unescape(url)), ' target="_blank" rel="noopener"' if ext else "", txt)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, s)
    s = RL_RE.sub(lambda m: '<span class="rl">〔%s〕</span>' % m.group(1), s)
    s = TAG_RE.sub(lambda m: '<span class="tag %s">%s</span>' % (m.group(1), m.group(2)), s)
    if xref:
        s = xrefs(s)
    return re.sub("(\\d+)", lambda m: "<code>%s</code>" % html.escape(codes[int(m.group(1))], quote=False), s)


def plain(s: str) -> str:
    s = re.sub(r"\{\{\w+:([^{}]+)\}\}", r"\1", s)
    return cjk_punct(re.sub(r"[*`]", "", s).strip())


# ---------------------------------------------------------------- 块解析
def split_row(ln: str) -> list:
    t = ln.strip()
    if t.startswith("|"):
        t = t[1:]
    if t.endswith("|") and not t.endswith("\\|"):
        t = t[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", t)]


def is_align_row(ln: str) -> bool:
    return bool(re.match(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", ln.strip()))


def parse_align(ln: str) -> list:
    out = []
    for c in split_row(ln):
        c = c.replace(" ", "")
        lft, rgt = c.startswith(":"), c.endswith(":")
        out.append("c" if (lft and rgt) else "r" if rgt else "l" if lft else None)
    return out


def _starts_block(s: str) -> bool:
    return bool(s.startswith(("#", ">", "```", "~~~", ":::", "|", "<!--")) or IMG_RE.match(s)
                or re.match(r"^([-*+]|\d+[.)])\s+", s) or s in ("---", "***", "___"))


def parse_blocks(lines: list, i: int = 0, closing: bool = False):
    blocks = []
    n = len(lines)
    while i < n:
        raw = lines[i]
        s = raw.strip()
        ln_no = i + 1
        if closing and s == ":::":
            return blocks, i + 1
        if not s:
            i += 1
            continue
        if s.startswith(":::") and len(s) > 3:
            kids, i = parse_blocks(lines, i + 1, closing=True)
            blocks.append({"k": "box", "cls": s[3:].strip(), "kids": kids, "line": ln_no})
            continue
        if s.startswith("```") or s.startswith("~~~"):
            fence = s[:3]
            lang = s[3:].strip().lower()
            j = i + 1
            body = []
            while j < n and not lines[j].strip().startswith(fence):
                body.append(lines[j])
                j += 1
            blocks.append({"k": "fence", "lang": lang, "body": "\n".join(body), "line": ln_no})
            i = j + 1
            continue
        if s.startswith("<!--"):
            j = i
            buf = []
            while j < n:
                buf.append(lines[j])
                if "-->" in lines[j]:
                    break
                j += 1
            txt = " ".join(buf)
            m = re.search(r"<!--\s*nav\s*[:：]\s*(.*?)\s*-->", txt)
            if m:
                blocks.append({"k": "navgrp", "label": m.group(1), "line": ln_no})
            i = j + 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*?)\s*#*$", s)
        if m:
            txt = m.group(2)
            cid = None
            mm = re.search(r"\s*\{#([A-Za-z][\w-]*)\}\s*$", txt)
            if mm:
                cid, txt = mm.group(1), txt[:mm.start()]
            blocks.append({"k": "h", "lv": len(m.group(1)), "text": txt.strip(), "id": cid, "line": ln_no})
            i += 1
            continue
        if s.startswith("|") and i + 1 < n and is_align_row(lines[i + 1]):
            hdr = split_row(s)
            align = parse_align(lines[i + 1])
            rows = []
            j = i + 2
            while j < n and lines[j].strip().startswith("|"):
                rows.append(split_row(lines[j]))
                j += 1
            blocks.append({"k": "table", "hdr": hdr, "rows": rows, "align": align, "line": ln_no})
            i = j
            continue
        if s.startswith(">"):
            buf = []
            j = i
            while j < n and lines[j].strip().startswith(">"):
                t = lines[j].strip()[1:]
                buf.append(t[1:] if t.startswith(" ") else t)
                j += 1
            blocks.append({"k": "quote", "lines": buf, "line": ln_no})
            i = j
            continue
        m = IMG_RE.match(s)
        if m:
            blocks.append({"k": "img", "alt": m.group(1), "src": m.group(2), "title": m.group(3) or "", "line": ln_no})
            i += 1
            continue
        if s in ("---", "***", "___"):
            blocks.append({"k": "hr", "line": ln_no})
            i += 1
            continue
        m = re.match(r"^([-*+]|\d+[.)])\s+(.*)$", s)
        if m:
            ordered = m.group(1)[0].isdigit()
            start = int(re.match(r"\d+", m.group(1)).group()) if ordered else 1
            items = []
            j = i
            while j < n:
                t = lines[j]
                ts = t.strip()
                mm = re.match(r"^([-*+]|\d+[.)])\s+(.*)$", ts)
                if mm and (mm.group(1)[0].isdigit()) == ordered and not t.startswith("    "):
                    items.append(mm.group(2))
                elif ts and (t.startswith("  ") or t.startswith("\t")) and items and not _starts_block(ts):
                    items[-1] += " " + ts
                else:
                    break
                j += 1
            blocks.append({"k": "list", "ordered": ordered, "start": start, "items": items, "line": ln_no})
            i = j
            continue
        if re.match(r"^<(div|details|summary|section|/div|/details|/section|br|hr)\b", s):
            buf = []
            j = i
            while j < n and lines[j].strip():
                buf.append(lines[j])
                j += 1
            blocks.append({"k": "rawhtml", "html": "\n".join(buf), "line": ln_no})
            i = j
            continue
        buf = [s]
        j = i + 1
        while j < n and lines[j].strip() and not _starts_block(lines[j].strip()):
            buf.append(lines[j].strip())
            j += 1
        blocks.append({"k": "p", "text": " ".join(buf) if not all(re.search(r"[一-鿿]$", b) for b in buf[:-1]) else "".join(buf), "line": ln_no})
        i = j
    return blocks, i


def parse_glossary(body: str) -> list:
    """glossary 块:每行「术语 | 是什么 | 可以理解成 | 对投资意味着什么」;术语可写别名「Ontology / 本体」(斜杠两侧留空格)。"""
    out = []
    for ln in body.splitlines():
        t = ln.strip()
        if not t or t.startswith("<!--") or is_align_row(t):
            continue
        c = split_row(t) if t.startswith("|") else [x.strip() for x in re.split(r"(?<!\\)\|", t)]
        c = (c + ["", "", "", ""])[:4]
        if c[0] in ("术语", "名词", "术语 / 别名"):
            continue
        aliases = [a.strip() for a in re.split(r"\s+[/／]\s+|／", c[0]) if a.strip()]
        out.append(dict(term=c[0], aliases=aliases or [c[0]], expl=c[1], ana=c[2], why=c[3]))
    return out


# ---------------------------------------------------------------- 渲染器
class Renderer:
    def __init__(self, md_path: Path, max_px: int = 1600, offline: bool = False, date: str = None, fig_index: bool = True):
        self.md_path = md_path
        self.base = md_path.parent
        self.max_px = max_px
        self.offline = offline
        self.date_arg = date
        self.fig_index = fig_index
        self.errors: list = []
        self.warns: list = []
        self.charts: list = []
        self.chart_ids: set = set()
        self.nav: list = []          # (lv, id, text, group)
        self.figs: list = []         # dict(anchor, title, kind, cls, ch)
        self.tables = 0
        self.title = ""
        self.meta_html = ""
        self.footer_html = ""
        self.ch_no = 0
        self.sec_no = 0
        self.chapters: list = []     # dict(title, id, html parts, stats)
        self.cur = None
        self.nav_group = None
        self.nav_group_explicit = False
        self.img_cache: dict = {}
        self.fig_seq = 0
        self.last_block_kind = None
        self.svg_seq = 0
        self.miss_seq = 0
        self.img_used: dict = {}     # 已出图的图片文件 → 首次出现行号
        self.anchors: set = set()
        # 基金经理版
        self.pm_prose: list = []     # (章 id, 文本):英文缩写首现检查
        self.pm_allow: list = []     # card.json plain.allow:公司名、代码等不算术语
        self.gloss: list = []        # 术语词典条目(全文预扫)
        self.gloss_alias: dict = {}
        self.gloss_re = None
        self.gloss_ids_used: set = set()
        self.glossary_rows = 0

    # ------------------------------------------------------------ 公共
    def err(self, msg: str, line=None):
        self.errors.append(("第 %s 行: " % line if line else "") + msg)

    def warn(self, msg: str, line=None):
        self.warns.append(("第 %s 行: " % line if line else "") + msg)

    def _new_fig(self, title: str, kind: str, cls: str, check_text: str = None) -> str:
        self.fig_seq += 1
        anchor = "fig-%d" % self.fig_seq
        mm = re.match(r"^\s*图\s*(\d+)-(\d+)", plain(title or ""))
        if mm and ("f%s-%s" % mm.groups()) not in self.anchors:
            anchor = "f%s-%s" % mm.groups()
        elif mm:
            self.warn("图号重复:图 %s-%s" % mm.groups())
        self.anchors.add(anchor)
        self.figs.append(dict(anchor=anchor, title=plain(title) or "(无图题)", kind=kind, cls=cls,
                              ch=self.cur["title"] if self.cur else ""))
        if self.cur is not None:
            self.cur["st"][kind] = self.cur["st"].get(kind, 0) + 1
            self.cur["st"]["titles"].append(plain(check_text or title))
            self.cur["st"]["figs"].append((kind, cls, plain(check_text or title)))
        return anchor

    def _src_html(self, src: str) -> str:
        if not src:
            return ""
        return inline(src)

    # ------------------------------------------------------------ 图片
    def _is_photo(self, im, fmt: str) -> bool:
        if fmt == "JPEG":
            return True
        from PIL import Image  # noqa
        t = im.convert("RGB")
        t.thumbnail((256, 256))
        cols = t.getcolors(maxcolors=65536)
        if cols is None:
            return True
        tot = sum(c for c, _ in cols) or 1
        top = sum(sorted((c for c, _ in cols), reverse=True)[:16]) / tot
        return len(cols) > 4000 and top < 0.65

    def _encode_bitmap(self, path: Path):
        raw = path.read_bytes()
        mime = mimetypes.guess_type(str(path))[0] or "image/png"
        try:
            from PIL import Image
        except Exception:  # noqa: BLE001
            self.warn("没有 PIL,图片原样内嵌: %s" % path.name)
            return raw, mime, 0, 0
        try:
            im = Image.open(io.BytesIO(raw))
            im.load()
        except Exception as e:  # noqa: BLE001
            self.err("图片无法读取 %s: %s" % (path.name, e))
            return raw, mime, 0, 0
        fmt = (im.format or "").upper()
        w, h = im.size
        lim = self.max_px
        scale = min(1.0, lim / float(max(w, h)))
        nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
        lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS")

        def flat(x):
            if x.mode in ("RGBA", "LA") or (x.mode == "P" and "transparency" in x.info):
                rgba = x.convert("RGBA")
                bg = Image.new("RGB", rgba.size, (255, 255, 255))
                bg.paste(rgba, mask=rgba.split()[3])
                return bg
            return x.convert("RGB")
        if self._is_photo(im, fmt):
            if fmt == "JPEG" and scale >= 1.0 and len(raw) <= 450_000:
                return raw, "image/jpeg", w, h
            rgb = flat(im)
            if scale < 1.0:
                rgb = rgb.resize((nw, nh), lanczos)
            buf = io.BytesIO()
            rgb.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
            return buf.getvalue(), "image/jpeg", nw, nh
        if scale >= 1.0 and (len(raw) <= 300_000 or fmt != "PNG"):
            return raw, (Image.MIME.get(fmt) or mime), w, h
        keep_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        im2 = im.convert("RGBA" if keep_alpha else "RGB")
        if scale < 1.0:
            im2 = im2.resize((nw, nh), lanczos)
        buf = io.BytesIO()
        try:
            im2.quantize(colors=256, method=getattr(getattr(Image, "Quantize", Image), "FASTOCTREE")).save(buf, "PNG", optimize=True)
        except Exception:  # noqa: BLE001
            buf = io.BytesIO()
            im2.save(buf, "PNG", optimize=True)
        if scale >= 1.0 and buf.tell() >= len(raw):
            return raw, "image/png", w, h
        return buf.getvalue(), "image/png", nw, nh

    def _fetch(self, url: str, line) -> Path:
        if self.offline:
            raise RuntimeError("--offline 模式不下载外链图片")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 render_report_v32"})
        data = urllib.request.urlopen(req, timeout=25).read()
        cache = HERE / ".img_cache"
        try:
            cache.mkdir(exist_ok=True)
        except OSError:  # skill 安装目录只读时改用系统临时目录
            import tempfile
            cache = Path(tempfile.gettempdir()) / "render_v32_img_cache"
            cache.mkdir(exist_ok=True)
        ext = Path(url.split("?")[0]).suffix or ".jpg"
        p = cache / ("ext_%d%s" % (abs(hash(url)) % 10 ** 10, ext))
        p.write_bytes(data)
        return p

    def embed_image(self, src: str, alt: str, line) -> str:
        if src.startswith("data:"):
            return '<img src="%s" alt="%s" loading="lazy" decoding="async">' % (esc(src), esc(alt))
        if src.startswith("http://") or src.startswith("https://"):
            try:
                path = self._fetch(src, line)
            except Exception as e:  # noqa: BLE001
                self.err("外链图片下载失败(不许留外链): %s (%s)" % (src, e), line)
                return '<div class="miss">外链图片未能内嵌:%s</div>' % esc(src)
        else:
            path = (self.base / src).resolve()
        if not path.exists():
            self.err("缺图: %s" % src, line)
            return '<div class="miss">缺图:%s</div>' % esc(src)
        if path.suffix.lower() == ".svg":
            svg = path.read_text(encoding="utf-8", errors="ignore")
            svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
            svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg, flags=re.I).strip()
            svg = re.sub(r"<script[\s\S]*?</script>", "", svg, flags=re.I)
            self.svg_seq += 1
            pfx = "s%d-" % self.svg_seq
            ids = set(re.findall(r'\bid="([^"]+)"', svg))
            if ids:
                svg = re.sub(r'\bid="([^"]+)"', lambda m: 'id="%s%s"' % (pfx, m.group(1)), svg)
                svg = re.sub(r"url\(#([^)\s]+)\)", lambda m: "url(#%s%s)" % (pfx, m.group(1)) if m.group(1) in ids else m.group(0), svg)
                svg = re.sub(r'((?:xlink:)?href)="#([^"]+)"', lambda m: '%s="#%s%s"' % (m.group(1), pfx, m.group(2)) if m.group(2) in ids else m.group(0), svg)
            if re.search(r'(?:href|src)="https?://', svg):
                self.err("SVG 内含外链: %s" % src, line)
            return '<div class="svgwrap">%s</div>' % svg
        key = str(path)
        if key not in self.img_cache:
            data, mime, w, h = self._encode_bitmap(path)
            # 单独成图时不把小图放大到超过原始宽度 1.35 倍(防糊);并排与谱系里的图由栅格宽度决定
            wh = (' width="%d" height="%d" style="max-width:%dpx"' % (w, h, int(w * 1.35))) if w and h else ""
            self.img_cache[key] = ("data:%s;base64,%s" % (mime, base64.b64encode(data).decode()), wh, len(data))
        uri, wh, _ = self.img_cache[key]
        return '<img src="%s" alt="%s"%s decoding="async">' % (uri, esc(alt), wh)

    def render_img(self, b: dict, src_line: str = None) -> str:
        alt = b["alt"].strip()
        cls, tag_txt, tag_cls, title = "other", "", "", alt
        m = re.match(r"^(\S{2,6}?)\s*[:：]\s*(.*)$", alt)
        if m:
            for pre, c, t, tc in IMG_KINDS:
                if m.group(1) == pre:
                    cls, tag_txt, tag_cls, title = c, t, tc, m.group(2)
                    break
        src = b.get("title") or ""
        if src_line:
            src = (src + " " if src else "") + src_line
        if not src:
            self.warn("原图缺来源行: %s" % alt[:40], b["line"])
        if cls == "other":
            self.warn("图片 alt 没有类别前缀(研报原图 / 官方图 / 实物图 / 示意图…): %s" % alt[:40], b["line"])
        chip = '<span class="tag %s kind">%s</span>' % (tag_cls, esc(tag_txt)) if tag_txt else ""
        body = self.embed_image(b["src"], plain(alt), b["line"])
        # 缺图不计图数;同一文件重复出图只计第一次(设计规格 §3「同一信息不重复出图」)
        key = b["src"] if b["src"].startswith(("http", "data:")) else str((self.base / b["src"]).resolve())
        if body.startswith('<div class="miss"'):
            self.miss_seq += 1
            anchor = "miss-%d" % self.miss_seq
        elif key in self.img_used:
            self.warn("同一图片重复出图(首次在第 %s 行),本次不计入图数: %s" % (self.img_used[key], b["src"]), b["line"])
            self.miss_seq += 1
            anchor = "dup-%d" % self.miss_seq
        else:
            self.img_used[key] = b["line"]
            anchor = self._new_fig(title, "images", cls, alt)
            if self.cur is not None:
                self.cur["st"]["img_" + cls] = self.cur["st"].get("img_" + cls, 0) + 1
        cap = "<figcaption>%s</figcaption>" % self._src_html(src) if src else ""
        hint = ('<div class="fig-hint">%s</div>' % inline(re.sub(r"^读图(提示)?\s*[:：]\s*", "", b["hint"]))) if b.get("hint") else ""
        return '<figure class="shot" id="%s"><div class="fig-h"><div class="fig-t">%s%s</div></div>%s%s%s</figure>' % (anchor, chip, inline(title, False), body, hint, cap)

    # ------------------------------------------------------------ 图表
    def _num(self, v, where, line):
        if v is None:
            return None
        if isinstance(v, bool):
            self.err("%s 含布尔值" % where, line)
            return None
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            t = v.strip().replace(",", "")
            if t in ("", "-", "—", "null", "NA", "n.a."):
                return None
            try:
                f = float(t)
                return int(f) if re.fullmatch(r"-?\d+", t) else f
            except ValueError:
                self.err("%s 含非数字「%s」" % (where, v), line)
                return None
        self.err("%s 含非法值 %r" % (where, v), line)
        return None

    def _cat_index(self, cats, v):
        if v is None:
            return None
        if isinstance(v, int) and not isinstance(v, bool):
            return v if 0 <= v < len(cats) else None
        v = str(v)
        return cats.index(v) if v in cats else None

    def render_chart(self, b: dict, src_line: str = None) -> str:
        line = b["line"]
        try:
            spec = lenient_json(b["body"])
        except Exception as e:  # noqa: BLE001
            self.err("chart JSON 解析失败: %s" % e, line)
            return '<div class="miss">chart JSON 解析失败(第 %s 行):%s</div>' % (line, esc(e))
        t = str(spec.get("type", "")).lower()
        if t not in CHART_TYPES:
            self.err("chart type「%s」不支持(可用 %s)" % (t, "/".join(CHART_TYPES)), line)
            return '<div class="miss">chart type 不支持:%s</div>' % esc(t)
        cats = spec.get("categories")
        series = spec.get("series") or []
        if t == "pie" and not cats and spec.get("data"):
            cats = [str(d.get("name")) for d in spec["data"]]
            series = [{"name": spec.get("series_name") or spec.get("unit") or "数值", "data": [d.get("value") for d in spec["data"]]}]
        if not isinstance(cats, list) or not cats:
            self.err("chart 缺 categories", line)
            return '<div class="miss">chart 缺 categories</div>'
        cats = [str(c) for c in cats]
        if not series:
            self.err("chart 缺 series", line)
            return '<div class="miss">chart 缺 series</div>'
        title = spec.get("title") or ""
        if not title:
            self.warn("交互图缺图题", line)
        elif not re.match(r"^图\s*[0-9]", title):
            self.warn("交互图题没有「图 n」编号: %s" % title[:30], line)
        norm = []
        for k, se in enumerate(series):
            data = se.get("data", se.get("values"))
            nm = str(se.get("name") or "系列%d" % (k + 1))
            if not isinstance(data, list):
                self.err("系列「%s」缺 data" % nm, line)
                data = [None] * len(cats)
            if len(data) != len(cats):
                self.err("系列「%s」有 %d 个值,categories 有 %d 个" % (nm, len(data), len(cats)), line)
                data = (list(data) + [None] * len(cats))[:len(cats)]
            vals = [self._num(v, "系列「%s」" % nm, line) for v in data]
            dg = se.get("digits", spec.get("digits"))
            if isinstance(dg, int):
                vals = [None if v is None else round(v, dg) for v in vals]
            o = {"name": nm, "data": vals}
            for key in ("type", "yAxisIndex", "unit", "color", "stack", "labels", "digits", "area"):
                if key in se and se[key] is not None:
                    o[key] = se[key]
            if o.get("type") not in (None, "bar", "line"):
                self.err("系列「%s」type 只能是 bar / line" % nm, line)
                o.pop("type", None)
            if o.get("labels") == "all":
                o["labels"] = True
            norm.append(o)
        cid = re.sub(r"[^\w-]", "_", str(spec.get("id") or "chart%d" % (len(self.charts) + 1)))
        if cid in self.chart_ids:
            self.warn("chart id 重复「%s」,已自动改名" % cid, line)
            k = 2
            while "%s_%d" % (cid, k) in self.chart_ids:
                k += 1
            cid = "%s_%d" % (cid, k)
        self.chart_ids.add(cid)
        dom = "c_" + cid
        unit = spec.get("unit") or ""
        js = {"dom": dom, "type": t, "categories": cats, "series": norm, "unit": unit,
              "y_name": spec.get("y_name", unit if t not in ("pie",) else ""),
              "y2_unit": spec.get("y2_unit") or "", "y2_name": spec.get("y2_name", spec.get("y2_unit") or "")}
        for key in ("y_min", "y_max", "y2_min", "y2_max", "others_grey", "colors", "labels", "total_label", "legend",
                    "rotate", "interval", "bar_width", "digits", "smooth", "area", "stack", "label_unit", "no_total", "x_name"):
            if key in spec and spec[key] is not None:
                js[key] = spec[key]
        if js.get("labels") == "all":
            js["labels"] = True
        js["y2"] = any(se.get("yAxisIndex") == 1 for se in norm)
        js["pct"] = bool(spec.get("percent"))
        # 预测年
        fc = None
        if spec.get("forecast_from") is not None:
            fc = self._cat_index(cats, spec["forecast_from"])
            if fc is None:
                self.warn("forecast_from「%s」不在 categories 里" % spec["forecast_from"], line)
        js["fc"] = fc if fc is not None else -1
        js["fc_label"] = spec.get("forecast_label") or "预测"
        if isinstance(spec.get("total_values"), list):
            js["total_values"] = [self._num(v, "total_values", line) for v in spec["total_values"]]
        # 高亮:系列名 → 系列高亮;类目名 / 下标 → 类目高亮
        hl = spec.get("highlight")
        hl_list = hl if isinstance(hl, list) else ([] if hl is None else [hl])
        names = [se["name"] for se in norm]
        hi_cats = []
        for h in hl_list:
            if isinstance(h, str) and h in names and (len(norm) > 1 or h not in cats):
                js["hi_series"] = h
            else:
                idx = self._cat_index(cats, h)
                if idx is None:
                    self.warn("highlight「%s」既不是系列名也不是类目" % h, line)
                else:
                    hi_cats.append(idx)
        js["hi_cats"] = hi_cats
        if isinstance(spec.get("cat_colors"), list):
            js["cat_colors"] = spec["cat_colors"]
        elif len(norm) == 1 and t in ("bar", "barh", "pie") and isinstance(spec.get("colors"), list) and len(spec["colors"]) == len(cats):
            js["cat_colors"] = spec["colors"]
            js.pop("colors", None)
        # 分段 / 断点 / 参考线
        bands, breaks = [], []
        segs = spec.get("segments") or []
        seg_idx = []
        for sg in segs:
            s0 = self._cat_index(cats, sg.get("from"))
            if s0 is None:
                self.warn("segments.from「%s」不在 categories 里" % sg.get("from"), line)
                continue
            seg_idx.append((s0, sg))
        seg_idx.sort(key=lambda x: x[0])
        for k, (s0, sg) in enumerate(seg_idx):
            e0 = self._cat_index(cats, sg.get("to")) if sg.get("to") is not None else None
            if e0 is None:
                e0 = (seg_idx[k + 1][0] - 1) if k + 1 < len(seg_idx) else len(cats) - 1
            bands.append({"s": s0, "e": max(s0, e0), "label": sg.get("label", ""), "fc": bool(sg.get("forecast"))})
            if sg.get("connect") is False and s0 > 0:
                breaks.append(s0)
        for br in spec.get("breaks") or []:
            bt = br.get("between") if isinstance(br, dict) else br
            if isinstance(bt, list) and len(bt) == 2:
                ix = self._cat_index(cats, bt[1])
                if ix:
                    breaks.append(ix)
        if fc is not None and fc >= 0 and spec.get("forecast_band", True) and not any(b0["s"] <= fc <= b0["e"] for b0 in bands):
            bands.append({"s": fc, "e": len(cats) - 1, "label": spec.get("forecast_label", "预测"), "fc": True})
        if t in ("pie",):
            bands = []
        js["bands"] = bands
        js["breaks"] = sorted(set(breaks))
        mls = []
        for ml in spec.get("marklines") or []:
            if isinstance(ml, dict) and (ml.get("y") is not None or ml.get("x") is not None):
                mls.append({k: ml[k] for k in ("x", "y", "label", "color", "pos") if k in ml})
        js["marklines"] = mls
        if t == "waterfall":
            tots = spec.get("totals") or []
            js["totals"] = [x for x in (self._cat_index(cats, v) for v in tots) if x is not None]
            js["wf_names"] = spec.get("waterfall_names") or ["总额", "增加", "减少"]
        # 图内文字同样转全角标点(类目、系列名、瀑布图图例)
        js["categories"] = [cjk_punct(c) for c in js["categories"]]
        for se in js["series"]:
            se["name"] = cjk_punct(se["name"])
        if js.get("hi_series"):
            js["hi_series"] = cjk_punct(js["hi_series"])
        if js.get("wf_names"):
            js["wf_names"] = [cjk_punct(x) for x in js["wf_names"]]
        self.charts.append(js)
        # HTML
        anchor = self._new_fig(title, "charts", "chart")
        hgt = spec.get("height")
        cls, style = "chart", ""
        if hgt in ("tall", "short"):
            cls += " " + hgt
        elif isinstance(hgt, (int, float)) and 160 <= hgt <= 900:
            style = ' style="height:%dpx"' % hgt
        src = spec.get("source") or ""
        if src_line:
            src = (src + " " if src else "") + src_line
        if not src:
            self.warn("交互图缺来源: %s" % (title[:30] or cid), line)
        note = spec.get("note") or ""
        parts = ['<figure class="cfig" id="%s">' % anchor, '<div class="fig-h">']
        if title:
            parts.append('<div class="fig-t">%s</div>' % inline(title, False))
        if spec.get("subtitle"):
            parts.append('<div class="fig-s">%s</div>' % inline(spec["subtitle"]))
        parts.append("</div>")
        parts.append('<div id="%s" class="%s"%s role="img" aria-label="%s"></div>' % (dom, cls, style, esc(plain(title))))
        if spec.get("table", True) is not False:
            parts.append(self.chart_table(spec, js, t))
        if src or note:
            parts.append("<figcaption>%s%s</figcaption>" % (self._src_html(src),
                         ('<span class="fig-note">%s</span>' % inline(note)) if note else ""))
        parts.append("</figure>")
        return "".join(parts)

    @staticmethod
    def fmt_num(v, digits=None) -> str:
        if v is None:
            return "—"
        if isinstance(v, str):
            return esc(v)
        if digits is not None:
            s = "{:,.{d}f}".format(v, d=int(digits))
        elif isinstance(v, int):
            s = "{:,}".format(v)
        else:
            r = repr(float(v))
            d = 0 if ("e" in r or "." not in r) else len(r.split(".")[1])
            d = min(d, 3)
            s = "{:,.{d}f}".format(v, d=d)
            if d and s.endswith("0" * d):
                s = s.split(".")[0] if float(v).is_integer() else s
        return s

    def chart_table(self, spec: dict, js: dict, t: str) -> str:
        cats, ser, unit = js["categories"], js["series"], js["unit"]
        dg = spec.get("digits")
        head0 = spec.get("table_head")
        rows_html = []
        single = len(ser) == 1 and t in ("bar", "barh", "pie", "waterfall")
        if single:
            se = ser[0]
            u = se.get("unit") or unit
            hdr = [head0 or "项目", "%s%s" % (se["name"], "(%s)" % u if u else "")]
            share = t == "pie" or spec.get("table_share")
            tot = sum(v for v in se["data"] if isinstance(v, (int, float))) if share else 0
            if share:
                hdr.append("占比")
            th = "".join('<th%s>%s</th>' % (' class="n"' if k else "", esc(h)) for k, h in enumerate(hdr))
            for k, c in enumerate(cats):
                v = se["data"][k]
                cells = ['<td>%s</td>' % esc(c), '<td class="n">%s</td>' % self.fmt_num(v, se.get("digits", dg))]
                if share:
                    cells.append('<td class="n">%s</td>' % ("—" if v is None or not tot else "%.1f%%" % (v / tot * 100)))
                hi = k in js.get("hi_cats", [])
                rows_html.append("<tr>%s</tr>" % "".join(cells).replace("<td>", "<td><strong>", 1).replace("</td>", "</strong></td>", 1) if hi else "<tr>%s</tr>" % "".join(cells))
            if share and tot:
                rows_html.append('<tr class="tot"><td>合计</td><td class="n">%s</td><td class="n">100%%</td></tr>' % self.fmt_num(round(tot, 3), se.get("digits", dg)))
        else:
            hdr0 = head0 or ("项目(%s)" % unit if unit and not any(se.get("unit") and se.get("unit") != unit for se in ser) else "项目")
            th = "<th>%s</th>" % esc(hdr0) + "".join('<th class="n">%s</th>' % esc(c) for c in cats)
            mixed = any(se.get("unit") and se.get("unit") != unit for se in ser) or js.get("y2")
            for se in ser:
                u = se.get("unit") or (js.get("y2_unit") if se.get("yAxisIndex") == 1 else unit)
                nm = se["name"] + ("(%s)" % u if (mixed and u) else "")
                if js.get("hi_series") == se["name"]:
                    nm = "<strong>%s</strong>" % esc(nm)
                else:
                    nm = esc(nm)
                rows_html.append("<tr><td>%s</td>%s</tr>" % (nm, "".join('<td class="n">%s</td>' % self.fmt_num(v, se.get("digits", dg)) for v in se["data"])))
            if t == "stack" and len(ser) > 1 and not spec.get("no_total") and js.get("total_values"):
                rows_html.append('<tr class="tot"><td>合计</td>%s</tr>' % "".join('<td class="n">%s</td>' % self.fmt_num(v, dg) for v in js["total_values"]))
            elif t == "stack" and len(ser) > 1 and not spec.get("no_total"):
                sums = []
                for k in range(len(cats)):
                    vs = [se["data"][k] for se in ser if isinstance(se["data"][k], (int, float))]
                    if not vs:
                        sums.append(None)
                        continue
                    d = max([0] + [len(repr(float(v)).split(".")[1]) if isinstance(v, float) and "e" not in repr(v) else 0 for v in vs])
                    sums.append(round(sum(vs), min(d, 3)))
                rows_html.append('<tr class="tot"><td>合计</td>%s</tr>' % "".join('<td class="n">%s</td>' % self.fmt_num(v, dg) for v in sums))
        for extra in spec.get("table_rows") or []:
            if isinstance(extra, list) and extra:
                lab = str(extra[0])
                cls = ' class="tot"' if re.match(r"^(合计|总计)", lab) else ' class="subrow"'
                rows_html.append("<tr%s><td>%s</td>%s</tr>" % (cls, inline(lab), "".join('<td class="n">%s</td>' % (self.fmt_num(self._num(v, "table_rows", None), dg) if not isinstance(v, str) or re.match(r"^-?[\d.,]+$", v) else esc(v)) for v in extra[1:])))
        return ('<details class="dv"><summary>表格视图</summary><div class="tbl-wrap"><table><thead><tr>%s</tr></thead>'
                "<tbody>%s</tbody></table></div></details>") % (th, "".join(rows_html))

    # ------------------------------------------------------------ 自绘图块
    def _json_block(self, b: dict, what: str):
        try:
            return lenient_json(b["body"])
        except Exception as e:  # noqa: BLE001
            self.err("%s JSON 解析失败: %s" % (what, e), b["line"])
            return None

    def _fig_wrap(self, cls: str, spec: dict, inner: str, kind: str, figcls: str, src_line: str = None, line=None) -> str:
        title = spec.get("title") or ""
        if not title:
            self.warn("%s 缺图题" % cls, line)
        anchor = self._new_fig(title, kind, figcls)
        src = spec.get("source") or ""
        if src_line:
            src = (src + " " if src else "") + src_line
        if not src:
            self.warn("%s 缺来源行: %s" % (cls, title[:30]), line)
        note = spec.get("note") or ""
        out = ['<figure class="%s" id="%s">' % (cls, anchor), '<div class="fig-h">']
        if title:
            out.append('<div class="fig-t">%s</div>' % inline(title, False))
        if spec.get("subtitle"):
            out.append('<div class="fig-s">%s</div>' % inline(spec["subtitle"]))
        out.append("</div>")
        out.append(inner)
        if src or note:
            out.append("<figcaption>%s%s</figcaption>" % (self._src_html(src), ('<span class="fig-note">%s</span>' % inline(note)) if note else ""))
        out.append("</figure>")
        return "".join(out)

    @staticmethod
    def _tag_cls(tag: str) -> str:
        if re.search(r"自制|自研|自产|核心|自建", tag):
            return "good"
        if re.search(r"外协|外购|外包|委外|采购|代工", tag):
            return "warn"
        if re.search(r"客户|第三方|合作", tag):
            return "info"
        return "hi"

    def _flow_step(self, st: dict, no: int, extra: str) -> str:
        cls = "fstep" + extra
        for f in ("hot", "muted", "strong"):
            if st.get(f):
                cls += " " + f
        tag = st.get("tag")
        tg = ('<span class="tag %s">%s</span>' % (st.get("tag_class") or self._tag_cls(tag), esc(tag))) if tag else ""
        h = ['<div class="%s">' % cls, '<div class="no">%02d%s</div>' % (no, tg), '<div class="lb">%s</div>' % inline(str(st.get("label", "")))]
        if st.get("sub"):
            h.append('<div class="sb">%s</div>' % inline(str(st["sub"])))
        if st.get("note"):
            h.append('<div class="nt">%s</div>' % inline(str(st["note"])))
        h.append("</div>")
        return "".join(h)

    def render_flow(self, b: dict, src_line: str = None) -> str:
        spec = self._json_block(b, "flow")
        if spec is None:
            return '<div class="miss">flow JSON 解析失败(第 %s 行)</div>' % b["line"]
        lanes = spec.get("lanes") or [{"name": None, "steps": spec.get("steps") or []}]
        per = int(spec.get("per_row") or 6)
        maxn = max(len(ln.get("steps") or []) for ln in lanes) if lanes else 0
        if maxn == 0:
            self.err("flow 没有步骤", b["line"])
        cols = min(per, maxn) or 1
        has_lane = any(ln.get("name") for ln in lanes)
        lw = max([len(str(ln.get("name") or "")) for ln in lanes] + [4])
        out = ['<div class="flow" style="--lw:%dpx">' % min(140, max(78, lw * 14 + 20))]
        no = 0
        tags_seen = []
        for ln in lanes:
            steps = ln.get("steps") or []
            rows = [steps[k:k + cols] for k in range(0, len(steps), cols)] or [[]]
            out.append('<div class="flow-lane%s">' % ("" if has_lane else " nolane"))
            if has_lane:
                out.append('<div class="lane-name">%s</div>' % inline(str(ln.get("name") or "")))
            out.append('<div class="flow-rows">')
            if not spec.get("continue_numbering", True):
                no = 0
            for r, rw in enumerate(rows):
                out.append('<div class="flow-steps" style="--n:%d">' % cols)
                if any(st.get("phase") for st in rw):
                    k = 0
                    while k < len(rw):
                        ph = rw[k].get("phase") or ""
                        j = k
                        while j + 1 < len(rw) and (rw[j + 1].get("phase") or "") == ph:
                            j += 1
                        hot = any(rw[x].get("hot") for x in range(k, j + 1)) and spec.get("phase_hot", False)
                        out.append('<div class="fphase%s" style="grid-column:span %d">%s</div>' % (" hot" if hot else "", j - k + 1, inline(ph) if ph else "&nbsp;"))
                        k = j + 1
                    if len(rw) < cols:
                        out.append('<div class="fpad" style="grid-column:span %d"></div>' % (cols - len(rw)))
                for k, st in enumerate(rw):
                    no += 1
                    last_in_lane = (r == len(rows) - 1 and k == len(rw) - 1)
                    extra = " last" if last_in_lane else (" wrap" if k == len(rw) - 1 else "")
                    if st.get("tag") and st["tag"] not in tags_seen:
                        tags_seen.append(st["tag"])
                    out.append(self._flow_step(st, no, extra))
                out.append("</div>")
            out.append("</div></div>")
        out.append("</div>")
        if spec.get("legend", True) and tags_seen:
            out.append('<div class="flow-legend">标签：%s%s</div>' % ("".join('<span class="tag %s">%s</span>' % (self._tag_cls(t), esc(t)) for t in tags_seen),
                                                                  "　橙框 = 关键工序 / 价值所在" if any(st.get("hot") for ln in lanes for st in (ln.get("steps") or [])) else ""))
        return self._fig_wrap("flowfig", spec, "".join(out), "diagrams", "flow", src_line, b["line"])

    def render_chain(self, b: dict, src_line: str = None) -> str:
        spec = self._json_block(b, "chain")
        if spec is None:
            return '<div class="miss">chain JSON 解析失败(第 %s 行)</div>' % b["line"]
        cols = spec.get("columns") or []
        if len(cols) < 2:
            self.err("chain 至少两列", b["line"])
        links = spec.get("links") or []
        tmpl = []
        for k in range(len(cols)):
            tmpl.append("minmax(0,1fr)")
            if k < len(cols) - 1:
                tmpl.append("%dpx" % int(spec.get("gap", 74)))
        out = ['<div class="chain" style="grid-template-columns:%s">' % " ".join(tmpl)]
        for k, c in enumerate(cols):
            me = " me" if c.get("me") or c.get("strong") else ""
            out.append('<div class="ccol%s"><div class="chead">%s</div><div class="cnodes">' % (me, inline(str(c.get("name", "")))))
            for nd in c.get("nodes") or []:
                cls = "cnode"
                for f in ("strong", "hot", "muted"):
                    if nd.get(f):
                        cls += " " + f
                h = '<div class="%s"><div class="lb">%s</div>' % (cls, inline(str(nd.get("label", ""))))
                if nd.get("sub"):
                    h += '<div class="sb">%s</div>' % inline(str(nd["sub"]))
                if nd.get("note"):
                    h += '<div class="nt">%s</div>' % inline(str(nd["note"]))
                out.append(h + "</div>")
            out.append("</div></div>")
            if k < len(cols) - 1:
                lk = links[k] if k < len(links) else ""
                fwd, back = (lk.get("fwd", ""), lk.get("back", "")) if isinstance(lk, dict) else (lk, "")
                a = ['<div class="carrow">']
                if fwd:
                    a.append('<div class="lk">%s</div>' % inline(str(fwd)))
                a.append('<div class="ln"></div>')
                if back:
                    a.append('<div class="ln back"></div><div class="lk back">%s</div>' % inline(str(back)))
                a.append("</div>")
                out.append("".join(a))
        out.append("</div>")
        lg = spec.get("legend", True)   # false 隐藏;字符串 = 自定义图例(虚线不是钱时用)
        if lg and any(isinstance(lk, dict) and lk.get("back") for lk in links):
            out.append('<div class="flow-legend">%s</div>' % (inline(lg) if isinstance(lg, str) else "实线箭头 = 货 / 服务流向；绿色虚线 = 钱的流向"))
        return self._fig_wrap("chainfig", spec, "".join(out), "diagrams", "chain", src_line, b["line"])

    def render_lineup(self, b: dict, src_line: str = None) -> str:
        """产品谱系:多张官方 / 研报实物图按功率段或容量排成一张图(设计规格 §3「全型号按功率段或容量排列,合成一张也算 1 张」)。"""
        spec = self._json_block(b, "lineup")
        if spec is None:
            return '<div class="miss">lineup JSON 解析失败(第 %s 行)</div>' % b["line"]
        items = spec.get("items") or []
        if not items:
            self.err("lineup 没有 items", b["line"])
        cols = max(1, int(spec.get("cols") or min(4, max(2, len(items)))))
        ih = spec.get("img_height")
        style = "--c:%d" % cols + (";--ih:%dpx" % ih if isinstance(ih, (int, float)) and 60 <= ih <= 400 else "")
        # 按 group 连续分组;各组并排流动(组宽 = 条目数 / cols),组头下划线横跨本组,组内超过 cols 个自动换行
        groups = []
        for it in items:
            g = it.get("group") or ""
            if not groups or groups[-1][0] != g:
                groups.append([g, bool(it.get("group_hot")), []])
            groups[-1][2].append(it)
        out = ['<div class="lineup c%d" style="%s">' % (cols, style)]
        for g, ghot, its in groups:
            n = min(len(its), cols)
            out.append('<div class="lu-g" style="--n:%d">' % n)
            if g:
                out.append('<div class="lu-grp%s">%s</div>' % (" hot" if ghot else "", inline(str(g))))
            out.append('<div class="lu-items">')
            for it in its:
                lab = str(it.get("label", ""))
                if it.get("img"):
                    img = self.embed_image(str(it["img"]), plain(lab), b["line"])
                else:
                    img = '<div class="miss">缺图</div>'
                    self.err("lineup 条目「%s」缺 img" % lab, b["line"])
                h = ['<div class="lu-item%s">' % (" hot" if it.get("hot") else ""), img]
                if lab:
                    h.append('<div class="lb">%s</div>' % inline(lab))
                if it.get("sub"):
                    h.append('<div class="sb">%s</div>' % inline(str(it["sub"])))
                h.append("</div>")
                out.append("".join(h))
            out.append("</div></div>")
        out.append("</div>")
        title = spec.get("title") or ""
        if not title:
            self.warn("lineup 缺图题", b["line"])
        src = spec.get("source") or ""
        if src_line:
            src = (src + " " if src else "") + src_line
        if not src:
            self.warn("lineup 缺来源行: %s" % title[:30], b["line"])
        ok_imgs = sum(1 for x in out if '<img ' in x or 'class="svgwrap"' in x)
        if ok_imgs:
            anchor = self._new_fig(title, "images", "product", "产品谱系 " + title)
            if self.cur is not None:
                self.cur["st"]["img_product"] = self.cur["st"].get("img_product", 0) + 1
        else:
            self.miss_seq += 1
            anchor = "miss-%d" % self.miss_seq
        chip = '<span class="tag hi kind">%s</span>' % esc(spec.get("chip") or "产品谱系")
        parts = ['<figure class="shot lineupfig" id="%s"><div class="fig-t">%s%s</div>' % (anchor, chip, inline(title))]
        if spec.get("subtitle"):
            parts.append('<div class="fig-s">%s</div>' % inline(spec["subtitle"]))
        parts.append("".join(out))
        note = spec.get("note") or ""
        if src or note:
            parts.append("<figcaption>%s%s</figcaption>" % (self._src_html(src), ('<span class="fig-note">%s</span>' % inline(note)) if note else ""))
        parts.append("</figure>")
        return "".join(parts)

    def render_timeline(self, b: dict, src_line: str = None) -> str:
        meta, evs = {}, []
        for ln in b["body"].splitlines():
            s = ln.strip()
            if not s:
                continue
            m = re.match(r"^(title|subtitle|source|note)\s*[:：]\s*(.*)$", s, flags=re.I)
            if m and "|" not in s:
                meta[m.group(1).lower()] = m.group(2)
                continue
            cells = [c.strip() for c in s.split("|")]
            yr = cells[0]
            tx = cells[1] if len(cells) > 1 else ""
            flag = cells[2].lower() if len(cells) > 2 else ""
            evs.append('<div class="ev%s"><span class="yr">%s</span> <span class="tx">%s</span></div>' % (" hot" if flag == "hot" else "", inline(yr), inline(tx)))
        if not evs:
            self.err("timeline 为空", b["line"])
        inner = '<div class="tl">%s</div>' % "".join(evs)
        if meta.get("title"):
            if src_line:
                meta["source"] = (meta.get("source", "") + " " + src_line).strip()
            return self._fig_wrap("tlfig", meta, inner, "diagrams", "timeline", None, b["line"])
        if src_line:
            inner += '<div class="srcline">%s</div>' % self._src_html(src_line)
        return inner

    def render_kpis(self, body: str) -> str:
        cards = []
        for ln in body.splitlines():
            if not ln.strip():
                continue
            c = [x.strip() for x in ln.split("|")] + ["", "", ""]
            lab, val, unit, sub = c[0], c[1], c[2], c[3]
            sh = inline(sub)
            sh = re.sub(r"(?<![\w.\-])([+＋][\d.,]+\s*(?:%|pct|个百分点)?)", r'<b class="up">\1</b>', sh)
            sh = re.sub(r"(?<![\w.\-])([−–-][\d.,]+\s*(?:%|pct|个百分点)?)", r'<b class="down">\1</b>', sh)
            cards.append('<div class="kpi"><div class="lab">%s</div><div class="val">%s%s</div>%s</div>' % (
                inline(lab), inline(val), ('<span class="u">%s</span>' % inline(unit)) if unit else "",
                ('<div class="sub">%s</div>' % sh) if sub else ""))
        return '<div class="kpis">%s</div>' % "".join(cards)

    def render_cards(self, body: str) -> str:
        cards = []
        for ln in body.splitlines():
            if not ln.strip():
                continue
            c = [x.strip() for x in ln.split("|", 1)]
            head = c[0]
            txt = c[1] if len(c) > 1 else ""
            m = re.match(r"^([①-⑳]|\d+[.、)]|[A-Z][.、)])\s*(.*)$", head)
            no, h4 = (m.group(1), m.group(2)) if m else ("", head)
            cards.append('<div class="card">%s<h4>%s</h4><p>%s</p></div>' % (('<div class="no">%s</div>' % esc(no)) if no else "", inline(h4), inline(txt)))
        return '<div class="cards">%s</div>' % "".join(cards)

    # ------------------------------------------------------------ 表
    NEUTRAL = {"—", "-", "–", "n.a.", "NA", "N/A", "数据不可得", "不适用", "/", "…", ""}

    def _is_num(self, c: str):
        t = strip_tags(inline(c)).strip()
        t = re.sub(r"〔[^〕]*〕", "", t).strip()
        if t in self.NEUTRAL:
            return None
        if re.fullmatch(r"(?:FY|CY)?(?:19|20)\d{2}(?:\s*年)?(?:[EAH][12]?|Q[1-4]|H[12])?", t):
            return None
        return bool(re.fullmatch(r"[−\-+±~≈约≥≤<>]?\s*[$¥€£]?\s*\d[\d,]*(?:\.\d+)?\s*(?:%|pct|pp|bp|x|倍|‰)?"
                                 r"(?:\s*[A-Za-z/]{0,6}|\s*(?:亿元|万元|元|亿|万|GW|GWh|MW|MWh|kW|kWh|天|人|家|个|台|次|套|年|月|元/W|元/Wh))?"
                                 r"(?:\s*[→~–-]\s*[−\-+]?\d[\d,]*(?:\.\d+)?\s*%?)?", t))

    def render_table(self, b: dict, caption: str = None, src_line: str = None) -> str:
        hdr, rows, align = b["hdr"], b["rows"], b["align"]
        ncol = len(hdr)
        rows = [(r + [""] * ncol)[:ncol] for r in rows]
        cls = []
        for k in range(ncol):
            a = align[k] if k < len(align) else None
            if a == "r":
                cls.append("n")
                continue
            if a == "c":
                cls.append("c")
                continue
            if a == "l" or k == 0:
                cls.append("")
                continue
            vals = [self._is_num(r[k]) for r in rows]
            yes, no = vals.count(True), vals.count(False)
            cls.append("n" if yes and yes >= 0.6 * (yes + no) else "")
        self.tables += 1
        if self.cur is not None:
            self.cur["st"]["tables"] = self.cur["st"].get("tables", 0) + 1
        anchor = "tab-%d" % self.tables
        mt = re.match(r"^\s*表\s*(\d+)-(\d+)", caption or "")
        if mt and ("t%s-%s" % mt.groups()) not in self.anchors:
            anchor = "t%s-%s" % mt.groups()
        self.anchors.add(anchor)
        title = caption or ""
        self.figs.append(dict(anchor=anchor, title=plain(title) or "(无表题)", kind="tables", cls="table", ch=self.cur["title"] if self.cur else ""))
        if not caption:
            self.warn("表格缺表题(表前一行写「表 n　标题」)", b["line"])
        th = "".join('<th%s>%s</th>' % ((' class="%s"' % cls[k]) if cls[k] else "", inline(h)) for k, h in enumerate(hdr))
        body = []
        for r in rows:
            first = plain(r[0])
            tot = bool(re.match(r"^(合计|总计|全球合计|全部合计|总额)", first) or re.search(r"合计$", first))
            body.append('<tr%s>%s</tr>' % (' class="tot"' if tot else "", "".join('<td%s>%s</td>' % ((' class="%s"' % cls[k]) if cls[k] else "", inline(c)) for k, c in enumerate(r))))
        cap = "<caption>%s</caption>" % inline(caption, False) if caption else ""
        tb = '<div class="tbl-wrap"><table>%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (cap, th, "".join(body))
        src = '<div class="srcline">%s</div>' % self._src_html(src_line) if src_line else ""
        return '<div class="tblock" id="%s">%s%s</div>' % (anchor, tb, src)

    # ------------------------------------------------------------ 章节与主流程
    def _start_chapter(self, title: str, cid: str):
        self.cur = {"title": plain(title), "id": cid, "parts": [], "h3": [],
                    "st": {"titles": [], "figs": []}, "group": self.nav_group, "explicit": self.nav_group_explicit,
                    "plain": 0, "plain_top": False, "roadmap": 0, "gl_seen": set(),
                    "is_gloss": bool(GLOSS_CH_RE.search(plain(title)))}
        self.chapters.append(self.cur)

    def emit(self, h: str):
        if self.cur is None:
            self._start_chapter("(页首)", "top")
            self.cur["pre"] = True
        self.cur["parts"].append(h)

    @staticmethod
    def _src_of(b):
        if b and b["k"] == "quote" and b["lines"]:
            first = b["lines"][0].strip()
            if re.match(r"^(来源|资料来源|数据来源)\s*[:：]", first):
                return " ".join(x.strip() for x in b["lines"] if x.strip())
        return None

    @staticmethod
    def _hint_of(b):
        if b and b["k"] == "quote" and b["lines"]:
            first = b["lines"][0].strip()
            if re.match(r"^读图(提示)?\s*[:：]", first):
                return " ".join(x.strip() for x in b["lines"] if x.strip())
        return None

    def render_blocks(self, blocks: list, top: bool = True) -> list:
        out = []
        i = 0
        n = len(blocks)
        while i < n:
            b = blocks[i]
            nxt = blocks[i + 1] if i + 1 < n else None
            k = b["k"]
            h = None
            consumed = 1
            if k == "h":
                lv = b["lv"]
                if lv == 1:
                    self.title = b["text"]
                    self.last_block_kind = "h1"
                    i += 1
                    continue
                if lv == 2:
                    self.ch_no += 1
                    self.sec_no = 0
                    cid = b["id"] or "c%d" % self.ch_no
                    self._start_chapter(b["text"], cid)
                    self.nav.append([2, cid, plain(b["text"]), None])
                    h = '<h2 id="%s">%s</h2>' % (cid, inline(b["text"], False))
                elif lv == 3:
                    self.sec_no += 1
                    ms = re.match(r"^(\d+)[.．](\d+)\s", b["text"])
                    cid = b["id"] or ("s%s-%s" % ms.groups() if ms else "c%d-%d" % (self.ch_no, self.sec_no))
                    txt = plain(b["text"])
                    self.nav.append([3, cid, re.sub(r"^\d+(?:[.．]\d+)*\s*", "", txt), None])
                    if self.cur is not None:
                        self.cur["h3"].append(txt)
                    h = '<h3 id="%s">%s</h3>' % (cid, inline(b["text"], False))
                else:
                    h = "<h4>%s</h4>" % inline(b["text"])
            elif k == "navgrp":
                self.nav_group = b["label"]
                self.nav_group_explicit = True
            elif k == "p":
                if CAPTION_RE.match(b["text"]) and nxt and nxt["k"] == "table":
                    src = self._src_of(blocks[i + 2]) if i + 2 < n else None
                    h = self.render_table(nxt, b["text"], src)
                    consumed = 3 if src else 2
                else:
                    self._prose(b["text"])
                    h = self._gl("<p>%s</p>" % inline(b["text"]))
            elif k == "table":
                src = self._src_of(nxt)
                h = self.render_table(b, None, src)
                consumed = 2 if src else 1
            elif k == "quote":
                h = self.render_quote(b)
                if h and not h.startswith('<div class="srcline"'):
                    h = self._gl(h)
            elif k == "img":
                src = self._src_of(nxt)
                j = i + (2 if src else 1)
                hint = self._hint_of(blocks[j]) if j < n else None
                if hint:
                    b = dict(b, hint=hint)
                h = self.render_img(b, src)
                consumed = (2 if src else 1) + (1 if hint else 0)
            elif k == "list":
                tag = "ol" if b["ordered"] else "ul"
                st0 = b.get("start", 1) if b["ordered"] else 1
                for x in b["items"]:
                    self._prose(x)
                h = self._gl("<%s%s>%s</%s>" % (tag, (' start="%d"' % st0) if st0 != 1 else "", "".join("<li>%s</li>" % inline(x) for x in b["items"]), tag))
            elif k == "hr":
                h = "<hr>"
            elif k == "rawhtml":
                raw = re.sub(r"<script[\s\S]*?</script>", "", b["html"], flags=re.I)
                h = raw
            elif k == "box":
                cls = b["cls"]
                if cls not in ("two-up", "three-up", "cards", "half"):
                    self.warn(":::%s 未知容器,按普通块渲染" % cls, b["line"])
                inner = self.render_blocks(b["kids"], top=False)
                nk = sum(1 for x in b["kids"] if x["k"] in ("fence", "img"))
                if cls == "two-up" and nk not in (2,):
                    self.warn(":::two-up 里有 %d 张图(应为 2)" % nk, b["line"])
                if cls == "three-up" and nk not in (3,):
                    self.warn(":::three-up 里有 %d 张图(应为 3)" % nk, b["line"])
                h = '<div class="%s">%s</div>' % (esc(cls), "".join(inner))
            elif k == "fence":
                lang = b["lang"]
                src = self._src_of(nxt)
                if lang == "chart":
                    h = self.render_chart(b, src)
                    consumed = 2 if src else 1
                elif lang in ("kpis", "kpi"):
                    h = self.render_kpis(b["body"])
                elif lang == "timeline":
                    h = self.render_timeline(b, src)
                    consumed = 2 if src else 1
                elif lang == "flow":
                    h = self.render_flow(b, src)
                    consumed = 2 if src else 1
                elif lang in ("chain", "structure"):
                    h = self.render_chain(b, src)
                    consumed = 2 if src else 1
                elif lang in ("lineup", "gallery"):
                    h = self.render_lineup(b, src)
                    consumed = 2 if src else 1
                elif lang == "cards":
                    for ln in b["body"].splitlines():
                        self._prose(ln)
                    h = self._gl(self.render_cards(b["body"]))
                elif lang == "roadmap":
                    h = self.render_roadmap(b, src)
                    consumed = 2 if src else 1
                elif lang == "glossary":
                    h = self.render_glossary(b)
                elif lang == "footer":
                    fb, _ = parse_blocks(b["body"].splitlines())
                    self.footer_html = "".join("<p>%s</p>" % inline(x["text"]) for x in fb if x["k"] == "p")
                elif lang == "meta":
                    self.meta_html = "".join("<p>%s</p>" % inline(x) for x in b["body"].splitlines() if x.strip())
                elif lang in ("html", "raw"):
                    h = re.sub(r"<script[\s\S]*?</script>", "", b["body"], flags=re.I)
                else:
                    h = '<pre class="code">%s</pre>' % esc(b["body"])
            if h is not None:
                if top:
                    self.emit(h)
                else:
                    out.append(h)
            self.last_block_kind = k if k != "h" else "h%d" % b["lv"]
            i += consumed
        return out

    def render_quote(self, b: dict) -> str:
        lines = b["lines"]
        first = lines[0].strip() if lines else ""
        m = re.match(r"^\[!(\w+)\]\s*(.*)$", first)
        qtype = m.group(1).lower() if m else None
        rest = ([m.group(2)] if m and m.group(2) else []) + lines[1:] if m else lines
        paras, buf = [], []
        for x in rest:
            if x.strip():
                buf.append(x.strip())
            elif buf:
                paras.append(" ".join(buf) if not all(re.search(r"[一-鿿]$", y) for y in buf[:-1]) else "".join(buf))
                buf = []
        if buf:
            paras.append(" ".join(buf) if not all(re.search(r"[一-鿿]$", y) for y in buf[:-1]) else "".join(buf))
        if qtype == "meta" or (qtype is None and self.last_block_kind == "h1" and not self.meta_html):
            ps = []
            for x in rest:
                if not x.strip():
                    continue
                t0 = inline(x.strip())
                t0 = re.sub(r"^([^<：:]{1,6})[：:]", r'<b class="ml">\1</b>', t0)
                ps.append("<p>%s</p>" % t0)
            self.meta_html = "".join(ps)
            return None
        if qtype is None:
            if self._src_of(b):
                return '<div class="srcline">%s</div>' % self._src_html(" ".join(paras))
            for p in paras:
                self._prose(p)
            return '<div class="note info">%s</div>' % "".join("<p>%s</p>" % inline(p) for p in paras)
        if not self._hint_of(b):
            for p in paras:
                self._prose(p)
        if qtype in ("plain", "analogy", "example", "eg"):
            # 页面上不写「白话」「打个比方」这类标签:块类型只用于排版和验收
            cls = {"plain": "plain", "analogy": "plain an", "example": "plain eg", "eg": "plain eg"}[qtype]
            if self.cur is not None:
                self.cur["plain"] += 1
                if not self.cur["h3"]:
                    self.cur["plain_top"] = True
                if qtype == "analogy":
                    self.cur["has_analogy"] = True
                if qtype in ("example", "eg"):
                    self.cur["has_eg"] = True
            ps = []
            for j, p in enumerate(paras):
                t = inline(p)
                if j == 0:
                    t = re.sub(r"^([^<:：。]{1,10}[:：])", r'<span class="nh">\1</span>', t)
                ps.append("<p>%s</p>" % t)
            return '<div class="%s">%s</div>' % (cls, "".join(ps))
        if qtype == "lead":
            if len(paras) == 1:
                return '<p class="lead">%s</p>' % inline(paras[0])
            return '<div class="lead">%s</div>' % "".join("<p>%s</p>" % inline(p) for p in paras)
        ncls = {"note": "note", "warn": "note", "info": "note info", "good": "note good", "bad": "note bad", "tip": "note info"}.get(qtype)
        if not ncls:
            self.warn("未知提示块类型 [!%s],按 note 渲染" % qtype, b["line"])
            ncls = "note"
        ps = []
        for j, p in enumerate(paras):
            t = inline(p)
            if j == 0:
                t = re.sub(r"^([^<:：。]{1,14}[:：])", r'<span class="nh">\1</span>', t)
            ps.append("<p>%s</p>" % t)
        return '<div class="%s">%s</div>' % (ncls, "".join(ps))

    # ------------------------------------------------------------ 基金经理版:白话、路线图、术语
    def _prose(self, text: str):
        if self.cur is not None and not self.cur.get("is_gloss") and text and text.strip():
            self.pm_prose.append((self.cur["id"], text))

    def load_glossary(self, md: str):
        """全文预扫 glossary 块:正文里的术语在词典之前出现也能加悬停释义。"""
        seen = set()
        for m in GLOSS_FENCE.finditer(md):
            for e in parse_glossary(m.group(1)):
                if e["term"] in seen:
                    continue
                seen.add(e["term"])
                e["id"] = "gl-%d" % (len(self.gloss) + 1)
                self.gloss.append(e)
        al = sorted(((a, e) for e in self.gloss for a in e["aliases"] if len(a) >= 2), key=lambda x: -len(x[0]))
        self.gloss_alias = {cjk_punct(html.escape(a, quote=False)): e for a, e in al}
        pats = []
        for a in self.gloss_alias:
            ea = re.escape(a)
            if re.match(r"^[A-Za-z0-9]", a):
                ea = r"(?<![A-Za-z0-9])" + ea
            if re.search(r"[A-Za-z0-9]$", a):
                ea += r"(?![A-Za-z0-9])"
            pats.append(ea)
        self.gloss_re = re.compile("|".join(pats)) if pats else None

    def _gl(self, h: str) -> str:
        """本章第一次出现的词典术语加虚线下划线与悬停释义;不进链接、代码、标签属性。"""
        if not self.gloss_re or self.cur is None or self.cur.get("is_gloss") or not h:
            return h
        seen = self.cur["gl_seen"]
        parts = re.split(r"(<[^>]+>)", h)
        stack = []   # 每层标签是否属于「不加释义」区:链接、代码、徽标、读者标签、提示块小标题

        def _one(m):
            e = self.gloss_alias.get(m.group(0))
            if not e or e["id"] in seen:
                return m.group(0)
            seen.add(e["id"])
            tip = plain(e["expl"]) + (("　可以理解成：" + plain(e["ana"])) if e.get("ana") else "")
            return '<span class="gl" tabindex="0" data-gl="%s" data-tip="%s">%s</span>' % (e["id"], esc(tip), m.group(0))
        for i, seg in enumerate(parts):
            if seg.startswith("<"):
                m = re.match(r"<(/?)([A-Za-z][A-Za-z0-9]*)([^>]*)>", seg)
                if not m or seg.endswith("/>") or m.group(2).lower() in ("br", "img", "hr", "input", "meta"):
                    continue
                if m.group(1):
                    if stack:
                        stack.pop()
                else:
                    tag = m.group(2).lower()
                    stack.append(tag in ("a", "code", "caption", "th") or bool(
                        tag == "span" and re.search(r'class="(plab|rl|gl|tag|nh)\b', m.group(3))))
                continue
            if any(stack) or not seg.strip():
                continue
            parts[i] = self.gloss_re.sub(_one, seg)
        return "".join(parts)

    def render_roadmap(self, b: dict, src_line: str = None) -> str:
        spec = self._json_block(b, "roadmap")
        if spec is None:
            return '<div class="miss">roadmap JSON 解析失败(第 %s 行)</div>' % b["line"]
        stages = spec.get("stages") or []
        if len(stages) < 2:
            self.err("roadmap 至少要 2 个阶段", b["line"])
        keys = ["solves", "cost", "who"]
        rows = spec.get("rows") or ["解决了什么", "代价", "谁受益谁受损"]
        rk = [(r[0], r[1]) if isinstance(r, (list, tuple)) else (r, keys[k] if k < len(keys) else "r%d" % k) for k, r in enumerate(rows)]
        out = ['<div class="rm" style="--n:%d">' % max(1, len(stages))]
        for k, st in enumerate(stages):
            cls = "rstage" + "".join(" " + f for f in ("now", "future", "hot") if st.get(f)) + (" last" if k == len(stages) - 1 else "")
            badge = '<span class="rnow">今天在这</span>' if st.get("now") else ('<span class="rfut">还没到</span>' if st.get("future") else "")
            h = ['<div class="%s">' % cls, '<div class="rera">%s%s</div>' % (inline(str(st.get("era", ""))), badge),
                 '<div class="rname">%s</div>' % inline(str(st.get("name", "")))]
            if st.get("gist"):
                self._prose(str(st["gist"]))
                h.append('<div class="rgist">%s</div>' % inline(str(st["gist"])))
            for lab, key in rk:
                if st.get(key):
                    self._prose(str(st[key]))
                    h.append('<div class="rrow"><span class="rl2">%s</span>%s</div>' % (esc(lab), inline(str(st[key]))))
            h.append("</div>")
            out.append("".join(h))
        out.append("</div>")
        fork = spec.get("fork") or {}
        if fork.get("options"):
            fo = ['<div class="rfork"><div class="rfl">%s</div><div class="rfo">' % inline(str(fork.get("label") or "下一步的分岔"))]
            for o in fork["options"]:
                for key in ("if", "signal"):
                    if o.get(key):
                        self._prose(str(o[key]))
                fo.append('<div class="ropt"><div class="rname">%s</div>%s%s</div>' % (
                    inline(str(o.get("name", ""))),
                    ('<div class="rrow"><span class="rl2">赢的条件</span>%s</div>' % inline(str(o["if"]))) if o.get("if") else "",
                    ('<div class="rrow"><span class="rl2">看什么信号</span>%s</div>' % inline(str(o["signal"]))) if o.get("signal") else ""))
            fo.append("</div></div>")
            out.append("".join(fo))
        if self.cur is not None:
            self.cur["roadmap"] += 1
        return self._fig_wrap("rmfig", spec, "".join(out), "diagrams", "roadmap", src_line, b["line"])

    def render_glossary(self, b: dict) -> str:
        es = parse_glossary(b["body"])
        if not es:
            self.err("glossary 为空", b["line"])
        ids = {e["term"]: e["id"] for e in self.gloss}
        rows = []
        for e in es:
            gid = ids.get(e["term"], "")
            if gid in self.gloss_ids_used:
                gid = ""
            self.gloss_ids_used.add(gid)
            if not e["expl"]:
                self.warn("术语「%s」缺白话解释" % e["term"], b["line"])
            rows.append('<tr%s><td class="glt">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                (' id="%s"' % gid) if gid else "", inline(e["term"], False), inline(e["expl"]),
                inline(e["ana"]) if e["ana"] else "—", inline(e["why"]) if e["why"] else "—"))
        self.glossary_rows += len(es)
        head = "".join("<th>%s</th>" % x for x in ("术语", "是什么", "可以理解成", "对投资意味着什么"))
        return '<div class="tblock gloss"><div class="tbl-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div></div>' % (
            head, "".join(rows))

    def pm_stats(self, chapters: list) -> dict:
        """基金经理版指标:零章、技术白话章、业务章章首白话、词典、英文缩写首现是否有白话解释。"""
        allow = ACR_ALLOW | set(self.pm_allow)
        gl_alias = [a for e in self.gloss for a in e["aliases"]]
        first, per_ch = {}, {}
        for cid, t in self.pm_prose:
            tt = re.sub(r"\]\([^)]*\)", "]", t)
            tt = plain(re.sub(r"〔[^〕]*〕|\{\{\w+:|\}\}", "", tt))
            for m in ACR_RE.finditer(tt):
                tok = m.group(1)
                base = re.sub(r"[\d.+\-]+[A-Za-z]?$", "", tok) or tok
                if tok in allow or base in allow:
                    continue
                lst = per_ch.setdefault(cid, [])
                if tok not in lst:
                    lst.append(tok)
                if tok not in first:
                    first[tok] = (tt, m.start(), m.end())
        unexpl = []
        for tok, (tt, a, z) in first.items():
            if tok in gl_alias or any(tok in x for x in gl_alias):
                continue
            after, before = tt[z:z + 60], tt[max(0, a - 12):a]
            if re.match(r"\s*[（(][^）)]{0,50}?[一-鿿]{2,}", after):
                continue
            if re.match(r"\s*[，,]?\s*(即|也就是|是指|指的是|意思是|中文叫|全称|就是)", after):
                continue
            if re.search(r"(简称|称为|叫做|英文缩写|英文叫|缩写为)\s*$", before):
                continue
            unexpl.append(tok)
        real = [c for c in self.chapters if not c.get("pre")]
        ch0 = next((c for c in real if CH0_RE.search(c["title"])), None)
        tech = next((c for c in real if c is not ch0 and TECH_RE.search(c["title"])), None)

        def cmp_of(c):   # 有「和同类 / 替代方案比」的节,且本章至少一张表
            return any(CMP_RE.search(h) for h in c["h3"]) and c["st"].get("tables", 0) >= 1
        d0 = None
        if ch0 is not None:
            txt = strip_tags(re.sub(r'<details class="dv">[\s\S]*?</details>', "", "".join(ch0["parts"])))
            d0 = dict(title=ch0["title"], first=(real[0] is ch0), cjk=cjk_count(txt), plain=ch0["plain"],
                      has_analogy=bool(ch0.get("has_analogy") or any(ANALOGY_H3.search(h) for h in ch0["h3"]) or "打个比方" in txt),
                      has_example=bool(ch0.get("has_eg") or any(EXAMPLE_H3.search(h) for h in ch0["h3"]) or "举个例子" in txt),
                      compare=cmp_of(ch0), acronyms=per_ch.get(ch0["id"], []))
        leaks = [plain(t)[:24] for _cid, t in self.pm_prose if LABEL_LEAK.match(t)]
        leaks += ["标题:" + c["title"] for c in real if "白话" in c["title"]]
        leaks += ["标题:" + h for c in real for h in c["h3"] if "白话" in h]
        return dict(
            ch0=d0, label_leaks=leaks,
            tech=(dict(title=tech["title"], roadmaps=tech["roadmap"], compare=cmp_of(tech)) if tech is not None else None),
            roadmaps=sum(c["roadmap"] for c in real),
            business_no_plain=[c["title"] for c, x in zip(real, chapters) if x["business"] and not c["plain_top"]],
            plain_blocks=sum(c["plain"] for c in real),
            glossary_terms=len(self.gloss), glossary_rows=self.glossary_rows,
            acronyms=len(first), unexplained=unexpl, gloss_marked=sum(len(c["gl_seen"]) for c in real))

    # ------------------------------------------------------------ 组装
    def _auto_groups(self):
        chs = [c for c in self.chapters if not c.get("pre")]
        if any(c["explicit"] for c in chs):
            return
        biz = [k for k, c in enumerate(chs) if any(re.search(r"行业规模|竞争格局|核心竞争|具体产品", h) for h in c["h3"])]
        if not biz:
            return
        first, last = biz[0], biz[-1]
        nbiz = len(biz)
        lab = ("%s大主业" % ("两" if nbiz == 2 else cn_num(nbiz))) if nbiz > 1 else "主要业务"
        for k, c in enumerate(chs):
            if k < first:
                c["group"] = None
            elif k <= last:
                c["group"] = lab
            elif re.search(r"来源|口径|附录|声明", c["title"]):
                c["group"] = "附录"
            else:
                c["group"] = "经营与跟踪"

    def brand(self):
        t = plain(self.title)
        m = re.match(r"^(.+?)\s*[(（]\s*([^()（）]+?)\s*[)）]\s*(.*)$", t)
        if m:
            return "%s %s" % (m.group(1), m.group(2)), (m.group(3) or "业务认知")
        return t, ""

    def report_date(self) -> str:
        if self.date_arg:
            return self.date_arg
        txt = strip_tags(self.meta_html)
        m = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", txt)
        if m:
            return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))
        return _dt.datetime.now().strftime("%Y-%m-%d")

    def nav_html(self) -> str:
        self._auto_groups()
        ch_by_id = {c["id"]: c for c in self.chapters}
        b1, b2 = self.brand()
        out = ['<nav class="toc" aria-label="目录"><div class="brand">%s%s</div>' % (esc(b1), ("<br>" + esc(b2)) if b2 else ""),
               '<div class="date">%s · 买方内部研究</div>' % esc(self.report_date())]
        grp = None
        for lv, cid, txt, _ in self.nav:
            if lv == 2:
                c = ch_by_id.get(cid)
                g = c["group"] if c else None
                if g and g != grp:
                    out.append('<div class="grp">%s</div>' % esc(g))
                grp = g
                st = c["st"] if c else {}
                nf = st.get("charts", 0) + st.get("images", 0) + st.get("diagrams", 0)
                cnt = '<span class="cnt">%d 图</span>' % nf if nf else ""
                out.append('<a href="#%s">%s%s</a>' % (cid, cnt, esc(txt)))
            else:
                out.append('<a href="#%s" class="l2">%s</a>' % (cid, esc(txt)))
        if self.fig_index and self.figs:
            if grp != "附录":
                out.append('<div class="grp">附录</div>')
            out.append('<a href="#figidx">图表目录</a>')
        out.append("</nav>")
        return "".join(out)

    def figidx_html(self) -> str:
        nfig = sum(1 for f in self.figs if f["kind"] != "tables")
        ntab = sum(1 for f in self.figs if f["kind"] == "tables")
        lab = {"charts": ("交互图", "ch"), "images": ("原图", "im"), "diagrams": ("示意", "dg"), "tables": ("表", "tb")}
        imgl = {"ref": "研报原图", "official": "官方图", "product": "实物图", "diagram": "示意图", "other": "图片"}
        dgl = {"flow": "流程图", "chain": "结构图", "timeline": "时间轴", "roadmap": "路线图"}
        parts = ['<h2 id="figidx">图表目录</h2>',
                 '<details class="figidx"><summary>全卡 %d 张图、%d 张表（点开看清单，点条目跳转）</summary>' % (nfig, ntab)]
        cur = None
        buf = []
        for f in self.figs:
            if f["ch"] != cur:
                if buf:
                    parts.append("<ol>%s</ol>" % "".join(buf))
                    buf = []
                cur = f["ch"]
                parts.append('<div class="fgch">%s</div>' % esc(cur or "页首"))
            k, c = lab[f["kind"]]
            if f["kind"] == "images":
                k = imgl.get(f["cls"], "图片")
            elif f["kind"] == "diagrams":
                k = dgl.get(f["cls"], "示意")
            buf.append('<li><span class="k %s">%s</span><a href="#%s">%s</a></li>' % (c, k, f["anchor"], esc(f["title"])))
        if buf:
            parts.append("<ol>%s</ol>" % "".join(buf))
        parts.append("</details>")
        return "".join(parts)

    def footer(self) -> str:
        t = plain(self.title)
        if self.footer_html:
            return '<div class="footer">%s</div>' % self.footer_html
        body = (
            "<p>本卡依据公司定期报告与公告、授权券商研究及第三方机构数据整理,供内部业务研究使用;"
            "<b>不含估值结论、目标价与投资评级</b>,不构成任何证券的买卖建议。</p>"
            "<p>交互图按底稿数值重绘(ECharts 5.5.1 内联,离线可开),每张图下「表格视图」可逐项核对;"
            "标「研报原图」「官方图」「招股书」的截图直接取自原文件并注明页码,对外分发前请移除研报原图。</p>")
        return '<div class="footer"><p><b>%s</b>　·　%s　·　买方内部研究</p>%s</div>' % (esc(t), esc(self.report_date()), body)

    def stats(self, html_doc: str, main_html: str) -> dict:
        def cnt(kind, cls=None):
            return sum(1 for f in self.figs if f["kind"] == kind and (cls is None or f["cls"] == cls))
        prose_src = re.sub(r'<details class="dv">[\s\S]*?</details>', "", main_html)
        prose_src = re.sub(r"<(script|svg)[\s\S]*?</\1>", "", prose_src)
        prose_src = prose_src.split('<h2 id="figidx">')[0]
        body_txt = strip_tags(prose_src)
        charts = cnt("charts")
        images = cnt("images")
        diagrams = cnt("diagrams")
        chapters = []
        for c in self.chapters:
            if c.get("pre"):
                continue
            st = c["st"]
            biz = any(re.search(r"行业规模|竞争格局|核心竞争|具体产品", h) for h in c["h3"])
            miss = []
            if biz:
                for name, pat, _hard, kinds in MUST_HAVE:
                    if not any(k in kinds and re.search(pat, t) for k, _c, t in st["figs"]):
                        miss.append(name)
            chtxt = strip_tags(re.sub(r'<details class="dv">[\s\S]*?</details>', "", "".join(c["parts"])))
            chapters.append(dict(title=c["title"], business=biz, charts=st.get("charts", 0), images=st.get("images", 0),
                                 diagrams=st.get("diagrams", 0), tables=st.get("tables", 0),
                                 figures=st.get("charts", 0) + st.get("images", 0) + st.get("diagrams", 0),
                                 flows=sum(1 for k, c, _t in st["figs"] if c == "flow"),
                                 cjk=cjk_count(chtxt), missing=miss))
        ext = re.findall(r'<(?:script|link|img|iframe|source|video|audio)\b[^>]*\b(?:src|href)="(https?:)?//[^"]*"', html_doc)
        ext += re.findall(r"url\(\s*['\"]?https?://", html_doc) + re.findall(r"@import", html_doc)
        return dict(
            generator=GENERATOR, title=plain(self.title), date=self.report_date(),
            figures_total=charts + images + diagrams, charts=charts,
            visuals_non_chart=images + diagrams,
            images=dict(total=images, ref=cnt("images", "ref"), official=cnt("images", "official"),
                        product=cnt("images", "product"), diagram=cnt("images", "diagram"), other=cnt("images", "other")),
            diagrams=dict(total=diagrams, flow=cnt("diagrams", "flow"), chain=cnt("diagrams", "chain"), timeline=cnt("diagrams", "timeline")),
            tables=self.tables, cjk_chars=cjk_count(body_txt), chapters=chapters,
            cjk_glossary=sum(c["cjk"] for c, x in zip(chapters, [c for c in self.chapters if not c.get("pre")]) if x.get("is_gloss")),
            xrefs=getattr(self, "xref_ok", 0), xref_missing=sorted(set(getattr(self, "xref_bad", []))),
            halfwidth_next_to_cjk=len(re.findall(r"[\u4e00-\u9fff][,;:()]|[,;:()][\u4e00-\u9fff]", body_txt)),
            fullwidth_punct=len(re.findall(r"[，；：（）]", body_txt)),
            html_bytes=len(html_doc.encode("utf-8")), external_refs=len(ext),
            pm=dict(self.pm_stats(chapters), todo=len(re.findall(r"\bTODO\b", body_txt))),
            errors=self.errors, warnings=self.warns)

    def build(self, md: str):
        self.load_glossary(md)
        blocks, _ = parse_blocks(md.splitlines())
        self.render_blocks(blocks)
        if not self.title:
            self.warn("没有一级标题 #")
            self.title = self.md_path.stem
        main = ["<h1>%s</h1>" % inline(self.title)]
        if self.meta_html:
            main.append('<div class="meta">%s</div>' % self.meta_html)
        for c in self.chapters:
            main.extend(c["parts"])
        if self.fig_index and self.figs:
            main.append(self.figidx_html())
        main.append(self.footer())
        main_html = "\n".join(main)
        ids = set(re.findall(r'\bid="([^"]+)"', main_html))
        self.xref_ok, self.xref_bad = 0, []

        def _fix(m):
            if m.group(1) in ids:
                self.xref_ok += 1
                return m.group(0)
            self.xref_bad.append(m.group(2))
            return m.group(2)
        main_html = re.sub(r'<a class="xref" href="#([^"]+)">(.*?)</a>', _fix, main_html)
        if self.xref_bad:
            self.warn("交叉引用找不到目标(已还原为纯文本):%s" % "、".join(sorted(set(self.xref_bad))[:30]))
        nav = self.nav_html()
        echarts_js = ECHARTS_PATH.read_text(encoding="utf-8") if self.charts else ""
        if self.charts and not echarts_js:
            self.err("找不到 ECharts: %s" % ECHARTS_PATH)
        specs = json.dumps(self.charts, ensure_ascii=False).replace("</", "<\\/")
        desc = strip_tags(self.meta_html)[:180]
        doc = "\n".join([
            "<!DOCTYPE html>", '<html lang="zh-CN">', "<head>", '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<meta name="generator" content="%s">' % GENERATOR,
            '<meta name="description" content="%s">' % esc(desc),
            "<title>%s</title>" % esc(plain(self.title)),
            "<style>%s</style>" % CSS, "</head>", "<body>",
            '<div class="layout">', nav, "<main>", main_html, "</main>", "</div>",
            '<button id="tocbtn" type="button" aria-label="打开目录">目录</button>',
            '<button id="backbtn" type="button" aria-label="返回原处">↩ 返回原处</button>',
            '<div id="lb" role="dialog" aria-label="图片放大"><img alt=""></div>',
            '<div id="gltip" role="tooltip"></div>' if self.gloss else "",
            '<script type="application/json" id="chart-specs">%s</script>' % specs,
            ("<script>\n%s\n</script>" % echarts_js) if echarts_js else "",
            "<script>%s</script>" % JS, ("<script>%s</script>" % GL_JS) if self.gloss else "", "</body>", "</html>"])
        return doc, self.stats(doc, main_html)


def gate_check(st: dict, g: dict) -> list:
    fails = []
    if st["figures_total"] < g["figs"]:
        fails.append("图 %d 张 < %d" % (st["figures_total"], g["figs"]))
    if st["charts"] < g["charts"]:
        fails.append("交互图 %d 张 < %d" % (st["charts"], g["charts"]))
    if st["visuals_non_chart"] < g["visuals"]:
        fails.append("原图 / 实物 / 流程 / 示意图 %d 张 < %d" % (st["visuals_non_chart"], g["visuals"]))
    if st["tables"] < g["tables"]:
        fails.append("表 %d 张 < %d" % (st["tables"], g["tables"]))
    cjk = st["cjk_chars"] - st.get("cjk_glossary", 0)   # 术语词典不计入篇幅门槛
    if cjk < g["cjk"]:
        fails.append("汉字 %d < %d%s" % (cjk, g["cjk"], "(已扣除术语词典 %d 字)" % st["cjk_glossary"] if st.get("cjk_glossary") else ""))
    hard = {name for name, _p, h, _k in MUST_HAVE if h}
    for c in st["chapters"]:
        if c["business"]:
            lack = [m for m in c["missing"] if m in hard]
            if lack:
                fails.append("「%s」缺 %s" % (c["title"], "、".join(lack)))
            if c["figures"] < 12:
                fails.append("「%s」图 %d 张 < 12" % (c["title"], c["figures"]))
    return fails


def pm_check(st: dict, g: dict) -> list:
    """基金经理版验收(DESIGN_pm.md §5)。"""
    pm = st["pm"]
    fails = []
    d0 = pm["ch0"]
    if not d0:
        fails.append("缺零章「一分钟看懂」(章题含 一分钟看懂 / 大白话 / 白话速览)")
    else:
        if not d0["first"]:
            fails.append("零章「%s」不在最前" % d0["title"])
        if not (g["ch0_min"] <= d0["cjk"] <= g["ch0_max"]):
            fails.append("零章汉字 %d 不在 %d–%d" % (d0["cjk"], g["ch0_min"], g["ch0_max"]))
        if not d0["has_analogy"]:
            fails.append("零章缺类比([!analogy] 块,或节题含「像什么」)")
        if not d0["has_example"]:
            fails.append("零章缺真实例子([!example] 块,或节题含「例子 / 案例」;具体客户或场景的前后对比)")
        if not d0["compare"]:
            fails.append("零章缺「和同类 / 替代方案有什么不同」对比节(节题含 不同 / 区别 / 对比 / 差在哪)与对比表")
        if len(d0["acronyms"]) > g["ch0_max_acr"]:
            fails.append("零章英文缩写 %d 个 > %d(%s)" % (len(d0["acronyms"]), g["ch0_max_acr"], "、".join(d0["acronyms"][:10])))
    if g["tech"]:
        if not pm["tech"]:
            fails.append("缺技术章(章题含 是怎么回事 / 往哪走 / 技术路径 / 技术演进)")
        else:
            if pm["tech"]["roadmaps"] < 1:
                fails.append("技术章缺路线图(roadmap 块)")
            if not pm["tech"]["compare"]:
                fails.append("技术章缺「和替代方案比差在哪」对比节(节题含 不同 / 区别 / 对比 / 差在哪)与对比表")
    for t in pm["business_no_plain"]:
        fails.append("「%s」第一个 ### 前缺通俗解释块([!plain] / [!analogy] / [!example])" % t)
    if pm.get("todo"):
        fails.append("正文残留 TODO %d 处(模板占位没写完)" % pm["todo"])
    if pm.get("label_leaks"):
        fails.append("页面上出现写作标签 %d 处(段首「白话:」「打个比方:」或标题含「白话」;改成自然句或小标题):%s" % (
            len(pm["label_leaks"]), "、".join(pm["label_leaks"][:6])))
    if pm["glossary_terms"] < g["min_glossary"]:
        fails.append("术语词典 %d 条 < %d" % (pm["glossary_terms"], g["min_glossary"]))
    if len(pm["unexplained"]) > g["max_unexplained"]:
        fails.append("首现没有白话解释的英文缩写 %d 个 > %d(%s)" % (
            len(pm["unexplained"]), g["max_unexplained"], "、".join(pm["unexplained"][:15])))
    return fails


def print_summary(st: dict, out: Path, fails):
    w = sys.stderr.write
    w("渲染完成 → %s (%.1f MB)\n" % (out, st["html_bytes"] / 1e6))
    w("图 %d 张 = 交互图 %d + 原图/实物 %d + 自绘流程/结构/时间轴/路线图 %d;表 %d;汉字 %d%s;外部引用 %d\n" % (
        st["figures_total"], st["charts"], st["images"]["total"], st["diagrams"]["total"], st["tables"], st["cjk_chars"],
        (",其中术语词典 %d(不计入篇幅门槛)" % st["cjk_glossary"]) if st.get("cjk_glossary") else "", st["external_refs"]))
    w("分章:\n")
    for c in st["chapters"]:
        w("  %-22s 图 %2d(交互 %d / 原图 %d / 示意 %d,其中流程 %d) 表 %d 汉字 %5d%s\n" % (
            c["title"][:22], c["figures"], c["charts"], c["images"], c["diagrams"], c.get("flows", 0), c["tables"], c["cjk"],
            ("  缺:" + "、".join(c["missing"])) if c["missing"] else ""))
    if st.get("copy_check"):
        cc = st["copy_check"]
        w("照抄检查:%d 句,命中 %d 句\n" % (cc["sentences"], len(cc["hits"])))
        for hh in cc["hits"][:40]:
            w("  照抄? 重合率 %.2f 公共片段 %d 字:%s\n" % (hh[0], hh[1], hh[2]))
        for hh in cc.get("review", [])[:40]:
            w("  人工复看(原始重合率 %.2f):%s\n" % (hh[0], hh[2]))
    pm = st.get("pm")
    if pm:
        d0 = pm["ch0"]
        w("基金经理版:零章 %s;技术章 %s;通俗解释块 %d;路线图 %d;词典 %d 条(正文悬停释义 %d 处);英文缩写 %d 个,首现无解释 %d 个%s\n" % (
            ("汉字 %d、解释块 %d、缩写 %d、对比%s" % (d0["cjk"], d0["plain"], len(d0["acronyms"]), "有" if d0["compare"] else "缺")) if d0 else "缺",
            ("路线图 %d、对比%s" % (pm["tech"]["roadmaps"], "有" if pm["tech"]["compare"] else "缺")) if pm["tech"] else "缺", pm["plain_blocks"], pm["roadmaps"],
            pm["glossary_terms"], pm["gloss_marked"], pm["acronyms"], len(pm["unexplained"]),
            ("(" + "、".join(pm["unexplained"][:20]) + ")") if pm["unexplained"] else ""))
        if pm["business_no_plain"]:
            w("  章首缺通俗解释块:%s\n" % "、".join(pm["business_no_plain"]))
    w("交叉引用 %d 处(失效 %d);与汉字相邻的半角标点 %d 处,全角 %d 处\n" % (st.get("xrefs", 0), len(st.get("xref_missing", [])), st.get("halfwidth_next_to_cjk", 0), st.get("fullwidth_punct", 0)))
    for e in st["errors"]:
        w("错误: %s\n" % e)
    for x in st["warnings"][:60]:
        w("提示: %s\n" % x)
    if len(st["warnings"]) > 60:
        w("提示: …另有 %d 条\n" % (len(st["warnings"]) - 60))
    if fails is not None:
        w(("验收未过: " + ";".join(fails) + "\n") if fails else "验收通过(%s)\n" % st.get("gate_mode", "--gate"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="业务认知卡 v3.2 MD → 单文件 HTML")
    ap.add_argument("md")
    ap.add_argument("--out")
    ap.add_argument("--date")
    ap.add_argument("--stats")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--lax", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--max-px", type=int, default=1600)
    ap.add_argument("--no-fig-index", action="store_true")
    ap.add_argument("--min-figs", type=int, default=GATE_DEFAULT["figs"])
    ap.add_argument("--min-charts", type=int, default=GATE_DEFAULT["charts"])
    ap.add_argument("--min-visuals", type=int, default=GATE_DEFAULT["visuals"])
    ap.add_argument("--min-tables", type=int, default=GATE_DEFAULT["tables"])
    ap.add_argument("--min-cjk", type=int, default=GATE_DEFAULT["cjk"])
    ap.add_argument("--ref", help="参考报告纯文本(照抄检查,--gate 时不达标即失败)")
    ap.add_argument("--ref-bg", default="", help="公司披露等背景语料(逗号分隔),其中出现过的片段不算照抄")
    ap.add_argument("--pm", action="store_true", help="基金经理版验收(DESIGN_pm.md §5)")
    ap.add_argument("--pm-min-glossary", type=int, default=PM_DEFAULT["min_glossary"])
    ap.add_argument("--pm-max-unexplained", type=int, default=PM_DEFAULT["max_unexplained"])
    ap.add_argument("--pm-ch0-min", type=int, default=PM_DEFAULT["ch0_min"])
    ap.add_argument("--pm-ch0-max", type=int, default=PM_DEFAULT["ch0_max"])
    ap.add_argument("--pm-ch0-max-acr", type=int, default=PM_DEFAULT["ch0_max_acr"])
    ap.add_argument("--pm-no-tech", action="store_true", help="本卡不要求技术白话章(消费品等,须用户同意)")
    ap.add_argument("--pm-allow", default="", help="不算术语的英文词(逗号分隔):公司名、代码、读者熟知的产品名")
    a = ap.parse_args(argv)
    md_path = Path(a.md).resolve()
    out = Path(a.out).resolve() if a.out else md_path.with_suffix(".html")
    r = Renderer(md_path, max_px=a.max_px, offline=a.offline, date=a.date, fig_index=not a.no_fig_index)
    r.pm_allow = [x.strip() for x in a.pm_allow.split(",") if x.strip()]
    doc, st = r.build(md_path.read_text(encoding="utf-8"))
    out.write_text(doc, encoding="utf-8")
    if st["external_refs"]:
        st["errors"].append("HTML 里有 %d 处外部资源引用" % st["external_refs"])
    fails = None
    if a.ref:
        from copycheck_v32 import check_html
        hits, nchk = check_html(doc, Path(a.ref).read_text(encoding="utf-8"),
                                [Path(p).read_text(encoding="utf-8", errors="ignore") for p in a.ref_bg.split(",") if p.strip()])
        st["copy_check"] = dict(sentences=nchk, hits=hits, review=getattr(check_html, "warns", []))
    if a.gate:
        fails = gate_check(st, dict(figs=a.min_figs, charts=a.min_charts, visuals=a.min_visuals, tables=a.min_tables, cjk=a.min_cjk))
        if a.ref and st["copy_check"]["hits"]:
            fails.append("与参考报告疑似照抄 %d 句(3 字片段重合率 ≥0.30 或公共片段 ≥12 字)" % len(st["copy_check"]["hits"]))
        st["gate_fails"] = fails
    if a.pm:
        pf = pm_check(st, dict(min_glossary=a.pm_min_glossary, max_unexplained=a.pm_max_unexplained, ch0_min=a.pm_ch0_min,
                               ch0_max=a.pm_ch0_max, ch0_max_acr=a.pm_ch0_max_acr, tech=not a.pm_no_tech))
        fails = (fails or []) + pf
        st["pm_fails"] = pf
    if a.gate or a.pm:
        st["gate_mode"] = " ".join(x for x, on in (("--gate", a.gate), ("--pm", a.pm)) if on)
    if a.stats:
        Path(a.stats).write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    print_summary(st, out, fails)
    if st["errors"] and not a.lax:
        return 2
    if fails:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
