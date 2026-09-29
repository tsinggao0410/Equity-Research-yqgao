#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
draw_moat.py (v2.4 新增) — 「壁垒台账图」:把「为什么别人做不了 / 追不上」一条条摆在同一张表里,
每条壁垒 = 类型 + 强度三档刻度 + 可验证证据 + 击穿条件(什么一发生它就不成立)+ 大约还能挡多久。
LO 基本面研究的核心一页:读者看完知道这门生意的护城河由哪几层组成、哪一层最薄、盯什么会先破。

强度档只有三级,且**必须由证据推出**,不许拍脑袋:
  强 = 有可量化证据且对手公开尝试过并失败 / 未追平;
  中 = 有证据但对手在缩小差距, 或只在部分细分成立;
  弱 = 只有定性说法或对手已追平, 写进来是为了点名它不是壁垒。

规格 (JSON):
{
  "title": "IREN 的壁垒由四层组成, 最薄的是 GPU 采购",
  "subtitle": "强度档由证据推出 · 击穿条件是可观测事件 · 2026-09-16",
  "layers": [
    {"name": "并网电力", "type": "资源 / 排队位次", "strength": "强",
     "evidence": "5GW 已签并网协议; ERCOT 大负荷排队 3 至 5 年, 2026 年新申请排到 2030 年",
     "kill": "德州放开排队或对手批量拿到同等容量", "horizon": "3 年内难变"},
    {"name": "GPU 采购", "type": "供应链 / 分配额度", "strength": "弱",
     "evidence": "GB300 分配按订单量给, CoreWeave 与超大云拿量更大",
     "kill": "已经不是壁垒: 有钱有合同就能拿货", "horizon": "当前不成立"}
  ],
  "footnote": "DNA 自绘 · 证据 FACT 10-K FY2026 [S1]、8-K [S4] · 2026-09-16"
}
用法: python draw_moat.py moat_spec.json --out images/moat_ladder.svg [--slot full]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _svgkit import (FS_BODY, FS_SMALL, GREY, INK, LH_BODY, LH_SMALL, LIGHT, LINE, NAVY, PAD, RED,  # noqa: E402
                     chars_for, foot_block, foot_height, foot_lines, head_block, run,
                     slot_width, svg_open, text, wrap)

LEVEL = {"强": 3, "中": 2, "弱": 1, "3": 3, "2": 2, "1": 1}
LEVEL_NAME = {3: "强", 2: "中", 1: "弱"}
LEVEL_FILL = {3: NAVY[0], 2: NAVY[2], 1: "#c9c9c9"}
COLS = (0.19, 0.13, 0.38, 0.30)     # 壁垒 | 强度 | 证据 | 击穿条件
HEAD_H = 32


def render(spec: dict, slot: str = "full", with_title: bool = False, no_footnote: bool = False) -> str:
    layers = spec.get("layers", [])
    width = slot_width(slot)
    if slot != "full":
        print(f"[!] 壁垒台账建议 --slot full (当前 {slot}, 证据列会很窄)", file=sys.stderr)
    inner = width - 2 * PAD
    w = [inner * c for c in COLS]
    x = [PAD, PAD + w[0], PAD + w[0] + w[1], PAD + w[0] + w[1] + w[2]]

    rows = []
    for ly in layers:
        lv = LEVEL.get(str(ly.get("strength", "")).strip(), 2)
        name_l = wrap(ly.get("name", ""), chars_for(w[0] - 20, FS_BODY))
        type_l = wrap(ly.get("type", ""), chars_for(w[0] - 20, FS_SMALL)) if ly.get("type") else []
        ev_l = wrap(ly.get("evidence", ""), chars_for(w[2] - 20, FS_BODY))
        kill_l = wrap(ly.get("kill", ""), chars_for(w[3] - 20, FS_BODY))
        hor_l = wrap(ly.get("horizon", ""), chars_for(w[3] - 20, FS_SMALL)) if ly.get("horizon") else []
        h = max(len(name_l) * LH_BODY + len(type_l) * LH_SMALL,
                len(ev_l) * LH_BODY,
                len(kill_l) * LH_BODY + len(hor_l) * LH_SMALL,
                LH_BODY + LH_SMALL) + 20
        rows.append((lv, name_l, type_l, ev_l, kill_l, hor_l, h))

    head, y0 = head_block(spec, width, PAD, with_title)
    top = y0 + 12
    fl = foot_lines(spec, width, no_footnote)
    height = top + HEAD_H + sum(r[6] for r in rows) + foot_height(fl) + 14
    out = [svg_open(width, height), head]

    out.append(f'<rect x="{PAD}" y="{top:.1f}" width="{inner:.1f}" height="{HEAD_H}" fill="{LIGHT}"/>')
    out.append(f'<line x1="{PAD}" y1="{top:.1f}" x2="{PAD + inner:.1f}" y2="{top:.1f}" stroke="{NAVY[1]}" stroke-width="1.5"/>')
    for i, lab in enumerate(("壁垒", "强度", "证据(可验证)", "击穿条件")):
        out.append(text(x[i] + 10, top + HEAD_H / 2 + 5.5, lab, size=FS_BODY, fill=NAVY[0], weight="600"))
    y = top + HEAD_H
    out.append(f'<line x1="{PAD}" y1="{y:.1f}" x2="{PAD + inner:.1f}" y2="{y:.1f}" stroke="{NAVY[1]}" stroke-width="1"/>')

    for lv, name_l, type_l, ev_l, kill_l, hor_l, h in rows:
        ty = y + 22
        for i, ln in enumerate(name_l):
            out.append(text(x[0] + 10, ty + i * LH_BODY, ln, size=FS_BODY, fill=INK, weight="600"))
        for i, ln in enumerate(type_l):
            out.append(text(x[0] + 10, ty + len(name_l) * LH_BODY + i * LH_SMALL, ln, size=FS_SMALL, fill=GREY))
        # 强度:三格刻度 + 档名
        seg_w, seg_h, gap = min(22.0, (w[1] - 60) / 3), 10, 4
        for k in range(3):
            filled = k < lv
            out.append(f'<rect x="{x[1] + 10 + k * (seg_w + gap):.1f}" y="{ty - 9:.1f}" width="{seg_w:.1f}" height="{seg_h}" '
                       f'fill="{LEVEL_FILL[lv] if filled else "#ffffff"}" stroke="{LEVEL_FILL[lv] if filled else LINE}" stroke-width="1"/>')
        out.append(text(x[1] + 10 + 3 * (seg_w + gap) + 4, ty, LEVEL_NAME[lv], size=FS_BODY,
                        fill=(RED if lv == 1 else NAVY[0]), weight="600"))
        for i, ln in enumerate(ev_l):
            out.append(text(x[2] + 10, ty + i * LH_BODY, ln, size=FS_BODY, fill=INK))
        for i, ln in enumerate(kill_l):
            out.append(text(x[3] + 10, ty + i * LH_BODY, ln, size=FS_BODY, fill=INK))
        for i, ln in enumerate(hor_l):
            out.append(text(x[3] + 10, ty + len(kill_l) * LH_BODY + i * LH_SMALL, ln, size=FS_SMALL, fill=GREY))
        y += h
        out.append(f'<line x1="{PAD}" y1="{y:.1f}" x2="{PAD + inner:.1f}" y2="{y:.1f}" stroke="{LINE}" stroke-width="0.8"/>')

    out.append(foot_block(fl, height))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(run("壁垒台账图 SVG (v2.4)", render))
