#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
comprehension_writer.py — P0 认知卡 (comprehension.json) 出口写出 + 自检。

把 Agent 填好的"认知卡内容 JSON"(顶层 11 个字段)校验后,套上 chain-bus `_meta`
信封,写出 CONTRACT §5 的 P0 产物。缺字段 / 类型错 → 直接报错 (非零退出),
避免漏字段流到下游。

用法:
    python comprehension_writer.py <card.json> \
        --narrative-id <id> \
        --out _chain_workspace/<id>/P0_comprehension/comprehension.json
    # 熟行业指针卡 (只填最小字段) 加 --pointer 放宽校验
    python comprehension_writer.py <card.json> --narrative-id <id> --out <path> --pointer

card.json 顶层字段 (CONTRACT §5):
    species_name(str) one_line_cognition(str)
    routes(list[{id,name,status,penetration_pct}])   # penetration_pct=整数百分数 0-100
                                                     # ★ 早期物种渗透率不可知 → 显式写 null
                                                     #   (= DATA NOT AVAILABLE, 唯一合法逃生门;
                                                     #    禁止编数字, 也禁止删 key)
    chains_count(int)
    necessity_tiers(dict A_rigid..F_sentiment)
    swing_variable(dict{name,direction,why,is_volatile,sensitivity})
        # ★ 铁律1 机器闸: direction 只能 '+'/'-' (禁 None);
        #   sensitivity 必须是非空 list ≥2 档, 每档 {level, edge, source}
        #   (方向与量级从数据 derive, 严禁预设 —— 实跑写反符号事故的防复发闸)
        # 双变量物种: 主导变量放 swing_variable, 次变量放可选 swing_variable_2 (同结构)
    contradictions(list)   # ★ 铁律2 输出位: 跨源矛盾
        # 每条 {claim_a, claim_b, source_a, source_b, resolution};
        # 主动找过但确无矛盾 → 显式写一条 {"none_found": true, "searched": "<找过什么>"}
    maturity_redzone(dict) model_reuse_diagnosis(str) cognitive_position(str)
    bom_seed(list[str]) glossary(list[{term,plain}])
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "chain-bus/1.0"
SOURCE_SKILL = "tech-species-primer"

# 全字段 (普通卡必出); 指针卡只需 POINTER_REQUIRED
FULL_REQUIRED = [
    "species_name", "one_line_cognition", "routes", "chains_count",
    "necessity_tiers", "swing_variable", "contradictions", "maturity_redzone",
    "model_reuse_diagnosis", "cognitive_position", "bom_seed", "glossary",
]
POINTER_REQUIRED = ["species_name", "one_line_cognition", "routes", "chains_count"]

NECESSITY_KEYS = ["A_rigid", "B_roi", "C_armsrace", "D_policy", "E_finance", "F_sentiment"]


def _err(msg: str, errs: list):
    errs.append(msg)


