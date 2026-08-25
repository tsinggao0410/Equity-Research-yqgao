"""概念篮子的 MIX 日内波动率 —— 三年历史序列与当前分位。

调用量设计（这块原来是瓶颈，439 次请求把 gtimg 打到限流）：

  1. 历史 K 线永久缓存。历史 bar 不会变，抓过就不再抓。缓存不按交易日 key，
     只在超过 STALE_DAYS 天没更新时才重拉。
  2. 今天的振幅不从 gtimg 取——问财的截面里已经有了，零额外请求。
  3. KlineStore 跨概念共享。半导体几个概念成分重叠极多，union 去重后
     只抓一次；第二、第三个概念基本全是缓存命中。
  4. basket_cap 只保留自由流通市值前 N 只。小市值尾巴对加权序列几乎没影响，
     对中位数有系统性偏低影响——但历史和当日用的是同一个篮子，分位仍然可比。

口径：
  日振幅 = (当日最高 - 当日最低) / 前收 × 100%   —— 与问财「振幅」字段同定义
  篮子 MIX = 当日各成分股振幅的横截面聚合（等权中位数 / 自由流通市值加权）
  ⚠ 加权用的是**当前**自由流通市值回溯套用，成分和权重都会漂，是近似；
    中位数序列不含这个假设，分位以它为准更稳。
"""
from __future__ import annotations

import datetime as dt
import json
import random
import statistics
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# 两个源互为备份。腾讯 gtimg 会被 WAF 拦（返回 waf.tencent.com/501page.html 而不是 JSON），
# 单源架构一被拦整条腿就废，所以主源用新浪，gtimg 兜底。
SINA_URL = ("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            "CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen={n}")
GTIMG_URL = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
             "?param={sym},day,,,{n},qfq")
_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
       "Referer": "https://finance.sina.com.cn"}


def _get_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", "ignore")
    if body.lstrip().startswith("<"):        # WAF 拦截页 / 错误页，不是数据
        raise ValueError("非 JSON 响应（可能被 WAF 拦截）")
    return json.loads(body)


def _bars_sina(sym: str, n: int) -> List[dict]:
    rows = _get_json(SINA_URL.format(sym=sym, n=n)) or []
    return [{"d": r["day"][:10], "h": float(r["high"]), "l": float(r["low"]),
             "c": float(r["close"]), "v": float(r.get("volume") or 0)}
            for r in rows if r.get("day")]


def _bars_gtimg(sym: str, n: int) -> List[dict]:
    payload = _get_json(GTIMG_URL.format(sym=sym, n=n))
    block = (payload.get("data") or {}).get(sym) or {}
    out = []
    for row in block.get("qfqday") or block.get("day") or []:
        if len(row) >= 5:
            out.append({"d": row[0], "h": float(row[3]), "l": float(row[4]),
                        "c": float(row[2]), "v": float(row[5]) if len(row) > 5 else 0.0})
    return out


SOURCES = (("sina", _bars_sina), ("gtimg", _bars_gtimg))

CACHE_DIR = Path(__file__).resolve().parent / ".klinecache"
BAR_SCHEMA = 2            # 1=只有 d/h/l/c；2=加了成交量 v。旧 schema 缓存必须重拉
STALE_DAYS = 10           # 缓存超过这么多天才重拉；窗口 727 天，差几天不影响分位
MIN_COVERAGE = 0.6        # 篮子里取到日K的比例低于此值，分位数不予采信
DEFAULT_BASKET_CAP = 60   # 每个概念最多取自由流通市值前 N 只进篮子。
                          # 60 只对中位数/加权都够稳，比 120 少一半请求。


def to_symbol(code: str) -> Optional[str]:
    """601398 / 601398.SH → sh601398。非 A 股返回 None。"""
    c = str(code or "").split(".")[0].strip()
    if not c.isdigit() or len(c) != 6:
        return None
    if c[0] == "6":
        return "sh" + c
    if c[0] in "03":
        return "sz" + c
    if c[0] in "48":
        return "bj" + c
    return None


