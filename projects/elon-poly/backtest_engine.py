#!/usr/bin/env python3
"""
Elon Polymarket 三因子模型 — 全量回测引擎 v1.0

核心逻辑：
  1. 从 xtracker 抓取历史日数据（141天）
  2. 构建 135 个滚动7天周期
  3. 模拟 Day5/Day6 入场：计算三因子预测 → 选档位 → 模拟押注 → 结算
  4. 输出 P&L、Sharpe、胜率、最大回撤

运行: python3 backtest_engine.py [--model MODEL_PARAMS_JSON]
"""

import requests
import math
import json
import sys
import os
import time
from datetime import datetime, timezone
from typing import Optional
import statistics

# ─── xtracker 数据 ───────────────────────────────────────────
XTRACKER_BASE = "https://xtracker.polymarket.com/api"
ELON_USER_ID   = "44196397"

# ─── 模型参数（可被 iterate 更新） ───────────────────────────
DEFAULT_PARAMS = {
    # 条件概率表 (day5_lo, day5_hi) -> (day7_mean, day7_std)
    "cond_table": [
        [100, 149, 194, 32],
        [150, 199, 265, 42],
        [200, 249, 315, 42],
        [250, 299, 379, 42],
        [300, 349, 427, 60],
        [350, 399, 518, 45],
        [400, 449, 555, 26],
    ],
    # 动量转移矩阵 [上周: 低/中/高] -> [本周: 低/中/高] 概率
    "momentum_matrix": [
        [0.61, 0.28, 0.11],   # 上周低
        [0.22, 0.45, 0.33],   # 上周中
        [0.08, 0.27, 0.65],   # 上周高
    ],
    "momentum_thresholds": [300, 400],   # 低<300, 中300-400, 高>400
    # 动量因子在 Day1-3 有效，Day5+ 下降
    "momentum_weight_by_day": [0.4, 0.4, 0.35, 0.25, 0.15, 0.05, 0.0],
    "daily_mean": 48.9,
    "daily_std": 25.1,
    "bin_width": 20,
    # 交易参数
    "min_edge": 0.08,        # 最小 edge 才入场
    "entry_day": 6,          # 主力入场日（Day6=index 5）
    "kelly_half": True,      # 使用半 Kelly
    "stake_per_trade": 500,  # 每次押注基础金额（USDC）
}

# ─── 工具函数 ─────────────────────────────────────────────────

def norm_cdf(x):
    """标准正态 CDF（数值近似）"""
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return 0.5 * (1.0 + sign * y)

def p_in_bracket(lo, hi, mean, std):
    """某档位 [lo, hi) 在 N(mean, std) 下的概率"""
    if std <= 0:
        return 1.0 if lo <= mean < hi else 0.0
    return norm_cdf((hi - mean) / std) - norm_cdf((lo - mean) / std)

def get_cond_entry(cond_table, day5_count):
    for lo, hi, d7mean, d7std in cond_table:
        if lo <= day5_count <= hi:
            return d7mean, d7std
    # 外插：超过最大区间
    if day5_count > 449:
        return 590, 20
    return 194, 32  # 小于最低区间

def momentum_class(count, thresholds):
    if count < thresholds[0]:
        return 0  # 低
    elif count <= thresholds[1]:
        return 1  # 中
    return 2  # 高

def kelly_fraction(p, b):
    """完整 Kelly = (p*(b+1)-1)/b，结果在 [0,1]"""
    if b <= 0:
        return 0
    f = (p * (b + 1) - 1) / b
    return max(0.0, min(1.0, f))

# ─── 数据获取 ─────────────────────────────────────────────────