def validate(card: dict, pointer: bool = False) -> list:
    """返回错误列表 (空=通过)。"""
    errs: list = []
    required = POINTER_REQUIRED if pointer else FULL_REQUIRED
    for f in required:
        if f not in card:
            _err(f"缺必出字段 '{f}'", errs)

    # 类型校验 (只对存在的字段查,缺失已在上面报过)
    if "species_name" in card and not isinstance(card["species_name"], str):
        _err("species_name 必须是 str", errs)
    if "one_line_cognition" in card and not isinstance(card["one_line_cognition"], str):
        _err("one_line_cognition 必须是 str", errs)

    if "chains_count" in card and not isinstance(card["chains_count"], int):
        _err(f"chains_count 必须是 int (当前 {type(card.get('chains_count')).__name__}) "
             f"—— 写数字 2,不要写 '2-3 并行链'", errs)

    routes = card.get("routes")
    if routes is not None:
        if not isinstance(routes, list):
            _err("routes 必须是 list", errs)
        else:
            if not routes:
                _err("routes 至少 1 条", errs)
            for i, r in enumerate(routes):
                if not isinstance(r, dict):
                    _err(f"routes[{i}] 必须是 dict", errs)
                    continue
                for k in ("id", "name", "status"):
                    if k not in r:
                        _err(f"routes[{i}] 缺 '{k}' (需 id/name/status)", errs)
                # penetration_pct: CONTRACT §5 字段，进报告第二节"渗透率"。
                # 量纲冻结 = 整数百分数 (15 = 15%)，区间 [0,100]，不要写 0.15。
                # (依 CONTRACT_NOTES_D #6 裁决；指针卡放宽为可选)
                if "penetration_pct" not in r:
                    if not pointer:
                        _err(f"routes[{i}] 缺 'penetration_pct' (整数百分数 0-100，喂报告第二节渗透率)", errs)
                else:
                    pp = r.get("penetration_pct")
                    if pp is not None:
                        if not isinstance(pp, (int, float)) or isinstance(pp, bool):
                            _err(f"routes[{i}].penetration_pct 必须是数字 (整数百分数，如 15)", errs)
                        elif not (0 <= pp <= 100):
                            _err(f"routes[{i}].penetration_pct={pp} 越界 —— 必须是 0-100 整数百分数 "
                                 f"(15=15%，不要写 0.15 也不要写 >100)", errs)

    if not pointer:
        nt = card.get("necessity_tiers")
        if nt is not None:
            if not isinstance(nt, dict):
                _err("necessity_tiers 必须是 dict", errs)
            else:
                for k in NECESSITY_KEYS:
                    if k not in nt:
                        _err(f"necessity_tiers 缺六档键 '{k}' (无内容给 [] 不要删 key)", errs)
                    elif not isinstance(nt[k], list):
                        _err(f"necessity_tiers['{k}'] 必须是 list", errs)

        for sv_key in ("swing_variable", "swing_variable_2"):
            sv = card.get(sv_key)
            if sv_key == "swing_variable_2" and sv is None:
                continue  # 次变量可选
            if sv is not None:
                if not isinstance(sv, dict):
                    _err(f"{sv_key} 必须是 dict", errs)
                else:
                    for k in ("name", "direction", "why", "is_volatile"):
                        if k not in sv:
                            _err(f"{sv_key} 缺 '{k}'", errs)
                    # ★ 铁律1: direction 禁 None —— "不知道方向"不是合法输出,
                    #   必须回去做敏感性表把符号 derive 出来 (写反符号事故防复发)
                    if sv.get("direction") not in ("+", "-"):
                        _err(f"{sv_key}.direction 必须是 '+' 或 '-' (禁 null/缺失 —— 方向必须从数据 derive, 铁律1)", errs)
                    # ★ 铁律1: 敏感性表必出 —— ≥2 档, 每档 {level, edge, source}
                    sens = sv.get("sensitivity")
                    if not isinstance(sens, list) or not sens:
                        _err(f"{sv_key}.sensitivity 必须是非空 list (铁律1: 敏感性表是防伪核心, 不做表=方向没 derive)", errs)
                    else:
                        if len(sens) < 2:
                            _err(f"{sv_key}.sensitivity 至少 2 档 (当前 {len(sens)} 档) —— 单点不构成敏感性", errs)
                        for i, s in enumerate(sens):
                            if not isinstance(s, dict):
                                _err(f"{sv_key}.sensitivity[{i}] 必须是 dict", errs)
                                continue
                            for k in ("level", "edge"):
                                if k not in s:
                                    _err(f"{sv_key}.sensitivity[{i}] 缺 '{k}' (level=变量档位, edge=对物种经济性的影响)", errs)
                            if not s.get("source"):
                                _err(f"{sv_key}.sensitivity[{i}] 缺 'source' (铁律7: 数字必须有出处, 不许拍)", errs)

        # ★ 铁律2: 跨源矛盾必有输出位 —— 找到写明细, 没找到显式声明 none_found
        cons = card.get("contradictions")
        if cons is not None:
            if not isinstance(cons, list) or not cons:
                _err("contradictions 必须是非空 list (铁律2: 主动找跨源矛盾; "
                     "确无矛盾写一条 {\"none_found\": true, \"searched\": \"...\"})", errs)
            else:
                for i, c in enumerate(cons):
                    if not isinstance(c, dict):
                        _err(f"contradictions[{i}] 必须是 dict", errs)
                        continue
                    if c.get("none_found"):
                        if not c.get("searched"):
                            _err(f"contradictions[{i}] none_found=true 必须带 'searched' (找过什么才有资格说没矛盾)", errs)
                        continue
                    for k in ("claim_a", "claim_b", "source_a", "source_b", "resolution"):
                        if k not in c:
                            _err(f"contradictions[{i}] 缺 '{k}' (矛盾五要素: 两个主张+两个来源+处理决策)", errs)

        mr = card.get("maturity_redzone")
        if mr is not None and not isinstance(mr, dict):
            _err("maturity_redzone 必须是 dict (stage/bottleneck)", errs)
        elif isinstance(mr, dict):
            for k in ("stage", "bottleneck"):
                if k not in mr:
                    _err(f"maturity_redzone 缺 '{k}'", errs)

        bs = card.get("bom_seed")
        if bs is not None:
            if not isinstance(bs, list):
                _err("bom_seed 必须是 list[str]", errs)
            elif not all(isinstance(x, str) for x in bs):
                _err("bom_seed 每个元素必须是 str (环节名)", errs)

        gl = card.get("glossary")
        if gl is not None:
            if not isinstance(gl, list):
                _err("glossary 必须是 list[{term,plain}]", errs)
            else:
                for i, g in enumerate(gl):
                    if not isinstance(g, dict) or "term" not in g or "plain" not in g:
                        _err(f"glossary[{i}] 必须是 {{term, plain}}", errs)

    return errs