class KlineStore:
    """日 K 仓库：永久缓存 + 跨概念共享。stats 里能看到真实发出了多少请求。"""

    def __init__(self, cache_dir: Path = CACHE_DIR, days: int = 800, workers: int = 3,
                 breaker_after: int = 12):
        self.dir = Path(cache_dir)
        self.dir.mkdir(exist_ok=True)
        self.days = days
        self.workers = workers
        # 熔断：连续这么多次失败就判定上游在限流，整批放弃。
        # 不熔断的话 200 个失败症状 × 4 轮退避重试 = 白烧 400 秒。
        self.breaker_after = breaker_after
        self._consecutive_fail = 0
        self.tripped = False
        self._mem: Dict[str, List[dict]] = {}
        self.stats = {"cache_hit": 0, "fetched": 0, "failed": 0, "seconds": 0.0,
                      "by_source": {}}

    def _path(self, sym: str) -> Path:
        return self.dir / f"{sym}.json"

    def _load(self, sym: str) -> Optional[List[dict]]:
        if sym in self._mem:
            return self._mem[sym]
        f = self._path(sym)
        if not f.exists():
            return None
        try:
            blob = json.loads(f.read_text())
            age = (dt.date.today() - dt.date.fromisoformat(blob["fetched"])).days
            if age > STALE_DAYS:
                return None
            # 缓存必须记根数：用 800 根建的缓存拿来充 1200 根的请求，
            # 早期阶段会静默缺数据（阶段①起点 2022-12 直接落在窗口外）
            if blob.get("days", 0) < self.days:
                return None
            if blob.get("schema", 1) < BAR_SCHEMA:   # 老缓存没有成交量，换手强度算不了
                return None
            self._mem[sym] = blob["bars"]
            return blob["bars"]
        except Exception:
            return None

    def _fetch(self, sym: str, retry: int = 2) -> List[dict]:
        """按 SOURCES 顺序试，任一源拿到就落盘。全源失败才记 failed。"""
        if self.tripped:
            return []
        for attempt in range(retry + 1):
            for name, getter in SOURCES:
                try:
                    bars = getter(sym, self.days)
                except Exception:
                    continue
                if bars:
                    self._path(sym).write_text(json.dumps(
                        {"fetched": dt.date.today().isoformat(), "src": name,
                         "days": self.days, "schema": BAR_SCHEMA, "bars": bars}))
                    self._consecutive_fail = 0
                    self.stats["by_source"][name] = self.stats["by_source"].get(name, 0) + 1
                    time.sleep(0.05 + random.random() * 0.1)
                    return bars
            if attempt < retry:
                time.sleep((1.6 ** attempt) + random.random())
        self._consecutive_fail += 1
        if self._consecutive_fail >= self.breaker_after:
            self.tripped = True
        return []

    def ensure(self, codes: Sequence[str]) -> Dict[str, Any]:
        """确保这批代码的日 K 都在仓库里。已缓存的一个请求都不发。"""
        syms = [s for s in {to_symbol(c) for c in codes} if s]
        missing = [s for s in syms if self._load(s) is None]
        self.stats["cache_hit"] += len(syms) - len(missing)
        if not missing:
            return {"requested": len(syms), "fetched": 0, "failed": 0}

        t0 = time.time()
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            results = list(pool.map(self._fetch, missing))
        self.stats["seconds"] += time.time() - t0

        failed = 0
        for sym, bars in zip(missing, results):
            if bars:
                self._mem[sym] = bars
            else:
                failed += 1
        self.stats["fetched"] += len(missing) - failed
        self.stats["failed"] += failed
        return {"requested": len(syms), "fetched": len(missing) - failed,
                "failed": failed, "tripped": self.tripped}

    def amplitude(self, code: str) -> Dict[str, float]:
        """{日期: 振幅%}。首根没有前收，丢掉——不拿当日开盘凑数。"""
        sym = to_symbol(code)
        bars = self._load(sym) if sym else None
        if not bars:
            return {}
        return {cur["d"]: (cur["h"] - cur["l"]) / prev["c"] * 100.0
                for prev, cur in zip(bars, bars[1:]) if prev["c"]}


