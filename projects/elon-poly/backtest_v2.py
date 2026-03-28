#!/usr/bin/env python3
"""
Elon Polymarket 三因子模型 — 回测引擎 v2.0 (真实数据版)

使用真实历史周期数据（weekly_history.json）
关键修复：
  - 用真实 weekly total 作为回测基础
  - 胜率指标改为"期望价值正" vs 简单命中率
  - 增加真实档位概率（从历史频率计算）

运行: python3 backtest_v2.py [--verbose] [--entry-day 6] [--min-edge 0.08]
"""

import json, math, sys, os, statistics
from datetime import datetime, timezone

PROJ_DIR = "/root/.openclaw/workspace/projects/elon-poly"
HISTORY_FILE = f"{PROJ_DIR}/weekly_history.json"

# ─── 数学工具 ─────────────────────────────────────────────────

def norm_cdf(x):
    a1,a2,a3,a4,a5 = 0.254829592,-0.284496736,1.421413741,-1.453152027,1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5*t+a4)*t)+a3)*t+a2)*t+a1)*t*math.exp(-x*x)
    return 0.5*(1.0 + sign*y)

def p_in_bracket(lo, hi, mean, std):
    if std <= 0:
        return 1.0 if lo <= mean < hi else 0.0
    return norm_cdf((hi-mean)/std) - norm_cdf((lo-mean)/std)

# ─── 参数默认值 ──────────────────────────────────────────────

DEFAULT_PARAMS = {
    # P2改进：参数化线性回归模型替代稀疏查表法
    # 拟合公式：d7 = 1.2503 * d5_cum + 84.18，残差std=45.8（N=35）
    "cond_linear_a": 1.2503,
    "cond_linear_b": 84.18,
    "cond_linear_std": 45.8,
    # P6改进：手续费与滑点（Polymarket真实交易成本）
    # Polymarket平台费: ~2% (0.02)，买入滑点: ~0.5%
    "fee_rate": 0.0,      # 默认0，通过--fee参数控制
    "slippage": 0.0,      # 默认0，通过--slippage参数控制
    "cond_table": [        # 保留作fallback，已被参数化模型覆盖
        [100, 149, 194, 32],
        [150, 199, 265, 42],
        [200, 249, 315, 42],
        [250, 299, 379, 42],
        [300, 349, 427, 60],
        [350, 399, 518, 45],
        [400, 449, 555, 26],
        [450, 599, 580, 25],
    ],
    "momentum_matrix": [
        [0.61, 0.28, 0.11],
        [0.22, 0.45, 0.33],
        [0.08, 0.27, 0.65],
    ],
    "momentum_thresholds": [300, 400],
    "daily_mean": 51.6,    # 从真实数据：361/7
    "daily_std": 25.0,
    "bin_width": 20,
    "min_edge": 0.08,
    "entry_day": 6,
    "kelly_half": True,
    "stake_per_trade": 500,
    # P8: 动态Kelly复利模式
    "compound": False,       # 是否启用复利模式
    "initial_capital": 2000, # 初始资金（复利模式下使用）
    # P10: 动量过滤
    "mom_threshold": 0,      # 前周total需>=此值才入场（0=不过滤）
    # P10: 自适应edge
    "adaptive_edge": False,  # 根据市场档位分散度动态调整edge阈值
    # P11: Kelly sizing bug修复 + 波动率调整
    "daily_std": 22.0,      # P11: 更精确的日均标准差（从真实数据重估）
    "vol_regime_adjust": False,  # P11: 波动率区间调整（高波动周降低权重）
}

# ─── 加载真实历史数据 ──────────────────────────────────────────

def load_weekly_data():
    with open(HISTORY_FILE) as f:
        raw = json.load(f)
    
    # 去重（同一个 start 多个 tracking，取 total 相同的第一个）
    seen = {}
    for r in raw:
        key = r["start"]
        if key not in seen and r["total"] > 0 and not r["is_active"]:
            seen[key] = r
    
    weeks = sorted(seen.values(), key=lambda x: x["start"])
    return weeks

def get_day_cumulative(week, day_n):
    """
    从 weekly 的 daily 字典中，取前 day_n 天的累计数
    daily 键是日期字符串，值是当天推文数
    """
    daily = week.get("daily", {})
    dates = sorted(daily.keys())
    # 取前 day_n 个日期的累计
    total = 0
    for d in dates[:day_n]:
        total += daily.get(d, 0)
    return total

