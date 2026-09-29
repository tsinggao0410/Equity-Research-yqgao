#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_v32.py — render_report_v32.py 的浏览器自测(playwright + chromium,1440 宽)。

用法
    python3 selftest_v32.py fixture.html [--ref ref.html] [--shots DIR] [--json out.json] [--narrow]
    python3 selftest_v32.py --stress [--n-charts 40 --n-flows 12 --n-images 10] [--workdir DIR]   # 生成 60+ 图压力样例并测(默认写到系统临时目录)

检查项(任何一项不过,退出码 1)
    ① JS 报错 0(console.error + pageerror)
    ② 离线:除 file:// 与 data: 之外的请求一律拦截并计数,须为 0
    ③ 每个 .chart[id] 都画出 canvas,且 canvas 上有非白像素(不是空白图)
    ④ 悬停:随机抽 3 张图悬停,tooltip 出现且带单位;含 null 的图悬停到该类目显示「—」
    ⑤ 每个「表格视图」details 可展开,展开后有表格行
    ⑥ 目录每个链接点击后目标标题滚到视口顶部附近(或页面已到底),hash 同步
    ⑦ 所有 <img> 为 data: 内嵌、已解码,位图最长边 ≤1600
    ⑧ 窄屏(390 宽)无横向滚动,目录隐藏、目录按钮出现(--narrow)
    ⑨ 打印:emulate print 后目录隐藏(并导出 PDF 检查可生成)
截图(--shots):页首视口、KPI + 表、首张图面板、两图并排、结构图、时间轴、三图并排、原图面板、流程图、提示块、
    卡片、瀑布图、目录;给了 --ref 时对参考报告同位置(页首、KPI、表、首图、时间轴、原图、提示块、目录)截图对比。
