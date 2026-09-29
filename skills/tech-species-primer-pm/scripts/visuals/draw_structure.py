#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
draw_structure.py (v2.4) — 官网/IR 没有业务结构图时,按 JSON 规格自画一张「商业逻辑结构图」(SVG, 自包含, 黑白灰+海军蓝)。
标 DNA(买方自绘),不冒充官方图。

v2.4:并入 _svgkit 字阶与槽宽 —— 框宽由槽宽 ÷ 列数算出, 框高由最长节点的行数算出 (不再截字);
     框内首行 15 粗、其余 15、右上小标与边标签 13;标题默认不画 (渲染器 caption 就是标题)。

规格 (JSON):
{
  "title": "玉柴国际 · 谁付钱、买什么、装在哪",
  "subtitle": "FY2025 · 上市口径 · 单位: 亿元 / 万台",
  "columns": [                                   # 从左到右的泳道, 每列若干节点
    {"name": "上游 (自制/外购)", "nodes": [{"id":"u1","label":"缸体/缸盖/曲轴\\n自制 (自铸>40万件)"}, {"id":"u2","label":"共轨+ECU\\n外购 (国际供应商)","muted":true}]},
    {"name": "玉柴 (GYMCL)", "nodes": [{"id":"H","label":"重型 >7L\\n11.0万台 · 98亿 · 39.6%","strong":true}]},
    {"name": "直接客户 (谁付钱)", "nodes": [{"id":"c1","label":"重卡 OEM\\n解放/东风/福田/陕汽","note":"客户兼对手"}]},
    {"name": "终端 (谁使用)", "nodes": [{"id":"e1","label":"物流车队 / 个体司机"}]}
  ],
  "edges": [ {"from":"u1","to":"H"}, {"from":"H","to":"c1","label":"配套目录","strong":true} ],
  "footnote": "DNA 自绘 · 数据 FACT 见 20-F FY2025 · 2026-09-15"
}
节点可选: strong(海军蓝实底, 重点) / muted(灰虚线, 外购或不并表) / note(右上小标)。
用法: python draw_structure.py spec.json --out images/structure.svg [--slot full] [--png]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _svgkit import (FS_BODY, FS_SMALL, GREY, INK, LH_BODY, LIGHT, NAVY, PAD,  # noqa: E402
                     chars_for, foot_block, foot_height, foot_lines, head_block, slot_width,
                     svg_open, text, text_w, wrap)

GAP_X_MIN, GAP_Y = 64, 24
HEAD_H = 34


