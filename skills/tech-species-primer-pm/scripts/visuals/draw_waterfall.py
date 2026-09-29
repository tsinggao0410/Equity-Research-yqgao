#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
draw_waterfall.py (v2.4) — 单位经济学瀑布图:一台 / 一个客户 / 一兆瓦 的钱从「收入」一步步扣到「利润」。
每根柱子标数字;kind=start 从 0 起,delta 浮动 (负数向下),subtotal/end 回到 0 起。黑白灰 + 海军蓝,自包含 SVG。

v2.4:按槽宽出图 (--slot), 柱宽由槽宽与步数算出;图内只有 15 (柱标签 / 数值) 与 13 (备注 / 占比 / 副题 / 脚注) 两个字号;标题默认不画。

规格 (JSON):
{
  "title": "一台重型发动机的账 (FY2025)",
  "subtitle": "ASP 8.87 万元 = 分档收入 ÷ 台数 (EST) · 综合毛利率 16.5% · 单位 元/台",
  "unit": "元",
  "steps": [
    {"label": "售价 (ASP)", "value": 88653, "kind": "start"},
    {"label": "原材料+外购件", "value": -62000, "kind": "delta", "note": "EST 按综合毛利率"},
    {"label": "人工+折旧", "value": -12000, "kind": "delta"},
    {"label": "单台毛利", "kind": "subtotal"},
    {"label": "销售/管理/研发", "value": -9800, "kind": "delta"},
    {"label": "单台营业利润", "kind": "end"}
  ],
  "plot_h": 300,
  "footnote": "DNA 自绘 · 数据 FACT 20-F FY2025 + EST 拆分 · 2026-09-16"
}
用法: python draw_waterfall.py spec.json --out images/unit_econ_H.svg [--slot half]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _svgkit import (FS_BODY, FS_SMALL, GREEN, GREY, INK, LH_BODY, LH_SMALL, LINE, NAVY, PAD, RED,  # noqa: E402
                     chars_for, fmt_num, foot_block, foot_height, foot_lines, head_block, run,
                     slot_width, svg_open, text, text_w, wrap)

DEFAULT_PLOT_H = {"full": 300, "half": 250, "third": 210}


def render(spec: dict, slot: str = "full", with_title: bool = False, no_footnote: bool = False) -> str:
    steps = spec.get("steps", [])
    unit = spec.get("unit", "")
    run_v = 0.0
    bars = []  # (step, y_from, y_to, kind, value_shown)
    for st in steps:
        kind = st.get("kind", "delta")
        if kind == "start":
            run_v = float(st["value"]); bars.append((st, 0.0, run_v, kind, run_v))
        elif kind in ("subtotal", "end"):
            v = float(st["value"]) if st.get("value") is not None else run_v
            run_v = v; bars.append((st, 0.0, run_v, kind, run_v))
        else:
            v = float(st["value"]); bars.append((st, run_v, run_v + v, kind, v)); run_v += v
    vals = [b[1] for b in bars] + [b[2] for b in bars] + [0.0]
    vmin, vmax = min(vals), max(vals)
    if vmax == vmin:
        vmax = vmin + 1
    n = max(len(bars), 1)

    width = slot_width(slot)
    plot_h = float(spec.get("plot_h") or DEFAULT_PLOT_H[slot])
    head, y0 = head_block(spec, width, PAD, with_title)
    top = y0 + 24   # 顶部留给「占售价 %」小字

    x0 = PAD + 8
    avail = width - PAD - 8 - x0
    step_w = avail / n
    bar_w = step_w * 0.72
    gap = step_w - bar_w

    # 柱下标签与备注:按柱宽换行
    lab_lines = [wrap(b[0].get("label", ""), chars_for(step_w - 4, FS_BODY))[:3] for b in bars]
    note_lines = [wrap(b[0]["note"], chars_for(step_w - 4, FS_SMALL))[:2] if b[0].get("note") else [] for b in bars]
    lab_h = max((len(l) for l in lab_lines), default=1) * LH_BODY
    note_h = max((len(l) for l in note_lines), default=0) * LH_SMALL
    fl = foot_lines(spec, width, no_footnote)
    height = top + plot_h + 22 + lab_h + note_h + foot_height(fl) + 10
    out = [svg_open(width, height), head]

    def ypix(v: float) -> float:
        return top + plot_h - (v - vmin) / (vmax - vmin) * plot_h

    out.append(f'<line x1="{x0 - 6}" y1="{ypix(0):.1f}" x2="{width - PAD}" y2="{ypix(0):.1f}" stroke="{LINE}" stroke-width="1"/>')
    for i, (st, a, b, kind, shown) in enumerate(bars):
        x = x0 + i * step_w + gap / 2
        ya, yb = ypix(a), ypix(b)
        top_y, h = min(ya, yb), abs(ya - yb)
        if kind == "start":
            fill = NAVY[1]
        elif kind in ("subtotal", "end"):
            fill = NAVY[0] if b >= 0 else "#ffffff"
        else:
            fill = "#c9d3dd" if shown < 0 else "#dfe7ee"
        stroke = RED if (kind in ("subtotal", "end") and b < 0) else "none"
        dash = ' stroke-dasharray="5 3"' if stroke != "none" else ""
        out.append(f'<rect x="{x:.1f}" y="{top_y:.1f}" width="{bar_w:.1f}" height="{max(h, 1):.1f}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash}/>')
        if i + 1 < n:
            out.append(f'<line x1="{x + bar_w:.1f}" y1="{yb:.1f}" x2="{x + step_w:.1f}" y2="{yb:.1f}" stroke="{GREY}" stroke-width="0.8" stroke-dasharray="3 3"/>')
        if kind in ("start", "subtotal", "end"):
            lab = fmt_num(b) + unit
            col = INK if b >= 0 else RED
        else:
            lab = ("+" if shown > 0 else "−") + fmt_num(abs(shown)) + unit
            col = GREEN if shown > 0 else RED
        if text_w(lab, FS_BODY) > bar_w + gap:      # 放不下就用次级字号
            size_v = FS_SMALL
        else:
            size_v = FS_BODY
        ly = top_y - 7 if (kind != "delta" or shown > 0) else top_y + h + 16
        out.append(text(x + bar_w / 2, ly, lab, size=size_v, fill=col, anchor="middle", weight="600"))
        for li, ln in enumerate(lab_lines[i]):
            out.append(text(x + bar_w / 2, top + plot_h + 22 + li * LH_BODY, ln, size=FS_BODY, fill=INK, anchor="middle"))
        for li, ln in enumerate(note_lines[i]):
            out.append(text(x + bar_w / 2, top + plot_h + 22 + lab_h + 2 + li * LH_SMALL, ln, size=FS_SMALL, fill=GREY, anchor="middle"))

    if bars and bars[0][3] == "start" and bars[0][2]:
        base = bars[0][2]
        for i, (st, a, b, kind, shown) in enumerate(bars):
            if kind in ("subtotal", "end"):
                x = x0 + i * step_w + gap / 2
                out.append(text(x + bar_w / 2, top - 9, f"{b / base * 100:.0f}% 的售价", size=FS_SMALL, fill=GREY, anchor="middle"))

    out.append(foot_block(fl, height))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(run("单位经济学瀑布图 SVG (v2.4 字阶 + 槽宽)", render))
