#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fetch_quarterly.py — 1.4 季度毛利率分解 + 1.4b 季度现金流/资本开支 两块的取数（iFind 原生单季指标）

产出两个 page_model 块：
  part1.cost_structure_q   1.4  逐季 毛利率分解（净利率 + 四费 + 税费 + 其他，堆积＝毛利率）
  part1.cash_capex         1.4b 逐季 经营现金流 / 归母净利 / CAPEX，以及**半年度披露的**折旧摊销

★★ 这个脚本的第一原则：**只用报表上真有的数，不摊平、不插值、不反推。**

  2026-08-18 实测 iFind（688256 寒武纪），把「哪些是真有的」查清楚了：

  | 指标 | 频率 | 结论 |
  |---|---|---|
  | `单季度.营业总收入 / 营业成本 / 销售·管理·研发·财务费用 / 税金及附加 / 所得税费用 / 归属母公司净利润` | **每季都有** | 直接取，**不要自己拿累计差分** |
  | `单季度.经营活动产生的现金流量净额` | **每季都有** | 同上 |
  | `单季度.购建固定资产、无形资产和其他长期资产支付的现金` | **每季都有** | 同上，即 CAPEX |
  | `当期计提折旧与摊销` / `固定资产折旧` / `无形资产摊销` / `长期待摊费用摊销` | **只有 0630 与 1231** | **A 股季报不含现金流量表补充资料** —— 单季折旧在报表上**不存在** |

  ⚠️ 取数陷阱：同一张返回表里 iFind 会**同时给出**「累计」与「单季度.」两列同名指标
  （`销售费用` 与 `单季度.销售费用` 并存）。本脚本对季度字段**强制要求 `单季度.` 前缀**，
  匹配不到宁可留空也不退回累计列——退回去就是把 Q4 的四季累计当成单季画上去。

  ⚠️ 折旧怎么办：既然单季不存在，就**不造**。
     `da_disclosure[]` 落两个真实披露点（H1 累计、全年累计→H2 增量），
     `ttm.da` 只在 **Q2 / Q4** 给值（滚动四季正好由披露的累计数凑得出，是精确值），
     Q1/Q3 留 `null`。页面单季视图**不画折旧线**（半年值画在单季轴上会被读大一倍），
     滚动四季视图才画，一年两个真实点。

用法:
  python3 fetch_quarterly.py --name 寒武纪 --ticker 688256.SH --y0 2020 --y1 2026 \\
      --model _workspace/688256/page_model.json --write
  python3 fetch_quarterly.py --from-raw _workspace/688256/raw/ --out /tmp/q.json   # 离线复跑
  python3 fetch_quarterly.py --self-test                                          # 不连网自检