def basket_history(
    members: Sequence[Dict[str, Any]],
    store: KlineStore,
    basket_cap: int = DEFAULT_BASKET_CAP,
    min_names: int = 5,
) -> Dict[str, Any]:
    """把成分股的日振幅合成篮子 MIX 序列，并给出同一批成分股的当日 MIX。

    members 用 concept_capacity() 出的那份，需要 code / float_mktcap / amplitude。
    只取自由流通市值前 basket_cap 只：小尾巴对加权序列几乎无影响，
    且历史与当日用的是同一个篮子，分位仍然可比。
    """
    from concept_capacity import mix_vol      # 循环引用，放函数内

    ranked = sorted((m for m in members if to_symbol(m.get("code"))),
                    key=lambda m: m.get("float_mktcap") or 0.0, reverse=True)
    basket = ranked[:basket_cap]
    store.ensure([m["code"] for m in basket])

    per_day: Dict[str, List[tuple]] = {}
    have: List[Dict[str, Any]] = []
    for m in basket:
        amp = store.amplitude(m["code"])
        if not amp:
            continue
        have.append(m)
        w = m.get("float_mktcap") or 0.0
        for d, a in amp.items():
            per_day.setdefault(d, []).append((a, w))

    median_s: Dict[str, float] = {}
    weighted_s: Dict[str, float] = {}
    for d, pairs in per_day.items():
        if len(pairs) < min_names:
            continue                     # 覆盖太薄的日子不算，避免早期几只股定调
        median_s[d] = statistics.median([a for a, _w in pairs])
        tw = sum(w for _a, w in pairs)
        if tw:
            weighted_s[d] = sum(a * w for a, w in pairs) / tw

    # 今天的点不从 gtimg 取——问财截面里已经有 振幅，覆盖的正是同一批成分股。
    today = mix_vol(have)

    coverage = len(have) / len(basket) if basket else 0.0
    float_covered = sum(m.get("float_mktcap") or 0 for m in have)
    float_total = sum(m.get("float_mktcap") or 0 for m in members)

    return {
        "median": dict(sorted(median_s.items())),
        "weighted": dict(sorted(weighted_s.items())),
        "today": today,
        "n_basket": len(basket),
        "n_have": len(have),
        "n_members": len(members),
        "coverage": coverage,
        "float_coverage": float_covered / float_total if float_total else 0.0,
        "reliable": coverage >= MIN_COVERAGE,
    }


def percentile_of(value: Optional[float], series: Dict[str, float],
                  lookback_days: int = 1095) -> Dict[str, Any]:
    """value 在近 lookback_days 个**自然日**窗口内的分位。默认 1095 天 = 三年。

    注意是自然日不是交易日：三年 ≈ 730 个交易日，写 730 会只回看两年。
    value 传问财当日截面算出来的 MIX（新鲜，且与 series 同一批成分股）。
    """
    if value is None or not series:
        return {"value": value, "pct": None, "n": 0}
    latest_d = max(series)
    cutoff = (dt.date.fromisoformat(latest_d) - dt.timedelta(days=lookback_days)).isoformat()
    vals = [v for d, v in series.items() if d >= cutoff]
    if not vals:
        return {"value": value, "pct": None, "n": 0}
    return {
        "value": value,
        "pct": sum(1 for v in vals if v < value) / len(vals) * 100.0,
        "n": len(vals),
        "start": min(d for d in series if d >= cutoff),
        "end": latest_d,
        "min": min(vals),
        "median": statistics.median(vals),
        "max": max(vals),
    }


def basket_index(
    members: Sequence[Dict[str, Any]],
    store: KlineStore,
    basket_cap: int = DEFAULT_BASKET_CAP,
    weight: str = "float_mktcap",
    exclude: str = "",
) -> Dict[str, Any]:
    """把成分股日收盘合成篮子价格指数（首日=100）。

    用于第二章阶段对照：个股该段涨了多少 vs 它所在的叙事/题材篮子涨了多少，
    差额就是个股超额——给 R/M/V 里的 M（板块贝塔）一个实测锚，而不是估的。

    exclude 传个股自己的代码：它若占篮子权重很大（实测巨星科技占"外贸出口"
    自由流通市值的 22.5%），不剔除的话「超额」会被自己稀释，算出来偏小。

    ⚠ 权重用**当前**自由流通市值回溯套用，成分也是当前成分（幸存者偏差）。
      所以它是"今天这批票在过去怎么走"，不是"当时那个板块怎么走"。
      等权序列不含权重假设，两个都给，读数时自己选。
    """
    ex = str(exclude or "").split(".")[0]
    members = [m for m in members if str(m.get("code") or "").split(".")[0] != ex] if ex else list(members)
    ranked = sorted((m for m in members if to_symbol(m.get("code"))),
                    key=lambda m: m.get("float_mktcap") or 0.0, reverse=True)
    basket = ranked[:basket_cap]
    store.ensure([m["code"] for m in basket])

    closes: Dict[str, Dict[str, float]] = {}
    weights: Dict[str, float] = {}
    for m in basket:
        sym = to_symbol(m["code"])
        bars = store._load(sym) if sym else None
        if not bars:
            continue
        closes[sym] = {b["d"]: b["c"] for b in bars}
        weights[sym] = (m.get(weight) or 0.0) if weight else 1.0

    if not closes:
        return {"dates": [], "eq": {}, "wt": {}, "n": 0}

    all_dates = sorted(set().union(*[set(c) for c in closes.values()]))
    base = {s: None for s in closes}
    eq: Dict[str, float] = {}
    wt: Dict[str, float] = {}
    for d in all_dates:
        rels, ws = [], []
        for sym, c in closes.items():
            px = c.get(d)
            if px is None:
                continue
            if base[sym] is None:
                base[sym] = px
            if base[sym]:
                rels.append(px / base[sym])
                ws.append(weights.get(sym) or 0.0)
        if len(rels) < 3:                 # 覆盖太薄的日子不出点
            continue
        eq[d] = statistics.fmean(rels) * 100.0
        tw = sum(ws)
        wt[d] = (sum(r * w for r, w in zip(rels, ws)) / tw * 100.0) if tw else eq[d]

    return {"dates": sorted(eq), "eq": eq, "wt": wt, "n": len(closes), "excluded": ex or None}


