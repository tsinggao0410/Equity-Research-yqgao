#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
draw_position_map.py (v2.4) — 「同行是谁、它在哪」的站位矩阵:行 = 站位 (云厂自有 / 独立第三方 / 老一代…),
列 = 产品档 / 细分市场;格子里写玩家名,本公司高亮。自包含 SVG,黑白灰 + 海军蓝。

v2.4:按槽宽出图 (--slot, 建议 full);列宽由槽宽 ÷ 列数算出;格内玩家名 15、行列头 15、脚注 13;标题默认不画。

规格 (JSON):
{
  "title": "云数据平台 · 谁站在哪",
  "subtitle": "行 = 站位 · 列 = 主攻负载 · 格内为玩家 (括号内年化收入, EST)",
  "rows": ["云厂商自有", "独立第三方", "老一代数仓"],
  "cols": ["数据仓库 / 分析", "数据工程 / 湖仓", "AI / ML"],
  "cells": { "云厂商自有|数据仓库 / 分析": ["BigQuery", "Redshift", "Fabric"],
             "独立第三方|数据仓库 / 分析": ["Snowflake ★", "Databricks"] },
  "highlight": "Snowflake",
  "footnote": "DNA 自绘 · 名单 FACT 10-K Competition 段 · 2026-09-16"
}
用法: python draw_position_map.py spec.json --out images/position_map.svg
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _svgkit import (FS_BODY, FS_SMALL, GREY, INK, LH_BODY, LIGHT, LINE, NAVY, PAD,  # noqa: E402
                     chars_for, foot_block, foot_height, foot_lines, head_block, run,
                     slot_width, svg_open, text, text_w, wrap)

ROW_LAB_W = 150
HEAD_H = 34
CELL_MIN_H = 64


def render(spec: dict, slot: str = "full", with_title: bool = False, no_footnote: bool = False) -> str:
    rows, cols = spec.get("rows", []), spec.get("cols", [])
    cells = spec.get("cells", {})
    hl = spec.get("highlight", "")
    width = slot_width(slot)
    cell_w = (width - 2 * PAD - ROW_LAB_W) / max(len(cols), 1)
    if cell_w < 150:
        print(f"[!] 槽 {slot} 放 {len(cols)} 列太挤 (每列 {cell_w:.0f}px) —— 改 --slot full 或合并列", file=sys.stderr)
    cell_chars = chars_for(cell_w - 22, FS_BODY)

    wrapped: dict[str, list[str]] = {}
    row_h: list[float] = []
    for r in rows:
        mx = 1
        for c in cols:
            key = f"{r}|{c}"
            lns: list[str] = []
            for it in cells.get(key, []):
                lns += wrap(it, cell_chars)
            wrapped[key] = lns
            mx = max(mx, len(lns) or 1)
        row_h.append(max(CELL_MIN_H, 18 + mx * LH_BODY))

    head, y0 = head_block(spec, width, PAD, with_title)
    top = y0 + 12
    fl = foot_lines(spec, width, no_footnote)
    height = top + HEAD_H + sum(row_h) + foot_height(fl) + 14
    out = [svg_open(width, height), head]

    x0 = PAD + ROW_LAB_W
    for ci, c in enumerate(cols):
        x = x0 + ci * cell_w
        out.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{cell_w:.1f}" height="{HEAD_H}" fill="{NAVY[1]}"/>')
        lns = wrap(c, chars_for(cell_w - 16, FS_BODY))[:2]
        for li, ln in enumerate(lns):
            ty = top + HEAD_H / 2 + 5.5 - (len(lns) - 1) * LH_BODY / 2 + li * LH_BODY
            out.append(text(x + cell_w / 2, ty, ln, size=FS_BODY, fill="#ffffff", anchor="middle", weight="600"))
    y = top + HEAD_H
    for ri, r in enumerate(rows):
        h = row_h[ri]
        out.append(f'<rect x="{PAD}" y="{y:.1f}" width="{ROW_LAB_W}" height="{h:.1f}" fill="{LIGHT}" stroke="{LINE}" stroke-width="0.8"/>')
        for li, ln in enumerate(wrap(r, chars_for(ROW_LAB_W - 20, FS_BODY))[:3]):
            out.append(text(PAD + 10, y + 24 + li * LH_BODY, ln, size=FS_BODY, fill=NAVY[0], weight="600"))
        for ci, c in enumerate(cols):
            x = x0 + ci * cell_w
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w:.1f}" height="{h:.1f}" fill="#ffffff" stroke="{LINE}" stroke-width="0.8"/>')
            ty = y + 24
            for it in cells.get(f"{r}|{c}", []):
                is_hl = bool(hl) and hl in it
                for ln in wrap(it, cell_chars):
                    if is_hl:
                        out.append(f'<rect x="{x + 6:.1f}" y="{ty - 14:.1f}" width="{min(cell_w - 12, text_w(ln, FS_BODY) + 10):.1f}" height="19" rx="3" fill="{NAVY[0]}"/>')
                        out.append(text(x + 11, ty, ln, size=FS_BODY, fill="#ffffff", weight="600"))
                    else:
                        out.append(text(x + 11, ty, ln, size=FS_BODY, fill=INK))
                    ty += LH_BODY
        y += h
    out.append(foot_block(fl, height))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(run("站位矩阵 SVG (v2.4 字阶 + 槽宽)", render))