def fetch_daily_counts(max_retries=3):
    """从 xtracker 获取 Elon 每日推文数列表（从最早到最新）"""
    for attempt in range(max_retries):
        try:
            r = requests.get(
                f"{XTRACKER_BASE}/users/{ELON_USER_ID}/posts/daily",
                timeout=20
            )
            r.raise_for_status()
            data = r.json()
            if data.get("success"):
                records = data["data"]
                # 按日期排序
                records.sort(key=lambda x: x.get("date", ""))
                return [(rec["date"], rec["count"]) for rec in records if "count" in rec]
        except Exception as e:
            print(f"[WARN] 数据获取失败 attempt {attempt+1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    # 回退：尝试 xtracker trackings 端点
    print("[INFO] 尝试 trackings 端点...")
    try:
        r = requests.get(f"{XTRACKER_BASE}/trackings", params={"activeOnly": "false"}, timeout=20)
        r.raise_for_status()
        data = r.json()
        if data.get("success"):
            # 找到所有 elon 追踪并合并每日数据
            all_daily = {}
            for tracking in data["data"]:
                title = tracking.get("title", "").lower()
                if "elon" not in title:
                    continue
                tid = tracking.get("id")
                if not tid:
                    continue
                try:
                    r2 = requests.get(f"{XTRACKER_BASE}/trackings/{tid}", 
                                     params={"includeStats": "true"}, timeout=15)
                    r2.raise_for_status()
                    t_data = r2.json().get("data", {})
                    for day_stat in t_data.get("dailyStats", []):
                        date = day_stat.get("date", "")
                        count = day_stat.get("count", 0)
                        if date:
                            all_daily[date] = all_daily.get(date, 0) + count
                except Exception:
                    pass
            if all_daily:
                result = sorted(all_daily.items())
                return result
    except Exception as e:
        print(f"[ERROR] 备用端点也失败: {e}")
    
    return []

# ─── 回测核心 ─────────────────────────────────────────────────

def build_windows(daily_counts, window_size=7):
    """将每日数据切成 7 天滚动窗口"""
    windows = []
    for i in range(len(daily_counts) - window_size + 1):
        w = daily_counts[i:i + window_size]
        windows.append(w)
    return windows

def compute_model_probs(window_days, prev_window_total, params, entry_day=5):
    """
    给定 entry_day（1-7，1=第一天），计算三因子模型各档位概率

    Returns: dict {bracket_lo: prob}
    """
    cond_table = params["cond_table"]
    momentum_matrix = params["momentum_matrix"]
    momentum_thresholds = params["momentum_thresholds"]
    momentum_weight_by_day = params["momentum_weight_by_day"]
    daily_mean = params["daily_mean"]
    daily_std = params["daily_std"]
    bin_width = params["bin_width"]

    day_idx = entry_day - 1  # 0-based

    # 已知累计
    cumulative = sum(c for _, c in window_days[:entry_day])
    days_left = 7 - entry_day

    # ─ 因子一：条件概率 ─
    if entry_day >= 5:
        day5_cum = sum(c for _, c in window_days[:5])
        d7mean, d7std = get_cond_entry(cond_table, day5_cum)
        # 但已知到 entry_day，剩余只需预测 days_left 天
        # 调整：T = cumulative + days_left * daily_mean ± sqrt(days_left)*daily_std
        # 与条件概率表融合（加权平均 mean/std）
        linear_mean = cumulative + days_left * daily_mean
        linear_std = math.sqrt(days_left) * daily_std
        # 条件概率表在 Day5 时权重 0.7，Day6 时 0.4，Day7 时 0.1
        cond_weight = max(0, 0.7 - (entry_day - 5) * 0.3)
        blended_mean = cond_weight * d7mean + (1 - cond_weight) * linear_mean
        blended_std = cond_weight * d7std + (1 - cond_weight) * linear_std
    else:
        # Day1-4：纯线性外推
        blended_mean = cumulative + days_left * daily_mean
        blended_std = math.sqrt(days_left) * daily_std

    # ─ 因子二：动量 ─
    mom_weight = momentum_weight_by_day[day_idx] if day_idx < len(momentum_weight_by_day) else 0
    if mom_weight > 0 and prev_window_total > 0:
        prev_class = momentum_class(prev_window_total, momentum_thresholds)
        mom_probs = momentum_matrix[prev_class]  # [p_low, p_mid, p_high]
        # 动量给出当前周期落在低/中/高的先验，映射为档位调整
        # 低区间均值 ~250, 中区间 ~350, 高区间 ~475
        mom_mean = (mom_probs[0] * 250 + mom_probs[1] * 350 + mom_probs[2] * 475)
        blended_mean = (1 - mom_weight) * blended_mean + mom_weight * mom_mean

    # ─ 计算各档位概率 ─
    bins = list(range(140, 620, bin_width))
    probs = {}
    for lo in bins:
        hi = lo + bin_width
        probs[lo] = p_in_bracket(lo, hi, blended_mean, blended_std)
    
    # 归一化（由于档位不覆盖全部范围，归一化确保概率合法）
    total = sum(probs.values())
    if total > 0:
        probs = {k: v / total for k, v in probs.items()}
    
    return probs, blended_mean, blended_std

def simulate_bet(model_probs, actual_total, params, week_vol_budget=500):
    """
    模拟在 entry_day 基于模型概率押注最优档位

    假设市场价格 = 无条件历史频率（"散户市场"），
    后续可接入真实 Polymarket 价格。

    Returns: (pnl, bet_bracket, hit, edge)
    """
    # 无条件市场价格（从研报历史分布，共135个窗口）
    MARKET_PRICES = {
        140: 0.030, 160: 0.037, 180: 0.022, 200: 0.030, 220: 0.037,
        240: 0.089, 260: 0.089, 280: 0.067, 300: 0.059, 320: 0.044,
        340: 0.096, 360: 0.089, 380: 0.052, 400: 0.044, 420: 0.015,
        440: 0.022, 460: 0.030, 480: 0.007, 500: 0.030, 520: 0.030,
        540: 0.030, 560: 0.037, 580: 0.015,
    }

    best_edge = 0
    best_bracket = None
    best_price = 0
    best_model_p = 0

    for lo, model_p in model_probs.items():
        market_p = MARKET_PRICES.get(lo, 0.030)
        edge = model_p - market_p
        if edge > best_edge:
            best_edge = edge
            best_bracket = lo
            best_price = market_p
            best_model_p = model_p

    if best_bracket is None or best_edge < params["min_edge"]:
        return 0, None, False, 0

    # Kelly 仓位
    b = (1 - best_price) / best_price  # 赔率
    f = kelly_fraction(best_model_p, b)
    if params["kelly_half"]:
        f /= 2

    stake = week_vol_budget * f
    stake = min(stake, week_vol_budget)  # 不超过预算

    # 是否命中
    actual_bin = (actual_total // 20) * 20  # 向下取整到 bin
    hit = (actual_bin == best_bracket)

    if hit:
        pnl = stake * b  # YES 命中
    else:
        pnl = -stake     # YES 未命中

    return pnl, best_bracket, hit, best_edge

def run_backtest(daily_data, params, verbose=False):
    """
    全量回测

    Returns: dict with metrics
    """
    if len(daily_data) < 14:
        return {"error": "数据不足"}

    windows = build_windows(daily_data, 7)
    
    pnl_list = []
    hit_list = []
    edge_list = []
    no_trade_count = 0

    for i, window in enumerate(windows):
        actual_total = sum(c for _, c in window)
        prev_total = sum(c for _, c in windows[i-1]) if i > 0 else 0

        # 在 entry_day=6 入场
        entry_day = params.get("entry_day", 6)
        model_probs, pred_mean, pred_std = compute_model_probs(
            window, prev_total, params, entry_day=entry_day
        )

        pnl, bracket, hit, edge = simulate_bet(model_probs, actual_total, params)

        if bracket is None:
            no_trade_count += 1
            continue

        pnl_list.append(pnl)
        hit_list.append(hit)
        edge_list.append(edge)

        if verbose:
            pred_bracket = (int(pred_mean) // 20) * 20
            actual_bracket = (actual_total // 20) * 20
            print(f"  周期{i+1:3d}: 实际={actual_total:4d}({actual_bracket}) "
                  f"预测={pred_mean:.0f}({pred_bracket}) "
                  f"押{bracket} edge={edge:.1%} pnl=${pnl:+.0f} {'✓' if hit else '✗'}")

    if not pnl_list:
        return {"error": "没有交易发生"}

    total_pnl = sum(pnl_list)
    win_rate = sum(hit_list) / len(hit_list)
    avg_pnl = total_pnl / len(pnl_list)
    
    if len(pnl_list) > 1:
        std_pnl = statistics.stdev(pnl_list)
        sharpe = (avg_pnl / std_pnl) * math.sqrt(52) if std_pnl > 0 else 0
    else:
        sharpe = 0

    # 最大回撤
    cum = 0
    peak = 0
    max_dd = 0
    for p in pnl_list:
        cum += p
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)

    return {
        "total_trades": len(pnl_list),
        "no_trade_periods": no_trade_count,
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "avg_pnl_per_trade": avg_pnl,
        "sharpe_annualized": sharpe,
        "max_drawdown": max_dd,
        "avg_edge": sum(edge_list) / len(edge_list),
        "profit_factor": (sum(p for p in pnl_list if p > 0) / 
                         abs(sum(p for p in pnl_list if p < 0)) 
                         if any(p < 0 for p in pnl_list) else float('inf')),
    }

# ─── 主程序 ───────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", type=str, default=None, help="JSON 参数文件路径")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--entry-day", type=int, default=6)
    parser.add_argument("--min-edge", type=float, default=0.08)
    parser.add_argument("--output", type=str, default=None, help="输出结果 JSON 文件")
    args = parser.parse_args()

    params = DEFAULT_PARAMS.copy()
    if args.params and os.path.exists(args.params):
        with open(args.params) as f:
            params.update(json.load(f))
    params["entry_day"] = args.entry_day
    params["min_edge"] = args.min_edge

    print("=" * 60)
    print("Elon Polymarket 三因子模型 — 回测引擎 v1.0")
    print("=" * 60)
    print(f"📥 获取历史数据...")

    daily_data = fetch_daily_counts()
    
    if not daily_data:
        print("[ERROR] 无法获取数据，使用内置统计数据模拟")
        # 使用研报中的统计常量生成模拟数据（种子固定确保可复现）
        import random
        random.seed(42)
        dates = [f"2025-11-{i:02d}" for i in range(1, 31)] + \
                [f"2025-12-{i:02d}" for i in range(1, 32)] + \
                [f"2026-01-{i:02d}" for i in range(1, 32)] + \
                [f"2026-02-{i:02d}" for i in range(1, 29)] + \
                [f"2026-03-{i:02d}" for i in range(1, 21)]
        # 按研报月度均值生成（11月23条/天，12月53条，1月55条，2月71条，3月50条）
        monthly_means = {"11": 23, "12": 53, "01": 55, "02": 71, "03": 50}
        daily_data = []
        for d in dates[:141]:
            month = d[5:7]
            mean = monthly_means.get(month, 48)
            count = max(6, int(random.gauss(mean, 18)))
            daily_data.append((d, count))
        print(f"  [模拟] 生成 {len(daily_data)} 天数据")
    else:
        print(f"  ✓ 获取到 {len(daily_data)} 天数据")

    print(f"\n🔬 运行回测 (entry_day=Day{params['entry_day']}, min_edge={params['min_edge']:.0%})")
    if args.verbose:
        print()

    results = run_backtest(daily_data, params, verbose=args.verbose)

    if "error" in results:
        print(f"\n[ERROR] {results['error']}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"📊 回测结果")
    print(f"{'='*60}")
    print(f"  交易次数:     {results['total_trades']} 次（跳过 {results['no_trade_periods']} 次）")
    print(f"  胜率:         {results['win_rate']:.1%}")
    print(f"  总P&L:        ${results['total_pnl']:+.0f}")
    print(f"  均值P&L/次:   ${results['avg_pnl_per_trade']:+.0f}")
    print(f"  年化Sharpe:   {results['sharpe_annualized']:.2f}")
    print(f"  最大回撤:     ${results['max_drawdown']:.0f}")
    print(f"  平均Edge:     {results['avg_edge']:.1%}")
    print(f"  盈亏比:       {results['profit_factor']:.2f}x")
    
    # 盈利判断
    is_profitable = (
        results["win_rate"] > 0.55 and
        results["sharpe_annualized"] > 1.5 and
        results["total_pnl"] > 0
    )
    
    print(f"\n{'='*60}")
    if is_profitable:
        print(f"  🎯 状态: 稳定盈利 — 可以实盘")
    else:
        print(f"  ⚠️  状态: 尚未达标，继续迭代")
        reasons = []
        if results["win_rate"] <= 0.55:
            reasons.append(f"胜率 {results['win_rate']:.1%} < 55%")
        if results["sharpe_annualized"] <= 1.5:
            reasons.append(f"Sharpe {results['sharpe_annualized']:.2f} < 1.5")
        if results["total_pnl"] <= 0:
            reasons.append(f"总P&L ${results['total_pnl']:.0f} < 0")
        print(f"  原因: {', '.join(reasons)}")
    print(f"{'='*60}")

    results["params"] = params
    results["is_profitable"] = is_profitable
    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    results["data_days"] = len(daily_data)

    output_path = args.output or "/root/.openclaw/workspace/projects/elon-poly/backtest_result.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 结果已写入: {output_path}")

    return 0 if is_profitable else 1

if __name__ == "__main__":
    sys.exit(main())
