"""篮子内分层（龙头/中军/后排）+ 每只票的 K 线方位。

两件事都只吃 `.klinecache` 里已经有的日线，**零额外请求**——那份缓存本来就是为了
算换手强度和离散度抓的，全篇成分股都在里面。

方位口径**照抄 `kline-reviewer` skill**，不自己发明（该 skill 在
`~/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/<uuid>/<uuid>/skills/kline-reviewer`）：
  · 多头排列 = MA5>MA10>MA20>MA60 且四根全向上          （references/moving-averages.md §2.1）
  · 空头排列 = MA5<MA10<MA20<MA60 且四根全向下          （同上 §2.2）
  · 粘合     = MA5/10/20 三根价格差 < 3%                （同上 §2.3）
  · 发散     = |MA5−MA60|/MA60 > 20% 或超该股历史 P90    （同上 §2.4）
  · 周线排列 × 日线排列 → 9 种状态                       （references/state-judgment.md §v2 矩阵）

为什么必须双周期：只看日线会把「周线多头里的一次回踩」误判成转空。
kline-reviewer 那张矩阵的第一列就是周线，日线只决定这一段在周线趋势里的位置。
"""
from __future__ import annotations

import datetime as dt
import statistics
from typing import Any, Dict, List, Optional, Sequence

BUNCH_PCT = 0.03      # 粘合阈值：MA5/10/20 极差 ÷ 收盘 < 3%
SPREAD_PCT = 0.20     # 发散阈值：|MA5−MA60| ÷ MA60 > 20%
SPREAD_Q = 80         # 或超过该股自身历史分位
SLOPE_LOOKBACK = 5    # 斜率：MA 相对 N 根前


def _ma(cl: Sequence[float], n: int) -> Optional[float]:
    return statistics.fmean(cl[-n:]) if len(cl) >= n else None


