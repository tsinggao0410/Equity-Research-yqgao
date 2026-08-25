# -*- coding: utf-8 -*-
"""
fetch_fmp_consensus.py — 1.5 节「券商预期区间 · 兑现记录 · 未来预期延展」取数（FMP stable API）
==============================================================================
v2（2026-08-08）把 1.5 从「两张割裂的图」改成**一条连续时间轴**：

    已披露期                          │  未来期
    ├─ 券商预测区间箱（Low–High）      │  ├─ 券商预测区间箱（Low–High）
    ├─ ▬ 区间均值      ← 内部预期点①   │  ├─ ▬ 区间均值
    ├─ ○ 财报前一致预期 ← 内部预期点②   │  └─（无实际值）
    └─ ★ 实际披露值（绿=beat 红=miss）  │
                                今天 ┊

三件事一张图说清：**券商当时怎么看 → 实际落在区间哪儿 → 现在对未来怎么看**。
收入 / 净利润 / EPS 三个口径都做（原来只有 EPS）。

为什么要两个「内部预期点」——它们不是一回事，差值本身是信息：
  · **区间均值**（`analyst-estimates.Avg`）= 当前快照下全体分析师的平均值，会被事后修订；
  · **财报前一致预期**（`earnings.epsEstimated`）= 该次财报**公布前**的一致预期点，point-in-time，不被事后修订。
  两者背离大 → 说明这期财报之后卖方大幅改了预测（预期重置），是第二章阶段归因的直接线索。

数据源（全部 /stable/，v3 legacy 已于 2025-08-31 停用）:
  · analyst-estimates?period=annual|quarter → revenue/ebitda/ebit/netIncome/eps 的 Low/Avg/High + numAnalysts
                                              **历史期同样有区间**（实测 300750 回溯到 2018，24-31 家覆盖）
  · income-statement?period=annual|quarter   → 实际 revenue/netIncome/eps（**年度实际值以此为准**）
  · earnings                                 → epsActual/epsEstimated/revenueActual/revenueEstimated（财报前一致预期点）
  · price-target-consensus / grades-*        → 目标价与评级（**实测仅美股有，A/港股返回空**）

⚠️ 口径坑（脚本已全部显式处理，不要绕过）:
  1. **箱体是全距不是四分位**——FMP 只给 Low/Avg/High，页面必须写明（`box_caliber`）。
  2. **年度 vs 单季不可混**：`earnings.epsActual` 是**单季**；`analyst-estimates(annual).eps` 是**全年**。
     本脚本按 period 分别取 income-statement 的 annual/quarter 实际值，不跨口径相减。
  3. **A股季度覆盖极薄**（实测 300750 年度 24-29 家 / 季度 1-4 家）→ coverage 逐指标算，薄的画虚线。
  4. **报告币种≠交易币种**（腾讯报 CNY 交易 HKD）→ 传 --page-currency 触发币种闸。
  5. **财年末日逐年漂移**（NVDA annual est 2027-01-25 vs inc 2016-01-31）→ 日期用**容差最近邻**匹配，不用等值。

用法:
  python3 scripts/fetch_fmp_consensus.py --ticker 300750 --market A \
      --page-currency CNY \
      --kline _workspace/300750/kline_weekly.json \
      --out _workspace/300750/fmp_consensus.json

输出直接进 page_model.part1.consensus（契约见 SKILL.md / references/11-consensus-boxplot.md）。
"""
import argparse, json, os, sys, time
import datetime as dt
import urllib.request, urllib.parse, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(HERE, "fmp_config.json")

YI = 1e8  # 亿
METRICS = ("rev", "np", "eps")


# ---------------------------------------------------------------- 配置 / 传输
def load_cfg():
    cfg = {}
    if os.path.exists(CFG_PATH):
        try:
            cfg = json.load(open(CFG_PATH, encoding="utf-8"))
        except Exception as e:
            print("!! fmp_config.json 解析失败: %s" % e, file=sys.stderr)
    key = os.environ.get("FMP_API_KEY") or cfg.get("api_key") or ""
    base = os.environ.get("FMP_BASE_URL") or cfg.get("base_url") or "https://financialmodelingprep.com/stable"
    if not key:
        sys.exit("!! 缺少 FMP api_key：设环境变量 FMP_API_KEY 或填 scripts/fmp_config.json")
    return {
        "key": key,
        "base": base.rstrip("/"),
        "inline_band": float(cfg.get("_inline_band_pct", 2.0)),
        "thin_n": int(cfg.get("_thin_coverage_n", 3)),
        "match_tol_days": int(cfg.get("_match_tol_days", 45)),
    }


