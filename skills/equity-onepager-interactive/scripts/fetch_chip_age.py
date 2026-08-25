# -*- coding: utf-8 -*-
"""
fetch_chip_age.py — 1.6 节「筹码龄结构」取数与建模
==============================================================================
★ 口径以用户既有的《沪深300+中证500 全生命周期筹码结构》为标准（2026-08-08 对齐）。
   该页口径 = 同花顺「筹码龄分析」复刻（档位 2/10/100 · 系数 1.0），已对客户端校准
   （2026-07-24 对表 002138：四档 4/4 精确、均龄 31.75 vs 客户端 31.74）。
   **本脚本按该标准实现，不自创口径。**

──────────────────────────── 模型 ────────────────────────────
成本转移衰减：当日换手 h_t 的筹码龄归零、存量 ×(1−h_t)，自上市首日累积；
上市前原始筹码计入长线档、龄按上市天数累计。

  逐批权重  w_i(T) = h_i · Π_{j=i+1..T}(1−h_j)
  原始残余  w_0(T) = Π_{j=start..T}(1−h_j)          ← 龄 = 距起点天数，入长线档
  总和恒为 1（归纳法：全体先 ×(1−h_T)，再补进 h_T）

**三条日度恒等式**（与逐批展开等价，可用于自检）：
  ① 全书均龄   T_t = (1−h_t)·(T_{t−1}+1)      → ΔT = 1 − h_t·(T_{t−1}+1)
     （日调整系数 (1−h) 是**乘在 (T+1) 上的因子、不是加项**；同样 1% 换手，
       砸在均龄 300 日的票上抹掉 3 天，砸在 30 日的票上只抹掉 0.3 天）
  ② 长线占比   ΔL_t = a₁₀₀ − h_t·L_{t−1}      = 老化流入 − 换手流出
  ③ 长线均龄   A_t = [(A_{t−1}+1)·L_{t−1} + 100·a₉₉] / (L_{t−1}+a₉₉)

──────────────────────────── 四档与两族指标 ────────────────────────────
档位（交易日）：超短 [0,2) · 短 [2,10) · 中 [10,100) · 长 [100,∞)
  · **真实均龄** = 逐批加权 Σw·age（所有相关性用它）
  · **同花顺均龄** = 四档占比 × 中点 (1/6/55/365)   ← 与客户端对表用这个
  · **长钱** = 龄≥100 日（机构/长线代理变量）；**中短** = 龄 2–99 日（热钱代理变量）
    超短档均龄恒在 0–1、无信息量，**不单列**
  · 分档均龄 = 该档内逐批加权 Σw·age / Σw
  · p720 = 当前真实均龄在过去 720 日中的分位（筹码温度计）

**为什么必须拆**：一条总均龄分不开两种成因——结构（长/中短此消彼长）与总量（两档一起变老/变年轻）。
参考页实测近 250 日里 572 只由结构主导、221 只由总量主导，**157 只(20%) 两项方向相反**，
这类票单看一条总均龄必然误判。

──────────────────────────── 已知边界（必须写进页面）────────────────────────────
· 四档占比与均龄**全部依赖「换手按比例打在所有批次上」(λ=1)**。
  分档换手率由价量**不可识别**：每天只有一条会计等式
  `超短占比·s超短 + 中短占比·s中短 + 长线占比·s长线 = h_t`，一个方程三个未知数；
  加再多天也是每天新增一个方程一组未知数，自由度不减。要定解须引入模型外观测
  （股东户数、龙虎榜、前十大流通股东变动、大宗交易）。
· λ 从 1.0 压到 0.3 的水平漂移÷自身波幅：中短均龄 12% < 占比 18% < 真实均龄 64% < **长线均龄 82%**
  （无界档让假设逐日复利），但 |Δρ(价,·)| 中位仅 0.03–0.10。
  → **水平值只当口径参考、跨股比较要同口径；方向、斜率、拐点、相关性才可直接采信。**
· 长线档只有一个入口（中线筹码熬过 100 日线）和一个出口（被换手卖掉），
  **不存在「长钱主动买入」路径** → 长线占比上升永远是被动的。
  真正的长钱进场表现为两段式：先看**中短占比**抬升（接货），100 个交易日后才轮到长线占比接棒。

用法:
  python3 scripts/fetch_chip_age.py --ticker 002371 --market A \\
      --out _workspace/002371/chip_age.json [--ifind-check]
  python3 scripts/fetch_chip_age.py --calibrate 002138        # 与同花顺对表自检
"""
import argparse, json, math, os, subprocess, sys

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)

