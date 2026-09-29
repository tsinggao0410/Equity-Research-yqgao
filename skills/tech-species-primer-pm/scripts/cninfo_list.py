#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巨潮资讯:A 股公司全部公告清单 + 按关键词下载 PDF 并转按页文本。

用法(全局 --root 放在子命令前):
  python3 cninfo_list.py [--root R] list 688205 [--from 2015-01-01]
        → R/sources/cninfo/announcements_all.json:[{date, title, url, size, id}],新到旧
  python3 cninfo_list.py [--root R] get --kw 年度报告,半年度报告,招股说明书 [--exclude 摘要,英文,更正] [--from 2019-01-01] [--dry]
        标题命中任一关键词(按正则匹配)且不含排除词的公告下载到 R/sources/cninfo/<date>_<title>_<id>.pdf,并调 pdf2txt.py 转文本。
        注意标题写法不统一(如「688205_德科立_2025_年度报告」),年报用 '(?<!半)年度报告' 排除半年报;先加 --dry 看命中
  常用关键词:招股说明书 / 年度报告 / 半年度报告 / 投资者关系活动记录表 / 募集说明书 / 问询函 / 回复 / 减持 / 质押 /
              股权激励 / 关联交易 / 募集资金存放与使用 / 业绩预告
科创板、创业板 IPO 问询回复不在巨潮,在交易所审核系统(见 references/data_sources.md)。
国内站点直连(不走代理);请求不带任何个人信息。
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import warnings

warnings.filterwarnings("ignore", message=".*OpenSSL.*")
import requests  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _card import find_root  # noqa: E402

H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
     "Origin": "http://www.cninfo.com.cn", "Referer": "http://www.cninfo.com.cn/"}


def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


def session():
    s = requests.Session()
    s.trust_env = False
    s.headers.update(H)
    return s


def org_id(s, code):
    r = s.post("http://www.cninfo.com.cn/new/information/topSearch/detailOfQuery",
               data={"keyWord": code, "maxSecNum": 10, "maxListNum": 5}, timeout=20)
    for c in r.json().get("keyBoardList") or []:
        if c.get("code") == code:
            return c["orgId"], c.get("zwjc", "")
    sys.exit("巨潮查不到 %s 的 orgId" % code)


def do_list(R, code, since):
    s = session()
    oid, name = org_id(s, code)
    column = "szse" if code[0] in "0123" else "sse"
    rows, page = [], 1
    while True:
        r = s.post("http://www.cninfo.com.cn/new/hisAnnouncement/query", data={
            "pageNum": page, "pageSize": 30, "column": column, "tabName": "fulltext", "plate": "",
            "stock": "%s,%s" % (code, oid), "searchkey": "", "secid": "", "category": "", "trade": "",
            "seDate": "%s~2099-12-31" % since, "sortName": "", "sortType": "", "isHLtitle": "true"}, timeout=30)
        j = r.json()
        for a in j.get("announcements") or []:
            t = re.sub(r"<[^>]+>", "", a["announcementTitle"])
            rows.append({"date": time.strftime("%Y-%m-%d", time.localtime(a["announcementTime"] / 1000)), "title": t,
                         "url": "http://static.cninfo.com.cn/" + a["adjunctUrl"], "size": a.get("adjunctSize"),
                         "id": str(a.get("announcementId"))})
        if not j.get("hasMore"):
            break
        page += 1
        time.sleep(0.4)
    rows.sort(key=lambda x: x["date"], reverse=True)
    d = R / "sources" / "cninfo"
    d.mkdir(parents=True, exist_ok=True)
    (d / "announcements_all.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("%s %s:%d 条公告(%s 起)→ sources/cninfo/announcements_all.json" % (code, name, len(rows), since))


def do_get(R, kws, excl, since, dry):
    d = R / "sources" / "cninfo"
    rows = json.loads((d / "announcements_all.json").read_text(encoding="utf-8"))
    hit = [x for x in rows if x["date"] >= since and any(re.search(k, x["title"]) for k in kws) and not any(e in x["title"] for e in excl)]
    print("命中 %d 条" % len(hit))
    s = session()
    got = []
    for x in hit:
        safe = re.sub(r"[\\/:*?\"<>|\s]+", "_", x["title"])[:60]
        fn = d / ("%s_%s_%s.pdf" % (x["date"], safe, x["id"]))
        print(("[dry] " if dry else "") + fn.name)
        if dry or (fn.exists() and fn.stat().st_size > 1000):
            continue
        r = s.get(x["url"], timeout=120)
        if r.status_code != 200 or not r.content.startswith(b"%PDF"):
            print("  FAIL", r.status_code, x["url"])
            continue
        fn.write_bytes(r.content)
        got.append(str(fn))
        time.sleep(0.5)
    if got:
        subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "pdf2txt.py"), "--root", str(R), *got])


args = sys.argv[1:]
root = opt(args, "--root")
R = find_root(root)
if not args:
    sys.exit(__doc__)
cmd = args.pop(0)
if cmd == "list":
    since = opt(args, "--from", "2000-01-01")
    do_list(R, args[0], since)
elif cmd == "get":
    kws = [k for k in (opt(args, "--kw", "") or "").split(",") if k]
    excl = [k for k in (opt(args, "--exclude", "摘要,英文版,英文") or "").split(",") if k]
    since = opt(args, "--from", "2000-01-01")
    dry = "--dry" in args
    if not kws:
        sys.exit("get 需要 --kw")
    do_get(R, kws, excl, since, dry)
else:
    sys.exit(__doc__)
