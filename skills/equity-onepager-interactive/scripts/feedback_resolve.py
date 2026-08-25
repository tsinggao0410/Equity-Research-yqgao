#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""feedback_resolve.py — 把「回应」写回 page_model，版本+1，并（可选）在云端标记已处理。

用法：
  1) 我按 round_<n>.md 逐条改完 page_model.json，并把答复填进 round_<n>_resolutions.json
     （每条：id / path / ask / action=fixed|answered|pending / answer）
  2) python scripts/feedback_resolve.py --ticker 688629 --round 2 --bump v3 \
       --changelog "v3：口径对账补齐、份额下调至 28%、每卡用量挂公司口径原句"
  3) python scripts/build_page.py --model _workspace/688629/page_model.json --out _workspace/688629/onepager.html
  4) python scripts/deploy_page.py --ticker 688629      （上线，读者即看到「本版反馈回应」）

写入 page_model：
  meta.version / meta.updated / meta.changelog
  feedback.resolved[]  ← action in (fixed, answered)
  feedback.open[]      ← action == pending（页面显示「待补数据」，诚实留白）
台账 annotations.json 里对应条目 status 置 resolved/triaged/wontfix。
"""
import argparse, io, json, os, urllib.request, urllib.error
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
CFG = os.path.join(HERE, "feedback_config.json")
ST = {"fixed": "resolved", "answered": "resolved", "pending": "triaged", "wontfix": "wontfix"}


def cfg():
    try:
        return json.load(io.open(CFG, encoding="utf-8")) or {}
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--bump", help="新版本号（如 v3）；不给则沿用现有 meta.version")
    ap.add_argument("--changelog", help="本版一句话变更（渲在「本版反馈回应」头部）")
    ap.add_argument("--model", help="page_model 路径（默认 _workspace/<ticker>/page_model.json）")
    ap.add_argument("--ws", help="工作目录（默认 _workspace/<ticker>）")
    ap.add_argument("--endpoint"); ap.add_argument("--token")
    ap.add_argument("--no-cloud", action="store_true", help="不回写云端 status")
    a = ap.parse_args()

    ws = a.ws or os.path.join(SKILL, "_workspace", a.ticker)
    fdir = os.path.join(ws, "feedback")
    model_p = a.model or os.path.join(ws, "page_model.json")
    res_p = os.path.join(fdir, "round_%d_resolutions.json" % a.round)
    for p in (model_p, res_p):
        if not os.path.exists(p):
            raise SystemExit("缺文件：%s" % p)

    model = json.load(io.open(model_p, encoding="utf-8"))
    res = json.load(io.open(res_p, encoding="utf-8")) or []

    bad = [r for r in res if not (r.get("answer") or "").strip()]
    if bad:
        raise SystemExit("以下条目 answer 为空（每条都必须有归宿：改了什么/答了什么/等什么数据）：\n  " +
                         "\n  ".join(str(r.get("id")) for r in bad))

    meta = model.setdefault("meta", {})
    fb = model.setdefault("feedback", {})
    fb.setdefault("report_id", (meta.get("ticker") or a.ticker).split(".")[0])
    fb.setdefault("rag_ws", fb["report_id"])
    if a.bump:
        meta["version"] = a.bump
    meta["updated"] = date.today().isoformat()
    if a.changelog:
        meta["changelog"] = a.changelog

    resolved = {r.get("id"): r for r in fb.get("resolved", []) if r.get("id")}
    openq = {r.get("id"): r for r in fb.get("open", []) if r.get("id")}
    n_fix = n_ans = n_pend = 0
    for r in res:
        rid = r.get("id")
        if not rid:
            continue
        act = (r.get("action") or "answered").lower()
        rec = {"id": rid, "path": r.get("path") or "", "sec_title": r.get("sec_title") or "",
               "on_ver": r.get("on_ver") or "", "reader": r.get("reader") or "",
               "ask": r.get("ask") or "", "answer": r.get("answer") or ""}
        openq.pop(rid, None); resolved.pop(rid, None)
        if act == "pending":
            rec["why_pending"] = rec.pop("answer")
            openq[rid] = rec; n_pend += 1
        else:
            rec["action"] = "fixed" if act == "fixed" else "answered"
            resolved[rid] = rec
            n_fix += 1 if act == "fixed" else 0
            n_ans += 1 if act != "fixed" else 0
    fb["resolved"] = list(resolved.values())
    fb["open"] = list(openq.values())
    json.dump(model, io.open(model_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("page_model 已更新：%s  version=%s  已改 %d / 已答 %d / 待补 %d"
          % (model_p, meta.get("version"), n_fix, n_ans, n_pend))

    led_p = os.path.join(fdir, "annotations.json")
    if os.path.exists(led_p):
        led = json.load(io.open(led_p, encoding="utf-8")) or []
        m = {r.get("id"): r for r in res}
        for it in led:
            if it.get("id") in m:
                it["status"] = ST.get((m[it["id"]].get("action") or "").lower(), "triaged")
                it["answer"] = m[it["id"]].get("answer") or ""
        json.dump(led, io.open(led_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("台账 status 已更新：%s" % led_p)

    c = cfg()
    endpoint = a.endpoint or os.environ.get("FB_ENDPOINT") or c.get("endpoint")
    token = a.token or os.environ.get("FB_ADMIN_TOKEN") or c.get("token")
    if endpoint and token and not a.no_cloud:
        for act, ids in (("resolved", [r["id"] for r in res if (r.get("action") or "") != "pending"]),
                         ("triaged", [r["id"] for r in res if (r.get("action") or "") == "pending"])):
            if not ids:
                continue
            body = json.dumps({"report_id": fb["report_id"], "ids": ids, "status": act}).encode("utf-8")
            req = urllib.request.Request(endpoint.rstrip("/") + "/api/status", data=body,
                                         headers={"content-type": "application/json", "x-fb-token": token})
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    print("云端 status(%s)：%s" % (act, r.read().decode("utf-8")[:120]))
            except urllib.error.HTTPError as e:
                print("⚠️ 云端 status 回写失败 HTTP %s（不影响本地）" % e.code)
            except Exception as e:
                print("⚠️ 云端 status 回写失败：%s（不影响本地）" % e)

    print("\n下一步：\n  python scripts/build_page.py --model %s --out %s\n  python scripts/deploy_page.py --ticker %s"
          % (model_p, os.path.join(ws, "onepager.html"), a.ticker))


if __name__ == "__main__":
    main()