# 档位（交易日）与同花顺均龄的档内中点 —— 标准口径，不要改
EDGES = [0, 2, 10, 100]                 # 超短 / 短 / 中 / 长
MIDPTS = [1, 6, 55, 365]
BAND_NAMES = ["超短 <2日", "短 2–10日", "中 10–100日", "长 >100日"]
LONG_D = 100                            # 长钱门槛
MID_LO = 2                              # 中短 = [2,100)
TURNOVER_CAP = 0.99
P_WIN = 720                             # 筹码温度计窗口
IFIND_BRIDGE = os.path.expanduser("~/.openclaw/workspace/tools/ifind-bridge.js")


def fnum(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- 取数
def fetch_daily(ticker, market, start):
    """日频前复权 + 换手率。起点尽量早（模型自上市首日累积）。"""
    import warnings, time
    warnings.filterwarnings("ignore")
    import akshare as ak
    s = start.replace("-", "")
    code = str(ticker).split(".")[0]
    if market == "US":
        raise SystemExit("!! 筹码龄模型依赖换手率(流通股本口径)，美股无可比口径，本节对美股不出")

    # ⚠️ 两个源的换手率**单位不同**，静默错误高发处：
    #    新浪 turnover = 小数(0.011772)，自带 outstanding_share；东财 换手率 = 百分数(1.1772)
    #    实测两者与 iFind 逐日 4 位小数完全一致。新浪作主源（更稳、给流通股本）。
    def _sina():
        if market != "A":
            raise RuntimeError("新浪腿仅 A 股")
        pre = "sh" if code.startswith(("6", "9")) else "sz"
        df = ak.stock_zh_a_daily(symbol=pre + code.zfill(6), start_date=s, adjust="qfq")
        out = []
        for _, r in df.iterrows():
            d, c, t = str(r["date"])[:10], fnum(r.get("close")), fnum(r.get("turnover"))
            if d and c is not None and t is not None:
                out.append({"d": d, "close": c, "h": t})
        return out, "AKShare 新浪 stock_zh_a_daily(qfq 日频；turnover=成交量/流通股本，小数口径)"

    def _east():
        fn = ak.stock_zh_a_hist if market == "A" else ak.stock_hk_hist
        sym = code.zfill(6) if market == "A" else code.zfill(5)
        df = fn(symbol=sym, period="daily", start_date=s, adjust="qfq")
        if "换手率" not in df.columns:
            raise RuntimeError("东财返回无『换手率』列")
        out = []
        for _, r in df.iterrows():
            d, c, t = str(r["日期"])[:10], fnum(r.get("收盘")), fnum(r.get("换手率"))
            if d and c is not None and t is not None:
                out.append({"d": d, "close": c, "h": t / 100.0})     # 百分数 → 小数
        return out, "AKShare 东财(qfq 日频；换手率百分数已换算为小数)"

    legs = [("新浪", _sina), ("东财", _east)] if market == "A" else [("东财", _east)]
    errs = []
    for name, leg in legs:
        for attempt in range(3):
            try:
                rows, src = leg()
                if rows:
                    rows.sort(key=lambda x: x["d"])
                    return rows, src
                errs.append("%s 返回空表" % name); break
            except Exception as e:
                errs.append("%s: %s" % (name, str(e)[:90])); time.sleep(1.2 * (attempt + 1))
    # 连乘模型缺一天整条链就错——不降级不估算
    raise SystemExit("!! 日频换手率全部取数腿失败，本节不出（不编造）：\n   " + "\n   ".join(errs[-6:]))


# ---------------------------------------------------------------- 核心：O(n) 前缀和
def chip_structure(rows, tail):
    """逐日筹码龄结构。用对数空间前缀和做 O(n)（逐批 O(n²) 在长历史上不可接受）。

    w_i(T) = h_i·Π_{j>i}(1−h_j) = u_i·S_T，其中 S_k=Π_{j≤k}(1−h_j)、u_i=h_i/S_i。
    于是任一连续批次区间的占比与龄加权和都能用 u_i、i·u_i 的前缀和 O(1) 取到；
    档位边界（age≥100 ⇔ i≤T−100）恰好是连续区间，前缀和天然适配。
    """
    n = len(rows)
    hs = []
    caps = []
    for r in rows:
        h = r["h"]
        if h > TURNOVER_CAP:
            caps.append({"d": r["d"], "raw_pct": round(h * 100, 2)})
            h = TURNOVER_CAP
        hs.append(h)

    logS = [0.0] * n          # log S_k
    acc = 0.0
    for k in range(n):
        acc += math.log1p(-hs[k])
        logS[k] = acc
    # u_i = h_i / S_i  → 用 log 空间避免下溢/上溢
    P1 = [0.0] * (n + 1)      # Σ u_i
    P2 = [0.0] * (n + 1)      # Σ i·u_i
    for i in range(n):
        u = math.exp(math.log(hs[i]) - logS[i]) if hs[i] > 0 else 0.0
        P1[i + 1] = P1[i] + u
        P2[i + 1] = P2[i] + i * u

    def rng(a, b, T):
        """批次下标 [a,b] 在第 T 日的 (占比和, 龄加权和)。a>b 返回 0。"""
        if a > b or b < 0:
            return 0.0, 0.0
        a = max(a, 0)
        ST = math.exp(logS[T])
        s1 = (P1[b + 1] - P1[a]) * ST
        s2 = ((T * (P1[b + 1] - P1[a])) - (P2[b + 1] - P2[a])) * ST
        return s1, s2

    out = []
    start_idx = max(0, n - tail)
    for T in range(n):
        if T < start_idx:
            continue
        ST = math.exp(logS[T])           # 原始残余（上市前/起点前筹码），龄 = T+1
        resid, resid_age = ST, T + 1

        # 四档：age∈[lo,hi) ⇔ i∈(T−hi, T−lo]
        bands = []
        for bi in range(4):
            lo = EDGES[bi]
            hi = EDGES[bi + 1] if bi < 3 else None
            a = 0 if hi is None else (T - hi + 1)
            b = T - lo
            s1, s2 = rng(a, b, T)
            if hi is None:               # 长档：把原始残余并进来（龄=T+1≥100 时）
                if resid_age >= LONG_D:
                    s1 += resid; s2 += resid * resid_age
            bands.append({"w": s1, "aw": s2})
        # 原始残余若还没满 100 日，归入它当时所属的档
        if resid_age < LONG_D:
            bi = 0 if resid_age < 2 else (1 if resid_age < 10 else 2)
            bands[bi]["w"] += resid; bands[bi]["aw"] += resid * resid_age

        tot = sum(b["w"] for b in bands)
        if tot <= 0:
            continue
        true_age = sum(b["aw"] for b in bands)                       # 真实均龄（总和=1，无需再除）
        ths_age = sum(b["w"] * MIDPTS[i] for i, b in enumerate(bands))   # 同花顺口径均龄
        longw = bands[3]["w"]
        midw = bands[1]["w"] + bands[2]["w"]                          # 中短 = [2,100)
        long_age = (bands[3]["aw"] / longw) if longw > 1e-12 else None
        mid_age = ((bands[1]["aw"] + bands[2]["aw"]) / midw) if midw > 1e-12 else None

        # 长线两条流量（恒等式②）：老化流入 a₁₀₀ = 第 T−100 日批次在 T 日的残余
        inflow, _ = rng(T - LONG_D, T - LONG_D, T)
        outflow = hs[T] * (out[-1]["long_pct"] / 100.0 if out else longw)

        out.append({
            "d": rows[T]["d"], "close": round(rows[T]["close"], 2), "h": round(hs[T] * 100, 4),
            "true_age": round(true_age, 2), "ths_age": round(ths_age, 2),
            "long_pct": round(longw * 100, 2), "mid_pct": round(midw * 100, 2),
            "ultra_pct": round(bands[0]["w"] * 100, 2), "short_pct": round(bands[1]["w"] * 100, 2),
            "mid_only_pct": round(bands[2]["w"] * 100, 2),
            "long_age": round(long_age, 1) if long_age else None,
            "mid_age": round(mid_age, 1) if mid_age else None,
            "inflow": round(inflow * 100, 4), "outflow": round(outflow * 100, 4),
            "resid_pct": round(resid * 100, 3),
        })
    return out, caps


def smooth_flows(series, win=20):
    """长线两条流量做 20 交易日滚动均值。
    日流量本身抖动极大（单日换手噪声），周采样后更抖，直接画会把「老化 vs 换手」的赛跑淹掉；
    平滑只用于展示，原始值保留在 inflow/outflow 里供 tooltip 与核对。"""
    n = len(series)
    for k in ("inflow", "outflow"):
        vals = [x[k] for x in series]
        for i in range(n):
            lo = max(0, i - win + 1)
            w = vals[lo:i + 1]
            series[i][k + "_ma"] = round(sum(w) / len(w), 4)


def add_percentile(series, win=P_WIN):
    """p720 筹码温度计：当前真实均龄在过去 win 日中的分位。"""
    ages = [x["true_age"] for x in series]
    for i, x in enumerate(series):
        lo = max(0, i - win + 1)
        w = ages[lo:i + 1]
        if len(w) < 20:
            x["p720"] = None
            continue
        x["p720"] = round(sum(1 for v in w if v <= x["true_age"]) / len(w) * 100, 1)


def weekly(series):
    """周线展示（计算为日度）—— 取每周最后一个交易日。"""
    out, key = [], None
    import datetime as dt
    for x in series:
        y, w, _ = dt.date.fromisoformat(x["d"]).isocalendar()
        if (y, w) != key:
            key = (y, w); out.append(x)
        else:
            out[-1] = x
    return out


def corr(a, b):
    xs = [(p, q) for p, q in zip(a, b) if p is not None and q is not None]
    if len(xs) < 20:
        return None
    n = len(xs)
    mx = sum(p for p, _ in xs) / n; my = sum(q for _, q in xs) / n
    sx = math.sqrt(sum((p - mx) ** 2 for p, _ in xs)); sy = math.sqrt(sum((q - my) ** 2 for _, q in xs))
    if sx < 1e-12 or sy < 1e-12:
        return None
    return round(sum((p - mx) * (q - my) for p, q in xs) / (sx * sy), 3)


def classify(rho, chg):
    """分型（方向感知），沿用参考页规则。"""
    if rho is None:
        return "数据不足"
    if rho <= -0.5:
        return "换手驱动"
    if rho >= 0.5:
        return "锁仓推升" if chg > 0 else "边跌边散"
    if abs(rho) < 0.3:
        return "弱关联"
    return "混合型"


# ---------------------------------------------------------------- iFind 校验
def ifind_crosscheck(ticker, rows, sample=40):
    if not os.path.exists(IFIND_BRIDGE):
        return {"ok": None, "note": "未找到 ifind-bridge.js，跳过交叉校验"}
    try:
        p = subprocess.run(["node", IFIND_BRIDGE, "stock", "get_stock_performance",
                            json.dumps({"query": "%s 近一年 换手率 收盘价" % ticker}, ensure_ascii=False)],
                           capture_output=True, text=True, timeout=180)
        answer = json.loads(json.loads(p.stdout)["data"])["answer"]
    except Exception as e:
        return {"ok": None, "note": "iFind 调用失败(%s)，跳过交叉校验" % type(e).__name__}
    ref = {}
    for line in answer.splitlines():
        parts = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(parts) < 5 or not parts[2].isdigit() or len(parts[2]) != 8:
            continue
        t = fnum(parts[4])
        if t is not None:
            ref["%s-%s-%s" % (parts[2][:4], parts[2][4:6], parts[2][6:])] = t / 100.0
    if not ref:
        return {"ok": None, "note": "iFind 未返回可解析换手率，跳过交叉校验"}
    ours = {r["d"]: r["h"] for r in rows}
    common = sorted(set(ref) & set(ours))[-sample:]
    if not common:
        return {"ok": None, "note": "无重叠日期，跳过交叉校验"}
    mx = max(abs(ref[d] - ours[d]) for d in common)
    return {"ok": mx < 5e-4, "checked_n": len(common), "max_abs_diff_pct": round(mx * 100, 4),
            "note": ("iFind 逐点校验通过：%d 个重叠交易日，换手率最大绝对偏差 %.4f 个百分点" % (len(common), mx * 100))
                    if mx < 5e-4 else
                    ("⚠️ iFind 与取数腿换手率不一致：%d 日中最大偏差 %.4f 个百分点，请人工核对后再用本节" % (len(common), mx * 100))}


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="1.6 筹码龄结构（同花顺口径复刻，档位 2/10/100）")
    ap.add_argument("--ticker"); ap.add_argument("--market", choices=["A", "HK"], default="A")
    ap.add_argument("--start", default="1999-01-01", help="尽量早；模型自上市首日累积")
    ap.add_argument("--tail-days", type=int, default=1500, help="输出多少个交易日（日度算全程）")
    ap.add_argument("--out"); ap.add_argument("--ifind-check", action="store_true")
    ap.add_argument("--calibrate", metavar="CODE", help="与同花顺对表自检（参考锚 002138：均龄 31.75 @2026-07-24）")
    a = ap.parse_args()

    tick = a.calibrate or a.ticker
    if not tick:
        sys.exit("!! 需要 --ticker 或 --calibrate")
    rows, src = fetch_daily(tick, a.market, a.start)
    series, caps = chip_structure(rows, a.tail_days)
    smooth_flows(series)
    add_percentile(series)
    if not series:
        sys.exit("!! 未算出序列")

    if a.calibrate:
        print("=== 与同花顺对表：%s（%d 个交易日，%s ~ %s）" % (tick, len(rows), rows[0]["d"], rows[-1]["d"]))
        for x in series[-3:]:
            print("  %s  同花顺口径均龄 %.2f | 真实均龄 %.2f | 四档 %.1f/%.1f/%.1f/%.1f"
                  % (x["d"], x["ths_age"], x["true_age"], x["ultra_pct"], x["short_pct"],
                     x["mid_only_pct"], x["long_pct"]))
        anchor = next((x for x in series if x["d"] == "2026-07-24"), None)
        if anchor:
            print("  ★ 2026-07-24 锚点：同花顺口径 %.2f（参考页对表值 31.75，客户端 31.74）→ 偏差 %.2f"
                  % (anchor["ths_age"], anchor["ths_age"] - 31.75))
        tot = [abs(x["ultra_pct"] + x["short_pct"] + x["mid_only_pct"] + x["long_pct"] - 100) for x in series]
        print("  四档合计与 100%% 的最大偏差：%.4f pp" % max(tot))
        return

    cur = series[-1]
    closes = [x["close"] for x in series]
    rho_true = corr(closes, [x["true_age"] for x in series])
    rho_long = corr(closes, [x["long_age"] for x in series])
    rho_mid = corr(closes, [x["mid_age"] for x in series])
    rho_longpct = corr(closes, [x["long_pct"] for x in series])
    chg = closes[-1] / closes[0] - 1 if closes[0] else 0
    gaps = []
    if caps:
        gaps.append("有 %d 个交易日换手率 >99%%（已钳制）：%s"
                    % (len(caps), "、".join("%s %.1f%%" % (c["d"], c["raw_pct"]) for c in caps[:5])))
    if cur["resid_pct"] > 5:
        gaps.append("起点前原始筹码残余 %.1f%%（>5%%）→ 请把 --start 往前推到上市首日" % cur["resid_pct"])

    out = {
        "ticker": tick, "market": a.market, "asof": rows[-1]["d"],
        "window": [rows[0]["d"], rows[-1]["d"]], "n_days": len(rows), "src": src,
        "std": "同花顺「筹码龄分析」复刻（档位 2/10/100 · 系数 1.0）；对齐用户《沪深300+中证500 全生命周期筹码结构》口径",
        "bands": {"edges": EDGES, "midpoints": MIDPTS, "names": BAND_NAMES, "long_d": LONG_D},
        "model": ("成本转移衰减：w_i(T)=h_i·Π_{j>i}(1−h_j)，起点前原始筹码 w_0=Π(1−h_j) 计入长线档(龄按天数累计)，总和恒为 1。"
                  "恒等式① 全书均龄 T_t=(1−h_t)·(T_{t−1}+1)；② 长线占比 ΔL_t=老化流入 a₁₀₀ − 换手流出 h_t·L_{t−1}"),
        "caliber": ("真实均龄=逐批加权 Σw·age（相关性用它）；同花顺均龄=四档占比×中点(1/6/55/365)，与客户端对表用它。"
                    "长钱=龄≥100日（含起点前原始筹码，机构/长线代理）；中短=龄2–99日（热钱代理）；"
                    "超短档均龄恒在0–1、无信息量，不单列。分档均龄=档内逐批加权 Σw·age/Σw。"
                    "p720=当前真实均龄在过去720日中的分位（筹码温度计）。图表周线展示、计算为日度。"),
        "limits": ("四档占比与均龄全部依赖「换手按比例打在所有批次上」(λ=1)：每天只有一条会计等式"
                   "『各档占比×各档换手率之和=当日换手率』，一个方程三个未知数，分档换手率由价量不可识别，"
                   "要定解须引入股东户数/龙虎榜/前十大流通股东变动等模型外观测。"
                   "λ 由 1.0 压到 0.3 的水平漂移÷自身波幅：中短均龄 12% < 占比 18% < 真实均龄 64% < 长线均龄 82%（无界档逐日复利），"
                   "但 |Δρ| 中位仅 0.03–0.10。→ 水平值只当口径参考、跨股比较要同口径；方向、斜率、拐点、相关性才可直接采信。"
                   "另：长线档只有一个入口（中线熬过100日线）和一个出口（被换手卖掉），不存在「长钱主动买入」路径——"
                   "长线占比上升永远是被动的；真正的长钱进场是两段式：先看中短占比抬升，100个交易日后才轮到长线接棒。"),
        "current": cur,
        "corr": {"price_true_age": rho_true, "price_long_age": rho_long,
                 "price_mid_age": rho_mid, "price_long_pct": rho_longpct},
        "regime": classify(rho_true, chg), "period_chg_pct": round(chg * 100, 1),
        "series": weekly(series),
        "ifind_check": ifind_crosscheck(tick, rows) if a.ifind_check else {"ok": None, "note": "未启用 iFind 交叉校验（--ifind-check）"},
        "gaps": gaps,
    }
    if not a.out:
        sys.exit("!! 需要 --out")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== 筹码龄结构 %s（%s ~ %s，%d 个交易日，周线输出 %d 点）→ %s"
          % (tick, out["window"][0], out["window"][1], out["n_days"], len(out["series"]), a.out))
    print("  数据源：%s" % src)
    print("\n当前（%s，收盘 %.2f）:" % (cur["d"], cur["close"]))
    print("  真实均龄 %.1f 日 | 同花顺口径 %.1f 日 | p720 分位 %s%%"
          % (cur["true_age"], cur["ths_age"], cur["p720"]))
    print("  四档占比：超短 %.1f%% / 短 %.1f%% / 中 %.1f%% / 长 %.1f%%"
          % (cur["ultra_pct"], cur["short_pct"], cur["mid_only_pct"], cur["long_pct"]))
    print("  ★结构层：长钱 %.1f%%（均龄 %s 日）| 中短 %.1f%%（均龄 %s 日）"
          % (cur["long_pct"], cur["long_age"], cur["mid_pct"], cur["mid_age"]))
    print("  长线流量：老化流入 %.3f pp/日 vs 换手流出 %.3f pp/日 → 净 %+.3f"
          % (cur["inflow"], cur["outflow"], cur["inflow"] - cur["outflow"]))
    print("\n相关性（区间涨幅 %+.1f%%）：ρ(价,真实龄)=%s | ρ(价,长钱龄)=%s | ρ(价,中短龄)=%s | ρ(价,长钱%%)=%s → 分型【%s】"
          % (out["period_chg_pct"], rho_true, rho_long, rho_mid, rho_longpct, out["regime"]))
    if gaps:
        print("\n缺口/提示：")
        for g in gaps:
            print("  ·", g)


if __name__ == "__main__":
    main()
