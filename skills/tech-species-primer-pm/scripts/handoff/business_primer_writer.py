#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
business_primer_writer.py — Mode B 业务认知卡 (business_primer.json) 出口写出 + 自检。

把 Agent 填好的"业务认知卡内容 JSON"(顶层 15 个字段)校验后,套上 `_meta` 信封写出。
缺字段 / 类型错 / 铁律闸没过 → 直接报错 (非零退出),避免漏字段流到 onepager / industry-model。
与 comprehension_writer.py (Mode A, chain-bus P0 契约) 平行,互不干涉。

用法:
    python business_primer_writer.py <card.json> \
        --subject-id yuchai-cyd-20260915 \
        --subject-type company            # company | industry
        --out ~/Desktop/research-materials/玉柴国际-CYD/primer/business_primer.json

card.json 顶层 16 字段 (SKILL.md 附录 B):
    entity(dict)  one_line_business(str)  analog(dict)  product_lines(list)  tech_primer(dict)
    moat(list)  customers(dict)  business_model(dict)  landscape(dict)  demand_drivers(dict)
    contradictions(list)  changes_and_debates(dict)  segment_separability(dict)
    glossary(list)  visuals(list)  sources(list)      # visuals_missing(list) 可选

硬闸 (来自铁律 2/7/8/9/10/11/12 + 铁律 1 同款):
    铁律 8  : product_lines ≥2, 每条 tier_rule 非空 (分档尺子要写边界+出处)
    铁律 9  : 有 asp_cny 的产品线必须带 asp_formula (写算式); 数值缺失显式 null
    铁律 10 : customers.direct 非空 + decider 非空 + customer_is_competitor 是 bool
    铁律 11 : entity.listed_name / operating_entity / reporting_scope 非空 (company); disambiguation 是 list
    铁律 12 : tech_primer.key_params ≥3, 每条 why_buyer_cares 非空且 pl_hook ∈ {q,p,gm,opex,capex,wc,none}
    铁律 19 : moat ≥2 层, 每层 layer/evidence/kill_condition 非空, strength ∈ 强|中|弱, type 合法, sources 非空 (v2.4)
    铁律 1  : demand_drivers.primary.direction ∈ {'+','-'}, sensitivity ≥2 档且每档 level/edge/source
    铁律 2  : contradictions 非空 (或显式 none_found + searched)
    铁律 7  : sources ≥3 (每条 title); glossary ≥5
    铁律 13 : visuals ≥1, 每条 file/role/source_type/caption/module; role=structure ≥1 (官方或 self_drawn);
              非 self_drawn 必须带 source_url; 每条 accessed 日期
软提醒 (打印不拦): rev_share_pct 合计偏离 100 ±5; standards_timeline 为空; 所有 gm_pct 为 null 等。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "business-primer/1.1"
SOURCE_SKILL = "tech-species-primer"

REQUIRED = [
    "entity", "one_line_business", "analog", "product_lines", "tech_primer",
    "moat", "customers", "business_model", "landscape", "demand_drivers",
    "contradictions", "changes_and_debates", "segment_separability",
    "glossary", "visuals", "sources",
]
MOAT_TYPES = {"资源牌照", "工艺良率", "客户认证", "规模成本", "转换成本", "网络效应", "数据", "渠道", "其他"}
MOAT_STRENGTH = {"强", "中", "弱"}
VISUAL_ROLES = {"product", "structure", "process", "application", "plant", "data", "other"}
VISUAL_SOURCE_TYPES = {"official_site", "ir_page", "ir_deck_or_report_pdf", "annual_report", "self_drawn", "industry_assoc"}
PL_HOOKS = {"q", "p", "gm", "opex", "capex", "wc", "none"}
MAKE_OR_BUY = {"自制", "外购", "混合"}


