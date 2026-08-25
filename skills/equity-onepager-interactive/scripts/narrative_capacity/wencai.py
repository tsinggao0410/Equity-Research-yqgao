"""问财数据腿 — 一次导航建会话，之后全部直发 POST。

为什么不抓 DOM：问财的表头是多日分组的（一个"区间振幅"表头跨 3 个日期列），
DOM 里表头项数和数据列数对不上，按位置映射会静默错列。底层 XHR 返回的 datas
是按字段名索引的（"区间振幅[20260814]": 3.785），结构上不可能错列。

为什么不每次都导航：页面导航要 ~10s（加载 + 等 JS 渲染），而 get-robot-data
本身就是个普通 form POST。首次导航拿到 cookie + hexin-v 后，把请求当模板改
question 直接重发，单次 ~0.8s。12 倍差距，且不多占问财一分钟的资源。

不需要 API key，走本机 Chrome。
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from urllib.parse import parse_qsl, quote, urlencode

RESULT_URL = "https://www.iwencai.com/unifiedwap/result?w={q}&querytype={t}"
ROBOT_DATA_MARK = "get-robot-data"
DEFAULT_PROFILE = Path.home() / ".iwencai-profile"

QUERY_TYPES = (
    "stock", "zhishu", "fund", "hkstock", "usstock",
    "threeboard", "conbond", "insurance", "futures", "lccp", "foreign_exchange",
)

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
)

PERPAGE = 100          # 服务端硬顶，写更大无效
# 免费版对 question 有长度上限（超了返回 status_code=-9138「question字段长度过长」）。
# 实测 203 字符被拒。留足余量，调用方按这个数切块。
MAX_QUESTION = 190
MAX_ROUNDS = 12        # 游标翻页轮数护栏
_STRIP_HEADERS = {"content-length", "host", "connection", "accept-encoding"}


class WencaiError(RuntimeError):
    pass


def _walk(node: Any) -> Iterator[dict]:
    """深度遍历，吐出所有同时带 columns 和 datas 的字典。"""
    if isinstance(node, dict):
        if "columns" in node and "datas" in node:
            yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _first_block(payload: dict) -> dict:
    return next(_walk(payload), {}) or {}


def _total_count(payload: dict) -> Optional[int]:
    extra = (_first_block(payload).get("meta") or {}).get("extra") or {}
    for k in ("code_count", "row_count"):
        if k in extra:
            try:
                return int(extra[k])
            except (TypeError, ValueError):
                pass
    return None


class WencaiSession:
    """一次导航建立会话模板，之后所有查询走直发 POST。

    stats 记录本次会话真实发出的请求数，便于核对调用量。
    """

    def __init__(self, profile_dir: str | Path = DEFAULT_PROFILE, headless: bool = True):
        self.profile_dir = str(profile_dir)
        self.headless = headless
        self._pw = None
        self.ctx = None
        self._tpl: Optional[Dict[str, Any]] = None
        self.stats = {"navigations": 0, "posts": 0, "seconds": 0.0}

    def __enter__(self) -> "WencaiSession":
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        kwargs = dict(
            user_data_dir=self.profile_dir,
            headless=self.headless,
            viewport={"width": 1600, "height": 1000},
            user_agent=_UA,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        try:
            self.ctx = self._pw.chromium.launch_persistent_context(channel="chrome", **kwargs)
        except Exception as e:
            # 不静默回退到内置 Chromium：它多半没下载，报错会变成
            # "Executable doesn't exist at …chrome-headless-shell"，把真正原因盖掉
            try:
                self.ctx = self._pw.chromium.launch_persistent_context(**kwargs)
            except Exception:
                raise WencaiError(
                    f"本机 Chrome 启动失败（{e}）。若 profile 被其他进程占用，"
                    f"关掉再试；要用内置 Chromium 需先跑 `playwright install chromium`") from e
        self.ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
            "window.chrome = window.chrome || {runtime:{}};"
        )
        return self

    def __exit__(self, *exc) -> None:
        if self.ctx:
            self.ctx.close()
        if self._pw:
            self._pw.stop()

    # ---------- 会话模板 ----------

    def _build_template(self, querytype: str) -> None:
        """导航一次，抓下 get-robot-data 的 URL / 头 / 表单体当模板。"""
        t0 = time.time()
        page = self.ctx.new_page()
        reqs: List[Any] = []
        page.on("request", lambda r: reqs.append(r) if ROBOT_DATA_MARK in r.url else None)
        try:
            page.goto(RESULT_URL.format(q=quote("沪深300"), t=querytype),
                      wait_until="load", timeout=45000)
            page.wait_for_timeout(4500)
            if not reqs or not reqs[0].post_data:
                raise WencaiError("导航没抓到 get-robot-data 请求，无法建立会话模板")
            tpl = reqs[0]
            self._tpl = {
                "url": tpl.url,
                "headers": {k: v for k, v in tpl.all_headers().items()
                            if k.lower() not in _STRIP_HEADERS},
                "form": dict(parse_qsl(tpl.post_data, keep_blank_values=True)),
            }
        finally:
            page.close()
        self.stats["navigations"] += 1
        self.stats["seconds"] += time.time() - t0

    def _post(self, question: str, perpage: int) -> dict:
        """直发一条查询。hexin-v 失效时自动重建会话再试一次。"""
        # 原地重试到第 4 次才重建会话——重建要跑 5 秒导航，是最贵的动作。
        # 连打几十条时问财偶发抖动，为一次抖动重建整个会话极不划算。
        for attempt in range(5):
            if self._tpl is None:
                self._build_template("stock")
            form = dict(self._tpl["form"])
            form["question"] = question
            form["perpage"] = str(perpage)
            form["page"] = "1"
            t0 = time.time()
            try:
                resp = self.ctx.request.post(
                    self._tpl["url"], headers=self._tpl["headers"],
                    data=urlencode(form), timeout=30000,
                )
                payload = resp.json()
            except Exception as e:
                if attempt >= 4:
                    raise WencaiError(f"查询失败：{e}") from e
                if attempt == 3:
                    self._tpl = None          # 连错四次，才怀疑是会话失效
                time.sleep(0.4 * (attempt + 1))
                continue
            finally:
                self.stats["posts"] += 1
                self.stats["seconds"] += time.time() - t0

            # 空结果 ≠ 会话失效。游标翻到尾巴本来就会返回空，
            # 拿它去重建模板等于白跑一次 5 秒导航。只认 status_code 判失效。
            if payload.get("status_code") in (0, None) or attempt:
                return payload
            self._tpl = None
        return {}

    # ---------- 查询 ----------

    def query(
        self,
        q: str,
        querytype: str = "stock",
        all_rows: bool = True,
        cursor_field: str = "总市值",
        perpage: int = PERPAGE,
        max_rounds: int = MAX_ROUNDS,
    ) -> Dict[str, Any]:
        """跑一条问句。rows 的 key 是问财自己的字段名，含日期戳。

        超过 100 条时靠 cursor_field 游标翻页：接口的 page 参数无效
        （meta.page 恒为 1，每页返回同一批），只能把问句本身切窄。
        """
        if querytype not in QUERY_TYPES:
            raise ValueError(f"querytype 需为 {QUERY_TYPES} 之一，收到 {querytype!r}")
        if self._tpl is None:
            self._build_template(querytype)

        notes: List[str] = []
        # 排序必须放进**第一条**查询：游标是"已取到的最小市值"，若首批是无序样本，
        # 它的最小值会落得很低，后面 `小于该值` 几乎捞不到新名字（实测 200 只只能取到 101 只）。
        base = f"{q} 按{cursor_field}从大到小排序" if (all_rows and cursor_field) else q
        payload = self._post(base, perpage)
        block = _first_block(payload)
        columns = block.get("columns") or []
        total = _total_count(payload)

        # 服务端的错误码必须往上抛，不能当成"空结果"。
        # -9138 = 问句超长，静默吞掉的话调用方会以为这批标的真的不存在。
        status = payload.get("status_code")
        if status not in (0, None):
            notes.append(f"问财报错 status={status}: {payload.get('status_msg')}")

        rows: Dict[str, dict] = {}
        _absorb(rows, block.get("datas") or [])

        if all_rows and total and total > len(rows):
            key = _key_of(columns, cursor_field)
            if not key:
                notes.append(f"没有「{cursor_field}」列，无法游标翻页，只取到首屏")
            else:
                for _ in range(max_rounds):
                    cur = min((to_num(r.get(key)) for r in rows.values()
                               if to_num(r.get(key)) is not None), default=None)
                    if cur is None:
                        notes.append("游标取值为空，停止翻页")
                        break
                    nxt = self._post(f"{base} {cursor_field}小于{cur / 1e8:.4f}亿", perpage)
                    got = _first_block(nxt).get("datas") or []
                    before = len(rows)
                    _absorb(rows, got)
                    if len(rows) == before:
                        break
                    if len(rows) >= total:
                        break
                else:
                    notes.append(f"翻到 {max_rounds} 轮护栏仍未取满")

        out = list(rows.values())
        truncated = bool(total) and len(out) < total
        if truncated:
            notes.append(f"只取到 {len(out)}/{total} 条，加总不完整")

        return {
            "query": base,
            "querytype": querytype,
            "status": payload.get("status_code"),
            "status_msg": payload.get("status_msg"),
            "columns": columns,
            "rows": out,
            "count": len(out),
            "total": total,
            "truncated": truncated,
            "notes": notes,
            "text": _extract_text(payload),
        }


def _absorb(store: Dict[str, dict], rows: List[dict]) -> None:
    for row in rows:
        if not isinstance(row, dict):
            continue
        fp = str(row.get("code") or row.get("股票代码")
                 or json.dumps(row, sort_keys=True, ensure_ascii=False))
        store.setdefault(fp, row)


def _key_of(columns: List[dict], index_name: str) -> Optional[str]:
    for col in columns:
        if col.get("index_name") == index_name:
            return col.get("key")
    return None


def _extract_text(payload: dict) -> str:
    try:
        return payload["data"]["answer"][0].get("text_answer", "") or ""
    except (KeyError, IndexError, TypeError):
        return ""


def column_index(result: Dict[str, Any]) -> Dict[str, List[dict]]:
    """按 index_name 归拢字段，值是该指标下的所有列（多日就是多条，带 timestamp）。"""
    idx: Dict[str, List[dict]] = {}
    for col in result.get("columns") or []:
        idx.setdefault(col.get("index_name") or col.get("key", ""), []).append(col)
    for cols in idx.values():
        cols.sort(key=lambda c: c.get("timestamp") or "", reverse=True)
    return idx


def pick(result: Dict[str, Any], index_name: str, latest: bool = True) -> Optional[str]:
    """把指标中文名解析成 rows 里的真实 key。找不到返回 None，绝不猜。"""
    idx = column_index(result)
    if index_name in idx:
        cols = idx[index_name]
        return (cols[0] if latest else cols[-1]).get("key")
    for name, cols in idx.items():
        if index_name in name:
            return (cols[0] if latest else cols[-1]).get("key")
    return None


# 必须带科学计数法：问财会把成交额一类的值返回成字符串 "3.1685751922E8"，
# 漏掉指数部分就是 1 亿倍的静默误差。
_NUM = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def to_num(value: Any) -> Optional[float]:
    """把问财的值转成 float。已经是数字就直接用；带中文单位的字符串按单位还原。"""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).replace(",", "").strip()
    m = _NUM.search(s)
    if not m:
        return None
    n = float(m.group())
    for unit, mult in (("万亿", 1e12), ("亿", 1e8), ("万", 1e4)):
        if unit in s:
            return n * mult
    return n