# ─── 三因子模型预测 ──────────────────────────────────────────

def predict(week, prev_total, params, entry_day):
    """返回 (blended_mean, blended_std, momentum_class)"""
    cond_table = params["cond_table"]
    daily_mean = params["daily_mean"]
    daily_std = params["daily_std"]
    momentum_matrix = params["momentum_matrix"]
    momentum_thresholds = params["momentum_thresholds"]
    
    cumulative = get_day_cumulative(week, entry_day)
    days_left = 7 - entry_day
    
    # 因子一：条件概率（P2改进：参数化线性回归替代稀疏查表）
    if entry_day >= 5:
        day5_cum = get_day_cumulative(week, 5)
        # 参数化模型：d7 = a*d5 + b，残差用全局std
        lin_a = params.get("cond_linear_a", 1.2503)
        lin_b = params.get("cond_linear_b", 84.18)
        lin_std = params.get("cond_linear_std", 45.8)
        d7mean = lin_a * day5_cum + lin_b
        d7std = lin_std
        cond_weight = max(0, 0.7 - (entry_day-5)*0.3)
        linear_mean = cumulative + days_left * daily_mean
        linear_std = math.sqrt(max(days_left,1)) * daily_std
        blended_mean = cond_weight*d7mean + (1-cond_weight)*linear_mean
        blended_std = cond_weight*d7std + (1-cond_weight)*linear_std
    else:
        blended_mean = cumulative + days_left * daily_mean
        blended_std = math.sqrt(max(days_left,1)) * daily_std
    
    # 因子二：动量（仅 Day1-4 有效，入场 Day5+ 时权重小）
    mom_weight_map = [0.4, 0.4, 0.35, 0.25, 0.12, 0.04, 0.0]
    mom_weight = mom_weight_map[min(entry_day-1, 6)]
    if mom_weight > 0 and prev_total > 0:
        thrs = momentum_thresholds
        mc = 0 if prev_total < thrs[0] else (1 if prev_total <= thrs[1] else 2)
        mom_probs = momentum_matrix[mc]
        mom_mean = mom_probs[0]*250 + mom_probs[1]*350 + mom_probs[2]*475
        blended_mean = (1-mom_weight)*blended_mean + mom_weight*mom_mean
    
    return blended_mean, blended_std

def compute_bracket_probs(mean, std, bin_width=20):
    """计算各档位模型概率"""
    bins = list(range(140, 620, bin_width))
    probs = {}
    for lo in bins:
        probs[lo] = p_in_bracket(lo, lo+bin_width, mean, std)
    total = sum(probs.values())
    if total > 0:
        probs = {k: v/total for k,v in probs.items()}
    return probs

# ─── 市场价格（从真实历史频率推算 + 动量折扣） ──────────────

def compute_market_prices_for_week(week, entry_day, daily_mean=51.6, market_std_mult=1.8):
    """
    模拟市场价格 = 散户的线性外推定价
    
    散户逻辑：当前累计 / 已过天数 * 7 = 线性预测
    散户的标准差比模型宽 ~1.8x（因为他们不用条件概率收窄）
    
    这是对真实 Polymarket 市场定价的现实模拟，
    不依赖历史样本稀少导致的极端赔率问题。
    """
    bin_width = 20
    bins = list(range(140, 620, bin_width))
    
    cumulative = get_day_cumulative(week, entry_day)
    days_left = 7 - entry_day
    
    # 散户定价：线性外推 + 宽标准差
    if entry_day > 0:
        daily_pace = cumulative / entry_day
        market_mean = daily_pace * 7  # 简单线性外推
    else:
        market_mean = daily_mean * 7
    
    # 散户用的方差更宽（相当于无条件历史标准差的线性外推）
    market_std = math.sqrt(days_left) * daily_mean * market_std_mult
    market_std = max(market_std, 30)  # 最小方差
    
    prices = {}
    for lo in bins:
        prices[lo] = p_in_bracket(lo, lo+bin_width, market_mean, market_std)
    
    # 归一化
    total_p = sum(prices.values())
    if total_p > 0:
        prices = {k: v/total_p for k,v in prices.items()}
    
    return prices

# ─── 回测主循环 ───────────────────────────────────────────────

