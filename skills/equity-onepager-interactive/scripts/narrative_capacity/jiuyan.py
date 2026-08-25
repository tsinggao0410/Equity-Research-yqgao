"""韭研公社产业库客户端 —— 按关键词取产业链及其成分股。

为什么要它：问财的「所属概念」是沾边就挂的标签，巨星科技（手工具出口商）
挂着芯片概念、军工、储能，拿去算容量全是噪音。韭研的产业链是人工梳理的，
同一个巨星科技出来的是「中美降税 / 越南工厂 / 外贸出口」——才是真实驱动。

接口：POST /jystock-app/api/v1/industry/list  body {"keyword":..,"start":1,"limit":N}
成分股就在返回的 `keyword` 字段里，不用点进详情（详情要登录，列表不用）。

token 按 timestamp 派生，脱离浏览器直调会被拒（errCode 110），
所以走 Playwright 让页面自己带签名——和问财那条腿同样的思路。
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

SEARCH_URL = "https://www.jiuyangongshe.com/industryChain?keyword={kw}"
API_MARK = "/api/v1/industry/list"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36")

# `keyword` 字段是空格分隔的混合串，里面还夹着转义引号做的分组：
#   工具五金 工程机械 宠物  跨境电商 巨星科技  欧圣电气 "三一重工  徐工机械 …"
_SPLIT = re.compile(r'[\s"\'　,，、;；/|]+')


class JiuyanSession:
    """一个浏览器实例连打多个关键词。没有登录，只用公开的列表接口。"""

    def __init__(self, headless: bool = True):
        self._pw = None
        self.browser = None
        self.ctx = None
        self.stats = {"searches": 0, "seconds": 0.0}

    def __enter__(self) -> "JiuyanSession":
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(
            channel="chrome", headless=True,
            args=["--disable-blink-features=AutomationControlled"])
        self.ctx = self.browser.new_context(user_agent=_UA, viewport={"width": 1500, "height": 950})
        return self

    def __exit__(self, *exc) -> None:
        if self.ctx:
            self.ctx.close()
        if self.browser:
            self.browser.close()
        if self._pw:
            self._pw.stop()

    def search(self, keyword: str, wait_ms: int = 3500) -> List[Dict[str, Any]]:
        """按关键词搜产业链。返回 [{title, industry_id, tokens, content, browsers, updated}]。"""
        import time
        t0 = time.time()
        page = self.ctx.new_page()
        hits: List[Any] = []
        page.on("response",
                lambda r: hits.append(r) if API_MARK in r.url else None)
        try:
            page.goto(SEARCH_URL.format(kw=quote(keyword)),
                      wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(wait_ms)
            payloads = []
            for r in hits:
                try:
                    payloads.append(r.json())
                except Exception:
                    continue
        finally:
            page.close()
            self.stats["searches"] += 1
            self.stats["seconds"] += time.time() - t0

        chains: List[Dict[str, Any]] = []
        for p in payloads:
            for item in ((p.get("data") or {}).get("result") or []):
                chains.append({
                    "title": item.get("title"),
                    "industry_id": item.get("industry_id"),
                    "tokens": [t for t in _SPLIT.split(item.get("keyword") or "") if t],
                    "content": item.get("content") or "",
                    "browsers": item.get("browsers_count"),
                    "updated": item.get("update_time"),
                })
        return chains


def chain_date(title: str) -> Optional[str]:
    """标题里的 (260416) / （20250120）是建链日期，抽出来做新鲜度判断。"""
    m = re.search(r"[（(](\d{6,8})[）)]", title or "")
    if not m:
        return None
    d = m.group(1)
    if len(d) == 6:               # 260416 → 2026-04-16
        return f"20{d[:2]}-{d[2:4]}-{d[4:6]}"
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}"


def first_lines(content: str, n: int = 2, width: int = 110) -> List[str]:
    """取 content 的前 n 条要点，用来在输出里交代这条链的逻辑。"""
    out = []
    for line in (content or "").split("\n"):
        line = line.strip()
        if line:
            out.append(line[:width])
        if len(out) >= n:
            break
    return out


_EV_DATE = re.compile(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日")
_EV_SPLIT = re.compile(r"(?:^|\n)\s*\d+[、.．)]\s*")


def parse_events(content: str, limit: int = 8) -> List[Dict[str, str]]:
    """把 content 拆成带日期的催化事件，按时间倒序。

    韭研的 content 是编号条目，每条开头基本都带一个日期：
      「1、2026年7月23日盘后讯，商务部：中美正就降税安排征求意见…」
    这就是这条叙事的催化节奏——回答"钱上一次为什么来、下一次可能什么时候来"。
    抽不出日期的条目丢掉，不猜。
    """
    out: List[Dict[str, str]] = []
    for chunk in _EV_SPLIT.split(content or ""):
        chunk = " ".join(chunk.split())
        if not chunk:
            continue
        m = _EV_DATE.search(chunk)
        if not m:
            continue
        y, mo, d = m.groups()
        out.append({"date": f"{y}-{int(mo):02d}-{int(d):02d}", "text": chunk[:150]})
    out.sort(key=lambda x: x["date"], reverse=True)
    return out[:limit]
