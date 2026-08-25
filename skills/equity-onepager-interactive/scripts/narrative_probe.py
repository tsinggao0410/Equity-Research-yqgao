# -*- coding: utf-8 -*-
"""narrative_probe.py —— 用 AlphaPai 把叙事链拆深（Phase 5.5 · references/09 §7b）

**为什么要有这个脚本**：09 §7 的 `narratives[].chain/subs` 原本靠 agent 自己想，容易只写出
「我已经知道的那几环」——而次级矛盾的价值恰恰在**我没想到的那一环**。AlphaPai 是一台
「卖方共识测量仪」：它读过全市场的研报/点评/纪要/公告，能回答「别人在这条链上争什么、
争到什么数字」。把主叙事喂给它，拿回来的是**候选**，不是结论。

**三种探针**（各自独立一次调用，不用多轮——AlphaPai 是静态三段式 RAG，多轮记忆弱）：

| 探针 | 底层接口 | 回答什么 | 落到 part4 的哪一格 |
|---|---|---|---|
| `challenge` | agent mode 9 观点Challenge | 这条链的哪一环最先断、反方给的数是多少 | `narratives[].weakest` + `chain[].status` + 新 `subs[]` |
| `decompose` | qa --mode Think (Wide Search) | 我没列出来的环节还有哪些 | 新 `subs[]` 候选 |
| `coverage`  | recall --type ...          | 这一格有几家在看、都是什么类型的料 | `items[].coverage` + `dispersion_basis` 形态 |

**铁律（写死在输出里，别绕过）**：
1. AlphaPai 的产出一律标 `provisional:true`，**必须回 research-rag / page_model 复核后**
   才能改 `status:'verified'` 进图（09 §10「数字没回原文核」是本 skill 踩过的最大的坑）。
2. 最有价值的往往不是它的结论，而是它**引用的别家数字** —— 脚本把 `references[]` 里
   带数字的句子单独抽成 `rival_numbers[]`，这才是 `dispersion_basis` 的原料。
3. 它推翻你的假设时不要护着自己的模型（实测：本脚本第一次跑就查出「新增产能在体外」，
   直接推翻了原页面「少数股东占比会随产能摊薄而下降」的基准假设）。

用法：
  # 1) 挑战一条叙事（最常用）
  python scripts/narrative_probe.py challenge --ticker 688825 --name 长鑫科技 \
      --claim "2027年归母净利润可达2900亿元，按13倍PE对应3.6万亿市值合理" \
      --concern "DRAM周期高点定价;少数股东权益扣减比例;2028年供给释放节奏" \
      --since 2026-01-01

  # 2) 拆环（把已有 chain 喂进去，问它缺哪些环）
  python scripts/narrative_probe.py decompose --ticker 688825 --name 长鑫科技 \
      --narrative "存储超级周期" --chain-file _workspace/688825/probe/chain_cycle.txt

  # 3) 测覆盖密度（判零覆盖用）
  python scripts/narrative_probe.py coverage --ticker 688825 \
      --topic "长鑫 DDR位元占比 产品结构 服务器与手机产能分配"

产物：`_workspace/<ticker>/probe/<probe>_<slug>.json`（结构化）+ `.md`（原文全文，供逐字取证）
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
AP = os.path.join(os.path.dirname(SKILL), 'alphapai-research', 'scripts', 'alphapai_client.py')
AP_DIR = os.path.dirname(os.path.dirname(AP))

# ── 提示词设计 ──────────────────────────────────────────────────────────────
# AlphaPai 是「问题感知检索」：问题里出现的实体/数字/口径词决定它捞到什么。
# 所以三条模板都遵守：① 实体全称+代码 ② 观点里必须带数字 ③ 把口径词写进 concern。

CHALLENGE_Q = (
    "Challenge该观点：{name}({ticker}) {claim}"
)
CHALLENGE_CONCERN = (
    "{concern}。请特别做到三件事："
    "①逐条列出市场上其他机构对同一指标给出的具体数字（机构名+日期+原样数字），不要只给方向；"
    "②指出该观点的逻辑链条里哪一环最先断、为什么；"
    "③给出未来12个月内可以证真或证伪它的具体可观测数据。"
    "如果某一项在你的资料里没有任何一家讨论过，请直接回答「没有」，不要用行业常识补齐。"
)

DECOMPOSE_Q = (
    "关于{name}({ticker})的「{narrative}」这条投资叙事，"
    "我已经把它拆成了下面这条推演链：\n{chain}\n\n"
    "请回答：这条链里我**没有列出来但同样会决定成败**的环节还有哪些？"
    "每指出一个环节，都请给出：(a) 这一环的具体机制；"
    "(b) 市场上各家对它的分歧——谁给了什么数字（机构名+日期+原样数字），极差多大；"
    "(c) 未来12个月内能判定它的公开事件或数据。"
    "只列你在资料里真正读到过讨论的环节；某一环若没有任何一家讨论过，"
    "请明确写「该环节零覆盖」，不要推测、不要用行业常识补齐。"
)

COVERAGE_TYPES = "report,foreign_report,comment,roadShow,roadShow_ir,ann,qa"


def run_ap(args, timeout=1500):
    """调 alphapai_client.py，返回 stdout 文本。失败抛错并把 stderr 带出来。
    注：alphapai-research v1.3 起各子命令默认就输出 JSON，`--json` 已被移除，别再加。"""
    cmd = [sys.executable, AP] + args
    p = subprocess.run(cmd, cwd=AP_DIR, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError('alphapai 调用失败(exit %s)\n%s' % (p.returncode, (p.stderr or '')[-1200:]))
    return p.stdout


def parse_payload(out):
    """从 CLI 输出里取出 {answer, references}。"""
    i = out.find('{')
    if i < 0:
        raise RuntimeError('未解析到 JSON：' + out[:400])
    d = json.loads(out[i:])
    if isinstance(d, dict) and 'data' in d and isinstance(d['data'], dict):
        d = d['data']
    return d.get('answer', '') or '', d.get('references', []) or []


NUM = re.compile(r'\d[\d,]*\.?\d*\s*(?:亿元|亿|万亿|美元|美金|万片|%|倍|元/GB|美元/GB|x|X|×)')


def rival_numbers(refs):
    """★ 从 references 里抽「别家给的数」——这才是 dispersion_basis 的原料。
    AlphaPai 的结论可以不信，但它引用的原句是可回溯的一手材料。"""
    out, seen = [], set()
    for r in refs or []:
        txt = (r.get('sentence') or r.get('chunk') or '').strip()
        if not txt:
            continue
        hits = NUM.findall(txt)
        if len(hits) < 2:            # 至少两个数才算「给了口径」
            continue
        key = (r.get('id'), txt[:60])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            'inst': r.get('instShortName') or r.get('teamName') or '未标注',
            'date': (r.get('publishDate') or '')[:10],
            'type': r.get('type'),
            'title': (r.get('title') or '')[:90],
            'url': r.get('url'),
            'page': r.get('page'),
            'numbers': hits[:12],
            'quote': txt[:600],          # 逐字，供 evidence[].quote 直接用
        })
    return out


def cov_stats(refs):
    """覆盖密度：按机构去重的家数 + 按类型分布 → 09 §4a 的 coverage 与形态判定。"""
    insts, types = {}, {}
    for r in refs or []:
        i = r.get('instShortName') or r.get('teamName') or '未标注'
        insts[i] = insts.get(i, 0) + 1
        t = r.get('type') or '?'
        types[t] = types.get(t, 0) + 1
    named = {k: v for k, v in insts.items() if k != '未标注'}
    return {'n_refs': len(refs or []), 'n_inst_named': len(named),
            'by_inst': dict(sorted(insts.items(), key=lambda x: -x[1])),
            'by_type': dict(sorted(types.items(), key=lambda x: -x[1]))}


def slug(s, n=34):
    s = re.sub(r'[^0-9A-Za-z一-龥]+', '_', s).strip('_')
    return s[:n] or 'probe'


def save(ticker, probe, key, obj, raw_md):
    d = os.path.join(SKILL, '_workspace', ticker, 'probe')
    os.makedirs(d, exist_ok=True)
    base = os.path.join(d, '%s_%s' % (probe, slug(key)))
    json.dump(obj, open(base + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(base + '.md', 'w', encoding='utf-8').write(raw_md)
    return base


def envelope(probe, ticker, question, answer, refs, extra=None):
    """统一信封。provisional 铁律写进数据本身，回填时想绕都绕不过去。"""
    o = {
        'probe': probe, 'ticker': ticker, 'asked_at': None,   # 时间由调用方 stamp，脚本不取系统时间
        'question': question,
        'provisional': True,
        'usage_rule': ('AlphaPai 产出＝候选，不是结论。进 page_model.part4 之前必须逐条回 '
                       'research-rag（rag_query.py search/get_doc）或 page_model 复核；'
                       '核不上的一律丢弃或标 coverage:0，不得直接引用。'),
        'answer_md': answer,
        'rival_numbers': rival_numbers(refs),
        'coverage': cov_stats(refs),
    }
    if extra:
        o.update(extra)
    return o


def main():
    ap = argparse.ArgumentParser(description='用 AlphaPai 深化叙事链拆解（Phase 5.5）')
    sub = ap.add_subparsers(dest='probe', required=True)

    c = sub.add_parser('challenge', help='agent mode 9：挑战一条叙事/观点，找最先断的一环')
    c.add_argument('--ticker', required=True); c.add_argument('--name', required=True)
    c.add_argument('--claim', required=True, help='观点全文，★必须带数字（利润/倍数/市值/份额）')
    c.add_argument('--concern', default='', help='关键前提，分号分隔（会进检索）')
    c.add_argument('--since', default=''); c.add_argument('--until', default='')
    c.add_argument('--label', default='', help='存盘用的短名，默认取 claim 前若干字')

    d = sub.add_parser('decompose', help='qa Think：把已有 chain 喂进去，问它缺哪些环')
    d.add_argument('--ticker', required=True); d.add_argument('--name', required=True)
    d.add_argument('--narrative', required=True, help='叙事名，如「存储超级周期」')
    d.add_argument('--chain', default='', help='已有推演链（每行一环）')
    d.add_argument('--chain-file', default='', help='从文件读推演链')
    d.add_argument('--since', default=''); d.add_argument('--until', default='')

    v = sub.add_parser('coverage', help='recall：测某一格的覆盖密度，判零覆盖')
    v.add_argument('--ticker', required=True)
    v.add_argument('--topic', required=True, help='候选次级矛盾的检索词')
    v.add_argument('--types', default=COVERAGE_TYPES)
    v.add_argument('--since', default=''); v.add_argument('--until', default='')

    a = ap.parse_args()
    if not os.path.exists(AP):
        sys.exit('未找到 alphapai_client.py：%s\n请先安装/升级 alphapai-research skill。' % AP)

    if a.probe == 'challenge':
        q = CHALLENGE_Q.format(name=a.name, ticker=a.ticker, claim=a.claim)
        concern = CHALLENGE_CONCERN.format(concern=(a.concern or '该观点的关键前提'))
        args = ['agent', '--mode', '9', '--question', q, '--template-text', a.claim,
                '--concern', concern, '--only-answer']
        if a.since: args += ['--start', a.since]
        if a.until: args += ['--end', a.until]
        ans, refs = parse_payload(run_ap(args))
        obj = envelope('challenge', a.ticker, q, ans, refs, {'claim': a.claim, 'concern': a.concern})
        base = save(a.ticker, 'challenge', a.label or a.claim, obj, ans)

    elif a.probe == 'decompose':
        chain = a.chain
        if a.chain_file:
            chain = open(a.chain_file, encoding='utf-8').read()
        if not chain.strip():
            sys.exit('--chain 或 --chain-file 至少给一个（不给已有链，它只会复述你已经知道的东西）')
        q = DECOMPOSE_Q.format(name=a.name, ticker=a.ticker, narrative=a.narrative, chain=chain.strip())
        args = ['qa', '--question', q, '--mode', 'Think']
        if a.since: args += ['--start', a.since]
        if a.until: args += ['--end', a.until]
        ans, refs = parse_payload(run_ap(args))
        obj = envelope('decompose', a.ticker, q, ans, refs, {'narrative': a.narrative})
        base = save(a.ticker, 'decompose', a.narrative, obj, ans)

    else:  # coverage
        args = ['recall', '--query', a.topic, '--type', a.types, '--no-cutoff']
        if a.since: args += ['--start', a.since]
        if a.until: args += ['--end', a.until]
        out = run_ap(args)
        i = out.find('{'); j = out.find('[')
        k = min([x for x in (i, j) if x >= 0] or [-1])
        if k < 0: sys.exit('recall 未返回可解析结果：' + out[:300])
        raw = json.loads(out[k:])
        refs = raw if isinstance(raw, list) else (raw.get('data') or raw.get('references') or [])
        if isinstance(refs, dict): refs = refs.get('list') or []
        st = cov_stats(refs)
        verdict = ('零覆盖（页面画虚线圈，coverage:0）' if st['n_inst_named'] == 0 else
                   '低覆盖（1-2 家，便宜的 alpha）' if st['n_inst_named'] <= 2 else
                   '已被广泛覆盖（先查是否单峰窄＝已定价，不是矛盾）')
        obj = {'probe': 'coverage', 'ticker': a.ticker, 'topic': a.topic, 'provisional': True,
               'usage_rule': 'coverage 家数只是密度，形态(双峰/单峰宽/零覆盖)必须看 rival_numbers 的实际数值分布。',
               'verdict': verdict, 'coverage': st, 'rival_numbers': rival_numbers(refs)}
        base = save(a.ticker, 'coverage', a.topic, obj,
                    '# coverage probe\n\n' + a.topic + '\n\n' + json.dumps(st, ensure_ascii=False, indent=1))

    print('probe=%s  → %s.json / .md' % (a.probe, base))
    print('  覆盖: %s 条引用 / %s 家具名机构' % (obj['coverage']['n_refs'], obj['coverage']['n_inst_named']))
    print('  按类型:', obj['coverage']['by_type'])
    print('  抽到「别家给的数」%d 条：' % len(obj['rival_numbers']))
    for r in obj['rival_numbers'][:8]:
        print('   · %-10s %s  %s' % (r['inst'], r['date'], ' / '.join(r['numbers'][:6])))
    print('\n⚠️ provisional=true —— 逐条回 research-rag 复核后才能进 part4。')


if __name__ == '__main__':
    main()