def _num_or_null(v) -> bool:
    return v is None or (isinstance(v, (int, float)) and not isinstance(v, bool))


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def validate(card: dict, subject_type: str = "company") -> list:
    """返回错误列表 (空=通过)。"""
    errs: list = []
    E = errs.append

    for f in REQUIRED:
        if f not in card:
            E(f"缺必出字段 '{f}'")

    # ── entity (铁律 11) ──
    ent = card.get("entity")
    if ent is not None:
        if not isinstance(ent, dict):
            E("entity 必须是 dict")
        else:
            if subject_type == "company":
                for k in ("listed_name", "operating_entity", "reporting_scope"):
                    if not _nonempty_str(ent.get(k)):
                        E(f"entity.{k} 必须非空 (铁律 11: 上市主体/并表主体/口径主体先消歧)")
            else:
                if not _nonempty_str(ent.get("reporting_scope")):
                    E("entity.reporting_scope 必须非空 (行业卡: 写明行业边界与协会口径)")
            if not isinstance(ent.get("disambiguation"), list):
                E("entity.disambiguation 必须是 list (无同名实体给 [], 不要删 key)")
            else:
                for i, d in enumerate(ent["disambiguation"]):
                    if not isinstance(d, dict) or not _nonempty_str(d.get("name")) or not _nonempty_str(d.get("data_trap")):
                        E(f"entity.disambiguation[{i}] 需 {{name, relation, data_trap}} (说清会混淆哪个数)")
            if "ownership_pct" in ent and not _num_or_null(ent["ownership_pct"]):
                E("entity.ownership_pct 必须是数字或 null")

    if "one_line_business" in card and not _nonempty_str(card["one_line_business"]):
        E("one_line_business 必须是非空 str (谁付钱×买什么×为什么找它)")

    an = card.get("analog")
    if an is not None:
        if not isinstance(an, dict) or not _nonempty_str(an.get("company")):
            E("analog 必须是 dict 且 company 非空 (它像谁)")
        else:
            for k in ("same", "different"):
                if not isinstance(an.get(k), list) or not an[k]:
                    E(f"analog.{k} 必须是非空 list (一样/不一样各至少 1 条)")

    # ── product_lines (铁律 8/9) ──
    pls = card.get("product_lines")
    if pls is not None:
        if not isinstance(pls, list) or len(pls) < 2:
            E("product_lines 必须是 ≥2 条的 list (只有 1 档不叫谱系; '其他' 也单列一档)")
        else:
            ids = set()
            for i, p in enumerate(pls):
                if not isinstance(p, dict):
                    E(f"product_lines[{i}] 必须是 dict"); continue
                for k in ("id", "name", "tier_rule", "q_def", "p_def", "driver"):
                    if not _nonempty_str(p.get(k)):
                        E(f"product_lines[{i}] 缺 '{k}' 或为空 (tier_rule=分档边界+出处, 铁律 8; q_def/p_def 喂 onepager segments)")
                if p.get("id") in ids:
                    E(f"product_lines[{i}].id={p.get('id')!r} 重复")
                ids.add(p.get("id"))
                if not isinstance(p.get("applications"), list) or not p["applications"]:
                    E(f"product_lines[{i}].applications 必须是非空 list (装在哪)")
                for k in ("units", "revenue_yi", "asp_cny", "rev_share_pct", "unit_share_pct", "gm_pct"):
                    if k in p and not _num_or_null(p[k]):
                        E(f"product_lines[{i}].{k} 必须是数字或 null (缺=null, 禁止写 '约 2 万')")
                if p.get("asp_cny") is not None and not _nonempty_str(p.get("asp_formula")):
                    E(f"product_lines[{i}] 有 asp_cny 但缺 asp_formula (铁律 9: ASP 必须写算式 '收入÷台数')")
                if not isinstance(p.get("competitors"), list):
                    E(f"product_lines[{i}].competitors 必须是 list (这一档跟谁打; 未知给 [])")

    # ── tech_primer (铁律 12) ──
    tp = card.get("tech_primer")
    if tp is not None:
        if not isinstance(tp, dict):
            E("tech_primer 必须是 dict")
        else:
            if not _nonempty_str(tp.get("how_it_works")):
                E("tech_primer.how_it_works 必须非空 (≤5 行白话原理)")
            kps = tp.get("key_params")
            if not isinstance(kps, list) or len(kps) < 3:
                E("tech_primer.key_params 必须是 ≥3 条的 list (买家看哪几个参数)")
            else:
                for i, kp in enumerate(kps):
                    if not isinstance(kp, dict):
                        E(f"tech_primer.key_params[{i}] 必须是 dict"); continue
                    if not _nonempty_str(kp.get("param")) or not _nonempty_str(kp.get("why_buyer_cares")):
                        E(f"tech_primer.key_params[{i}] 缺 param / why_buyer_cares (铁律 12: 答不出买家为什么在意就删掉)")
                    if kp.get("pl_hook") not in PL_HOOKS:
                        E(f"tech_primer.key_params[{i}].pl_hook={kp.get('pl_hook')!r} 必须 ∈ {sorted(PL_HOOKS)} (进 P&L 哪个口)")
            if not isinstance(tp.get("standards_timeline"), list):
                E("tech_primer.standards_timeline 必须是 list (无标准驱动的行业给 [])")
            bom = tp.get("bom_skeleton")
            if not isinstance(bom, list) or len(bom) < 3:
                E("tech_primer.bom_skeleton 必须是 ≥3 条的 list (自制/外购骨架, 种子级)")
            else:
                for i, b in enumerate(bom):
                    if not isinstance(b, dict) or not _nonempty_str(b.get("part")):
                        E(f"tech_primer.bom_skeleton[{i}] 缺 part"); continue
                    if b.get("make_or_buy") not in MAKE_OR_BUY:
                        E(f"tech_primer.bom_skeleton[{i}].make_or_buy={b.get('make_or_buy')!r} 必须 ∈ {sorted(MAKE_OR_BUY)}")
            if not _nonempty_str(tp.get("moat")):
                E("tech_primer.moat 必须非空 (以 '对手追上需要__' 收尾)")

    # ── moat (铁律 19, v2.4) ──
    mo = card.get("moat")
    if mo is not None:
        if not isinstance(mo, list) or len(mo) < 2:
            E("moat 必须是 ≥2 条的 list (铁律 19: 壁垒至少拆两层; 一层写不出来就是没做功课)")
        else:
            for i, m in enumerate(mo):
                if not isinstance(m, dict):
                    E(f"moat[{i}] 必须是 dict"); continue
                for k in ("layer", "evidence", "kill_condition"):
                    if not _nonempty_str(m.get(k)):
                        E(f"moat[{i}] 缺 '{k}' (每层要写: 是什么壁垒 / 可验证证据 / 什么一发生它就不成立)")
                if m.get("strength") not in MOAT_STRENGTH:
                    E(f"moat[{i}].strength={m.get('strength')!r} 必须 ∈ {sorted(MOAT_STRENGTH)} (强=对手试过没追平, 中=差距在缩小, 弱=已被追平)")
                if m.get("type") not in MOAT_TYPES:
                    E(f"moat[{i}].type={m.get('type')!r} 必须 ∈ {sorted(MOAT_TYPES)}")
                if not isinstance(m.get("sources"), list) or not m["sources"]:
                    E(f"moat[{i}].sources 必须是非空 list (壁垒强度要有出处; 只有一个来源就降一档)")

    # ── customers (铁律 10) ──
    cu = card.get("customers")
    if cu is not None:
        if not isinstance(cu, dict):
            E("customers 必须是 dict")
        else:
            if not isinstance(cu.get("direct"), list) or not cu["direct"]:
                E("customers.direct 必须是非空 list (谁付款; 年报不点名就从新闻取并标 EST)")
            else:
                for i, d in enumerate(cu["direct"]):
                    if not isinstance(d, dict) or not _nonempty_str(d.get("name")) or not _nonempty_str(d.get("evidence")):
                        E(f"customers.direct[{i}] 需 {{name, tier, evidence}} (evidence 写 FACT/EST + 来源)")
            if not isinstance(cu.get("end_users"), list) or not cu["end_users"]:
                E("customers.end_users 必须是非空 list (谁使用)")
            if not _nonempty_str(cu.get("decider")):
                E("customers.decider 必须非空 (谁选型)")
            for k in ("top1_pct", "top5_pct"):
                if k in cu and not _num_or_null(cu[k]):
                    E(f"customers.{k} 必须是数字或 null")
            if not isinstance(cu.get("customer_is_competitor"), bool):
                E("customers.customer_is_competitor 必须是 bool (客户即竞争者要点亮)")
            if not isinstance(cu.get("matrix"), list):
                E("customers.matrix 必须是 list (场景×产品线矩阵)")

    # ── business_model ──
    bm = card.get("business_model")
    if bm is not None:
        if not isinstance(bm, dict):
            E("business_model 必须是 dict")
        else:
            rs = bm.get("revenue_streams")
            if not isinstance(rs, list) or not rs:
                E("business_model.revenue_streams 必须是非空 list")
            else:
                for i, r in enumerate(rs):
                    if not isinstance(r, dict) or not _nonempty_str(r.get("stream")):
                        E(f"business_model.revenue_streams[{i}] 缺 stream")
                    elif "share_pct" in r and not _num_or_null(r["share_pct"]):
                        E(f"business_model.revenue_streams[{i}].share_pct 必须是数字或 null")
            for k in ("pricing_power", "working_capital", "capex_intensity", "value_capture"):
                if not _nonempty_str(bm.get(k)):
                    E(f"business_model.{k} 必须非空")
            if not isinstance(bm.get("cost_structure"), list) or not bm["cost_structure"]:
                E("business_model.cost_structure 必须是非空 list")
            ue = bm.get("unit_economics")
            if not isinstance(ue, list) or not ue:
                E("business_model.unit_economics 必须是非空 list (每档 ASP×GM→单台毛利, 缺 GM 写 null)")
            else:
                for i, u in enumerate(ue):
                    if not isinstance(u, dict) or not _nonempty_str(u.get("line")):
                        E(f"business_model.unit_economics[{i}] 缺 line"); continue
                    for k in ("asp_cny", "gm_pct", "gross_per_unit_cny"):
                        if k in u and not _num_or_null(u[k]):
                            E(f"business_model.unit_economics[{i}].{k} 必须是数字或 null")

    # ── landscape ──
    ls = card.get("landscape")
    if ls is not None:
        if not isinstance(ls, dict):
            E("landscape 必须是 dict")
        else:
            if not _nonempty_str(ls.get("market_size")):
                E("landscape.market_size 必须非空 (总量 + 口径)")
            sbt = ls.get("share_by_tier")
            if not isinstance(sbt, list) or not sbt:
                E("landscape.share_by_tier 必须是非空 list")
            else:
                for i, t in enumerate(sbt):
                    if not isinstance(t, dict) or not _nonempty_str(t.get("tier")) or not _nonempty_str(t.get("source")):
                        E(f"landscape.share_by_tier[{i}] 需 tier + source (份额必须写分子分母口径来源)")
                    elif "company_pct" in t and not _num_or_null(t["company_pct"]):
                        E(f"landscape.share_by_tier[{i}].company_pct 必须是数字或 null")
            comps = ls.get("competitors")
            if not isinstance(comps, list) or len(comps) < 2:
                E("landscape.competitors 必须是 ≥2 条的 list")
            else:
                for i, c in enumerate(comps):
                    if not isinstance(c, dict) or not _nonempty_str(c.get("name")) or not _nonempty_str(c.get("position")):
                        E(f"landscape.competitors[{i}] 需 name + position (站位: 独立第三方/整车厂自配/外资合资)")
            if not isinstance(ls.get("competitive_axes"), list) or not ls["competitive_axes"]:
                E("landscape.competitive_axes 必须是非空 list")

    # ── demand_drivers (铁律 1 同款) ──
    dd = card.get("demand_drivers")
    if dd is not None:
        if not isinstance(dd, dict):
            E("demand_drivers 必须是 dict")
        else:
            pr = dd.get("primary")
            if not isinstance(pr, dict):
                E("demand_drivers.primary 必须是 dict")
            else:
                for k in ("name", "affects"):
                    if not _nonempty_str(pr.get(k)):
                        E(f"demand_drivers.primary.{k} 必须非空")
                if pr.get("direction") not in ("+", "-"):
                    E("demand_drivers.primary.direction 必须是 '+' 或 '-' (禁 null; 方向从数据 derive, 铁律 1)")
                sens = pr.get("sensitivity")
                if not isinstance(sens, list) or len(sens) < 2:
                    E("demand_drivers.primary.sensitivity 必须 ≥2 档 (单点不构成敏感性)")
                else:
                    for i, sv in enumerate(sens):
                        if not isinstance(sv, dict):
                            E(f"demand_drivers.primary.sensitivity[{i}] 必须是 dict"); continue
                        for k in ("level", "edge", "source"):
                            if not _nonempty_str(str(sv.get(k, "")) if sv.get(k) is not None else ""):
                                E(f"demand_drivers.primary.sensitivity[{i}] 缺 '{k}' (level=变量档位, edge=对公司量价影响, source=出处)")
            if not isinstance(dd.get("secondary"), list):
                E("demand_drivers.secondary 必须是 list (无则 [])")
            if not isinstance(dd.get("history"), list):
                E("demand_drivers.history 必须是 list (历史周期轮次; 无则 [])")

    # ── contradictions (铁律 2/11) ──
    cons = card.get("contradictions")
    if cons is not None:
        if not isinstance(cons, list) or not cons:
            E("contradictions 必须是非空 list (铁律 2: 主动找跨源/跨口径矛盾; 确无 → [{\"none_found\": true, \"searched\": \"...\"}])")
        else:
            for i, c in enumerate(cons):
                if not isinstance(c, dict):
                    E(f"contradictions[{i}] 必须是 dict"); continue
                if c.get("none_found"):
                    if not _nonempty_str(c.get("searched")):
                        E(f"contradictions[{i}] none_found=true 必须带 'searched'")
                    continue
                for k in ("claim_a", "claim_b", "source_a", "source_b", "resolution"):
                    if not _nonempty_str(c.get(k)):
                        E(f"contradictions[{i}] 缺 '{k}' (矛盾五要素)")

    # ── changes_and_debates ──
    cd = card.get("changes_and_debates")
    if cd is not None:
        if not isinstance(cd, dict):
            E("changes_and_debates 必须是 dict")
        else:
            for k in ("bull", "bear", "core_disagreement", "cognitive_position"):
                if not _nonempty_str(cd.get(k)):
                    E(f"changes_and_debates.{k} 必须非空")
            ss = cd.get("structural_shifts")
            if not isinstance(ss, list) or not ss:
                E("changes_and_debates.structural_shifts 必须是非空 list (没有结构性变化的公司不存在)")
            else:
                for i, sh in enumerate(ss):
                    if not isinstance(sh, dict) or not _nonempty_str(sh.get("shift")) or not _nonempty_str(sh.get("stage")):
                        E(f"changes_and_debates.structural_shifts[{i}] 需 shift + stage (真量产/试点/PPT)")
                    elif not isinstance(sh.get("is_new_species"), bool):
                        E(f"changes_and_debates.structural_shifts[{i}].is_new_species 必须是 bool (true → 起 Mode A 卡)")

    # ── segment_separability ──
    sp = card.get("segment_separability")
    if sp is not None:
        if not isinstance(sp, dict):
            E("segment_separability 必须是 dict")
        else:
            lc = sp.get("lines_count")
            if not isinstance(lc, int) or isinstance(lc, bool) or lc < 1:
                E(f"segment_separability.lines_count 必须是 ≥1 的 int (当前 {lc!r}) —— 写数字 4, 不要写 '3-4 条'")
            if not _nonempty_str(sp.get("diagnosis")):
                E("segment_separability.diagnosis 必须非空 (3 层结论一句话)")
            if not isinstance(sp.get("table"), list) or not sp["table"]:
                E("segment_separability.table 必须是非空 list (产线/客户/周期 三层)")

    # ── glossary / sources (铁律 7) ──
    gl = card.get("glossary")
    if gl is not None:
        if not isinstance(gl, list) or len(gl) < 5:
            E("glossary 必须是 ≥5 条的 list (科普卡名词表)")
        else:
            for i, g in enumerate(gl):
                if not isinstance(g, dict) or not _nonempty_str(g.get("term")) or not _nonempty_str(g.get("plain")):
                    E(f"glossary[{i}] 必须是 {{term, plain}}")
    # ── visuals (铁律 13) ──
    vs = card.get("visuals")
    if vs is not None:
        if not isinstance(vs, list) or not vs:
            E("visuals 必须是非空 list (铁律 13: 至少一张结构图, 官方没有就 draw_structure.py 自绘)")
        else:
            has_structure = False
            for i, v in enumerate(vs):
                if not isinstance(v, dict):
                    E(f"visuals[{i}] 必须是 dict"); continue
                for k in ("id", "file", "caption", "module"):
                    if not _nonempty_str(v.get(k)):
                        E(f"visuals[{i}] 缺 '{k}'")
                if v.get("role") not in VISUAL_ROLES:
                    E(f"visuals[{i}].role={v.get('role')!r} 必须 ∈ {sorted(VISUAL_ROLES)}")
                if v.get("source_type") not in VISUAL_SOURCE_TYPES:
                    E(f"visuals[{i}].source_type={v.get('source_type')!r} 必须 ∈ {sorted(VISUAL_SOURCE_TYPES)} (铁律 13: 只许官网/IR/年报/自绘)")
                elif v.get("source_type") != "self_drawn" and not _nonempty_str(v.get("source_url")):
                    E(f"visuals[{i}] 非自绘图必须带 source_url (来源行要能回溯)")
                if not _nonempty_str(v.get("accessed")):
                    E(f"visuals[{i}] 缺 'accessed' (访问/绘制日期)")
                if v.get("role") == "structure":
                    has_structure = True
            if not has_structure:
                E("visuals 里没有 role='structure' 的图 (铁律 13: 业务/商业逻辑结构图必有一张, 官方没有就自绘标 DNA)")
    vm = card.get("visuals_missing")
    if vm is not None and not isinstance(vm, list):
        E("visuals_missing 必须是 list (没拿到的图: {what, why})")

    so = card.get("sources")
    if so is not None:
        if not isinstance(so, list) or len(so) < 3:
            E("sources 必须是 ≥3 条的 list (铁律 7: 数字要有出处)")
        else:
            for i, x in enumerate(so):
                if not isinstance(x, dict) or not _nonempty_str(x.get("title")):
                    E(f"sources[{i}] 缺 title")
    return errs


