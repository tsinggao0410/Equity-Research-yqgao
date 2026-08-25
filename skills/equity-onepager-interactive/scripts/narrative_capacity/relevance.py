"""问财概念的关联度打分。

问财自带 `诊股概念分类贴合度`，但只吐贴合度最高的一条，拿不到完整排名
（试过 "贴合度排名小于20"、"按贴合度排名排序" 都不给）。所以自己算。

信号全部免费——公司画像那一次调用里已经带回主营产品名称和两套行业分类：

  biz    概念名与主营产品/行业的字面重合    最强信号，直接反映是不是主业
  narrow 概念有多窄（成分股数）            越窄越具体；伞形标签几乎没有定位信息
  order  问财自己的排序                    经验上靠前的更贴身

三项都打印出来，谁高谁低看得见，不做黑箱。
"""
from __future__ import annotations

import re
from math import log
from typing import Any, Dict, List, Optional, Sequence

W_BIZ, W_NARROW, W_ORDER = 0.55, 0.30, 0.15
BIZ_OVERRIDE = 0.8      # 主营匹配到这个程度，即使是伞形标签也不该滤掉
_CLEAN = re.compile(r"[^0-9a-z一-鿿]+")

# 通用修饰片段：命中它们说明不了任何事。
# "智能物流""智能家居"只因为主营里有"智能工具"就拿 0.5，是纯噪音。
STOP_FRAGMENTS = {
    "智能", "概念", "经济", "产业", "中国", "新型", "高端", "龙头", "综合",
    "通用", "其他", "系统", "技术", "服务", "产品", "工程", "国际", "现代",
}


def biz_text(profile: Dict[str, Any]) -> str:
    """把主营产品 + 两套行业分类拼成一段可匹配的文本。"""
    parts = [
        str(profile.get("products") or "").replace("||", " "),
        str(profile.get("ths_industry") or "").replace("-", " "),
        str(profile.get("sw_industry") or "").replace("-", " "),
    ]
    return _CLEAN.sub(" ", " ".join(parts).lower())


def biz_match(concept: str, text: str) -> float:
    """概念名里能在主营文本中找到的最长连续子串占比。

    "存储芯片" 在 "…存储芯片…" 里整词命中 → 1.0
    "芯片概念" 只有"芯片"命中          → 0.5
    "露营经济" 手工具公司的主营里找不到  → 0.0
    """
    c = _CLEAN.sub("", (concept or "").lower())
    if not c:
        return 0.0
    best = 0
    for i in range(len(c)):
        for j in range(len(c), i + best, -1):
            frag = c[i:j]
            if len(frag) >= 2 and frag not in STOP_FRAGMENTS and frag in text:
                best = len(frag)
                break
    return best / len(c)


def matched_fragment(concept: str, text: str) -> str:
    """打分时命中的那个片段，打印出来让人能核对，不做黑箱。"""
    c = _CLEAN.sub("", (concept or "").lower())
    best, frag = 0, ""
    for i in range(len(c)):
        for j in range(len(c), i + best, -1):
            cand = c[i:j]
            if len(cand) >= 2 and cand not in STOP_FRAGMENTS and cand in text:
                best, frag = len(cand), cand
                break
    return frag


def narrowness(size: Optional[int], umbrella_min: int = 500) -> float:
    """成分股数 → [0,1]，越窄越高。对数刻度：50 只和 100 只的差别比 400 和 450 大。"""
    if not size or size <= 0:
        return 0.0
    if size >= umbrella_min:
        return 0.0
    return max(0.0, 1.0 - log(size) / log(umbrella_min))


def score_concepts(
    profile: Dict[str, Any],
    sizes: Dict[str, Optional[int]],
    umbrella_min: int = 500,
) -> List[Dict[str, Any]]:
    """给公司的每个可交易概念打关联度分，高到低排序。"""
    from concept_capacity import classify

    text = biz_text(profile)
    concepts = profile.get("tradable") or []
    n = max(len(concepts), 1)

    scored = []
    for rank, c in enumerate(concepts):
        size = sizes.get(c)
        b = biz_match(c, text)
        w = narrowness(size, umbrella_min)
        o = 1.0 - rank / n
        scored.append({
            "concept": c,
            "facet": classify(c),
            "size": size,
            "biz": b,
            "hit": matched_fragment(c, text),
            "narrow": w,
            "order": o,
            "score": W_BIZ * b + W_NARROW * w + W_ORDER * o,
            "umbrella": bool(size and size >= umbrella_min),
        })
    return sorted(scored, key=lambda x: -x["score"])


def top_themes(
    scored: Sequence[Dict[str, Any]],
    n: int,
    max_per_facet: int = 2,
) -> List[Dict[str, Any]]:
    """取关联度最高的 n 个，同一个面最多 max_per_facet 个。

    纯按分数取会退化成同一个面的近义词（存储芯片/芯片概念/MCU芯片），
    留一条软性的多样性约束，但主序仍然是关联度。
    """
    picked: List[Dict[str, Any]] = []
    used: Dict[str, int] = {}
    for item in scored:
        # 伞形一律剔除，不留后门。曾经为"储能"(895只，主营确有 powerstations)开过
        # BIZ_OVERRIDE 例外，但结果没用：895 只的篮子里本股排第 98、占 0.2%，
        # 钱来了也轮不到——主营再相关，容量读数和份额读数都没有决策含义。
        if item["umbrella"]:
            continue
        f = item["facet"]
        if used.get(f, 0) >= max_per_facet:
            continue
        picked.append(item)
        used[f] = used.get(f, 0) + 1
        if len(picked) >= n:
            break
    return picked
