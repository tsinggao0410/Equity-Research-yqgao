#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
draw_bars.py (v2.4) — 研报式柱线图 (自包含 SVG, 黑白灰 + 海军蓝):分组柱 / 堆叠柱 + 可选折线 (右轴),每根柱、每个点标数字。
用在「核心模式深挖」:量 × 价分解、季度收入结构、两套账(GAAP vs 非 GAAP)、每 MW 单价比较、资金缺口。

v2.4:按槽宽出图 (--slot full/half/third), 渲染后 1:1 不缩放;图内只有 15 (类目 / 图例 / 柱顶合计) 与 13 (刻度 / 数值 / 副题 / 脚注) 两个字号;
     标题默认不画 (渲染器的「图 n · 论断句」就是标题), 要独立看图时加 --title。

规格 (JSON):
{
  "title": "产品收入 = 年均客户数 × 单客户年收入",      # 默认不画进图, 写进 MD 的 ![图 · …]
  "subtitle": "客户数千家 (柱, 左轴) · 单客户年产品收入万美元 (线, 右轴)",   # 单位与口径, 画在图顶
  "categories": ["FY22", "FY23", "FY24", "FY25", "FY26"],
  "series": [
    {"name": "年均客户数 (千家)", "values": [5.0, 6.9, 8.6, 10.3, 12.2], "type": "bar"},
    {"name": "单客户年收入 (万美元)", "values": [22.6, 28.2, 30.9, 33.6, 36.7], "type": "line", "axis": "right"}
  ],
  "stacked": false,            # 多个 bar 序列时: true 堆叠 / false 分组
  "digits": 1,                 # 数值标签小数位 (默认自动)
  "plot_h": 300,               # 可选, 绘图区高度 (默认按槽: full 300 / half 250 / third 210)
  "footnote": "来源 …"
}
颜色: 第 1 个柱深海军蓝, 第 2 个中海军蓝, 第 3 个浅, 第 4 个灰;线为深海军蓝带圆点。负值柱向下画。
用法: python draw_bars.py spec.json --out images/xxx.svg [--slot half]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _svgkit import (FS_BODY, FS_SMALL, GREY, INK, LH_BODY, LH_SMALL, LINE, NAVY, PAD, RED,  # noqa: E402
                     chars_for, fmt_num, foot_block, foot_height, foot_lines, head_block, run,
                     slot_width, svg_open, text, text_w, wrap)

BAR_COLORS = [NAVY[1], NAVY[2], NAVY[3], "#c9c9c9", "#9a9a9a"]
LINE_COLORS = [NAVY[0], RED, NAVY[2]]
DEFAULT_PLOT_H = {"full": 300, "half": 250, "third": 210}


def _nice_max(v: float) -> float:
    if v <= 0:
        return 1.0
    import math
    exp = 10 ** math.floor(math.log10(v))
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if v <= m * exp:
            return m * exp
    return 10 * exp


