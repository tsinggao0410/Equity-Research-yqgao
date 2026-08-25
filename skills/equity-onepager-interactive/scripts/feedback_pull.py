#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""feedback_pull.py — 把读者在一页纸上的标注拉回来，汇总成「改稿清单」。

三种入口（任选，可混用）：
  A. 云端（配了 Worker）：
     python scripts/feedback_pull.py --ticker 688629 --only-new
  B. 页面导出的 JSON（纯本地模式 / 无云端）：
     python scripts/feedback_pull.py --ticker 688629 --from-file "C:/…/feedback_688629_v1_1753...json"
  C. 用户直接把「复制反馈摘要」的 MD 粘进对话 → 我手写 items 进 annotations.json 也行（本脚本非必须）。

产物（落 _workspace/<ticker>/feedback/）：
  annotations.json        总台账（跨轮累积，按 id 去重，保留 status）
  round_<n>.md            本轮 triage：按模块(JSON 路径)分组 + 每条建议动作 + 改稿清单
  round_<n>_resolutions.json  回应骨架（我填 answer/action）→ 交给 feedback_resolve.py 写回 page_model

配置：scripts/feedback_config.json {"endpoint":"https://…workers.dev","token":"…"}
     或环境变量 FB_ENDPOINT / FB_ADMIN_TOKEN；命令行 --endpoint/--token 优先。
