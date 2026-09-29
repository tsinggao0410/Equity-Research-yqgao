#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
localize_pdf_figure.py (v2.4.2, 铁律 22) — 把 PDF 里的日文 / 英文图表**本地化成中文**后再进卡。
PDF 里的文字是矢量的, 能精确拿到每一行的文字与位置, 所以不用 OCR: 抽出来 → 你(Agent)填中文 → 覆盖回去。

两步:
  1) extract: 把某页某个区域里的文字行抽成 JSON(text / bbox / size), 术语表里能对上的先自动填 zh, 其余 zh 留空等你填。
     python localize_pdf_figure.py extract --pdf ir/FY25_JP_Presentation.pdf --page 30 --bbox 40,80,920,520 \\
         --glossary ../references/glossary_jp_zh.json --out specs/loc_p30.json
     (--bbox 省略 = 整页;单位是 PDF 点;先用 fetch_visuals.py --pdf 或 PyMuPDF 看页面定包围盒)
  2) 你打开 loc_p30.json, 把每条的 "zh" 填成中文(数字、英文缩写、品牌英文名可以留空 = 不改);
     品牌名按卡的实体消歧表译(スシロー → 寿司郎), 单位按术语表(億円 → 亿日元)。
  3) apply: 按 bbox 把原文抹白、写上中文, 出 PNG 进卡。
     python localize_pdf_figure.py apply --spans specs/loc_p30.json --out images/deck_fy25_p30_zh.png [--zoom 3] [--font /System/Library/Fonts/PingFang.ttc]

纪律:
  * 段落型页面用默认的合并 (整句翻再自动换行);项目符号列表、表格、图例密集的页面用 --no-merge 逐行翻, 位置才对得上。
  * 只翻文字, 不改数字; 译不准的宁可留原文 + 在图题里解释, 不要猜。
  * 出图后 Read 一眼: 中文是否盖住了原文、有没有溢出到相邻格子;溢出就把 zh 缩短或分两行(zh 里用 \\n)。
  * 图题写中文论断句, 来源行写「业绩说明会材料 FY25 第 30 页(日文原版, 文字已译)」。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    print("[X] 需要 PyMuPDF: python3 -m pip install --user pymupdf", file=sys.stderr); raise SystemExit(1)

KANA = re.compile(r"[\u3040-\u30ff]")
CJK = re.compile(r"[\u3400-\u9fff]")
FONT_CANDIDATES = ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc",
                   "/System/Library/Fonts/STHeiti Medium.ttc", "/Library/Fonts/Microsoft YaHei.ttf",
                   "C:/Windows/Fonts/msyh.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"]


def needs_translation(s: str) -> bool:
    """有假名或汉字才需要翻;纯数字 / 纯 ASCII 不翻。"""
    return bool(KANA.search(s) or CJK.search(s))


def auto_fill(text: str, gl: dict) -> str:
    """术语表精确命中就自动填;否则用 patterns 只替换单位, 剩下留给人。"""
    t = text.strip()
    terms = gl.get("terms", {})
    if t in terms:
        return terms[t]
    out = t
    for pat, rep in gl.get("patterns", []):
        out = re.sub(pat, rep, out)
    # 整词替换(长词优先, 避免「売上」吃掉「売上高」)
    for k in sorted(terms, key=len, reverse=True):
        if k in out and len(k) >= 2:
            out = out.replace(k, terms[k])
    return out if (out != t and not KANA.search(out)) else ""


