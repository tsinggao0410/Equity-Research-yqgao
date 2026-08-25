#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fetch_ifind.py — pull the 4 Part-1 datasets for an A-share company from iFind and
parse the returned markdown pipe-tables into structured JSON. Deterministic FETCH
only; the agent maps parsed tables -> page_model (segment-label normalisation,
dimension choice, unit conversion) per SKILL.md, because iFind NL column names
drift run-to-run.

Reuses the existing, working client (does NOT re-implement transport):
  C:/Users/youqi/.claude/skills/ifind-research/scripts/ifind_client.py

Usage:
  python fetch_ifind.py --name 立昂微 --ticker 605358.SH --y0 2015 --y1 2024 \
                        --out _workspace/605358/ifind_tables.json
Datasets: segment(分产品/分行业/分地区) · holders · dupont · cost.
"""
import argparse, json, os, re, subprocess, sys

def _ifind_dir():
    """Locate the ifind-research skill across machines (win/mac)."""
    for c in (os.environ.get("IFIND_SKILL_DIR"),
              os.path.expanduser("~/.claude/skills/ifind-research"),
              r"C:/Users/youqi/.claude/skills/ifind-research"):
        if c and os.path.isfile(os.path.join(c, "scripts", "ifind_client.py")):
            return c
    return os.path.expanduser("~/.claude/skills/ifind-research")

IFIND_DIR = _ifind_dir()
IFIND_CLI = os.path.join(IFIND_DIR, "scripts", "ifind_client.py")


def run_ifind(subcmd, query, timeout=150):
    """Call the ifind CLI, return parsed dict {'answer': str} or {'error': ...}."""
    try:
        p = subprocess.run([sys.executable, IFIND_CLI, subcmd, query],
                           cwd=IFIND_DIR, capture_output=True, text=True,
                           encoding="utf-8", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "query": query}
    out = p.stdout or ""
    try:
        j = json.loads(out)
        data = (j or {}).get("data") or {}
        if isinstance(data, str):          # ★本机 client 把 data 序列化成 JSON 字符串
            try:
                data = json.loads(data)
            except Exception:
                data = {"answer": data}
        ans = (data or {}).get("answer") or ""
        return {"answer": ans, "raw_code": j.get("code")}
    except Exception:
        return {"error": "unparsed", "stdout": out[:800], "stderr": (p.stderr or "")[:400], "query": query}


def parse_md_table(answer):
    """Parse the first markdown pipe-table in `answer` -> {columns, rows}.
    Cuts off trailing '# 指标参数信息' / '# 行情衍生指标' blocks."""
    if not answer:
        return {"columns": [], "rows": []}
    # keep only up to the first '#' heading that follows the table
    body = re.split(r"\n#\s", answer)[0]
    lines = [ln.strip() for ln in body.splitlines() if ln.strip().startswith("|")]
    if not lines:
        return {"columns": [], "rows": []}
    def cells(ln):
        return [c.strip() for c in ln.strip().strip("|").split("|")]
    cols = cells(lines[0])
    rows = []
    for ln in lines[1:]:
        if re.match(r"^\|[\s:\-|]+\|?$", ln):   # separator row
            continue
        c = cells(ln)
        if len(c) == len(cols):
            rows.append(c)
    return {"columns": cols, "rows": rows}


def detect_market(ticker):
    """A / HK / US。iFind 的 fin/holders 只认 A 股，其余市场必须走 fetch_fundamentals_hkus.py。"""
    t = ticker.strip().upper()
    if t.endswith((".SH", ".SZ", ".BJ")) or re.fullmatch(r"\d{6}", t):
        return "A"
    if t.endswith(".HK") or re.fullmatch(r"\d{4,5}", t):
        return "HK"
    if re.fullmatch(r"[A-Z][A-Z.\-]{0,9}", t):
        return "US"
    return "A"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--ticker", required=True)
    # ★1.4 要「上市以来」（02 §1.4）：--y0 一律传**上市首年**，不要用这个默认值。
    #   上市日期走 fetch_stock_profile.py，或 iFind info 查「上市日期」。CK-8 d4b 会核对起点。
    ap.add_argument("--y0", default="2015", help="起始年——1.4 要求＝上市首年，别用默认值")
    ap.add_argument("--y1", default="2024")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rawdir", default=None, help="dir to dump raw answers (default: alongside out)")
    ap.add_argument("--market", choices=["A", "HK", "US"], default=None,
                    help="缺省按 ticker 自动判定；非 A 股直接拦截")
    ap.add_argument("--force", action="store_true", help="明知港美股仍要跑 iFind（调试用）")
    a = ap.parse_args()

    # ---- 市场闸 -------------------------------------------------------------
    # 为什么要拦：iFind 的 fin/holders 对港美股返回的是「查询结果为空」而**不是报错**
    # （实测 00700 腾讯控股），六张表会全部落空且脚本只在末尾打一行 ⚠️ gaps，
    # 不看日志就会拿着一份空表往下走 Phase2。
    mkt = a.market or detect_market(a.ticker)
    if mkt != "A" and not a.force:
        print("=" * 78)
        print("⛔ %s 判定为 %s 股 —— iFind fin/holders 不解析非 A 股主体，跑下去会得到 6 张空表。"
              % (a.ticker, {"HK": "港", "US": "美"}[mkt]))
        print("   改用港美股取数腿（东财三表/分析指标 + SEC EDGAR 分部 + 币种口径闸）：")
        print()
        print("   python scripts/fetch_fundamentals_hkus.py --ticker %s --market %s \\"
              % (a.ticker.replace(".HK", "").replace(".", ""), mkt))
        print("       --y0 %s --y1 %s --out %s" % (a.y0, a.y1, a.out.replace("ifind_tables", "fundamentals")))
        print()
        print("   若确属 A 股被误判，显式传 --market A；调试 iFind 行为用 --force。")
        print("=" * 78)
        sys.exit(2)

    yr = "%s年至%s年 各年度" % (a.y0, a.y1)
    N = a.name
    queries = {
        "segment_product": ("fin", "%s %s 分产品主营业务收入金额、占比及毛利率" % (N, yr)),
        "segment_industry": ("fin", "%s %s 分行业主营业务收入金额、占比及毛利率" % (N, yr)),
        "segment_region":   ("fin", "%s %s 分地区主营业务收入金额及占比" % (N, yr)),
        "dupont":           ("fin", "%s %s 净资产收益率ROE、销售净利率、总资产周转率、权益乘数" % (N, yr)),
        # ★2026-08-18：1.4 改成毛利率分解堆积柱，恒等式要求同分母的**税金及附加**与**所得税费用**两项，
        #   否则它们会被塞进「其他轧差」把塞子撑大（CK-8 d2b 允许最多缺 2 项）。
        "cost":             ("fin", "%s %s 营业总收入、营业总收入同比增长率、营业成本、销售费用、管理费用、研发费用、财务费用、"
                                     "税金及附加、所得税费用、毛利率、销售净利率、期间费用率" % (N, yr)),
        # ★2026-08-18：这三类是 1.4 堆积图里「补回利润 / 吃掉利润」的显式段。
        #   A 股**政府补助与投资收益经常就是盈亏分界线**（寒武纪 2020 两项合计约占营收 49%）；
        #   不单列就整块塞进「其他轧差」，读者只看到一个大灰块，看不出「利润是补助给的」。
        #   单独一条查询：挤进上面那条会把 NL 语句撑到 15 个指标，实测容易整表返空。
        "cost_other":       ("fin", "%s %s 其他收益、投资收益、公允价值变动损益、信用减值损失、资产减值损失" % (N, yr)),
        "holders":          ("holders", "%s %s 前十大股东及前十大流通股东名称、持股数量、持股比例、股份性质" % (N, yr)),
    }

    outdir = os.path.dirname(os.path.abspath(a.out))
    rawdir = a.rawdir or os.path.join(outdir, "raw")
    os.makedirs(rawdir, exist_ok=True)

    result = {"name": N, "ticker": a.ticker, "y0": a.y0, "y1": a.y1, "tables": {}, "errors": {}}
    for key, (sub, q) in queries.items():
        print("[fetch] %s ..." % key, flush=True)
        r = run_ifind(sub, q)
        ans = r.get("answer", "")
        with open(os.path.join(rawdir, key + ".md"), "w", encoding="utf-8") as f:
            f.write("QUERY: %s\n\n%s" % (q, ans if ans else json.dumps(r, ensure_ascii=False)))
        if "error" in r or not ans:
            result["errors"][key] = r.get("error", "empty")
            result["tables"][key] = {"columns": [], "rows": [], "query": q}
            print("   -> %s" % result["errors"][key])
            continue
        tbl = parse_md_table(ans)
        tbl["query"] = q
        result["tables"][key] = tbl
        print("   -> %d cols x %d rows" % (len(tbl["columns"]), len(tbl["rows"])))

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("wrote %s  (raw md in %s)" % (a.out, rawdir))
    # quick summary of any gaps for the agent
    if result["errors"]:
        print("\n⚠️ gaps:", ", ".join(result["errors"].keys()), "— use fallback per SKILL.md 01-data-recipes")


if __name__ == "__main__":
    main()
