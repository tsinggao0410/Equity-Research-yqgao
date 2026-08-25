"""公司 → 分面概念画像 → 概念的可交易容量。

一次调用拿全公司画像（概念/两套行业分类/主营产品/地域/市值），
概念再按"面"归类，避免前三个全落在同一个面上——兆易创新按问财原序取前三是
存储芯片/汽车芯片/MCU芯片，三个都是产品面，下游应用面和客户面一个都没覆盖到。

数字全部来自问财 get-robot-data 原始字段，取不到的指标返回 None 并进 warnings，
不当 0 处理。
"""
from __future__ import annotations

import datetime as dt
import json
import re
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from wencai import MAX_QUESTION, WencaiSession, pick, to_num

# 概念成分数每天几乎不变，且概念在不同公司之间大量重复（芯片概念、融资融券……）。
# 落盘共享，重复运行和跨公司都不再重复探测。
SIZE_CACHE = Path(__file__).resolve().parent / ".concept_sizes.json"
SIZE_TTL_DAYS = 7

# ---------------- 概念分面 ----------------
# 顺序即优先级：先判机制（剔除），再判客户，再产品，再应用，再主题，最后区域。
# "汽车芯片"落产品（芯片是名词中心），"汽车电子"落应用（没有裸"电子"关键词）。

FACETS: List[tuple] = [
    # 机制 / 事件 / 参股 —— 一律剔除。它们不描述主业：
    # "融资融券" 覆盖两千多只，"参股银行" 说的是资产负债表上的股权而不是经营。
    ("机制", re.compile(
        r"融资融券|[沪深]股通|港股通|次新股|^新股|专精特新|国企改革|国资改革"
        r"|人民币(贬|升)值|同花顺[^;]*\d|中国AI\s*\d|中报预增|年报预增|业绩预[增减告]"
        r"|MSCI|富时|标普|道琼斯|破净|高送转|股权转让|并购重组|举牌|减持|回购"
        r"|机构重仓|基金重仓|QFII|社保|北向|转融通|注册制|创业板综|科创综|ST"
        r"|^参股|参股(银行|券商|保险|基金|期货|新三板|科创)")),
    ("客户生态", re.compile(
        r"华为|小米|苹果|特斯拉|英伟达|阿里巴巴|腾讯|百度|字节|抖音|快手|小红书"
        r"|比亚迪|中芯国际|富士康|台积电|三星|鸿蒙|鲲鹏|昇腾|海思|DeepSeek|智谱"
        r"|OpenAI|Meta|谷歌|亚马逊|微软|蔚来|理想|小鹏|宁德|沃尔玛|亚马逊|Costco")),
    ("产品技术", re.compile(
        r"芯片|存储|闪存|DRAM|NAND|NOR|MCU|CPU|GPU|FPGA|封装|光刻|材料|设备"
        r"|电池|模组|传感器|PCB|覆铜板|光模块|CPO|光纤|面板|OLED|MiniLED|MicroLED"
        r"|电机|减速器|丝杠|轴承|连接器|被动元件|功率器件|分立器件|第三代半导体"
        r"|液冷|电源|逆变器|铜箔|隔膜|正极|负极|稀土|钨|锂|钴|镍"
        r"|工具|刀具|紧固件|铸造|锻造|模具|机床|激光|阀门|泵|齿轮")),
    # 渠道 / 商业模式 —— 出口制造、消费品公司的关键一面，原来整条缺失，
    # 巨星科技的"跨境电商"曾经掉进未分类。
    ("渠道模式", re.compile(
        r"跨境电商|电商|直播|带货|免税|新零售|连锁|经销|代工|ODM|OEM|贴牌"
        r"|出海|外贸|进出口|供应链|仓储|自有品牌|渠道|批发|团购|会员店")),
    # 消费场景 —— To C 的使用场景，与工业下游分开。
    ("消费场景", re.compile(
        r"露营|户外|宠物|预制菜|茶饮|白酒|啤酒|食品|饮料|乳业|调味|化妆品|美妆"
        r"|医美|母婴|婴童|珠宝|黄金饰|旅游|酒店|餐饮|影视|院线|游戏|潮玩|IP经济"
        r"|谷子|家居|家电|家纺|服装|鞋|体育|健身|银发|养老|生育|婚庆")),
    ("下游应用", re.compile(
        r"汽车|手机|服务器|数据中心|AIDC|机器人|眼镜|耳机|穿戴|音箱|医疗|器械"
        r"|光伏|风电|储能|核电|军工|航空|航天|卫星|无人机|无人驾驶|智能座舱"
        r"|PC|平板|教育|农业|养殖|快递|物流|工程机械|建筑|地产|水泥|钢铁"
        r"|充电桩|换电|氢能|电网|轨交|船舶|安防|摄像|环保|水务")),
    ("主题叙事", re.compile(
        r"人工智能|AI|信创|国产替代|自主可控|东数西算|算力|数字经济|数据要素"
        r"|元宇宙|虚拟现实|增强现实|区块链|数字货币|量子|新质|中特估|一带一路"
        r"|数据安全|网络安全|物联网|工业互联网|5G|6G|低空经济|合成生物|可控核聚变"
        r"|绿电|碳中和|碳交易|减速带|专利")),
    ("区域属性", re.compile(
        r"自贸区|大湾区|西部大开发|海峡两岸|雄安|京津冀|长三角|成渝|东北振兴"
        r"|上海|北京|深圳|广东|浙江|江苏|山东|四川|新疆|西藏|海南|水利")),
]