def extract(a) -> int:
    doc = fitz.open(a.pdf)
    pg = doc[a.page - 1]
    clip = fitz.Rect(*[float(v) for v in a.bbox.split(",")]) if a.bbox else pg.rect
    gl = json.loads(Path(a.glossary).read_text(encoding="utf-8")) if a.glossary and Path(a.glossary).exists() else {}
    d = pg.get_text("dict", clip=clip)
    rows = []
    for b in d.get("blocks", []):
        for ln in b.get("lines", []):
            spans = [s for s in ln.get("spans", []) if s.get("text", "").strip()]
            if not spans:
                continue
            text = "".join(s["text"] for s in spans)
            if not needs_translation(text):
                continue
            x0 = min(s["bbox"][0] for s in spans); y0 = min(s["bbox"][1] for s in spans)
            x1 = max(s["bbox"][2] for s in spans); y1 = max(s["bbox"][3] for s in spans)
            size = max(s.get("size", 10) for s in spans)
            color = spans[0].get("color", 0)
            rows.append({"text": text, "bbox": [x0, y0, x1, y1], "size": size, "color": f"#{color:06x}"})
    # 把同一段落里被 PDF 拆开的相邻行合并 (左边对齐 + 行距很近 + 字号一样), 这样能整句翻译再自动换行回去
    if not a.no_merge:
        merged = []
        for r in sorted(rows, key=lambda r: (round(r["bbox"][1] / 4), r["bbox"][0])):
            hit = None
            for m in reversed(merged[-8:]):          # 两栏排版时上一行不一定是同栏, 往回找同栏的段
                same_size = abs(m["size"] - r["size"]) <= 1.0
                left_aligned = abs(m["bbox"][0] - r["bbox"][0]) <= 1.5 * r["size"]
                vgap = r["bbox"][1] - m["bbox"][3]
                ended = m["text"].rstrip().endswith(("。", "．", "."))      # 上一段已经句号收尾 → 是新段落, 不并
                bullet = r["text"].lstrip()[:1] in "=■◼•・*＊(（【「-"           # 新行以符号开头 → 是列表项, 不并
                if same_size and left_aligned and -0.3 * r["size"] <= vgap <= 0.7 * r["size"] and not ended and not bullet and m.get("lines", 1) < a.max_merge:
                    hit = m; break
            if hit is not None:
                m = hit
                m["text"] = (m["text"].rstrip() + r["text"].lstrip()) if KANA.search(m["text"] + r["text"]) else (m["text"] + " " + r["text"])
                m["bbox"] = [min(m["bbox"][0], r["bbox"][0]), min(m["bbox"][1], r["bbox"][1]), max(m["bbox"][2], r["bbox"][2]), max(m["bbox"][3], r["bbox"][3])]
                m["lines"] = m.get("lines", 1) + 1
                continue
            merged.append(dict(r, lines=1))
        rows = merged
    for i, r in enumerate(rows):
        r["id"] = f"t{i+1:03d}"; r["zh"] = auto_fill(r["text"], gl)
        r["bbox"] = [round(v, 1) for v in r["bbox"]]; r["size"] = round(r["size"], 1)
        r.setdefault("lines", 1)
    payload = {"pdf": str(Path(a.pdf).resolve()), "page": a.page, "clip": [round(v, 1) for v in clip],
               "note": "把每条 zh 填成中文;留空 = 保留原文不改;zh 写 ␡ (或 erase:true) = 只抹掉不写字;zh 里可用 \\n 分两行", "rows": rows}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    n_auto = sum(1 for r in rows if r["zh"])
    print(f"[OK] 抽出 {len(rows)} 行需要翻译的文字 → {a.out}(术语表自动填了 {n_auto} 行, 剩 {len(rows)-n_auto} 行等你填)", file=sys.stderr)
    for r in rows:
        print(f"   {r['id']}  {r['text'][:40]!r:<44} → {r['zh'][:30]!r}", file=sys.stderr)
    return 0


def _font(size: int, path: str | None):
    from PIL import ImageFont
    cands = ([path] if path else []) + FONT_CANDIDATES
    for p in cands:
        if p and Path(p).exists():
            try:
                return ImageFont.truetype(p, size=max(size, 6))
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