def get(cfg, path, **params):
    """GET /stable/<path>?...&apikey= 。失败返回 (None, 错误串)，不抛——缺一个接口不该毁整份报告。"""
    params["apikey"] = cfg["key"]
    url = "%s/%s?%s" % (cfg["base"], path, urllib.parse.urlencode(params))
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "equity-onepager/2.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read().decode("utf-8", "replace")
            data = json.loads(body)
            if isinstance(data, dict) and ("Error Message" in data or "error" in data):
                return None, str(data)[:200]
            return data, None
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:160]
            except Exception:
                pass
            if e.code in (429, 502, 503) and attempt < 2:
                time.sleep(2 + attempt * 3)
                continue
            return None, "HTTP %s %s" % (e.code, detail)
        except Exception as e:
            if attempt < 2:
                time.sleep(1.5)
                continue
            return None, "%s: %s" % (type(e).__name__, e)
    return None, "重试耗尽"


# ---------------------------------------------------------------- 工具
def to_fmp_symbol(ticker, market):
    """A股 600519→600519.SS / 300750→300750.SZ；港股 700→0700.HK；韩股 000660→000660.KS；美股原样。"""
    t = str(ticker).strip().upper()
    if "." in t and t.rsplit(".", 1)[1] in ("SS", "SZ", "HK", "SHH", "SHZ", "KS", "KQ"):
        return t
    bare = t.split(".")[0]
    if market == "A":
        return (bare.zfill(6) + ".SS") if bare.startswith(("6", "9")) else (bare.zfill(6) + ".SZ")
    if market == "HK":
        return bare.zfill(4) + ".HK"
    if market == "KR":
        return bare.zfill(6) + ".KS"   # KOSPI；创业板 KOSDAQ 请直接传带 .KQ 的完整代码
    return bare


def fnum(x):
    try:
        v = float(x)
        return v if v == v and v not in (float("inf"), float("-inf")) else None
    except (TypeError, ValueError):
        return None


