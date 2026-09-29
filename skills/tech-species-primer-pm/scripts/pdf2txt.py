#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 PDF 按页抽成文本:R/sources/text/<同名>.txt,页标记 `=== pN ===`(N = PDF 页码,从 1 起)。
全卡统一写 PDF 页码(A 股招股书常见「印刷页码 = PDF 页码 − 1」,不要混用)。

用法:python3 pdf2txt.py [--root R] [--out-dir DIR] [--force] a.pdf [b.pdf ...]
  已存在且非空则跳过;--force 重抽。抽不出字(扫描件)的页会在汇总里报「空页」,需要 OCR 或换原件。
"""
import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _card import find_root  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("pdfs", nargs="+")
ap.add_argument("--root")
ap.add_argument("--out-dir")
ap.add_argument("--force", action="store_true")
a = ap.parse_args()
out_dir = Path(a.out_dir).resolve() if a.out_dir else find_root(a.root) / "sources" / "text"
out_dir.mkdir(parents=True, exist_ok=True)
for x in a.pdfs:
    p = Path(x).resolve()
    out = out_dir / (p.stem + ".txt")
    if out.exists() and out.stat().st_size > 0 and not a.force:
        print("skip", out.name)
        continue
    d = fitz.open(p)
    empty = 0
    with open(out, "w", encoding="utf-8") as f:
        for i, pg in enumerate(d):
            t = pg.get_text()
            empty += not t.strip()
            f.write("=== p%d ===\n%s\n" % (i + 1, t))
    print("%s  %d 页%s → %s" % (p.name, len(d), (",空页 %d" % empty) if empty else "", out.name))
