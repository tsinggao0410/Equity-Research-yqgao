#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_page.py — inline Chart.js + engine + app + page_model JSON into one
self-contained onepager.html. Deliberately thin: all rendering logic lives in
templates/app.js (client-side), all math in scripts/model_engine.js.

Usage:
  python build_page.py --model _workspace/<ticker>/page_model.json \
                       --out   _workspace/<ticker>/onepager.html
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)

def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def market_label(code):
    return {"A": "A股", "HK": "港股", "US": "美股"}.get((code or "A").upper(), code or "")

def build(model, template=None, chartjs=None, engine=None, app=None, annot=None, no_annot=False):
    template = template or os.path.join(SKILL, "templates", "onepager_template.html")
    chartjs  = chartjs  or os.path.join(SKILL, "scripts", "vendor", "chart.umd.min.js")
    engine   = engine   or os.path.join(SKILL, "scripts", "model_engine.js")
    app      = app      or os.path.join(SKILL, "templates", "app.js")
    annot    = annot    or os.path.join(SKILL, "templates", "annot.js")

    html = read(template)
    meta = model.get("meta", {})
    # 1) metadata tokens first (so any {{...}} inside injected JS is never touched)
    data_json = json.dumps(model, ensure_ascii=False).replace("</", "<\\/")
    repl = {
        "{{TITLE}}":  "%s %s · 认知一页纸" % (meta.get("name", ""), meta.get("ticker", "")),
        "{{NAME}}":   meta.get("name", ""),
        "{{TICKER}}": meta.get("ticker", ""),
        "{{MARKET}}": market_label(meta.get("market")),
        "{{DATA}}":   data_json,
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    # 2) inline the big JS payloads
    html = html.replace("/*__CHARTJS__*/", read(chartjs))
    html = html.replace("/*__ENGINE__*/",  read(engine))
    html = html.replace("/*__APP__*/",     read(app))
    # 3) 反馈标注层（annot.js）——可用 --no-annot 关掉（交付纯只读版时）
    html = html.replace("/*__ANNOT__*/", "" if no_annot else read(annot))
    return html


def to_artifact(html):
    """Body-only fragment (style block hoisted to top) for the Artifact wrapper,
    which supplies its own <!doctype>/<head>/<body>. Keeps all inline JS/CSS."""
    style = re.search(r"<style>.*?</style>", html, re.S)
    body = re.search(r"<body>(.*?)</body>", html, re.S)
    return (style.group(0) if style else "") + "\n" + (body.group(1) if body else html)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="page_model.json")
    ap.add_argument("--out", required=True, help="output onepager.html")
    ap.add_argument("--template"); ap.add_argument("--chartjs"); ap.add_argument("--engine"); ap.add_argument("--app")
    ap.add_argument("--annot", help="标注层 js（默认 templates/annot.js）")
    ap.add_argument("--no-annot", action="store_true", help="不内联反馈标注层（只读交付版）")
    ap.add_argument("--endpoint", help="反馈云端 base URL（写入 feedback.endpoint；不给则用 model 里的值/纯本地）")
    ap.add_argument("--version", help="覆盖 meta.version（如 v2）；同时刷 meta.updated")
    ap.add_argument("--mode", choices=["standalone", "artifact"], default="standalone",
                    help="standalone=full self-contained HTML; artifact=body-only fragment for claude.ai Artifact")
    a = ap.parse_args()
    with open(a.model, "r", encoding="utf-8") as f:
        model = json.load(f)
    # 反馈层配置：endpoint/report_id/rag_ws 缺省自动补，避免每次手写
    fb = model.setdefault("feedback", {})
    meta = model.setdefault("meta", {})
    tick = (meta.get("ticker") or "").strip()
    fb.setdefault("report_id", tick.split(".")[0] or "unknown")
    fb.setdefault("rag_ws", fb["report_id"])
    fb.setdefault("autosync", True)
    if a.endpoint:
        fb["endpoint"] = a.endpoint.rstrip("/")
    if a.version:
        meta["version"] = a.version
        meta["updated"] = __import__("datetime").date.today().isoformat()
    meta.setdefault("version", "v1")
    html = build(model, a.template, a.chartjs, a.engine, a.app, a.annot, a.no_annot)
    if a.mode == "artifact":
        html = to_artifact(html)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote %s (%d KB)" % (a.out, len(html.encode("utf-8")) // 1024))

if __name__ == "__main__":
    main()
