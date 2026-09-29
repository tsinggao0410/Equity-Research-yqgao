#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_visuals.py — Mode B 视觉素材层:从公司官网 / IR 页 / IR deck PDF 抓产品图与业务结构图,
落地成 images/ + visuals_manifest.json + contact_sheet.html,供认知卡挑图。

只抓三类来源 (铁律 13): 公司官网 / IR 页 / 年报·IR deck·招股书 PDF。**不抓搜索引擎图片。**

用法 (三种输入可混用):
  # 1) 静态网页 (大多数公司官网产品页可直接 curl)
  python fetch_visuals.py --url https://www.yuchai.com/product/engine.htm \
      --url https://www.yuchaidiesel.com/product/pro-list-56-0.htm \
      --keywords "YCK15N,YCK13,YCS06,YCY30,产业链,动力系统,发动机" \
      --out-dir ~/Desktop/research-materials/玉柴国际-CYD/primer

  # 2) JS 渲染的页面 (ajax 加载的产品卡 / Akamai 挡 curl 的 IR 站) —— 浏览器路径,两种喂法任选:
  #    a. Claude Browser 打开页面 → javascript_tool 跑 BROWSER_SNIPPET (见下) → 把返回 JSON 存成文件
  python fetch_visuals.py --img-list truck_list.json --out-dir ...
  #    b. 把 document.documentElement.outerHTML 存成文件 (更大, 一般不需要)
  python fetch_visuals.py --html-file page.html --base-url https://investor.example.com/ --out-dir ...

  # 3) IR deck / 年报 PDF: 按关键词挑页渲成 PNG (业务结构图 / 产品矩阵 / 收入拆分图通常在这)
  python fetch_visuals.py --pdf "May 2026 Presentation.pdf" --keywords "business,segment,product,value chain,revenue" --out-dir ...

  --crawl 1     从 --url 页面出发,再抓同域名下链接文字/URL 命中关键词的子页 (默认 0 不爬)
  --min-px 300  过滤小图 (logo/icon);--max-per-page 40;--no-proxy 剥掉环境代理 (国内官网常需要)

产物:
  <out-dir>/images/<sha1前10>.<ext>          图片文件 (去重)
  <out-dir>/visuals_manifest.json             每张图: file/source_url/page_url/page_title/alt/context/w/h/score/matched/suggested_module
  <out-dir>/contact_sheet.html                缩略图总览 (自包含), 人和 Agent 都能扫一眼挑图

退出码: 0 有图;2 一张也没抓到 (页面被挡/全 JS 渲染) —— 转浏览器路径。

BROWSER_SNIPPET (在 Claude Browser 的 javascript_tool 里执行;先滚到底把 ajax/懒加载触发出来,再导出图片清单):
    for (let i=0;i<6;i++){ window.scrollTo(0,document.body.scrollHeight); await new Promise(r=>setTimeout(r,700));
      const lm=document.querySelector('#load_more,.load-more,.more'); if(lm) lm.click(); }
    const near=el=>{let c=el;for(let k=0;k<5&&c;k++){const t=(c.innerText||'').replace(/\s+/g,' ').trim();if(t.length>1)return t.slice(0,80);c=c.parentElement;}return '';};
    JSON.stringify({page_url:location.href,page_title:document.title,list:[...document.images]
      .filter(i=>(i.naturalWidth||0)>=200).map(i=>({src:i.currentSrc||i.src,alt:i.alt||'',ctx:near(i),
      w:i.naturalWidth,h:i.naturalHeight,href:(i.closest('a')||{}).href||''}))})
  → 结果存成 <name>.json, 喂 --img-list。IR deck PDF 被 Akamai 挡时, curl/fetch 都拿不到文件:
    让用户用真实浏览器下载到 primer/ir/ 再走 --pdf (或经用户同意后用 Chrome 扩展下载)。
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
from html import escape
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:  # pragma: no cover
    print(f"[X] 需要 requests + beautifulsoup4: {e}", file=sys.stderr)
    raise SystemExit(1)

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
SKIP_NAME = re.compile(r"logo|icon|favicon|arrow|btn|button|banner-bg|sprite|placeholder|qrcode|qr_code|wechat|weixin|loading|blank\.|spacer", re.I)

