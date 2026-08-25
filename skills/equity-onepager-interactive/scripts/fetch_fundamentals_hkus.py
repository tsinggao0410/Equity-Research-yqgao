#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fetch_fundamentals_hkus.py — 港股/美股 Part1 取数（iFind 不解析港美股，本脚本是其替身）
==============================================================================
为什么存在：`fetch_ifind.py` 的 fin/holders 只认 A 股，喂港美股会返回「查询结果为空」
且**不报错**（六张表全空，只在末尾打 ⚠️ gaps）。本脚本走东财港美股财报接口 + SEC EDGAR，
把 Part1 能拿的都拿到，拿不到的**显式列进 gaps**，不让缺口静默通过。

  美股：东财三表(2000起) + 分析指标(杜邦四项齐) + SEC EDGAR R-file 分部(产品线/报告分部)
  港股：东财三表(2001起) + 分析指标(9年,周转率需推导) + etnet 一致预期 + 估值/规模比较
        —— **分部收入无结构化源**，只能年报PDF/纪要手抄（gaps 里会写明）

用法:
  python scripts/fetch_fundamentals_hkus.py --ticker AAPL  --market US --y0 2016 --y1 2025 \
      --out _workspace/AAPL/fundamentals.json
  python scripts/fetch_fundamentals_hkus.py --ticker 00700 --market HK --y0 2016 --y1 2025 \
      --out _workspace/00700/fundamentals.json

产出 JSON（供 Phase2 人工映射进 page_model.part1 / meta，口径与 A 股线一致）:
  meta{name,currency,unit,shares_yi,price,mcap_yi,pe_ttm,currency_check}
  tables{income,balance,cashflow,indicators,dupont,cost_structure,revenue,consensus,profile,pe_history}
  gaps[]      ← **必读**：缺什么 + 建议补法（派系图/股权树/分部等）
  sources{}   ← 每表来源与 as-of