def soft_warnings(card: dict, pointer: bool = False) -> list:
    """非阻断提醒 (打印不拦)。"""
    warns: list = []
    if pointer:
        return warns
    nt = card.get("necessity_tiers") or {}
    routes = card.get("routes") or []
    # M2 三档 Tier1/2/3 → 六档映射: Tier1→A_rigid, Tier2→B_roi, Tier3 不入档;
    # C/D/E/F 由"四档三问"补 (见 SKILL.md M2)。A/B 全空但 routes 存在 = 映射没做
    if routes and isinstance(nt, dict) and not (nt.get("A_rigid") or nt.get("B_roi")):
        warns.append("necessity_tiers 的 A_rigid 与 B_roi 均为空但 routes 非空 —— "
                     "M2 三档 Tier1→A_rigid / Tier2→B_roi 的映射疑似没做, 核实后再交 P2")
    return warns


def build_meta(narrative_id: str, pointer: bool = False) -> dict:
    return {
        "narrative_id": narrative_id,
        "phase": "P0",
        "schema_version": SCHEMA_VERSION,
        "units": {"mkt_cap": "yi_cny", "profit": "yi_cny", "tam": "yi_cny"},
        "join_keys": ["segment_sid"],  # P0 喂 P1 的种子是环节级
        "source_skill": SOURCE_SKILL,
        "card_type": "pointer" if pointer else "full",  # WS4 闸侧按此放行/降 warn
        "written_at": datetime.now(timezone.utc).isoformat(),
    }


def normalize(card: dict, pointer: bool) -> dict:
    """对指针卡补齐缺省 key,保证下游 .get() 不炸。"""
    out = dict(card)
    if pointer:
        out.setdefault("necessity_tiers", {k: [] for k in NECESSITY_KEYS})
        out.setdefault("swing_variable", {"name": "", "direction": "+", "why": "", "is_volatile": False,
                                          "sensitivity": []})
        out.setdefault("contradictions", [{"none_found": True, "searched": "指针卡(熟行业)未展开跨源矛盾搜索"}])
        out.setdefault("maturity_redzone", {"stage": "", "bottleneck": ""})
        out.setdefault("model_reuse_diagnosis", "")
        out.setdefault("cognitive_position", "")
        out.setdefault("bom_seed", [])
        out.setdefault("glossary", [])
    # 指针卡标记 (WS4: validate_bus depth/input 闸按 card_type 放行或降 warn)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="P0 认知卡写出 + 自检")
    ap.add_argument("card", help="填好的认知卡内容 JSON (顶层 11 字段)")
    ap.add_argument("--narrative-id", required=True, help="叙事 id,如 sodium-battery-20260604")
    ap.add_argument("--out", required=True, help="输出 comprehension.json 路径")
    ap.add_argument("--pointer", action="store_true", help="熟行业指针卡,只校验最小字段")
    args = ap.parse_args()

    try:
        card = json.loads(Path(args.card).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[X] 读取 card 失败: {e}", file=sys.stderr)
        return 1

    # 若用户误把 _meta 也写进了卡内容,剥掉再校验 (_meta 由本脚本生成)
    card.pop("_meta", None)

    errs = validate(card, pointer=args.pointer)
    if errs:
        print(f"[X] P0 认知卡校验失败 ({len(errs)} 处) —— 修好再写出:", file=sys.stderr)
        for e in errs:
            print(f"   - {e}", file=sys.stderr)
        return 1

    for w in soft_warnings(card, pointer=args.pointer):
        print(f"[!] {w}", file=sys.stderr)

    card = normalize(card, args.pointer)
    payload = {"_meta": build_meta(args.narrative_id, pointer=args.pointer)}
    payload.update(card)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    mode = "指针卡" if args.pointer else "全字段卡"
    print(f"[OK] P0 认知卡 ({mode}) 已写出 → {out_path}", file=sys.stderr)
    print(f"     species={card.get('species_name')} | routes={len(card.get('routes', []))} "
          f"| chains_count={card.get('chains_count')} | bom_seed={len(card.get('bom_seed', []))} "
          f"| glossary={len(card.get('glossary', []))}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