# 关键词 → 建议模块 (只是建议, 最终由 Agent 定)
MODULE_HINTS = [
    (re.compile(r"产业链|价值链|value chain|供应链|supply chain|业务结构|business structure|商业模式|business model|布局|生态|ecosystem|集团架构|organization|战略|strategy|一图|概览|overview|segment", re.I), "B0/B4 业务结构"),
    (re.compile(r"原理|工作|剖视|剖面|structure|cutaway|schematic|示意|技术路线|roadmap|平台|platform|排放|emission|后处理|aftertreatment", re.I), "B2 技术科普"),
    (re.compile(r"应用|配套|案例|场景|solution|解决方案|客户|customer|application|车型|整车|装机|fleet", re.I), "B3 下游应用"),
    (re.compile(r"工厂|产线|车间|基地|factory|plant|production|capacity|铸造|foundry", re.I), "B4 商业模式(产能)"),
    (re.compile(r"市场|份额|market|share|排名|竞争|competit", re.I), "B5 行业格局"),
    (re.compile(r"收入|revenue|销量|units|财务|financial|增长|growth|毛利|margin", re.I), "B1/B4 数据图"),
]


def guess_module(text: str, kw_hit: list[str]) -> str:
    for rx, mod in MODULE_HINTS:
        if rx.search(text):
            return mod
    if kw_hit:
        return "B1 产品谱系(型号图)"
    return "待定"


def session(no_proxy: bool) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "*/*", "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
    if no_proxy:
        s.trust_env = False
    return s


def fetch_html(sess: requests.Session, url: str, timeout: int = 30) -> tuple[str, str] | None:
    try:
        r = sess.get(url, timeout=timeout)
    except Exception as e:  # noqa: BLE001
        print(f"[!] GET 失败 {url}: {e}", file=sys.stderr)
        return None
    if r.status_code != 200:
        print(f"[!] HTTP {r.status_code} {url} —— 若是 403/Access Denied(Akamai/Q4 IR 站),走浏览器路径 --html-file", file=sys.stderr)
        return None
    if "text/html" not in r.headers.get("content-type", "") and not r.text.lstrip().lower().startswith("<"):
        print(f"[!] 非 HTML {url}", file=sys.stderr)
        return None
    r.encoding = r.apparent_encoding or r.encoding
    return r.text, r.url


def nearest_heading(tag) -> str:
    cur = tag
    for _ in range(6):
        if cur is None:
            break
        prev = cur.find_previous(["h1", "h2", "h3", "h4", "figcaption", "strong"])
        if prev is not None:
            t = prev.get_text(" ", strip=True)
            if t:
                return t[:80]
        cur = cur.parent
    return ""