金额口径：绝对额一律给 `*_yi`＝**当地币种亿元**（美股=亿美元，港股财报币种见 meta.currency）。
⚠️ 本脚本不做汇率换算——page_model 若要统一成人民币亿元，在 Phase2 显式乘 fx 并记进 meta.fx。
"""
import argparse, datetime as dt, html, json, os, re, sys, urllib.request

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)

SEC_UA = os.environ.get("SEC_UA", "equity-onepager research@example.com")
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


# ---------------------------------------------------------------- 小工具
def _num(x):
    """'$ 416,161' / '(220,960)' / '12.3亿' → float；不可解析返回 None"""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return None if x != x else float(x)          # NaN → None
    s = str(x).strip().replace(",", "").replace("$", "").replace("%", "").strip()
    if s in ("", "-", "--", "—", "nan", "None"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    mult = 1.0
    if s.endswith("亿"):
        s, mult = s[:-1], 1e8
    elif s.endswith("万"):
        s, mult = s[:-1], 1e4
    try:
        v = float(s) * mult
    except ValueError:
        return None
    return -v if neg else v


def _yi(v):
    return None if v is None else round(v / 1e8, 4)


def _http(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": SEC_UA,
                                               "Accept-Encoding": "gzip, deflate"})
    raw = _OPENER.open(req, timeout=timeout).read()
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw)
    return raw


def _ak():
    import akshare as ak
    return ak


def _try(label, fn, gaps, sources, *a, **kw):
    """跑一个取数动作；失败不中断，记进 gaps。"""
    try:
        r = fn(*a, **kw)
        if r is None or (hasattr(r, "empty") and r.empty):
            gaps.append("%s：接口返回空" % label)
            return None
        sources[label] = kw.pop("_src", label)
        return r
    except Exception as e:
        gaps.append("%s：%s: %s" % (label, type(e).__name__, str(e)[:120]))
        return None


# ---------------------------------------------------------------- 三表：长表 → 透视
def pivot_long(df, period_col, item_col, amount_col, years=None):
    """东财长表(每行一个科目一个报告期) → {periods:[新→旧], items:{科目:{期:值}}}"""
    periods, items = [], {}
    for _, r in df.iterrows():
        p = str(r[period_col])[:10]
        if years and not (years[0] <= p[:4] <= years[1]):
            continue
        it = str(r[item_col]).strip()
        v = _num(r[amount_col])
        if p not in periods:
            periods.append(p)
        items.setdefault(it, {})[p] = v
    periods = sorted(set(periods), reverse=True)
    return {"periods": periods, "items": items}


def series(piv, names, periods):
    """按科目别名列表取一条时间序列（按 periods 顺序）；返回 (values, 命中的科目名)。
    ⚠️ 跳过「在 periods 区间内全为空」的候选——东财会保留公司早年才披露的科目名，
    直接命中它会得到一列 None 且**不报错**（实测 AAPL 的『其他营业费用』2021 年后消失）。"""
    for n in names:
        if n in piv["items"]:
            vals = [piv["items"][n].get(p) for p in periods]
            if any(v is not None for v in vals):
                return vals, n
    return [None] * len(periods), None


def add_series(a, b):
    """两条序列逐期相加，None 视作缺省；两边都 None 则保持 None"""
    out = []
    for x, y in zip(a, b):
        out.append(None if (x is None and y is None) else (x or 0) + (y or 0))
    return out


# ---------------------------------------------------------------- 美股：东财
def fetch_us(ticker, years, gaps, sources):
    ak = _ak()
    out = {}
    for key, sym in (("income", "综合损益表"), ("balance", "资产负债表"), ("cashflow", "现金流量表")):
        df = _try("US 三表-%s" % sym, ak.stock_financial_us_report_em, gaps, sources,
                  stock=ticker, symbol=sym, indicator="年报")
        if df is not None:
            out[key] = pivot_long(df, "REPORT_DATE", "ITEM_NAME", "AMOUNT", years)
            out[key]["source"] = "东财 stock_financial_us_report_em(%s,年报)" % sym
    ind = _try("US 分析指标", ak.stock_financial_us_analysis_indicator_em, gaps, sources,
               symbol=ticker, indicator="年报")
    if ind is not None:
        out["indicators"] = wide_indicators(ind, "REPORT_DATE", years,
                                            "东财 stock_financial_us_analysis_indicator_em(年报)")
    return out


# ---------------------------------------------------------------- 港股：东财 + etnet
def fetch_hk(ticker, years, gaps, sources):
    ak = _ak()
    t = ticker.zfill(5)
    out = {}
    for key, sym in (("income", "利润表"), ("balance", "资产负债表"), ("cashflow", "现金流量表")):
        df = _try("HK 三表-%s" % sym, ak.stock_financial_hk_report_em, gaps, sources,
                  stock=t, symbol=sym, indicator="年度")
        if df is not None:
            out[key] = pivot_long(df, "REPORT_DATE", "STD_ITEM_NAME", "AMOUNT", years)
            out[key]["source"] = "东财 stock_financial_hk_report_em(%s,年度)" % sym
    ind = _try("HK 分析指标", ak.stock_financial_hk_analysis_indicator_em, gaps, sources,
               symbol=t, indicator="年度")
    if ind is not None:
        out["indicators"] = wide_indicators(ind, "REPORT_DATE", years,
                                            "东财 stock_financial_hk_analysis_indicator_em(年度)")
    # 一致预期（etnet；A 股线里没有的额外锚：给 Forward 算账用，含最高/最低=分歧区间）
    for ind_name in ("盈利预测概览", "综合盈利预测"):
        fc = _try("HK 一致预期(%s)" % ind_name, ak.stock_hk_profit_forecast_et, gaps, sources,
                  symbol=t, indicator=ind_name)
        if fc is not None:
            cols = list(fc.columns)
            rows = fc.astype(object).where(fc.notna(), None).values.tolist()
            out["consensus"] = {"source": "etnet stock_hk_profit_forecast_et(%s)" % ind_name,
                                "columns": cols, "rows": rows,
                                "dispersion": consensus_dispersion(cols, rows)}
            break
    # 估值/规模（口径要自己对，见 currency_check）
    val = _try("HK 估值比较", ak.stock_hk_valuation_comparison_em, gaps, sources, symbol=t)
    if val is not None and len(val):
        out["valuation_cmp"] = {"source": "东财 stock_hk_valuation_comparison_em",
                                "row": {c: (None if val.iloc[0][c] != val.iloc[0][c] else val.iloc[0][c])
                                        for c in val.columns}}
    sc = _try("HK 规模比较", ak.stock_hk_scale_comparison_em, gaps, sources, symbol=t)
    if sc is not None and len(sc):
        out["scale_cmp"] = {"source": "东财 stock_hk_scale_comparison_em",
                            "row": {c: (None if sc.iloc[0][c] != sc.iloc[0][c] else sc.iloc[0][c])
                                    for c in sc.columns},
                            "warn": "实测该表『营业总收入』可能是单季而非年度、『总市值』与 收盘价×股本 对不上 → 只当参考,勿直接当锚"}
    prof = _try("HK 公司概况", ak.stock_hk_company_profile_em, gaps, sources, symbol=t)
    if prof is not None and len(prof):
        out["profile"] = {c: str(prof.iloc[0][c])[:400] for c in prof.columns}
    pe = _try("HK PE历史(亿牛)", ak.stock_hk_indicator_eniu, gaps, sources,
              symbol="hk" + t, indicator="市盈率")
    if pe is not None and len(pe):
        rows = [[str(r["date"])[:10], _num(r["pe"])] for _, r in pe.iterrows()]
        stale_yrs = dt.date.today().year - int(rows[-1][0][:4])
        note = "Part2 估值锚可用：现值在历史分位"
        if stale_yrs >= 2:
            note = ("⚠️ **序列停更在 %s（滞后约 %d 年）**，不能用来算『当前 PE 处于历史分位』；"
                    "只可用作更早年份的区间参照，现值分位改用 valuation_cmp 的 PE-TTM + 自算 PE 交叉定位"
                    % (rows[-1][0], stale_yrs))
            gaps.append("港股 PE 历史(亿牛)停更在 %s → 历史分位类结论不得用它算" % rows[-1][0])
        out["pe_history"] = {"source": "亿牛 stock_hk_indicator_eniu(市盈率)",
                             "n": len(rows), "from": rows[0][0], "to": rows[-1][0],
                             "stale_years": stale_yrs, "quantile_note": note,
                             "daily": rows[-1500:]}
    return out


def consensus_dispersion(cols, rows):
    """etnet 逐家机构预测 → 按财政年度算分歧度（家数/极差/中位/形态）。
    这是第四章 `dispersion_basis` 的现成原料——港股在这一格反而比 A 股好取
    （A 股要靠 RAG/AlphaPai 逐条挖，这里接口直接给逐家数字+机构名+更新日期）。"""
    def col(name):
        return cols.index(name) if name in cols else None
    iy, ip, it = col("财政年度"), col("纯利/亏损"), col("目标价")
    if iy is None:
        return None
    out = {}
    for r in rows:
        y = str(r[iy])
        for label, i in (("纯利", ip), ("目标价", it)):
            if i is None or r[i] is None:
                continue
            v = _num(r[i])
            if v is None:
                continue
            out.setdefault(y, {}).setdefault(label, []).append(v)
    summary = {}
    for y, d in sorted(out.items()):
        summary[y] = {}
        for label, vals in d.items():
            vals = sorted(vals)
            n, lo, hi = len(vals), vals[0], vals[-1]
            med = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
            summary[y][label] = {
                "n": n, "min": lo, "max": hi, "median": med,
                "spread_pct": round((hi / lo - 1) * 100, 1) if lo else None,
                "shape_hint": "极差>50%→查是否双峰(把 rows 逐条列进 dispersion_basis)"
                              if lo and hi / lo > 1.5 else "单峰窄"}
    return summary


def wide_indicators(df, period_col, years, src):
    """分析指标宽表 → {periods:[新→旧], cols:{字段:{期:值}}}"""
    keep = [c for c in df.columns if c not in
            ("SECUCODE", "SECURITY_CODE", "SECURITY_NAME_ABBR", "ORG_CODE",
             "SECURITY_INNER_CODE", "ORGTYPE")]
    periods, cols = [], {}
    for _, r in df.iterrows():
        p = str(r[period_col])[:10]
        if years and not (years[0] <= p[:4] <= years[1]):
            continue
        if p not in periods:
            periods.append(p)
        for c in keep:
            v = r[c]
            cols.setdefault(c, {})[p] = (_num(v) if not isinstance(v, str) or _num(v) is not None
                                         else str(v))
    periods = sorted(set(periods), reverse=True)
    return {"periods": periods, "cols": cols, "source": src}


# ---------------------------------------------------------------- SEC EDGAR 分部
def sec_cik(ticker):
    j = json.loads(_http("https://www.sec.gov/files/company_tickers.json"))
    for v in j.values():
        if v["ticker"].upper() == ticker.upper():
            return str(v["cik_str"]).zfill(10), v["title"]
    raise RuntimeError("SEC 无此 ticker: %s" % ticker)


def _rfile_rows(url):
    h = _http(url).decode("utf-8", errors="ignore")
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).replace("\xa0", " ").strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        cells = [c for c in cells if c != ""]
        if cells:
            rows.append(cells)
    return rows


_MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def _parse_date(s):
    m = re.match(r"([A-Z][a-z]{2})\.?\s+(\d{1,2}),\s*(\d{4})", s.strip())
    if not m:
        return None
    return "%s-%02d-%02d" % (m.group(3), _MONTHS[m.group(1)], int(m.group(2)))


def parse_segment_table(rows):
    """R-file 表 → {member: {period: value}}；单元格行=成员上下文, 多元格行=科目+数值"""
    unit_mult = 1.0
    if rows and re.search(r"\$ in Millions", rows[0][0], re.I):
        unit_mult = 1e6
    elif rows and re.search(r"\$ in Thousands", rows[0][0], re.I):
        unit_mult = 1e3
    periods = []
    for r in rows[:4]:
        ds = [_parse_date(c) for c in r]
        if sum(1 for d in ds if d) >= 2:
            periods = [d for d in ds if d]
            break
    if not periods:
        return None
    data, member = {}, "TOTAL"
    for r in rows:
        if len(r) == 1:
            lbl = r[0].strip()
            if _parse_date(lbl) or re.search(r"\$ in ", lbl, re.I):
                continue
            # 抽象行(不是成员上下文)：[Line Items]/[Abstract]/[Roll Forward]/[Table]
            if re.search(r"\[(line items|abstract|roll forward|table)\]\s*$", lbl, re.I):
                continue
            # 老版 filing(RR Donnelley 排版)把成员写成 "Government [Member]"；
            # 一律按 "含 [ 就跳过" 会把成员上下文丢掉 → member 停在 TOTAL,
            # 后续每个分部的 Revenues 行会**依次覆盖 TOTAL**,最后 TOTAL=最后一个分部的值
            # (实测 PLTR FY2020 10-K: TOTAL 变成 4.82 亿=Commercial,而真值 10.93 亿)。
            lbl = re.sub(r"\s*\[(member|domain)\]\s*$", "", lbl, flags=re.I).strip()
            if "[" in lbl or not lbl:
                continue
            member = lbl
            continue
        label, vals = r[0], [_num(c) for c in r[1:]]
        vals = [v for v in vals if v is not None]
        # 复数 "Revenues" 是 PLTR/多数 SaaS 的写法，只认单数会让整表返回 None（2026-08-12 踩过）
        if not re.search(r"^(net sales|revenues?|total revenues?|net revenues?|total net sales)$",
                         label.strip(), re.I):
            continue
        if not vals:
            continue
        data.setdefault(member, {})
        for p, v in zip(periods, vals):
            data[member][p] = v * unit_mult
    return data or None


def sec_segments(ticker, n_filings, gaps):
    """近 n 份 10-K 的 FilingSummary → 分部/产品线收入。返回 {cut: {member:{period:val}}}"""
    cik, name = sec_cik(ticker)
    sub = json.loads(_http("https://data.sec.gov/submissions/CIK%s.json" % cik))
    rec = sub["filings"]["recent"]
    tenk = [i for i, f in enumerate(rec["form"]) if f == "10-K"][:n_filings]
    if not tenk:
        gaps.append("SEC 分部：该主体无 10-K（可能是 20-F 外国私人发行人）→ 走 20-F 分部附注人工读")
        return {}, name
    cuts = {}
    for i in tenk:
        acc = rec["accessionNumber"][i].replace("-", "")
        base = "https://www.sec.gov/Archives/edgar/data/%d/%s" % (int(cik), acc)
        try:
            fs = _http(base + "/FilingSummary.xml").decode("utf-8", errors="ignore")
        except Exception as e:
            gaps.append("SEC FilingSummary 失败(%s): %s" % (rec["accessionNumber"][i], e))
            continue
        for blk in re.findall(r"<Report[^>]*>(.*?)</Report>", fs, re.S):
            nm = re.search(r"<ShortName>(.*?)</ShortName>", blk, re.S)
            fn = re.search(r"<HtmlFileName>(.*?)</HtmlFileName>", blk, re.S)
            if not (nm and fn):
                continue
            short = html.unescape(nm.group(1))
            # 实测 PLTR 用单数 "(Detail)"、AAPL 用复数 "(Details)" → 两者都要认，
            # 只认复数会让整个分部腿静默返回空（2026-08-12 踩过）。
            if not re.search(r"\(Details?\)", short, re.I):
                continue          # 只要 Detail(s) 表（有数字），跳过 Tables/正文
            # PLTR 把附注名前缀到每张表（"Segment and Geographic Information - <表名>"），
            # 拿整串去匹配会让 对账表/PP&E表 也命中 region → 只用 " - " 之后的真表名分类。
            tname = short.rsplit(" - ", 1)[-1] if " - " in short else short
            if re.search(r"reconcil|property|equipment|long-?lived", tname, re.I):
                continue          # 分部对账表 / 非收入的地区资产表
            if re.search(r"disaggregat", tname, re.I):
                cut = "product"   # 收入分解（产品线/收入类型）
            elif re.search(r"reportable segment", tname, re.I):
                cut = "reportable"
            elif re.search(r"(revenue|net sales).*(geograph|countr)|(geograph|countr).*(revenue|net sales)",
                           tname, re.I):
                cut = "region"
            else:
                continue
            try:
                d = parse_segment_table(_rfile_rows(base + "/" + fn.group(1)))
            except Exception as e:
                gaps.append("SEC R-file 解析失败 %s: %s" % (short, str(e)[:80]))
                continue
            if not d:
                continue
            tgt = cuts.setdefault(cut, {"members": {}, "reports": []})
            tgt["reports"].append({"accn": rec["accessionNumber"][i], "table": short})
            for mem, ser in d.items():
                # 成员名跨年报会换写法（'Americas' ↔ 'Americas | Operating segments'），
                # 不归一会渲成两条各缺一半的重复分部线。
                # 限定词可能在**前**（PLTR 'Operating Segments | Government'）也可能在**后**
                # （AAPL 'Americas | Operating segments'）→ 按 '|' 拆开逐段剔除限定词，
                # 只留真正的成员名；剔空的（纯限定词行，值=合计）直接丢弃。
                QUAL = (r"^geographic\s+concentration\s+risk$|^concentration\s+risk$|"
                        r"^revenue\s+benchmark$|^(minimum|maximum)$")
                keep = []
                for p in [x.strip() for x in mem.split("|") if x.strip()]:
                    if re.search(QUAL, p, re.I):
                        continue
                    # 限定词可能**长在成员名里**：FY2024 写 'Government Operating Segment'，
                    # 而 FY2023/FY2025 写 'Government' → 只做整段匹配会留下两条各缺一半的重复线
                    # (实测 Σ分部 比财报高 55%)。故剥掉尾部的 (Operating|Reportable) Segment(s)。
                    p = re.sub(r"\s*(operating|reportable)?\s*segments?$", "", p, flags=re.I).strip()
                    if p:
                        keep.append(p)
                key = " | ".join(keep).strip()
                if not key:
                    continue          # 纯限定词成员(等于合计),不建线
                if key.upper() == "TOTAL":
                    key = "TOTAL"
                tgt_ser = tgt["members"].setdefault(key, {})
                for p, v in ser.items():        # 跨年报合并：老 filing 只补早年空档，
                    tgt_ser.setdefault(p, v)    # 不覆盖新 filing 的重述值
    for cut, v in cuts.items():
        v["source"] = "SEC EDGAR 10-K FilingSummary R-file"
        v["caliber"] = {"product": "收入分解附注(产品线/收入类型)",
                        "reportable": "报告分部附注(ASC 280)",
                        "region": "地区/国家收入附注"}[cut]
    return cuts, name


# ---------------------------------------------------------------- 派生：杜邦 / 费率 / 营收
IND = {  # 分析指标字段名 → 统一键（美股与港股共用大部分）
    "roe": ["ROE_AVG"], "roa": ["ROA"], "gm": ["GROSS_PROFIT_RATIO"],
    "nm": ["NET_PROFIT_RATIO"], "dar": ["DEBT_ASSET_RATIO"],
    "tat": ["TOTAL_ASSETS_TR"], "rev": ["OPERATE_INCOME"], "rev_yoy": ["OPERATE_INCOME_YOY"],
    "np": ["PARENT_HOLDER_NETPROFIT", "HOLDER_PROFIT"], "eps": ["BASIC_EPS"],
    "gp": ["GROSS_PROFIT"], "cur": ["CURRENCY"],
}


def ind_series(indicators, key, periods):
    if not indicators:
        return [None] * len(periods)
    for c in IND[key]:
        if c in indicators["cols"]:
            return [indicators["cols"][c].get(p) for p in periods]
    return [None] * len(periods)


def build_dupont(market, indicators, periods, gaps, balance=None):
    """ROE = 净利率 × 总资产周转率 × 权益乘数。美股周转率直给；港股缺 → ROA/净利率 反推[Inference]"""
    if not indicators:
        gaps.append("杜邦：分析指标缺失，无法构建")
        return None
    roe = ind_series(indicators, "roe", periods)
    nm = ind_series(indicators, "nm", periods)
    dar = ind_series(indicators, "dar", periods)
    tat = ind_series(indicators, "tat", periods)
    roa = ind_series(indicators, "roa", periods)
    notes = []
    em = []
    ta, ta_it = series(balance, ["总资产", "资产总额", "资产总计"], periods) if balance else ([], None)
    # 归母口径优先（ROE 分母是归母权益）：美股『归属于母公司股东权益』/ 港股『股东权益』；
    # 『总权益』『股东权益合计』含少数股东，只作兜底，命中时 notes 会写明口径
    eq, eq_it = series(balance, ["归属于母公司股东权益", "股东权益", "本公司拥有人应占权益",
                                 "净资产", "股东权益合计", "总权益", "权益总额"], periods) \
        if balance else ([], None)
    if ta_it and eq_it:
        em = [round(a / e, 4) if (a is not None and e) else None for a, e in zip(ta, eq)]
        notes.append("权益乘数 = %s/%s 资产负债表实算 [FACT]" % (ta_it, eq_it))
        if eq_it in ("股东权益合计", "总权益", "权益总额"):
            notes.append("⚠️ 权益分母是**含少数股东**口径，而 ROE 分子多为归母 → 恒等式会系统性偏低，页面需注明")
    else:
        for d in dar:
            em.append(round(1.0 / (1.0 - d / 100.0), 4) if d not in (None, 100) else None)
        notes.append("权益乘数 = 1/(1−资产负债率) [Inference]（资产负债表未取到，非直给）")
    if all(v is None for v in tat):
        tat = [round(a / n, 4) if (a is not None and n) else None for a, n in zip(roa, nm)]
        notes.append("总资产周转率 = ROA/销售净利率 [Inference]（港股分析指标不直给周转率）")
    else:
        notes.append("总资产周转率 = TOTAL_ASSETS_TR 直给 [FACT]")
    check = []
    for r, n, t, e in zip(roe, nm, tat, em):
        if None in (r, n, t, e) or r == 0:
            check.append(None)
        else:
            check.append(round((n * t * e) / r, 3))       # 恒等式闭合度，理想≈1
    bad = [c for c in check if c is not None and abs(c - 1) > 0.25]
    if bad:
        notes.append("⚠️ 恒等式闭合度偏离>25%% 的年份 %d 个（口径差异，映射前人工核）" % len(bad))
    return {"years": [p[:4] for p in periods], "periods": periods,
            "roe": roe, "net_margin": nm, "asset_turnover": tat, "equity_multiplier": em,
            "identity_check": check, "notes": notes,
            "source": indicators["source"]}


def build_cost_structure(market, income, indicators, periods, gaps):
    """费率瀑布：营收/营业成本/毛利率/净利率 + 销售·管理·研发·财务 费率"""
    if not income:
        gaps.append("成本费率：利润表缺失")
        return None
    if market == "US":
        rev, rev_it = series(income, ["主营收入", "营业收入"], periods)
        cost, _ = series(income, ["主营成本", "营业成本"], periods)
        sell, _ = series(income, ["营销费用"], periods)
        admin, admin_it = series(income, ["其他营业费用", "一般及行政费用"], periods)
        rnd, _ = series(income, ["研发费用"], periods)
        fin, fin_it = series(income, ["利息支出", "融资成本"], periods)
        if fin_it is None:
            gaps.append("美股财务费用率：东财损益表未单列利息支出（只有『利息收入』净额）→ 标 ⚠️未查到 或从 10-K 附注读")
        if admin_it is None:
            gaps.append("美股销售/管理二分不成立：多数美股按 SG&A 合并披露，东财只落『营销费用』一行"
                        "（实测 AAPL 2025 该行 6.63%＝Selling 19,524M + G&A 8,077M 合计）→ "
                        "费率图应**合并渲一条 SG&A**，不要当成 A 股的销售费用/管理费用分开解读")
    else:
        rev, rev_it = series(income, ["营业额", "营运收入"], periods)
        cost, _ = series(income, ["营运支出"], periods)
        sell, _ = series(income, ["销售及分销费用"], periods)
        admin, admin_it = series(income, ["行政开支"], periods)
        rnd, rnd_it = series(income, ["研发费用", "研发开支"], periods)
        fin, _ = series(income, ["融资成本"], periods)
        if rnd_it is None:
            gaps.append("港股研发费用：东财利润表不单列（多并入行政开支）→ 研发费率标 ⚠️未查到，需年报附注")
        gaps.append("港股收入口径：『营业额』(主营) vs 『营运收入』(含其他营业收入) 两行并存，"
                    "本表取 %s；页面 caliber 必须写明，勿与 A 股『营业总收入』混用" % rev_it)

    def rate(x):
        return [round(v / r * 100, 3) if (v is not None and r) else None for v, r in zip(x, rev)]

    gm = ind_series(indicators, "gm", periods)
    nm = ind_series(indicators, "nm", periods)
    if all(v is None for v in gm):
        gm = [round((r - c) / r * 100, 3) if (r and c is not None) else None for r, c in zip(rev, cost)]
    return {"years": [p[:4] for p in periods], "periods": periods,
            "total_rev_yi": [_yi(v) for v in rev], "op_cost_yi": [_yi(v) for v in cost],
            "gross_margin": gm, "net_margin": nm,
            "sell_exp_rate": rate(sell), "admin_exp_rate": rate(admin),
            "sga_rate": rate(add_series(sell, admin)),      # 销售+管理合并口径(美股常态)
            "sga_split_available": admin_it is not None,    # False → 页面只能渲合并 SG&A 一条
            "rnd_exp_rate": rate(rnd), "fin_exp_rate": rate(fin),
            "rev_item": rev_it, "source": income.get("source")}


def build_revenue(market, income, indicators, periods, segments, gaps):
    if market == "US":
        rev, rev_it = series(income, ["主营收入", "营业收入"], periods) if income else ([], None)
    else:
        rev, rev_it = series(income, ["营业额", "营运收入"], periods) if income else ([], None)
    yoy = ind_series(indicators, "rev_yoy", periods)
    if all(v is None for v in yoy):
        yoy = []
        for i, v in enumerate(rev):
            prev = rev[i + 1] if i + 1 < len(rev) else None
            yoy.append(round((v / prev - 1) * 100, 3) if (v is not None and prev) else None)
    out = {"years": [p[:4] for p in periods], "periods": periods,
           "total_yi": [_yi(v) for v in rev], "yoy": yoy, "rev_item": rev_it,
           "caliber": "东财口径 %s" % rev_it, "segments": []}
    if segments:
        for cut, blk in segments.items():
            allp = sorted({p for s in blk["members"].values() for p in s}, reverse=True)
            keep = [p for p in allp if any(p[:4] == q[:4] for q in periods)] or allp
            segs = []
            for mem, ser in blk["members"].items():
                if mem == "TOTAL":
                    continue
                segs.append({"name": mem, "periods": keep,
                             "values_yi": [_yi(ser.get(p)) for p in keep]})
            out["segments"].append({"cut": cut, "caliber": blk["caliber"],
                                    "source": blk["source"], "periods": keep,
                                    "total_yi": [_yi(blk["members"].get("TOTAL", {}).get(p)) for p in keep],
                                    "items": segs})
    else:
        gaps.append("分部收入：**无结构化源**。港股→年报『分部资料』附注 PDF/AlphaPai 纪要人工抄；"
                    "美股→若本脚本 SEC 段为空，读 10-K Segment/Disaggregation 附注。"
                    "CK-3 要求 Σ分部=总收入，缺此项 Part3 的 STP 拆分无法过闸。")
    return out


# ---------------------------------------------------------------- meta / 市值锚
def last_close(ticker, market, gaps):
    """复用 fetch_kline.py 的取价逻辑，不重复实现传输层"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import fetch_kline as fk
    except Exception as e:
        gaps.append("现价：无法导入 fetch_kline(%s)" % e)
        return None, None
    start = (dt.date.today() - dt.timedelta(days=60)).isoformat()
    try:
        daily, src = fk.fetch_akshare(ticker, market, start)
        if daily:
            return daily[-1]["c"], src
    except Exception:
        pass
    try:
        wk, src = fk.fetch_tencent(ticker, market, 12)
        if wk:
            return wk[-1]["c"], src
    except Exception as e:
        gaps.append("现价：akshare 与腾讯均失败(%s)" % str(e)[:80])
    return None, None


