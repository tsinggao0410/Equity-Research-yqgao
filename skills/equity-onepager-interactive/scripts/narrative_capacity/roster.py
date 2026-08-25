"""A 股名册：股票简称 → 代码。一次性建好落盘，之后本地查。

为什么需要它：韭研公社的产业链把成分股和题材词混在一个字段里
（"工具五金 工程机械 宠物 跨境电商 巨星科技 欧圣电气 …"），
而问财的多标的查询里只要掺进一个题材词，整条查询就返回 0 条——
必须先把非个股的 token 精确剔掉，模糊规则不行。
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from wencai import WencaiSession, pick

ROSTER_FILE = Path(__file__).resolve().parent / ".roster.json"
ROSTER_TTL_DAYS = 30      # 名称变更（更名/退市/新股）按月刷新足够


def build(s: WencaiSession) -> Dict[str, str]:
    """从问财拉全 A 股名册。~5500 只，按 100/轮 游标翻页，一次性成本。"""
    # 全市场 ~5500 只、每轮 100 条，护栏必须放到 60+ 轮，默认的 12 轮只能取到前 1300 只
    r = s.query("全部A股 股票代码 股票简称 总市值", all_rows=True,
                cursor_field="总市值", max_rounds=80)
    name_key, code_key = pick(r, "股票简称"), pick(r, "股票代码")
    if r.get("truncated"):
        raise RuntimeError(f"名册没取全：{r['count']}/{r['total']}，{r.get('notes')}")
    roster = {}
    for row in r["rows"]:
        name, code = row.get(name_key), row.get(code_key)
        if name and code:
            roster[str(name).strip()] = str(code).split(".")[0]
    return roster


def load(s: Optional[WencaiSession] = None, ttl_days: int = ROSTER_TTL_DAYS) -> Dict[str, str]:
    """读缓存；过期或缺失且给了 session 就重建。"""
    try:
        blob = json.loads(ROSTER_FILE.read_text())
        age = (dt.date.today() - dt.date.fromisoformat(blob["built"])).days
        if age <= ttl_days and blob.get("roster"):
            return blob["roster"]
    except Exception:
        pass

    if s is None:
        raise RuntimeError("名册缺失或过期，需要传入 WencaiSession 重建")

    roster = build(s)
    ROSTER_FILE.write_text(json.dumps(
        {"built": dt.date.today().isoformat(), "n": len(roster), "roster": roster},
        ensure_ascii=False))
    return roster


def split_names(tokens: List[str], roster: Dict[str, str]) -> Tuple[List[str], List[str]]:
    """把 token 列表切成 (个股名, 非个股词)。只认名册里的精确名，不做模糊匹配。"""
    # 必须去重：韭研的 keyword 字段里同一只票可能出现两次（分组标注造成），
    # 不去重的话显示的成分数会虚高（实测 27 个 token 其实只有 21 只票）。
    hits, misses, seen = [], [], set()
    for t in tokens:
        t = t.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        (hits if t in roster else misses).append(t)
    return hits, misses
