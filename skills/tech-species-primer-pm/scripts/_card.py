#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""卡片工作目录的公共工具:找卡根目录(含 card.json 的目录)、读 card.json、skill 自身路径。

卡根目录 R 的约定(new_card.py 建好):
    R/card.json            卡的元数据(名称、代码、日期、目录分组、验收门槛、照抄检查背景语料)
    R/materials.md         材料清单            R/questions.md   必答问题清单
    R/parts/NN_章名.md     各章正文;NN_facts.md 数字台账;NN_gaps.md 口径冲突与缺口
    R/images/cN_*.jpg|png|svg                  图片(文件名以章号开头)
    R/sources/{text,cninfo,reports,alphapai,market,peers,web}/   原始材料与按页文本
    R/work/{00_header.md,BRIEF.md,facts_spine.md,stats.json,test/,shots/,pdfimg/}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent          # skill 根目录
SCRIPTS = SKILL / "scripts"
RENDERER = SCRIPTS / "render_report_v32.py"
REF_TEXT = SKILL / "assets" / "reference" / "ref_text.txt"


def find_root(arg: str | None = None) -> Path:
    """--root 给了就用它;否则从当前目录往上找第一个含 card.json 的目录。"""
    if arg:
        r = Path(arg).expanduser().resolve()
        if not r.is_dir():
            sys.exit("卡根目录不存在: %s" % r)
        return r
    here = Path.cwd().resolve()
    for d in [here, *here.parents]:
        if (d / "card.json").is_file():
            return d
    sys.exit("找不到 card.json:请在卡根目录里运行,或加 --root <卡根目录>(先用 new_card.py 建目录)")


def load_card(root: Path) -> dict:
    p = root / "card.json"
    if not p.is_file():
        sys.exit("缺 %s(先用 new_card.py 建目录)" % p)
    return json.loads(p.read_text(encoding="utf-8"))
