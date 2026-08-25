"""【叙事】与【题材】双轨容量表。两种入口自动识别：

    python radar.py 巨星科技 4      个股 → 它挂在哪些叙事和题材下
    python radar.py 越南工厂        题材词 → 这条叙事底下有谁、容量多少

叙事 = 韭研公社产业链。人工梳理、事件驱动、带建链日期和逻辑要点，
       成分点名给出（20~30 只）。回答"市场在讲什么故事"。
题材 = 问财所属概念。机器打标、覆盖全 A 股，成分是筛出来的（几十到上千只）。
       回答"资金会往哪个池子里找票"。

两者口径一致（容量三口径 + MIX 日内波动 + 三年分位），可以直接横比。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import roster                                                        # noqa: E402
from jiuyan import JiuyanSession, chain_date, first_lines            # noqa: E402
from wencai import WencaiSession                                     # noqa: E402
from concept_capacity import (company_profile, concept_capacity,     # noqa: E402
                              codes_capacity, probe_sizes, subject_of,
                              breadth, yi, pct)
from relevance import score_concepts, top_themes                     # noqa: E402
from vol_percentile import KlineStore, basket_history, percentile_of  # noqa: E402

TARGET = sys.argv[1] if len(sys.argv) > 1 else "巨星科技"
N_THEME = int(sys.argv[2]) if len(sys.argv) > 2 else 4
PROFILE = os.environ.get("WC_PROFILE", os.path.expanduser("~/.iwencai-profile"))


def band(p):
    if p is None:
        return ""
    return "极低" if p < 10 else "偏低" if p < 30 else "中枢" if p < 70 else "偏高" if p < 90 else "极高"


def row_line(label, sub, n, r, h, pm, reliable=True):
    if not reliable:
        return f"{label:<20}{sub:<10}{n:>7}   ✗ 解析不全，不出数"
    cap = r["capacity"]
    pt = (f"{pm['pct']:.0f}分位 {band(pm['pct'])}"
          if h["reliable"] and pm["pct"] is not None else "数据不可得")
    return (f"{label:<20}{sub:<10}{n:>7}{yi(cap['total_mktcap']):>12}"
            f"{yi(cap['float_mktcap']):>12}{yi(cap['amount']):>10}"
            f"{pct(h['today']['median']):>9}{pt:>13}")


t0 = time.time()
store = KlineStore()
detail = []

# 韭研的搜索先跑完再开问财会话：sync_playwright 不能嵌套，
# 两个 with 套在一起会报 "Sync API inside the asyncio loop"。
with JiuyanSession() as jy:
    chains = jy.search(TARGET)

with WencaiSession(profile_dir=PROFILE) as s:
    rs = roster.load(s)
    is_company = TARGET in rs          # 名册里有就是个股，否则按题材词处理

    # ---------- 头部 + 题材候选 ----------
    themes = []
    if is_company:
        p = company_profile(s, TARGET)
        if not p["found"]:
            sys.exit(f"问财查不到「{TARGET}」")
        print(f"【个股模式】{p['name']} {p['code']}　{p['ths_industry']}　"
              f"总市值 {yi(p['mktcap'])} / 自由流通 {yi(p['float_mktcap'])}")
        prods = [x for x in str(p.get("products") or "").split("||") if x][:6]
        print(f"  主营产品  {'、'.join(prods) or '-'}")

        sizes = probe_sizes(s, p["tradable"])
        scored = score_concepts(p, sizes)
        themes = top_themes(scored, N_THEME)

        print(f"\n【题材候选】问财 {len(p['concepts_all'])} 个概念，"
              f"剔机制 {len(p['mechanism'])} 个，按关联度排序")
        print(f"  {'概念':<14}{'面':<10}{'成分':>6}{'主营匹配':>9}{'命中片段':<10}"
              f"{'窄度':>6}{'原序':>6}{'总分':>7}")
        for it in scored[:12]:
            mark = ("  ★选中" if it in themes else ("  ✗伞形" if it["umbrella"] else ""))
            if it in themes and it["umbrella"]:
                mark = "  ★选中(伞形·主营强相关)"
            print(f"  {it['concept']:<14}{it['facet']:<10}{str(it['size'] or '?'):>6}"
                  f"{it['biz']:>9.2f}  {it['hit'] or '—':<10}"
                  f"{it['narrow']:>6.2f}{it['order']:>6.2f}{it['score']:>7.2f}{mark}")
    else:
        # 题材词模式：问财有没有同名概念？有就拿来和韭研的叙事直接对照。
        print(f"【题材词模式】{TARGET}")
        n = probe_sizes(s, [TARGET]).get(TARGET)
        if n:
            themes = [{"concept": TARGET, "facet": "—", "size": n,
                       "score": float("nan"), "biz": float("nan"),
                       "narrow": float("nan"), "order": float("nan")}]
            print(f"  问财有同名概念「{TARGET}」，{n} 只成分 —— 与韭研的叙事口径直接对照")
        else:
            print(f"  问财没有同名概念，只出叙事口径")

    # ---------- 韭研叙事 ----------
    print(f"\n{'名称':<20}{'类型':<10}{'成分':>7}{'总市值':>12}{'自由流通':>12}"
          f"{'成交额':>10}{'MIX':>9}{'三年分位':>13}")
    print("─" * 96)

    print("── 叙事（韭研公社·人工梳理） " + "─" * 62)
    if not chains:
        print(f"  韭研搜不到「{TARGET}」相关产业链")
    for c in chains:
        names, others = roster.split_names(c["tokens"], rs)
        if not names:
            print(f"{c['title'][:18]:<20}{'叙事':<10}   无可解析A股成分")
            continue
        r = codes_capacity(s, [(n, rs[n]) for n in names])
        h = basket_history(r["members"], store)
        pm = percentile_of(h["today"]["median"], h["median"])
        detail.append(("叙事", c, names, others, r, h, pm))
        print(row_line(c["title"][:18], "叙事", len(names), r, h, pm, r["reliable"]))

    print("── 题材（问财·机器标签） " + "─" * 66)
    if not themes:
        print("  无")
    for it in themes:
        r = concept_capacity(s, it["concept"])
        h = basket_history(r["members"], store)
        pm = percentile_of(h["today"]["median"], h["median"])
        detail.append(("题材", it, None, None, r, h, pm))
        print(row_line(it["concept"], f"题材·{breadth(r['n_declared'])}",
                       r["n_members"], r, h, pm))

    # ---------- 明细 ----------
    print("\n【明细】")
    for kind, meta, names, others, r, h, pm in detail:
        if kind == "叙事":
            print(f"\n─── [叙事] {meta['title']}   建链 {chain_date(meta['title']) or '?'}"
                  f" · 更新 {meta['updated'][:10]} · 浏览 {meta['browsers']}")
            for ln in first_lines(meta["content"], 2):
                print(f"      · {ln}")
            print(f"  成分 {len(names)} 只：{'、'.join(names)}")
            if others:
                print(f"  已排除 {len(others)} 个非A股token：{'、'.join(others)}")
        else:
            head = f"\n─── [题材] {meta['concept']}［{breadth(meta['size'])}］"
            if is_company:
                head += (f"关联度 {meta['score']:.2f}（主营匹配{meta['biz']:.2f}"
                         f" 窄度{meta['narrow']:.2f} 原序{meta['order']:.2f}）")
            print(head)
            print(f"  成分 {r['n_members']}/{r['n_declared']} 只")

        m = r["mix_intraday_vol"]
        print(f"  容量  总市值 {yi(r['capacity']['total_mktcap'])}"
              f" | 自由流通 {yi(r['capacity']['float_mktcap'])}"
              f" | 当日成交额 {yi(r['capacity']['amount'])}")
        print(f"  当日MIX  中位数 {pct(m['median'])} | 流通市值加权 {pct(m['float_weighted'])}"
              f" | 成交额加权 {pct(m['amount_weighted'])}")
        if h["reliable"] and pm["pct"] is not None:
            print(f"  三年分位  {pct(pm['value'])} → 第 {pm['pct']:.0f} 分位 {band(pm['pct'])}"
                  f"  [{pm['start']}~{pm['end']} {pm['n']}日 低{pm['min']:.2f}"
                  f" 中{pm['median']:.2f} 高{pm['max']:.2f}]")
        for w in r["warnings"]:
            print(f"  ⚠ {w}")

    # ---------- 叙事 vs 题材 的重合度 ----------
    nar = [d for d in detail if d[0] == "叙事"]
    thm = [d for d in detail if d[0] == "题材"]
    if nar and thm:
        print("\n【叙事 ∩ 题材】同名/同题下两个篮子的成分重合度")
        for _k, cm, names, _o, _r, _h, _p in nar:
            nset = set(names)
            for _k2, tm, _n2, _o2, tr, _h2, _p2 in thm:
                tset = {str(m.get("name") or "") for m in tr["members"]}
                inter = nset & tset
                print(f"  {cm['title'][:16]:<18} ∩ {tm['concept']:<10} "
                      f"{len(inter):>3}/{len(nset)} 只重合"
                      f"（{len(inter) / len(nset):.0%}）"
                      + (f"：{'、'.join(sorted(inter)[:8])}" if inter else ""))

print(f"\n【调用量】韭研 {jy.stats['searches']} 搜索（{jy.stats['seconds']:.1f}s）"
      f" | 问财 导航{s.stats['navigations']}+POST{s.stats['posts']}（{s.stats['seconds']:.1f}s）"
      f" | 日K 命中{store.stats['cache_hit']}/新抓{store.stats['fetched']}"
      f"/失败{store.stats['failed']}（{store.stats['seconds']:.1f}s）")
print(f"          总耗时 {time.time() - t0:.1f}s")
