"""公司 → 韭研公社产业链 → 各链的可交易容量与波动分位。

    python chain_demo.py 巨星科技

和 demo.py 的区别只在概念来源：demo.py 用问财的「所属概念」（沾边就挂的标签），
本脚本用韭研公社人工梳理的产业链（点名给成分股）。下游的容量、MIX、分位口径一致。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import roster                                                       # noqa: E402
from jiuyan import JiuyanSession, chain_date, first_lines           # noqa: E402
from wencai import WencaiSession                                    # noqa: E402
from concept_capacity import codes_capacity, yi, pct                # noqa: E402
from vol_percentile import KlineStore, basket_history, percentile_of  # noqa: E402

COMPANY = sys.argv[1] if len(sys.argv) > 1 else "巨星科技"
PROFILE = os.environ.get("WC_PROFILE", os.path.expanduser("~/.iwencai-profile"))


def band(p):
    if p is None:
        return ""
    return "极低" if p < 10 else "偏低" if p < 30 else "中枢" if p < 70 else "偏高" if p < 90 else "极高"


t_start = time.time()
store = KlineStore()

with JiuyanSession() as jy:
    chains = jy.search(COMPANY)

if not chains:
    sys.exit(f"韭研公社搜不到「{COMPANY}」相关产业链")

print(f"【韭研产业链】{COMPANY} 命中 {len(chains)} 条")
for c in chains:
    print(f"  {c['title']}   建链 {chain_date(c['title']) or '?'} · 更新 {c['updated'][:10]}"
          f" · 浏览 {c['browsers']}")

with WencaiSession(profile_dir=PROFILE) as s:
    rs = roster.load(s)
    print(f"\n（A股名册 {len(rs)} 只，用于把成分股从题材词里精确切出来）")

    print(f"\n{'产业链':<18}{'A股成分':>8}{'总市值':>12}{'自由流通':>12}"
          f"{'成交额':>10}{'篮子MIX':>9}{'三年分位':>10}")
    print("─" * 82)

    rows = []
    for c in chains:
        names, others = roster.split_names(c["tokens"], rs)
        if not names:
            print(f"{c['title'][:16]:<18}  没有可解析的 A 股成分，跳过")
            continue
        r = codes_capacity(s, [(n, rs[n]) for n in names])
        h = basket_history(r["members"], store)
        pm = percentile_of(h["today"]["median"], h["median"])
        pw = percentile_of(h["today"]["float_weighted"], h["weighted"])
        rows.append((c, names, others, r, h, pm, pw))
        _ = None

        if not r["reliable"]:
            print(f"{c['title'][:16]:<18}{len(names):>8}   ✗ 只解析出 {r['resolve_rate']:.0%}，"
                  f"加总不可信，不出数")
            continue
        pct_txt = (f"{pm['pct']:.0f}分位" if h["reliable"] and pm["pct"] is not None
                   else "数据不可得")
        print(f"{c['title'][:16]:<18}{len(names):>8}{yi(r['capacity']['total_mktcap']):>13}"
              f"{yi(r['capacity']['float_mktcap']):>13}{yi(r['capacity']['amount']):>11}"
              f"{pct(h['today']['median']):>10}{pct_txt:>11}")

    print("\n【明细】")
    for c, names, others, r, h, pm, pw in rows:
        print(f"\n─── {c['title']}")
        for line in first_lines(c["content"], 2):
            print(f"    · {line}")
        print(f"  A股成分 {len(names)} 只：{'、'.join(names)}")
        if others:
            print(f"  非A股token {len(others)} 个（题材词/港美股，已排除出加总）：{'、'.join(others)}")
        m = r["mix_intraday_vol"]
        print(f"  容量  总市值 {yi(r['capacity']['total_mktcap'])}"
              f" | 自由流通 {yi(r['capacity']['float_mktcap'])}"
              f" | 当日成交额 {yi(r['capacity']['amount'])}")
        print(f"  当日MIX  中位数 {pct(m['median'])} | 流通市值加权 {pct(m['float_weighted'])}"
              f" | 成交额加权 {pct(m['amount_weighted'])}")
        if h["reliable"] and pm["pct"] is not None:
            print(f"  三年分位  中位数口径 {pct(pm['value'])} → 第 {pm['pct']:.0f} 分位 {band(pm['pct'])}"
                  f"  [{pm['start']}~{pm['end']} {pm['n']}日 低{pm['min']:.2f} 中{pm['median']:.2f} 高{pm['max']:.2f}]")
            print(f"            加权口径   {pct(pw['value'])} → 第 {pw['pct']:.0f} 分位 {band(pw['pct'])}")
        else:
            print(f"  三年分位  ✗ 数据不可得——篮子 {h['n_have']}/{h['n_basket']} 只有日K")
        for w in r["warnings"]:
            print(f"  ⚠ {w}")

print(f"\n【调用量】韭研 {jy.stats['searches']} 次搜索（{jy.stats['seconds']:.1f}s）")
print(f"          问财 导航 {s.stats['navigations']} + POST {s.stats['posts']}（{s.stats['seconds']:.1f}s）")
print(f"          日K  缓存命中 {store.stats['cache_hit']} / 新抓 {store.stats['fetched']}"
      f" / 失败 {store.stats['failed']}（{store.stats['seconds']:.1f}s）")
print(f"          总耗时 {time.time() - t_start:.1f}s")
