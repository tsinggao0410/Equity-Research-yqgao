"""叙事内部的离散度 · 共同因子解释力 · 我的 β。

回答的是「**这条线上选股重不重要**」：

  紧致（低离散、高 R²）＝ 叙事是真因子，钱进来无差别买，吃贝塔就行；
  离散（高离散、低 R²）＝ 叙事只是标签，真正驱动各票的是别的东西，
                          选错票叙事对了也不赚钱。

三个量：

  csd_daily  日均横截面标准差 = mean_t( std_i(x_i,t) )，单位 %/日
             ⚠ 必须用**日频**不用累计收益：累计方差会被窗口长度污染
               （建链早的天然方差大），日频是每日量，跨篮子可直接比。
  r2_mean    成分股超额对篮子超额回归的平均 R² = 这条叙事解释了多少波动
  beta_self  本股对篮子的 β = 叙事来了我放大多少
             （和「份额」互补：份额是权重＝钱会不会买到我，β 是弹性＝买到了涨多少）

⚠ 必须先减掉市场（默认沪深300）再算：否则全市场普涨时每条线的 R² 都很高，
  「是真因子还是标签」这个问题就问不出来了。
"""
from __future__ import annotations

import datetime as dt
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from vol_percentile import CACHE_DIR, KlineStore, SOURCES, to_symbol

MARKET = "sh000300"       # 市场因子，沪深300
MIN_DAYS = 40             # 回归样本下限，不足不出数
MIN_NAMES = 6             # 横截面下限


def market_bars(sym: str = MARKET, days: int = 1150, stale_days: int = 10) -> List[dict]:
    """市场指数日K，和个股共用一个缓存目录。"""
    f = Path(CACHE_DIR) / f"{sym}.json"
    try:
        blob = json.loads(f.read_text())
        age = (dt.date.today() - dt.date.fromisoformat(blob["fetched"])).days
        if age <= stale_days and blob.get("days", 0) >= days:
            return blob["bars"]
    except Exception:
        pass
    for _name, getter in SOURCES:
        try:
            bars = getter(sym, days)
        except Exception:
            continue
        if bars:
            Path(CACHE_DIR).mkdir(exist_ok=True)
            f.write_text(json.dumps({"fetched": dt.date.today().isoformat(),
                                     "days": days, "schema": 2, "bars": bars}))
            return bars
    return []


def _rets(bars: Sequence[dict]) -> Dict[str, float]:
    return {b["d"]: (b["c"] / a["c"] - 1.0)
            for a, b in zip(bars, bars[1:]) if a.get("c") and b.get("c")}


def _ols(y: List[float], x: List[float]) -> tuple:
    """返回 (beta, r2)。样本不足或 x 无方差时返回 (None, None)，不硬算。"""
    n = len(y)
    if n < MIN_DAYS:
        return None, None
    vx = statistics.pvariance(x)
    if vx <= 0:
        return None, None
    mx, my = statistics.fmean(x), statistics.fmean(y)
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y)) / n
    beta = cov / vx
    vy = statistics.pvariance(y)
    r2 = (cov * cov) / (vx * vy) if vy > 0 else None
    return beta, r2


