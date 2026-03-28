#!/usr/bin/env python3
"""
Elon Tweet Count Tracker & Predictor
实时查询 xtracker API，预测7天周期最终落点，输出交易建议

Usage:
    python3 elon_tracker.py              # 一次性运行，输出当前状态和建议
    python3 elon_tracker.py --loop       # 持续轮询模式（每3分钟）
    python3 elon_tracker.py --history    # 输出历史统计分析
"""

import requests
import time
import json
import sys
import math
from datetime import datetime, timezone, timedelta
from typing import Optional

# ============================================================
# 配置
# ============================================================
XTRACKER_BASE = "https://xtracker.polymarket.com/api"
ELON_HANDLE = "elonmusk"
ELON_USER_ID = "44196397"
POLL_INTERVAL = 180  # 常规轮询间隔（秒）
POLL_INTERVAL_CRITICAL = 60  # 最后4小时轮询间隔
POLL_INTERVAL_FINAL = 10  # 最后15分钟轮询间隔

# 历史统计常量（从141天数据计算）
HIST_DAILY_MEAN = 48.9
HIST_DAILY_STD = 25.1
HIST_7D_MEAN = 344.1
HIST_7D_STD = 112.8

# 条件概率表：Day5累计 -> (Day7均值, Day7标准差)
CONDITIONAL_TABLE = {
    (100, 149): (194, 32),
    (150, 199): (265, 42),
    (200, 249): (315, 42),
    (250, 299): (379, 42),
    (300, 349): (427, 60),
    (350, 399): (518, 45),
    (400, 449): (555, 26),
}

# 盘口档位宽度
BIN_WIDTH = 20


# ============================================================
# xtracker API 客户端
# ============================================================

def api_get(path: str, params: dict = None) -> dict:
    """通用 xtracker API GET 请求"""
    url = f"{XTRACKER_BASE}{path}"
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            raise ValueError(f"API returned success=false: {data}")
        return data["data"]
    except requests.RequestException as e:
        print(f"[ERROR] API request failed: {e}")
        raise