# 成分股数超过这个数就是"伞形标签"：覆盖面太广，对单个公司没有定位信息，
# 算出来的容量也不可解读——不会因为芯片概念有 34.5 万亿就说巨星科技的赛道这么大。
# 而且它们是调用量大头（1214 只要翻 13 轮）。默认跳过。
UMBRELLA_MIN = 500
NARROW_MAX = 150       # 低于此视为"窄"，定位性最强


def breadth(n: Optional[int]) -> str:
    if n is None:
        return "未知"
    return "窄" if n < NARROW_MAX else ("中" if n < UMBRELLA_MIN else "伞形")

PROFILE_FIELDS = {
    "code": "股票代码",
    "name": "股票简称",
    "ths_industry": "所属同花顺行业",
    "sw_industry": "所属申万行业",
    "products": "主营产品名称",
    "province": "省份",
    "city": "城市",
    "n_concepts": "所属概念数量",
    "mktcap": "总市值",
    "float_mktcap": "自由流通市值",
}

# 只拉真正用得上的字段。换手率被成交额覆盖，概念解析问财在成分股查询里从不返回，
# 都从问句里去掉——多写一个指标会让问财多算一列，白花时间。
MEMBER_TAIL = "总市值 自由流通市值 振幅 成交额"

MEMBER_FIELDS = {
    "code": "股票代码",
    "name": "股票简称",
    "mktcap": "总市值",
    "float_mktcap": "自由流通市值",
    "amount": "成交额",
    "amplitude": "振幅",
}


def classify(concept: str) -> str:
    for facet, pattern in FACETS:
        if pattern.search(concept):
            return facet
    return "未分类"


def company_profile(s: WencaiSession, company: str) -> Dict[str, Any]:
    """一次调用拿全公司画像。概念按面归类，机制标签单独隔离。

    机制标签必须剔除：它们不是可交易主题，成分覆盖全市场，
    "融资融券"能把两千多只股票算进来，加总市值毫无意义。
    """
    q = (f"{company} 所属概念 所属同花顺行业 所属申万行业 主营产品名称 省份 "
         f"所属概念数量 总市值 自由流通市值")
    r = s.query(q, all_rows=False)
    if not r["rows"]:
        return {"company": company, "query": q, "found": False}

    row = r["rows"][0]
    out: Dict[str, Any] = {"company": company, "query": q, "found": True}
    for out_key, cn in PROFILE_FIELDS.items():
        val = row.get(pick(r, cn) or "")
        out[out_key] = to_num(val) if out_key in ("mktcap", "float_mktcap") else val

    concepts = [c.strip() for c in re.split(r"[;；]", str(row.get(pick(r, "所属概念") or "") or ""))
                if c.strip()]
    by_facet: Dict[str, List[str]] = {}
    for c in concepts:
        by_facet.setdefault(classify(c), []).append(c)

    out["concepts_all"] = concepts
    out["by_facet"] = by_facet
    out["mechanism"] = by_facet.get("机制", [])
    out["tradable"] = [c for c in concepts if classify(c) != "机制"]
    return out