def basket_dispersion(
    members: Sequence[Dict[str, Any]],
    store: KlineStore,
    self_code: str = "",
    since: Optional[str] = None,
    basket_cap: int = 60,
) -> Optional[Dict[str, Any]]:
    """算一个篮子的离散度三件套。取不到足够样本返回 None（不出半吊子数）。"""
    ranked = sorted((m for m in members if to_symbol(m.get("code"))),
                    key=lambda m: m.get("float_mktcap") or 0.0, reverse=True)
    basket = ranked[:basket_cap]
    store.ensure([m["code"] for m in basket])

    mkt = _rets(market_bars())
    if not mkt:
        return None

    # 个股超额收益 x = r − r_市场
    ex: Dict[str, Dict[str, float]] = {}
    name_of: Dict[str, str] = {}
    for m in basket:
        sym = to_symbol(m["code"])
        bars = store._load(sym) if sym else None
        if not bars:
            continue
        r = _rets(bars)
        x = {d: v - mkt[d] for d, v in r.items() if d in mkt and (since is None or d >= since)}
        if len(x) >= MIN_DAYS:
            ex[sym] = x
            name_of[sym] = m.get("name") or sym
    if len(ex) < MIN_NAMES:
        return None

    dates = sorted(set().union(*[set(v) for v in ex.values()]))

    # 篮子超额 = 当日可得成分股超额的等权均值
    xb: Dict[str, float] = {}
    csd: List[float] = []
    for d in dates:
        vals = [v[d] for v in ex.values() if d in v]
        if len(vals) < MIN_NAMES:
            continue
        xb[d] = statistics.fmean(vals)
        csd.append(statistics.pstdev(vals))
    if len(xb) < MIN_DAYS:
        return None

    common = sorted(xb)
    betas, r2s = [], []
    per: Dict[str, Dict[str, float]] = {}      # 逐只 β / R²，页面「入选理由」兜底要用
    beta_self = r2_self = None
    for sym, x in ex.items():
        ds = [d for d in common if d in x]
        if len(ds) < MIN_DAYS:
            continue
        b, r2 = _ols([x[d] for d in ds], [xb[d] for d in ds])
        if b is None:
            continue
        betas.append(b)
        per[sym[2:]] = {"beta": round(b, 2), "r2": round(r2, 2) if r2 is not None else None}
        if r2 is not None:
            r2s.append(r2)
        if self_code and sym.endswith(self_code):
            beta_self, r2_self = b, r2

    if not betas:
        return None

    # 窗口内累计超额（相对市场），点名最强最弱
    cum = []
    for sym, x in ex.items():
        v = 1.0
        for d in common:
            if d in x:
                v *= (1 + x[d])
        cum.append((name_of[sym], (v - 1) * 100))
    for sym, x in ex.items():                  # 逐只累计超额，和 β 放一起
        v = 1.0
        for d in common:
            if d in x:
                v *= (1 + x[d])
        per.setdefault(sym[2:], {})["cum"] = round((v - 1) * 100, 1)
    cum.sort(key=lambda t: t[1])
    qs = statistics.quantiles([c for _n, c in cum], n=4) if len(cum) >= 4 else None

    return {
        "window": [common[0], common[-1]], "n_days": len(common), "n_names": len(ex),
        "csd_daily": round(statistics.fmean(csd) * 100, 2),
        "r2_mean": round(statistics.fmean(r2s), 2) if r2s else None,
        "beta_self": round(beta_self, 2) if beta_self is not None else None,
        "r2_self": round(r2_self, 2) if r2_self is not None else None,
        "beta_p25": round(statistics.quantiles(betas, n=4)[0], 2) if len(betas) >= 4 else None,
        "beta_med": round(statistics.median(betas), 2),
        "beta_p75": round(statistics.quantiles(betas, n=4)[2], 2) if len(betas) >= 4 else None,
        "cum_med": round(statistics.median([c for _n, c in cum]), 1),
        "cum_q1": round(qs[0], 1) if qs else None,
        "cum_q3": round(qs[2], 1) if qs else None,
        "best": {"name": cum[-1][0], "r": round(cum[-1][1], 1)},
        "worst": {"name": cum[0][0], "r": round(cum[0][1], 1)},
        "per": per,
    }


def tightness(d: Optional[Dict[str, Any]]) -> str:
    """R² 翻成一句人话：叙事是真因子还是标签。阈值是经验值，不是统计检验。"""
    if not d or d.get("r2_mean") is None:
        return ""
    r = d["r2_mean"]
    return "齐涨齐跌·吃贝塔" if r >= 0.45 else ("半跟随·选股有用" if r >= 0.25 else "各走各的·只是标签")
