#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
annotate_photo.py (v2.4) — 给官方实物图 / 界面截图打「编号框 + 图例」(像研报里那种:散热水箱①、柴油机②、发电机③、控制屏④)。
输入官方图 + 框坐标 (0–1 比例, 与分辨率无关),输出 PNG:框线海军蓝、编号圆标、底部白底图例条。
读者看一张图就知道「这个东西由哪几块组成、每块叫什么」。**框只能标图里真有的部件;标注是 DNA,原图来源保留在 caption。**

v2.4:图例字号按**它在版式里的槽宽**倒算 (--slot full/half/third), 让缩放后正好落在 15/13 两档字阶上,
     不再随原图分辨率漂移 (旧版 1600px 宽的图放进 half 槽, 图例只有 9px)。

规格 (JSON):
{
  "image": "images/H_YCK15N_gas_engine.jpg",
  "out": "images/H_YCK15N_annotated.png",
  "slot": "half",                                       # 可选, 也可用命令行 --slot 覆盖
  "title": "YCK15N 燃气机 · 部件一眼看",                  # 可选, 画在图例条第一行
  "boxes": [ {"x": 0.62, "y": 0.10, "w": 0.30, "h": 0.25, "label": "涡轮增压器"},
             {"x": 0.05, "y": 0.35, "w": 0.45, "h": 0.40, "label": "缸体 (自制铸件)"} ],
  "note": "标注 DNA · 原图 玉柴产品站 2026-09-15",        # 可选, 图例条末行
  "stroke": "#ffffff"                                    # 可选, 框线色 (深色底图用白色; 默认海军蓝)
}
用法: python annotate_photo.py spec.json [--slot half]   (或 --image/--out/--box "x,y,w,h,label" 多次)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _svgkit import FS_BODY, FS_SMALL, SLOT_W  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    print("[X] 需要 Pillow", file=sys.stderr); raise SystemExit(1)

NAVY = (22, 57, 90)
NAVY_D = (13, 34, 55)
INK = (34, 34, 34)
GREY = (107, 107, 107)
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Microsoft YaHei.ttf",
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=max(size, 8))
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


def annotate(spec: dict, slot: str = "full") -> Path:
    src = Path(spec["image"]).expanduser()
    im = Image.open(src).convert("RGB")
    W, H = im.size
    slot = spec.get("slot", slot)
    if slot not in SLOT_W:
        raise SystemExit(f"[X] slot 只能是 {list(SLOT_W)}")
    # 图会被渲染器按槽宽等比缩放 → 想让图例落在 15px, 原图里就要画 15 × W / 槽宽
    k = W / SLOT_W[slot]
    fs = int(round(FS_BODY * k))
    fs_note = int(round(FS_SMALL * k))
    font, font_b, font_n = load_font(fs), load_font(fs), load_font(fs_note)
    lw = max(2, int(round(2.5 * k)))
    r = int(fs * 0.85)
    boxes = spec.get("boxes", [])
    stroke = tuple(int(spec["stroke"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) if spec.get("stroke") else NAVY

    d0 = ImageDraw.Draw(im)
    est_w = max((d0.textlength(b.get("label", ""), font=font) for b in boxes), default=0) + r * 2 + fs
    per_row = max(1, min(3 if len(boxes) > 4 else max(1, len(boxes)), int((W - 2 * fs) // max(est_w, 1))))
    rows = (len(boxes) + per_row - 1) // per_row
    line_h = int(fs * 1.7)
    legend_h = int(line_h * (rows + (1 if spec.get("title") else 0)) + (fs_note * 1.9 if spec.get("note") else 0) + fs)
    canvas = Image.new("RGB", (W, H + legend_h), (255, 255, 255))
    canvas.paste(im, (0, 0))
    d = ImageDraw.Draw(canvas)

    for i, b in enumerate(boxes, 1):
        x, y, w, h = b["x"] * W, b["y"] * H, b["w"] * W, b["h"] * H
        d.rectangle([x, y, x + w, y + h], outline=stroke, width=lw)
        cx, cy = x + r + lw, y + r + lw
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=NAVY, outline=(255, 255, 255), width=max(1, lw // 2))
        t = str(i)
        tw = d.textlength(t, font=font_b)
        d.text((cx - tw / 2, cy - fs * 0.62), t, fill=(255, 255, 255), font=font_b)

    y = H + fs * 0.6
    x_pad = int(fs)
    if spec.get("title"):
        d.text((x_pad, y), spec["title"], fill=NAVY_D, font=font_b)
        y += line_h
    col_w = (W - 2 * x_pad) / per_row
    for i, b in enumerate(boxes, 1):
        col, row = (i - 1) % per_row, (i - 1) // per_row
        bx = x_pad + col * col_w
        by = y + row * line_h
        d.ellipse([bx, by + 2, bx + r * 2, by + 2 + r * 2], fill=NAVY)
        t = str(i); tw = d.textlength(t, font=font_b)
        d.text((bx + r - tw / 2, by + 2 + r - fs * 0.62), t, fill=(255, 255, 255), font=font_b)
        d.text((bx + r * 2 + fs * 0.5, by), b["label"], fill=INK, font=font)
    y += rows * line_h
    if spec.get("note"):
        d.text((x_pad, y), spec["note"], fill=GREY, font=font_n)
    out = Path(spec.get("out") or src.with_name(src.stem + "_annotated.png")).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    print(f"[OK] {out} ({canvas.size[0]}x{canvas.size[1]}, {len(boxes)} 个标注, 槽 {slot} → 图例 {fs}px 原图 = {FS_BODY}px 版面)", file=sys.stderr)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="官方实物图打编号框 + 图例 (v2.4 字阶按槽宽倒算)")
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--slot", default="full", choices=list(SLOT_W), help="这张图在版式里占的槽 (决定图例字号)")
    ap.add_argument("--image"); ap.add_argument("--out"); ap.add_argument("--title"); ap.add_argument("--note")
    ap.add_argument("--box", action="append", default=[], help='"x,y,w,h,标签" (0–1 比例)')
    a = ap.parse_args()
    if a.spec:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    else:
        if not a.image:
            ap.error("需要 spec.json 或 --image")
        spec = {"image": a.image, "out": a.out, "title": a.title, "note": a.note, "boxes": []}
        for s in a.box:
            x, y, w, h, lab = s.split(",", 4)
            spec["boxes"].append({"x": float(x), "y": float(y), "w": float(w), "h": float(h), "label": lab})
    annotate(spec, slot=a.slot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