def subject_of(concept: str) -> str:
    """概念名 → 问财主语。"小米概念" 已自带"概念"二字，别拼成"小米概念概念股"。"""
    return (concept if concept.endswith("概念") else f"{concept}概念") + "股"


def _load_size_cache() -> Dict[str, dict]:
    try:
        return json.loads(SIZE_CACHE.read_text())
    except Exception:
        return {}


def probe_sizes(s: WencaiSession, concepts: Sequence[str],
                ttl_days: int = SIZE_TTL_DAYS) -> Dict[str, Optional[int]]:
    """探每个概念的成分股数：perpage=1 只取 meta.extra.code_count，单次 ~0.35s。

    先探再取，是为了在花大代价翻页之前就把伞形标签挡掉——
    芯片概念 915 只要翻 10 轮、机器人概念 1216 只要翻 13 轮，探测才花一次。
    命中缓存则连这一次都省掉。
    """
    cache = _load_size_cache()
    today = dt.date.today()
    sizes: Dict[str, Optional[int]] = {}
    dirty = False

    for c in concepts:
        hit = cache.get(c)
        if hit:
            try:
                if (today - dt.date.fromisoformat(hit["d"])).days <= ttl_days:
                    sizes[c] = hit["n"]
                    continue
            except Exception:
                pass
        try:
            n = s.query(subject_of(c), all_rows=False, perpage=1).get("total")
        except Exception:
            n = None
        sizes[c] = n
        if n is not None:
            cache[c] = {"n": n, "d": today.isoformat()}
            dirty = True

    if dirty:
        try:
            SIZE_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0))
        except Exception:
            pass
    return sizes


def select_concepts(
    s: WencaiSession,
    profile: Dict[str, Any],
    n: int,
    umbrella_min: int = UMBRELLA_MIN,
) -> Dict[str, Any]:
    """选 n 个概念：先剔机制、再剔伞形，然后每个面各取一个。

    返回 {"picks": [(概念, 面, 成分数)], "umbrella": [...], "sizes": {...}}。
    伞形的单独列出来给人看，不是静默丢掉。
    实在凑不满 n 个时才回补伞形，并在 picks 里如实标出面为「伞形回补」。
    """
    tradable = profile["tradable"]
    sizes = probe_sizes(s, tradable)

    keep = [c for c in tradable if (sizes.get(c) or 0) <= umbrella_min]
    umbrella = [(c, sizes.get(c)) for c in tradable if (sizes.get(c) or 0) > umbrella_min]

    order = [f for f, _ in FACETS if f != "机制"] + ["未分类"]
    pools: Dict[str, List[str]] = {f: [] for f in order}
    for c in keep:
        pools.setdefault(classify(c), []).append(c)

    picks: List[tuple] = []
    while len(picks) < n and any(pools.get(f) for f in order):
        for f in order:
            if len(picks) >= n:
                break
            if pools.get(f):
                c = pools[f].pop(0)
                picks.append((c, f, sizes.get(c)))

    for c, size in umbrella:                 # 窄概念不够时才回补，并标明来源
        if len(picks) >= n:
            break
        picks.append((c, "伞形回补", size))

    return {"picks": picks, "umbrella": umbrella, "sizes": sizes, "kept": keep}


