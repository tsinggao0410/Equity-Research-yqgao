#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
draw_moneyflow.py (v2.4) — 「钱怎么流」图:客户付的钱从左边进公司,再从右边分给供应商 / 员工 / 折旧 / 税 / 股东。
带宽 = 金额,读者一眼看出「一块钱里几毛给了谁」。黑白灰 + 海军蓝,自包含 SVG,标 DNA 自绘 + 数据出处。

v2.4:按槽宽出图 (--slot, 建议 full);带内标签 15、备注与列头 13;标题默认不画 (渲染器 caption 就是标题)。

规格 (JSON):
{
  "title": "Snowflake · FY2026 一块钱去哪了",
  "subtitle": "GAAP 口径 · 单位 亿美元 · 10-K FY2026",
  "unit": "亿美元",
  "inflows":  [ {"label": "产品收入", "value": 44.7, "note": "13,245 家客户按用量付费"},
                {"label": "专业服务", "value": 1.9} ],
  "hub":      {"label": "Snowflake", "sub": "收入 46.6"},
  "outflows": [ {"label": "云厂商算力与存储", "value": 12.4, "kind": "cogs", "note": "AWS/Azure/GCP"},
                {"label": "销售与市场", "value": 19.0, "kind": "opex"},
                {"label": "经营亏损", "value": 6.9, "kind": "loss"} ],   # 亏损: 自动挪到左侧当「缺口」带;盈利公司用 kind=profit 放右侧
  "footnote": "DNA 自绘 · 数据 FACT 10-K FY2026 · 2026-09-16"
}
kind ∈ cogs | opex | da | interest | tax | profit | loss | other  (决定颜色: profit 深海军蓝, loss 砖红虚线, cogs 中海军蓝, 其余灰阶)
右侧合计 ≠ 左侧合计时自动加一条「差额」带并在 stderr 提示 (通常是漏了 D&A / 利息 / 税 / 其他收支)。
用法: python draw_moneyflow.py spec.json --out images/moneyflow_fy2026.svg
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _svgkit import (FS_BODY, FS_SMALL, GREY, INK, LH_SMALL, LIGHT, NAVY, PAD, RED,  # noqa: E402
                     chars_for, fit, fmt_num, foot_block, foot_height, foot_lines, head_block, run,
                     slot_width, svg_open, text, text_w, wrap)

KIND_FILL = {
    "cogs": NAVY[2], "opex": NAVY[3], "da": "#c9c9c9", "interest": "#c9c9c9", "tax": "#c9c9c9",
    "other": "#d9d9d9", "profit": NAVY[0], "loss": "#ffffff",
}
KIND_STROKE = {"loss": RED}
KIND_TEXT = {"profit": "#ffffff", "cogs": "#ffffff"}

HUB_W = 150
BAND_GAP = 9
MIN_BAND = 26          # 一行 15px 标签放得下
TWO_LINE_BAND = 52     # 够高就把备注放第二行


def _layout(items: list[dict], top: float, total_h: float, total_v: float) -> list[tuple[float, float]]:
    """按金额分配高度,最小高度保证标签可读;返回 [(y, h)]。"""
    n = len(items)
    avail = total_h - BAND_GAP * (n - 1)
    hs = [max(MIN_BAND, avail * (abs(it["value"]) / total_v)) if total_v else avail / n for it in items]
    scale = avail / sum(hs) if sum(hs) > avail else 1.0
    hs = [h * scale for h in hs]
    ys, y = [], top
    for h in hs:
        ys.append((y, h)); y += h + BAND_GAP
    return ys


