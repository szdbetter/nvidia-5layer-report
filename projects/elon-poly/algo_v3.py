"""
Algo V3: Regime-aware Elon tweet prediction  [ITERATION #8]

Bug fix: resolved bracket 匹配改用 numeric overlap (原用string比较失败)
       — trailing spaces / different dashes / format差异 → 匹配失效
       — 现在用: resolved_val ∈ [bracket_lo, bracket_hi] 判断

Data: uses day5_price_snapshots.json (70 weeks, 2024-05 to 2025-09) which has
      actual Polymarket day-5 prices AND resolved brackets.
      weekly_history.json (35 weeks, 2025-11 to 2026-03) is a DIFFERENT event
      series with zero date overlap — NOT combinable for backtesting.

Regime detection: uses resolved_val (weekly tweet count) as regime proxy,
      the same data we are predicting on — so regime is based on recent pace.
"""
import json, re, math, statistics

SNAPS_FILE = '/root/.openclaw/workspace/projects/elon-poly/day5_price_snapshots.json'

with open(SNAPS_FILE) as f:
    raw_snaps = json.load(f)


def parse_val(b):
    """Parse bracket string → (lo, hi, midpoint). Returns (None,None,None) on failure."""
    b = b.strip()
    m = re.match(r'^<(\d+)$', b)
    if m:
        hi = int(m.group(1)) - 1
        return 0, hi, hi / 2
    m = re.match(r'^(\d+)\+$', b)
    if m:
        lo = int(m.group(1))
        return lo, lo + 100, lo + 50
    m = re.match(r'^(\d+)[–\-](\d+)$', b)
    if m:
        lo = int(m.group(1))
        hi = int(m.group(2))
        return lo, hi, (lo + hi) / 2
    return None, None, None


def norm_cdf(x):
    t = 1 / (1 + 0.3275911 * abs(x))
    p = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 +
        t * (-1.453152027 + t * 1.061405429))))
    r = 1 - p * math.exp(-x * x)
    return 0.5 * (1 + r) if x >= 0 else 0.5 * (1 - r)


def bracket_prob(lo, hi, mu, sigma):
    sigma = max(sigma, 20)
    if hi == lo + 100:
        return 1 - norm_cdf((lo - mu) / sigma)
    if lo == 0:
        return norm_cdf((hi - mu) / sigma)
    return norm_cdf((hi - mu) / sigma) - norm_cdf((lo - mu) / sigma)


# ─── Build week list ────────────────────────────────────────────────────────
snaps = []
for s in raw_snaps:
    rb = s['resolved_bracket']
    lo, hi, val = parse_val(rb)
    if val is None:
        continue
    snaps.append({
        'start': s['start'],
        'event_id': s['event_id'],
        'resolved_val': val,
        'resolved_lo': lo,
        'resolved_hi': hi,
        'resolved_bracket': rb,
        'day5_prices': s['day5_prices'],
    })
snaps.sort(key=lambda x: x['start'])
print(f"Loaded {len(snaps)} snap weeks: {snaps[0]['start']} → {snaps[-1]['start']}")


