#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""deploy_page.py — 把一页纸放上「反馈平台」（Cloudflare Worker + 静态资源），读者即可在线标注。

典型用法：
  # 首次（先按 feedback/worker/wrangler.toml 顶部三步建好 KV + secret）
  python scripts/deploy_page.py --ticker 688629 --model _workspace/688629/page_model.json \
      --endpoint https://onepager-feedback.<子域>.workers.dev
  # 之后更新（endpoint 已记在 feedback_config.json，不用再给）
  python scripts/deploy_page.py --ticker 688629 --model _workspace/688629/page_model.json --version v3

做四件事：
  1) （给了 --model 就）调 build_page.py 重建 HTML，把 endpoint/version 烧进页面
  2) 拷进 feedback/worker/site/<ticker>/index.html （多标的共存，历次报告都留着）
  3) 重生成 site/index.html 报告索引
  4) wrangler deploy（--no-deploy 可只 stage 不上线）
洁净闸：site/ 只允许 .html —— 任何 .env/.json/密钥文件在这里都会拦住不上线。
"""
import argparse, io, json, os, re, shutil, subprocess, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
WORKER = os.path.join(SKILL, "feedback", "worker")
SITE = os.path.join(WORKER, "site")
CFG = os.path.join(HERE, "feedback_config.json")
ALLOW_EXT = {".html"}


def cfg():
    try:
        return json.load(io.open(CFG, encoding="utf-8")) or {}
    except Exception:
        return {}


def save_cfg(d):
    cur = cfg(); cur.update({k: v for k, v in d.items() if v})
    json.dump(cur, io.open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def page_meta(path):
    """从已建好的 html 里抠标题/版本（生成索引用，不解析 JS）。"""
    try:
        s = io.open(path, encoding="utf-8").read(400000)
    except Exception:
        return {"title": os.path.basename(os.path.dirname(path)), "version": ""}
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    v = re.search(r'"version"\s*:\s*"([^"]{1,20})"', s)
    return {"title": (t.group(1).strip() if t else ""), "version": (v.group(1) if v else "")}


def build_index():
    rows = []
    for name in sorted(os.listdir(SITE)) if os.path.isdir(SITE) else []:
        d = os.path.join(SITE, name)
        idx = os.path.join(d, "index.html")
        if not os.path.isdir(d) or not os.path.exists(idx):
            continue
        m = page_meta(idx)
        rows.append((name, m["title"] or name, m["version"],
                     date.fromtimestamp(os.path.getmtime(idx)).isoformat()))
    html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>公司认知一页纸 · 报告库</title>
<style>:root{--bg:#fdfcf9;--panel:#fff;--fg:#1a1c22;--muted:#565d6b;--line:#e3dfd4;--accent:#14384f}
@media(prefers-color-scheme:dark){:root{--bg:#16171b;--panel:#1c1e24;--fg:#e9e6dd;--muted:#a2a9b6;--line:#2c2f38;--accent:#8fb3cc}}
body{margin:0;background:var(--bg);color:var(--fg);font-family:"Times New Roman","KaiTi","楷体",serif;font-size:16px;line-height:1.7}
main{max-width:820px;margin:0 auto;padding:48px 22px 80px}
h1{color:var(--accent);font-size:24px;border-bottom:2px solid var(--accent);padding-bottom:8px}
p.cap{color:var(--muted);font-size:13.5px}
a.card{display:block;text-decoration:none;color:inherit;background:var(--panel);border:1px solid var(--line);
border-left:3px solid var(--accent);border-radius:0 4px 4px 0;padding:13px 17px;margin:11px 0}
a.card:hover{border-left-width:6px}
.t{font-weight:700;font-size:17px}.m{color:var(--muted);font-size:12.5px;font-variant-numeric:tabular-nums}
.v{display:inline-block;background:var(--accent);color:#fff;font-size:11px;font-weight:700;padding:1px 8px;border-radius:2px;margin-left:8px;vertical-align:2px}
</style></head><body><main><h1>公司认知一页纸 · 报告库</h1>
<p class="cap">点进任一报告 → 选中文字或点模块右上 <b>✎</b> 提疑问 → 「同步到云端」；我汇总后重出新版，页顶会有「本版反馈回应」。</p>
"""
    if not rows:
        html += '<p class="cap">（还没有报告，先跑 deploy_page.py --ticker …）</p>'
    for name, title, ver, mt in rows:
        html += ('<a class="card" href="./%s/"><div class="t">%s%s</div><div class="m">%s · 更新 %s</div></a>\n'
                 % (name, title or name, ('<span class="v">%s</span>' % ver) if ver else "", name, mt))
    html += "</main></body></html>\n"
    io.open(os.path.join(SITE, "index.html"), "w", encoding="utf-8", newline="\n").write(html)
    return len(rows)