"""
import argparse, io, json, os, re, sys, urllib.request, urllib.error
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
CFG = os.path.join(HERE, "feedback_config.json")

TYPE_LB = {"q": "没看懂", "d": "数据存疑", "s": "要原文", "i": "建议补", "o": "认可"}
TYPE_ACT = {
    "q": "把这段逻辑拆成 driver_chain 分步（每步 expr→val）或改写 model.logic；术语进脚注",
    "d": "回 RAG/iFind 复核该数字 → 若是口径打架 → 建/补 model.calibers 对账表；若是假设错 → 改 assume 并说明",
    "s": "rag_query.py get_doc 取原句 → 落 model.evidence[{doc_id,page,quote,implication}] 并在正文挂 [Ex] 角标",
    "i": "评估是否加情景/对标/分部；采纳则改模型并在 changelog 写清，不采纳则写不采纳理由",
    "o": "无需改稿（认可留痕）",
}
ORDER = {"d": 0, "s": 1, "q": 2, "i": 3, "o": 4}


def cfg():
    d = {}
    if os.path.exists(CFG):
        try:
            d = json.load(io.open(CFG, encoding="utf-8")) or {}
        except Exception:
            d = {}
    return d


def fetch_cloud(endpoint, token, rid, only_new):
    url = endpoint.rstrip("/") + "/api/ann?report_id=" + rid + ("&only_new=1" if only_new else "")
    req = urllib.request.Request(url, headers={"x-fb-token": token or ""})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            j = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:200]
        raise SystemExit("云端拉取失败 HTTP %s: %s\n（401=token 不对；先跑 curl %s/api/health 自检）" % (e.code, body, endpoint))
    except Exception as e:
        raise SystemExit("云端拉取失败：%s\n（没配云端就用 --from-file 读页面导出的 JSON）" % e)
    if not j.get("ok"):
        raise SystemExit("云端返回异常：%s" % j)
    return j.get("items") or []


def read_file(path):
    j = json.load(io.open(path, encoding="utf-8"))
    if isinstance(j, list):
        return j
    return j.get("items") or []


def md_escape(s):
    return re.sub(r"\s+", " ", str(s or "")).replace("|", "\\|").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True, help="report_id（通常裸代码，如 688629）")
    ap.add_argument("--endpoint"); ap.add_argument("--token")
    ap.add_argument("--from-file", action="append", default=[], help="页面导出的 feedback json（可多次给）")
    ap.add_argument("--only-new", action="store_true", help="云端只拉 status=new 的")
    ap.add_argument("--round", type=int, help="轮次号（默认自动 = 已有 round 文件数+1）")
    ap.add_argument("--ws", help="工作目录（默认 _workspace/<ticker>）")
    a = ap.parse_args()

    c = cfg()
    endpoint = a.endpoint or os.environ.get("FB_ENDPOINT") or c.get("endpoint") or ""
    token = a.token or os.environ.get("FB_ADMIN_TOKEN") or c.get("token") or ""

    ws = a.ws or os.path.join(SKILL, "_workspace", a.ticker)
    fdir = os.path.join(ws, "feedback")
    os.makedirs(fdir, exist_ok=True)

    incoming = []
    for f in a.from_file:
        incoming += read_file(f)
    if endpoint and not a.from_file:
        incoming += fetch_cloud(endpoint, token, a.ticker, a.only_new)
    if not incoming and not a.from_file:
        print("⚠️ 没配 endpoint 也没给 --from-file —— 无来源可拉。")
        print("   纯本地模式下：让用户在页面点「导出 JSON」发你，再 --from-file 读；或让用户点「复制反馈摘要」粘对话。")
        sys.exit(1)

    ledger_p = os.path.join(fdir, "annotations.json")
    ledger = []
    if os.path.exists(ledger_p):
        try:
            ledger = json.load(io.open(ledger_p, encoding="utf-8")) or []
        except Exception:
            ledger = []
    known = {x.get("id"): x for x in ledger if x.get("id")}
    fresh = []
    for it in incoming:
        i = it.get("id")
        if not i:
            continue
        if i in known:
            old = known[i]
            # 已处理过的条目：内容有更新才重新入本轮
            if (old.get("note") or "") == (it.get("note") or "") and old.get("status") in ("triaged", "resolved", "wontfix"):
                continue
            old.update({k: v for k, v in it.items() if v not in (None, "")})
            fresh.append(old)
        else:
            it.setdefault("status", "new")
            known[i] = it
            ledger.append(it)
            fresh.append(it)

    json.dump(ledger, io.open(ledger_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    n = a.round or (len([f for f in os.listdir(fdir) if re.match(r"round_\d+\.md$", f)]) + 1)
    if not fresh:
        print("本次没有新标注（台账 %d 条）。" % len(ledger))
        return

    fresh.sort(key=lambda x: (ORDER.get(x.get("type"), 9), x.get("path") or "", x.get("created") or ""))
    by_path = {}
    for it in fresh:
        by_path.setdefault(it.get("path") or "(未锚定模块)", []).append(it)

    L = ["# 反馈 triage · %s · round %d" % (a.ticker, n), "",
         "- 拉取日期：%s" % date.today().isoformat(),
         "- 本轮新增/更新：%d 条（台账累计 %d 条）" % (len(fresh), len(ledger)),
         "- 来源：%s" % ("云端 " + endpoint if endpoint and not a.from_file else "本地导出文件 " + ", ".join(a.from_file)),
         "", "## 按模块（JSON 路径 = 直接改这个字段）", ""]
    for path, its in sorted(by_path.items(), key=lambda kv: -len(kv[1])):
        L.append("### `%s`　（%d 条）" % (path, len(its)))
        L.append("")
        L.append("| id | 类型 | 章节 | 划中原文 | 读者疑问 | 建议动作 |")
        L.append("|---|---|---|---|---|---|")
        for it in its:
            t = it.get("type", "q")
            L.append("| `%s` | %s | %s | %s | %s | %s |" % (
                it.get("id", ""), TYPE_LB.get(t, t), md_escape(it.get("sec_title"))[:26],
                md_escape(it.get("quote"))[:90], md_escape(it.get("note")) or "—", TYPE_ACT.get(t, "")))
        L.append("")
    hard = [x for x in fresh if x.get("type") in ("d", "s", "q")]
    L += ["## 改稿清单（按此顺序做，做完一条勾一条）", ""]
    for it in hard:
        L.append("- [ ] `%s` %s → **%s**　｜ %s" % (
            it.get("id", ""), TYPE_LB.get(it.get("type"), ""), it.get("path") or "(待定位)",
            md_escape(it.get("note") or it.get("quote"))[:80]))
    L += ["", "## 纪律", "",
          "1. **每条都要有归宿**：改了 / 答了 / 明确待补（写清等什么数据、什么时点回填）——不许静默丢。",
          "2. 数据存疑类必须回一手源复核（RAG 原句 or iFind 原值），不能靠记忆答。",
          "3. 口径类疑问 → 一律建 `model.calibers` 对账表（差多少/选哪个/为什么），不要只在正文加一句解释。",
          "4. 填完 `round_%d_resolutions.json` 后跑：" % n,
          "   `python scripts/feedback_resolve.py --ticker %s --round %d --bump v<下一版>`" % (a.ticker, n),
          "   然后 `build_page.py` 重出页面 + `deploy_page.py` 上线，读者会在页顶看到「本版反馈回应」。"]

    md_p = os.path.join(fdir, "round_%d.md" % n)
    io.open(md_p, "w", encoding="utf-8", newline="\n").write("\n".join(L))

    res = [{"id": it.get("id"), "path": it.get("path") or "", "sec_title": it.get("sec_title") or "",
            "on_ver": it.get("ver") or "", "reader": it.get("reader") or "",
            "ask": (it.get("note") or it.get("quote") or "")[:300],
            "action": "fixed" if it.get("type") in ("d", "s") else ("answered" if it.get("type") == "q" else "pending"),
            "answer": ""} for it in fresh if it.get("type") != "o"]
    res_p = os.path.join(fdir, "round_%d_resolutions.json" % n)
    json.dump(res, io.open(res_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("wrote %s (%d 条)" % (md_p, len(fresh)))
    print("wrote %s  ← 填 answer/action(fixed|answered|pending) 后交给 feedback_resolve.py" % res_p)
    print("台账 %s（累计 %d 条）" % (ledger_p, len(ledger)))


if __name__ == "__main__":
    main()