"""
from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 压力样例与打印 PDF 写到临时目录(skill 安装目录可能只读),--workdir 可改
WORK = Path(tempfile.gettempdir()) / "tsp_selftest_v32"

JS_CANVAS_CHECK = r"""
() => {
  const out = [];
  document.querySelectorAll('.chart[id]').forEach(el => {
    const cv = el.querySelector('canvas');
    let ink = 0, tot = 0;
    if (cv && cv.width && cv.height) {
      try {
        const ctx = cv.getContext('2d');
        const w = cv.width, h = cv.height;
        const d = ctx.getImageData(0, 0, w, h).data;
        for (let i = 0; i < d.length; i += 4 * 7) {  // 抽样
          tot++;
          if (d[i + 3] > 0 && (d[i] < 235 || d[i + 1] < 235 || d[i + 2] < 235)) ink++;
        }
      } catch (e) { ink = -1; }
    }
    out.push({id: el.id, canvas: !!cv, w: cv ? cv.width : 0, h: cv ? cv.height : 0,
              ink: tot ? ink / tot : 0, err: !!el.querySelector('.chart-err')});
  });
  return out;
}
"""


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def shoot(page, sel, path, pad=0, nth=0):
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    loc = page.locator(sel)
    if loc.count() <= nth:
        return None
    el = loc.nth(nth)
    el.scroll_into_view_if_needed()
    page.wait_for_timeout(700)
    el.screenshot(path=str(path))
    return str(path)


def scroll_through(page, step=700):
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    h = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < h:
        page.evaluate("window.scrollTo(0, %d)" % y)
        page.wait_for_timeout(35)
        y += step
        h = page.evaluate("document.documentElement.scrollHeight")
    page.evaluate("window.scrollTo(0, 0)")


def test_page(pw, html: Path, shots: Path = None, ref: Path = None, narrow: bool = True) -> dict:
    res = {"file": str(html), "checks": {}, "fails": [], "shots": []}
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    external, errors = [], []

    def on_route(route):
        u = route.request.url
        if u.startswith("file:") or u.startswith("data:") or u.startswith("blob:") or u.startswith("about:"):
            return route.continue_()
        external.append(u)
        return route.abort()
    ctx.route("**/*", on_route)
    page = ctx.new_page()
    page.on("console", lambda m: errors.append("console.%s: %s" % (m.type, m.text)) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
    t0 = time.time()
    page.goto(html.as_uri(), wait_until="load")
    res["load_s"] = round(time.time() - t0, 2)
    # ③ 所有图画出 canvas:先看懒加载是否按视口工作,再滚动 + 等待空闲队列画完
    page.wait_for_timeout(150)
    early = page.evaluate("window.__charts ? window.__charts.made : -1")
    scroll_through(page)
    total = page.evaluate("window.__charts ? window.__charts.total : 0")
    for _ in range(80):
        made = page.evaluate("window.__charts ? window.__charts.made : 0")
        if made >= total:
            break
        page.wait_for_timeout(100)
    cv = page.evaluate(JS_CANVAS_CHECK)
    no_canvas = [c["id"] for c in cv if not c["canvas"] or c["err"]]
    blank = [c["id"] for c in cv if c["canvas"] and 0 <= c["ink"] < 0.004]
    res["checks"]["charts"] = dict(total=total, made=page.evaluate("window.__charts.made"), containers=len(cv),
                                   made_before_scroll=early, no_canvas=no_canvas, blank=blank,
                                   min_ink=round(min([c["ink"] for c in cv] or [0]), 4))
    if no_canvas or len(cv) != total:
        res["fails"].append("图表未画出 canvas: %s" % no_canvas)
    if blank:
        res["fails"].append("空白图: %s" % blank)
    # ④ 悬停 tooltip
    ids = [c["id"] for c in cv]
    random.seed(7)
    pick = random.sample(ids, min(3, len(ids)))
    tips = []
    specs = page.evaluate("JSON.parse(document.getElementById('chart-specs').textContent)")
    by = {s["dom"]: s for s in specs}
    null_target = None
    for s in specs:
        if s["type"] in ("pie", "waterfall"):
            continue
        for se in s["series"]:
            if any(v is None for v in se["data"]) and not all(v is None for v in se["data"]):
                k = se["data"].index(None)
                if all(se2["data"][k] is None for se2 in s["series"]):
                    continue
                null_target = (s["dom"], k)
                break
        if null_target:
            break
    targets = [(p, None) for p in pick] + ([null_target] if null_target else [])
    for dom, k in targets:
        s = by[dom]
        el = page.locator("#" + dom)
        el.scroll_into_view_if_needed()
        page.wait_for_timeout(250)
        box = el.bounding_box()
        if s["type"] == "pie":
            x, y = box["x"] + box["width"] * 0.5 + box["height"] * 0.27, box["y"] + box["height"] * 0.56
        elif s["type"] == "barh":
            x, y = box["x"] + box["width"] * 0.3, box["y"] + box["height"] * 0.5
        else:
            n = len(s["categories"])
            kk = k if k is not None else n // 2
            px = page.evaluate("""([dom, kk]) => { const c = echarts.getInstanceByDom(document.getElementById(dom));
                 const p = c.convertToPixel({xAxisIndex: 0}, kk); return p; }""", [dom, kk])
            x, y = box["x"] + px, box["y"] + box["height"] * 0.55
        page.mouse.move(x, y)
        page.wait_for_timeout(450)
        txt = page.evaluate("""(dom) => { const el = document.getElementById(dom);
             const ds = Array.from(el.querySelectorAll('div')).filter(d => d.style && d.style.position === 'absolute' && d.innerText && getComputedStyle(d).display !== 'none' && getComputedStyle(d).opacity !== '0');
             return ds.map(d => d.innerText).join(' | '); }""", dom)
        unit = s.get("unit") or ""
        ok = bool(txt.strip())
        rec = dict(dom=dom, type=s["type"], text=txt[:160].replace("\n", " "), ok=ok)
        if k is not None:
            rec["null_idx"] = k
            rec["dash_ok"] = "—" in txt
            if not rec["dash_ok"]:
                res["fails"].append("null 值悬停未显示「—」: %s" % dom)
        if unit and ok and s["type"] not in ("pie",):
            rec["unit_ok"] = unit in txt or (unit == "%" and "%" in txt)
            if not rec["unit_ok"]:
                res["fails"].append("tooltip 未带单位: %s" % dom)
        if not ok:
            res["fails"].append("悬停无 tooltip: %s" % dom)
        tips.append(rec)
        page.mouse.move(5, 5)
    res["checks"]["tooltips"] = tips
    # ⑤ 表格视图
    dv = page.evaluate("""() => { const out = []; document.querySelectorAll('details.dv').forEach((d, i) => {
          d.querySelector('summary').click(); out.push({i, open: d.open, rows: d.querySelectorAll('tbody tr').length,
          vis: d.querySelector('table').getBoundingClientRect().height > 0}); d.open = false; }); return out; }""")
    bad_dv = [d for d in dv if not (d["open"] and d["rows"] > 0 and d["vis"])]
    n_fig_charts = page.evaluate("document.querySelectorAll('figure.cfig').length")
    n_fig_dv = page.evaluate("document.querySelectorAll('figure.cfig details.dv').length")
    res["checks"]["table_views"] = dict(count=len(dv), bad=len(bad_dv), charts_with_view=n_fig_dv, chart_figs=n_fig_charts)
    if bad_dv:
        res["fails"].append("表格视图展开失败 %d 个" % len(bad_dv))
    # 用真实点击再测一个
    if dv:
        s0 = page.locator("details.dv > summary").first
        s0.scroll_into_view_if_needed()
        s0.click()
        page.wait_for_timeout(150)
        res["checks"]["table_view_click"] = page.evaluate("document.querySelector('details.dv').open")
        if not res["checks"]["table_view_click"]:
            res["fails"].append("表格视图鼠标点击未展开")
        s0.click()
    # ⑥ 目录链接(恢复页面自带的平滑滚动,测真实点击)
    page.evaluate("document.documentElement.style.scrollBehavior = ''")
    links = page.evaluate("Array.from(document.querySelectorAll('nav.toc a[href^=\"#\"]')).map(a => a.getAttribute('href'))")
    bad_links = []
    for hrf in links:
        page.locator('nav.toc a[href="%s"]' % hrf).click()
        ok = False
        for _ in range(30):
            page.wait_for_timeout(60)
            st = page.evaluate("""(h) => { const t = document.getElementById(h.slice(1)); if (!t) return null;
                 const r = t.getBoundingClientRect(); const se = document.scrollingElement;
                 return {top: r.top, hash: location.hash, atEnd: Math.abs(se.scrollTop + innerHeight - se.scrollHeight) < 3}; }""", hrf)
            if st and st["hash"] == hrf and (-3 <= st["top"] <= 60 or (st["atEnd"] and st["top"] >= -3)):
                ok = True
                break
        if not ok:
            bad_links.append((hrf, st))
    active = page.evaluate("(document.querySelector('nav.toc a.on')||{}).textContent || ''")
    res["checks"]["toc"] = dict(links=len(links), bad=bad_links, active_after_last_click=active)
    if bad_links:
        res["fails"].append("目录链接未跳转到位: %s" % bad_links[:5])
    if not links:
        res["fails"].append("目录为空")
    # ⑦ 图片
    imgs = page.evaluate("""() => Array.from(document.querySelectorAll('main img')).map(im => ({data: im.src.startsWith('data:'),
            w: im.naturalWidth, h: im.naturalHeight, mime: im.src.slice(5, im.src.indexOf(';')), kb: Math.round(im.src.length * 0.75 / 1024)}))""")
    bad_img = [i for i in imgs if not i["data"] or not i["w"]]
    big = [i for i in imgs if max(i["w"], i["h"]) > 1600]
    res["checks"]["images"] = dict(count=len(imgs), bad=bad_img, over_1600=big, detail=imgs)
    if bad_img:
        res["fails"].append("图片未内嵌或未解码 %d" % len(bad_img))
    if big:
        res["fails"].append("图片最长边 >1600: %s" % big)
    # 统计
    res["checks"]["dom"] = page.evaluate("""() => ({
        figures: document.querySelectorAll('main figure').length,
        chart_figs: document.querySelectorAll('main figure.cfig').length,
        shots: document.querySelectorAll('main figure.shot').length,
        flows: document.querySelectorAll('main figure.flowfig').length,
        chains: document.querySelectorAll('main figure.chainfig').length,
        tl_figs: document.querySelectorAll('main figure.tlfig').length,
        tables: document.querySelectorAll('main .tblock table').length,
        kpis: document.querySelectorAll('.kpi').length,
        notes: document.querySelectorAll('.note').length,
        leads: document.querySelectorAll('.lead').length,
        two_up: document.querySelectorAll('.two-up').length, three_up: document.querySelectorAll('.three-up').length,
        rl: document.querySelectorAll('.rl').length, tags: document.querySelectorAll('main .tag').length,
        num_right: document.querySelectorAll('.tblock td.n').length,
        tot_rows: document.querySelectorAll('.tblock tr.tot').length,
        captions: document.querySelectorAll('.tblock caption').length,
        figcaptions: document.querySelectorAll('main figure figcaption').length,
        footer: !!document.querySelector('.footer'), meta: !!document.querySelector('.meta'),
        nav_brand: (document.querySelector('nav.toc .brand')||{}).innerText || '',
        nav_date: (document.querySelector('nav.toc .date')||{}).innerText || '',
        nav_groups: Array.from(document.querySelectorAll('nav.toc .grp')).map(g => g.innerText),
        hscroll: document.scrollingElement.scrollWidth > innerWidth + 1,
        ext_attr: document.documentElement.outerHTML.match(/(?:src|href)="https?:\\/\\/(?!example\\.com)/g) || []
    })""")
    # 截图(程序滚动一律关掉平滑滚动,避免截到滚动中途)
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(500)
        p = shots / "v32_01_top.png"
        page.screenshot(path=str(p))
        res["shots"].append(str(p))
        plan = [("v32_02_kpis", ".kpis"), ("v32_03_table", ".tblock"), ("v32_04_chart", "figure.cfig"),
                ("v32_05_twoup", ".two-up"), ("v32_06_chain", "figure.chainfig"), ("v32_07_timeline", "figure.tlfig"),
                ("v32_08_threeup", ".three-up"), ("v32_09_shot", "main > figure.shot"), ("v32_10_flow", "figure.flowfig"),
                ("v32_11_flow_lanes", "figure.flowfig"), ("v32_12_note", ".note"), ("v32_13_cards", ".cards"),
                ("v32_14_waterfall", "#c_a_bridge"), ("v32_15_figidx", "details.figidx"),
                ("v32_21_lineup", "figure.lineupfig"), ("v32_22_threeup_mix", ".three-up"),
                ("v32_23_line_segments", "figure.cfig:has(#c_a_gm_hist)"), ("v32_24_bar_highlight", "figure.cfig:has(#c_b_mkt)"),
                ("v32_25_stack_tall", "figure.cfig:has(#c_a_mkt)")]
        for name, sel in plan:
            nth = 1 if name in ("v32_11_flow_lanes", "v32_22_threeup_mix") else 0
            if name == "v32_14_waterfall":
                sel = "figure.cfig:has(#c_a_bridge)"
            if name == "v32_15_figidx":
                page.evaluate("document.querySelector('details.figidx') && (document.querySelector('details.figidx').open = true)")
            r = shoot(page, sel, shots / (name + ".png"), nth=nth)
            if r:
                res["shots"].append(r)
        # 表格视图展开态
        d = page.locator("figure.cfig").first
        d.scroll_into_view_if_needed()
        page.locator("figure.cfig details.dv > summary").first.click()
        page.wait_for_timeout(300)
        d.screenshot(path=str(shots / "v32_16_tableview_open.png"))
        res["shots"].append(str(shots / "v32_16_tableview_open.png"))
        # 悬停态
        el = page.locator(".chart[id]").first
        el.scroll_into_view_if_needed()
        bx = el.bounding_box()
        page.mouse.move(bx["x"] + bx["width"] * 0.62, bx["y"] + bx["height"] * 0.6)
        page.wait_for_timeout(500)
        page.locator("figure.cfig").first.screenshot(path=str(shots / "v32_17_tooltip.png"))
        res["shots"].append(str(shots / "v32_17_tooltip.png"))
        page.mouse.move(3, 3)
        # 目录(吸顶)滚到中段
        page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight * 0.45)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(shots / "v32_18_mid_sticky_toc.png"))
        res["shots"].append(str(shots / "v32_18_mid_sticky_toc.png"))
    # ⑨ 打印:视口先设成 A4 纸面宽度(794px)再切 print 媒体,模拟浏览器打印时的版面宽度
    page.set_viewport_size({"width": 794, "height": 1123})
    page.wait_for_timeout(300)
    page.emulate_media(media="print")
    page.wait_for_timeout(500)
    res["checks"]["print_chart_fit"] = page.evaluate("""() => Array.from(document.querySelectorAll('.chart[id]')).filter(el => {
        const cv = el.querySelector('canvas'); if (!cv) return false;
        return cv.getBoundingClientRect().width > el.getBoundingClientRect().width + 2; }).map(el => el.id)""")
    if res["checks"]["print_chart_fit"]:
        res["fails"].append("打印时图宽超出容器: %s" % res["checks"]["print_chart_fit"][:5])
    res["checks"]["print_nav_hidden"] = page.evaluate("getComputedStyle(document.querySelector('nav.toc')).display === 'none'")
    if not res["checks"]["print_nav_hidden"]:
        res["fails"].append("打印时目录未隐藏")
    try:
        pdf = (shots or WORK) / (html.stem + "_print.pdf")
        page.pdf(path=str(pdf), format="A4", print_background=True)
        res["checks"]["print_pdf_kb"] = round(pdf.stat().st_size / 1024)
        if shots is None:
            pdf.unlink()
    except Exception as e:  # noqa: BLE001
        res["checks"]["print_pdf_err"] = str(e)[:200]
    page.emulate_media(media="screen")
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(300)
    # ⑧ 窄屏
    if narrow:
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        nr = page.evaluate("""() => ({hscroll: document.scrollingElement.scrollWidth > innerWidth + 1,
             sw: document.scrollingElement.scrollWidth,
             nav: getComputedStyle(document.querySelector('nav.toc')).display,
             btn: getComputedStyle(document.getElementById('tocbtn')).display})""")
        res["checks"]["narrow_390"] = nr
        if nr["hscroll"]:
            wide = page.evaluate("""() => Array.from(document.querySelectorAll('main *')).filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.tbl-wrap') && !e.closest('.svgwrap')).slice(0, 8).map(e => e.tagName + '.' + e.className)""")
            res["fails"].append("390 宽出现横向滚动: %s" % wide)
        if nr["nav"] != "none" or nr["btn"] == "none":
            res["fails"].append("窄屏目录未隐藏 / 目录按钮未出现")
        if shots:
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(300)
            page.screenshot(path=str(shots / "v32_19_mobile_top.png"))
            res["shots"].append(str(shots / "v32_19_mobile_top.png"))
            fl = page.locator("figure.flowfig").first
            if fl.count():
                fl.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                fl.screenshot(path=str(shots / "v32_20_mobile_flow.png"))
                res["shots"].append(str(shots / "v32_20_mobile_flow.png"))
        page.set_viewport_size({"width": 1440, "height": 900})
    res["checks"]["js_errors"] = errors
    res["checks"]["external_requests"] = external
    if errors:
        res["fails"].append("JS 报错 %d: %s" % (len(errors), errors[:3]))
    if external:
        res["fails"].append("外部请求 %d: %s" % (len(external), external[:3]))
    browser.close()
    # 参考报告同位置截图
    if ref and shots:
        res["ref_shots"] = ref_shots(pw, ref, shots)
    return res


def ref_shots(pw, ref: Path, shots: Path) -> list:
    out = []
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:", "about:")) else r.abort())
    page = ctx.new_page()
    page.goto(ref.as_uri(), wait_until="load")
    page.wait_for_timeout(1200)
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    page.screenshot(path=str(shots / "ref_01_top.png"))
    out.append(str(shots / "ref_01_top.png"))
    plan = [("ref_02_kpis", ".kpis", 0), ("ref_03_table", "main > .tbl-wrap", 0), ("ref_04_chart", "figure", 0),
            ("ref_07_timeline", ".tl", 0), ("ref_09_shot", ".shot", 0), ("ref_12_note", ".note", 0),
            ("ref_05_barh", "figure:has(#c_inv_share)", 0)]
    for name, sel, nth in plan:
        r = shoot(page, sel, shots / (name + ".png"), nth=nth)
        if r:
            out.append(r)
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight * 0.45)")
    page.wait_for_timeout(600)
    page.screenshot(path=str(shots / "ref_18_mid_sticky_toc.png"))
    out.append(str(shots / "ref_18_mid_sticky_toc.png"))
    m = page.evaluate("""() => { const q = s => document.querySelector(s); const cs = (s, p) => q(s) ? getComputedStyle(q(s))[p] : null;
        return {nav_w: q('nav') && q('nav').getBoundingClientRect().width, main_pad: cs('main', 'padding'),
                h2: cs('h2', 'fontSize'), h3: cs('h3', 'fontSize'), body: cs('body', 'fontSize'), th_bg: cs('th', 'backgroundColor'),
                fig_radius: cs('figure', 'borderRadius'), chart_h: q('.chart') && q('.chart').getBoundingClientRect().height,
                figures: document.querySelectorAll('figure').length, shots: document.querySelectorAll('.shot').length}; }""")
    (shots / "ref_metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    browser.close()
    return out


def metrics(pw, html: Path) -> dict:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(html.as_uri(), wait_until="load")
    page.wait_for_timeout(300)
    m = page.evaluate("""() => { const q = s => document.querySelector(s); const cs = (s, p) => q(s) ? getComputedStyle(q(s))[p] : null;
        return {nav_w: q('nav') && q('nav').getBoundingClientRect().width, main_pad: cs('main', 'padding'),
                h2: cs('h2', 'fontSize'), h3: cs('h3', 'fontSize'), body: cs('body', 'fontSize'), th_bg: cs('th', 'backgroundColor'),
                fig_radius: cs('figure', 'borderRadius'), chart_h: q('.chart') && q('.chart').getBoundingClientRect().height}; }""")
    browser.close()
    return m


# ---------------------------------------------------------------- 压力样例(60+ 图)
def make_stress_images(d: Path, n: int) -> list:
    """合成 n 张互不相同的示意位图(渲染器对同一文件重复出图只计一次,压力样例必须用不同文件);
    每 4 张里有 1 张 2400px 宽 PNG 噪声图,检验「照片转 JPEG q82、最长边 ≤1600」。"""
    from PIL import Image, ImageDraw
    d.mkdir(parents=True, exist_ok=True)
    out = []
    rnd = random.Random(5)
    for k in range(n):
        big = (k % 4 == 3)
        w, h = (2400, 1350) if big else (1100, 650)
        p = d / ("st_%02d.%s" % (k, "png" if big else "jpg"))
        if not p.exists():
            base = tuple(rnd.randint(170, 245) for _ in range(3))
            im = Image.new("RGB", (w, h), base)
            dr = ImageDraw.Draw(im)
            for _ in range(40):
                x0, y0 = rnd.randint(0, w - 50), rnd.randint(0, h - 50)
                dr.rectangle([x0, y0, x0 + rnd.randint(30, w // 4), y0 + rnd.randint(20, h // 4)],
                             fill=tuple(rnd.randint(20, 230) for _ in range(3)))
            if big:  # 加噪声,让它被判成照片
                px = im.load()
                for _ in range(w * h // 6):
                    x, y = rnd.randrange(w), rnd.randrange(h)
                    r, g, b_ = px[x, y]
                    px[x, y] = ((r + rnd.randint(-40, 40)) % 256, (g + rnd.randint(-40, 40)) % 256, (b_ + rnd.randint(-40, 40)) % 256)
            dr.text((20, 20), "stress image %02d" % k, fill=(0, 0, 0))
            if p.suffix == ".jpg":
                im.save(p, quality=90)
            else:
                im.save(p)
        out.append(p)
    return out


def make_stress_md(path: Path, n_charts=None, n_flows=None, n_images=None) -> Path:
    """按设计规格 §3 的分章下限排一份 60+ 图的样例(数字为虚构演示值):总览 7、三个主业章各 13(行业规模 2、
    竞争格局 1、历史演变 1 + 流程 1、具体产品 谱系 1 + 原图 2 + 流程 1、核心竞争要点 1、公司优势 2 + 结构图 1)、
    非主业 4、UE 9(两两并排)、跟什么走 5、正在变什么 3。验证渲染器在用户要求的 55–70 张图规模下全部画出、验收可过。"""
    rnd = random.Random(11)
    imgs = make_stress_images(path.parent / "fixture_images" / "stress", 18)
    rel = lambda p: p.relative_to(path.parent).as_posix()  # noqa: E731
    cats = ["2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026E"]
    types = ["stack", "bar", "line", "group", "combo", "area", "barh", "pie", "waterfall"]
    seq = {"c": 0}
    para = ("压力样例正文,用来撑起篇幅并检查长文下的目录高亮、懒加载与打印分页。**这里是一处加粗的核心判断**,"
            "后面接一句普通叙述,说明数字从哪里来、为什么要紧、什么时候能验证。")

    def chart(ch_no, t=None, title=None):
        seq["c"] += 1
        k = seq["c"]
        t = t or types[k % len(types)]
        ttl = title or "图 %d-%d %s 演示" % (ch_no, k, t)
        if t == "pie":
            sp = {"type": "pie", "data": [{"name": "甲", "value": 40}, {"name": "乙", "value": 35}, {"name": "丙", "value": 25}], "unit": "亿元"}
        elif t == "waterfall":
            sp = {"type": "waterfall", "categories": ["单价", "成本一", "成本二", "费用", "毛利"],
                  "series": [{"name": "元/W", "data": [1.0, -0.4, -0.15, -0.05, 0.4]}], "totals": ["单价", "毛利"], "unit": "元/W", "digits": 2}
        elif t == "barh":
            sp = {"type": "barh", "categories": ["厂商甲", "压力样例", "厂商乙", "其他厂商合计"], "series": [{"name": "份额", "data": [20, 15, 12, 53]}],
                  "unit": "%", "highlight": "压力样例", "height": "short"}
        elif t == "combo":
            sp = {"type": "combo", "categories": cats,
                  "series": [{"name": "收入", "type": "bar", "data": [rnd.randint(10, 90) for _ in cats]},
                             {"name": "毛利率", "type": "line", "yAxisIndex": 1, "unit": "%", "data": [round(rnd.uniform(15, 40), 1) for _ in cats]}],
                  "unit": "亿元", "y2_unit": "%", "forecast_from": "2026E"}
        else:
            ns = 1 if t == "bar" else 3
            sp = {"type": t, "categories": cats, "forecast_from": "2026E", "unit": "%" if t in ("line", "area") else "亿元",
                  "series": [{"name": "序列%d" % (j + 1), "data": [round(rnd.uniform(5, 60), 1) for _ in cats]} for j in range(ns)]}
            if t == "stack":
                sp["total_label"] = True
        sp.update({"id": "s%d" % k, "title": ttl, "source": "来源:压力样例(虚构数据,自测用)p%d" % k})
        return ["```chart", json.dumps(sp, ensure_ascii=False), "```", ""]

    def flow(title):
        fl = {"title": title, "subtitle": "自制 / 外协标签;橙框为价值集中工序",
              "steps": [{"label": "来料检验", "sub": "外购器件抽检", "tag": "外购", "phase": "来料"},
                        {"label": "SMT 贴片", "tag": "自制", "phase": "板级", "hot": True},
                        {"label": "功率模块", "tag": "自制", "phase": "整机"}, {"label": "整机装配", "phase": "整机"},
                        {"label": "老化测试", "phase": "整机"}, {"label": "物流", "tag": "外协", "phase": "交付"},
                        {"label": "并网调试", "phase": "交付", "note": "并网认证周期"}],
              "source": "来源:压力样例招股书 p60(虚构)"}
        return ["```flow", json.dumps(fl, ensure_ascii=False), "```", ""]

    def chain(title):
        c = {"title": title, "columns": [{"name": "上游", "nodes": [{"label": "器件", "muted": True}, {"label": "电芯"}]},
                                         {"name": "本公司", "me": True, "nodes": [{"label": "系统", "strong": True}]},
                                         {"name": "客户", "nodes": [{"label": "开发商"}, {"label": "电网"}]}],
             "links": [{"fwd": "采购", "back": "付款"}, {"fwd": "交付", "back": "货款"}], "source": "来源:压力样例(作者自绘)"}
        return ["```chain", json.dumps(c, ensure_ascii=False), "```", ""]

    def table(ch_no, k):
        return ["表 %d-%d　演示表" % (ch_no, k), "", "| 项目 | 2024 | 2025 |", "|---|---|---|",
                "| 收入(亿元) | 1,234.5 | 1,456.7 |", "| 合计 | 1,234.5 | 1,456.7 |", "", "> 来源:压力样例", ""]

    L = ["# 压力样例(999999.XX)业务认知", "", "> 2026-09-24 · 买方内部研究 · 渲染器压力自测:60+ 张图,数字全部为虚构演示值。", ""]
    # 一、总览 7
    L += ["## 一、公司总览", "", "> [!lead] 总览。", "", para * 6, ""]
    for _ in range(5):
        L += chart(1)
    L += ["```timeline", "title: 图 1-t 发展时间轴演示", "source: 来源:压力样例", "2001 | 成立 |", "2011 | 上市 | hot", "2025 | 新业务 |", "```", ""]
    L += chain("图 1-c 产业链与商业模式结构演示") + table(1, 1) + table(1, 2)
    # 二~四、主业 3 × 13
    for bi, name in enumerate(["业务 A", "业务 B", "业务 C"]):
        n = bi + 2
        L += ["## %s、%s" % ("二三四"[bi], name), "", "> [!lead] 主业章。", ""]
        L += ["### %d.1 行业规模" % n, "", para * 8, ""] + chart(n, "stack") + chart(n, "line")
        L += ["> [!note] 口径分歧:机构甲与机构乙数字并列。", ""]
        L += ["### %d.2 竞争格局" % n, "", para * 6, ""] + chart(n, "barh") + table(n, 1)
        L += ["### %d.3 历史演变" % n, "", para * 6, ""] + chart(n, "combo") + flow("图 %d-f1 生产流程演示:从来料到并网" % n)
        L += ["### %d.4 具体产品" % n, "", para * 8, ""]
        items = [{"img": rel(imgs[bi * 6 + j]), "label": "型号 %d" % j, "sub": "%d kW" % (50 * (j + 1)), "group": "组 %d" % (j // 2)} for j in range(4)]
        L += ["```lineup", json.dumps({"title": "图 %d-p 产品谱系演示" % n, "items": items, "source": "来源:压力样例官网(虚构)"}, ensure_ascii=False), "```", ""]
        L += ["![研报原图:参数对比演示 %d](%s \"来源:压力样例研报(虚构)p%d\")" % (n, rel(imgs[bi * 6 + 4]), n), ""]
        L += ["![示意图:原理拓扑演示 %d](%s \"来源:压力样例研报(虚构)p%d\")" % (n, rel(imgs[bi * 6 + 5]), n + 10), ""]
        L += flow("图 %d-f2 交付流程演示:订单到并网" % n)
        L += ["### %d.5 核心竞争要点" % n, "", para * 5, ""] + chart(n, "group")
        L += ["### %d.6 公司优势" % n, "", para * 6, ""] + chart(n, "bar") + chart(n, "area") + chain("图 %d-c 商业模式结构演示" % n) + table(n, 2)
    # 五、非主业 4
    L += ["## 五、非主要业务简述", "", para * 4, ""]
    for _ in range(4):
        L += chart(5)
    # 六、UE 9(两两并排)
    L += ["## 六、UE与经营效率", "", para * 4, ""]
    for _ in range(4):
        L += [":::two-up"] + chart(6, "line") + chart(6, "bar") + [":::", ""]
    L += chart(6, "waterfall") + table(6, 1)
    # 七、跟什么走 5;八、正在变什么 3
    L += ["## 七、跟什么走", "", para * 4, ""]
    for _ in range(5):
        L += chart(7)
    L += ["## 八、正在变什么", "", para * 4, ""]
    for _ in range(3):
        L += chart(8)
    L += table(8, 1)
    L += ["## 九、来源与口径", "", para, ""] + table(9, 1)
    path.write_text("\n".join(L), encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", nargs="?")
    ap.add_argument("--ref")
    ap.add_argument("--shots")
    ap.add_argument("--json")
    ap.add_argument("--no-narrow", action="store_true")
    ap.add_argument("--stress", action="store_true")
    ap.add_argument("--n-charts", type=int, default=40)
    ap.add_argument("--n-flows", type=int, default=12)
    ap.add_argument("--n-images", type=int, default=10)
    ap.add_argument("--workdir", help="压力样例输出目录(默认系统临时目录 tsp_selftest_v32/)")
    a = ap.parse_args(argv)
    global WORK
    if a.workdir:
        WORK = Path(a.workdir).resolve()
    WORK.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    results = {}
    if a.stress:
        md = make_stress_md(WORK / "fixture_stress.md", a.n_charts, a.n_flows, a.n_images)
        html = WORK / "fixture_stress.html"
        code, log = run([sys.executable, str(HERE / "render_report_v32.py"), str(md), "--out", str(html), "--gate",
                         "--stats", str(WORK / "fixture_stress_stats.json")])
        results["stress_render"] = dict(exit=code, log=log.strip().splitlines()[:14])
        a.html = str(html)
    if not a.html:
        ap.error("需要 html 或 --stress")
    with sync_playwright() as pw:
        r = test_page(pw, Path(a.html).resolve(), Path(a.shots).resolve() if a.shots else None,
                      Path(a.ref).resolve() if a.ref else None, narrow=not a.no_narrow)
        results["page"] = r
        results["metrics"] = metrics(pw, Path(a.html).resolve())
    fails = r["fails"][:]
    if a.stress and results["stress_render"]["exit"] != 0:
        fails.append("压力样例渲染 / 验收退出码 %d" % results["stress_render"]["exit"])
    results["fails"] = fails
    txt = json.dumps(results, ensure_ascii=False, indent=1)
    if a.json:
        Path(a.json).write_text(txt, encoding="utf-8")
    c = r["checks"]
    print("文件: %s(载入 %.2fs)" % (a.html, r["load_s"]))
    print("图表: 容器 %d / 画出 %d(滚动前已画 %d,懒加载);空白 %d;最小着色率 %s" % (
        c["charts"]["containers"], c["charts"]["made"], c["charts"]["made_before_scroll"], len(c["charts"]["blank"]), c["charts"]["min_ink"]))
    print("悬停: %s" % "; ".join("%s %s%s" % (t["dom"], "ok" if t["ok"] else "无", (" 「—」ok" if t.get("dash_ok") else "") if "null_idx" in t else "") for t in c["tooltips"]))
    print("表格视图: %d 个,坏 %d;交互图面板 %d 个中带表格视图 %d" % (c["table_views"]["count"], c["table_views"]["bad"], c["table_views"]["chart_figs"], c["table_views"]["charts_with_view"]))
    print("目录: %d 个链接,未到位 %d" % (c["toc"]["links"], len(c["toc"]["bad"])))
    print("图片: %d 张,未内嵌/未解码 %d,>1600px %d" % (c["images"]["count"], len(c["images"]["bad"]), len(c["images"]["over_1600"])))
    print("DOM: %s" % json.dumps({k: v for k, v in c["dom"].items() if k not in ("ext_attr",)}, ensure_ascii=False))
    if "narrow_390" in c:
        print("390 宽: %s" % c["narrow_390"])
    print("打印: 目录隐藏 %s;PDF %s KB" % (c["print_nav_hidden"], c.get("print_pdf_kb")))
    print("JS 报错 %d;外部请求 %d" % (len(c["js_errors"]), len(c["external_requests"])))
    if a.stress:
        print("压力样例渲染: exit=%s\n  %s" % (results["stress_render"]["exit"], "\n  ".join(results["stress_render"]["log"])))
    print("结果: %s" % ("通过" if not fails else "未通过 → " + ";".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
