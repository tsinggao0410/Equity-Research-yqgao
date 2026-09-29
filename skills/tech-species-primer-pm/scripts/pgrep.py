#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 R/sources/text/*.txt 里按正则找句子,给出 PDF 页码(=== pN ===)。取数、核数、写台账都用它定位原页。

用法:python3 pgrep.py [--root R] [-C 行数] <文件名或glob,不带 .txt> '<正则>'
  例:pgrep.py AR2025 '主营业务分产品'      pgrep.py '*招股*' '产能利用率' -C 2      pgrep.py '*' '前五名客户'
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _card import find_root  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("pattern")
ap.add_argument("-C", type=int, default=0)
ap.add_argument("--root")
ap.add_argument("--max", type=int, default=200, help="最多输出条数")
a = ap.parse_args()
T = find_root(a.root) / "sources" / "text"
files = sorted(T.glob(a.name + ".txt")) or sorted(T.glob("*" + a.name + "*.txt"))
if not files:
    sys.exit("没找到 %s/%s.txt" % (T, a.name))
pat = re.compile(a.pattern, re.I)
n = 0
for fp in files:
    L = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
    pg, pages = "?", []
    for line in L:
        m = re.match(r"=== ([ps]\d+) ===", line)
        if m:
            pg = m.group(1)
        pages.append(pg)
    for i, line in enumerate(L):
        if pat.search(line):
            s = " ".join(x.strip() for x in L[max(0, i - a.C): i + a.C + 1])
            print("%s [%s] %s" % (fp.stem if len(files) > 1 else "", pages[i], s[:600]))
            n += 1
            if n >= a.max:
                sys.exit("… 超过 %d 条,收窄正则或加 --max" % a.max)