def build_meta(market, ticker, name, income, indicators, periods, hk_extra, gaps):
    cur = None
    if indicators and "CURRENCY" in indicators["cols"]:
        cur = list(indicators["cols"]["CURRENCY"].values())[0]
    price, psrc = last_close(ticker, market, gaps)
    # 股数：优先加权股数(美股损益表直给)，否则 归母净利/EPS 反推
    shares = None
    if income:
        sh, sh_it = series(income, ["基本加权平均股数-普通股", "摊薄加权平均股数-普通股"], periods)
        if sh and sh[0]:
            shares, shares_src = sh[0], "损益表 %s" % sh_it
    if shares is None:
        np_ = ind_series(indicators, "np", periods)
        eps = ind_series(indicators, "eps", periods)
        if np_ and eps and np_[0] and eps[0]:
            shares, shares_src = np_[0] / eps[0], "归母净利/基本EPS 反推 [Inference]"
    if shares is None:
        shares_src = None
        gaps.append("总股本：未取到（美股走 EDGAR dei:EntityCommonStockSharesOutstanding，港股走年报/披露易）")
    mcap = price * shares if (price and shares) else None
    np0 = (ind_series(indicators, "np", periods) or [None])[0]
    pe_calc = round(mcap / np0, 2) if (mcap and np0) else None
    meta = {"name": name, "ticker": ticker, "market": market,
            "currency_reported": cur, "unit": "亿(当地币种)",
            "price": price, "price_source": psrc,
            "shares_yi": _yi(shares), "shares_source": shares_src,
            "mcap_yi": _yi(mcap), "mcap_note": "= 现价 × 股本（自算，非接口直给）",
            "pe_ttm_calc": pe_calc, "pe_calc_note": "= 自算市值 / 最新年度归母净利（非 TTM，年度口径）"}
    # 币种/口径交叉校验：自算 PE vs 接口 PE 差太多 → 多半是币种或期数错位
    if market == "HK" and hk_extra.get("valuation_cmp"):
        pe_api = _num(hk_extra["valuation_cmp"]["row"].get("市盈率-TTM"))
        if pe_api and pe_calc:
            ratio = round(pe_calc / pe_api, 3)
            meta["currency_check"] = {
                "pe_calc": pe_calc, "pe_api_ttm": pe_api, "ratio": ratio,
                "verdict": "OK(±15%内)" if abs(ratio - 1) <= 0.15 else
                           "⚠️ 偏离>15%：多半是 财报币种≠交易币种（如腾讯报人民币、交易港元）或 年度vs TTM 期数错位。"
                           "**未查清前不得把 mcap_yi 直接喂估值范式**（赔率会整体错一个汇率）"}
            if abs(ratio - 1) > 0.15:
                gaps.append("币种/口径：自算PE %.2f vs 接口PE-TTM %.2f（差 %.0f%%）→ 必须人工定 fx 与口径"
                            % (pe_calc, pe_api, (ratio - 1) * 100))
    return meta


