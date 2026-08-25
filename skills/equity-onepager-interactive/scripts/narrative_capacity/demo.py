"""公司 → 分面概念 → 各概念的可交易容量与波动分位。

    python demo.py 兆易创新 4
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wencai import WencaiSession                                    # noqa: E402
from concept_capacity import (company_profile, select_concepts,       # noqa: E402
                              concept_capacity, breadth, yi, pct, UMBRELLA_MIN)
from vol_percentile import KlineStore, basket_history, percentile_of  # noqa: E402

COMPANY = sys.argv[1] if len(sys.argv) > 1 else "兆易创新"
TOPN = int(sys.argv[2]) if len(sys.argv) > 2 else 4
PROFILE = os.environ.get("WC_PROFILE", os.path.expanduser("~/.iwencai-profile"))


def band(p):
    if p is None:
        return ""
    return "极低" if p < 10 else "偏低" if p < 30 else "中枢" if p < 70 else "偏高" if p < 90 else "极高"


t_start = time.time()
store = KlineStore()

with WencaiSession(profile_dir=PROFILE) as s:
    p = company_profile(s, COMPANY)
    if not p["found"]:
        sys.exit(f"问财查不到「{COMPANY}」")

    print(f"【公司画像】{p['name']} ({p['code']})")
    print(f"  同花顺行业  {p['ths_industry']}")
    print(f"  申万行业    {p['sw_industry']}")
    print(f"  注册地      {p.get('province') or '-'}{p.get('city') or ''}")
    print(f"  市值        总 {yi(p['mktcap'])} / 自由流通 {yi(p['float_mktcap'])}")
    prods = str(p.get("products") or "").split("||")
    print(f"  主营产品    {'、'.join(x for x in prods[:6] if x) or '-'}")

    print(f"\n【概念分面】共 {len(p['concepts_all'])} 个")
    for facet, items in p["by_facet"].items():
        tag = "（已剔除，非可交易主题）" if facet == "机制" else ""
        print(f"  {facet:<5}({len(items):>2}){tag}  {'、'.join(items)}")

    sel = select_concepts(s, p, TOPN)
    picks = sel["picks"]
    if sel["umbrella"]:
        print(f"\n  伞形标签已跳过（成分 >{UMBRELLA_MIN} 只，对单公司无定位信息、容量不可解读）：")
        for c, size in sel["umbrella"]:
            print(f"     {c}  {size} 只")
    print(f"  → 跨面选取 {len(picks)} 个：" +
          "、".join(f"{c}[{f}·{sz}只]" for c, f, sz in picks))

    print(f"\n{'概念':<10}{'面':<8}{'宽窄':<5}{'成分':>9}{'总市值':>12}{'自由流通':>12}"
          f"{'成交额':>10}{'篮子MIX':>9}{'三年分位':>10}")
    print("─" * 90)

    rows = []
    for concept, facet, _size in picks:
        r = concept_capacity(s, concept)
        h = basket_history(r["members"], store)
        pm = percentile_of(h["today"]["median"], h["median"])
        pw = percentile_of(h["today"]["float_weighted"], h["weighted"])
        rows.append((concept, facet, r, h, pm, pw))

        n = f"{r['n_members']}/{r['n_declared']}"
        pct_txt = (f"{pm['pct']:.0f}分位" if h["reliable"] and pm["pct"] is not None
                   else "数据不可得")
        print(f"{concept:<10}{facet:<8}{breadth(r['n_declared']):<6}{n:>9}{yi(r['capacity']['total_mktcap']):>13}"
              f"{yi(r['capacity']['float_mktcap']):>13}{yi(r['capacity']['amount']):>11}"
              f"{pct(h['today']['median']):>10}{pct_txt:>11}")   # 篮子口径，与分位同源

    print("\n【明细】")
    for concept, facet, r, h, pm, pw in rows:
        print(f"\n─── {concept}［{facet}］ {r['n_members']}/{r['n_declared']} 只"
              + ("  ⚠未取全" if r["truncated"] else ""))
        m = r["mix_intraday_vol"]
        print(f"  当日MIX·全{r['n_members']}只   中位数 {pct(m['median'])}"
              f" | 流通市值加权 {pct(m['float_weighted'])} | 成交额加权 {pct(m['amount_weighted'])}")
        t = h["today"]
        print(f"  当日MIX·篮子{h['n_have']}只  中位数 {pct(t['median'])}"
              f" | 流通市值加权 {pct(t['float_weighted'])}   ← 分位用这一行，与历史同篮子")
        if h["reliable"] and pm["pct"] is not None:
            print(f"  三年分位  中位数口径 → 第 {pm['pct']:.0f} 分位 {band(pm['pct'])}"
                  f"  [{pm['start']}~{pm['end']} {pm['n']}日 低{pm['min']:.2f} 中{pm['median']:.2f} 高{pm['max']:.2f}]")
            print(f"            加权口径   → 第 {pw['pct']:.0f} 分位 {band(pw['pct'])}")
        else:
            print(f"  三年分位  ✗ 数据不可得——篮子 {h['n_have']}/{h['n_basket']} 只有日K"
                  f"（{h['coverage']:.0%}），低于阈值不出分位")
        print(f"  波动篮子  自由流通前 {h['n_basket']} 只，覆盖全概念自由流通市值的 {h['float_coverage']:.0%}")
        for w in r["warnings"]:
            print(f"  ⚠ {w}")

print(f"\n【调用量】问财 导航 {s.stats['navigations']} 次 + 直发 POST {s.stats['posts']} 次"
      f"（{s.stats['seconds']:.1f}s）")
print(f"          日K  缓存命中 {store.stats['cache_hit']} 只 / 新抓 {store.stats['fetched']} 只"
      f" / 失败 {store.stats['failed']} 只（{store.stats['seconds']:.1f}s）")
print(f"          总耗时 {time.time() - t_start:.1f}s")
