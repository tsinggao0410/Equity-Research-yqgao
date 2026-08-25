#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rag_query.py — 薄封装:对某标的的 research-rag 工作区跑 search/facts/get_doc/open_artifact。

复用 research-rag 的 agentic 检索(dense qwen3-vl + BM25 + RRF + 时效)，不重造。
第一参数 = 工作区名(通常 ticker，解析为 research-rag/workspaces/<name>) 或绝对路径；
其余参数原样透传给 research-rag/skill/cli.py，并自动补 --ws。

用法:
  python rag_query.py <ws> search "<标的> 卖方 目标价 算账" --ticker 605358.SH --as-of 2025-06-30 --top 8
  python rag_query.py <ws> facts 立昂微 毛利率 --by-segment
  python rag_query.py <ws> get_doc <doc_id> --text
--as-of 防前视(后验复盘必用)；--ticker/--type 元数据预过滤提精度。
"""
import os, subprocess, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
def _rr_root():
    cfg = os.path.join(HERE, "rag_config.json")
    cands = []
    try:
        r = json.load(open(cfg, encoding="utf-8")).get("research_rag_root")
        if r:
            cands.append(r)
    except Exception:
        pass
    cands += [os.environ.get("RESEARCH_RAG_ROOT"),
              "~/Desktop/rag", "~/Desktop/gyasset/research-rag",
              r"C:/Users/youqi/Desktop/gyasset/research-rag"]
    for c in cands:
        if c and os.path.isfile(os.path.join(os.path.expanduser(c), "skill", "cli.py")):
            return os.path.expanduser(c)
    return os.path.expanduser(cands[0] if cands and cands[0] else "~/Desktop/rag")

def main():
    if len(sys.argv) < 3:
        print("usage: python rag_query.py <ws_name_or_path> <search|facts|get_doc|open_artifact> ...")
        sys.exit(2)
    RR = _rr_root()
    ws = sys.argv[1]
    if not os.path.isabs(ws):
        ws = os.path.join(RR, "workspaces", ws)
    if not os.path.isdir(ws):
        print("⚠️ 工作区不存在: %s\n   先在 Phase0.0 建库: cd %s && python research_system.py --zip <zip> --target <标的> --project <ticker>  (或 --sweep)" % (ws, RR))
        sys.exit(1)
    cli = os.path.join(RR, "skill", "cli.py")
    # research-rag/skill/cli.py 用环境变量 RAG_WORKSPACE 选工作区，不吃 --ws（传了会 argparse 报错）
    argv = [sys.executable, cli] + sys.argv[2:]
    env = dict(os.environ, RAG_WORKSPACE=ws)
    sys.exit(subprocess.run(argv, cwd=RR, env=env).returncode)

if __name__ == "__main__":
    main()
