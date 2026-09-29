#!/usr/bin/env python3
"""playwright 截图验版式:首屏、每章首屏、抽样若干图、390 宽手机首屏;统计 JS 报错、坏图、横向溢出,
并记录每章截图是否真的停在该章 h2 上。

用法:python3 shots.py [--root R] [html路径] [输出目录]
      默认 html = R/<out_stem>.html(card.json),输出 = R/work/shots/;结果写 shots.json,验收看 chapters[].ok、
      js_errors、broken_imgs、mobile_scrollWidth(应 ≤ 390)。截图用 Read 工具逐张看。

要点(2026-09-24 德科立卡第一章评审修正):页面 CSS 有 html{scroll-behavior:smooth},直接 scrollTo 后短等会截到
上一章或空白。所以:①注入样式关掉平滑滚动;②用 h2 自己的 scrollIntoView 定位;③等可视区图片 decode、两帧
requestAnimationFrame、再给 ECharts 留时间;④截图前后量 h2 顶部位置,偏离超过 40px 重试一次。
"""
import argparse, json, pathlib, sys
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _card import find_root, load_card  # noqa: E402

_ap = argparse.ArgumentParser()
_ap.add_argument("--root")
_ap.add_argument("html", nargs="?")
_ap.add_argument("out", nargs="?")
_a = _ap.parse_args()
if _a.html:
    html = pathlib.Path(_a.html).resolve()
    R = html.parent
else:
    R = find_root(_a.root)
    html = R / (load_card(R)["out_stem"] + ".html")
out = pathlib.Path(_a.out).resolve() if _a.out else R / "work" / "shots"
out.mkdir(parents=True, exist_ok=True)
NO_SMOOTH = "html,body{scroll-behavior:auto !important}"
SETTLE_JS = """async () => {
  const vis = [...document.images].filter(i => { const r = i.getBoundingClientRect();
    return r.bottom > 0 && r.top < window.innerHeight; });
  await Promise.all(vis.map(i => i.complete ? (i.decode ? i.decode().catch(() => {}) : 0)
                                            : new Promise(r => { i.onload = i.onerror = r; })));
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  return vis.length;
}"""
errs = []
chapters = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
    pg.on("console", lambda m: errs.append("console.%s: %s" % (m.type, m.text)) if m.type == "error" else None)
    pg.goto(html.as_uri(), wait_until="networkidle")
    pg.add_style_tag(content=NO_SMOOTH)
    pg.evaluate(SETTLE_JS)
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(out / "00_首屏.png"))
    # 先整页滚一遍,触发懒加载图片与图表,避免之后定位时版面位移
    h = pg.evaluate("document.scrollingElement.scrollHeight")
    y = 0
    while y < h:
        pg.evaluate("y => window.scrollTo({top: y, behavior: 'instant'})", y); pg.wait_for_timeout(120); y += 800
        h = pg.evaluate("document.scrollingElement.scrollHeight")
    pg.wait_for_timeout(1500)
    heads = pg.eval_on_selector_all("main h2", "els => els.map(e => ({id: e.id, t: e.textContent.trim()}))")
    for i, hd in enumerate(heads):
        loc = pg.locator("main h2").nth(i)
        top = None
        for attempt in range(2):
            loc.evaluate("e => { e.scrollIntoView({block: 'start', behavior: 'instant'}); window.scrollBy({top: -12, behavior: 'instant'}); }")
            pg.evaluate(SETTLE_JS)
            pg.wait_for_timeout(900)          # ECharts 由 IntersectionObserver 触发,给它时间画完
            top = loc.evaluate("e => Math.round(e.getBoundingClientRect().top)")
            if 0 <= top <= 40:
                break
        at_end = pg.evaluate("() => window.scrollY + window.innerHeight >= document.scrollingElement.scrollHeight - 20")
        f = out / ("ch%02d.png" % (i + 1))
        pg.screenshot(path=str(f))
        # 页面末尾的短节(如图表目录)滚不到顶,h2 在可视区内即算定位成功
        ok = bool(top is not None and (0 <= top <= 40 or (at_end and 0 <= top < 900)))
        chapters.append(dict(n=i + 1, h2=hd["t"], h2_top=top, page_end=at_end, ok=ok,
                             png=f.name, png_bytes=f.stat().st_size))
    # 图表数与已渲染 canvas 数
    n_chart = pg.eval_on_selector_all("figure.cfig", "els => els.length")
    n_canvas = pg.eval_on_selector_all("canvas", "els => els.length")
    n_img = pg.eval_on_selector_all("main img", "els => els.length")
    broken = pg.eval_on_selector_all("main img", "els => els.filter(i => !i.complete || i.naturalWidth === 0).length")
    # 抽几张图:每隔若干个 figure 截一张
    sel = pg.query_selector_all("main figure, main .fig, main .panel")
    picks = list(range(0, len(sel), max(1, len(sel) // 10)))[:12]
    for k in picks:
        try:
            sel[k].scroll_into_view_if_needed(); pg.evaluate(SETTLE_JS); pg.wait_for_timeout(600)
            sel[k].screenshot(path=str(out / ("fig_%03d.png" % k)))
        except Exception as e:
            errs.append("shot fail %d: %s" % (k, e))
    mob = b.new_page(viewport={"width": 390, "height": 844})
    mob.on("pageerror", lambda e: errs.append("mobile pageerror: %s" % e))
    mob.goto(html.as_uri(), wait_until="networkidle"); mob.add_style_tag(content=NO_SMOOTH)
    mob.evaluate(SETTLE_JS); mob.wait_for_timeout(1500)
    mob.screenshot(path=str(out / "mobile_首屏.png"))
    sw = mob.evaluate("document.documentElement.scrollWidth")
    b.close()
res = dict(html=str(html), h2=[h["t"] for h in heads], chapters=chapters,
           chapters_ok=sum(c["ok"] for c in chapters), chapters_total=len(chapters),
           charts=n_chart, canvas=n_canvas, imgs=n_img, broken_imgs=broken, figures_sampled=picks,
           mobile_scrollWidth=sw, js_errors=errs)
(out / "shots.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