def run_regime_backtest(lookback=12, regime_window=3, regime_threshold=1.15,
                        min_edge=0.06, kelly_frac=0.5,
                        multi_bracket=False, max_brackets=2,
                        bet=20):
    """
    Regime-aware backtest with FIXED numeric bracket matching.

    Regime detection: uses resolved tweet counts from lookback window.
    Win = resolved_val falls within the predicted bracket [lo, hi].
    """
    trades = []
    start_idx = lookback + 1

    for i in range(start_idx, len(snaps)):
        cur = snaps[i]

        # ── Regime detection using historical resolved tweet counts ─────────
        hist_vals = [snaps[j]['resolved_val'] for j in range(i - lookback, i)]
        recent    = [snaps[j]['resolved_val'] for j in range(i - regime_window, i)]

        if len(hist_vals) < 5 or len(recent) < 1:
            continue

        long_mean   = statistics.mean(hist_vals)
        recent_mean = statistics.mean(recent)

        if recent_mean > long_mean * regime_threshold:
            regime = 'HIGH'
        elif recent_mean < long_mean / regime_threshold:
            regime = 'LOW'
        else:
            regime = 'NORMAL'

        # ── Build regime-filtered distribution ─────────────────────────────
        if regime == 'HIGH':
            regime_hist = [v for v in hist_vals if v > long_mean * 1.10]
        elif regime == 'LOW':
            regime_hist = [v for v in hist_vals if v < long_mean * 0.90]
        else:
            regime_hist = hist_vals

        if len(regime_hist) < 4:
            regime_hist = hist_vals

        mu    = statistics.mean(regime_hist)
        sigma = statistics.stdev(regime_hist) if len(regime_hist) > 1 else statistics.stdev(hist_vals)

        # ── Find best bracket ─────────────────────────────────────────────
        prices = cur['day5_prices']
        best_edge = -999.0
        best_bracket = None
        best_price   = None
        best_lo = None
        best_hi = None

        for bracket_str, mp in prices.items():
            if mp <= 0.01 or mp >= 0.99:
                continue
            lo, hi, _ = parse_val(bracket_str)
            if lo is None:
                continue
            prob = bracket_prob(lo, hi, mu, sigma)
            edge = prob - mp
            if edge > best_edge:
                best_edge   = edge
                best_bracket = bracket_str
                best_price   = mp
                best_lo = lo
                best_hi = hi

        if best_edge < min_edge or best_bracket is None:
            continue

        # ── FIXED: Win = resolved_val ∈ [best_lo, best_hi] ─────────────────
        # (Previously used string equality which silently failed on spaces/dashes)
        won = (cur['resolved_val'] >= best_lo and cur['resolved_val'] <= best_hi)

        # ── Kelly sizing ──────────────────────────────────────────────────
        b        = max(0.001, (1.0 - best_price) / best_price)
        raw_f    = (best_price * (b + 1) - 1) / b
        f        = max(0.0, min(raw_f * kelly_frac, 0.25))
        stake    = bet * (f / 0.25)  # scale Kelly fraction to bet size

        if multi_bracket:
            candidates = []
            for bracket_str, mp in prices.items():
                if mp <= 0.01 or mp >= 0.99:
                    continue
                lo, hi, _ = parse_val(bracket_str)
                if lo is None:
                    continue
                prob = bracket_prob(lo, hi, mu, sigma)
                edge = prob - mp
                if edge >= min_edge:
                    candidates.append((edge, lo, hi, mp, bracket_str))
            candidates.sort(reverse=True)
            selected    = candidates[:max_brackets]
            total_edge  = sum(e for e, _, _, _, _ in selected)
            week_pnl    = 0.0
            for (e, lo, hi, mp, bracket_str) in selected:
                weight  = e / total_edge if total_edge > 0 else 1.0
                b_i     = max(0.001, (1.0 - mp) / mp)
                rf_i    = (mp * (b_i + 1) - 1) / b_i
                f_i     = max(0.0, min(rf_i * kelly_frac, 0.25))
                bet_i   = bet * (f_i / 0.25) * weight
                hit_i   = (cur['resolved_val'] >= lo and cur['resolved_val'] <= hi)
                pnl_i   = bet_i * b_i if hit_i else -bet_i
                week_pnl += pnl_i
            profit      = week_pnl
            n_brackets  = len(selected)
        else:
            profit     = stake * b if won else -stake
            n_brackets = 1

        trades.append({
            'won': won,
            'profit': round(profit, 2),
            'edge': round(best_edge, 4),
            'regime': regime,
            'week': cur['start'][:10],
            'bet_bracket': best_bracket,
            'bet_lo': best_lo,
            'bet_hi': best_hi,
            'resolved_val': cur['resolved_val'],
            'resolved_bracket': cur['resolved_bracket'],
            'price': best_price,
            'n_brackets': n_brackets,
            'mu': round(mu, 1),
            'sigma': round(sigma, 1),
        })

    if len(trades) < 4:
        return None

    profits = [t['profit'] for t in trades]
    wins     = sum(1 for t in trades if t['won'])
    total    = sum(profits)
    avg      = statistics.mean(profits)
    std      = statistics.stdev(profits) if len(profits) > 1 else 0.01
    sharpe   = round((avg / std) * math.sqrt(52), 3)

    return {
        'n': len(trades), 'wins': wins, 'wr': round(wins / len(trades), 3),
        'pnl': round(total, 2), 'sharpe': sharpe,
        'avg': round(avg, 2), 'trades': trades,
    }


