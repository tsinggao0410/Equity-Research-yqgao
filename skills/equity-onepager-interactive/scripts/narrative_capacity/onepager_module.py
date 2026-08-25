"""把叙事/题材容量算成 onepager 的 page_model 片段。

    python3 onepager_module.py --name 巨星科技 --model <page_model.json> [--write]

产出两块：
  part1.narrative_capacity      → 第一章 1.7 可交易容量与波动位置（横截面）
  part2.phases[i].basket_beta   → 第二章 2.2 阶段列内 个股 vs 篮子 涨幅对照

第二块是这个模块真正的价值：阶段分解里的 M（板块/贝塔）原来只能估，
现在有实测锚——个股该段涨了多少、它所在的叙事篮子涨了多少，差额就是超额。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import roster                                                        # noqa: E402
from jiuyan import JiuyanSession, chain_date, first_lines, parse_events  # noqa: E402
from wencai import WencaiSession, pick                               # noqa: E402
from concept_capacity import (company_profile, codes_capacity,       # noqa: E402
                              MAX_QUESTION)
from dispersion import basket_dispersion, tightness                  # noqa: E402
from relevance import biz_match                                      # noqa: E402
from vol_percentile import (KlineStore, basket_index, basket_turnover,  # noqa: E402
                            percentile_of, smooth, to_symbol, window_return)
from bench_index import fetch_bench                                   # noqa: E402
from tiering import ma_posture, tier_members                          # noqa: E402

# 韭研标题的日期括号半角全角混用：中美降税(260416) / 外贸出口（20250120）
_TITLE = re.compile(r"[（(].*$")


def short_title(t: str) -> str:
    return _TITLE.sub("", t or "").strip()

YI = 1e8
# 阶段①起点 2022-12，到今天约 900 个交易日；留足余量，缓存会记根数不会误命中旧的
KLINE_DAYS = 1150


def yi(x):
    return None if x is None else round(x / YI, 1)


PEER_N = 6          # 每个篮子展示几只核心个股（按自由流通市值）


# 子题材词有两类匹配不上：行话（果链/纺服）和地理（越南工厂/越南生产基地）。
# 行话给同义扩展；地理从行业主营根本推不出来——那种链的入选依据在韭研正文里，
# 匹配不到就走实证兜底（β + 自建链累计超额），不编。
SUBTHEME_SYN = {
    "果链": "苹果 消费电子 零部件 组装 光学 声学 结构件 玻璃 精密",
    "纺服": "服装 纺织 棉纺 针织 家纺 鞋 面料 印染",
    "轻工业": "家居 家具 文具 造纸 塑料 日用 五金",
    "工具五金": "工具 五金 手工具 电动工具 刀具",
    "工程机械": "工程机械 起重 挖掘 装载 叉车 高空作业 液压 铲运 推土",
    "宠物": "宠物 饲料 食品",
    "跨境电商": "电商 跨境 出海 品牌消费 互联网",
    "纺织": "纺织 棉纺 印染 面料 服装 家纺",
}


def assign_subtheme(ind: str, prod: str, subs: List[str]) -> str:
    """把公司归到这条链的子题材上——那就是它「凭什么入选」。

    韭研 keyword 字段里，非个股的 token 就是子题材词：
      「工具五金 工程机械 宠物 跨境电商 | 巨星科技 欧圣电气 … 三一重工 徐工机械 …」
    三一/徐工归工程机械、巨星/欧圣归工具五金。原来这些词被当噪音丢掉了，其实是分组标签。
    用主营+行业去匹配，命中最长片段的那个子题材就是归属；匹配不上返回空，不猜。
    """
    text = f"{ind} {prod}".lower()
    best, hit = "", 0.0
    for t in subs:
        v = biz_match(t, text)
        for syn in (SUBTHEME_SYN.get(t, "")).split():
            if syn and syn.lower() in text:
                v = max(v, 1.0)
        if v > hit:
            best, hit = t, v
    return best if hit >= 0.5 else ""


def mention_of(content: str, name: str, width: int = 60) -> str:
    """韭研正文里点名这家公司的那句话（有则引，无则空）。"""
    if not name:
        return ""
    for seg in re.split(r"[。；\n]", content or ""):
        if name in seg:
            seg = " ".join(seg.split())
            return seg[:width] + ("…" if len(seg) > width else "")
    return ""


def peer_intros(s: WencaiSession, codes: List[str]) -> Dict[str, Dict[str, str]]:
    """给一批代码取 {末级行业, 首个主营产品}，两项分开返回好上表格分列。

    "这条线上还有谁" 比 "这条线有多少只" 有用得多——看到徐工机械/三一重工，
    就知道中美降税这条线的真实构成是工程机械出口，不是手工具。
    问句仍受 ~200 字符限制，按长度切块。
    """
    tail = "所属同花顺行业 主营产品名称"
    out: Dict[str, Dict[str, str]] = {}
    budget = MAX_QUESTION - len(tail) - 1
    chunk: List[str] = []
    size = 0

    def flush(cs):
        if not cs:
            return
        try:
            r = s.query(f"{' '.join(cs)} {tail}", all_rows=False)
        except Exception:
            return
        ck, ik, pk = pick(r, "股票代码"), pick(r, "所属同花顺行业"), pick(r, "主营产品名称")
        for row in r["rows"]:
            code = str(row.get(ck) or "").split(".")[0]
            ind = str(row.get(ik) or "").split("-")[-1].strip()
            prod = str(row.get(pk) or "").split("||")[0].strip()
            if code and (ind or prod):
                out[code] = {"ind": ind, "prod": prod[:18]}

    for c in codes:
        need = len(c) + (1 if chunk else 0)
        if chunk and size + need > budget:
            flush(chunk); chunk, size = [c], len(c)
        else:
            chunk.append(c); size += need
    flush(chunk)
    return out


TIER_ORD = {"龙头": 0, "中军": 1, "后排": 2}
TIER_CAP = {"龙头": 4, "中军": 4, "后排": 3}     # 每层最多展示几只


def pick_peers(members, tiers, self_code):
    """按层挑展示名单，而不是无脑取自由流通前 6。

    ★这一步是分层真正付钱的地方：龙头是**行情属性**，常常不在市值前 6 里。
    按市值取前 6 会把「谁在定义这条线的涨幅」整个漏掉。本股无论在哪一层都强制进名单。
    """
    ok = [m for m in members if m.get("float_mktcap")]
    ok.sort(key=lambda m: m["float_mktcap"], reverse=True)
    cd = lambda m: str(m.get("code") or "").split(".")[0]
    out, cnt = [], {"龙头": 0, "中军": 0, "后排": 0}
    for m in sorted(ok, key=lambda m: (TIER_ORD.get((tiers.get(cd(m)) or {}).get("tier"), 9),
                                       -(m.get("float_mktcap") or 0))):
        t = (tiers.get(cd(m)) or {}).get("tier") or "后排"
        # tiering.py 在「整条线都跌」时会发出 '相对最强' 这类层名（那种情况下本就没有龙头，
        # 见 CK-1.7 l）；TIER_CAP 只列了三层，直接下标会 KeyError → 未知层按后排配额兜底。
        cnt.setdefault(t, 0)
        if cnt[t] < TIER_CAP.get(t, 3) or cd(m) == self_code:
            out.append(m); cnt[t] = cnt.get(t, 0) + 1
    return out


def basket_payload(kind: str, label: str, sub: str, r: Dict[str, Any],
                   tv: Dict[str, Any], self_code: str,
                   extra: Dict[str, Any]) -> Dict[str, Any]:
    """一条叙事/题材的三个量：分母(容量) · 分子(资金来没来) · 我的份额。

    单独看容量没有决策含义——8,347 亿这个数不配上「钱有多少」和「我占多少」，
    推不出任何东西。三个量凑齐才能出一句有用的话。
    """
    cap = r["capacity"]
    members = r["members"]

    # 我的份额与位次：钱来了会不会买到我
    ranked = sorted([m for m in members if m.get("float_mktcap")],
                    key=lambda m: m["float_mktcap"], reverse=True)
    mine = next((m for m in members
                 if str(m.get("code") or "").split(".")[0] == self_code), None)
    rank = next((i + 1 for i, m in enumerate(ranked)
                 if str(m.get("code") or "").split(".")[0] == self_code), None)
    share = None
    if mine and mine.get("float_mktcap") and cap.get("float_mktcap"):
        share = round(mine["float_mktcap"] / cap["float_mktcap"] * 100, 1)

    out: Dict[str, Any] = {
        "kind": kind, "name": label, "sub": sub,
        "n": r["n_members"], "n_declared": r.get("n_declared"),
        "mktcap_yi": yi(cap.get("total_mktcap")),
        "float_yi": yi(cap.get("float_mktcap")),
        "amount_yi": yi(cap.get("amount")),
        "self": {"share_pct": share, "rank": rank, "of": len(ranked)},
        # 核心个股：★按层挑（龙头/中军/后排），不是无脑取自由流通前 N
        # ★2026-08-16：同时带上总市值。页面那一列原来只有 float_yi 且**无表头**，
        # 读者按「市值」去认，比亚迪自由流通 2,184 亿 vs 总市值 7,642 亿，差 3.5 倍
        # ——数字没错，是口径没标。两个口径一起给，就没有认错的余地。
        "peers": [{"name": m.get("name"),
                   "code": str(m.get("code") or "").split(".")[0],
                   "float_yi": yi(m.get("float_mktcap")),
                   "mktcap_yi": yi(m.get("mktcap")),
                   "is_self": str(m.get("code") or "").split(".")[0] == self_code}
                  for m in pick_peers(members, extra.get("_tiers") or {}, self_code)],
        "members": [m.get("name") for m in members if m.get("name")],
        "warnings": r.get("warnings") or [],
    }

    # 分子：换手强度 = Σ成交额/Σ自由流通市值，及其三年分位
    ser = smooth(tv.get("series") or {}, 5)
    if tv.get("reliable") and len(ser) > 60:
        now = ser[max(ser)]
        pc = percentile_of(now, ser)
        out["turnover"] = {
            "now": round(now, 2), "pct": round(pc["pct"]) if pc.get("pct") is not None else None,
            "lo": round(pc["min"], 2), "med": round(pc["median"], 2), "hi": round(pc["max"], 2),
            "win_n": pc.get("n"), "win_from": pc.get("start"), "win_to": pc.get("end"),
        }
    else:
        out["turnover"] = None
        out["warnings"] = list(out["warnings"]) + [
            f"换手强度不可得：篮子 {tv.get('n_have')}/{tv.get('n_basket')} 只有日K"]
    out.update(extra)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="公司简称，如 巨星科技")
    ap.add_argument("--model", required=True, help="page_model.json 路径")
    ap.add_argument("--profile", default=os.environ.get(
        "WC_PROFILE", os.path.expanduser("~/.iwencai-profile")))
    ap.add_argument("--write", action="store_true", help="直接写回 page_model（默认只出片段）")
    ap.add_argument("--out", default=None, help="片段输出路径")
    ap.add_argument("--bench", default="", help=(
        "同期对照锚：申万二级行业名，逗号分隔（如 光伏设备,电网设备）。"
        "沪深300 自动附加。名录见 python3 bench_index.py --list <关键词>。"
        "概念篮子有诞生日、早期阶段会被硬闸掉，这条腿是那些阶段唯一的对照。"))
    args = ap.parse_args()

    model = json.load(open(args.model, encoding="utf-8"))
    phases = model.get("part2", {}).get("phases") or []
    if not phases:
        sys.exit("page_model 里没有 part2.phases，无法做阶段标注")

    store = KlineStore(days=KLINE_DAYS)

    with JiuyanSession() as jy:
        chains = jy.search(args.name)

    baskets: List[Dict[str, Any]] = []
    indices: List[Dict[str, Any]] = []

    with WencaiSession(profile_dir=args.profile) as s:
        rs = roster.load(s)
        p = company_profile(s, args.name)
        if not p["found"]:
            sys.exit(f"问财查不到「{args.name}」")
        self_code = str(p.get("code") or "").split(".")[0]

        # ---- 叙事：韭研产业链 ----
        for c in chains:
            names, others = roster.split_names(c["tokens"], rs)
            if not names:
                continue
            r = codes_capacity(s, [(n, rs[n]) for n in names])
            if not r["reliable"]:
                print(f"  ⚠ 跳过「{c['title']}」：只解析出 {r['resolve_rate']:.0%}", file=sys.stderr)
                continue
            tv = basket_turnover(r["members"], store)
            idx = basket_index(r["members"], store, exclude=self_code)
            # 叙事有生日：离散度窗口从建链日起算
            born = chain_date(c["title"])
            disp = basket_dispersion(r["members"], store, self_code, since=born)
            # ★分层用全篮子成分算（龙头常不在市值前几名里），方位吃已缓存的日线，零额外请求
            tiers = tier_members(r["members"], ((disp or {}).get("per") or {}))
            baskets.append(basket_payload(
                "叙事", short_title(c["title"]), born or "",
                r, tv, self_code,
                {"disp": disp, "disp_since": born or "", "_tiers": tiers,
                 "subthemes": others,          # 非个股 token ＝ 这条链的子题材词
                 "_content": c["content"],
                 "catalysts": parse_events(c["content"]),
                 "logic": (first_lines(c["content"], 1) or [""])[0],
                 "updated": (c.get("updated") or "")[:10],
                 "browsers": c.get("browsers"),
                 "excluded": others}))
            indices.append({"kind": "叙事", "name": short_title(c["title"]),
                            "idx": idx, "born": born or ""})

        # 题材（问财机器打标的概念）已按用户要求整块移除：
        # 沾边就挂、噪音大（智能物流里出现万科A），且离散度实测 R² 普遍 <0.2，
        # 说明那些标签根本不是共同因子，放进来只是占版面。1.7 只保留韭研的叙事。

        # ---- 入选理由：子题材归属 + 韭研原文点名 ----
        for b in baskets:
            subs = b.get("subthemes") or []
            content = b.get("_content") or ""
            for pr in b.get("peers") or []:
                pr["_subs"] = subs
                pr["_content"] = content

        # ---- 核心个股的一句话介绍（所有篮子合并去重，一次批量取）----
        need = []
        for b in baskets:
            for pr in b.get("peers") or []:
                if pr["code"] and pr["code"] not in need:
                    need.append(pr["code"])
        intros = peer_intros(s, need)
        for b in baskets:
            for pr in b.get("peers") or []:
                info = intros.get(pr["code"]) or {}
                pr["ind"] = info.get("ind", "")
                pr["prod"] = info.get("prod", "")
                sub = assign_subtheme(pr["ind"], pr["prod"], pr.pop("_subs", []) or [])
                quote = mention_of(pr.pop("_content", "") or "", pr.get("name") or "")
                # 优先级：韭研原文点名 > 子题材归属 > 实证兜底（跟不跟这条线，用数字说）
                pv = ((b.get("disp") or {}).get("per") or {}).get(pr["code"]) or {}
                pr["beta"] = pv.get("beta")
                pr["cum"] = pv.get("cum")
                # ★分层（龙头/中军/后排）与 K 线方位，判据随标签一起带出去
                tv2 = (b.get("_tiers") or {}).get(pr["code"]) or {}
                pr["tier"] = tv2.get("tier")
                pr["tier_basis"] = tv2.get("basis")
                sym = to_symbol(pr["code"])
                bars = store._load(sym) if sym else None
                po = ma_posture(bars) if bars else None
                if po:
                    pr["posture"] = po.get("state")
                    pr["posture_why"] = po.get("why")
                    pr["ma"] = po.get("ma")
                else:
                    pr["posture"] = None
                    pr["posture_why"] = "该股日线缓存缺失，方位不可得"
                parts = [x for x in (sub, quote) if x]
                if not parts and pv.get("beta") is not None:
                    parts = [f"β {pv['beta']}"
                             + (f" · 自建链 {pv['cum']:+.0f}%" if pv.get("cum") is not None else "")]
                pr["why"] = "　".join(parts)

    # ---- 同期对照锚：概念篮子被硬闸掉的阶段，靠它才有对照 ----
    bench = fetch_bench([x.strip() for x in args.bench.split(",") if x.strip()])

    # ---- 第二章：逐阶段 个股 vs 篮子 ----
    weekly = model["part2"]["weekly"]
    for ph in phases:
        d0, d1 = ph.get("from"), ph.get("to")
        stock = ph.get("chg")
        if stock is None:
            c0 = next((w["c"] for w in weekly if w["d"] >= d0), None)
            c1 = next((w["c"] for w in reversed(weekly) if w["d"] <= d1), None)
            stock = (c1 / c0 - 1) * 100 if c0 and c1 else None
        rows, dropped = [], []
        for ent in indices:
            eq = window_return(ent["idx"]["eq"], d0, d1)
            wt = window_return(ent["idx"]["wt"], d0, d1)
            if eq is None:
                continue
            # ★概念诞生日硬闸：建链日晚于阶段起点 = 这个概念在当时不存在，
            #   成分是照着已经涨完的那批票圈出来的，算出来的「超额」是伪读数。
            #   这比幸存者偏差更硬——不是输家掉出名单，是整个类别事后定义。
            born = ent.get("born") or ""
            if not born:
                dropped.append({"name": ent["name"], "born": None,
                                "chg_if_forced": round(eq, 1),
                                "why": "建链日不可核（标题无日期），无法证明这条叙事在本段已存在"})
                continue
            if born > d0:
                dropped.append({"name": ent["name"], "born": born,
                                "chg_if_forced": round(eq, 1),
                                "why": f"概念成立于 {born}，晚于本段起点 {d0}——"
                                       f"当时不存在，成分为事后定义"})
                continue
            rows.append({
                "kind": ent["kind"], "name": ent["name"], "born": born,
                "chg": round(eq, 1), "chg_w": round(wt, 1) if wt is not None else None,
                "excess": round(stock - eq, 1) if stock is not None else None,
            })
        # 行业/市场锚：分类持续维护、非事后圈定，只要指数序列覆盖到本段起点就算数
        bench_rows = []
        for b in bench:
            ser = b.get("series") or {}
            if b.get("error"):
                bench_rows.append({"kind": b["kind"], "name": b["name"],
                                   "chg": None, "error": b["error"]})
                continue
            first = b.get("first_date") or ""
            if first and first > d0:
                bench_rows.append({"kind": b["kind"], "name": b["name"], "chg": None,
                                   "error": f"指数序列自 {first} 起，未覆盖本段起点 {d0}"})
                continue
            r = window_return(ser, d0, d1)
            if r is None:
                continue
            bench_rows.append({
                "kind": b["kind"], "name": b["name"], "code": b.get("code"),
                "chg": round(r, 1),
                "excess": round(stock - r, 1) if stock is not None else None,
            })
        ph["basket_beta"] = {
            "stock_chg": round(stock, 1) if stock is not None else None,
            "rows": rows,
            "dropped": dropped,
            "bench": bench_rows,
            "usable": bool(rows) or any(x.get("chg") is not None for x in bench_rows),
            "note": "篮子＝等权指数（首日=100）且**已剔除本股**，否则个股权重大时超额会被自己稀释"
                    "（巨星科技占「外贸出口」自由流通市值 22.5%）；超额=个股涨幅−篮子涨幅，"
                    "给 R/M/V 里的 M 一个实测锚。"
                    "　★两道口径限制：①**概念诞生日硬闸**——建链日晚于本段起点的叙事整行剔除"
                    "（列在 dropped 里，只交代不给数），概念当时不存在时算出的超额是伪读数；"
                    "②留下的行仍是**当前成分回溯套用**，含幸存者偏差，只比方向与量级、不作精确值。"
                    "　行业/市场锚（bench）是申万二级行业指数与沪深300：分类持续维护、成分非事后圈定，"
                    "与概念篮子不同源，两者绝对值不可直接比。",
        }

    for b in baskets:
        b.pop("_tiers", None)                       # 内部键，不进产物

    model.setdefault("part1", {})["narrative_capacity"] = {
        "asof": model.get("meta", {}).get("asof"),
        "note": "三个量一起读：容量＝钱要摊多薄 · 换手强度＝钱来了没有 · 位次＝钱来了会不会买到我。"
                "单看容量没有决策含义。伞形篮子（成分 >500 只）已剔除。",
        "caliber": "第一性原理：股价＝资金÷筹码——叙事决定钱往哪去，容量决定钱摊多薄，"
                   "我的份额决定我分到多少。容量大≠需求大，反过来：容量大是吸收力强、单位资金推力小；"
                   "真正有赔率的是失配——叙事级别高但篮子小。容量能独立回答的只有一件事：仓位放不放得进去。"
                   "　换手强度＝Σ成交额÷Σ自由流通市值（5日平滑），是「钱来了没有」的单调指标；"
                   "三年分位窗口 1095 自然日。（不用日振幅分位：波动低既可能没人玩、也可能筹码锁死蓄势，"
                   "方向不单调。）自由流通股数由 当前自由流通市值÷最新收盘价 反推，期内视为不变。"
                   "核心个股按自由流通市值取前 6，▶ 为本股。"
                   "　离散度：日均横截面标准差＝mean_t(std_i(超额收益))，用日频不用累计"
                   "（累计方差会被窗口长度污染，日频跨篮子可比）；R²＝成分股超额对篮子超额回归的均值，"
                   "衡量这条叙事解释了多少波动；β＝本股对篮子的弹性。三者都**先减去沪深300**再算，"
                   "否则全市场普涨时每条线的 R² 都很高、问不出「是真因子还是标签」。"
                   "叙事窗口自建链日起算，题材无建链日固定用近一年，两者窗口不同源不可直接比绝对值。",
        "src": "韭研公社 industry/list + 问财 get-robot-data + 新浪日K(备源腾讯)",
        "baskets": baskets,
    }

    frag = {"part1.narrative_capacity": model["part1"]["narrative_capacity"],
            "part2.phases[].basket_beta": [
                {"phase": ph["name"], **ph["basket_beta"]} for ph in phases]}

    # 硬闸的结果要在 stderr 上说清楚，否则「阶段①没有对照」看着像取数失败
    for ph in phases:
        bb = ph["basket_beta"]
        if bb["dropped"]:
            print(f"  ⓘ {ph['name']}｜{ph.get('from')}~{ph.get('to')}："
                  f"叙事篮子 {len(bb['rows'])} 条可用 / {len(bb['dropped'])} 条被诞生日硬闸剔除",
                  file=sys.stderr)
        if not bb["usable"]:
            print(f"  ⚠ {ph['name']}：**本段无任何合法对照**——概念篮子全部事后定义，"
                  f"行业锚也未覆盖。该段 basket_beta 不得渲染、logic 里不得出现篮子数字。",
                  file=sys.stderr)
    out = args.out or os.path.join(os.path.dirname(args.model), "narrative_capacity.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(frag, f, ensure_ascii=False, indent=1)
    print(f"片段已写 {out}")

    if args.write:
        with open(args.model, "w", encoding="utf-8") as f:
            json.dump(model, f, ensure_ascii=False, indent=1)
        print(f"已写回 {args.model}")


if __name__ == "__main__":
    main()
