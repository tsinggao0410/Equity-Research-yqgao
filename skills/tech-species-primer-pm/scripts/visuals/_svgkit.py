#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_svgkit.py (v2.4) — Mode B 自绘图的公共底座 (黑白灰 + 海军蓝, 无衬线, 自包含 SVG)。
draw_bars / draw_waterfall / draw_flow / draw_moneyflow / draw_position_map / draw_structure 共用;不单独运行。

v2.4 字阶纪律 (铁律 18):
  * 全卡只有四个字号: 标题 24 / 章题 18 / 正文 15 / 次级 13。图内文字只用后两档:
      FS_BODY  15 = 标签、类目、图例、框内文字、表头   (= HTML 正文 / 表格 / 图 caption)
      FS_SMALL 13 = 轴刻度、数值标签、备注、副题、脚注 (= HTML 来源行 / 说明行)
  * 图按它在版式里的**槽宽**画, 渲染后 1:1 不缩放: --slot full 1108 / half 543 / third 354 (见 SLOT_W)。
    渲染器 render_primer_html.py 的页宽 1180 − 左右 36 = 1108; 并排 gap 22 → half = (1108−22)/2, third = (1108−44)/3。
  * 图内**不画标题** (渲染器的「图 n · 论断句」caption 就是标题); spec 的 title 保留给 caption / 独立看图 (--title 才画)。
    subtitle (单位 / 口径) 画在图顶, footnote (算法 / 口径说明) 画在图底, 都是 FS_SMALL 灰字, 自动换行。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

NAVY = ["#0d2237", "#16395a", "#2f5f8a", "#7ba0c2", "#d6e1ea"]
INK = "#222222"
GREY = "#6b6b6b"
GREY2 = "#9a9a9a"
LINE = "#bdbdbd"
LIGHT = "#f2f2f2"
GREEN = "#2e6b52"
RED = "#9e3b33"
FONT = "-apple-system, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif"

# ---- 字阶 (与 render_primer_html.py 的 CSS 一一对应) ----
FS_BODY = 15
FS_SMALL = 13
LH_BODY = 21      # 行距
LH_SMALL = 18
ALLOWED_FS = {FS_BODY, FS_SMALL}

# ---- 槽宽 (与 render_primer_html.py 的版式一一对应) ----
PAGE_W, PAGE_PAD, GRID_GAP = 1180, 36, 22
CONTENT_W = PAGE_W - 2 * PAGE_PAD                      # 1108
SLOT_W = {"full": CONTENT_W, "half": (CONTENT_W - GRID_GAP) // 2, "third": (CONTENT_W - 2 * GRID_GAP) // 3}  # 1108 / 543 / 355
PAD = 24          # 图内边距


def slot_width(slot: str) -> float:
    if slot not in SLOT_W:
        raise SystemExit(f"[X] --slot 只能是 {list(SLOT_W)} (单张 full, 两张并排 half, 三张并排 third)")
    return float(SLOT_W[slot])


def cw(ch: str) -> float:
    """字符宽 (em): CJK = 1, 其他 ≈ 0.56。"""
    return 1.0 if ord(ch) > 0x2E80 else 0.56


def text_w(s: str, size: float = FS_BODY) -> float:
    """估算文字像素宽。"""
    return sum(cw(c) for c in str(s)) * size


def chars_for(px: float, size: float = FS_BODY) -> int:
    """px 像素里能放几个 CJK 字宽 (wrap() 的 max_chars)。"""
    return max(1, int(px / size))


def svg_open(width: float, height: float) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
            f'viewBox="0 0 {width:.0f} {height:.0f}" font-family="{FONT}" style="font-variant-numeric:tabular-nums">'
            f'<rect width="{width:.0f}" height="{height:.0f}" fill="#ffffff"/>')


def text(x, y, s, size=FS_BODY, fill=INK, anchor="start", weight="400", extra="") -> str:
    if size not in ALLOWED_FS:
        raise ValueError(f"字号 {size} 不在字阶 {sorted(ALLOWED_FS)} 里 (铁律 18)")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" {extra}>{escape(str(s))}</text>')


def fit(s: str, px: float, size: float = FS_BODY) -> str:
    """把一行文字截到 px 像素以内, 超出加「…」。"""
    w, out = 0.0, ""
    for ch in str(s):
        w += cw(ch) * size
        if w > px - size * 0.8:
            return out.rstrip() + "…"
        out += ch
    return out