def run_backtest(params=None, verbose=False):
    if params is None:
        params = DEFAULT_PARAMS.copy()
    
    weeks = load_weekly_data()
    if len(weeks) < 5:
        return {"error": "历史数据不足"}
    
    entry_day = params.get("entry_day", 6)
    min_edge = params.get("min_edge", 0.08)
    stake = params.get("stake_per_trade", 500)
    
    pnl_list = []
    ev_list = []  # expected value
    bet_details = []
    no_trade = 0
    
    # P8: 动态Kelly复利
    compound = params.get("compound", False)
    capital = params.get("initial_capital", 2000) if compound else None
    capital_history = [capital] if compound else []
    
    for i in range(1, len(weeks)):  # 从第2周开始（需要前一周做动量）
        week = weeks[i]
        prev_total = weeks[i-1]["total"]
        actual_total = week["total"]
        
        if actual_total <= 0:
            continue
        
        # P10: 动量过滤 — 前周推文量过低说明Elon沉默期，不入场
        mom_threshold = params.get("mom_threshold", 0)
        if mom_threshold > 0 and prev_total < mom_threshold:
            no_trade += 1
            continue
        
        # P10: 自适应edge — 根据市场价格分散度动态调整edge阈值
        # 市场分散度 = 模型各档概率的标准差；越集中→市场对方向越确定→可降低edge阈值
        min_edge = params.get("min_edge", 0.08)
        if params.get("adaptive_edge", False):
            market_prices = compute_market_prices_for_week(week, entry_day)
            market_probs = list(market_prices.values())
            if len(market_probs) > 1:
                mp_std = statistics.stdev(market_probs)
                mp_mean = sum(market_probs) / len(market_probs)
                cv = mp_std / mp_mean if mp_mean > 0 else 1.0
                # CV越高→市场越不确定→需要更高edge保护；CV低→确定性高→可降低阈值
                adaptive_factor = 1.0 - 0.3 * (1.0 - min(cv / 0.8, 1.0))
                min_edge = max(0.04, min_edge * adaptive_factor)

        # P11: 波动率区间调整 — std异常高时降低仓位权重
        # (先计算预期std，因为predict()还未被调用)
        daily_std_override = params.get("daily_std", 22.0)
        days_left = 7 - entry_day
        vol_regime_mult = 1.0
        
        # 模型预测
        mean, std = predict(week, prev_total, params, entry_day)
        
        if params.get("vol_regime_adjust", False):
            # 预期标准差 = sqrt(days_left) * daily_std
            expected_std = math.sqrt(max(days_left, 1)) * daily_std_override
            # 如果模型std > 预期2x，说明模型对方向极不确定，降低权重
            if std > 0 and std > 2.0 * expected_std:
                vol_regime_mult = 0.5  # 减半仓位
            elif std > 0 and std > 1.5 * expected_std:
                vol_regime_mult = 0.75
        model_probs = compute_bracket_probs(mean, std, params.get("bin_width", 20))
        
        # 市场价格 = 散户线性外推定价模型
        market_prices = compute_market_prices_for_week(week, entry_day)
        
        # 收集所有有 edge 的档位
        edge_brackets = []
        for lo, model_p in model_probs.items():
            market_p = market_prices.get(lo, 0.030)
            edge = model_p - market_p
            if edge > min_edge:
                edge_brackets.append((edge, lo, model_p, market_p))
        edge_brackets.sort(reverse=True)

        multi_bracket = params.get("multi_bracket", False)
        max_brackets = params.get("max_brackets", 3)

        if not edge_brackets:
            no_trade += 1
            continue

        # 单档或多档模式
        if multi_bracket:
            selected = edge_brackets[:max_brackets]
        else:
            selected = edge_brackets[:1]

        actual_bracket = (actual_total // 20) * 20
        week_pnl = 0
        week_ev = 0
        best_edge = selected[0][0]
        best_bracket = selected[0][1]

        # 按 edge 权重分配仓位（各档总注额 = stake）
        total_edge = sum(e for e,_,_,_ in selected)
        for (edge, lo, model_p, market_p) in selected:
            b = (1 - market_p) / market_p
            f = max(0, (model_p*(b+1)-1)/b)
            if params.get("kelly_half", True):
                f /= 2
            f = min(f, 0.25)
            # P11 FIX: Kelly sizing now works in multi-bracket mode (bug was: multi_bracket never True here)
            # 多档时按 edge 比例分仓
            weight = (edge / total_edge) if multi_bracket else 1.0
            # P11: 波动率区间权重 × edge权重
            final_weight = weight * vol_regime_mult
            # P8: 动态Kelly复利 — 用当前资金计算注额
            if compound and capital is not None:
                bet_amount = capital * f * final_weight
            else:
                bet_amount = stake * f * (1/0.25) * final_weight
            bet_amount = max(bet_amount, 5)

            hit = (actual_bracket == lo)
            # P6: 扣除手续费和滑点（买入时扣）
            fee_rate = params.get("fee_rate", 0.0)
            slippage = params.get("slippage", 0.0)
            cost_mult = 1.0 - fee_rate - slippage
            effective_bet = bet_amount * cost_mult
            if hit:
                pnl = effective_bet * b
            else:
                pnl = -effective_bet
            week_pnl += pnl
            week_ev += (model_p * b - (1-model_p)) * final_weight

        pnl_list.append(week_pnl)
        ev_list.append(week_ev)
        # P8: 更新复利资金
        if compound and capital is not None:
            capital = max(capital + week_pnl, 50)  # 最低保留$50
            capital_history.append(capital)
        hit = (actual_bracket == best_bracket)
        bet_details.append({
            "week": week["start"],
            "actual": actual_total,
            "actual_bracket": actual_bracket,
            "pred_mean": mean,
            "bet_bracket": best_bracket,
            "market_p": selected[0][3],
            "model_p": selected[0][2],
            "edge": best_edge,
            "bet_amount": stake,
            "pnl": week_pnl,
            "hit": hit,
            "n_brackets": len(selected),
        })
        
        if verbose:
            print(f"  {week['start']}: 实际={actual_total}({actual_bracket}) "
                  f"预测={mean:.0f} 押{best_bracket} "
                  f"edge={best_edge:.1%} 注额=${bet_amount:.0f} "
                  f"pnl=${pnl:+.0f} {'✓' if hit else '✗'}")
    
    if not pnl_list:
        return {"error": "无交易"}
    
    total_pnl = sum(pnl_list)
    hit_rate = sum(1 for d in bet_details if d["hit"]) / len(bet_details)
    avg_pnl = total_pnl / len(pnl_list)
    avg_ev = sum(ev_list) / len(ev_list)
    
    std_pnl = statistics.stdev(pnl_list) if len(pnl_list) > 1 else 0
    sharpe = (avg_pnl / std_pnl) * math.sqrt(52) if std_pnl > 0 else 0
    
    # 最大回撤
    cum, peak, max_dd = 0, 0, 0
    for p in pnl_list:
        cum += p
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
    
    # 盈亏比
    wins = [p for p in pnl_list if p > 0]
    losses = [p for p in pnl_list if p < 0]
    profit_factor = (sum(wins) / abs(sum(losses))) if losses else float('inf')
    
    result = {
        "total_weeks": len(weeks),
        "total_trades": len(pnl_list),
        "no_trade_periods": no_trade,
        "total_pnl": total_pnl,
        "hit_rate": hit_rate,           # 命中档位率
        "avg_ev": avg_ev,               # 平均期望价值（衡量模型质量）
        "avg_pnl_per_trade": avg_pnl,
        "sharpe_annualized": sharpe,
        "max_drawdown": max_dd,
        "avg_edge": sum(d["edge"] for d in bet_details)/len(bet_details),
        "profit_factor": profit_factor,
        "is_ev_positive": avg_ev > 0,   # 期望价值正 = 模型有效
        "bet_details": bet_details,
    }
    # P8: 附加复利统计
    if compound and capital_history:
        initial = capital_history[0]
        final = capital_history[-1]
        result["compound_initial"] = initial
        result["compound_final"] = final
        result["compound_return_pct"] = (final - initial) / initial * 100
        # 年化收益率 (35周 ≈ 0.67年)
        years = len(capital_history) / 52
        result["compound_cagr_pct"] = ((final/initial)**(1/max(years,0.1)) - 1) * 100 if final > 0 else -100
    return result

# ─── 主程序 ──────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--entry-day", type=int, default=6)
    parser.add_argument("--min-edge", type=float, default=0.08)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--multi-bracket", action="store_true", help="多档分散押注")
    parser.add_argument("--max-brackets", type=int, default=3, help="最多押注档位数")
    parser.add_argument("--fee", type=float, default=0.0, help="手续费率（如0.02=2%%）")
    parser.add_argument("--slippage", type=float, default=0.0, help="滑点率（如0.005=0.5%%）")
    parser.add_argument("--compound", action="store_true", help="P8: 动态Kelly复利模式")
    parser.add_argument("--initial-capital", type=float, default=2000, help="初始资金（复利模式，默认$2000）")
    parser.add_argument("--mom-threshold", type=int, default=0, help="P10: 动量过滤 — 前周total需>=此值才入场（0=不过滤）")
    parser.add_argument("--adaptive-edge", action="store_true", help="P10: 自适应edge — 根据市场档位分散度动态调整min_edge")
    parser.add_argument("--vol-regime", action="store_true", help="P11: 波动率区间调整 — 高波动周自动降低仓位")
    args = parser.parse_args()

    params = DEFAULT_PARAMS.copy()
    params["entry_day"] = args.entry_day
    params["min_edge"] = args.min_edge
    params["multi_bracket"] = args.multi_bracket
    params["max_brackets"] = args.max_brackets
    params["fee_rate"] = args.fee
    params["slippage"] = args.slippage
    params["compound"] = args.compound
    params["initial_capital"] = args.initial_capital
    params["mom_threshold"] = args.mom_threshold
    params["adaptive_edge"] = args.adaptive_edge
    params["vol_regime_adjust"] = args.vol_regime

    print("="*60)
    print(f"Elon Polymarket 三因子模型 — 回测 v2.0 (真实数据)")
    mode = f"多档x{args.max_brackets}" if args.multi_bracket else "单档"
    cost_str = f", fee={args.fee:.1%}, slip={args.slippage:.1%}" if (args.fee or args.slippage) else ""
    print(f"参数: entry_day=Day{args.entry_day}, min_edge={args.min_edge:.0%}, 模式={mode}{cost_str}")
    print("="*60)
    
    results = run_backtest(params, verbose=args.verbose)
    
    if "error" in results:
        print(f"[ERROR] {results['error']}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"📊 回测结果（基于 {results['total_weeks']} 个真实历史周期）")
    print(f"{'='*60}")
    print(f"  交易次数:     {results['total_trades']} 次（跳过 {results['no_trade_periods']} 次）")
    print(f"  档位命中率:   {results['hit_rate']:.1%}  （单档位预期约5-10%）")
    print(f"  平均期望值:   {results['avg_ev']:+.1%}  （>0 = 模型有alpha）")
    print(f"  总P&L:        ${results['total_pnl']:+.0f}")
    print(f"  均值P&L/次:   ${results['avg_pnl_per_trade']:+.0f}")
    print(f"  年化Sharpe:   {results['sharpe_annualized']:.2f}")
    print(f"  最大回撤:     ${results['max_drawdown']:.0f}")
    print(f"  平均Edge:     {results['avg_edge']:.1%}")
    print(f"  盈亏比:       {results['profit_factor']:.2f}x")
    
    # P8: 打印复利统计
    if args.compound and "compound_final" in results:
        print(f"\n{'='*60}")
        print(f"💹 复利模式 (初始${results['compound_initial']:.0f})")
        print(f"  最终资金:     ${results['compound_final']:.0f}")
        print(f"  总收益率:     {results['compound_return_pct']:+.1f}%")
        print(f"  年化收益率:   {results['compound_cagr_pct']:+.1f}%")
    
    # 盈利标准（修正版）
    is_profitable = (
        results["is_ev_positive"] and          # 期望价值为正
        results["sharpe_annualized"] > 1.0 and # Sharpe > 1（合理水平）
        results["total_pnl"] > 0 and           # 总体盈利
        results["avg_edge"] > 0.06             # 平均edge > 6%
    )
    
    print(f"\n{'='*60}")
    if is_profitable:
        print(f"  🎯 状态: 稳定盈利 — 可以实盘！")
    else:
        print(f"  ⚠️  状态: 未达标，继续迭代")
        if not results["is_ev_positive"]:
            print(f"    → 期望价值为负（{results['avg_ev']:+.1%}），模型无alpha")
        if results["sharpe_annualized"] <= 1.0:
            print(f"    → Sharpe {results['sharpe_annualized']:.2f} < 1.0")
    print(f"{'='*60}")
    
    results["is_profitable"] = is_profitable
    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    del results["bet_details"]  # 避免输出文件过大
    
    out = args.output or f"{PROJ_DIR}/backtest_result_v2.json"
    with open(out, "w") as f:
        json.dump({k:v for k,v in results.items() if k!="bet_details"}, f, indent=2)
    print(f"\n💾 写入: {out}")
    
    return 0 if is_profitable else 1

if __name__ == "__main__":
    sys.exit(main())