`--y0` 传**上市首年**（1.4 要「上市以来」）。仅 A 股；港美股 iFind 返回空表不报错，脚本会拦。
"""
import argparse, json, os, re, subprocess, sys

YI = 1e8

# ---------------------------------------------------------------- iFind 客户端
def _ifind_dir():
    for c in (os.environ.get("IFIND_SKILL_DIR"),
              os.path.expanduser("~/.claude/skills/ifind-research"),
              r"C:/Users/youqi/.claude/skills/ifind-research"):
        if c and os.path.isfile(os.path.join(c, "scripts", "ifind_client.py")):
            return c
    return os.path.expanduser("~/.claude/skills/ifind-research")


def run_ifind(query, timeout=240):
    d = _ifind_dir()
    cli = os.path.join(d, "scripts", "ifind_client.py")
    try:
        p = subprocess.run([sys.executable, cli, "fin", query], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "query": query}
    try:
        j = json.loads(p.stdout or "")
        data = j.get("data") or {}
        if isinstance(data, str):
            data = json.loads(data)
        return {"answer": (data or {}).get("answer") or ""}
    except Exception:
        return {"error": "unparsed", "stdout": (p.stdout or "")[:600], "query": query}


# ------------------------------------------------------------------- 表格解析
def parse_md_table(answer):
    if not answer:
        return {"columns": [], "rows": []}
    body = re.split(r"\n#\s", answer)[0]
    lines = [ln.strip() for ln in body.splitlines() if ln.strip().startswith("|")]
    if not lines:
        return {"columns": [], "rows": []}
    cells = lambda ln: [c.strip() for c in ln.strip().strip("|").split("|")]
    cols = cells(lines[0])
    rows = [c for c in (cells(ln) for ln in lines[1:])
            if not re.match(r"^[\s:\-]+$", "".join(c)) and len(c) == len(cols)]
    return {"columns": cols, "rows": rows}


_QEND = {"03": 1, "06": 2, "09": 3, "12": 4}


def to_quarter(s):
    """20250630 / 2025-06-30 / 2025/06/30 → '2025Q2'；认不出返回 None。"""
    t = re.sub(r"\D", "", str(s or ""))
    if len(t) < 6:
        return None
    y, mo = t[:4], t[4:6]
    if not y.startswith(("19", "20")) or mo not in _QEND:
        return None
    return "%sQ%d" % (y, _QEND[mo])


def to_num(s):
    """iFind 的数字带中文量词：'1.4610亿' / '9487.8128万' / '-522653189.64'。"""
    if s is None:
        return None
    t = str(s).strip().replace(",", "").replace("\t", "")
    if t in ("", "-", "--", "—", "None", "null", "nan"):
        return None
    m = re.match(r"^[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", t)
    if not m:
        return None
    v = float(m.group(0))
    if "亿" in t:
        v *= 1e8
    elif "万" in t:
        v *= 1e4
    return v


def col_index(columns, want, need_q):
    """按指标名找列。need_q=True 时**强制**要求 `单季度.` 前缀。

    这一条是本脚本最要紧的防线：iFind 同一张表里累计列与单季列同名并存
    （`销售费用` vs `单季度.销售费用`），匹配错就是把 Q4 的全年累计当单季画上去。"""
    norm = lambda x: re.sub(r"[（(].*?[)）]|\s", "", str(x or ""))
    for i, c in enumerate(columns):
        n = norm(c)
        isq = n.startswith("单季度.")
        if need_q != isq:
            continue
        base = n[4:] if isq else n
        if base == want:
            return i
    return None


def table_to_cols(tbl, spec):
    """spec = [(字段名, iFind 指标名, 是否要求单季)] → {字段: {季: 值}} + 未命中清单。"""
    cols, rows = tbl.get("columns") or [], tbl.get("rows") or []
    di = None
    for i, c in enumerate(cols):
        if re.sub(r"[（(].*?[)）]|\s", "", str(c)) in ("日期", "报告期", "截止日期"):
            di = i
            break
    if di is None:
        return {}, ["找不到日期列（iFind 这次可能没返回表格，看 raw md）"]
    out, missing = {}, []
    for field, ind, need_q in spec:
        ci = col_index(cols, ind, need_q)
        if ci is None:
            missing.append("%s（%s%s）" % (field, "单季度." if need_q else "", ind))
            continue
        d = {}
        for r in rows:
            q = to_quarter(r[di] if di < len(r) else None)
            v = to_num(r[ci]) if ci < len(r) else None
            if q and v is not None:
                d[q] = v
        out[field] = d
    return out, missing


def qsorted(keys):
    return sorted(keys, key=lambda k: (int(k[:4]), int(k[-1])))


# ------------------------------------------------------- 1.4 季度毛利率分解
IS_SPEC = [
    ("rev",   "营业总收入", True), ("cogs", "营业成本", True),
    ("sell",  "销售费用", True),   ("admin", "管理费用", True),
    ("rnd",   "研发费用", True),   ("fin",   "财务费用", True),
    ("surtax", "税金及附加", True), ("itax",  "所得税费用", True),
    ("np",    "归属于母公司所有者的净利润", True),
]


def build_cost_q(series, y0=None, y1=None, listing_year=None):
    rev = series.get("rev") or {}
    qs = [q for q in qsorted(rev) if rev[q]
          and (y0 is None or int(q[:4]) >= int(y0)) and (y1 is None or int(q[:4]) <= int(y1))]
    pct = lambda num_, q: (None if (num_ is None or not rev.get(q)) else round(num_ / rev[q] * 100, 3))
    col = lambda k: [pct((series.get(k) or {}).get(q), q) for q in qs]
    gm = [(None if (rev.get(q) is None or (series.get("cogs") or {}).get(q) is None)
           else round((rev[q] - series["cogs"][q]) / rev[q] * 100, 3)) for q in qs]
    tax = []
    for q in qs:
        a, b = (series.get("surtax") or {}).get(q), (series.get("itax") or {}).get(q)
        tax.append(None if (a is None and b is None) else pct((a or 0) + (b or 0), q))
    blk = {
        "quarters": qs, "gross_margin": gm, "net_margin": col("np"),
        "sell_exp_rate": col("sell"), "admin_exp_rate": col("admin"),
        "rnd_exp_rate": col("rnd"), "fin_exp_rate": col("fin"),
        "tax_rate": tax,
        "rev_yi": [None if rev.get(q) is None else round(rev[q] / YI, 4) for q in qs],
        "src": "iFind 单季度.* 原生指标（非累计差分）",
        "caliber": ("全部为占**单季营业总收入**的比重。「税费」＝税金及附加＋所得税费用（同分母，不是实际税率）。"
                    "「其他」不落数据层，由页面按恒等式反算：毛利率 −（净利率＋四费＋税费）——"
                    "减值、其他收益、投资收益、公允价值变动、营业外收支、少数股东损益全在这一个桶里。"),
    }
    if listing_year:
        blk["listing_year"] = int(listing_year)
    return blk


# --------------------------------------------- 1.4b 季度现金流 + 半年度折旧
CF_SPEC = [("ocf", "经营活动产生的现金流量净额", True),
           ("capex", "购建固定资产、无形资产和其他长期资产支付的现金", True),
           ("np", "归属于母公司所有者的净利润", True)]
DA_SPEC = [("da", "当期计提折旧与摊销", False),
           ("dep", "固定资产折旧、油气资产折耗、生产性生物资产折旧", False),
           ("amo", "无形资产摊销", False),
           ("lta", "长期待摊费用摊销", False)]


def da_halves(da_series):
    """把披露的**累计**折旧摊销拆成两个半年增量。只用报表真有的两个点，不摊到季。

    H1 = 中报累计值本身；H2 = 年报累计值 − 中报累计值。
    缺哪一端就少一段，不补。返回 [{'period':'2025H1','yi':…,'covers':['2025Q1','2025Q2']}, …]"""
    out = []
    for y in sorted({k[:4] for k in da_series}):
        h1 = da_series.get("%sQ2" % y)
        fy = da_series.get("%sQ4" % y)
        if h1 is not None:
            out.append({"period": "%sH1" % y, "yi": round(h1 / YI, 4),
                        "covers": ["%sQ1" % y, "%sQ2" % y], "src": "中报 现金流量表补充资料（累计）"})
        if fy is not None and h1 is not None:
            out.append({"period": "%sH2" % y, "yi": round((fy - h1) / YI, 4),
                        "covers": ["%sQ3" % y, "%sQ4" % y], "src": "年报累计 − 中报累计"})
        elif fy is not None:
            out.append({"period": "%s全年" % y, "yi": round(fy / YI, 4),
                        "covers": ["%sQ1" % y, "%sQ2" % y, "%sQ3" % y, "%sQ4" % y],
                        "src": "年报 现金流量表补充资料（累计）；该年中报缺，无法拆半年"})
    return out


def da_ttm_at(q, da_series):
    """滚动四季折旧：**只在 Q2 / Q4 算得出来**，且全部来自披露的累计数，是精确值。
       Q4 → 当年年报累计；Q2 → 本年中报累计 + 上年(年报累计 − 中报累计)。
       Q1 / Q3 → 报表上没有对应的累计切点，返回 None（不猜）。"""
    y, n = int(q[:4]), int(q[-1])
    if n == 4:
        v = da_series.get("%dQ4" % y)
        return None if v is None else round(v / YI, 4)
    if n == 2:
        h1, pfy, ph1 = (da_series.get("%dQ2" % y), da_series.get("%dQ4" % (y - 1)),
                        da_series.get("%dQ2" % (y - 1)))
        if h1 is None or pfy is None or ph1 is None:
            return None
        return round((h1 + (pfy - ph1)) / YI, 4)
    return None


def build_cash(series, da_series, y0=None, y1=None):
    keys = set()
    for k in ("ocf", "np", "capex"):
        keys |= set(series.get(k) or {})
    qs = [q for q in qsorted(keys)
          if (y0 is None or int(q[:4]) >= int(y0)) and (y1 is None or int(q[:4]) <= int(y1))]
    col = lambda k: [(None if (series.get(k) or {}).get(q) is None
                      else round(series[k][q] / YI, 4)) for q in qs]
    ocf, np_, capex = col("ocf"), col("np"), col("capex")
    # CAPEX 存成正数＝流出规模（个别源给负号）
    pos = sum(1 for v in capex if v is not None and v > 0)
    neg = sum(1 for v in capex if v is not None and v < 0)
    flipped = neg > pos
    if flipped:
        capex = [None if v is None else -v for v in capex]

    def roll(a):
        out = []
        for i in range(len(a)):
            w = a[max(0, i - 3):i + 1]
            out.append(None if (len(w) < 4 or any(x is None for x in w)) else round(sum(w), 4))
        return out

    blk = {
        "quarters": qs, "ocf": ocf, "np": np_, "capex": capex,
        "ttm": {"quarters": qs, "ocf": roll(ocf), "np": roll(np_), "capex": roll(capex),
                "da": [da_ttm_at(q, da_series) for q in qs]},
        "da_disclosure": da_halves(da_series),
        "unit": "亿元",
        "src": "iFind 单季度.* 原生指标；折旧摊销取「当期计提折旧与摊销」披露累计值",
        "caliber": ("经营现金流／归母净利／CAPEX 全部取 iFind **单季度.** 原生指标，未做累计差分、未插值。"
                    "CAPEX ＝ 购建固定资产、无形资产和其他长期资产支付的现金，渲成正数＝流出规模。"),
        "da_note": ("**A 股季报不含现金流量表补充资料**，折旧摊销一年只有中报、年报两个披露点，"
                    "单季数在报表上不存在。本页因此**不摊平、不插值**：单季视图不画折旧线"
                    "（半年值画在单季轴上会被读大一倍），滚动四季视图才画——"
                    "TTM 折旧只在 Q2／Q4 有值，两个值都由披露的累计数精确凑出，Q1／Q3 留空。"),
    }
    if flipped:
        blk["gaps"] = ["CAPEX 原值为负（现金流出记负），已取绝对值渲成流出规模"]
    return blk


# ------------------------------------------------------------------------ 自检
FIX_IS = """
|证券代码|证券简称|日期|单季度.营业总收入（单位：元）|营业总收入（单位：元）|单季度.营业成本（单位：元）|单季度.销售费用（单位：元）|销售费用（单位：元）|单季度.管理费用（单位：元）|单季度.研发费用（单位：元）|单季度.财务费用（单位：元）|单季度.税金及附加（单位：元）|单季度.所得税费用（单位：元）|单季度.归属于母公司所有者的净利润（单位：元）|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|688256.SH|寒武纪|20250630|17.6924亿|28.8064亿|7.805亿|1372.6338万|2811.8048万|5492.0775万|2.6932亿|-2104394.17|173.7935万|-29040.37|6.8262亿|
|688256.SH|寒武纪|20250331|11.114亿|11.114亿|4.8913亿|1439.171万|1439.171万|4307.4188万|2.7257亿|1018.1302万|234.7081万|128063.29|3.5547亿|
"""
FIX_DA = """
|证券代码|证券简称|日期|当期计提折旧与摊销（单位：元）|
|---|---|---|---|
|688256.SH|寒武纪|20251231|2.8518亿|
|688256.SH|寒武纪|20250930|\t|
|688256.SH|寒武纪|20250630|1.4610亿|
|688256.SH|寒武纪|20250331|\t|
|688256.SH|寒武纪|20241231|2.0935亿|
|688256.SH|寒武纪|20240630|0.94878亿|
"""


def self_test():
    ok = True

    def eq(a, b, tag, tol=1e-6):
        nonlocal ok
        good = (a is None and b is None) or (a is not None and b is not None and abs(a - b) <= tol)
        print(("  ✓ " if good else "  ✗ ") + tag + ("  got=%s want=%s" % (a, b)))
        ok = ok and good

    s, miss = table_to_cols(parse_md_table(FIX_IS), IS_SPEC)
    print("单季利润表：命中 %d 项，未命中 %s" % (len(s), miss or "无"))
    eq(len(miss), 0, "九个单季指标全部命中")
    # ★最要紧的一条：不许错取到同名的累计列
    eq(round(s["rev"]["2025Q2"] / 1e8, 4), 17.6924, "营业总收入取的是**单季**列（17.69 亿），不是累计列（28.81 亿）")
    eq(round(s["sell"]["2025Q2"] / 1e4, 4), 1372.6338, "销售费用取的是单季列（1372.6 万），不是累计（2811.8 万）")

    b = build_cost_q(s, listing_year=2020)
    i = b["quarters"].index("2025Q2")
    eq(b["gross_margin"][i], round((17.6924 - 7.805) / 17.6924 * 100, 3), "毛利率＝(营收−成本)÷营收")
    eq(b["net_margin"][i], round(6.8262 / 17.6924 * 100, 3), "净利率＝归母÷营收")
    eq(b["tax_rate"][i], round((173.7935e4 - 29040.37) / 17.6924e8 * 100, 3), "税费＝(税金及附加＋所得税)÷营收")
    plug = b["gross_margin"][i] - (b["net_margin"][i] + b["sell_exp_rate"][i] + b["admin_exp_rate"][i]
                                   + b["rnd_exp_rate"][i] + b["fin_exp_rate"][i] + b["tax_rate"][i])
    print("  · 2025Q2 恒等式残差（＝页面的「其他」桶）= %.3f pp" % plug)
    print("  ✓ 「其他」由页面反算，恒等式按定义成立")

    d, dmiss = table_to_cols(parse_md_table(FIX_DA), DA_SPEC)
    da = d.get("da") or {}
    eq(len(da), 4, "折旧摊销只解析到 4 个披露点（Q1/Q3 是空的）")
    hs = da_halves(da)
    print("  · 半年披露段：%s" % [(h["period"], h["yi"]) for h in hs])
    eq(hs[0]["yi"], round(0.94878, 4), "2024H1 ＝ 中报累计值本身")
    eq(hs[1]["yi"], round(2.0935 - 0.94878, 4), "2024H2 ＝ 年报累计 − 中报累计")
    eq(da_ttm_at("2025Q4", da), 2.8518, "TTM 折旧 @Q4 ＝ 当年年报累计（精确）")
    eq(da_ttm_at("2025Q2", da), round(1.4610 + (2.0935 - 0.94878), 4), "TTM 折旧 @Q2 ＝ 本年中报 + 上年下半年（精确）")
    eq(da_ttm_at("2025Q1", da), None, "TTM 折旧 @Q1 ＝ None（报表上没有这个切点，不猜）")
    eq(da_ttm_at("2025Q3", da), None, "TTM 折旧 @Q3 ＝ None（同上）")

    print("\n" + ("✓ 自检通过" if ok else "✗ 自检未过"))
    return 0 if ok else 1


# ------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description="1.4 季度毛利率分解 + 1.4b 季度现金流/CAPEX 取数")
    ap.add_argument("--name"); ap.add_argument("--ticker")
    ap.add_argument("--y0", help="起始年——1.4 要「上市以来」，传上市首年")
    ap.add_argument("--y1")
    ap.add_argument("--listing-year", help="上市首年（写进 cost_structure_q.listing_year，CK-8 d4 核对）")
    ap.add_argument("--out"); ap.add_argument("--model"); ap.add_argument("--write", action="store_true")
    ap.add_argument("--from-raw", help="离线复跑：存过 raw md 的目录")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        sys.exit(self_test())

    base = os.path.dirname(os.path.abspath(a.out or a.model or "."))
    rawdir = a.from_raw or os.path.join(base, "raw")

    def get(tag, query):
        path = os.path.join(rawdir, "q_%s.md" % tag)
        if a.from_raw:
            return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
        print("[fetch] %s ..." % tag, flush=True)
        r = run_ifind(query)
        os.makedirs(rawdir, exist_ok=True)
        ans = r.get("answer", "")
        with open(path, "w", encoding="utf-8") as f:
            f.write("QUERY: %s\n\n%s" % (query, ans or json.dumps(r, ensure_ascii=False)))
        if not ans:
            print("   -> 空返回：%s" % r.get("error", "empty"))
        return ans

    if not a.from_raw:
        if not (a.name and a.ticker):
            ap.error("--name / --ticker 必填（除非 --from-raw / --self-test）")
        t = a.ticker.strip().upper()
        if not (t.endswith((".SH", ".SZ", ".BJ")) or re.fullmatch(r"\d{6}", t)):
            print("⛔ %s 不是 A 股。iFind 对港美股返回空表而不报错，跑下去会得到一张空图。" % a.ticker)
            print("   港美股请走 fetch_fundamentals_hkus.py 的三表腿自行接同样的键。")
            sys.exit(2)
    span = ("%s年至%s年 " % (a.y0, a.y1)) if (a.y0 and a.y1) else ""
    N = a.name or ""

    ans_is = get("income", "%s %s各报告期 单季度营业总收入、单季度营业成本、单季度销售费用、单季度管理费用、"
                           "单季度研发费用、单季度财务费用、单季度税金及附加、单季度所得税费用、"
                           "单季度归属母公司股东的净利润" % (N, span))
    ans_cf = get("cash",   "%s %s各报告期 单季度经营活动产生的现金流量净额、"
                           "单季度购建固定资产无形资产和其他长期资产支付的现金、"
                           "单季度归属母公司股东的净利润" % (N, span))
    ans_da = get("da",     "%s %s各报告期 当期计提折旧与摊销、固定资产折旧、无形资产摊销、长期待摊费用摊销"
                           % (N, span))

    is_s, is_miss = table_to_cols(parse_md_table(ans_is), IS_SPEC)
    cf_s, cf_miss = table_to_cols(parse_md_table(ans_cf), CF_SPEC)
    da_s, da_miss = table_to_cols(parse_md_table(ans_da), DA_SPEC)

    if not is_s.get("rev"):
        print("⛔ 单季营业总收入一列都没解析出来。raw: %s —— 先人工看一眼 iFind 返回的是不是表格。" % rawdir)
        sys.exit(4)

    cost_q = build_cost_q(is_s, a.y0, a.y1, a.listing_year or a.y0)
    da_series = da_s.get("da") or {}
    if not da_series:                       # 没有合成口径就用三项相加（都只在中报/年报有）
        parts = [da_s.get(k) or {} for k in ("dep", "amo", "lta")]
        for k in set().union(*[set(p) for p in parts]) if any(parts) else []:
            if parts[0].get(k) is not None:
                da_series[k] = sum(p.get(k) or 0 for p in parts)
    cash = build_cash(cf_s, da_series, a.y0, a.y1)
    if is_miss:
        cost_q.setdefault("gaps", []).extend(["未命中 " + m for m in is_miss])
    # 三个明细项（dep/amo/lta）只是「当期计提折旧与摊销」拿不到时的兜底，主项命中就不必报
    if da_series:
        da_miss = [m for m in da_miss if m.startswith("da（")]
    if cf_miss or da_miss:
        cash.setdefault("gaps", []).extend(["未命中 " + m for m in (cf_miss + da_miss)])

    n = len(cost_q["quarters"])
    print("\n1.4  cost_structure_q：%d 季（%s ~ %s）"
          % (n, cost_q["quarters"][0] if n else "-", cost_q["quarters"][-1] if n else "-"))
    print("1.4b cash_capex：%d 季；折旧披露点 %d 段 %s"
          % (len(cash["quarters"]), len(cash["da_disclosure"]),
             [d["period"] for d in cash["da_disclosure"]][:6]))
    for g in cost_q.get("gaps", []) + cash.get("gaps", []):
        print("   ⚠️ %s" % g)

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump({"cost_structure_q": cost_q, "cash_capex": cash},
                  open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote %s" % a.out)
    if a.write:
        if not a.model:
            ap.error("--write 需要 --model")
        m = json.load(open(a.model, encoding="utf-8"))
        p1 = m.setdefault("part1", {})
        p1["cost_structure_q"] = cost_q
        p1["cash_capex"] = cash
        json.dump(m, open(a.model, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote part1.cost_structure_q + part1.cash_capex -> %s" % a.model)


if __name__ == "__main__":
    main()