def clean_gate():
    bad = []
    for root, _dirs, files in os.walk(SITE):
        for f in files:
            if os.path.splitext(f)[1].lower() not in ALLOW_EXT:
                bad.append(os.path.relpath(os.path.join(root, f), SITE))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--model", help="page_model.json（给了就重建 HTML，把 endpoint/version 烧进去）")
    ap.add_argument("--html", help="已建好的 onepager.html（不给 --model 时用；默认 _workspace/<ticker>/onepager.html）")
    ap.add_argument("--endpoint", help="Worker base URL（首次给一次，会存进 feedback_config.json）")
    ap.add_argument("--version", help="覆盖 meta.version（如 v3）")
    ap.add_argument("--no-deploy", action="store_true", help="只 stage 不上线")
    a = ap.parse_args()

    ws = os.path.join(SKILL, "_workspace", a.ticker)
    endpoint = a.endpoint or os.environ.get("FB_ENDPOINT") or cfg().get("endpoint") or ""
    if a.endpoint:
        save_cfg({"endpoint": a.endpoint.rstrip("/")})

    html = a.html or os.path.join(ws, "onepager.html")
    if a.model:
        cmd = [sys.executable, os.path.join(HERE, "build_page.py"), "--model", a.model, "--out", html]
        if endpoint:
            cmd += ["--endpoint", endpoint]
        if a.version:
            cmd += ["--version", a.version]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print((r.stdout or "").strip() or (r.stderr or "").strip())
        if r.returncode:
            raise SystemExit("build_page 失败")
    if not os.path.exists(html):
        raise SystemExit("找不到 HTML：%s（先 build_page.py 或给 --model）" % html)
    if not endpoint:
        print("⚠️ 未配 endpoint —— 页面将是纯本地模式（读者只能导出 JSON / 复制摘要）。给一次 --endpoint 即可。")

    dst_dir = os.path.join(SITE, a.ticker)
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copyfile(html, os.path.join(dst_dir, "index.html"))
    n = build_index()
    print("staged %s → site/%s/index.html（索引 %d 份报告）" % (os.path.basename(html), a.ticker, n))

    bad = clean_gate()
    if bad:
        raise SystemExit("洁净闸拦住：site/ 下有非 .html 文件，先删掉再部署 → %s" % bad[:10])
    if a.no_deploy:
        print("--no-deploy：已 stage，未上线。"); return

    toml = io.open(os.path.join(WORKER, "wrangler.toml"), encoding="utf-8").read()
    if "PASTE_KV_ID_AFTER_CREATE" in toml:
        raise SystemExit("wrangler.toml 里 KV id 还没填 —— 先按该文件顶部三步：wrangler login → "
                         "wrangler kv namespace create ANNOT → 填 id → wrangler secret put FB_ADMIN_TOKEN")
    r = subprocess.run("npx wrangler deploy", cwd=WORKER, shell=True, capture_output=True, text=True)
    out = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
    print(out[-2500:])
    if r.returncode:
        raise SystemExit("wrangler deploy 失败（首发偶发抖动，重试一次通常就过）")
    url = re.findall(r"https://[^\s]+workers\.dev", out)
    if url:
        base = url[0].rstrip("/")
        save_cfg({"endpoint": base})
        print("\n✅ 上线：%s/%s/　（索引页 %s/）" % (base, a.ticker, base))
        if not endpoint:
            print("   ⚠️ 本次页面里没烧 endpoint —— 用 --endpoint %s 再跑一次，读者才能一键同步标注。" % base)


if __name__ == "__main__":
    main()
