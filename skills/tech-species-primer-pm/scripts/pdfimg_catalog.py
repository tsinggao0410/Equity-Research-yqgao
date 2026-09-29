#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""招股书 / 年报 / 问询回复里的图批量抽出来并建目录,供各章挑官方图(工艺流程、产品、产能、同行对比、产业链)。

用法:python3 pdfimg_catalog.py [--root R] --tag IPO path/to/招股书.pdf [--pages 100-160] [--min-px 300]
                                [--render-drawings 80] [--zoom 2]
  输出:R/work/pdfimg/<tag>/p012_x345.png(内嵌位图,按 xref 去重)、page012_render.png(矢量图多的页整页渲染),
        目录 R/work/pdfimg/catalog.json 追加/替换该 tag 的记录:
        {src:tag, page, file, w, h, caps:[页内「图 x / 表 x / 示意图 / 流程图」行], render?:true, drawings?:n, pdf}
  挑图:先看 catalog 的 caps 和页码,再用 Read 看图;矢量页需要裁剪时用 PIL 按比例裁。页码一律是 PDF 页码。
  过滤:宽或高 < --min-px 的位图(logo、页眉、图标)不收;同一 xref 在多页重复(水印、页眉图)只收一次。
"""
import argparse
import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _card import find_root  # noqa: E402

CAP_RE = re.compile(r"^\s*((图|表)\s*[0-9一二三四五六七八九十]+[-－.．:：、\s]|.{0,30}(示意图|流程图|工艺流程|工序|结构图|架构图|拓扑|原理图|产业链|图例|产品图|实物图|布局图|分布图|对比))")

ap = argparse.ArgumentParser()
ap.add_argument("pdf")
ap.add_argument("--tag", required=True, help="来源简称,如 IPO / AR2025 / IR1(用作子目录名)")
ap.add_argument("--root")
ap.add_argument("--pages", help="只处理这些页,如 100-160,200")
ap.add_argument("--min-px", type=int, default=300)
ap.add_argument("--render-drawings", type=int, default=80, help="页内矢量绘图对象 ≥ 该数且无大位图时整页渲染")
ap.add_argument("--zoom", type=float, default=2.0)
a = ap.parse_args()

R = find_root(a.root)
out = R / "work" / "pdfimg" / a.tag
out.mkdir(parents=True, exist_ok=True)
cat_p = R / "work" / "pdfimg" / "catalog.json"
cat = json.loads(cat_p.read_text(encoding="utf-8")) if cat_p.exists() else []
cat = [c for c in cat if c.get("src") != a.tag]

d = fitz.open(a.pdf)
sel = None
if a.pages:
    sel = set()
    for part in a.pages.split(","):
        lo, _, hi = part.partition("-")
        sel.update(range(int(lo), int(hi or lo) + 1))
seen, recs = set(), []
for i, pg in enumerate(d):
    pno = i + 1
    if sel and pno not in sel:
        continue
    caps = [ln.strip()[:80] for ln in pg.get_text().splitlines() if len(ln.strip()) <= 60 and CAP_RE.match(ln)][:6]
    big = 0
    for info in pg.get_images(full=True):
        xref, w, h = info[0], info[2], info[3]
        if xref in seen or w < a.min_px or h < a.min_px:
            continue
        seen.add(xref)
        try:
            pix = fitz.Pixmap(d, xref)
            if pix.n - pix.alpha >= 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            fn = "p%03d_x%d.png" % (pno, xref)
            pix.save(out / fn)
        except Exception as e:  # noqa: BLE001
            print("skip p%d xref %d: %s" % (pno, xref, e))
            continue
        big += 1
        recs.append(dict(src=a.tag, page=pno, file="%s/%s" % (a.tag, fn), w=pix.width, h=pix.height, caps=caps, pdf=str(Path(a.pdf).name)))
    try:
        nd = len(pg.get_drawings())
    except Exception:  # noqa: BLE001
        nd = 0
    if nd >= a.render_drawings and big == 0:
        fn = "page%03d_render.png" % pno
        pix = pg.get_pixmap(matrix=fitz.Matrix(a.zoom, a.zoom))
        pix.save(out / fn)
        recs.append(dict(src=a.tag, page=pno, file="%s/%s" % (a.tag, fn), w=pix.width, h=pix.height, caps=caps,
                         render=True, drawings=nd, pdf=str(Path(a.pdf).name)))
cat += recs
cat_p.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
print("%s:%d 页,收图 %d(位图 %d、整页渲染 %d)→ %s;catalog 共 %d 条" % (
    a.tag, len(d), len(recs), sum(1 for r in recs if not r.get("render")), sum(1 for r in recs if r.get("render")),
    out, len(cat)))