def collect_img_candidates(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    page_title = (soup.title.get_text(strip=True) if soup.title else "")[:100]
    cands: list[dict] = []
    seen: set[str] = set()

    def add(src: str, alt: str, ctx: str, kind: str):
        if not src or src.startswith("data:"):
            return
        u = urljoin(base_url, src.strip())
        if u in seen:
            return
        seen.add(u)
        cands.append({"src": u, "alt": alt[:120], "context": ctx[:200], "kind": kind, "page_title": page_title})

    for im in soup.find_all("img"):
        srcs = [im.get("src"), im.get("data-src"), im.get("data-original"), im.get("data-lazy-src")]
        ss = im.get("srcset") or im.get("data-srcset")
        if ss:
            # 取 srcset 里最大的一张
            parts = [p.strip().split()[0] for p in ss.split(",") if p.strip()]
            if parts:
                srcs.append(parts[-1])
        alt = (im.get("alt") or im.get("title") or "")
        par_a = im.find_parent("a")
        ctx = " | ".join(x for x in [alt, (par_a.get_text(" ", strip=True)[:60] if par_a else ""), nearest_heading(im)] if x)
        for s in srcs:
            if s:
                add(s, alt, ctx, "img")
    for src_tag in soup.find_all("source"):
        ss = src_tag.get("srcset") or src_tag.get("data-srcset")
        if ss:
            parts = [p.strip().split()[0] for p in ss.split(",") if p.strip()]
            if parts:
                add(parts[-1], "", nearest_heading(src_tag), "picture")
    for tag in soup.find_all(style=re.compile(r"background(-image)?\s*:", re.I)):
        for m in re.finditer(r"url\(([^)]+)\)", tag.get("style", "")):
            u = m.group(1).strip("'\" ")
            add(u, "", tag.get_text(" ", strip=True)[:80] or nearest_heading(tag), "css-bg")
    return cands


def same_domain_links(html: str, base_url: str, kws: list[str]) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    host = urlparse(base_url).netloc.split(":")[0]
    root = ".".join(host.split(".")[-2:])
    out, seen = [], set()
    for a in soup.find_all("a", href=True):
        u = urljoin(base_url, a["href"].strip())
        pu = urlparse(u)
        if pu.scheme not in ("http", "https") or root not in pu.netloc or u.split("#")[0] in seen:
            continue
        txt = (a.get_text(" ", strip=True) + " " + u).lower()
        if any(k.lower() in txt for k in kws) or re.search(r"product|产品|pro-list|solution|business|about|投资者|investor", txt):
            seen.add(u.split("#")[0])
            out.append(u.split("#")[0])
    return out


def download_image(sess: requests.Session, url: str, out_dir: Path, min_px: int) -> dict | None:
    try:
        r = sess.get(url, timeout=30)
    except Exception as e:  # noqa: BLE001
        return {"error": f"GET 失败: {e}"}
    if r.status_code != 200 or len(r.content) < 2000:
        return {"error": f"HTTP {r.status_code} / {len(r.content)}B"}
    ct = r.headers.get("content-type", "")
    if "image" not in ct and Path(urlparse(url).path).suffix.lower() not in IMG_EXT:
        return {"error": f"非图片 content-type={ct}"}
    sha = hashlib.sha1(r.content).hexdigest()
    w = h = None
    fmt = None
    if Image is not None:
        try:
            with Image.open(io.BytesIO(r.content)) as im:
                w, h = im.size
                fmt = (im.format or "").lower()
        except Exception:  # noqa: BLE001
            return {"error": "PIL 打不开 (可能是 svg/损坏)"}
        if fmt == "gif" or (w is not None and (w < min_px or h < min_px)):
            return {"error": f"太小或 gif ({w}x{h} {fmt})"}
    ext = {"jpeg": ".jpg", "png": ".png", "webp": ".webp", "bmp": ".bmp"}.get(fmt or "", Path(urlparse(url).path).suffix.lower() or ".jpg")
    fn = out_dir / f"{sha[:10]}{ext}"
    if not fn.exists():
        fn.write_bytes(r.content)
    return {"file": str(fn), "sha1": sha, "width": w, "height": h, "bytes": len(r.content), "format": fmt}


MODEL_CODE = re.compile(r"\b[A-Z]{2,4}\d{2,4}[A-Z]?(?:-\d+|系列|\s?series)?\b|[A-Z]{1,3}\d{2,4}[A-Z]{0,2}\b")


def score_candidate(c: dict, kws: list[str]) -> tuple[int, list[str]]:
    text = f"{c.get('alt','')} {c.get('context','')} {c.get('src','')}"
    hit = [k for k in kws if k and k.lower() in text.lower()]
    sc = 10 * len(hit)
    w, h = c.get("width") or 0, c.get("height") or 0
    if w and h:
        sc += min(w * h // 40000, 30)  # 面积加分,封顶 30
        if w > 2.5 * h or h > 2.5 * w:
            sc -= 25  # 横幅 (1920×600 这种) 多半是 banner, 只配当 B3 场景配图
    alt = c.get("alt", "")
    if alt:
        sc += 5
        if MODEL_CODE.search(alt):
            sc += 20  # alt 直接是型号 (YCK15N / WP13 / H100) —— 产品谱系最想要的图
    if SKIP_NAME.search(c.get("src", "")):
        sc -= 40
    return sc, hit


def render_pdf_pages(pdf: Path, out_dir: Path, kws: list[str], max_pages: int, dpi: int) -> list[dict]:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("[!] 没有 PyMuPDF (pip install pymupdf) —— PDF 挑页跳过;可用 pdftoppm 手工渲", file=sys.stderr)
        return []
    doc = fitz.open(str(pdf))
    picked: list[dict] = []
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        low = text.lower()
        hit = [k for k in kws if k and k.lower() in low]
        n_img = len(page.get_images(full=True))
        n_draw = len(page.get_drawings()) if hasattr(page, "get_drawings") else 0
        chart_like = (n_img >= 1 or n_draw >= 40) and len(text) < 2500
        if not (hit or chart_like):
            continue
        sc = 10 * len(hit) + (15 if chart_like else 0) + min(n_draw // 20, 15)
        pix = page.get_pixmap(dpi=dpi)
        fn = out_dir / f"{pdf.stem[:30].replace(' ', '_')}_p{i+1:03d}.png"
        pix.save(str(fn))
        first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")[:100]
        picked.append({
            "id": "", "file": str(fn), "source_url": f"{pdf.name}#page={i+1}", "page_url": str(pdf),
            "page_title": first_line, "alt": first_line, "context": text[:300].replace("\n", " "),
            "width": pix.width, "height": pix.height, "bytes": fn.stat().st_size, "sha1": hashlib.sha1(fn.read_bytes()).hexdigest(),
            "score": sc, "matched": hit, "suggested_module": guess_module(text, hit), "source_type": "ir_deck_or_report_pdf",
            "pdf_page": i + 1, "n_images": n_img, "n_drawings": n_draw,
        })
    picked.sort(key=lambda x: -x["score"])
    return picked[:max_pages]


def write_contact_sheet(items: list[dict], out: Path, title: str):
    import base64
    cards = []
    for it in items:
        try:
            data = Path(it["file"]).read_bytes()
            if Image is not None:
                with Image.open(io.BytesIO(data)) as im:
                    im.thumbnail((360, 360))
                    buf = io.BytesIO()
                    im.convert("RGB").save(buf, "JPEG", quality=70)
                    data = buf.getvalue()
                mime = "image/jpeg"
            else:
                mime = "image/png"
            b64 = base64.b64encode(data).decode()
        except Exception:  # noqa: BLE001
            continue
        cap = escape(f"{it.get('id','')} · {it.get('suggested_module','')} · score {it.get('score')} · {it.get('width')}×{it.get('height')}")
        meta = escape(f"{it.get('alt') or it.get('context','')}")
        src = escape(it.get("source_url", ""))
        cards.append(f"<figure><img src='data:{mime};base64,{b64}'><figcaption><b>{cap}</b><br>{meta}<br><small>{src}</small></figcaption></figure>")
    html = f"""<!doctype html><meta charset='utf-8'><title>{escape(title)}</title>
<style>body{{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:#fff;color:#222;margin:24px}}
h1{{font-size:18px;color:#1f3a5f}} .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}}
figure{{margin:0;border:1px solid #ddd;padding:8px;background:#fafafa}} img{{width:100%;height:auto;background:#fff}}
figcaption{{font-size:12px;line-height:1.45;margin-top:6px;word-break:break-all}} small{{color:#777}}</style>
<h1>{escape(title)} · {len(cards)} 张候选</h1><div class='grid'>{''.join(cards)}</div>"""
    out.write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Mode B 视觉素材抓取 (官网/IR/PDF)")
    ap.add_argument("--url", action="append", default=[], help="页面 URL,可重复")
    ap.add_argument("--html-file", action="append", default=[], help="浏览器渲染后保存的 HTML 文件,可重复 (配 --base-url)")
    ap.add_argument("--base-url", action="append", default=[], help="与 --html-file 一一对应的页面 URL")
    ap.add_argument("--img-list", action="append", default=[], help="浏览器 BROWSER_SNIPPET 导出的图片清单 JSON,可重复")
    ap.add_argument("--pdf", action="append", default=[], help="IR deck / 年报 PDF,可重复")
    ap.add_argument("--keywords", default="", help="逗号分隔:型号名/产品词/结构图词,用于打分与 PDF 挑页")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--crawl", type=int, default=0, help="0=只抓给定页;1=再抓一层同域命中关键词的子页")
    ap.add_argument("--min-px", type=int, default=300)
    ap.add_argument("--max-per-page", type=int, default=40)
    ap.add_argument("--max-pages-total", type=int, default=25, help="crawl 时最多抓多少页")
    ap.add_argument("--pdf-max-pages", type=int, default=20)
    ap.add_argument("--pdf-dpi", type=int, default=144)
    ap.add_argument("--no-proxy", action="store_true", help="剥掉环境代理 (国内官网常需要)")
    ap.add_argument("--sleep", type=float, default=0.3)
    args = ap.parse_args()

    kws = [k.strip() for k in args.keywords.split(",") if k.strip()]
    out_dir = Path(args.out_dir).expanduser().resolve()
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    sess = session(args.no_proxy)

    pages: list[tuple[str, str]] = []  # (html, url)
    queue = list(args.url)
    visited: set[str] = set()
    while queue and len(pages) < args.max_pages_total:
        u = queue.pop(0)
        if u in visited:
            continue
        visited.add(u)
        got = fetch_html(sess, u)
        time.sleep(args.sleep)
        if not got:
            continue
        html, final = got
        pages.append((html, final))
        if args.crawl >= 1 and len(visited) == 1 + 0:
            pass
        if args.crawl >= 1 and u in args.url:
            for link in same_domain_links(html, final, kws):
                if link not in visited:
                    queue.append(link)
    for hf, bu in zip(args.html_file, args.base_url or [""] * len(args.html_file)):
        p = Path(hf).expanduser()
        if p.exists():
            pages.append((p.read_text(encoding="utf-8", errors="ignore"), bu or f"file://{p}"))
        else:
            print(f"[!] 找不到 {hf}", file=sys.stderr)

    # 浏览器导出的清单 → 伪装成一页候选
    extra_pages: list[tuple[list[dict], str]] = []
    for lf in args.img_list:
        p = Path(lf).expanduser()
        if not p.exists():
            print(f"[!] 找不到 {lf}", file=sys.stderr)
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        purl = d.get("page_url", f"file://{p}")
        cands = []
        for it in d.get("list", []):
            cands.append({"src": urljoin(purl, it.get("src", "")), "alt": (it.get("alt") or "")[:120],
                          "context": (it.get("ctx") or it.get("context") or "")[:200], "kind": "browser",
                          "page_title": d.get("page_title", ""), "detail_url": it.get("href", "")})
        extra_pages.append((cands, purl))

    items: list[dict] = []
    seen_sha: set[str] = set()
    all_pages = [(collect_img_candidates(html, purl), purl) for html, purl in pages] + extra_pages
    for cands, purl in all_pages:
        n_ok = 0
        for c in cands:
            if n_ok >= args.max_per_page:
                break
            if SKIP_NAME.search(c["src"]) and not any(k.lower() in (c["alt"] + c["context"]).lower() for k in kws):
                continue
            dl = download_image(sess, c["src"], img_dir, args.min_px)
            time.sleep(args.sleep / 3)
            if not dl or "error" in dl:
                continue
            if dl["sha1"] in seen_sha:
                continue
            seen_sha.add(dl["sha1"])
            c.update(dl)
            sc, hit = score_candidate(c, kws)
            host = urlparse(purl).netloc
            items.append({
                "id": "", "file": c["file"], "source_url": c["src"], "page_url": purl, "page_title": c.get("page_title", ""),
                "alt": c.get("alt", ""), "context": c.get("context", ""), "width": c["width"], "height": c["height"],
                "bytes": c["bytes"], "sha1": c["sha1"], "score": sc, "matched": hit,
                "suggested_module": guess_module(c.get("alt", "") + " " + c.get("context", "") + " " + c["src"], hit),
                "source_type": "ir_page" if re.search(r"investor|ir\.|/ir/", purl, re.I) else "official_site",
                "host": host, "detail_url": c.get("detail_url", ""),
            })
            n_ok += 1
        print(f"[i] {purl} → 候选 {len(cands)} / 落地 {n_ok}", file=sys.stderr)

    for pdf in args.pdf:
        p = Path(pdf).expanduser()
        if not p.exists():
            print(f"[!] 找不到 PDF {pdf}", file=sys.stderr)
            continue
        got = render_pdf_pages(p, img_dir, kws, args.pdf_max_pages, args.pdf_dpi)
        print(f"[i] PDF {p.name} → 挑出 {len(got)} 页", file=sys.stderr)
        items.extend(got)

    items.sort(key=lambda x: -x["score"])
    for i, it in enumerate(items, 1):
        it["id"] = f"V{i:02d}"
    manifest = {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "keywords": kws, "pages": [u for _, u in pages] + [u for _, u in extra_pages], "pdfs": args.pdf,
        "count": len(items), "items": items,
        "note": "score 只是排序建议;挑图后把选中的条目 (加 caption/module/shows) 填进 business_primer.json 的 visuals[]",
    }
    (out_dir / "visuals_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_contact_sheet(items, out_dir / "contact_sheet.html", f"视觉素材候选 · {out_dir.name}")
    print(f"[OK] {len(items)} 张 → {img_dir}  | manifest → {out_dir/'visuals_manifest.json'} | 总览 → {out_dir/'contact_sheet.html'}", file=sys.stderr)
    if not items:
        print("[X] 一张也没抓到:页面可能被 Akamai/Q4 挡 (403) 或全 JS 渲染 —— 用 Claude Browser 打开页面,把 outerHTML 存文件后走 --html-file;"
              "PDF 被挡则需真实浏览器下载后走 --pdf", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