def render(spec: dict, slot: str = "full", with_title: bool = False, no_footnote: bool = False) -> str:
    cats = spec.get("categories", [])
    series = spec.get("series", [])
    bars = [s for s in series if s.get("type", "bar") == "bar"]
    lines = [s for s in series if s.get("type") == "line"]
    stacked = bool(spec.get("stacked"))
    digits = spec.get("digits")
    # 柱序列允许 null (缺数): 画成 0 高度且不标数
    missing = {(id(s), i) for s in bars for i, v in enumerate(s["values"]) if v is None}
    for s in bars:
        s["values"] = [0 if v is None else v for v in s["values"]]
    n = len(cats)
    width = slot_width(slot)
    plot_h = float(spec.get("plot_h") or DEFAULT_PLOT_H[slot])

    head, y0 = head_block(spec, width, PAD, with_title)
    top = y0 + 14

    # 左右轴刻度标签宽度 → 绘图区左右留白
    if stacked and bars:
        tops = [sum(max(0, s["values"][i]) for s in bars) for i in range(n)]
        bots = [sum(min(0, s["values"][i]) for s in bars) for i in range(n)]
    else:
        tops = [max([s["values"][i] for s in bars] + [0]) for i in range(n)] if bars else [0]
        bots = [min([s["values"][i] for s in bars] + [0]) for i in range(n)] if bars else [0]
    lmax = _nice_max(max(tops) if tops else 1)
    lmin = -_nice_max(-min(bots)) if min(bots) < 0 else 0.0
    lvals = [v for s in lines for v in s["values"] if v is not None]
    rmax = _nice_max(max(lvals)) if lvals else 1.0
    rmin = -_nice_max(-min(lvals)) if lvals and min(lvals) < 0 else 0.0

    ldig = 0 if abs(lmax) >= 10 else 1
    rdig = 0 if abs(rmax) >= 10 else 1
    lw_axis = max(text_w(fmt_num(lmin + (lmax - lmin) * k / 4, digits=ldig), FS_SMALL) for k in range(5)) + 10
    rw_axis = (max(text_w(fmt_num(rmin + (rmax - rmin) * k / 4, digits=rdig), FS_SMALL) for k in range(5)) + 10) if lines else 8
    x0 = PAD + lw_axis
    x1 = width - PAD - rw_axis
    plot_w = x1 - x0
    slot_px = plot_w / max(n, 1)

    # 类目标签:按每格宽度换行, 最多两行
    cat_lines = [wrap(str(c), chars_for(slot_px - 6, FS_BODY))[:2] for c in cats]
    cat_h = max((len(l) for l in cat_lines), default=1) * LH_BODY + 8

    # 图例:按槽宽排版, 放不下就换行
    legend_items = [(s["name"], BAR_COLORS[i % len(BAR_COLORS)], "bar") for i, s in enumerate(bars)]
    legend_items += [(s["name"] + "(右轴)", LINE_COLORS[i % len(LINE_COLORS)], "line") for i, s in enumerate(lines)]
    legend_rows: list[list[tuple]] = [[]]
    used = 0.0
    for it in legend_items:
        w_it = 20 + text_w(it[0], FS_BODY) + 20
        if used + w_it > plot_w and legend_rows[-1]:
            legend_rows.append([]); used = 0.0
        legend_rows[-1].append(it); used += w_it
    legend_h = len(legend_rows) * LH_BODY + 10 if legend_items else 0

    fl = foot_lines(spec, width, no_footnote)
    height = top + plot_h + cat_h + legend_h + foot_height(fl) + 10
    out = [svg_open(width, height), head]

    def yl(v: float) -> float:
        return top + plot_h - (v - lmin) / (lmax - lmin) * plot_h

    def yr(v: float) -> float:
        return top + plot_h - (v - rmin) / (rmax - rmin) * plot_h

    # 网格与刻度
    for k in range(5):
        v = lmin + (lmax - lmin) * k / 4
        y = yl(v)
        out.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{LINE if k else GREY}" stroke-width="{0.6 if k else 1}"/>')
        out.append(text(x0 - 8, y + 4.5, fmt_num(v, digits=ldig), size=FS_SMALL, fill=GREY, anchor="end"))
    if lmin < 0:
        out.append(f'<line x1="{x0}" y1="{yl(0):.1f}" x2="{x1}" y2="{yl(0):.1f}" stroke="{GREY}" stroke-width="1"/>')
    if lines:
        for k in range(5):
            v = rmin + (rmax - rmin) * k / 4
            out.append(text(x1 + 8, yr(v) + 4.5, fmt_num(v, digits=rdig), size=FS_SMALL, fill=GREY, anchor="start"))

    # 柱
    group_w = slot_px * 0.64
    nb = 1 if stacked else max(len(bars), 1)
    bw = group_w / nb
    # 数值标签放不下就整张图不标 (窄槽), 提醒作者换宽槽
    lab_ok = True
    for s in bars:
        for v in s["values"]:
            if text_w(fmt_num(v, digits=digits), FS_SMALL) > (bw - 3) * (1.6 if stacked else 1.0):
                lab_ok = False
    if not lab_ok:
        print(f"[!] 槽 {slot} 太窄, 柱上数值标签放不下已省略 —— 改 --slot full 或减少类目", file=sys.stderr)
    for i in range(n):
        gx = x0 + slot_px * i + (slot_px - group_w) / 2
        pos_acc, neg_acc = 0.0, 0.0
        for bi, s in enumerate(bars):
            v = s["values"][i]
            col = BAR_COLORS[bi % len(BAR_COLORS)]
            if stacked:
                base = pos_acc if v >= 0 else neg_acc
                y_a, y_b = yl(base), yl(base + v)
                x = gx
                if v >= 0:
                    pos_acc += v
                else:
                    neg_acc += v
            else:
                y_a, y_b = yl(0), yl(v)
                x = gx + bi * bw
            yt, hh = min(y_a, y_b), abs(y_a - y_b)
            out.append(f'<rect x="{x:.1f}" y="{yt:.1f}" width="{bw - 3:.1f}" height="{max(hh, 0.5):.1f}" fill="{col}"/>')
            lab = "" if ((id(s), i) in missing or not lab_ok) else fmt_num(v, digits=digits)
            if stacked and hh >= LH_SMALL:
                out.append(text(x + (bw - 3) / 2, yt + hh / 2 + 4.5, lab, size=FS_SMALL, fill="#ffffff" if bi < 2 else INK, anchor="middle"))
            elif not stacked:
                out.append(text(x + (bw - 3) / 2, (yt - 6) if v >= 0 else (yt + hh + 14), lab, size=FS_SMALL, fill=INK, anchor="middle"))
        if stacked and bars:
            tot = sum(s["values"][i] for s in bars)
            out.append(text(gx + group_w / 2, yl(max(tot, pos_acc)) - 7, fmt_num(tot, digits=digits), size=FS_BODY, fill=INK, anchor="middle", weight="600"))
        for li, ln in enumerate(cat_lines[i]):
            out.append(text(x0 + slot_px * i + slot_px / 2, top + plot_h + 20 + li * LH_BODY, ln, size=FS_BODY, fill=INK, anchor="middle"))

    # 线
    for li, s in enumerate(lines):
        col = LINE_COLORS[li % len(LINE_COLORS)]
        pts = [(x0 + slot_px * i + slot_px / 2, yr(s["values"][i]) if s["values"][i] is not None else None) for i in range(n)]
        seg: list[tuple[float, float]] = []
        for x, y in pts + [(0.0, None)]:
            if y is None:
                if len(seg) > 1:
                    out.append('<polyline points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in seg) + f'" fill="none" stroke="{col}" stroke-width="2"/>')
                seg = []
            else:
                seg.append((x, y))
        for i, (x, y) in enumerate(pts):
            if y is None:
                continue
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#ffffff" stroke="{col}" stroke-width="2"/>')
            if not lab_ok:
                continue
            lab = fmt_num(s["values"][i], digits=digits)
            # 标签放在点的右侧并垫白底; 若离柱顶合计标签太近 (<24px) 就放到点的右下方
            lw = text_w(lab, FS_SMALL) + 8
            bar_top_y = yl(tops[i]) if tops and i < len(tops) else -1e9
            ty = y + 16 if abs(y - bar_top_y) < 24 else y - 6
            out.append(f'<rect x="{x + 6:.1f}" y="{ty - 12:.1f}" width="{lw:.1f}" height="16" fill="#ffffff" opacity="0.9"/>')
            out.append(text(x + 9, ty, lab, size=FS_SMALL, fill=col, anchor="start", weight="600"))

    # 图例
    ly = top + plot_h + cat_h + LH_BODY
    for row in legend_rows:
        lx = x0
        for name, col, kind in row:
            if kind == "bar":
                out.append(f'<rect x="{lx}" y="{ly - 10}" width="12" height="12" fill="{col}"/>')
            else:
                out.append(f'<line x1="{lx}" y1="{ly - 4}" x2="{lx + 14}" y2="{ly - 4}" stroke="{col}" stroke-width="2"/>'
                           f'<circle cx="{lx + 7}" cy="{ly - 4}" r="3" fill="#fff" stroke="{col}" stroke-width="2"/>')
            out.append(text(lx + 20, ly, name, size=FS_BODY, fill=INK))
            lx += 20 + text_w(name, FS_BODY) + 20
        ly += LH_BODY

    out.append(foot_block(fl, height))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(run("研报式柱线图 SVG (v2.4 字阶 + 槽宽)", render))