def render(spec: dict, slot: str = "full", with_title: bool = False, no_footnote: bool = False) -> str:
    unit = spec.get("unit", "")
    inflows = [dict(x) for x in spec.get("inflows", [])]
    outflows = [dict(x) for x in spec.get("outflows", [])]
    # 亏损 = 客户付的钱不够付成本, 缺口靠现金/股权补 → 它是左边的一条流入带, 不是右边的支出
    moved = [x for x in outflows if x.get("kind") == "loss"]
    if moved:
        outflows = [x for x in outflows if x.get("kind") != "loss"]
        for x in moved:
            x.setdefault("note", "缺口靠现金 / 股权 / 股权激励填")
        inflows += moved
        print(f"[i] {len(moved)} 条 kind=loss 已挪到左侧 (亏损是缺口, 不是支出)", file=sys.stderr)
    tin = sum(x["value"] for x in inflows)
    tout = sum(x["value"] for x in outflows)
    if abs(tin - tout) > max(0.005 * max(tin, tout), 1e-9):
        diff = tin - tout
        print(f"[!] 左右不平: 流入 {tin:.2f} vs 流出 {tout:.2f}, 差 {diff:+.2f} → 自动加「其他/差额」带", file=sys.stderr)
        (outflows if diff > 0 else inflows).append({"label": "其他 / 差额", "value": abs(diff), "kind": "other"})
        tin = sum(x["value"] for x in inflows); tout = sum(x["value"] for x in outflows)
    total = max(tin, tout)
    revenue = sum(x["value"] for x in inflows if x.get("kind") not in ("loss", "other")) or tin  # 百分比一律相对收入

    width = slot_width(slot)
    link = max(70.0, (width - 2 * PAD - HUB_W) * 0.105)
    col_w = (width - 2 * PAD - HUB_W - 2 * link) / 2
    if col_w < 190:
        print(f"[!] 槽 {slot} 太窄 (每列 {col_w:.0f}px), 钱流图建议 --slot full", file=sys.stderr)

    head, y0 = head_block(spec, width, PAD, with_title)
    top = y0 + 24     # 顶部留给列头
    n_max = max(len(inflows), len(outflows))
    body_h = max(300.0, n_max * 62.0)
    fl = foot_lines(spec, width, no_footnote)
    height = top + body_h + foot_height(fl) + 16
    out = [svg_open(width, height), head]

    x_in = PAD
    x_hub = PAD + col_w + link
    x_out = x_hub + HUB_W + link

    out.append(f'<rect x="{x_hub:.1f}" y="{top:.1f}" width="{HUB_W}" height="{body_h:.1f}" rx="6" fill="{LIGHT}" stroke="{NAVY[1]}" stroke-width="1.5"/>')
    hub = spec.get("hub", {})
    out.append(text(x_hub + HUB_W / 2, top + body_h / 2 - 4, fit(hub.get("label", "公司"), HUB_W - 12, FS_BODY), size=FS_BODY, weight="600", anchor="middle"))
    if hub.get("sub"):
        out.append(text(x_hub + HUB_W / 2, top + body_h / 2 + 17, fit(hub["sub"], HUB_W - 12, FS_SMALL), size=FS_SMALL, fill=GREY, anchor="middle"))

    def draw_side(items: list[dict], x_col: float, is_in: bool) -> None:
        lay = _layout(items, top, body_h, total)
        y = top
        for it, (by, bh) in zip(items, lay):
            kind = it.get("kind", "other")
            hub_slot_h = body_h * (it["value"] / total) if total else bh
            if is_in:
                x1, x2 = x_col + col_w, x_hub
                p = (f"M{x1:.1f},{by:.1f} C{(x1 + x2) / 2:.1f},{by:.1f} {(x1 + x2) / 2:.1f},{y:.1f} {x2:.1f},{y:.1f} "
                     f"L{x2:.1f},{y + hub_slot_h:.1f} C{(x1 + x2) / 2:.1f},{y + hub_slot_h:.1f} {(x1 + x2) / 2:.1f},{by + bh:.1f} {x1:.1f},{by + bh:.1f} Z")
            else:
                x1, x2 = x_hub + HUB_W, x_col
                p = (f"M{x1:.1f},{y:.1f} C{(x1 + x2) / 2:.1f},{y:.1f} {(x1 + x2) / 2:.1f},{by:.1f} {x2:.1f},{by:.1f} "
                     f"L{x2:.1f},{by + bh:.1f} C{(x1 + x2) / 2:.1f},{by + bh:.1f} {(x1 + x2) / 2:.1f},{y + hub_slot_h:.1f} {x1:.1f},{y + hub_slot_h:.1f} Z")
            out.append(f'<path d="{p}" fill="{NAVY[4] if kind != "loss" else "#f6e9e7"}" stroke="none" opacity="0.9"/>')
            is_loss = kind == "loss"
            if is_in:
                fill = "#ffffff" if is_loss else NAVY[1]
                stroke, dash = (RED, ' stroke-dasharray="5 3"') if is_loss else ("none", "")
                tc = RED if is_loss else "#ffffff"
            else:
                fill = KIND_FILL.get(kind, "#d9d9d9")
                stroke, dash = KIND_STROKE.get(kind, "none"), ""
                tc = KIND_TEXT.get(kind, INK)
            out.append(f'<rect x="{x_col:.1f}" y="{by:.1f}" width="{col_w:.1f}" height="{bh:.1f}" rx="3" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash}/>')
            pct = f"{it['value'] / revenue * 100:.0f}%" if revenue else ""
            label = f"{it['label']}  {fmt_num(it['value'])}{unit}  {pct}" + ("(占收入)" if is_loss else "")
            label = fit(label, col_w - 20, FS_BODY)
            ty = by + min(bh, 26) / 2 + 5.5
            out.append(text(x_col + 10, ty, label, size=FS_BODY, fill=tc, weight="600"))
            if it.get("note"):
                note_fill = "#e6ecf2" if tc == "#ffffff" else GREY
                if bh >= TWO_LINE_BAND:
                    out.append(text(x_col + 10, ty + LH_SMALL + 2, fit(it["note"], col_w - 20, FS_SMALL), size=FS_SMALL, fill=note_fill))
                else:   # 矮带: 备注接在标签后面同一行
                    lw = text_w(label, FS_BODY) + 12
                    out.append(text(x_col + 10 + lw, ty, fit(it["note"], col_w - 20 - lw, FS_SMALL), size=FS_SMALL, fill=note_fill))
            y += hub_slot_h

    draw_side(inflows, x_in, True)
    draw_side(outflows, x_out, False)
    out.append(text(x_in, top - 9, f"谁付钱 · 收入 {fmt_num(revenue)}{unit}", size=FS_SMALL, fill=NAVY[1], weight="600"))
    out.append(text(x_out, top - 9, fit("钱去了哪 · 每 1 元收入的分配 (% 相对收入)", col_w, FS_SMALL), size=FS_SMALL, fill=NAVY[1], weight="600"))
    out.append(foot_block(fl, height))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(run("钱怎么流 (money-flow) SVG (v2.4 字阶 + 槽宽)", render))