def head_block(spec: dict, width: float, y: float, with_title: bool = False) -> tuple[str, float]:
    """图顶: 可选标题 (FS_BODY 600 海军蓝) + 副题 (FS_SMALL 灰, 自动换行)。返回 (svg, 下一段起始 y)。"""
    out: list[str] = []
    if with_title and spec.get("title"):
        for ln in wrap(spec["title"], chars_for(width - 2 * PAD, FS_BODY)):
            y += LH_BODY
            out.append(text(PAD, y, ln, size=FS_BODY, weight="600", fill=NAVY[0]))
        y += 2
    if spec.get("subtitle"):
        for ln in wrap(spec["subtitle"], chars_for(width - 2 * PAD, FS_SMALL)):
            y += LH_SMALL
            out.append(text(PAD, y, ln, size=FS_SMALL, fill=GREY))
        y += 2
    return "".join(out), y


def foot_lines(spec: dict, width: float, no_footnote: bool = False) -> list[str]:
    if no_footnote or not spec.get("footnote"):
        return []
    return wrap(spec["footnote"], chars_for(width - 2 * PAD, FS_SMALL))


def foot_height(lines: list[str]) -> float:
    return (len(lines) * LH_SMALL + 6) if lines else 0.0


def foot_block(lines: list[str], height: float) -> str:
    """脚注贴着图底画 (先用 foot_height 把高度算进 height)。"""
    if not lines:
        return ""
    y0 = height - 8 - (len(lines) - 1) * LH_SMALL
    return "".join(text(PAD, y0 + i * LH_SMALL, ln, size=FS_SMALL, fill=GREY) for i, ln in enumerate(lines))


def wrap(s: str, max_chars: int) -> list[str]:
    """中英文混排的粗略换行:按字符宽度 (CJK=1, 其他=0.56) 切。显式 \\n 优先。"""
    lines: list[str] = []
    for para in str(s).replace("\\n", "\n").split("\n"):
        # 切成「词」:连续拉丁字符/数字算一个词, 每个 CJK 字算一个词, 空格是可断点
        tokens = re.findall(r"[A-Za-z0-9$%.,:/+\-()]+|\s+|.", para)
        cur, w = "", 0.0
        for tk in tokens:
            tw = sum(cw(c) for c in tk)
            if w + tw > max_chars and cur.strip():
                lines.append(cur.rstrip()); cur, w = "", 0.0
                if tk.isspace():
                    continue
            if tw > max_chars:  # 超长单词硬切
                for ch in tk:
                    if w + cw(ch) > max_chars and cur:
                        lines.append(cur); cur, w = "", 0.0
                    cur += ch; w += cw(ch)
                continue
            cur += tk; w += tw
        lines.append(cur.rstrip())
    return lines


def fmt_num(v: float, unit: str = "", digits: int | None = None) -> str:
    if v is None:
        return "n/a"
    av = abs(v)
    if digits is None:
        digits = 0 if av >= 100 else (1 if av >= 10 else 2)
    s = f"{v:,.{digits}f}"
    return f"{s}{unit}" if unit else s


def slug(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z一-鿿]+", "_", s).strip("_")


# ---- 命令行 (六个 draw_*.py 共用) ----
def cli(desc: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("spec", help="规格 JSON")
    ap.add_argument("--out", required=True, help="输出 SVG 路径")
    ap.add_argument("--slot", default="full", choices=list(SLOT_W),
                    help="图在版式里占的槽: full 单张 1108px / half 两张并排 543px / third 三张并排 354px (默认 full)")
    ap.add_argument("--title", action="store_true", help="把 spec.title 画进图里 (默认不画: 渲染器的「图 n」caption 就是标题)")
    ap.add_argument("--no-footnote", action="store_true", help="不画 spec.footnote")
    return ap


def run(desc: str, render) -> int:
    """标准入口: 读 spec → render(spec, slot, with_title, no_footnote) → 写 SVG。"""
    a = cli(desc).parse_args()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    svg = render(spec, slot=a.slot, with_title=a.title, no_footnote=a.no_footnote)
    out = Path(a.out).expanduser(); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    w = re.search(r'width="(\d+)"', svg).group(1)
    print(f"[OK] SVG → {out} (槽 {a.slot} {w}px, 字号 {sorted(ALLOWED_FS)})", file=sys.stderr)
    return 0
