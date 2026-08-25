"""同期存在的对照锚：沪深300 + 申万二级行业指数。

为什么要这条腿——概念篮子有诞生日。「800V HVDC 高压直流电源」建链于 2026-07-09，
把它套到 2022 年的阶段上算出来的「超额」没有意义：那个概念当时不存在，成分是照着
已经涨完的那批票挑出来的。onepager_module 现在按建链日硬闸掉这类行，早期阶段会
整段没有对照——所以补一条真·同期存在的锚。

选申万二级不选东财行业板块：东财 `stock_board_industry_hist_em` 在本机被远端掐
（RemoteDisconnected），申万走 akshare `index_hist_sw` 稳定，且行业分类是持续维护的
成分表，不是事后按涨幅圈出来的概念，没有「定义后验」问题。历史深度实测：
801733 其他电源设备Ⅱ 到 2014-02，光伏设备/电池/电网设备 到 2021-12（2021 分类改版）。

口径与概念篮子不同源，不可直接比绝对值，只比方向与量级：
  行业指数 = 申万口径成分加权（当期成分，非回溯套用）
  概念篮子 = 当前成分等权回溯套用

    from bench_index import fetch_bench, list_sw2
    rows = fetch_bench(["光伏设备", "电网设备"])     # 沪深300 自动附加
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

CACHE_DIR = Path(__file__).resolve().parent / ".benchcache"
STALE_DAYS = 3

_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
       "Referer": "https://finance.sina.com.cn"}
SINA_URL = ("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            "CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen={n}")

# 市场腿固定挂上：任何阶段都存在，是「大盘怎么走」的下限对照
MARKET = {"code": "sh000300", "name": "沪深300", "kind": "市场"}


def _cache_path(key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{key}.json"


def _cached(key: str) -> Optional[Dict[str, Any]]:
    p = _cache_path(key)
    if not p.exists():
        return None
    if (time.time() - p.stat().st_mtime) > STALE_DAYS * 86400:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save(key: str, payload: Dict[str, Any]) -> None:
    try:
        _cache_path(key).write_text(json.dumps(payload, ensure_ascii=False),
                                    encoding="utf-8")
    except Exception:
        pass


def _sina_index(sym: str, n: int = 1400) -> Dict[str, float]:
    req = urllib.request.Request(SINA_URL.format(sym=sym, n=n), headers=_UA)
    with urllib.request.urlopen(req, timeout=25) as resp:
        body = resp.read().decode("utf-8", "ignore")
    if body.lstrip().startswith("<"):
        raise ValueError("非 JSON 响应（可能被 WAF 拦截）")
    rows = json.loads(body) or []
    return {r["day"][:10]: float(r["close"]) for r in rows if r.get("day")}


def list_sw2() -> List[Dict[str, str]]:
    """申万二级行业名录 [{code, name, n}]。选锚时先看这张表，不要凭印象猜名字。"""
    hit = _cached("_sw2_info")
    if hit:
        return hit["rows"]
    import akshare as ak
    df = ak.sw_index_second_info()
    rows = [{"code": str(r["行业代码"]).split(".")[0],
             "name": str(r["行业名称"]),
             "n": int(r["成份个数"])} for _, r in df.iterrows()]
    _save("_sw2_info", {"rows": rows})
    return rows


def _sw_series(code: str) -> Dict[str, float]:
    import akshare as ak
    df = ak.index_hist_sw(symbol=code, period="day")
    return {str(r["日期"])[:10]: float(r["收盘"]) for _, r in df.iterrows()}


def fetch_bench(sw2_names: List[str], with_market: bool = True) -> List[Dict[str, Any]]:
    """按申万二级行业名取指数序列；沪深300 默认附加。

    取不到的那条不静默丢——返回 `error` 字段，调用方要把它渲成「数据不可得」，
    否则页面上少一条锚看不出来。
    """
    out: List[Dict[str, Any]] = []
    if with_market:
        ent: Dict[str, Any] = dict(MARKET)
        try:
            hit = _cached(MARKET["code"])
            ser = hit["series"] if hit else _sina_index(MARKET["code"])
            if not hit:
                _save(MARKET["code"], {"series": ser})
            ent["series"] = ser
            ent["first_date"] = min(ser) if ser else None
        except Exception as e:
            ent["series"], ent["error"] = {}, f"沪深300 取数失败：{e}"
        out.append(ent)

    if not sw2_names:
        return out

    try:
        info = {x["name"]: x for x in list_sw2()}
    except Exception as e:
        out.append({"kind": "行业", "name": "、".join(sw2_names), "series": {},
                    "error": f"申万名录取数失败：{e}"})
        return out

    for nm in sw2_names:
        meta = info.get(nm)
        if not meta:
            near = [k for k in info if nm in k or k in nm][:3]
            out.append({"kind": "行业", "name": nm, "series": {},
                        "error": f"申万二级无此行业名"
                                 + (f"，形近：{'/'.join(near)}" if near else "")})
            continue
        ent = {"kind": "行业", "name": nm, "code": meta["code"], "n": meta["n"]}
        try:
            hit = _cached(meta["code"])
            ser = hit["series"] if hit else _sw_series(meta["code"])
            if not hit:
                _save(meta["code"], {"series": ser})
            ent["series"] = ser
            ent["first_date"] = min(ser) if ser else None
        except Exception as e:
            ent["series"], ent["error"] = {}, f"{nm} 取数失败：{e}"
        out.append(ent)
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        kw = sys.argv[2] if len(sys.argv) > 2 else ""
        for r in list_sw2():
            if not kw or kw in r["name"]:
                print(f"{r['code']}  {r['name']}  ({r['n']})")
    else:
        for e in fetch_bench(sys.argv[1:]):
            s = e.get("series") or {}
            print(f"{e['kind']:4s} {e['name']:12s} "
                  f"{len(s):5d} bars  {min(s) if s else '-'}..{max(s) if s else '-'}"
                  f"  {e.get('error','')}")