def _ma_series(cl: Sequence[float], n: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for i in range(len(cl)):
        out.append(statistics.fmean(cl[i - n + 1:i + 1]) if i + 1 >= n else None)
    return out


def _weekly(bars: Sequence[Dict[str, Any]]) -> List[float]:
    """日线 → 周线收盘（每个 ISO 周取最后一根）。"""
    byw: Dict[Any, float] = {}
    for b in bars:
        try:
            d = dt.date.fromisoformat(b["d"])
        except Exception:
            continue
        byw[d.isocalendar()[:2]] = float(b["c"])
    return [byw[k] for k in sorted(byw)]


def _arrange(cl: Sequence[float], spans: Sequence[int]) -> Dict[str, Any]:
    """一组均线的排列形态。返回 {kind, mas, slopes, spread}。"""
    mas = [_ma(cl, n) for n in spans]
    if any(m is None for m in mas):
        return {"kind": None, "why": f"K 线不足 {max(spans)} 根"}
    slopes = []
    for n in spans:
        ser = _ma_series(cl, n)
        prev = ser[-1 - SLOPE_LOOKBACK] if len(ser) > SLOPE_LOOKBACK else None
        slopes.append(None if prev is None else (ser[-1] - prev))
    last = cl[-1] or 1.0
    short = mas[:3]                                   # MA5/10/20 判粘合
    bunch = (max(short) - min(short)) / abs(last)
    spread = abs(mas[0] - mas[-1]) / abs(mas[-1]) if mas[-1] else 0.0

    up = all(s is not None and s > 0 for s in slopes)
    dn = all(s is not None and s < 0 for s in slopes)
    desc = mas == sorted(mas, reverse=True)
    asc = mas == sorted(mas)

    # 短端有序但被长端压着 / 顶着，是最常见也最有含义的两种形态，
    # 并进「混乱」就把「反抽未站上季线」和「回调没破季线」这两句话丢了。
    short_desc = len(mas) >= 3 and mas[0] > mas[1] > mas[2]
    short_asc = len(mas) >= 3 and mas[0] < mas[1] < mas[2]
    long_above = len(mas) >= 4 and mas[2] < mas[3]     # MA20 < MA60，长端压着
    long_below = len(mas) >= 4 and mas[2] > mas[3]

    if desc and up:
        kind = "多头"
    elif asc and dn:
        kind = "空头"
    elif bunch < BUNCH_PCT:
        kind = "粘合"
    elif desc:
        kind = "偏多"                                  # 排列对但斜率没全跟上
    elif asc:
        kind = "偏空"
    elif short_desc and long_above:
        kind = "短多长空"                              # 反抽：短端翻多，还在季线下
    elif short_asc and long_below:
        kind = "短空长多"                              # 回调：短端转弱，季线仍托着
    else:
        kind = "混乱"
    # 查表只用三桶（对齐 kline-reviewer 的 3×3 矩阵），细形态留给 modifier 与文案
    bucket = "多" if kind in ("多头", "偏多") else ("空" if kind in ("空头", "偏空") else "平")
    return {"kind": kind, "bucket": bucket, "mas": [round(m, 2) for m in mas],
            "bunch": round(bunch, 4), "spread": round(spread, 4),
            "slopes_up": up, "slopes_dn": dn}


def _spread_pct_rank(cl: Sequence[float]) -> Optional[float]:
    """当前 |MA5−MA60|/MA60 在自身历史里的分位。"""
    s5, s60 = _ma_series(cl, 5), _ma_series(cl, 60)
    hist = [abs(a - b) / abs(b) for a, b in zip(s5, s60)
            if a is not None and b is not None and b]
    if len(hist) < 60:
        return None
    now = hist[-1]
    return round(sum(1 for v in hist if v <= now) / len(hist) * 100, 1)


# 周线 × 日线（各归三桶 多/平/空）→ 9 态，一格不差地对齐 kline-reviewer
# references/state-judgment.md 的 v2 矩阵。细形态（短多长空/短空长多/粘合/发散）
# 不进查表，只做 modifier——否则 64 种组合列不完，也没法审。
STATE = {
    ("多", "多"): "主升·共振",
    ("多", "平"): "主升中继·蓄势",
    ("多", "空"): "回调升级风险",
    ("平", "多"): "转势·右侧启动",
    ("平", "平"): "震荡·待方向",
    ("平", "空"): "震荡偏弱·向下试探",
    ("空", "多"): "底部反转·右侧启动",
    ("空", "平"): "底部粘合·等右侧金叉",
    ("空", "空"): "主跌·共振",
}

# modifier：(周线桶, 日线细形态) → 覆写成更准的说法
REFINE = {
    ("空", "短多长空"): "底部反抽·未站上季线",
    ("平", "短多长空"): "震荡转强·未站上季线",
    ("多", "短空长多"): "主升中回调·季线未破",
    ("平", "短空长多"): "震荡转弱·季线未破",
    ("空", "混乱"): "主跌中反抽·无结构",
    ("多", "混乱"): "主升中结构转乱",
}


def ma_posture(bars: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """一只票的方位。bars = KlineStore 的日线 [{d,h,l,c,v}]。"""
    cl = [float(b["c"]) for b in bars if b.get("c")]
    if len(cl) < 70:
        return {"state": None, "why": f"日线仅 {len(cl)} 根，不足 70 根算不出 MA60"}
    dd = _arrange(cl, (5, 10, 20, 60))
    wk = _weekly(bars)
    ww = _arrange(wk, (5, 10, 20, 60)) if len(wk) >= 60 else _arrange(wk, (5, 10, 20))
    if not dd.get("kind") or not ww.get("kind"):
        return {"state": None, "why": dd.get("why") or ww.get("why") or "均线算不出"}

    pr = _spread_pct_rank(cl)
    state = REFINE.get((ww["bucket"], dd["kind"])) or STATE.get((ww["bucket"], dd["bucket"]))
    if state is None:
        state = f"{ww['kind']}周线 / {dd['kind']}日线"
    # 发散过头时升格（kline-reviewer §2.4：P90 或 >20% 不追高）
    hot = (pr is not None and pr >= SPREAD_Q) or dd["spread"] > SPREAD_PCT
    if hot and state == "主升·共振":
        state = "主升末期·过热"
    elif hot and state == "主跌·共振":
        state = "主跌末段·超跌"

    return {"state": state, "d": dd["kind"], "w": ww["kind"],
            "spread_pct": round(dd["spread"] * 100, 1), "spread_rank": pr,
            "ma": dd["mas"], "n_days": len(cl), "n_weeks": len(wk),
            "d_kind": dd["kind"], "w_kind": ww["kind"],
            "why": f"周线{ww['kind']} × 日线{dd['kind']}"
                   + (f" · MA5-MA60 张开 {dd['spread']*100:.0f}%"
                      + (f"（自身 P{pr:.0f}）" if pr is not None else "") if hot else "")}


def tier_members(members: Sequence[Dict[str, Any]], per: Dict[str, Dict[str, Any]],
                 lead_q: float = 0.8, mid_q: float = 0.667) -> Dict[str, Dict[str, Any]]:
    """篮子内分三层。判据全部随标签一起返回，不给裸标签。

    **龙头**＝这条线的涨幅由谁定义：窗口内累计超额排前 20%，且 β≥1（跟得动还放大）。
             一只都不满足时退到「超额第一名」，并在 basis 里写明 β 不够。
    **中军**＝自由流通市值前 1/3 且不是龙头：盘子扛得住，钱进来先买它。
    **后排**＝其余。弹性可能最大，但要靠前面两层先动。

    为什么不用市值直接分层：龙头是**行情属性**不是规模属性。市值最大的常常是中军
    （阳光实测在 8 条 AI 电力篮子里市值排第 1，但同期超额是负的，那就不是龙头）。
    """
    ms = [m for m in members if m.get("code")]
    if not ms:
        return {}
    code = lambda m: str(m.get("code") or "").split(".")[0]
    cums = [(code(m), (per.get(code(m)) or {}).get("cum")) for m in ms]
    have = [(c, v) for c, v in cums if v is not None]
    out: Dict[str, Dict[str, Any]] = {}
    if not have:
        for m in ms:
            out[code(m)] = {"tier": "后排", "basis": "无累计超额数据，未分层"}
        return out

    vals = sorted(v for _c, v in have)
    cut = vals[min(len(vals) - 1, int(len(vals) * lead_q))]
    caps = sorted((m.get("float_mktcap") or 0) for m in ms)
    capcut = caps[min(len(caps) - 1, int(len(caps) * mid_q))]

    # ★龙头必须是绝对涨的。整条线都在跌时，前 20% 分位照样是负数，
    #   把一只超额 −10% 的票叫「龙头」是错的——那种情况下**这条线就是没有龙头**，
    #   而「没有龙头」本身就是结论：钱还没进来，或者进来了又走了。
    leads = [c for c, v in have if v >= cut and v > 0
             and (per.get(c) or {}).get("beta") is not None and per[c]["beta"] >= 1.0]
    headless = not leads
    best_c, best_v = max(have, key=lambda t: t[1])

    for m in ms:
        c = code(m)
        p = per.get(c) or {}
        cum, beta = p.get("cum"), p.get("beta")
        cap = m.get("float_mktcap") or 0
        if headless and c == best_c:
            out[c] = {"tier": "相对最强", "headless": True,
                      "basis": f"超额 {best_v:+.0f}%"
                               + (f" · β{beta:.2f}" if beta is not None else "")
                               + "　本篮子无龙头：超额最高的这只也是负的，钱没进来"}
            continue
        if c in leads:
            b = (f"超额 {cum:+.0f}%" if cum is not None else "超额不可得")
            b += f" · β{beta:.2f}" if beta is not None else " · β不可得"
            if beta is None or beta < 1.0:
                b += "（β 未达 1，按超额第一名定）"
            out[c] = {"tier": "龙头", "basis": b}
        elif cap >= capcut:
            out[c] = {"tier": "中军", "basis": f"自由流通 {cap/1e8:.0f} 亿（前 1/3）"
                      + (f" · 超额 {cum:+.0f}%" if cum is not None else "")}
        else:
            out[c] = {"tier": "后排", "basis": f"自由流通 {cap/1e8:.0f} 亿"
                      + (f" · 超额 {cum:+.0f}%" if cum is not None else "")}
    if headless:
        for v in out.values():
            v["headless"] = True
    return out