def _members_from(r: Dict[str, Any]) -> tuple:
    """把一条查询结果转成 members 列表 + 缺字段告警。"""
    warnings: List[str] = list(r.get("notes") or [])
    keys = {out: pick(r, cn) for out, cn in MEMBER_FIELDS.items()}
    for out, cn in MEMBER_FIELDS.items():
        if keys[out] is None:
            warnings.append(f"问财未返回「{cn}」字段")

    members: List[Dict[str, Any]] = []
    for row in r["rows"]:
        m = {out: row.get(k) if k else None for out, k in keys.items()}
        for f in ("mktcap", "float_mktcap", "amount", "amplitude"):
            m[f] = to_num(m[f])
        members.append(m)
    return members, warnings


def _aggregate(members: List[Dict[str, Any]], warnings: List[str]) -> Dict[str, Any]:
    def _sum(field: str) -> tuple:
        vals = [m[field] for m in members if m[field] is not None]
        return (sum(vals) if vals else None), len(vals)

    total_mktcap, n_mkt = _sum("mktcap")
    float_mktcap, n_flt = _sum("float_mktcap")
    amount, n_amt = _sum("amount")
    for label, n in (("总市值", n_mkt), ("自由流通市值", n_flt), ("成交额", n_amt)):
        if n < len(members):
            warnings.append(f"{label}：{len(members) - n}/{len(members)} 只缺值，加总仅覆盖 {n} 只")
    return {"total_mktcap": total_mktcap, "float_mktcap": float_mktcap, "amount": amount}


MIN_RESOLVED = 0.9    # 解析率低于此，容量加总不予采信


def chunk_codes(codes: Sequence[str], tail: str, cap: int = MAX_QUESTION) -> List[List[str]]:
    """按**问句长度**切块，不是按个数。

    问财免费版 question 有 ~200 字符上限，25 个 6 位代码 + 指标尾巴就会超
    （实测 203 被拒，status_code=-9138）。按个数切会时灵时不灵。
    """
    budget = cap - len(tail) - 1
    out, cur, used = [], [], 0
    for c in codes:
        need = len(c) + (1 if cur else 0)
        if cur and used + need > budget:
            out.append(cur)
            cur, used = [c], len(c)
        else:
            cur.append(c)
            used += need
    if cur:
        out.append(cur)
    return out


def codes_capacity(s: WencaiSession, entries: Sequence[tuple], retry: int = 2) -> Dict[str, Any]:
    """给一份明确的标的清单（(简称, 代码) 对），算容量与当日 MIX。

    用于韭研公社这类人工梳理的产业链——成分是点名给出的，不是"概念股"筛出来的。

    按**代码**查而不是名字：名字里有"龙头股份""大叶股份"这种含修饰词的，
    有被问财当成筛选条件的风险；代码没有歧义。

    问财偶发会返回残缺响应（25 只只回 1 只），所以解析不全时重试；
    重试后仍不全就把 reliable 置 False——残缺的加总比没有数更危险。
    """
    members: List[Dict[str, Any]] = []
    warnings: List[str] = []
    resolved: set = set()

    by_code = {c: n for n, c in entries}
    for codes in chunk_codes([c for _n, c in entries], MEMBER_TAIL):
        chunk = [(by_code[c], c) for c in codes]
        want = set(codes)
        part: List[Dict[str, Any]] = []
        for attempt in range(retry + 1):
            # all_rows=False：块内 ≤ 100 只不会触发翻页，
            # 顺便省下" 按总市值从大到小排序"那 11 个字符的问句预算
            r = s.query(f"{' '.join(codes)} {MEMBER_TAIL}", all_rows=False)
            part, warn = _members_from(r)
            got = {str(m.get("code") or "").split(".")[0] for m in part}
            if len(got & want) >= len(want) * MIN_RESOLVED:
                warnings.extend(warn)
                break
            if attempt == retry:
                warnings.extend(warn)
                warnings.append(
                    f"这批 {len(want)} 只只解析出 {len(got & want)} 只，重试 {retry} 次仍不全")
        members.extend(part)
        resolved |= {str(m.get("code") or "").split(".")[0] for m in part}

    missing = [(n, c) for n, c in entries if c not in resolved]
    rate = 1 - len(missing) / len(entries) if entries else 0.0
    if missing:
        warnings.append(f"{len(missing)}/{len(entries)} 只未解析：{'、'.join(n for n, _c in missing[:8])}")

    return {
        "n_members": len(members),
        "n_requested": len(entries),
        "missing": missing,
        "resolve_rate": rate,
        "reliable": rate >= MIN_RESOLVED,
        "capacity": _aggregate(members, warnings),
        "mix_intraday_vol": mix_vol(members),
        "members": members,
        "warnings": warnings,
    }


