#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
draw_flow.py (v2.4) — 横向流程链 / 多泳道流程图 (自包含 SVG, 黑白灰 + 海军蓝)。
用在:「它怎么工作」(电 → 变电站 → 机房 → GPU → 客户)、「怎么卖」(拿地拿电 → 建机房 → 签长约 → 交付 → 按月收租)、
「一份订单怎么走」(试用 → 容量合同 → 消费 → 续约)。每步一个框 (标题 + 副行),可选 note 放框下,strong 高亮。

v2.4:框宽由槽宽 ÷ 步数算出 (不再固定 168px, 图也不再超出版心被缩小);框内标题 15、副行与 note 13;标题默认不画。

规格 (JSON):
{
  "title": "一份 Snowflake 订单怎么走",
  "subtitle": "消费型软件的 land-and-expand",
  "steps": [ {"label": "免费试用", "sub": "30 天 / 400 美元额度"},
             {"label": "签容量合同", "sub": "预付 1–3 年 credits", "strong": true, "note": "进 RPO"},
             {"label": "按用量消耗", "sub": "跑一次查询扣一次 credit", "note": "确认收入"},
             {"label": "续约 / 加购", "sub": "NRR 125%"} ],
  "lanes": [ {"name": "谁选型", "steps": [...]}, {"name": "谁付钱", "steps": [...]} ],   # 有 lanes 时忽略 steps, 每条泳道一行
  "footnote": "DNA 自绘 · 数据 FACT 10-K FY2026 · 2026-09-16"
}
用法: python draw_flow.py spec.json --out images/flow_order.svg [--slot full]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _svgkit import (FS_BODY, FS_SMALL, GREY, INK, LH_BODY, LH_SMALL, LIGHT, NAVY, PAD,  # noqa: E402
                     chars_for, foot_block, foot_height, foot_lines, head_block, run,
                     slot_width, svg_open, text, text_w, wrap)

GAP = 26
LANE_LAB_W = 116


def _box_h(steps: list[dict], box_w: float) -> tuple[float, int, int]:
    """框高 = 标题行 + 副行行数;返回 (框高, 最多副行数, 最多 note 行数)。"""
    max_sub = max((len(wrap(st.get("sub", ""), chars_for(box_w - 20, FS_SMALL))[:2]) for st in steps), default=0)
    max_note = max((len(wrap(st["note"], chars_for(box_w, FS_SMALL))[:2]) if st.get("note") else 0 for st in steps), default=0)
    return 16 + LH_BODY + max_sub * LH_SMALL + 12, max_sub, max_note


def _row(out: list[str], steps: list[dict], x0: float, y: float, box_w: float, box_h: float) -> None:
    for i, st in enumerate(steps):
        x = x0 + i * (box_w + GAP)
        strong = st.get("strong")
        fill = NAVY[1] if strong else LIGHT
        stroke = NAVY[1] if strong else "#cfcfcf"
        tc = "#ffffff" if strong else INK
        sc = "#e6ecf2" if strong else GREY
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{box_w:.1f}" height="{box_h:.1f}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>')
        out.append(f'<circle cx="{x + 16:.1f}" cy="{y + 17:.1f}" r="10" fill="{"#ffffff" if strong else NAVY[1]}"/>')
        out.append(text(x + 16, y + 21.5, str(i + 1), size=FS_SMALL, fill=(NAVY[1] if strong else "#ffffff"), anchor="middle", weight="600"))
        lab = wrap(st.get("label", ""), chars_for(box_w - 40, FS_BODY))[0]
        out.append(text(x + 33, y + 22, lab, size=FS_BODY, fill=tc, weight="600"))
        for li, ln in enumerate(wrap(st.get("sub", ""), chars_for(box_w - 20, FS_SMALL))[:2]):
            out.append(text(x + 12, y + 16 + LH_BODY + 4 + li * LH_SMALL, ln, size=FS_SMALL, fill=sc))
        for li, ln in enumerate(wrap(st.get("note", ""), chars_for(box_w, FS_SMALL))[:2] if st.get("note") else []):
            out.append(text(x + box_w / 2, y + box_h + 16 + li * LH_SMALL, ln, size=FS_SMALL, fill=GREY, anchor="middle"))
        if i + 1 < len(steps):
            out.append(f'<line x1="{x + box_w + 2:.1f}" y1="{y + box_h / 2:.1f}" x2="{x + box_w + GAP - 5:.1f}" y2="{y + box_h / 2:.1f}" stroke="{GREY}" stroke-width="1.4" marker-end="url(#arr)"/>')


def render(spec: dict, slot: str = "full", with_title: bool = False, no_footnote: bool = False) -> str:
    lanes = spec.get("lanes") or [{"name": None, "steps": spec.get("steps", [])}]
    n = max((len(l.get("steps", [])) for l in lanes), default=1)
    has_lane_names = any(l.get("name") for l in lanes)
    width = slot_width(slot)
    x0 = PAD + (LANE_LAB_W if has_lane_names else 0)
    box_w = (width - PAD - x0 - (n - 1) * GAP) / max(n, 1)
    if box_w < 110:
        print(f"[!] 槽 {slot} 放 {n} 步太挤 (每框 {box_w:.0f}px) —— 改 --slot full 或减少步数", file=sys.stderr)

    all_steps = [st for l in lanes for st in l.get("steps", [])] or [{}]
    box_h, _, max_note = _box_h(all_steps, box_w)
    row_h = box_h + (max_note * LH_SMALL + 14 if max_note else 0) + 26

    head, y0 = head_block(spec, width, PAD, with_title)
    fl = foot_lines(spec, width, no_footnote)
    height = y0 + 10 + len(lanes) * row_h + foot_height(fl) + 8
    out = [svg_open(width, height)]
    out.append(f'<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{GREY}"/></marker></defs>')
    out.append(head)
    y = y0 + 10
    for ln in lanes:
        if ln.get("name"):
            for li, s in enumerate(wrap(ln["name"], chars_for(LANE_LAB_W - 10, FS_BODY))[:2]):
                out.append(text(PAD, y + 22 + li * LH_BODY, s, size=FS_BODY, fill=NAVY[1], weight="600"))
        _row(out, ln.get("steps", []), x0, y, box_w, box_h)
        y += row_h
    out.append(foot_block(fl, height))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(run("横向流程链 SVG (v2.4 字阶 + 槽宽)", render))
