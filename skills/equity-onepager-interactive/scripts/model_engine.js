/* =============================================================================
 * equity-onepager-interactive · model_engine.js
 * Pure client-side compute engine for Part 3 (P&L model + 8 valuation paradigms).
 * No DOM. Attaches to window.EONE (browser) and module.exports (node test).
 *
 * Contract: operates on the `part3` slice of page_model.json. Everything the
 * page shows in Part 3 is derived here, so editing any assumption -> recompute()
 * -> re-render. Colour semantics mirror buyside-model-builder:
 *   actuals = locked (blue)   assumptions = editable (yellow)   rest = computed.
 * ========================================================================== */
(function (root) {
  'use strict';

  // ---- small numeric helpers -------------------------------------------------
  var clamp = function (x, lo, hi) { return Math.max(lo, Math.min(hi, x)); };
  var num = function (x, d) { x = parseFloat(x); return isFinite(x) ? x : (d === undefined ? 0 : d); };
  var last = function (a) { return a && a.length ? a[a.length - 1] : 0; };
  var mean = function (a) { var s = 0, n = 0, i; for (i = 0; i < a.length; i++) { if (isFinite(a[i])) { s += a[i]; n++; } } return n ? s / n : 0; };
  var round = function (x, p) { var f = Math.pow(10, p || 0); return Math.round((x + Number.EPSILON) * f) / f; };

  // broadcast helper: length-1 array -> constant; length-N -> index i; scalar ok
  function at(arr, i, def) {
    if (arr == null) return (def === undefined ? 0 : def);
    if (typeof arr === 'number') return arr;
    if (!arr.length) return (def === undefined ? 0 : def);
    if (arr.length === 1) return num(arr[0], def);
    return num(arr[Math.min(i, arr.length - 1)], def);
  }

  /* ---------------------------------------------------------------------------
   * recomputePL(part3)
   * History columns = LOCKED ACTUALS (from hist_actual, sourced from iFind).
   * Forecast columns = segment Q x P x GM drivers + opex assumption rates,
   * run through the universal profit bridge. Mirrors buyside-model-builder's
   * "blue actual vs yellow assumption" split so the interactive chain is honest.
   * opex rates accept a length-1 array (constant, broadcast) or length-F array.
   * Returns { years, H, F, seg:[{name,q,p,rev,gp,gm}], byYear:[], revYoY }.
   * ------------------------------------------------------------------------- */
  // 母段 Q×P 推进（与普通分部同一套 factor 自校准逻辑），供 split 子段拆分用
  function driveQP(node, F) {
    var hq = (node.hist && node.hist.q) || [], hp = (node.hist && node.hist.p) || [],
        hr = (node.hist && node.hist.rev) || [];
    var a = node.assume || {}, qg = a.q_growth || [], pg = a.p_growth || [];
    var facs = [], i;
    for (i = 0; i < hq.length; i++)
      if (isFinite(hq[i]) && isFinite(hp[i]) && hq[i] * hp[i] !== 0 && isFinite(hr[i]))
        facs.push(hr[i] / (hq[i] * hp[i]));
    var factor = facs.length ? mean(facs) : num(node.unit_rev_factor, 1);
    var q = hq.slice(), p = hp.slice(), rev = hr.slice();
    var qPrev = last(hq), pPrev = last(hp);
    for (i = 0; i < F; i++) {
      var qi = qPrev * (1 + at(qg, i)), pi = pPrev * (1 + at(pg, i));
      q.push(qi); p.push(pi); rev.push(qi * pi * factor); qPrev = qi; pPrev = pi;
    }
    return { key: node.key, name: node.name, factor: factor, q: q, p: p, rev: rev };
  }

  function recomputePL(m) {
    m = m || {};
    var histY = (m.hist_years || []).slice();
    var fcstY = (m.forecast_years || []).slice();
    var years = histY.concat(fcstY);
    var H = histY.length, F = fcstY.length, T = years.length;
    var ha = m.hist_actual || {};
    var op = m.opex || {};
    var shares = num(m.shares_yi, 0);

    /* ---- 母段（parents）：先把「合计」算出来，子段再按 share 拆 ------------
     * 用途：一个披露分部里混着两门生意（口径/单位都不同），但披露只给合计。
     * 母段不进 P&L（不重复计收入），只作为子段的分母。share 是可调假设。 */
    var PAR = {};
    (m.parents || []).forEach(function (pn) { PAR[pn.key] = driveQP(pn, F); });
    var SPL = m.splits || {};
    function shareAt(pkey, t) {                     // 拆分比例 λ：历史锁定 + 预测可调
      var sp = SPL[pkey]; if (!sp) return 1;
      var arr = (t < H) ? (sp.share_hist || []) : (sp.share || []);
      var i = (t < H) ? t : (t - H);
      var v = num(arr[Math.min(i, Math.max(0, arr.length - 1))], 0);
      return clamp(v, 0, 1);
    }

    // ---- per-segment Q/P/Rev/GM (history from disclosure, forecast from drivers)
    var segs = (m.segments || []).map(function (s) {
      var hq = (s.hist && s.hist.q) || [], hp = (s.hist && s.hist.p) || [],
          hr = (s.hist && s.hist.rev) || [], hg = (s.hist && s.hist.gm) || [];
      var a = s.assume || {};
      var qg = a.q_growth || [], pg = a.p_growth || [], gmF = a.gm || [];
      var i, q, p, rev, gm, factor;

      if (s.derive && PAR[s.derive.parent]) {
        /* --- 派生段：收入 = 母段 × λ（或 1−λ）；价走自己的口径；量 = 收入 ÷ 价 ---
         * 量是「隐含量」（与上游 TAM 报告同口径），所以 量×价＝收入 恒等成立，
         * 不存在对账误差。λ 与 价 是驱动，量是结果。 */
        var par = PAR[s.derive.parent], resid = (s.derive.take === 'residual');
        factor = num(s.unit_rev_factor, 1);
        p = hp.slice(); rev = []; q = []; gm = hg.slice();
        var pPrev0 = last(hp);
        for (i = 0; i < F; i++) { pPrev0 = pPrev0 * (1 + at(pg, i)); p.push(pPrev0); gm.push(at(gmF, i, last(hg))); }
        for (i = 0; i < T; i++) {
          var lam = shareAt(s.derive.parent, i);
          var r = num(par.rev[i]) * (resid ? (1 - lam) : lam);
          rev.push(r);
          q.push((isFinite(p[i]) && p[i] * factor !== 0) ? r / (p[i] * factor) : 0);
        }
      } else {
        // calibrate unit factor so rev = q*p*factor ties to disclosed rev (auto-units)
        var facs = [];
        for (i = 0; i < hq.length; i++)
          if (isFinite(hq[i]) && isFinite(hp[i]) && hq[i] * hp[i] !== 0 && isFinite(hr[i]))
            facs.push(hr[i] / (hq[i] * hp[i]));
        factor = facs.length ? mean(facs) : (s.unit_rev_factor || 1);
        q = hq.slice(); p = hp.slice(); rev = hr.slice(); gm = hg.slice();
        var qPrev = last(hq), pPrev = last(hp);
        for (i = 0; i < F; i++) {
          var qi = qPrev * (1 + at(qg, i)), pi = pPrev * (1 + at(pg, i));
          q.push(qi); p.push(pi); rev.push(qi * pi * factor);
          gm.push(at(gmF, i, last(hg))); qPrev = qi; pPrev = pi;
        }
      }
      var gp = rev.map(function (r, k) { return r * num(gm[k]); });
      return { name: s.name, key: s.key, factor: factor, derived: !!s.derive,
               q: q, p: p, rev: rev, gm: gm, gp: gp };
    });

    var byYear = [];
    for (var t = 0; t < T; t++) {
      var isF = t >= H, fi = t - H, k;
      var row;
      if (!isF) {
        // ----- HISTORY: trust disclosed actuals; fall back to segment sums -----
        var rev = (ha.rev && isFinite(ha.rev[t])) ? ha.rev[t] : segs.reduce(function (a, s) { return a + num(s.rev[t]); }, 0);
        var gm = (ha.gross_margin && isFinite(ha.gross_margin[t])) ? ha.gross_margin[t]
                 : (rev ? segs.reduce(function (a, s) { return a + num(s.gp[t]); }, 0) / rev : 0);
        var gp = rev * gm;
        var sga = rev * (ha.sga_rate ? num(ha.sga_rate[t]) : 0);
        var rnd = rev * (ha.rnd_rate ? num(ha.rnd_rate[t]) : 0);
        var ebit = (ha.ebit && isFinite(ha.ebit[t])) ? ha.ebit[t] : gp - sga - rnd;
        var da = (ha.da && isFinite(ha.da[t])) ? ha.da[t] : 0;
        var ebitda = (ha.ebitda && isFinite(ha.ebitda[t])) ? ha.ebitda[t] : ebit + da;
        var np = (ha.net_profit && isFinite(ha.net_profit[t])) ? ha.net_profit[t] : ebit * (1 - num(op.tax_rate && op.tax_rate[0], 0.15));
        row = { rev: rev, gp: gp, gm: gm, sga: sga, rnd: rnd, ebit: ebit, da: da, ebitda: ebitda,
                pretax: ebit, tax: ebit - np, netProfit: np };
      } else {
        // ----- FORECAST: build from drivers + assumption rates -----
        var rev = segs.reduce(function (a, s) { return a + num(s.rev[t]); }, 0);
        var gp = segs.reduce(function (a, s) { return a + num(s.gp[t]); }, 0);
        var gm = rev ? gp / rev : 0;
        /* 费用层：优先用回归式 销售+管理 = FC(固定) + VC×营收。
         * 手填费率会把经营杠杆抹平——固定费用摊薄本身就是模型要展示的机制。 */
        var reg = op.sga_reg;
        var sga = (reg && (isFinite(reg.fc) || isFinite(reg.vc)))
                  ? (num(reg.fc) + num(reg.vc) * rev)
                  : rev * at(op.sga_rate, fi, 0);
        var rnd = rev * at(op.rnd_rate, fi, 0);
        var impair = at(op.impair, fi, 0);           // 信用/资产减值（显式一行，可调）
        var ebit = gp - sga - rnd - impair + at(op.other_op, fi, 0);
        var da = at(op.da, fi, 0);
        var ebitda = ebit + da;
        var pretax = ebit + at(op.other_nonop, fi, 0) - at(op.net_interest, fi, 0);
        var tax = pretax * at(op.tax_rate, fi, 0);
        var minority = pretax * at(op.minority_rate, fi, 0);
        var np = pretax - tax - minority;
        row = { rev: rev, gp: gp, gm: gm, sga: sga, rnd: rnd, impair: impair, ebit: ebit, da: da, ebitda: ebitda,
                pretax: pretax, tax: tax, netProfit: np };
      }
      row.year = years[t]; row.isForecast = isF;
      row.ebitMargin = row.rev ? row.ebit / row.rev : 0;
      row.netMargin = row.rev ? row.netProfit / row.rev : 0;
      row.eps = shares ? row.netProfit / shares : 0;
      byYear.push(row);
    }

    // 母段（合计）也导出：页面要展示「机房温控合计 = 液冷 + 非液冷」的闭合关系
    var parents = (m.parents || []).map(function (pn) {
      var pr = PAR[pn.key], sh = [];
      for (var i = 0; i < T; i++) sh.push(shareAt(pn.key, i));
      return { key: pn.key, name: pn.name, q: pr.q, p: pr.p, rev: pr.rev, share: sh, factor: pr.factor };
    });
    return { years: years, H: H, F: F, seg: segs, byYear: byYear, parents: parents,
             fcstStart: H, revYoY: yoy(byYear.map(function (r) { return r.rev; })) };
  }

  function yoy(a) {
    return a.map(function (v, i) { return i && a[i - 1] ? (v / a[i - 1] - 1) : null; });
  }

  /* ---------------------------------------------------------------------------
   * Valuation paradigms. Each returns { mcap (亿), detail, ok }.
   * pl = output of recomputePL, used to LINK forward profit/ebitda so that
   * editing a P&L assumption flows into the valuation (the live chain).
   * ------------------------------------------------------------------------- */
  function fwdProfit(pl, p) {
    // pick a forecast year's net profit as forward profit; p.year_offset 0-based
    // into forecast years, default the last forecast year.
    if (!pl || !pl.byYear.length) return num(p.fwd_profit_yi, 0);
    if (isFinite(p.fwd_profit_yi) && p.link !== true) return num(p.fwd_profit_yi);
    var fy = pl.byYear.filter(function (r) { return r.isForecast; });
    if (!fy.length) return num(p.fwd_profit_yi, last(pl.byYear).netProfit);
    var idx = clamp(num(p.year_offset, fy.length - 1), 0, fy.length - 1);
    return fy[idx].netProfit;
  }
  function fwdEbitda(pl, p) {
    if (isFinite(p.ebitda_yi) && p.link !== true) return num(p.ebitda_yi);
    var fy = pl && pl.byYear.filter(function (r) { return r.isForecast; });
    if (!fy || !fy.length) return num(p.ebitda_yi, 0);
    var idx = clamp(num(p.year_offset, fy.length - 1), 0, fy.length - 1);
    return fy[idx].ebitda;
  }

  var PARADIGM = {
    // 1) 对标大哥法 -----------------------------------------------------------
    // 硬规则: 必须点名大哥(leader_name); 默认口径 basis='revenue' = 收入占比→市值占比
    leader: function (p, pl) {
      var lc = num(p.leader_current), lm = num(p.leader_mcap), fs = num(p.follower_steady);
      var vpot = lc ? (fs / lc) * lm : 0;
      var adj = clamp(1 + num(p.adj), 0.70, 1.30);
      var vadj = vpot * adj;
      var mcap = vadj / Math.pow(1 + num(p.r, 0.09), num(p.n, 0));   // ★折现率统一 8–10% 档，缺省 9%（2026-08-12）
      var basis = (p.basis === 'profit' || p.metric === '利润') ? '利润' : '收入';
      var who = p.leader_name || '⚠️大哥未指明';
      return { mcap: mcap, ok: lc > 0, leaderName: p.leader_name || null, basis: basis,
        detail: '对标 ' + who + ' · 本司稳态' + basis + fmt(fs) + '亿 / 大哥' + basis + fmt(lc) +
                '亿 = ' + pct(lc ? fs / lc : 0) + ' × 大哥市值' + fmt(lm) + '亿 ×调整' + pct(adj - 1) +
                (num(p.n) ? ' ÷(1+' + pct(p.r) + ')^' + num(p.n) : '') };
    },
    // 2) PE 法 ---------------------------------------------------------------
    pe: function (p, pl) {
      var prof = fwdProfit(pl, p), pe = num(p.pe, 20), r = num(p.r, 0.09), n = num(p.n, 0);   // ★r 缺省 9%（8–10% 档）
      var mcap = prof * pe / Math.pow(1 + r, n);
      return { mcap: mcap, ok: prof !== 0,
        detail: 'Forward净利' + fmt(prof) + '亿 ×' + fmt(pe) + 'x' + (n ? ' ÷(1+' + pct(r) + ')^' + n : '') };
    },
    // 3) PEG 法 --------------------------------------------------------------
    peg: function (p, pl) {
      var prof = isFinite(p.profit_yi) && p.link !== true ? num(p.profit_yi) : fwdProfit(pl, p);
      var g = clamp(num(p.g, 20), 0, num(p.g_cap, 50));
      var pegt = num(p.peg, 1.0);
      var targetPe = pegt * g;
      var mcap = prof * targetPe;
      return { mcap: mcap, ok: prof > 0 && g > 0,
        detail: 'PE=PEG' + fmt(pegt) + '×增速' + fmt(g) + '% =' + fmt(targetPe) + 'x ×净利' + fmt(prof) + '亿' };
    },
    // 4) SOTP (A+B) ----------------------------------------------------------
    sotp: function (p, pl) {
      var segs = p.segments || [], sum = 0, lines = [];
      segs.forEach(function (s) {
        var v = num(s.profit_yi) * num(s.mult);
        sum += v;
        lines.push(s.name + ' ' + fmt(s.profit_yi) + '亿×' + fmt(s.mult) + 'x=' + fmt(v) + '亿');
      });
      var nc = num(p.net_cash_yi);
      var mcap = sum + nc;
      return { mcap: mcap, ok: segs.length > 0,
        detail: lines.join(' | ') + (nc ? ' | +净现金' + fmt(nc) + '亿' : '') };
    },
    // 5) PB-ROE --------------------------------------------------------------
    pbroe: function (p, pl) {
      var roe = num(p.roe), coe = num(p.coe, 0.10), bv = num(p.equity_yi);
      var pb = coe ? roe / coe : 0;
      var mcap = bv * pb;
      return { mcap: mcap, ok: bv > 0 && coe > 0,
        detail: '净资产' + fmt(bv) + '亿 ×PB(' + pct(roe) + '/' + pct(coe) + '=' + fmt(pb) + ')' };
    },
    // 6) EV/EBITDA -----------------------------------------------------------
    evebitda: function (p, pl) {
      var eb = fwdEbitda(pl, p), mult = num(p.mult, 10), ndebt = num(p.net_debt_yi);
      var ev = eb * mult, mcap = ev - ndebt;
      return { mcap: mcap, ok: eb !== 0,
        detail: 'EBITDA' + fmt(eb) + '亿×' + fmt(mult) + 'x=EV' + fmt(ev) + '亿 −净债务' + fmt(ndebt) + '亿' };
    },
    // 7) 终局份额法 -----------------------------------------------------------
    endgame: function (p, pl) {
      var tam = num(p.tam_yi), sh = num(p.share), nm = num(p.net_margin), pe = num(p.pe, 22),
          r = num(p.r, 0.09), n = num(p.n, 0);   // ★r 缺省 9%（8–10% 档）
      var terminal = tam * sh * nm * pe;
      var mcap = terminal / Math.pow(1 + r, n);
      return { mcap: mcap, ok: tam > 0 && sh > 0,
        detail: 'TAM' + fmt(tam) + '亿×份额' + pct(sh) + '×净利率' + pct(nm) + '×' + fmt(pe) + 'x ÷(1+' + pct(r) + ')^' + n };
    },
    // 8) 反推隐含 (诊断, 默认权重0) --------------------------------------------
    implied: function (p, pl, ctx) {
      var cur = num((ctx && ctx.currentMcap) || p.current_mcap_yi);
      var peMid = num(p.pe_mid, 20), nm = num(p.net_margin, 0.10);
      var impProfit = peMid ? cur / peMid : 0;
      var impRev = nm ? impProfit / nm : 0;
      return { mcap: cur, ok: true, diagnostic: true,
        detail: '市场隐含: 净利' + fmt(impProfit) + '亿(PE' + fmt(peMid) + 'x) → 收入' + fmt(impRev) + '亿(净利率' + pct(nm) + ')' };
    }
  };

  /* ---------------------------------------------------------------------------
   * runValuation(valuation, pl) -> full valuation result with weighted blend.
   * ------------------------------------------------------------------------- */
  function runValuation(v, pl) {
    v = v || {};
    var shares = num(v.shares_yi, 0);
    var cur = num(v.current_mcap_yi, 0);
    var ctx = { currentMcap: cur, shares: shares };
    var rows = (v.paradigms || []).map(function (pd) {
      var fn = PARADIGM[pd.key];
      var res = fn ? fn(pd.params || {}, pl, ctx) : { mcap: 0, ok: false, detail: 'unknown paradigm' };
      var mcap = res.mcap;
      return {
        key: pd.key, name: pd.name, weight: num(pd.weight, 0),
        diagnostic: !!res.diagnostic, ok: res.ok !== false,
        mcap: mcap, target: shares ? mcap / shares : 0,
        odds: cur ? mcap / cur - 1 : 0, detail: res.detail
      };
    });

    // weighted blend over non-diagnostic, weight>0, finite paradigms
    var active = rows.filter(function (r) { return !r.diagnostic && r.weight > 0 && isFinite(r.mcap) && r.ok; });
    var wsum = active.reduce(function (a, r) { return a + r.weight; }, 0);
    var blendMcap = wsum ? active.reduce(function (a, r) { return a + r.weight * r.mcap; }, 0) / wsum : 0;
    active.forEach(function (r) { r.wnorm = wsum ? r.weight / wsum : 0; });

    // dispersion / range over active paradigms
    var caps = active.map(function (r) { return r.mcap; }).filter(isFinite).sort(function (a, b) { return a - b; });
    var vmin = caps.length ? caps[0] : 0, vmax = caps.length ? caps[caps.length - 1] : 0;
    var vmed = caps.length ? (caps.length % 2 ? caps[(caps.length - 1) / 2] : (caps[caps.length / 2 - 1] + caps[caps.length / 2]) / 2) : 0;
    var disp = vmax ? (vmax - vmin) / vmax : 0;
    var verdict = disp < 0.20 ? { level: 'ok', text: '多锚自洽(离散<20%)·可用点估计' }
                 : disp <= 0.50 ? { level: 'warn', text: '有分歧(离散20–50%)·建议看区间' }
                 : { level: 'risk', text: '冲突(离散>50%)·不宜出单值,查分歧变量' };

    return {
      rows: rows, active: active,
      blend: { mcap: blendMcap, target: shares ? blendMcap / shares : 0, odds: cur ? blendMcap / cur - 1 : 0, wsum: wsum },
      range: { min: vmin, max: vmax, median: vmed, dispersion: disp, verdict: verdict },
      currentMcap: cur, shares: shares
    };
  }

  // ---- formatting used inside detail strings --------------------------------
  function fmt(x) { x = parseFloat(x); if (!isFinite(x)) return '—'; return (Math.abs(x) >= 100 ? round(x, 0) : round(x, 1)).toLocaleString(); }
  function pct(x) { x = parseFloat(x); if (!isFinite(x)) return '—'; return round(x * 100, 1) + '%'; }

  var EONE = {
    recomputePL: recomputePL, runValuation: runValuation,
    PARADIGM: PARADIGM, _util: { clamp: clamp, num: num, mean: mean, round: round, fmt: fmt, pct: pct, yoy: yoy }
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = EONE;
  root.EONE = EONE;
})(typeof window !== 'undefined' ? window : this);
