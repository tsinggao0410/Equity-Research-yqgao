#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本 skill 打成可上传 claude.ai(设置 → Customize → Skills)的包:<out>/<skill 目录名>.skill 和同内容的 .zip
(基金经理版即 tech-species-primer-pm.skill)。

用法:python3 pack_skill.py [--out ~/Desktop] [--no-test]
检查(claude.ai 上传要求,contradiction-library 打包时核过):包内顶层目录名 = skill 名、只有一个 SKILL.md、frontmatter 有
name/description、文件数 ≤ 200、解压后 < 30MB、文件名全是 ASCII(中文文件名上传会失败)。跳过 __pycache__、.DS_Store、.img_cache。
自测:解到临时目录,跑渲染器回归测试(含基金经理版 test_render_pm.py:两份写法样例须过 --pm)、渲染 fixture、
new_card → merge_card 冒烟(零章与技术白话章骨架带 TODO,--gate --pm 应退出 3),确认包内路径自洽、不依赖源目录。
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
NAME = SKILL.name
MAX_FILES, MAX_BYTES = 200, 30 * 1024 * 1024
SKIP_DIRS = {"__pycache__", ".img_cache", ".git"}
SKIP_FILES = {".DS_Store"}


def collect():
    files = []
    for root, dirs, fs in os.walk(SKILL):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(fs):
            if f in SKIP_FILES or f.endswith(".pyc"):
                continue
            files.append(Path(root) / f)
    return files


def check(files):
    errs = []
    s = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", s, re.S)
    if not m or not re.search(r"^name:\s*%s\s*$" % re.escape(NAME), m.group(1), re.M) or "description:" not in m.group(1):
        errs.append("SKILL.md frontmatter 缺 name(须等于目录名 %s)或 description" % NAME)
    else:
        d = re.search(r'^description:\s*"?(.*?)"?\s*$', m.group(1), re.M).group(1)
        if len(d) > 1024 or "<" in d or ">" in d:
            errs.append("description 超 1024 字符或含尖括号(%d)" % len(d))
    if sum(1 for f in files if f.name == "SKILL.md") != 1:
        errs.append("SKILL.md 不止一个")
    bad = [str(f.relative_to(SKILL)) for f in files if not str(f.relative_to(SKILL)).isascii()]
    if bad:
        errs.append("非 ASCII 文件名:%s" % bad[:5])
    total = sum(f.stat().st_size for f in files)
    if len(files) > MAX_FILES:
        errs.append("文件数 %d > %d" % (len(files), MAX_FILES))
    if total >= MAX_BYTES:
        errs.append("解压后 %.1fMB ≥ 30MB" % (total / 1e6))
    return errs, total


def selftest(pkg):
    with tempfile.TemporaryDirectory() as t:
        zipfile.ZipFile(pkg).extractall(t)
        S = Path(t) / NAME
        sc = S / "scripts"
        py = sys.executable
        steps = [
            ("回归测试", [py, str(sc / "test_render_r3.py")], None),
            ("基金经理版回归测试", [py, str(sc / "test_render_pm.py")], None),
            ("渲染 fixture", [py, str(sc / "render_report_v32.py"), str(S / "assets/fixture/fixture.md"),
                             "--out", str(Path(t) / "fixture.html"), "--offline"], None),
            ("new_card", [py, str(sc / "new_card.py"), "--root", str(Path(t) / "card"), "--name", "测试公司",
                          "--code", "000001.SZ", "--date", "2026-01-01"], None),
        ]
        for label, cmd, cwd in steps:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
            if r.returncode != 0:
                return "%s 失败:%s" % (label, (r.stdout + r.stderr)[-800:])
        R = Path(t) / "card"
        (R / "parts" / "01_公司总览.md").write_text(
            "## 一、公司总览\n\n> [!lead] 冒烟测试。\n\n测试正文。\n\n```chart\n"
            '{"id":"c1_t","title":"图 1-1 测试","type":"bar","categories":["2024","2025"],'
            '"series":[{"name":"收入","data":[1,2]}],"unit":"亿元","source":"来源:测试"}\n```\n', encoding="utf-8")
        r = subprocess.run([py, str(sc / "merge_card.py"), "--root", str(R), "--no-gate"], capture_output=True, text=True)
        if r.returncode != 0 or not (R / "测试公司-业务认知-基金经理版.html").exists():
            return "merge_card --no-gate 失败:%s" % (r.stdout + r.stderr)[-800:]
        r = subprocess.run([py, str(sc / "merge_card.py"), "--root", str(R)], capture_output=True, text=True)
        if r.returncode != 3:
            return "merge_card --gate 应因篇幅不足退出 3,实际 %d:%s" % (r.returncode, (r.stdout + r.stderr)[-800:])
        if "残留 TODO" not in (r.stdout + r.stderr):
            return "merge_card 没有按 edition=pm 加 --pm 验收(应报零章 / 技术白话章骨架残留 TODO)"
        html = (R / "测试公司-业务认知-基金经理版.html").read_text(encoding="utf-8")
        if "echarts" not in html.lower():
            return "HTML 未内联 ECharts"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path.home() / "Desktop"))
    ap.add_argument("--no-test", action="store_true")
    a = ap.parse_args()
    files = collect()
    errs, total = check(files)
    if errs:
        sys.exit("打包检查未过:\n  " + "\n  ".join(errs))
    out = Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    pkg = out / (NAME + ".skill")
    with zipfile.ZipFile(pkg, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            z.write(f, (Path(NAME) / f.relative_to(SKILL)).as_posix())
    zp = out / (NAME + ".zip")
    zp.write_bytes(pkg.read_bytes())
    print("打包:%d 个文件,解压 %.2fMB,包 %.2fMB → %s(另有同内容 %s)" % (
        len(files), total / 1e6, pkg.stat().st_size / 1e6, pkg, zp.name))
    if not a.no_test:
        e = selftest(pkg)
        if e:
            sys.exit("自测未过:" + e)
        print("自测通过:回归测试(含基金经理版)、fixture 渲染、new_card → merge_card(--no-gate 出 HTML;--gate --pm 按篇幅不足与 TODO 退出 3)")


if __name__ == "__main__":
    main()
