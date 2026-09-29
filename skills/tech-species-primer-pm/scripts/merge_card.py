#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并 parts → <out_stem>.md,渲染成同名 HTML,并跑 --gate(含照抄检查);基金经理版另跑 --pm。

用法:python3 merge_card.py [--root R] [--no-gate] [--lax] [--feishu]
  - 顺序:work/00_header.md + parts/NN_*.md(按 NN 排序,跳过 NN_facts.md / NN_gaps.md / NN_terms.md / 以 _ 开头的文件)。
  - 术语词典:parts 里没有 ```glossary 块时,把各章 NN_terms.md(术语台账,表头「术语 | 含义 | 可以理解为 | 投资相关性」)
    按章序合并去重,自动追加一章「附录、术语小词典」;同一术语多章都写了,取第一次出现的那条,冲突写进输出提示。
  - card.json 的 edition = "pm" 时加 --pm 验收,门槛取 plain{min_glossary, max_unexplained, ch0_min, ch0_max, ch0_max_acr,
    tech, allow}(DESIGN_pm.md §5)。
  - card.json 的 nav:{"02": "三大主业", ...} → 在该章前插入 <!-- nav: 组名 -->(目录分组)。
  - 渲染参数取 card.json 的 date、gate(min_cjk/min_figs/min_charts/min_visuals/min_tables)、ref_bg(照抄检查背景语料,
    相对 R 的路径列表,一般放年报/招股书按页文本,两份报告都转述公司原话时不算照抄)。
  - --feishu:另存一份 <feishu_name>.html(用户习惯命名「公司科普-YYMMDD」),上传飞书用。
退出码同渲染器:0 通过;2 有错误(缺图、JSON 错、外链残留);3 --gate 未达标。
"""
import argparse
import re
import shutil
import subprocess
import sys

from _card import REF_TEXT, RENDERER, find_root, load_card

ap = argparse.ArgumentParser()
ap.add_argument("--root")
ap.add_argument("--no-gate", action="store_true")
ap.add_argument("--lax", action="store_true")
ap.add_argument("--feishu", action="store_true")
a = ap.parse_args()
R = find_root(a.root)
card = load_card(R)
stem = card["out_stem"]
parts = sorted(p for p in (R / "parts").glob("[0-9][0-9]_*.md")
               if not re.search(r"_(facts|gaps|terms)\.md$", p.name))
if not parts:
    sys.exit("parts/ 里没有 NN_章名.md")
nav = card.get("nav") or {}
out = [(R / "work" / "00_header.md").read_text(encoding="utf-8").rstrip() + "\n"]
for p in parts:
    nn = p.name[:2]
    txt = re.sub(r"^<!--\s*nav:.*?-->\s*", "", p.read_text(encoding="utf-8").strip())
    if nn in nav:
        out.append("<!-- nav: %s -->\n" % nav[nn])
    out.append(txt + "\n")


def split_row(ln):
    t = ln.strip().strip("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", t)]


def collect_terms():
    """各章 NN_terms.md → glossary 块正文(去重,保留章序)。"""
    rows, seen, clash = [], {}, []
    for tp in sorted((R / "parts").glob("[0-9][0-9]_terms.md")):
        for ln in tp.read_text(encoding="utf-8").splitlines():
            t = ln.strip()
            if not t.startswith("|") or re.match(r"^\|?\s*:?-{2,}", t):
                continue
            c = (split_row(t) + ["", "", "", ""])[:4]
            if not c[0] or c[0] in ("术语", "名词"):
                continue
            key = re.split(r"\s+[/／]\s+", c[0])[0].strip().lower()
            if key in seen:
                if c[1] and c[1] != seen[key][1]:
                    clash.append("%s(%s 与先出现的写法不同,已取先出现的)" % (c[0], tp.name))
                continue
            seen[key] = c
            rows.append(" | ".join(x.replace("|", "\\|") for x in c))
    return rows, clash


has_gloss = any("```glossary" in x for x in out)
if card.get("edition") == "pm" and not has_gloss:
    trows, clash = collect_terms()
    if trows:
        out.append("<!-- nav: 附录 -->\n" if "附录" not in nav.values() else "")
        out.append("## 附录、术语小词典\n\n> [!lead] 正文中每章首次出现的术语可悬停(手机上点按)查看解释;"
                   "下表按章节出现顺序集中列出含义、类比与投资相关性。\n\n```glossary\n术语 | 含义 | 可以理解为 | 投资相关性\n%s\n```\n" % "\n".join(trows))
        print("术语词典:由 %d 份 NN_terms.md 合成 %d 条" % (len(list((R / "parts").glob("[0-9][0-9]_terms.md"))), len(trows)))
        for x in clash:
            print("术语冲突:", x)
md = R / (stem + ".md")
md.write_text("\n".join(out), encoding="utf-8")
print("merged %d parts → %s" % (len(parts), md.name))

g = card.get("gate") or {}
cmd = [sys.executable, str(RENDERER), str(md), "--out", str(R / (stem + ".html")),
       "--stats", str(R / "work" / "stats.json")]
if card.get("date"):
    cmd += ["--date", card["date"]]
if not a.no_gate:
    cmd += ["--gate", "--ref", str(REF_TEXT)]
    for k in ("min_cjk", "min_figs", "min_charts", "min_visuals", "min_tables"):
        if g.get(k) is not None:
            cmd += ["--" + k.replace("_", "-"), str(g[k])]
    bg = [str(R / x) for x in card.get("ref_bg") or [] if (R / x).exists()]
    if bg:
        cmd += ["--ref-bg", ",".join(bg)]
    if card.get("edition") == "pm":
        pl = card.get("plain") or {}
        cmd.append("--pm")
        for k in ("min_glossary", "max_unexplained", "ch0_min", "ch0_max", "ch0_max_acr"):
            if pl.get(k) is not None:
                cmd += ["--pm-" + k.replace("_", "-"), str(pl[k])]
        if pl.get("tech") is False:
            cmd.append("--pm-no-tech")
        if pl.get("allow"):
            cmd += ["--pm-allow", ",".join(pl["allow"])]
if a.lax:
    cmd.append("--lax")
r = subprocess.run(cmd, capture_output=True, text=True)
print((r.stdout + r.stderr)[-6000:])
if r.returncode == 0 and a.feishu and card.get("feishu_name"):
    dst = R / (card["feishu_name"] + ".html")
    shutil.copy2(R / (stem + ".html"), dst)
    print("飞书用副本 →", dst.name)
sys.exit(r.returncode)