def soft_warnings(card: dict) -> list:
    warns: list = []
    pls = card.get("product_lines") or []
    shares = [p.get("rev_share_pct") for p in pls if isinstance(p, dict)]
    if shares and all(isinstance(x, (int, float)) for x in shares):
        tot = sum(shares)
        if abs(tot - 100) > 5:
            warns.append(f"product_lines.rev_share_pct 合计 {tot:.1f}%,偏离 100 超 5 个点 —— 少了'其他'档或口径不一致")
    if pls and all((p.get("gm_pct") is None) for p in pls if isinstance(p, dict)):
        warns.append("所有产品线 gm_pct 都是 null —— 确认年报确实不披露分档毛利率;能从卖方拆分补的标 EST 补上")
    tp = card.get("tech_primer") or {}
    if isinstance(tp, dict) and isinstance(tp.get("standards_timeline"), list) and not tp["standards_timeline"]:
        warns.append("tech_primer.standards_timeline 为空 —— 确认这个行业真的没有监管/技术代际驱动")
    cu = card.get("customers") or {}
    if isinstance(cu, dict) and cu.get("top5_pct") is None:
        warns.append("customers.top5_pct 为 null —— 年报通常披露前五客户占比,再找一遍")
    bm = card.get("business_model") or {}
    if isinstance(bm, dict):
        ue = bm.get("unit_economics") or []
        if ue and all(isinstance(u, dict) and u.get("gross_per_unit_cny") is None for u in ue):
            warns.append("unit_economics 全部 gross_per_unit_cny=null —— 至少用综合毛利率给一个 blended 单台毛利 (标 EST)")
    vs = card.get("visuals") or []
    covered = {v.get("product_line_id") for v in vs if isinstance(v, dict) and v.get("role") == "product"}
    missing_pl = [p.get("id") for p in pls if isinstance(p, dict) and p.get("id") not in covered and p.get("id") != "O"]
    if missing_pl:
        warns.append(f"产品线 {missing_pl} 没有 role='product' 的官方实物图 (铁律 13: 每档一张; '其他' 档可免)")
    mo = card.get("moat") or []
    if isinstance(mo, list) and mo:
        strengths = [m.get("strength") for m in mo if isinstance(m, dict)]
        if strengths and all(s == "强" for s in strengths):
            warns.append("moat 全部是「强」—— 铁律 19: 一张全强的壁垒表等于没做功课, 至少写清哪一层最薄")
        thin = [m.get("layer") for m in mo if isinstance(m, dict) and m.get("strength") == "弱"]
        if not thin:
            warns.append("moat 里没有一条「弱」—— 确认真的没有已被追平的环节, 有就点名 (LO 研究看的是哪层先破)")
    cd = card.get("changes_and_debates") or {}
    if isinstance(cd, dict):
        ns = [s for s in (cd.get("structural_shifts") or []) if isinstance(s, dict) and s.get("is_new_species")]
        if ns:
            warns.append(f"{len(ns)} 条结构变化标了 is_new_species=true —— 记得为它们起 Mode A 认知卡: "
                         + "; ".join(s.get("shift", "") for s in ns))
    return warns


