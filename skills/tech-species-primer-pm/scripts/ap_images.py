#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AlphaPai 研报原图:批量搜图 → 合并去重 → 按编号下载。只用 `image` 接口(recall 全文召回常报积分不足,不要调)。

用法(全局 --root 放在子命令前):
  python3 ap_images.py [--root R] search  "检索词1" "检索词2" ...   [--terms-file terms.txt] [--topk 40]
        每个词一次 alphapai_client.py image 调用,结果存 R/sources/alphapai/q/NN_词.json(已有则跳过,可断点续跑)
  python3 ap_images.py [--root R] merge
        合并 q/*.json → R/sources/alphapai/all_images.json(按 imageUrl 去重;每条加 _id、_page = pageIndex + 1、
        _inst 机构名、_queries 命中的检索词)。挑图时看 articleTitle / _inst / publishDate / _page / captionList。
  python3 ap_images.py [--root R] get 12 15 33 ... [--prefix c2_ap]
        下载选中的编号 → R/sources/alphapai/img/<prefix>_<id>.jpg,登记 selected.json(机构、日期、页码、原图注、URL)。
        下载后必须用 Read 看一眼:含公司盈利预测、估值、评级、目标价的原图不用;图题与内容对得上才复制进 images/。
客户端路径:环境变量 ALPHAPAI_CLIENT,否则 ~/.claude/skills/alphapai-research/scripts/alphapai_client.py。
来源行写法:「来源:<机构>(<报告封面日期>)p<_page> 图 x「原图注」」;AlphaPai 入库日可能比封面晚 1 天,以封面为准。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _card import find_root  # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
CLI = os.environ.get("ALPHAPAI_CLIENT") or os.path.expanduser("~/.claude/skills/alphapai-research/scripts/alphapai_client.py")


def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


args = sys.argv[1:]
root = opt(args, "--root")
R = find_root(root)
AP = R / "sources" / "alphapai"
(AP / "q").mkdir(parents=True, exist_ok=True)
if not args:
    sys.exit(__doc__)
cmd = args.pop(0)

if cmd == "search":
    topk = opt(args, "--topk", "40")
    tf = opt(args, "--terms-file")
    terms = list(args)
    if tf:
        terms += [t.strip() for t in Path(tf).read_text(encoding="utf-8").splitlines() if t.strip() and not t.startswith("#")]
    if not Path(CLI).exists():
        sys.exit("找不到 AlphaPai 客户端:%s(设 ALPHAPAI_CLIENT)" % CLI)
    start = len(list((AP / "q").glob("*.json")))
    for i, t in enumerate(terms, 1):
        safe = "".join(c if c.isalnum() else "_" for c in t)[:40]
        hit = list((AP / "q").glob("*_%s.json" % safe))
        if hit and hit[0].stat().st_size > 50:
            print("cached", t)
            continue
        fn = AP / "q" / ("%03d_%s.json" % (start + i, safe))
        p = subprocess.run([sys.executable, CLI, "image", "-q", t, "--files-range", "3", "8", "9", "--topk", topk, "--json"],
                           capture_output=True, text=True, timeout=180)
        try:
            d = json.loads(p.stdout.strip())
        except Exception:  # noqa: BLE001
            print("FAIL", t, (p.stdout + p.stderr)[:200])
            continue
        if isinstance(d, list):
            d = {"data": d}
        d["_query"] = t
        fn.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(t, len(d.get("data") or []), flush=True)
        time.sleep(1.0)

elif cmd == "merge":
    seen, order = {}, []
    for fn in sorted((AP / "q").glob("*.json")):
        d = json.loads(fn.read_text(encoding="utf-8"))
        q = d.get("_query") or fn.stem
        for it in d.get("data") or []:
            u = it.get("imageUrl")
            if not u:
                continue
            if u in seen:
                seen[u]["_queries"].append(q)
                continue
            it = dict(it)
            it["_queries"] = [q]
            it["_inst"] = ",".join(x.get("name", "") for x in (it.get("institutionList") or []))
            it["_page"] = (it.get("pageIndex") or 0) + 1
            seen[u] = it
            order.append(u)
    items = [seen[u] for u in order]
    for i, it in enumerate(items):
        it["_id"] = i
    (AP / "all_images.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print("合并 %d 条 → all_images.json" % len(items))
    for it in items[:30]:
        print("%4d %s %s p%s %s | %s" % (it["_id"], (it.get("publishDate") or "")[:10], it["_inst"][:8], it["_page"],
                                        (it.get("articleTitle") or "")[:30], "; ".join(it.get("captionList") or [])[:40]))

elif cmd == "get":
    prefix = opt(args, "--prefix", "ap")
    items = {x["_id"]: x for x in json.loads((AP / "all_images.json").read_text(encoding="utf-8"))}
    (AP / "img").mkdir(exist_ok=True)
    selp = AP / "selected.json"
    sel = json.loads(selp.read_text(encoding="utf-8")) if selp.exists() else []
    for s in args:
        x = items[int(s)]
        path = AP / "img" / ("%s_%s.jpg" % (prefix, s))
        if not (path.exists() and path.stat().st_size > 0):
            try:
                data = urllib.request.urlopen(urllib.request.Request(x["imageUrl"], headers={"User-Agent": UA}), timeout=30).read()
                path.write_bytes(data)
            except Exception as e:  # noqa: BLE001
                print("FAIL", s, e)
                continue
            time.sleep(0.3)
        sel = [r for r in sel if r["file"] != str(path.relative_to(R))]
        sel.append({"file": str(path.relative_to(R)), "_id": x["_id"], "inst": x["_inst"], "date": (x.get("publishDate") or "")[:10],
                    "title": x.get("articleTitle"), "page": x["_page"], "caption": x.get("captionList"),
                    "footnote": x.get("footnoteList"), "imageUrl": x["imageUrl"], "queries": x["_queries"]})
        print("OK", path.name, x["_inst"], (x.get("publishDate") or "")[:10], "p%s" % x["_page"])
    selp.write_text(json.dumps(sel, ensure_ascii=False, indent=1), encoding="utf-8")
else:
    sys.exit(__doc__)
