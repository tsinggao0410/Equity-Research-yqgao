#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""官方图下载与登记(官网 / IR 页 / 官方 PDF):默认存 R/sources/web/img/ 并写 catalog.json,挑中后再复制进 R/images/cN_*。
用法(全局选项放在子命令前):python3 imggrab.py [--root R] [--dir 相对R的目录] <子命令> ...
  get NAME IMG_URL PAGE_URL "alt/图注"        下载网页图(webp/gif 转 png),量尺寸,宽 <400px 拒收
  pdfpage NAME PDF_REL PAGE_NO "图注" [zoom]  把 R 下某 PDF 的一页渲染成 png(官方 PDF 原图页)
  pdfimg NAME PDF_REL PAGE_NO XREF "图注"     抽 PDF 某页内嵌位图(xref 由 pdfimgs 列出)
  pdfimgs PDF_REL [PAGE_NO]                    列出 PDF 内嵌位图 xref 与尺寸
  note NAME "内容一句话" "建议章节"             补写 content / chapter
  drop NAME                                   删除该图与登记
catalog 字段:file, img_url, page_url, alt, width, height, content, chapter, access_date, source_type
请求只带浏览器 UA,不带任何个人信息(不要把用户邮箱放进请求)。"""
import sys, json, pathlib, subprocess, io, time, datetime
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _card import find_root  # noqa: E402

_args = sys.argv[1:]
_root = _dir = None
while _args and _args[0] in ("--root", "--dir"):
    if _args[0] == "--root":
        _root = _args[1]
    else:
        _dir = _args[1]
    _args = _args[2:]
R = find_root(_root)
IMG = R / (_dir or "sources/web/img")
CAT = IMG / "catalog.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
TODAY = datetime.date.today().isoformat()
IMG.mkdir(parents=True, exist_ok=True)


def load():
    return json.loads(CAT.read_text()) if CAT.exists() else []


def save(L):
    CAT.write_text(json.dumps(L, ensure_ascii=False, indent=1))


def upsert(rec):
    L = [x for x in load() if x["file"] != rec["file"]]
    old = [x for x in load() if x["file"] == rec["file"]]
    if old:
        for k in ("content", "chapter"):
            if old[0].get(k) and not rec.get(k):
                rec[k] = old[0][k]
    L.append(rec)
    save(L)


def get(name, url, page, alt):
    raw = subprocess.run(["curl", "-s", "-L", "-A", UA, "-m", "90", "--retry", "2", "-w", "", url], capture_output=True).stdout
    time.sleep(0.3)
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception as e:
        print("FAIL 非图片", url, len(raw)); return
    w, h = im.size
    if w < 400:
        print("REJECT 宽 %d<400" % w, url); return
    fmt = (im.format or "").upper()
    if fmt in ("JPEG", "JPG"):
        ext = ".jpg"; data = raw
    elif fmt == "PNG":
        ext = ".png"; data = raw
    else:  # webp / gif 等 → png
        ext = ".png"; b = io.BytesIO()
        (im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")).save(b, "PNG"); data = b.getvalue()
    out = IMG / (name + ext)
    out.write_bytes(data)
    upsert({"file": str(out.relative_to(R)), "img_url": url, "page_url": page, "alt": alt, "width": w, "height": h,
            "content": "", "chapter": "", "access_date": TODAY, "source_type": "网页原图(%s)" % fmt})
    print("OK %s %dx%d %s" % (out.name, w, h, fmt))


def pdfpage(name, pdf_rel, pno, cap, zoom=2.0):
    import fitz
    d = fitz.open(R / pdf_rel)
    pg = d[int(pno) - 1]
    pix = pg.get_pixmap(matrix=fitz.Matrix(float(zoom), float(zoom)))
    out = IMG / (name + ".png")
    pix.save(out)
    upsert({"file": str(out.relative_to(R)), "img_url": "%s#p%s(整页渲染 x%s)" % (pdf_rel, pno, zoom), "page_url": pdf_rel, "alt": cap,
            "width": pix.width, "height": pix.height, "content": "", "chapter": "", "access_date": TODAY, "source_type": "官方 PDF 页面渲染"})
    print("OK %s %dx%d" % (out.name, pix.width, pix.height))


def pdfimgs(pdf_rel, pno=None):
    import fitz
    d = fitz.open(R / pdf_rel)
    rng = [int(pno) - 1] if pno else range(len(d))
    for i in rng:
        for x in d[i].get_images(full=True):
            print("p%d xref=%d %dx%d %s" % (i + 1, x[0], x[2], x[3], x[5]))


def pdfimg(name, pdf_rel, pno, xref, cap):
    import fitz
    d = fitz.open(R / pdf_rel)
    pix = fitz.Pixmap(d, int(xref))
    if pix.n - pix.alpha >= 4:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    if pix.width < 400:
        print("REJECT 宽 %d<400" % pix.width); return
    out = IMG / (name + ".png")
    pix.save(out)
    upsert({"file": str(out.relative_to(R)), "img_url": "%s#p%s xref%s(内嵌位图)" % (pdf_rel, pno, xref), "page_url": pdf_rel, "alt": cap,
            "width": pix.width, "height": pix.height, "content": "", "chapter": "", "access_date": TODAY, "source_type": "官方 PDF 内嵌图"})
    print("OK %s %dx%d" % (out.name, pix.width, pix.height))


def note(name, content, chapter):
    L = load(); hit = 0
    for x in L:
        if pathlib.Path(x["file"]).stem == name:
            x["content"] = content; x["chapter"] = chapter; hit = 1
    save(L); print("noted" if hit else "NOT FOUND " + name)


def drop(name):
    L = load(); keep = []
    for x in L:
        if pathlib.Path(x["file"]).stem == name:
            (R / x["file"]).unlink(missing_ok=True); print("dropped", x["file"])
        else:
            keep.append(x)
    save(keep)


if __name__ == "__main__":
    a = _args
    if not a or a[0] not in ("get", "pdfpage", "pdfimgs", "pdfimg", "note", "drop"):
        sys.exit(__doc__)
    {"get": lambda: get(*a[1:5]), "pdfpage": lambda: pdfpage(*a[1:]), "pdfimgs": lambda: pdfimgs(*a[1:]),
     "pdfimg": lambda: pdfimg(*a[1:6]), "note": lambda: note(*a[1:4]), "drop": lambda: drop(a[1])}[a[0]]()
