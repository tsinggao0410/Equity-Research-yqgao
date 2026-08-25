#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""phase_valuation.py — 2.2 阶段估值算账的**双口径**计算（TTM × Forward），写进
`part2.valuations[i].calibers`。

    python3 scripts/phase_valuation.py --model _workspace/<t>/page_model.json \
        [--q-series _workspace/<t>/q_series.json] [--write]

★由来（2026-08-16 读者反馈，赛力斯 v3.2.1 阶段①）：
    原文只用 TTM 口径算了一遍——「TTM 收入约 250 亿，P/S 从 1.6x 压到 0.6x」——
    读者要求「不仅要用 TTM 的估值口径算一遍，如果有的话还要用 Forward 口径算一遍」。
    查下来 **Forward 数据当时就躺在同一份 page_model 里**：`part2.fwd_pe.ciq.rows`
    从 2022-12-16 起日频给 ps1/ps2/pe1/pe2，阶段① 全程覆盖。没算，不是没数据。

★为什么会漏：`valuations[]` 的算账是一坨 **prose HTML**（`body` 字段）。
    03 §③ 的规范里其实写了「…→PE 档→隐含→**Forward 年限**→ΔPE vs 上段」，
    但散文里少写一段没有任何东西会报错——**这就是 schema 降级的标准长相**：
    契约要求的结构项被写进自由文本，于是「写了」和「没写」在机器看来一模一样。
    治法与开篇章 company_type 从 {label,note} 升到 {title,points[{k,v}]} 完全同构：
    **把必答项拆成字段，让漏掉这件事本身可被机器看见。**

★为什么两把尺子都要算（不是凑格式）：
    分子是同一个市值，分母换一把，读数差异**本身就是结论**——
      · 两口径同向且量级接近 → 这一段的倍数变化是真的，不是口径错觉；
      · TTM 压缩而 Forward 没压 → 市场在给还没到报表里的东西买单（抢跑）；
      · Forward 压缩而 TTM 没压 → 预期在下修，报表还没反映（最危险的那一种）；
      · 一把能算一把算不出 → 「当时根本没有这把尺子」，那句话就是这一段的定价机制。
    赛力斯阶段①：TTM 与 Forward 的 P/S 都从 ~1.6–1.7x 压到 ~0.6–0.7x，
    而两个口径的 PE 都无定义（已发生亏、预期也亏）——「没有 E 可以除」是这段的全部真相。

★口径纪律：
  · 分子（市值）两把尺子**共用同一个**——取 Capital IQ 自己的 mcap（= ps1 × rev1），
    与它算 pe1 用的分子同源。共用分子后，两个读数的差异只可能来自分母，才可比。
  · TTM 分母**按公告日可见**取，不用期末日：2023-06-09 那天能看到的最新报告是 23Q1
    （2023-04-29 公告），不是 23Q2。不做这一步就是前视偏差。
  · 落在数据窗口外的边界（如阶段① 起点 2022-12-02 早于 CIQ 首日 2022-12-16）
    吸附到最近可得日并把实际用的日期写进 `asof`，不插值、不外推。