def apply(a) -> int:
    from PIL import Image, ImageDraw
    spec = json.loads(Path(a.spans).read_text(encoding="utf-8"))
    doc = fitz.open(spec["pdf"]); pg = doc[spec["page"] - 1]
    clip = fitz.Rect(*spec["clip"]); Z = float(a.zoom)
    pix = pg.get_pixmap(matrix=fitz.Matrix(Z, Z), clip=clip, alpha=False)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    d = ImageDraw.Draw(im)
    n = 0
    for r in spec["rows"]:
        zh = (r.get("zh") or "").strip()
        erase = bool(r.get("erase")) or zh == "␡"        # 只抹掉不写字 (合并后多出来的碎行、已并进别处的尾巴)
        if not zh and not erase:
            continue
        x0, y0, x1, y1 = [(v - (clip.x0 if i % 2 == 0 else clip.y0)) * Z for i, v in enumerate(r["bbox"])]
        pad = 0.0 if r["size"] < 11 else min(1.5 * Z, 0.12 * r["size"] * Z)   # 小标签不垫, 别把旁边的数字抹掉
        zh = zh.replace("◼", "■").replace("▪", "■").replace("●", "•")   # PingFang 没有的方块符号换成有的
        # 抹白:略大于原文框, 盖住原文
        d.rectangle([x0 - pad, y0 - pad, x1 + pad, y1 + pad], fill=(255, 255, 255))
        if erase:
            n += 1; continue
        explicit = zh.split("\\n") if "\\n" in zh else zh.split("\n")
        box_w, box_h = (x1 - x0), (y1 - y0)
        n_src = max(1, int(r.get("lines", 1)))
        fs = int(r["size"] * Z * 0.92)

        def wrap_to(width: float, font) -> list[str]:
            out_lines = []
            for para in explicit:
                cur = ""
                for ch in para:
                    if d.textlength(cur + ch, font=font) > width and cur:
                        out_lines.append(cur); cur = ch
                    else:
                        cur += ch
                out_lines.append(cur)
            return out_lines

        # 先按原字号自动换行;行数超过原段行数 (或高度超框) 就缩字号, 最小缩到 60%
        while True:
            f = _font(fs, a.font)
            lines = wrap_to(box_w * 1.04, f)
            if (len(lines) <= n_src and fs * len(lines) * 1.05 <= box_h * 1.35) or fs <= int(r["size"] * Z * 0.6):
                break
            fs -= 1
        f = _font(fs, a.font)
        col = r.get("color", "#222222")
        try:
            rgb = tuple(int(col.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        except Exception:  # noqa: BLE001
            rgb = (34, 34, 34)
        if rgb == (255, 255, 255):
            rgb = (34, 34, 34)
        # 行距: 文字行数不超过原段行数时沿用原段的行距 (对齐原来的项目符号), 否则紧排
        line_h = max(fs * 1.05, box_h / n_src) if len(lines) <= n_src else fs * 1.05
        y = y0 + (box_h - line_h * len(lines)) / 2 if len(lines) < n_src else y0
        for s in lines:
            d.text((x0, y), s, fill=rgb, font=f); y += line_h
        n += 1
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    im.save(a.out)
    print(f"[OK] {a.out} ({im.width}x{im.height}), 覆盖了 {n} 行中文;Read 一眼确认没有溢出", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="PDF 图表本地化: extract → 填 zh → apply")
    sp = ap.add_subparsers(dest="cmd", required=True)
    e = sp.add_parser("extract"); e.add_argument("--pdf", required=True); e.add_argument("--page", type=int, required=True)
    e.add_argument("--bbox", default=None, help="x0,y0,x1,y1 (PDF 点), 省略 = 整页"); e.add_argument("--glossary", default=None)
    e.add_argument("--out", required=True); e.add_argument("--no-merge", action="store_true", help="不合并相邻行 (项目符号列表、表格页用这个, 逐行翻)")
    e.add_argument("--max-merge", type=int, default=4, help="一段最多合并几行 (默认 4)")
    p = sp.add_parser("apply"); p.add_argument("--spans", required=True); p.add_argument("--out", required=True)
    p.add_argument("--zoom", default=3.0); p.add_argument("--font", default=None)
    a = ap.parse_args()
    return extract(a) if a.cmd == "extract" else apply(a)


if __name__ == "__main__":
    raise SystemExit(main())