def get_active_tracking() -> Optional[dict]:
    """获取当前活跃的 elon 7天追踪任务"""
    trackings = api_get("/trackings", {"activeOnly": "true"})
    elon_trackings = []
    for t in trackings:
        title = t.get("title", "").lower()
        if "elon" in title and "tweet" in title:
            # 优先选择7天周期（非3天短盘）
            start = datetime.fromisoformat(t["startDate"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(t["endDate"].replace("Z", "+00:00"))
            days = (end - start).days
            if days >= 6:  # 7天或8天周期
                elon_trackings.append(t)
    
    if not elon_trackings:
        # 回退：返回任何 elon 追踪
        for t in trackings:
            if "elon" in t.get("title", "").lower():
                elon_trackings.append(t)
    
    if not elon_trackings:
        return None
    
    # 返回最新的
    return sorted(elon_trackings, key=lambda x: x["startDate"], reverse=True)[0]


def get_tracking_stats(tracking_id: str) -> dict:
    """获取追踪任务的统计数据（含每日明细）"""
    return api_get(f"/trackings/{tracking_id}", {"includeStats": "true"})


def get_realtime_count(tracking_id: str) -> dict:
    """获取当前累计推文数和状态"""
    data = get_tracking_stats(tracking_id)
    stats = data.get("stats", {})
    return {
        "tracking_id": tracking_id,
        "title": data.get("title", ""),
        "start_date": data.get("startDate"),
        "end_date": data.get("endDate"),
        "cumulative": stats.get("cumulative", 0),
        "pace": stats.get("pace", 0),
        "days_elapsed": stats.get("daysElapsed", 0),
        "days_remaining": stats.get("daysRemaining", 0),
        "days_total": stats.get("daysTotal", 7),
        "is_complete": stats.get("isComplete", False),
        "daily": stats.get("daily", []),
        "percent_complete": stats.get("percentComplete", 0),
    }


# ============================================================
# 预测引擎
# ============================================================

def normal_cdf(x: float) -> float:
    """标准正态CDF近似（Abramowitz & Stegun）"""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def predict_final_count(cumulative: int, days_elapsed: float, days_total: float = 7) -> dict:
    """
    基于当前累计推文数和已过天数，预测最终7天总数。
    
    返回：{
        mean: 预测均值,
        std: 预测标准差,
        ci_95: (下界, 上界),
        bin_probabilities: {(low, high): probability}
    }
    """
    days_remaining = max(0.01, days_total - days_elapsed)
    
    # 方法1：简单线性外推 + 历史波动
    if days_elapsed > 0:
        current_rate = cumulative / days_elapsed
        predicted_mean = cumulative + current_rate * days_remaining
    else:
        predicted_mean = HIST_7D_MEAN
    
    # 方法2：条件概率表（Day 5+ 精度更高）
    if days_elapsed >= 4.5:
        # 使用条件表
        for (lo, hi), (cond_mean, cond_std) in CONDITIONAL_TABLE.items():
            day5_equiv = cumulative * (5 / days_elapsed) if days_elapsed > 0 else 0
            if lo <= day5_equiv <= hi:
                predicted_mean = cond_mean * (cumulative / (day5_equiv if day5_equiv > 0 else 1))
                break
    
    # 方法3：剩余天数的不确定性
    remaining_mean = days_remaining * HIST_DAILY_MEAN
    remaining_std = math.sqrt(days_remaining) * HIST_DAILY_STD
    
    final_mean = cumulative + remaining_mean
    final_std = remaining_std
    
    # 加权平均（越接近结算，越信任当前pace）
    weight_pace = min(1.0, days_elapsed / days_total)
    if days_elapsed > 0:
        pace_mean = cumulative + (cumulative / days_elapsed) * days_remaining
        final_mean = weight_pace * pace_mean + (1 - weight_pace) * final_mean
    
    # 95% 置信区间
    ci_lower = max(0, final_mean - 1.96 * final_std)
    ci_upper = final_mean + 1.96 * final_std
    
    # 各档位概率
    bin_probs = {}
    for bin_start in range(0, 800, BIN_WIDTH):
        bin_end = bin_start + BIN_WIDTH
        if final_std > 0:
            p = normal_cdf((bin_end - final_mean) / final_std) - \
                normal_cdf((bin_start - final_mean) / final_std)
        else:
            p = 1.0 if bin_start <= final_mean < bin_end else 0.0
        if p > 0.001:  # 只保留概率 > 0.1% 的档位
            bin_probs[(bin_start, bin_end - 1)] = round(p, 4)
    
    return {
        "mean": round(final_mean, 1),
        "std": round(final_std, 1),
        "ci_95": (round(ci_lower), round(ci_upper)),
        "bin_probabilities": bin_probs,
        "days_remaining": round(days_remaining, 2),
    }


# ============================================================
# 交易建议引擎
# ============================================================

def calculate_edge(predicted_prob: float, market_price: float) -> dict:
    """
    计算单个档位的交易优势。
    
    Args:
        predicted_prob: 模型预测该档位 YES 的概率
        market_price: 当前 YES 价格（0-1）
    
    Returns:
        edge, kelly, half_kelly, expected_return
    """
    if market_price <= 0 or market_price >= 1:
        return {"edge": 0, "kelly": 0, "half_kelly": 0, "ev_per_dollar": 0, "action": "SKIP"}
    
    edge = predicted_prob - market_price
    odds = (1 - market_price) / market_price  # YES 赔率
    
    kelly = (predicted_prob * (odds + 1) - 1) / odds if odds > 0 else 0
    half_kelly = max(0, kelly / 2)
    
    ev_per_dollar = predicted_prob * (1 - market_price) - (1 - predicted_prob) * market_price
    
    if edge > 0.05:
        action = "BUY YES"
    elif edge < -0.05:
        action = "BUY NO"
    else:
        action = "HOLD"
    
    return {
        "edge": round(edge, 4),
        "kelly": round(kelly, 4),
        "half_kelly": round(half_kelly, 4),
        "ev_per_dollar": round(ev_per_dollar, 4),
        "action": action,
    }


def generate_recommendation(stats: dict, market_prices: dict = None) -> dict:
    """
    生成完整交易建议。
    
    Args:
        stats: get_realtime_count() 的返回值
        market_prices: {(bin_low, bin_high): yes_price} 字典，如无则跳过 edge 计算
    """
    prediction = predict_final_count(
        cumulative=stats["cumulative"],
        days_elapsed=stats["days_elapsed"],
        days_total=stats["days_total"],
    )
    
    # 找到概率最高的3个档位
    top_bins = sorted(
        prediction["bin_probabilities"].items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]
    
    recommendations = []
    for (bin_lo, bin_hi), prob in top_bins:
        rec = {
            "bin": f"{bin_lo}-{bin_hi}",
            "predicted_prob": prob,
        }
        
        if market_prices and (bin_lo, bin_hi) in market_prices:
            price = market_prices[(bin_lo, bin_hi)]
            rec["market_price"] = price
            rec.update(calculate_edge(prob, price))
        
        recommendations.append(rec)
    
    # 入场建议
    days_remaining = prediction["days_remaining"]
    if days_remaining > 3:
        timing = "OBSERVE - 不确定性过高，不建议入场"
    elif days_remaining > 1.5:
        timing = "READY - 可小仓位试探（10-20%）"
    elif days_remaining > 0.17:  # > 4 hours
        timing = "ACTIVE - 主力建仓窗口（20-40%仓位）"
    else:
        timing = "CRITICAL - 全仓确认窗口（70-100%仓位）"
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_count": stats["cumulative"],
        "days_elapsed": stats["days_elapsed"],
        "days_remaining": prediction["days_remaining"],
        "prediction": {
            "mean": prediction["mean"],
            "std": prediction["std"],
            "ci_95": prediction["ci_95"],
        },
        "top_bins": recommendations,
        "timing": timing,
    }


# ============================================================
# 历史分析
# ============================================================

def print_history_analysis():
    """输出历史统计分析"""
    print("=" * 70)
    print("ELON MUSK 推文盘口 — 历史统计分析")
    print("=" * 70)
    
    print(f"\n📊 每日推文统计（N=141天）")
    print(f"   均值: {HIST_DAILY_MEAN}")
    print(f"   标准差: {HIST_DAILY_STD}")
    print(f"   范围: [6, 121]")
    
    print(f"\n📊 7天滚动窗口统计（N=135）")
    print(f"   均值: {HIST_7D_MEAN}")
    print(f"   中位数: 339")
    print(f"   标准差: {HIST_7D_STD}")
    print(f"   范围: [145, 591]")
    
    print(f"\n📊 条件概率表（Day5累计 → Day7最终）")
    print(f"   {'Day5累计':>12}  {'Day7均值':>8}  {'Day7标准差':>10}  {'95% CI':>16}")
    for (lo, hi), (mean, std) in sorted(CONDITIONAL_TABLE.items()):
        ci = f"[{mean - 2*std}, {mean + 2*std}]"
        print(f"   {lo:>4}-{hi:<4}      {mean:>6}      {std:>6}      {ci:>16}")
    
    print(f"\n📊 盘口分区命中频率（7天滚动窗口，BIN={BIN_WIDTH}）")
    # Hardcoded from analysis
    dist = [
        ("140-159", 4, 3.0), ("160-179", 5, 3.7), ("180-199", 3, 2.2),
        ("200-219", 4, 3.0), ("220-239", 5, 3.7), ("240-259", 12, 8.9),
        ("260-279", 12, 8.9), ("280-299", 9, 6.7), ("300-319", 8, 5.9),
        ("320-339", 6, 4.4), ("340-359", 13, 9.6), ("360-379", 12, 8.9),
        ("380-399", 7, 5.2), ("400-419", 6, 4.4), ("420-439", 2, 1.5),
        ("440-459", 3, 2.2), ("460-479", 4, 3.0), ("480-499", 1, 0.7),
        ("500-519", 4, 3.0), ("520-539", 4, 3.0), ("540-559", 4, 3.0),
        ("560-579", 5, 3.7), ("580-599", 2, 1.5),
    ]
    for label, count, pct in dist:
        bar = "█" * int(pct * 2)
        print(f"   {label}: {count:>3} ({pct:>5.1f}%) {bar}")


# ============================================================
# 主程序
# ============================================================

def run_once():
    """单次运行：获取状态 → 预测 → 输出建议"""
    print("=" * 70)
    print(f"🔍 ELON TWEET TRACKER — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)
    
    # 1. 获取活跃追踪
    tracking = get_active_tracking()
    if not tracking:
        print("[WARN] 没有找到活跃的 Elon 推文追踪任务")
        print("       可能当前没有进行中的 Polymarket 盘口")
        return
    
    tracking_id = tracking["id"]
    print(f"\n📌 活跃追踪: {tracking.get('title', 'N/A')}")
    print(f"   ID: {tracking_id}")
    print(f"   周期: {tracking.get('startDate', '?')} → {tracking.get('endDate', '?')}")
    
    # 2. 获取实时数据
    stats = get_realtime_count(tracking_id)
    print(f"\n📊 当前状态:")
    print(f"   累计推文: {stats['cumulative']}")
    print(f"   已过天数: {stats['days_elapsed']}")
    print(f"   剩余天数: {stats['days_remaining']}")
    print(f"   当前pace: {stats['pace']} 条/天")
    print(f"   完成度: {stats['percent_complete']}%")
    
    if stats["daily"]:
        print(f"\n📅 每日明细:")
        for d in stats["daily"]:
            print(f"   {d.get('date', '?')}: {d.get('count', 0)} 条 (累计: {d.get('cumulative', 0)})")
    
    # 3. 生成预测和建议
    rec = generate_recommendation(stats)
    
    print(f"\n🎯 预测结果:")
    print(f"   预测均值: {rec['prediction']['mean']}")
    print(f"   标准差: {rec['prediction']['std']}")
    print(f"   95% CI: {rec['prediction']['ci_95']}")
    
    print(f"\n📈 概率最高的档位:")
    for r in rec["top_bins"]:
        prob_bar = "█" * int(r["predicted_prob"] * 50)
        print(f"   {r['bin']}: {r['predicted_prob']*100:.1f}% {prob_bar}")
    
    print(f"\n⏰ 入场建议: {rec['timing']}")
    print("=" * 70)


def run_loop():
    """持续轮询模式"""
    print("🔄 启动持续轮询模式 (Ctrl+C 退出)")
    while True:
        try:
            run_once()
            
            # 动态调整轮询间隔
            tracking = get_active_tracking()
            if tracking:
                end = datetime.fromisoformat(tracking["endDate"].replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                hours_remaining = (end - now).total_seconds() / 3600
                
                if hours_remaining < 0.25:  # 最后15分钟
                    interval = POLL_INTERVAL_FINAL
                elif hours_remaining < 4:  # 最后4小时
                    interval = POLL_INTERVAL_CRITICAL
                else:
                    interval = POLL_INTERVAL
            else:
                interval = POLL_INTERVAL
            
            print(f"\n⏳ 下次查询: {interval}秒后\n")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n👋 退出")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(30)


if __name__ == "__main__":
    if "--history" in sys.argv:
        print_history_analysis()
    elif "--loop" in sys.argv:
        run_loop()
    else:
        run_once()