def concept_capacity(s: WencaiSession, concept: str) -> Dict[str, Any]:
    """一个概念的可交易容量与当前日内波动。

    容量三个口径，从松到紧：
      total_mktcap   总市值加总          —— 名义盘子
      float_mktcap   自由流通市值加总     —— 真正能换手的部分，"可交易容量"看这个
      amount         当日成交额加总       —— 今天实际吃得下多少钱

    MIX 日内波动率：日振幅 =(当日最高-最低)/前收，问财原生字段。三个混合口径：
      median          等权中位数        —— 典型个股
      float_weighted  自由流通市值加权   —— 资金体感
      amount_weighted 成交额加权        —— 成交实际发生处
    """
    r = s.query(f"{subject_of(concept)} {MEMBER_TAIL}", all_rows=True, cursor_field="总市值")
    warnings: List[str] = list(r.get("notes") or [])

    keys = {out: pick(r, cn) for out, cn in MEMBER_FIELDS.items()}
    for out, cn in MEMBER_FIELDS.items():
        if keys[out] is None:
            warnings.append(f"问财未返回「{cn}」字段")

    members: List[Dict[str, Any]] = []
    for row in r["rows"]:
        m = {out: row.get(k) if k else None for out, k in keys.items()}
        for f in ("mktcap", "float_mktcap", "amount", "amplitude"):
            m[f] = to_num(m[f])
        members.append(m)

    def _sum(field: str) -> tuple:
        vals = [m[field] for m in members if m[field] is not None]
        return (sum(vals) if vals else None), len(vals)

    total_mktcap, n_mkt = _sum("mktcap")
    float_mktcap, n_flt = _sum("float_mktcap")
    amount, n_amt = _sum("amount")
    for label, n in (("总市值", n_mkt), ("自由流通市值", n_flt), ("成交额", n_amt)):
        if n < len(members):
            warnings.append(f"{label}：{len(members) - n}/{len(members)} 只缺值，加总仅覆盖 {n} 只")

    return {
        "concept": concept,
        "n_members": len(members),
        "n_declared": r.get("total"),
        "truncated": r.get("truncated", False),
        "capacity": {"total_mktcap": total_mktcap, "float_mktcap": float_mktcap, "amount": amount},
        "mix_intraday_vol": mix_vol(members),
        "members": members,
        "warnings": warnings,
    }


def mix_vol(members: Sequence[Dict[str, Any]], amp_field: str = "amplitude") -> Dict[str, Any]:
    """篮子的混合日内波动率。四个口径一起给，读数时自己选。"""
    amps = [(m[amp_field], m.get("float_mktcap"), m.get("amount"))
            for m in members if m.get(amp_field) is not None]
    if not amps:
        return {"median": None, "mean": None, "float_weighted": None,
                "amount_weighted": None, "n": 0}

    def _w(slot: int) -> Optional[float]:
        pairs = [(a, t[slot]) for t in amps for a in (t[0],) if t[slot]]
        tw = sum(w for _a, w in pairs)
        return sum(a * w for a, w in pairs) / tw if tw else None

    vals = [a for a, _f, _t in amps]
    return {
        "median": statistics.median(vals),
        "mean": statistics.fmean(vals),
        "float_weighted": _w(1),
        "amount_weighted": _w(2),
        "n": len(vals),
    }


def yi(x: Optional[float]) -> str:
    """元 → 亿元。None 明确显示为数据不可得。"""
    return "数据不可得" if x is None else f"{x / 1e8:,.0f}亿"


def pct(x: Optional[float]) -> str:
    return "数据不可得" if x is None else f"{x:.2f}%"