"""
import argparse, io, json, os, datetime as dt

# 法定披露截止日（拿不到真实公告日时的兜底，宁晚勿早——早了就是前视）
STATUTORY = {3: (4, 30), 6: (8, 31), 9: (10, 31), 12: (4, 30)}


def q_key(p):
    """'2023-03-31' → (2023, 3)"""
    y, m = int(p[:4]), int(p[5:7])
    return (y, m)


def announce_of(period, earnings):
    """季度期末 → 真实公告日；拿不到用法定截止日兜底。"""
    y, m = q_key(period)
    want = {3: ("一季报",), 6: ("中报", "半年报"), 9: ("三季报",), 12: ("年报",)}[m]
    best = None
    for e in earnings or []:
        if e.get("type") in want and e.get("date"):
            d = e["date"]
            # 年报公告在次年，其余在当年
            yy = y + 1 if m == 12 else y
            if d[:4] == str(yy) and (best is None or d < best):
                best = d
    if best:
        return best
    am, ad = STATUTORY[m]
    yy = y + 1 if m == 12 else y
    return "%04d-%02d-%02d" % (yy, am, ad)


def load_quarters(model, q_series_path):
    """单季 rev/np 序列。优先外部完整序列，其次 page_model 里的 consensus.quarters。"""
    out, src = {}, None
    if q_series_path and os.path.exists(q_series_path):
        for r in json.load(io.open(q_series_path, encoding="utf-8")) or []:
            if r.get("p") and r.get("rev") is not None:
                out[r["p"]] = {"rev": r.get("rev"), "np": r.get("np")}
        src = os.path.basename(q_series_path)
    cq = (((model.get("part1") or {}).get("consensus") or {}).get("quarters")) or []
    for r in cq:
        d = r.get("date")
        if not d or r.get("is_future"):
            continue
        rev = (r.get("rev") or {}).get("actual")
        np_ = (r.get("np") or {}).get("actual")
        if rev is None and np_ is None:
            continue
        if d not in out:                       # 外部序列优先，这里只补缺口
            out[d] = {"rev": rev, "np": np_}
            src = (src + " + consensus.quarters") if src else "part1.consensus.quarters"
    return out, (src or "—")


def ttm_at(date, quarters, earnings):
    """截至 `date` **当时可见**的 TTM（滚动 4 个单季）。返回 (rev, np, 最新季, 缺口数)。"""
    vis = [p for p in quarters if announce_of(p, earnings) <= date]
    if not vis:
        return None, None, None, 4
    vis.sort(key=q_key)
    last = vis[-1]
    y, m = q_key(last)
    want, cur = [], (y, m)
    for _ in range(4):
        want.append("%04d-%02d-%02d" % (cur[0], cur[1], {3: 31, 6: 30, 9: 30, 12: 31}[cur[1]]))
        cur = (cur[0] - 1, 12) if cur[1] == 3 else (cur[0], cur[1] - 3)
    have = [w for w in want if w in quarters]
    miss = 4 - len(have)
    rev = sum(quarters[w]["rev"] for w in have if quarters[w].get("rev") is not None) if have else None
    nps = [quarters[w]["np"] for w in have if quarters[w].get("np") is not None]
    np_ = sum(nps) if len(nps) == len(have) and have else None
    return (rev if miss == 0 else None), (np_ if miss == 0 else None), last, miss


def ciq_at(date, rows):
    """吸附到 ≤date 的最后一个可得日；早于首日则吸附到首日。返回 (row, 实际日期)。"""
    if not rows:
        return None, None
    ok = [r for r in rows if r.get("d") and r["d"] <= date]
    r = ok[-1] if ok else rows[0]
    return r, r.get("d")


def f(x, n=2):
    try:
        v = float(x)
        return round(v, n) if v == v else None
    except (TypeError, ValueError):
        return None


def leg(start, end):
    """一条腿的 {start,end,delta}；任一端缺就返回 None。"""
    if start is None or end is None:
        return None
    return {"start": start, "end": end, "delta": round(end - start, 2)}


def pctc(a, b):
    """b 相对 a 的变动（小数）。"""
    if a in (None, 0) or b is None:
        return None
    return b / a - 1.0


def fwd_decomp(r0, r1):
    """★Forward 口径的**恒等式**分解：市值 ≡ 前瞻盈利 × 前瞻PE。

    这不是估计、不是回归——两边都是 CIQ 当天的读数，乘起来就是市值本身。
    所以「这一段跌的是盈利还是倍数」在 Forward 口径下有**唯一答案**，
    不像 TTM 口径下的 R/M/V 要靠每股拆分与假设。
    分歧出现时以本式为准：TTM 的 E 里装的是过去四个季度已经赚到的钱，
    行情拐点上它天然滞后（赛力斯阶段⑥：TTM 的 E 里全是 2025 年的好日子）。
    """
    if not (r0 and r1):
        return None
    n0, n1 = f(r0.get("ni1"), 3), f(r1.get("ni1"), 3)
    p0, p1 = f(r0.get("pe1"), 3), f(r1.get("pe1"), 3)
    if None in (n0, n1, p0, p1) or n0 <= 0 or n1 <= 0 or p0 <= 0 or p1 <= 0:
        return None
    dn, dp = pctc(n0, n1), pctc(p0, p1)
    dm = (1 + dn) * (1 + dp) - 1
    lead = "盈利预期" if abs(dn) >= abs(dp) else "倍数"
    return {"ni_start": n0, "ni_end": n1, "pe_start": p0, "pe_end": p1,
            "d_earn_pct": round(dn * 100, 1), "d_mult_pct": round(dp * 100, 1),
            "d_mcap_pct": round(dm * 100, 1), "lead": lead,
            "identity": "市值变动 %+.1f%% ＝ 前瞻盈利 %+.1f%% × 前瞻PE %+.1f%%（恒等式，非估计）"
                        % (dm * 100, dn * 100, dp * 100)}


PE_MAX = 150.0          # 超过这个数就不再是「在给盈利定价」，ln(PE₁/PE₀) 也不再有解释力


def ruler_suggest(ttm, fwd):
    """★这一段的 R/M/V 该用哪把尺子（03 §2f-q2，2026-08-18 用户改制）。

    盈利趋零时 ln(NM₁/NM₀) 与 ln(PE₁/PE₀) 不是「很大」，是**没有定义**。
    硬算的结果每次都长一个样：V 吃掉整段涨幅、R 与 M 被挤成两根看不见的短条，
    读者读成「这一段全是估值在动」——而真相通常是「这一段根本没有盈利这把尺子」。
    两句话的仓位含义相反，所以这里只做**探测**并把理由写全，`ruler` 由作者拍板。

    返回 {'ruler': 'PE|PS|PB', 'why': '…', 'triggers': [...]}。"""
    trig, ends = [], []
    for tag, o in (("TTM", ttm), ("Forward", fwd)):
        pe = o.get("pe") or {}
        if pe.get("na"):
            trig.append("%s：%s" % (tag, pe["na"]))
            continue
        for side in ("start", "end"):
            v = pe.get(side)
            if v is None:
                continue
            ends.append(v)
            if v <= 0:
                trig.append("%s %s端 PE %.1f ≤ 0" % (tag, "起" if side == "start" else "终", v))
            elif v > PE_MAX:
                trig.append("%s %s端 PE %.0fx > %.0fx（已不是在给盈利定价）"
                            % (tag, "起" if side == "start" else "终", v, PE_MAX))
        d = o.get("denom") or {}
        for side in ("start", "end"):
            rev, np_ = d.get("rev_%s" % side), d.get("np_%s" % side)
            if rev and np_ is not None and rev > 0:
                nm = np_ / rev
                if 0 < abs(nm) < 0.02:
                    trig.append("%s %s端 净利率 %.2f%%（|净利率|<2%%，分母趋零，ln 对微小重述极敏感）"
                                % (tag, "起" if side == "start" else "终", nm * 100))

    if not trig:
        return {"ruler": "PE", "why": "两端盈利均为正且量级正常，PE 三因子分解成立", "triggers": []}

    # PE 不可用时：收入还能不能当锚，看两把尺子里有没有一条 P/S 算得出来
    ps_ok = any((o.get("ps") or {}).get("delta") is not None for o in (ttm, fwd))
    if ps_ok:
        return {"ruler": "PS",
                "why": ("PE 在本段不可用（%s）；P/S 两端都算得出，收入仍是定价锚 → R＝收入、V＝P/S、"
                        "M 层无盈利可拆填 0 并在 basis 写明" % trig[0]),
                "triggers": trig}
    return {"ruler": "PB",
            "why": ("PE 与 P/S 在本段都不可用（%s）；退到净资产口径 → R＝净资产、V＝PB、M 层填 0。"
                    "**PB 腿的净资产与 PB 需自行补数，本脚本没有资产负债表腿**" % trig[0]),
            "triggers": trig}


def read_line(ttm, fwd):
    """两把尺子摆在一起该读出什么——这一句才是算两遍的理由。"""
    tp, fp = (ttm.get("ps") or {}), (fwd.get("ps") or {})
    te, fe = (ttm.get("pe") or {}), (fwd.get("pe") or {})
    dc = fwd.get("decomp")

    # ── 首选：Forward 恒等式分解可算时，它直接给出「杀的是盈利还是倍数」──────
    if dc:
        head = ("Forward 口径（恒等式）：%s，**主要来自%s**。"
                % (dc["identity"].split("（")[0], dc["lead"]))
        dte = te.get("delta")
        if dte is not None and dc["d_mult_pct"] is not None:
            # TTM 的倍数变化方向与 Forward 的倍数变化方向相反 = 两把尺子讲的是两个故事
            if dte * dc["d_mult_pct"] < 0:
                return (head + "　⚠️ 与 TTM 口径**结论相反**：TTM PE %+.1fx（看着像杀估值），"
                        "而前瞻倍数 %+.1f%% 几乎没动——差别在分母，"
                        "TTM 的 E 装的是过去四个季度**已经赚到**的钱，行情拐点上天然滞后。"
                        "**拐点段以 Forward 口径为准。**" % (dte, dc["d_mult_pct"]))
        return head

    # ── 次选：两个口径的同一把尺子都能算，比方向与量级 ────────────────────────
    for name, a, b in (("PE", te, fe), ("P/S", tp, fp)):
        if a.get("delta") is not None and b.get("delta") is not None:
            da, db = a["delta"], b["delta"]
            if da * db > 0 and (abs(da - db) <= max(0.35 * max(abs(da), abs(db)), 0.15)):
                return ("两把尺子同向且量级接近（TTM %s %+.2fx / Forward %+.2fx）"
                        "→ 这一段的倍数变化是真的，不是口径错觉。" % (name, da, db))
            if da * db > 0:
                return ("两把尺子同向但量级差得多（TTM %s %+.2fx vs Forward %+.2fx）"
                        "→ 预期与已发生的调整速度不一致，拐点上信 Forward。" % (name, da, db))
            if da < 0 < db:
                return ("TTM %s 在压、Forward 在抬（%+.2fx vs %+.2fx）"
                        "→ 分母换了：要么预期被下修得比价格更快，要么市场在给还没进报表的东西买单，"
                        "看 Forward 盈利腿的方向定夺。" % (name, da, db))
            return ("Forward %s 在压、TTM 还没压（%+.2fx vs %+.2fx）"
                    "→ 预期正在下修而报表还没反映，是两者里更危险的那一种。" % (name, db, da))

    # ── 一把能算一把不能——「当时没有这把尺子」本身就是定价机制 ────────────────
    tna = te.get("na") or tp.get("na") or ttm.get("na")
    fna = fe.get("na") or fp.get("na") or fwd.get("na")
    if te.get("delta") is None and fe.get("delta") is None:
        base = "两个口径的 PE 都无定义"
        if tna or fna:
            base += "（已发生：%s；前瞻：%s）" % (tna or "—", fna or "—")
        if tp.get("delta") is not None or fp.get("delta") is not None:
            base += "——「没有 E 可以除」就是这一段的定价机制，市场只能拿 P/S 当尺子。"
        return base
    return "只有一个口径可算，另一个当时不存在——这件事本身就是这一段的定价机制。"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--q-series", help="单季 rev/np 序列 json（[{p,rev,np}]），补 consensus.quarters 的缺口")
    ap.add_argument("--write", action="store_true", help="写回 part2.valuations[].calibers")
    a = ap.parse_args()

    model = json.load(io.open(a.model, encoding="utf-8"))
    P2 = model.get("part2") or {}
    phases = P2.get("phases") or []
    vals = P2.get("valuations") or []
    rows = (((P2.get("fwd_pe") or {}).get("ciq")) or {}).get("rows") or []
    earnings = P2.get("earnings") or []
    quarters, qsrc = load_quarters(model, a.q_series)

    if not phases:
        raise SystemExit("part2.phases 为空")
    if len(vals) != len(phases):
        print("⚠️ valuations(%d) 与 phases(%d) 不同长，按 phases 补齐" % (len(vals), len(phases)))
        while len(vals) < len(phases):
            vals.append({})

    print("单季序列来源：%s（%d 个季度）　CIQ 日频：%d 行 %s→%s"
          % (qsrc, len(quarters), len(rows), rows[0]["d"] if rows else "—", rows[-1]["d"] if rows else "—"))
    print("─" * 108)
    print("%-26s %-22s %-24s %-24s" % ("阶段", "市值(亿,同一分子)", "TTM 口径", "Forward 口径(FY+1)"))
    print("─" * 108)

    for i, ph in enumerate(phases):
        d0, d1 = ph.get("from"), ph.get("to")
        r0, a0 = ciq_at(d0, rows)
        r1, a1 = ciq_at(d1, rows)

        def mcap(r):
            ps, rev = f(r and r.get("ps1"), 4), f(r and r.get("rev1"), 4)
            return round(ps * rev, 1) if (ps and rev) else None
        m0, m1 = mcap(r0), mcap(r1)

        # ---- Forward（FY+1 一致预期）------------------------------------
        fwd = {"ok": bool(r0 and r1), "src": (P2.get("fwd_pe") or {}).get("src") or "Capital IQ 日频一致预期",
               "asof": {"start": a0, "end": a1},
               "fy": {"start": (r0 or {}).get("fy1"), "end": (r1 or {}).get("fy1")},
               "denom": {"rev_start": f((r0 or {}).get("rev1"), 1), "rev_end": f((r1 or {}).get("rev1"), 1),
                         "np_start": f((r0 or {}).get("ni1"), 2), "np_end": f((r1 or {}).get("ni1"), 2)},
               "pe": leg(f((r0 or {}).get("pe1")), f((r1 or {}).get("pe1"))) or {},
               "ps": leg(f((r0 or {}).get("ps1")), f((r1 or {}).get("ps1"))) or {}}
        if not fwd["pe"]:
            neg = [x for x in (fwd["denom"]["np_start"], fwd["denom"]["np_end"]) if x is not None and x <= 0]
            fwd["pe"] = {"na": "FY+1 一致预期归母为负，PE 无定义" if neg else "该端无 Forward PE 覆盖"}
        dc = fwd_decomp(r0, r1)
        if dc:
            fwd["decomp"] = dc
        if a0 and d0 and a0 != d0:
            fwd["snap_note"] = "起点吸附：%s → %s（CIQ 首个可得日，不外推）" % (d0, a0)

        # ---- TTM（按公告日可见）-----------------------------------------
        tr0, tn0, lq0, ms0 = ttm_at(d0, quarters, earnings)
        tr1, tn1, lq1, ms1 = ttm_at(d1, quarters, earnings)
        ttm = {"ok": bool(tr0 and tr1), "src": qsrc,
               "q_asof": {"start": lq0, "end": lq1},
               "caliber": "按公告日可见的滚动 4 个单季，非期末日（避免前视）",
               "denom": {"rev_start": f(tr0, 1), "rev_end": f(tr1, 1), "np_start": f(tn0, 2), "np_end": f(tn1, 2)}}
        ttm["ps"] = leg(f(m0 / tr0) if (m0 and tr0) else None, f(m1 / tr1) if (m1 and tr1) else None) or {}
        pe0 = f(m0 / tn0) if (m0 and tn0 and tn0 > 0) else None
        pe1_ = f(m1 / tn1) if (m1 and tn1 and tn1 > 0) else None
        ttm["pe"] = leg(pe0, pe1_) or {}
        if not ttm["pe"]:
            neg = [x for x in (tn0, tn1) if x is not None and x <= 0]
            ttm["pe"] = {"na": "已披露 TTM 归母为负，PE 无定义" if neg else "该端 TTM 数据不全"}
        if ms0 or ms1:
            ttm["gap_note"] = "单季缺口：起点缺 %d 季、终点缺 %d 季，缺口端不出数" % (ms0, ms1)

        cal = {"numerator": {"caliber": "Capital IQ 市值（= Forward P/S × Forward 收入，与其 PE 分子同源）",
                             "mcap_start_yi": m0, "mcap_end_yi": m1},
               "ttm": ttm, "fwd": fwd}
        cal["read"] = read_line(ttm, fwd)
        cal["ruler_suggest"] = ruler_suggest(ttm, fwd)
        vals[i]["calibers"] = cal

        def show(o):
            if o.get("pe", {}).get("delta") is not None:
                return "PE %.1f→%.1fx (%+.1f)" % (o["pe"]["start"], o["pe"]["end"], o["pe"]["delta"])
            if o.get("ps", {}).get("delta") is not None:
                return "P/S %.2f→%.2fx (%+.2f)" % (o["ps"]["start"], o["ps"]["end"], o["ps"]["delta"])
            return (o.get("pe", {}).get("na") or "不可得")[:22]
        print("%-26s %-22s %-24s %-24s" % ((ph.get("name") or "")[:13],
              "%s→%s" % (m0 or "—", m1 or "—"), show(ttm), show(fwd)))
        print("     读数：%s" % cal["read"])
        rs = cal["ruler_suggest"]
        if rs["ruler"] != "PE":
            print("     ⚠️ R/M/V 尺子建议改 %s：%s" % (rs["ruler"], rs["why"]))
            print("        → phases[%d].factor_quant 填 ruler/ruler_why 后重算三因子（03 §2f-q2，CK-8 g5）" % i)

    print("─" * 108)
    if a.write:
        P2["valuations"] = vals
        model["part2"] = P2
        json.dump(model, io.open(a.model, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("✓ 已写回 %s 的 part2.valuations[].calibers（%d 段）" % (a.model, len(phases)))
    else:
        print("（试算，未写回；加 --write 落盘）")


if __name__ == "__main__":
    main()