def build_meta(subject_id: str, subject_type: str, data_as_of: str | None) -> dict:
    return {
        "subject_id": subject_id,
        "mode": "B",
        "card_type": "business",
        "subject_type": subject_type,
        "schema_version": SCHEMA_VERSION,
        "source_skill": SOURCE_SKILL,
        "units": {"revenue": "yi_cny", "asp": "cny_per_unit", "pct": "percent"},
        "data_as_of": data_as_of or "",
        "written_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Mode B 业务认知卡写出 + 自检")
    ap.add_argument("card", help="填好的业务认知卡内容 JSON (顶层 14 字段)")
    ap.add_argument("--subject-id", required=True, help="如 yuchai-cyd-20260915")
    ap.add_argument("--subject-type", choices=["company", "industry"], default="company")
    ap.add_argument("--data-as-of", default=None, help="数据截止说明,如 'FY2025 (20-F 2026-02-27)'")
    ap.add_argument("--out", required=True, help="输出 business_primer.json 路径")
    args = ap.parse_args()

    try:
        card = json.loads(Path(args.card).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"[X] 读取 card 失败: {e}", file=sys.stderr)
        return 1

    meta_in = card.pop("_meta", None) or {}
    data_as_of = args.data_as_of or meta_in.get("data_as_of")

    errs = validate(card, subject_type=args.subject_type)
    if errs:
        print(f"[X] Mode B 业务认知卡校验失败 ({len(errs)} 处) —— 修好再写出:", file=sys.stderr)
        for e in errs:
            print(f"   - {e}", file=sys.stderr)
        return 1

    for w in soft_warnings(card):
        print(f"[!] {w}", file=sys.stderr)

    payload = {"_meta": build_meta(args.subject_id, args.subject_type, data_as_of)}
    payload.update(card)

    out_path = Path(args.out).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    pls = card.get("product_lines", [])
    print(f"[OK] Mode B 业务认知卡已写出 → {out_path}", file=sys.stderr)
    print(f"     subject={card.get('entity', {}).get('listed_name') or args.subject_id} | product_lines={len(pls)} "
          f"| lines_count={card.get('segment_separability', {}).get('lines_count')} "
          f"| contradictions={len(card.get('contradictions', []))} | glossary={len(card.get('glossary', []))} "
          f"| visuals={len(card.get('visuals', []))} | sources={len(card.get('sources', []))}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