# ─── Grid Search ────────────────────────────────────────────────────────────
print("=" * 70)
print(" Elon Polymarket — Iteration #8 (Regime + Fixed Numeric Matching)")
print("=" * 70)
print()

configs = []
print(f"{'参数组合':58} | 交易 | 胜率 | 总P&L | Sharpe")
print("-" * 110)

best_pnl = -9999
best_params = None
best_result = None

for lookback in [8, 12, 16, 20]:
    for rw in [2, 3, 4, 5]:
        for rt in [1.05, 1.10, 1.15, 1.20, 1.30]:
            for me in [0.04, 0.06, 0.08, 0.10, 0.12]:
                for mb in [False, True]:
                    mb_kw = {'multi_bracket': mb, 'max_brackets': 2} if mb else {}
                    r = run_regime_backtest(lookback, rw, rt, me, **mb_kw)
                    if not r:
                        continue
                    label = (f"lb={lookback} rw={rw} rt={rt:.2f} edge>{me:.0%}"
                             + (" multi" if mb else " single"))
                    configs.append({
                        'lookback': lookback, 'rw': rw, 'rt': rt, 'me': me,
                        'mb': mb, 'pnl': r['pnl'], 'sharpe': r['sharpe'],
                        'wr': r['wr'], 'n': r['n'],
                    })
                    if r['pnl'] > 0:
                        print(f"{label:58} | {r['n']:3} | {r['wr']:.0%} | ${r['pnl']:+.0f} | {r['sharpe']:+.3f}")
                    if r['pnl'] > best_pnl:
                        best_pnl = r['pnl']
                        best_params = (lookback, rw, rt, me, mb)
                        best_result = r

if best_result is None:
    print("❌ No profitable configuration found!")
    import sys; sys.exit(1)

print()
print("=" * 70)
print(f"🏆 最优: lb={best_params[0]} rw={best_params[1]} rt={best_params[2]:.2f} "
      f"edge>{best_params[3]:.0%} {'多档x2' if best_params[4] else '单档'}")
print(f"   n={best_result['n']} wins={best_result['wins']} "
      f"wr={best_result['wr']:.0%} pnl=${best_result['pnl']:+.0f} sharpe={best_result['sharpe']:+.3f}")
print("=" * 70)

# ─── Regime breakdown ───────────────────────────────────────────────────────
regime_stats = {}
for t in best_result['trades']:
    regime_stats.setdefault(t['regime'], {'wins': 0, 'n': 0, 'pnl': 0.0})
    regime_stats[t['regime']]['n'] += 1
    regime_stats[t['regime']]['pnl'] += t['profit']
    if t['won']:
        regime_stats[t['regime']]['wins'] += 1

print("\nRegime 分解:")
for regime, s in sorted(regime_stats.items()):
    wr = s['wins'] / max(s['n'], 1)
    print(f"  [{regime}] n={s['n']} wins={s['wins']} wr={wr:.0%} P&L=${s['pnl']:+.0f}")

# ─── Print trade details ────────────────────────────────────────────────────
print("\n交易明细:")
for t in best_result['trades']:
    mark = "✅" if t['won'] else "❌"
    inBracket = "∈" if t['won'] else "∉"
    print(f"  {mark} {t['week']} [{t['regime']:6}] "
          f"押{t['bet_bracket']:20} "
          f"resolved={t['resolved_val']}({inBracket}[{t['bet_lo']},{t['bet_hi']}]) "
          f"μ={t['mu']:.0f}σ={t['sigma']:.0f} "
          f"edge={t['edge']:+.0%} price={t['price']:.3f} "
          f"P&L=${t['profit']:+.0f}")

# ─── Save ───────────────────────────────────────────────────────────────────
out = {
    'params': {
        'lookback': best_params[0], 'regime_window': best_params[1],
        'regime_threshold': best_params[2], 'min_edge': best_params[3],
        'multi_bracket': best_params[4], 'max_brackets': 2,
    },
    'result': {k: v for k, v in best_result.items() if k != 'trades'},
    'trades': best_result['trades'],
    'regime_breakdown': regime_stats,
}

with open('/root/.openclaw/workspace/projects/elon-poly/algo_v3_result.json', 'w') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f"\n✅ 保存至 algo_v3_result.json")
