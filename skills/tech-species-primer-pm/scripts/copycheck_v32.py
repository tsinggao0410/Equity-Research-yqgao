#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""copycheck_v32.py — 与参考报告的照抄检查(render_report_v32.py --gate --ref 调用,也可单独跑)。

口径(第三轮评审提出「单句 3 字片段重合率 ≥0.3 或 12 字以上公共片段」,本脚本按下述办法落地):
  1. 只查正文:段落、列表、导语、提示块、图题、表格单元格;不查来源行、图注、表格视图、目录。
  2. 句子按 。;;!? 切分;规范化后汉字 ≥15 个才检查。规范化 = 删去书名号《…》里的报告名、删去括号内的出处
     (含 p 页码、年报、纪要、深度等字样)、只保留汉字。数字与英文不参与比较:相同事实(数字)允许相同。
  3. 背景语料(公司年报、半年报、招股书原文)里出现过的 3 字片段 / 12 字片段不算照抄:两份报告都转述公司原话
     时必然重合,这不是抄参考报告。
  4. 判定照抄:「参考报告独有」的 3 字片段占句子 3 字片段的比重 ≥0.30,或与参考报告有 ≥12 个汉字的
     独有公共片段(不在背景语料里)。
用法:python3 copycheck_v32.py 卡.html ref_text.txt [背景1.txt,背景2.txt] [--all]
"""
import html
import re
import sys

MIN_CJK = 15
RATIO_MAX = 0.30
LCS_MAX = 12
WARN_RAW = 0.55   # 不扣背景语料的原始重合率,只提示人工复看(相同事实会抬高它)


def strip_cite(s: str) -> str:
    s = re.sub(r"《[^《》]{0,80}》", "", s)
    s = re.sub(r"[(（][^()（）]{0,60}(?:p\d|年报|半年报|招股书|纪要|点评|深度|报告|进门财经)[^()（）]{0,60}[)）]", "", s)
    return s


def cjk(s: str) -> str:
    return "".join(re.findall(r"[一-鿿]", strip_cite(s)))


def sentences_from_html(doc: str) -> list:
    main = doc.split("<main>", 1)[-1].split('<h2 id="figidx">')[0]
    for pat in (r'<details class="dv">[\s\S]*?</details>', r"<figcaption>[\s\S]*?</figcaption>",
                r'<div class="srcline">[\s\S]*?</div>', r"<(script|style|svg)[\s\S]*?</\1>", r"<caption>[\s\S]*?</caption>",
                r'<div class="footer">[\s\S]*?</div>\s*$'):
        main = re.sub(pat, "", main)
    txt = html.unescape(re.sub(r"<[^>]+>", "\n", main))
    out = []
    for para in txt.split("\n"):
        for s in re.split(r"[。；;！？!?]", para):
            s = s.strip()
            if len(cjk(s)) >= MIN_CJK:
                out.append(s)
    return out


def check_html(doc: str, ref_txt: str, bg_txts=()):
    ref = cjk(ref_txt)
    bg = "".join(cjk(b) for b in bg_txts)
    bg3 = {bg[i:i + 3] for i in range(len(bg) - 2)}
    bg12 = {bg[i:i + LCS_MAX] for i in range(len(bg) - LCS_MAX + 1)}
    r3all = {ref[i:i + 3] for i in range(len(ref) - 2)}
    r3 = r3all - bg3
    r12 = {ref[i:i + LCS_MAX] for i in range(len(ref) - LCS_MAX + 1)} - bg12
    hits, warns, sents = [], [], sentences_from_html(doc)
    for s in sents:
        n = cjk(s)
        sh = [n[i:i + 3] for i in range(len(n) - 2)]
        ratio = sum(1 for x in sh if x in r3) / max(1, len(sh))
        lcs = 0
        for i in range(len(n) - LCS_MAX + 1):
            if n[i:i + LCS_MAX] in r12:
                k = LCS_MAX
                while i + k < len(n) and n[i:i + k + 1] in ref:
                    k += 1
                lcs = max(lcs, k)
        raw = sum(1 for x in sh if x in r3all) / max(1, len(sh))
        if ratio >= RATIO_MAX or lcs >= LCS_MAX:
            hits.append((round(ratio, 2), lcs, s[:80]))
        elif raw >= WARN_RAW:
            warns.append((round(raw, 2), 0, s[:80]))
    check_html.warns = warns
    return hits, len(sents)


if __name__ == "__main__":
    doc = open(sys.argv[1], encoding="utf-8").read()
    ref = open(sys.argv[2], encoding="utf-8").read()
    bgs = [open(p, encoding="utf-8", errors="ignore").read() for p in (sys.argv[3].split(",") if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else [])]
    hits, n = check_html(doc, ref, bgs)
    print("检查 %d 句,命中 %d 句" % (n, len(hits)))
    for h in hits:
        print("  %.2f  %2d  %s" % h)
    print("人工复看(原始重合率 ≥%.2f,不计入门槛):%d 句" % (WARN_RAW, len(check_html.warns)))
    for h in check_html.warns:
        print("  %.2f  %s" % (h[0], h[2]))
