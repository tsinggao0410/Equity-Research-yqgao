/**
 * 一页纸反馈平台 Worker —— 既托管报告静态页，又收标注。
 *
 *   GET  /                      → site/ 里的报告索引（deploy_page.py 生成）
 *   GET  /<ticker>/             → 该标的报告（site/<ticker>/index.html）
 *   POST /api/ann               → 读者提交标注（无需鉴权，写入 KV）
 *   GET  /api/ann?report_id=X   → 我拉标注（需 x-fb-token = FB_ADMIN_TOKEN）
 *   POST /api/status            → 我标记已处理（需 token），下次 pull 可 --only-new
 *   GET  /api/health            → 存活 + KV 绑定自检
 *
 * KV：key = ann:<report_id>:<item_id>，value = 标注 JSON（含 server 侧 recv_at）。
 * 设计取舍：读者只写不读（GET 需 token）——避免互相看到彼此草稿式标注；
 * 「答复」通过我重出 v_n+1 页面的 feedback.resolved 广播给所有读者。
 */
const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,OPTIONS',
  'access-control-allow-headers': 'content-type,x-fb-token',
  'access-control-max-age': '86400',
};
const J = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json;charset=utf-8', ...CORS } });

const S = (v, n) => (v == null ? '' : String(v).slice(0, n));
const KEY = (rid, id) => `ann:${rid}:${id}`;

function clean(it, ctx) {
  const id = S(it.id, 40).replace(/[^A-Za-z0-9_-]/g, '') || ('A' + Math.random().toString(36).slice(2, 10));
  return {
    id,
    type: ['q', 'd', 's', 'i', 'o'].includes(it.type) ? it.type : 'q',
    quote: S(it.quote, 400),
    note: S(it.note, 2000),
    path: S(it.path, 160),
    sec: S(it.sec, 60),
    sec_title: S(it.sec_title, 80),
    ver: S(it.ver, 20),
    reader: S(it.reader || ctx.reader, 40),
    created: S(it.created, 24),
    report_id: ctx.report_id,
    ticker: ctx.ticker,
    recv_at: new Date().toISOString().slice(0, 19).replace('T', ' '),
    status: 'new',
  };
}

async function listAll(kv, prefix) {
  const out = [];
  let cursor;
  do {
    const r = await kv.list({ prefix, cursor, limit: 1000 });
    cursor = r.list_complete ? null : r.cursor;
    for (const k of r.keys) out.push(k.name);
  } while (cursor);
  return out;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname;
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

    if (p === '/api/health') {
      return J({ ok: true, kv: !!env.ANNOT, admin_token_set: !!env.FB_ADMIN_TOKEN, ts: new Date().toISOString() });
    }

    if (p === '/api/ann' && request.method === 'POST') {
      if (!env.ANNOT) return J({ ok: false, error: 'KV 未绑定(ANNOT)' }, 500);
      let b;
      try { b = await request.json(); } catch { return J({ ok: false, error: 'bad json' }, 400); }
      const report_id = S(b.report_id, 64).replace(/[^A-Za-z0-9_.-]/g, '');
      const items = Array.isArray(b.items) ? b.items.slice(0, 200) : [];
      if (!report_id) return J({ ok: false, error: 'report_id 必填' }, 400);
      if (!items.length) return J({ ok: true, saved: 0 });
      const ctx = { report_id, ticker: S(b.ticker, 24), reader: S(b.reader, 40) };
      let saved = 0;
      for (const raw of items) {
        const it = clean(raw, ctx);
        await env.ANNOT.put(KEY(report_id, it.id), JSON.stringify(it));   // 同 id 覆盖 = 幂等重传
        saved++;
      }
      return J({ ok: true, saved });
    }

    if (p === '/api/ann' && request.method === 'GET') {
      if (request.headers.get('x-fb-token') !== env.FB_ADMIN_TOKEN || !env.FB_ADMIN_TOKEN)
        return J({ ok: false, error: 'unauthorized' }, 401);
      if (!env.ANNOT) return J({ ok: false, error: 'KV 未绑定(ANNOT)' }, 500);
      const rid = S(url.searchParams.get('report_id'), 64).replace(/[^A-Za-z0-9_.-]/g, '');
      const onlyNew = url.searchParams.get('only_new') === '1';
      const names = await listAll(env.ANNOT, rid ? `ann:${rid}:` : 'ann:');
      const items = [];
      for (const n of names) {
        const v = await env.ANNOT.get(n, 'json');
        if (!v) continue;
        if (onlyNew && v.status && v.status !== 'new') continue;
        items.push(v);
      }
      items.sort((a, b) => String(a.created).localeCompare(String(b.created)));
      return J({ ok: true, count: items.length, items });
    }

    if (p === '/api/status' && request.method === 'POST') {
      if (request.headers.get('x-fb-token') !== env.FB_ADMIN_TOKEN || !env.FB_ADMIN_TOKEN)
        return J({ ok: false, error: 'unauthorized' }, 401);
      let b; try { b = await request.json(); } catch { return J({ ok: false, error: 'bad json' }, 400); }
      const rid = S(b.report_id, 64).replace(/[^A-Za-z0-9_.-]/g, '');
      const ids = Array.isArray(b.ids) ? b.ids.slice(0, 500) : [];
      const status = ['new', 'triaged', 'resolved', 'wontfix'].includes(b.status) ? b.status : 'triaged';
      let n = 0;
      for (const id of ids) {
        const k = KEY(rid, S(id, 40));
        const v = await env.ANNOT.get(k, 'json');
        if (!v) continue;
        v.status = status; v.status_at = new Date().toISOString().slice(0, 19).replace('T', ' ');
        if (b.answer) v.answer = S(b.answer, 1200);
        await env.ANNOT.put(k, JSON.stringify(v)); n++;
      }
      return J({ ok: true, updated: n, status });
    }

    if (p.startsWith('/api/')) return J({ ok: false, error: 'not found' }, 404);

    // 其余交给静态资源（site/ 下的报告页）
    if (env.ASSETS) return env.ASSETS.fetch(request);
    return new Response('no assets bound', { status: 404 });
  },
};