def d(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def nearest(target, pool, tol_days):
    """财年末日逐年漂移（NVDA 1/25 vs 1/31），必须容差最近邻，不能等值匹配。"""
    t = d(target)
    if not t:
        return None
    best, bestgap = None, None
    for k in pool:
        kd = d(k)
        if not kd:
            continue
        gap = abs((kd - t).days)
        if gap <= tol_days and (bestgap is None or gap < bestgap):
            best, bestgap = k, gap
    return best


def q_label(date_str):
    dd = d(date_str)
    if not dd:
        return str(date_str)[:10]
    return "%02dQ%d" % (dd.year % 100, (dd.month - 1) // 3 + 1)


def y_label(date_str):
    dd = d(date_str)
    return "FY%d" % dd.year if dd else str(date_str)[:4]


def band(lo, avg, hi, n, scale=1.0, thin_n=3):
    """一个指标的分布三元组。coverage 必须**逐指标**算：
    实测 300750 FY2024 收入 24 家但 EPS 只有 2 家，用 max() 会把「EPS 样本极薄」盖掉，箱线图就骗人。"""
    lo, avg, hi = fnum(lo), fnum(avg), fnum(hi)
    if avg is None and lo is None and hi is None:
        return None
    nn = fnum(n)
    out = {
        "lo": round(lo * scale, 4) if lo is not None else None,
        "avg": round(avg * scale, 4) if avg is not None else None,
        "hi": round(hi * scale, 4) if hi is not None else None,
        "n": int(nn) if nn is not None else None,
        "coverage": "none" if (nn is None or nn < 1) else ("thin" if nn < thin_n else "ok"),
    }
    if out["avg"] and out["lo"] is not None and out["hi"] is not None and out["avg"] != 0:
        out["spread"] = round((out["hi"] - out["lo"]) / abs(out["avg"]), 4)
    # 合成区间探测用的 lo/avg、hi/avg 比值**必须从未取整的原值算**：
    # np 以「亿」计(~50)、eps 以「元」计(~0.67)，同样 round(...,4) 保留的有效位数差 4 个数量级，
    # 用取整后的值算比值会让本该相等的 np/eps 比值对不上，合成带就会被标漏（实测 002371 年度 np 标 8 期、eps 只标 4 期）。
    if avg and lo is not None and hi is not None and avg != 0:
        out["_r"] = [lo / avg, hi / avg]
    return out


# ---------------------------------------------------------------- 实际值 / 财报前预期
def pull_actuals(cfg, sym, period):
    """income-statement 实际值。annual→全年口径，quarter→单季口径，**绝不跨口径**。"""
    rows, err = get(cfg, "income-statement", symbol=sym, period=period, limit=40)
    if err or not isinstance(rows, list):
        return {}, ["income-statement(%s) 失败: %s" % (period, err or "返回非列表")]
    out = {}
    for r in rows:
        date = str(r.get("date", ""))[:10]
        if not date:
            continue
        rev, ni, eps = fnum(r.get("revenue")), fnum(r.get("netIncome")), fnum(r.get("eps"))
        out[date] = {
            "shs": fnum(r.get("weightedAverageShsOut")),   # EPS 口径闸要用（见 normalize_eps_basis）
            "rev": round(rev / YI, 3) if rev is not None else None,
            "np": round(ni / YI, 3) if ni is not None else None,
            "eps": round(eps, 4) if eps is not None else None,
            "ccy": r.get("reportedCurrency"),
        }
    return out, []


def pull_pre_estimates(cfg, sym, limit=40):
    """earnings 的 epsEstimated/revenueEstimated = **财报公布前**的一致预期点（point-in-time，不被事后修订）。
    与 analyst-estimates 的 Avg（当前快照）是两个东西，两者都要，差值本身是信息。"""
    rows, err = get(cfg, "earnings", symbol=sym, limit=limit)
    if err or not isinstance(rows, list):
        return {}, [], ["earnings 失败: %s" % (err or "返回非列表")]
    by_date, raw = {}, []
    for r in rows:
        date = str(r.get("date", ""))[:10]
        if not date:
            continue
        ra, re_ = fnum(r.get("revenueActual")), fnum(r.get("revenueEstimated"))
        rec = {
            "date": date,
            "eps_act": fnum(r.get("epsActual")), "eps_pre": fnum(r.get("epsEstimated")),
            "rev_act": round(ra / YI, 3) if ra is not None else None,
            "rev_pre": round(re_ / YI, 3) if re_ is not None else None,
        }
        # FMP earnings 里有一批 date==报告期末、估计值全空的**占位行**
        # （002371 实测 2019~2024 每年 12-31 各一条），入池会污染值匹配
        if rec["eps_pre"] is None and rec["rev_pre"] is None:
            continue
        by_date[date] = rec
        raw.append(rec)
    raw.sort(key=lambda x: x["date"])
    return by_date, raw, []


# ---------------------------------------------------------------- 预期区间 + 合并
def verdict_of(actual, ref, inline_band):
    if actual is None or ref in (None, 0):
        return None, None
    surp = (actual - ref) / abs(ref) * 100
    v = "beat" if surp > inline_band else ("miss" if surp < -inline_band else "inline")
    return round(surp, 2), v


def pull_estimates(cfg, sym, period, asof, actuals, pre_map, limit=40):
    thin_n, tol, inline = cfg["thin_n"], cfg["match_tol_days"], cfg["inline_band"]
    rows, err = get(cfg, "analyst-estimates", symbol=sym, period=period, limit=limit)
    if err or not isinstance(rows, list):
        return [], ["analyst-estimates(%s) 失败: %s" % (period, err or "返回非列表")]
    out, gaps, claimed = [], [], set()          # claimed: 一个 earnings 行只能被一个报告期认领
    for r in sorted(rows, key=lambda x: str(x.get("date", ""))):
        date = str(r.get("date", ""))[:10]
        if not date:
            continue
        n_rev, n_eps = r.get("numAnalystsRevenue"), r.get("numAnalystsEps")
        rec = {
            "date": date,
            "label": q_label(date) if period == "quarter" else y_label(date),
            "is_future": date > asof,
            "rev": band(r.get("revenueLow"), r.get("revenueAvg"), r.get("revenueHigh"), n_rev, 1.0 / YI, thin_n),
            "np": band(r.get("netIncomeLow"), r.get("netIncomeAvg"), r.get("netIncomeHigh"), n_eps, 1.0 / YI, thin_n),
            "eps": band(r.get("epsLow"), r.get("epsAvg"), r.get("epsHigh"), n_eps, 1.0, thin_n),
            "ebitda": band(r.get("ebitdaLow"), r.get("ebitdaAvg"), r.get("ebitdaHigh"), n_rev, 1.0 / YI, thin_n),
        }

        # ---- 挂实际披露值（容差最近邻；财年末日会漂）
        ak = nearest(date, actuals.keys(), tol)
        if ak:
            rec["actual_date"] = ak
            rec["actual_shs"] = actuals[ak].get("shs")
            for m in METRICS:
                if rec.get(m) is not None:
                    rec[m]["actual"] = actuals[ak].get(m)

        # ---- 挂财报前一致预期点（point-in-time）
        # ⚠️ `earnings` 接口**本身就是季度口径**（epsEstimated=该季一致预期）。
        #    年度期若也走容差匹配，会把「某个季度的预期」挂到「全年箱」上——口径错配。
        #    实测 002371 年末距最近财报日 73 天 > 45 天容差侥幸没触发，但换公司就会中招。
        #    所以：**只有 period=='quarter' 才挂 pre_est**，年度期没有对应的年度财报前一致预期点。
        # ★ 财报前一致预期只挂季度，且**必须按实际值配对，不能按日期就近**。
        #   A股年报与一季报公告只差两三周：实测 26Q1(2026-03-31) 以 17 天之差抢走了
        #   2026-04-17 那行（实为 FY2025 年报），把真 miss 判成 beat +132%。
        if period == "quarter" and ak:
            pk = match_earnings_row(actuals[ak], pre_map, claimed=claimed)
            if not pk:
                gaps.append("%s 未能按营收值配到 earnings 行 → 该期退回用区间均值判定(basis=avg)" % rec["label"])
            if pk:
                claimed.add(pk)
                rec["pre_est_date"] = pk
                pre = pre_map[pk]
                if rec.get("eps") is not None:
                    rec["eps"]["pre_est"] = pre.get("eps_pre")
                if rec.get("rev") is not None:
                    rec["rev"]["pre_est"] = pre.get("rev_pre")

        levels = [b["coverage"] for b in (rec["rev"], rec["eps"]) if b]
        rec["coverage"] = ("none" if "none" in levels else "thin" if "thin" in levels else "ok") if levels else "none"
        if rec["is_future"] and rec["coverage"] != "ok":
            gaps.append("%s(%s) 覆盖薄：收入 n=%s / EPS n=%s → 箱线图画虚线，不作共识用"
                        % (rec["label"], period, (rec["rev"] or {}).get("n"), (rec["eps"] or {}).get("n")))
        out.append(rec)

    # ---- 判定之前先过两道口径闸（顺序不能反）
    mark_synthetic_bands(out, gaps, period)
    disable_eps_history(out, gaps, period)

    # ---- 逐指标算：vs 财报前预期(优先) / vs 区间均值；以及是否落在区间内
    for rec in out:
        for m in METRICS:
            b = rec.get(m)
            if not b:
                continue
            act = b.get("actual")
            b["surp_vs_pre"], b["verdict"] = verdict_of(act, b.get("pre_est"), inline)
            b["surp_vs_avg"], v_avg = verdict_of(act, b.get("avg"), inline)
            if b.get("verdict") is None:
                b["verdict"] = v_avg          # 无财报前预期时退回用区间均值判定
                b["verdict_basis"] = "avg" if v_avg else None
            else:
                b["verdict_basis"] = "pre"
            # 合成区间不参与"实际是否落在区间内"——那条带子是假的
            # 合成区间不参与"实际是否落在区间内"；退化区间（宽度<均值1%）同样不参与——
            # 分母趋近 0 会把任何微小偏离放大成离谱数值（实测 AAPL 某期 lo=1.429/hi=1.4291 → range_pos=1010）。
            if (act is not None and b.get("lo") is not None and b.get("hi") is not None
                    and not b.get("synthetic")):
                width = b["hi"] - b["lo"]
                if b.get("avg") and abs(width / b["avg"]) < 0.01:
                    b["degenerate"] = True
                else:
                    b["in_range"] = bool(b["lo"] <= act <= b["hi"])
                    b["range_pos"] = round((act - b["lo"]) / width, 3) if width else None
    sanity_check_series(out, gaps, period)
    return out, gaps


def match_earnings_row(actual_rec, pre_map, rel_tol=0.005, claimed=None):
    """把 earnings 行配到正确的报告期：**用 revenueActual 数值配对**，不是日期就近。
    earnings 行自带该期实际营收，与 income-statement 的当期营收对得上才是同一期。
    日期就近在 A 股必错——年报(4月中)与一季报(4月底)只差两周。"""
    tgt = actual_rec.get("rev")
    if tgt is None or not tgt:
        return None
    best, bestgap = None, None
    for k, v in pre_map.items():
        if claimed and k in claimed:          # 已被别的报告期认领，不重复挂
            continue
        ra = v.get("rev_act")
        if ra is None or not tgt:
            continue
        gap = abs(ra - tgt) / abs(tgt)
        if gap <= rel_tol and (bestgap is None or gap < bestgap):
            best, bestgap = k, gap
    return best


def mark_synthetic_bands(rows, gaps, period, min_run=3, tol=1e-4):
    """★ 识别 FMP 的**合成区间**（2026-08-08 审计确认的重大坑）。

    FMP 对早年缺失的分析师分歧数据会**回填一个固定比例的假区间**：
      · 002371 FY2015–FY2022：lo/avg 恒为 0.9448、hi/avg 恒为 1.0593（覆盖家数在 8~17 间跳，比值纹丝不动）
      · 300750 FY2018–FY2022：恒为 0.8479 / 1.2823
      · 0700.HK FY2015–FY2022：恒为 0.8819 / 1.0427
      · **AAPL FY1998–FY2023 长达 26 年恒为 0.80 / 1.20**（字面意义的 avg±20%，铁证）
    这种带子**不是真实分歧**，拿它算「区间命中率 / 实际在区间中的位置」会得到离谱结论
    （实测 002371 np 的 avg_range_pos = −0.46，剔除合成带后翻转为 +0.53，in_range 从 54.5%→100%）。

    **必须探测式识别，不能写死年份**——合成带的比例值 per-ticker 不同，终止年份也不同。
    规则：同一指标上连续 ≥min_run 期的 lo/avg 与 hi/avg 比值都相同（容差 tol）→ 整段标 synthetic。
    已知保守之处：只重复 2 期的尾行（如 0700.HK FY2028/29）不会被标记，宁可漏标不误伤。"""
    for m in METRICS:
        ratios = [(tuple(r[m]["_r"]) if (r.get(m) and r[m].get("_r")) else None) for r in rows]
        i = 0
        while i < len(ratios):
            if ratios[i] is None:
                i += 1
                continue
            j = i + 1
            while (j < len(ratios) and ratios[j] is not None
                   and abs(ratios[j][0] - ratios[i][0]) < tol and abs(ratios[j][1] - ratios[i][1]) < tol):
                j += 1
            if j - i >= min_run:
                for k in range(i, j):
                    rows[k][m]["synthetic"] = True
                gaps.append("%s·%s %s–%s 共 %d 期为 FMP **合成区间**（lo/avg=%.4f、hi/avg=%.4f 恒定，与覆盖家数脱钩），"
                            "已排除出全部兑现统计，页面画灰"
                            % (period, {"rev": "收入", "np": "净利润", "eps": "EPS"}[m],
                               rows[i]["label"], rows[j - 1]["label"], j - i, ratios[i][0], ratios[i][1]))
            i = j


def disable_eps_history(rows, gaps, period):
    """★ EPS 历史兑现整体下线（2026-08-08 审计结论，比"重算"更正确）。

    一度尝试把实际 EPS 按"预期口径隐含股本"重算再比，但那个隐含股本本身不可靠：
      · 002371 侥幸成立（隐含股本 FY2015–FY2023 恒 718.3M）；
      · **300750 直接失效**——Low/High 的隐含股本被钉死在 4540.3M，而 Avg 的隐含股本自己在漂
        （FY2023 4384.3M / FY2024 4962.3M / FY2025 5160.6M / FY2026 4507.5M），
        FY2024 的 4962M 既不等于当前股本也不等于期内加权。用它做分母是引入新的错。
    而且即便重算成功，EPS 的 beat/miss 会与净利润完全同号（分子分母都是净利润的线性变换），
    这条腿本就不含独立信息。

    所以：**已披露期的 EPS 不参与兑现比较**（不画实际值、不进统计）；
    未来期的 eps.avg 保留——那里分母是当前股本，与市值同口径，第二章 forward PE 要用。
    收入与净利润两条腿不受影响，它们的实际值与预期同源同口径。"""
    n = 0
    for r in rows:
        b = r.get("eps")
        if not b or r.get("is_future"):
            continue
        if b.get("actual") is not None or b.get("pre_est") is not None:
            b["actual"] = None
            b["pre_est"] = None
            b["hist_disabled"] = "FMP 预期 EPS 与实际 EPS 分母不同源（预期用固定/漂移的隐含股本，实际用当年报告加权股本），历史兑现不可比"
            n += 1
    if n:
        gaps.append("%s·EPS：%d 期已下线历史兑现比较（FMP 预期与实际 EPS 分母不同源）；"
                    "收入/净利润两条腿不受影响，未来期 EPS 预测区间仍保留供 forward PE 用" % (period, n))


def sanity_check_series(rows, gaps, period):
    """FMP 远端年份常因覆盖骤降出现「收入涨、EPS 反跌」的脏数据
    （实测 NVDA FY2030 epsAvg 12.29 < FY2029 15.32，n 从 27 掉到 13）。
    不修数，只标记——页面把该期画灰并提示，避免拿脏数据做 forward PE。"""
    prev = None
    for r in rows:
        if not r.get("is_future"):
            prev = r
            continue
        e, rev = r.get("eps") or {}, r.get("rev") or {}
        if prev and prev.get("is_future"):
            pe_, prev_rev = prev.get("eps") or {}, prev.get("rev") or {}
            if (e.get("avg") and pe_.get("avg") and rev.get("avg") and prev_rev.get("avg")
                    and e["avg"] < pe_["avg"] * 0.9 and rev["avg"] > prev_rev["avg"]):
                r["suspect"] = "收入环比上行但 EPS 均值较上期跌 %.0f%%（覆盖 %s→%s 家），疑为 FMP 远端样本切换" % (
                    (1 - e["avg"] / pe_["avg"]) * 100, pe_.get("n"), e.get("n"))
                gaps.append("%s(%s) %s" % (r["label"], period, r["suspect"]))
        prev = r


# ---------------------------------------------------------------- 统计
def hit_stats(rows, metric, inline_band):
    """两套独立命中率：
      · beat_rate  = 实际 vs 一致预期点 的方向命中（传统口径）
      · in_range_rate = 实际落在券商 Low–High **区间内**的比例（区间口径，衡量卖方"敢不敢给区间"）
    区间命中率低 = 券商区间给窄了/系统性偏，比 beat_rate 更能说明预测质量。"""
    done = [r for r in rows if not r.get("is_future") and r.get(metric) and r[metric].get("actual") is not None]
    n_syn_all = sum(1 for r in done if r[metric].get("synthetic"))
    done = [r for r in done if not r[metric].get("synthetic")]     # 合成区间排除出**全部**兑现统计
    scored = [r for r in done if r[metric].get("verdict")]
    if not scored:
        return None
    beat = sum(1 for r in scored if r[metric]["verdict"] == "beat")
    miss = sum(1 for r in scored if r[metric]["verdict"] == "miss")
    inline = sum(1 for r in scored if r[metric]["verdict"] == "inline")
    def _agg(vals):
        if not vals:
            return {"n": 0, "avg": None, "median": None}
        v = sorted(vals); m = len(v) // 2
        return {"n": len(v), "avg": round(sum(v) / len(v), 2),
                "median": round(v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2, 2)}
    # 两个基准不是同一个东西，混起来求均值没有统计含义
    # （实测 002371 季度 EPS：basis=pre 的 15 期均值 +24.5%，basis=avg 的 13 期 +11.6%，混出的 18.5% 不对应任何真实口径）
    vs_pre = _agg([r[metric]["surp_vs_pre"] for r in scored if r[metric].get("surp_vs_pre") is not None])
    vs_avg = _agg([r[metric]["surp_vs_avg"] for r in scored if r[metric].get("surp_vs_avg") is not None])
    prim = vs_pre if vs_pre["n"] else vs_avg
    surps = [r[metric]["surp_vs_pre"] if r[metric].get("surp_vs_pre") is not None
             else r[metric]["surp_vs_avg"] for r in scored]
    median = prim["median"]
    # 合成区间已在 mark_synthetic_bands 里被剥夺 in_range/range_pos，这里自然不计入
    ranged = [r for r in done if r[metric].get("in_range") is not None]
    streak, last = 0, None
    for r in reversed(scored):
        if last is None:
            last = r[metric]["verdict"]
        if r[metric]["verdict"] == last and last in ("beat", "miss"):
            streak += 1
        else:
            break
    pos_all = [r[metric]["range_pos"] for r in done if r[metric].get("range_pos") is not None]
    pos = [x for x in pos_all if 0 <= x <= 1]
    n_above = sum(1 for x in pos_all if x > 1)
    n_below = sum(1 for x in pos_all if x < 0)
    return {
        "metric": metric, "n": len(scored), "beat": beat, "miss": miss, "inline": inline,
        "beat_rate": round(beat / len(scored) * 100, 1),
        "vs_pre": vs_pre, "vs_avg": vs_avg,           # 分列，别混
        "avg_surp": prim["avg"], "median_surp": median,
        "surp_basis": "pre" if vs_pre["n"] else "avg",
        "streak": streak, "streak_dir": last if streak else None,
        "in_range_n": len(ranged),
        "in_range_rate": (round(sum(1 for r in ranged if r[metric]["in_range"]) / len(ranged) * 100, 1)
                          if ranged else None),
        # 只对**落在区间内**的样本求平均位置；越界的单独计数，别混进均值（越界值可到 1010）
        "avg_range_pos": round(sum(pos) / len(pos), 3) if pos else None,
        "n_pos_inrange": len(pos), "n_above_hi": n_above, "n_below_lo": n_below,
        "synthetic_excluded": n_syn_all,      # 因合成区间被排除出全部统计的期数（页面要说明）
        "degenerate_excluded": sum(1 for r in done if r[metric].get("degenerate")),
        "inline_band_pct": inline_band,
    }


def attach_price_reaction(rows, kline_path, metric="eps"):
    """给每个已披露期算财报后 +1周 / +4周 涨跌幅。
    「beat 但不涨」是本 skill 反复强调的信号（002371 阶段①），必须画出来。"""
    if not kline_path:
        return ["未提供 --kline → 不叠财报后股价反应"]
    if not os.path.exists(kline_path):
        return ["kline 文件不存在(%s) → 不叠股价反应" % kline_path]
    try:
        kd = json.load(open(kline_path, encoding="utf-8"))
        weekly = kd if isinstance(kd, list) else (kd.get("weekly") or [])
        pts = sorted((w["d"], fnum(w.get("c"))) for w in weekly if w.get("d") and fnum(w.get("c")))
    except Exception as e:
        return ["kline 解析失败(%s) → 不叠股价反应" % type(e).__name__]
    if not pts:
        return ["kline 为空 → 不叠股价反应"]
    hit, out_of_window = 0, 0
    for r in rows:
        if r.get("is_future"):
            continue
        b = r.get(metric) or {}
        if b.get("actual") is None:
            continue
        # 锚点必须是财报**实际公布日**（earnings 的 date），不是报告期末。
        # 年报期末 12-31 与实际公布日（次年 3-4 月）差 3 个月，用期末会把股价反应算到完全错误的时间段。
        # 只有 pre_est_date（来自 earnings，即公布日）可信；没有就跳过这一期，**不用期末凑合**。
        ref = r.get("pre_est_date")
        if not ref:
            continue
        # ⚠️ 财报日早于 K 线窗口起点时，最近邻会全部落到**第一根 K 线**上，
        #    产出一串一模一样的假涨跌幅（实测 002371 的 21Q4/22Q1/22Q4 都被算成 -8.0%）。
        #    窗口外的期一律跳过，不猜。
        if ref < pts[0][0]:
            out_of_window += 1
            continue
        i = next((k for k, (dd, _) in enumerate(pts) if dd >= ref), None)
        if i is None:
            continue
        base = pts[i][1]
        for horizon, key in ((1, "px_1w"), (4, "px_4w")):
            j = i + horizon
            if j < len(pts) and base:
                r[key] = round((pts[j][1] / base - 1) * 100, 2)
        hit += 1
        v = b.get("verdict")
        if v == "beat" and r.get("px_1w") is not None and r["px_1w"] < 0:
            r["divergence"] = "beat_but_down"
        elif v == "miss" and r.get("px_1w") is not None and r["px_1w"] > 0:
            r["divergence"] = "miss_but_up"
    notes = []
    if out_of_window:
        notes.append("%d 个财报期早于 K 线窗口起点(%s) → 这些期不算股价反应（避免全部落到第一根K线产生假值）"
                     % (out_of_window, pts[0][0]))
    if not hit:
        notes.append("kline 窗口与财报期完全不重叠 → 股价反应为空")
    return notes


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="FMP 券商预期区间 + 兑现记录 + 未来预期延展")
    ap.add_argument("--ticker", required=True, help="裸代码或带后缀，如 300750 / 0700 / NVDA")
    ap.add_argument("--market", required=True, choices=["A", "HK", "US", "KR"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--kline", help="kline_weekly.json，用于叠财报后股价反应")
    ap.add_argument("--page-currency", help="page_model.meta.currency，用于报告币种一致性闸")
    ap.add_argument("--quarters-limit", type=int, default=40)
    ap.add_argument("--years-limit", type=int, default=16)
    a = ap.parse_args()

    cfg = load_cfg()
    sym = to_fmp_symbol(a.ticker, a.market)
    asof = dt.date.today().isoformat()
    gaps = []
    print("[FMP] symbol=%s market=%s asof=%s" % (sym, a.market, asof), file=sys.stderr)

    # ---- 实际值 + 财报前一致预期点
    act_y, g = pull_actuals(cfg, sym, "annual"); gaps += g
    act_q, g = pull_actuals(cfg, sym, "quarter"); gaps += g
    pre_map, pre_raw, g = pull_pre_estimates(cfg, sym); gaps += g

    reported_ccy = next((v.get("ccy") for v in list(act_y.values()) + list(act_q.values()) if v.get("ccy")), None)
    ccy_warn = None
    if a.page_currency and reported_ccy and a.page_currency.upper() != reported_ccy.upper():
        ccy_warn = ("FMP 报告币种=%s，页面展示币种=%s —— 本节金额为 %s，"
                    "与页面其余 *_yi 不同币，不可直接相加/比市值。"
                    % (reported_ccy, a.page_currency.upper(), reported_ccy))
        gaps.append(ccy_warn)

    # ---- 预期区间（历史+未来一条轴）
    quarters, g1 = pull_estimates(cfg, sym, "quarter", asof, act_q, pre_map, a.quarters_limit)
    years, g2 = pull_estimates(cfg, sym, "annual", asof, act_y, pre_map, a.years_limit)
    gaps += g1 + g2

    # 股价反应只做季度：季度期能从 earnings 拿到**实际公布日**；
    # 年度期只有报告期末（12-31），距年报实际公布（次年 3-4 月）差 3 个月，用它做锚点必错。
    # 锚在**收入**不是 EPS：EPS 历史兑现已整体下线(预期与实际分母不同源)，
    # eps.actual 恒为 None → 用 eps 当锚会让每一期都被跳过，产出假的
    # 「kline 窗口与财报期完全不重叠」(2026-08-12 PLTR 实测踩过)。
    # 收入也正是本 skill 认可的兑现口径（只看收入与净利润）。
    gaps += attach_price_reaction(quarters, a.kline, "rev")

    stats = {p: {m: hit_stats(rows, m, cfg["inline_band"]) for m in METRICS}
             for p, rows in (("quarter", quarters), ("annual", years))}

    # ---- 目标价 / 评级（实测仅美股）
    targets = None
    tc, err = get(cfg, "price-target-consensus", symbol=sym)
    if isinstance(tc, list) and tc:
        t = tc[0]
        targets = {"high": fnum(t.get("targetHigh")), "low": fnum(t.get("targetLow")),
                   "consensus": fnum(t.get("targetConsensus")), "median": fnum(t.get("targetMedian"))}
    elif err:
        gaps.append("price-target-consensus 失败: %s" % err)

    grades = None
    gc, err = get(cfg, "grades-consensus", symbol=sym)
    if isinstance(gc, list) and gc:
        g0 = gc[0]
        grades = {k: g0.get(k) for k in ("strongBuy", "buy", "hold", "sell", "strongSell", "consensus")}
    elif err:
        gaps.append("grades-consensus 失败: %s" % err)

    grades_hist = []
    gh, _ = get(cfg, "grades-historical", symbol=sym, limit=24)
    if isinstance(gh, list):
        for r in sorted(gh, key=lambda x: str(x.get("date", ""))):
            grades_hist.append({"date": str(r.get("date", ""))[:10],
                                "sb": r.get("analystRatingsStrongBuy"), "b": r.get("analystRatingsBuy"),
                                "h": r.get("analystRatingsHold"), "s": r.get("analystRatingsSell"),
                                "ss": r.get("analystRatingsStrongSell")})

    out = {
        "symbol": sym, "ticker": a.ticker, "market": a.market, "asof": asof, "schema": 2,
        "src": "FMP /stable (analyst-estimates · income-statement · earnings · price-target-consensus · grades)",
        "unit": "亿元(原报告币种)", "reported_currency": reported_ccy,
        "page_currency": (a.page_currency or "").upper() or None, "currency_warn": ccy_warn,
        "box_caliber": ("箱体=券商预测 Low–High 全距（FMP 只给最低/均值/最高，非四分位）；"
                        "横线=区间均值(当前快照)；空心圈=财报前一致预期(point-in-time，不被事后修订)；"
                        "五角星=实际披露值(带圈=落在券商区间外)；n=覆盖家数；n<%d 画虚线箱表示样本过薄。"
                        "如需真四分位箱线图，需补逐家机构预测（港股走 etnet，A股走 AlphaPai/iFind）。" % cfg["thin_n"]),
        "quarters": quarters, "years": years,
        "stats": stats, "pre_estimates_raw": pre_raw,
        "targets": targets, "grades": grades, "grades_hist": grades_hist,
        "gaps": gaps,
    }

    for _rows in (quarters, years):          # _r 是合成带探测的内部中间量，不落盘
        for _r0 in _rows:
            for _m in METRICS:
                if isinstance(_r0.get(_m), dict):
                    _r0[_m].pop("_r", None)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---- 控制台自查
    def fmt(b, unit=""):
        if not b:
            return "—"
        f = lambda v: "—" if v is None else ("%.1f" % v if abs(v) >= 10 else "%.2f" % v)
        s = "%s–%s(均%s)" % (f(b.get("lo")), f(b.get("hi")), f(b.get("avg")))
        if b.get("actual") is not None:
            s += " 实际%s" % f(b["actual"])
            if b.get("verdict"):
                s += "[%s%s]" % (b["verdict"], "" if b.get("in_range") is None else ("·区间内" if b["in_range"] else "·区间外"))
        return s + unit

    print("\n=== 年度：券商区间 vs 实际 → %s" % a.out)
    for r in years[-9:]:
        print("  %-7s %-6s 收入 %-34s | EPS %s" % (r["label"], "未来" if r["is_future"] else "已披露",
                                                 fmt(r.get("rev"), "亿"), fmt(r.get("eps"))))
    print("\n=== 季度（近 8 期）")
    for r in quarters[-8:]:
        print("  %-7s %-6s 收入 %-34s | EPS %s" % (r["label"], "未来" if r["is_future"] else "已披露",
                                                 fmt(r.get("rev"), "亿"), fmt(r.get("eps"))))
    for per in ("annual", "quarter"):
        for m in METRICS:
            s = stats[per][m]
            if not s:
                continue
            print("\n=== %s·%s 兑现统计（%d 期，inline 带 ±%.1f%%）"
                  % ("年度" if per == "annual" else "季度", {"rev": "收入", "np": "净利润", "eps": "EPS"}[m],
                     s["n"], s["inline_band_pct"]))
            print("  beat %d / miss %d / inline %d → 方向命中率 %.1f%%（基准=%s）"
                  % (s["beat"], s["miss"], s["inline"], s["beat_rate"],
                     "财报前一致预期" if s["surp_basis"] == "pre" else "区间均值"))
            for lbl, k in (("vs 财报前预期", "vs_pre"), ("vs 区间均值", "vs_avg")):
                a2 = s[k]
                if a2["n"]:
                    print("    %s：n=%d 平均 %+.2f%% 中位 %+.2f%%" % (lbl, a2["n"], a2["avg"], a2["median"]))
            if s["in_range_rate"] is not None:
                print("  区间命中率 %.1f%%（%d 期）| 区间内样本平均位置 %s（n=%d，50%%=正中）| 越上沿 %d 期 / 越下沿 %d 期"
                      % (s["in_range_rate"], s["in_range_n"], s["avg_range_pos"],
                         s["n_pos_inrange"], s["n_above_hi"], s["n_below_lo"]))
            if s["synthetic_excluded"] or s["degenerate_excluded"]:
                print("  已剔除：合成区间 %d 期 / 退化区间 %d 期" % (s["synthetic_excluded"], s["degenerate_excluded"]))
            if s["streak"]:
                print("  当前连续 %d 期 %s" % (s["streak"], "超预期" if s["streak_dir"] == "beat" else "低于预期"))
    div = [r for r in quarters if r.get("divergence")]
    if div:
        print("\n⚠ 预期与股价背离 %d 次（beat不涨/miss不跌，读图重点）：%s"
              % (len(div), "、".join("%s %s %+.1f%%" % (r["label"], r["divergence"], r.get("px_1w", 0)) for r in div[-6:])))
    if targets:
        print("\n=== 目标价 低%s / 中位%s / 高%s" % (targets["low"], targets["median"], targets["high"]))
    if gaps:
        print("\n缺口（不编造，页面按缺失处理）:")
        for g in gaps[:14]:
            print("  ·", g)


if __name__ == "__main__":
    main()