def window_return(series: Dict[str, float], d0: str, d1: str) -> Optional[float]:
    """区间涨幅%。端点不是交易日就取窗口内最近的可用点，取不到返回 None，不外推。"""
    if not series:
        return None
    inside = [d for d in series if d0 <= d <= d1]
    if len(inside) < 2:
        return None
    a, b = min(inside), max(inside)
    if not series[a]:
        return None
    return (series[b] / series[a] - 1.0) * 100.0


def basket_turnover(
    members: Sequence[Dict[str, Any]],
    store: KlineStore,
    basket_cap: int = DEFAULT_BASKET_CAP,
    min_names: int = 5,
) -> Dict[str, Any]:
    """篮子的换手强度时序 = Σ成交额 ÷ Σ自由流通市值。

    这是"钱来了没有"的单调指标——钱进来它就抬，没进来就低，没有歧义。
    （原先用的日振幅分位是钝的：波动低既可能是没人玩，也可能是筹码锁死蓄势，方向不单调。）

    口径：自由流通股数 = 当前自由流通市值 ÷ 最新收盘价，回溯期内视为不变（不复权调整股本）。
    比值里收盘价上下抵消，所以 换手强度 = Σ(量×收) / Σ(自由流通股×收)，只依赖成交量与股数。
    """
    ranked = sorted((m for m in members if to_symbol(m.get("code"))),
                    key=lambda m: m.get("float_mktcap") or 0.0, reverse=True)
    basket = ranked[:basket_cap]
    store.ensure([m["code"] for m in basket])

    per_day: Dict[str, List[tuple]] = {}
    n_have = 0
    for m in basket:
        sym = to_symbol(m["code"])
        bars = store._load(sym) if sym else None
        if not bars or not m.get("float_mktcap"):
            continue
        last_c = next((b["c"] for b in reversed(bars) if b.get("c")), None)
        if not last_c:
            continue
        shares = m["float_mktcap"] / last_c        # 自由流通股数（近似：期内不变）
        if shares <= 0:
            continue
        n_have += 1
        for b in bars:
            if b.get("v") and b.get("c"):
                per_day.setdefault(b["d"], []).append((b["v"] * b["c"], shares * b["c"]))

    series: Dict[str, float] = {}
    for d, pairs in per_day.items():
        if len(pairs) < min_names:
            continue
        denom = sum(x[1] for x in pairs)
        if denom:
            series[d] = sum(x[0] for x in pairs) / denom * 100.0    # %

    return {"series": dict(sorted(series.items())), "n_basket": len(basket),
            "n_have": n_have, "reliable": bool(basket) and n_have / len(basket) >= MIN_COVERAGE}


def smooth(series: Dict[str, float], win: int = 5) -> Dict[str, float]:
    """N 日均值平滑。单日换手噪声很大，看趋势要平滑；分位也用平滑后的比才稳。"""
    ds = sorted(series)
    out: Dict[str, float] = {}
    for i, d in enumerate(ds):
        lo = max(0, i - win + 1)
        vals = [series[x] for x in ds[lo:i + 1]]
        out[d] = statistics.fmean(vals)
    return out