def render(spec: dict, slot: str = "full", with_title: bool = False, no_footnote: bool = False) -> str:
    cols = spec.get("columns", [])
    ncol = max(len(cols), 1)
    width = slot_width(slot)
    gap_x = max(GAP_X_MIN, (width - 2 * PAD) * 0.055)
    node_w = (width - 2 * PAD - (ncol - 1) * gap_x) / ncol
    if node_w < 150:
        print(f"[!] 槽 {slot} 放 {ncol} 列太挤 (每框 {node_w:.0f}px) —— 改 --slot full 或合并列", file=sys.stderr)
    chars = chars_for(node_w - 16, FS_BODY)

    # 先换行, 再按最长节点定统一框高
    wrapped: dict[int, list[list[str]]] = {}
    max_lines = 1
    for ci, col in enumerate(cols):
        wrapped[ci] = []
        for nd in col.get("nodes", []):
            lns: list[str] = []
            for part in str(nd.get("label", "")).replace("\\n", "\n").split("\n"):
                lns += wrap(part, chars)
            wrapped[ci].append(lns)
            max_lines = max(max_lines, len(lns))
    node_h = max_lines * LH_BODY + 18
    max_nodes = max((len(c.get("nodes", [])) for c in cols), default=1)

    head, y0 = head_block(spec, width, PAD, with_title)
    top = y0 + 12
    body_h = max_nodes * (node_h + GAP_Y) - GAP_Y
    fl = foot_lines(spec, width, no_footnote)
    height = top + HEAD_H + body_h + foot_height(fl) + 18

    pos: dict[str, tuple[float, float]] = {}
    out = [svg_open(width, height)]
    out.append('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
               f'<path d="M0,0 L10,5 L0,10 z" fill="{GREY}"/></marker></defs>')
    out.append(head)

    for ci, col in enumerate(cols):
        x = PAD + ci * (node_w + gap_x)
        out.append(text(x + node_w / 2, top + 18, col.get("name", ""), size=FS_BODY, fill=NAVY[1], anchor="middle", weight="600"))
        out.append(f'<line x1="{x:.1f}" y1="{top + 26:.1f}" x2="{x + node_w:.1f}" y2="{top + 26:.1f}" stroke="{NAVY[1]}" stroke-width="1.2"/>')
        nodes = col.get("nodes", [])
        block_h = len(nodes) * (node_h + GAP_Y) - GAP_Y
        y_start = top + HEAD_H + (body_h - block_h) / 2
        for ni, nd in enumerate(nodes):
            y = y_start + ni * (node_h + GAP_Y)
            strong, muted = nd.get("strong"), nd.get("muted")
            fill = NAVY[1] if strong else ("#ffffff" if muted else LIGHT)
            stroke = NAVY[1] if strong else (GREY if muted else "#cfcfcf")
            dash = ' stroke-dasharray="4 3"' if muted else ""
            tcol = "#ffffff" if strong else INK
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{node_w:.1f}" height="{node_h:.1f}" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.2"{dash}/>')
            lines = wrapped[ci][ni]
            ty = y + node_h / 2 - (len(lines) - 1) * LH_BODY / 2 + 5
            for li, ln in enumerate(lines):
                fw = "600" if (li == 0 and len(lines) > 1) else "400"
                out.append(text(x + node_w / 2, ty + li * LH_BODY, ln, size=FS_BODY, fill=tcol, anchor="middle", weight=fw))
            if nd.get("note"):
                out.append(text(x + node_w, y - 6, nd["note"], size=FS_SMALL, fill=GREY, anchor="end"))
            pos[nd.get("id", f"{ci}-{ni}")] = (x, y)

    for e in spec.get("edges", []):
        a, b = pos.get(e.get("from")), pos.get(e.get("to"))
        if not a or not b:
            print(f"[!] edge 节点不存在: {e}", file=sys.stderr)
            continue
        (ax, ay), (bx, by) = a, b
        if bx > ax:
            x1, y1, x2, y2 = ax + node_w, ay + node_h / 2, bx, by + node_h / 2
        elif bx < ax:
            x1, y1, x2, y2 = ax, ay + node_h / 2, bx + node_w, by + node_h / 2
        else:
            x1, y1, x2, y2 = ax + node_w / 2, ay + node_h, bx + node_w / 2, by
        mx = (x1 + x2) / 2
        path = f"M{x1:.1f},{y1:.1f} C{mx:.1f},{y1:.1f} {mx:.1f},{y2:.1f} {x2:.1f},{y2:.1f}" if bx != ax else f"M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}"
        out.append(f'<path d="{path}" fill="none" stroke="{NAVY[1] if e.get("strong") else GREY}" stroke-width="{2 if e.get("strong") else 1.2}" marker-end="url(#arr)"/>')
        if e.get("label"):
            lw = text_w(e["label"], FS_SMALL) + 10
            out.append(f'<rect x="{mx - lw / 2:.1f}" y="{(y1 + y2) / 2 - 12:.1f}" width="{lw:.1f}" height="17" fill="#ffffff" opacity="0.92"/>')
            out.append(text(mx, (y1 + y2) / 2, e["label"], size=FS_SMALL, fill=GREY, anchor="middle"))

    out.append(foot_block(fl, height))
    out.append("</svg>")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="自画商业逻辑结构图 (SVG, v2.4 字阶 + 槽宽)")
    ap.add_argument("spec"); ap.add_argument("--out", required=True)
    ap.add_argument("--slot", default="full", choices=["full", "half", "third"])
    ap.add_argument("--title", action="store_true"); ap.add_argument("--no-footnote", action="store_true")
    ap.add_argument("--png", action="store_true", help="同时出 PNG (需 cairosvg 或 rsvg-convert)")
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    svg = render(spec, slot=a.slot, with_title=a.title, no_footnote=a.no_footnote)
    out = Path(a.out).expanduser(); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"[OK] SVG → {out} (槽 {a.slot})", file=sys.stderr)
    if a.png:
        png = out.with_suffix(".png")
        try:
            import cairosvg  # type: ignore
            cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png), output_width=1600)
            print(f"[OK] PNG → {png}", file=sys.stderr)
        except Exception:  # noqa: BLE001
            import shutil, subprocess
            if shutil.which("rsvg-convert"):
                subprocess.run(["rsvg-convert", "-w", "1600", "-o", str(png), str(out)], check=False)
                print(f"[OK] PNG (rsvg) → {png}", file=sys.stderr)
            else:
                print("[!] 没有 cairosvg / rsvg-convert,只出了 SVG(HTML 渲染器直接内嵌 SVG,不需要 PNG)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
