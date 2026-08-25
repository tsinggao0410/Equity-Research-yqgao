#!/usr/bin/env python3
"""
fetch_feishu_msgs.py — 飞书投研群消息采集器（onepager 前置资料一环）

在指定飞书群（默认「作文实时2」）按标的关键词搜索消息，导出为:
  - <关键词>.json   原始全量（lark-cli 输出，逐条含 message_id/链接/全文）
  - <关键词>.md     清洗后正文（去图片标记，保留时间/发送者/链接）
  - _merged.md      全关键词合并去重（按 message_id），供 rag_add 一次入库

依赖: lark-cli (npm -g @larksuite/cli)，用户身份已授权 search:message scope。

用法:
  python fetch_feishu_msgs.py --target "京东方A 000725"
  python fetch_feishu_msgs.py --target "顺络电子 002138" --groups "作文实时2,科技大制造-成长小队"
  python fetch_feishu_msgs.py --target "立昂微 605358" --start 2024-01-01 --end 2026-12-31
  python fetch_feishu_msgs.py --list-groups        # 列出可选群（动态查 chat-list）

输出目录: --out-dir，默认 <当前目录>/feishu/。RAG 入库时直接:
  python rag_add.py feishu/ --ws workspaces/<ticker>
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

DEFAULT_GROUPS = "作文实时2"
KEYWORD_HINTS = ["调研", "纪要", "点评", "目标价", "业绩", "交流"]  # 备用扩展，当前未用


def run_cli(args):
    """调 lark-cli，返回解析后的 JSON"""
    cmd = ["lark-cli"] + args
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if p.returncode != 0:
        raise RuntimeError(f"lark-cli {' '.join(args)} 失败:\n{p.stderr[:800]}")
    return json.loads(p.stdout)


def list_groups():
    """列出用户所在群: name -> chat_id"""
    d = run_cli(["im", "+chat-list", "--types", "group", "--page-size", "100", "--format", "json"])
    out = {}
    for c in d.get("data", {}).get("chats", []):
        name = c.get("name") or ""
        if name:
            out[name] = c["chat_id"]
    return out


def resolve_groups(names):
    """群名 -> chat_id；支持直接传 chat_id（oc_ 开头）"""
    groups = list_groups()
    resolved = []
    for n in names:
        n = n.strip()
        if not n:
            continue
        if n.startswith("oc_"):
            resolved.append((n, n))
        elif n in groups:
            resolved.append((n, groups[n]))
        else:
            print(f"⚠ 群「{n}」未找到，跳过（可用 --list-groups 查看）", file=sys.stderr)
    return resolved


def search_messages(chat_id, query, start=None, end=None):
    args = ["im", "+messages-search", "--chat-id", chat_id, "--query", query,
            "--page-all", "--page-limit", "40", "--format", "json"]
    if start:
        args += ["--start", start]
    if end:
        args += ["--end", end]
    d = run_cli(args)
    return d.get("data", {}).get("messages", [])


def clean_content(raw):
    """content 清洗: 转义还原、图片标记化、压缩空行"""
    if not raw:
        return ""
    s = raw
    try:
        if isinstance(raw, str) and raw.strip().startswith("{"):
            obj = json.loads(raw)
            for k in ("body", "content", "text"):
                if k in obj:
                    v = obj[k]
                    if isinstance(v, str):
                        s = v
                    elif isinstance(v, dict):
                        s = v.get("text") or v.get("content") or json.dumps(v, ensure_ascii=False)
                    break
    except Exception:
        pass
    s = s.replace("\\n", "\n").replace("\\t", " ")
    s = re.sub(r"!\[Image\]\([^)]*\)", "[图片]", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "[图片]", s)
    s = re.sub(r"<img[^>]*>", "[图片]", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def fmt_time(ts):
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts


def msg_to_md(m):
    sender = m.get("sender", {}).get("name", "?")
    link = m.get("message_app_link", "")
    lines = [
        f"## {fmt_time(m['create_time'])}  [{sender}]  ({m.get('msg_type','')})",
        f"- message_id: `{m['message_id']}`",
    ]
    if link:
        lines.append(f"- 链接: {link}")
    lines += ["", clean_content(m.get("content", "")), "", "---", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="飞书投研群消息采集")
    ap.add_argument("--target", help="标的，如 '京东方A 000725'（用于拆关键词）")
    ap.add_argument("--keywords", default="", help="逗号分隔搜索词；缺省用标的简称+代码")
    ap.add_argument("--groups", default=DEFAULT_GROUPS, help="群名/chat_id，逗号分隔")
    ap.add_argument("--start", default=None, help="起始时间 ISO（可选）")
    ap.add_argument("--end", default=None, help="结束时间 ISO（可选）")
    ap.add_argument("--out-dir", default=None,
                    help="输出目录；缺省自动归档到 ~/Desktop/research-materials/<公司名>-<代码>/feishu/")
    ap.add_argument("--list-groups", action="store_true", help="列出可选群并退出")
    args = ap.parse_args()

    if args.list_groups:
        for name, cid in list_groups().items():
            print(f"{name}\t{cid}")
        return

    if not args.target and not args.keywords:
        ap.error("需要 --target 或 --keywords")

    # 关键词: 显式 keywords 优先，否则 target 拆简称+代码
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    else:
        kw = set()
        for tok in args.target.replace("Ａ", "A").replace("（", " ").replace("）", " ").split():
            tok = tok.strip()
            if not tok:
                continue
            if re.fullmatch(r"\d{6}", tok):
                kw.add(tok)                      # 6位代码
            else:
                kw.add(tok)
                # 中文名前缀: 先取开头连续汉字
                m = re.match(r"^([\u4e00-\u9fff]+)", tok)
                if m:
                    pre = m.group(1)
                    if len(pre) < len(tok):
                        # 带字母后缀（京东方A→京东方）
                        kw.add(pre)
                    elif len(pre) == 4:
                        # 4字纯中文名（顺络电子→顺络），2字前缀更贴近群聊简称
                        kw.add(pre[:2])
        # 去掉过短/过泛的词（泛词: 股份/科技/公司/集团/北方/东方/电子/国际 等）
        STOP = {"公司", "股份", "科技", "集团", "北方", "东方", "西部", "南方", "中国",
                "国际", "工业", "电子", "信息", "实业", "控股", "发展", "建设"}
        kw = {k for k in kw if len(k) >= 2 and k not in STOP}
        keywords = sorted(kw, key=len, reverse=True)

    groups = resolve_groups([g for g in args.groups.split(",") if g.strip()])
    if not groups:
        print("没有可用群，退出", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out_dir or os.path.expanduser("~/Desktop/research-materials")
    if not args.out_dir:
        # 默认按「公司名-代码」归档: ~/Desktop/research-materials/<公司名>-<代码>/feishu/
        code = next((t for t in (args.target or "").replace("Ａ", "A").split() if re.fullmatch(r"\d{6}", t)), None)
        name = None
        if args.target:
            toks = [t for t in args.target.replace("Ａ", "A").split() if not re.fullmatch(r"\d{6}", t)]
            if toks:
                name = toks[0]
        if code:
            comp_dir = f"{name}-{code}" if name else code
            out_dir = os.path.join(out_dir, comp_dir, "feishu")
    os.makedirs(out_dir, exist_ok=True)

    all_msgs = {}  # message_id -> msg
    for gname, gid in groups:
        for kw in keywords:
            print(f"搜索 [{gname}] {kw} ...", file=sys.stderr)
            try:
                msgs = search_messages(gid, kw, args.start, args.end)
            except RuntimeError as e:
                print(f"  ⚠ {e}", file=sys.stderr)
                continue
            if not msgs:
                print(f"  （0 条）", file=sys.stderr)
                continue
            safe = re.sub(r"[^\w\u4e00-\u9fff]", "_", f"{gname}_{kw}")
            with open(os.path.join(out_dir, f"{safe}.json"), "w") as f:
                json.dump(msgs, f, ensure_ascii=False, indent=1)
            with open(os.path.join(out_dir, f"{safe}.md"), "w") as f:
                f.write(f"# 飞书群「{gname}」关键词「{kw}」消息导出\n\n"
                        f"- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"- 群: {gname} ({gid}) | 关键词: {kw} | 共 {len(msgs)} 条\n\n")
                for m in msgs:
                    f.write(msg_to_md(m))
            for m in msgs:
                all_msgs[m["message_id"]] = m
            print(f"  ✓ {len(msgs)} 条", file=sys.stderr)

    # 合并去重
    if all_msgs:
        merged = sorted(all_msgs.values(), key=lambda m: m["create_time"])
        with open(os.path.join(out_dir, "_merged.json"), "w") as f:
            json.dump(merged, f, ensure_ascii=False, indent=1)
        with open(os.path.join(out_dir, "_merged.md"), "w") as f:
            f.write(f"# 飞书群消息合并（{args.target or args.keywords}）\n\n"
                    f"- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"- 群: {', '.join(g for g, _ in groups)} | 关键词: {', '.join(keywords)}\n"
                    f"- 去重后共 {len(merged)} 条\n\n")
            for m in merged:
                f.write(msg_to_md(m))
        times = sorted(m["create_time"] for m in merged)
        print(f"\n完成: {len(keywords)} 关键词 × {len(groups)} 群 → 去重 {len(merged)} 条", file=sys.stderr)
        print(f"时间范围: {times[0][:10]} ~ {times[-1][:10]}", file=sys.stderr)
        print(f"输出目录: {out_dir}", file=sys.stderr)
        print(f"RAG 入库: python rag_add.py {out_dir} --ws workspaces/<ticker>", file=sys.stderr)
    else:
        print("未搜到任何消息", file=sys.stderr)


if __name__ == "__main__":
    main()