# ---------------------------------------------------------------- 结构性缺口（港美股共有）
def structural_gaps(market):
    g = ["十大股东/派系逐季堆积图（CK-1 必出模块）：港美股**结构性不存在** A 股口径的逐季十大流通股东。"
         "港股→CCASS/披露易(无零鉴权API)；美股→13F 机构持仓(滞后45天,口径不同)。"
         "建议该格改渲『主要股东/机构持仓』降级版并在图上标注受限。",
         "股权结构树 qcc（CK-1 必出模块）：qcc 只覆盖中国大陆主体。"
         "%s → 母公司(开曼/BVI)与境外子公司不解析；若有大陆运营主体可单独查大陆那一层并注明只是局部。"
         % ("港股" if market == "HK" else "美股")]
    if market == "US":
        g.append("美股一致预期：akshare 无覆盖 → 走 AlphaPai roadShow_us(美股业绩会) 或卖方模型，标【Estimate】")
    return g


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True, help="美股裸码 AAPL / 港股 00700")
    ap.add_argument("--market", required=True, choices=["HK", "US"])
    ap.add_argument("--y0", default=str(dt.date.today().year - 10))
    ap.add_argument("--y1", default=str(dt.date.today().year))
    ap.add_argument("--out", required=True)
    ap.add_argument("--sec-filings", type=int, default=3, help="回溯几份 10-K 取分部(默认3≈5-7年)")
    ap.add_argument("--no-segments", action="store_true")
    a = ap.parse_args()

    years = (a.y0, a.y1)
    gaps, sources = [], {}
    print("[1/4] 三表 + 分析指标 (%s %s) ..." % (a.market, a.ticker), flush=True)
    raw = fetch_us(a.ticker, years, gaps, sources) if a.market == "US" \
        else fetch_hk(a.ticker, years, gaps, sources)

    income = raw.get("income")
    indicators = raw.get("indicators")
    periods = (indicators or income or {}).get("periods", [])
    if income and indicators:                      # 以利润表期数为准（更长）
        periods = income["periods"]
        periods = [p for p in periods if p in indicators["periods"]] or income["periods"]
    print("    报告期 %d 个: %s" % (len(periods), ", ".join(periods[:3]) + (" ..." if len(periods) > 3 else "")))

    segments, name = None, a.ticker
    if a.market == "US" and not a.no_segments:
        print("[2/4] SEC EDGAR 分部 (10-K R-file) ...", flush=True)
        try:
            segments, name = sec_segments(a.ticker, a.sec_filings, gaps)
            print("    拿到切面: %s" % (", ".join("%s(%d项)" % (k, len(v["members"]) - 1)
                                                 for k, v in segments.items()) or "无"))
        except Exception as e:
            gaps.append("SEC 分部整体失败: %s: %s" % (type(e).__name__, str(e)[:120]))
            print("    ⚠️ %s" % e)
    else:
        print("[2/4] 分部：港股无结构化源，跳过（见 gaps）")
    if a.market == "HK" and raw.get("profile", {}).get("公司名称"):
        name = raw["profile"]["公司名称"]

    print("[3/4] 派生 杜邦/费率/营收 + 市值锚 ...", flush=True)
    dupont = build_dupont(a.market, indicators, periods, gaps, raw.get("balance"))
    cost = build_cost_structure(a.market, income, indicators, periods, gaps)
    revenue = build_revenue(a.market, income, indicators, periods, segments, gaps)
    meta = build_meta(a.market, a.ticker, name, income, indicators, periods, raw, gaps)
    gaps.extend(structural_gaps(a.market))

    out = {"ticker": a.ticker, "market": a.market, "asof": dt.date.today().isoformat(),
           "y0": a.y0, "y1": a.y1, "meta": meta,
           "tables": {"income": income, "balance": raw.get("balance"), "cashflow": raw.get("cashflow"),
                      "indicators": indicators, "dupont": dupont, "cost_structure": cost,
                      "revenue": revenue,
                      "consensus": raw.get("consensus"), "valuation_cmp": raw.get("valuation_cmp"),
                      "scale_cmp": raw.get("scale_cmp"), "profile": raw.get("profile"),
                      "pe_history": raw.get("pe_history")},
           "gaps": gaps, "sources": sources}

    print("[4/4] 落盘 ...", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        # default=str: etnet/东财 表里混有 datetime.date 与 numpy 标量，直接 dump 会 TypeError
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    print("✅ %s  (%s %s, %d 期)" % (a.out, a.market, a.ticker, len(periods)))
    if meta.get("mcap_yi"):
        print("   市值锚: %.1f 亿(当地币种) = %.2f × %.2f 亿股 | PE(自算) %s"
              % (meta["mcap_yi"], meta["price"], meta["shares_yi"], meta["pe_ttm_calc"]))
    print("\n⚠️ gaps (%d 条，Phase2 映射前逐条处理):" % len(gaps))
    for g in gaps:
        print("   - %s" % g)


if __name__ == "__main__":
    main()
