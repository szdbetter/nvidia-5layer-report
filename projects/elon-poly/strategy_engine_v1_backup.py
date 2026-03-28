#!/usr/bin/env python3
"""
Elon Poly 三因子策略引擎 + 止盈止损 + 数据采集
每小时运行一次，输出决策到 /tmp/elon_strategy.json
"""
import os, json, re, math, requests, subprocess, sqlite3
from datetime import datetime, timezone
from collections import defaultdict

PROJ = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = "/tmp/elon_strategy.json"
OB_FILE = os.path.join(PROJ, "orderbook_snapshots.jsonl")
DECISION_LOG = os.path.join(PROJ, "decision_log.jsonl")
DB_FILE = os.path.join(PROJ, "elon_data.db")
DISCORD_CH = "1480446033531240469"

# 持仓
POSITIONS = {
    "280-299": {"shares": 23.1, "entry_price": 0.13, "cost": 3.00},
    "300-319": {"shares": 17.6, "entry_price": 0.17, "cost": 2.99},
}
TOTAL_COST = 5.99

# 事件参数
DAY0 = datetime(2026, 3, 20, 16, 0, tzinfo=timezone.utc)
DEADLINE = datetime(2026, 3, 27, 16, 0, tzinfo=timezone.utc)
HIST_MEAN = 344
HIST_STD = 80

# ============================================================
# 数据采集层
# ============================================================

def get_tweets():
    """获取实时推文数据"""
    r = requests.get("https://xtracker.polymarket.com/api/trackings/d861bacb-6108-45d6-9a14-47b9e58ea095?includeStats=true", timeout=15)
    data = r.json()['data']
    total = data['stats']['total']
    daily = defaultdict(int)
    for h in data['stats'].get('daily', []):
        daily[h['date'][:10]] += h['count']
    return total, dict(sorted(daily.items()))

def get_all_prices():
    """获取所有bracket盘口价格"""
    r = requests.get("https://gamma-api.polymarket.com/events/278377", timeout=15)
    prices = {}
    for m in r.json().get("markets", []):
        q = m.get("question","")
        m2 = re.search(r'post (\d+)-(\d+) tweets', q)
        if not m2: continue
        br = f"{m2.group(1)}-{m2.group(2)}"
        prices[br] = {
            "ask": float(m.get("bestAsk") or 0),
            "bid": float(m.get("bestBid") or 0),
            "last": float(m.get("lastTradePrice") or 0),
            "volume": float(m.get("volumeNum") or m.get("volume") or 0),
        }
    return prices

def search_musk_news():
    """因子3: Musk/企业新闻信号（简化版：检查推文速率突变作为代理指标）"""
    # 完整版需要Twitter API或Fiona抓取，当前用速率突变检测代替
    # 逻辑：如果最近3小时速率 vs 前24小时均速差异>2倍，视为事件驱动
    signals = []
    try:
        total, daily = get_tweets()
        rates = list(daily.values())
        if len(rates) >= 2:
            # Fix: exclude current incomplete day (last entry) from analysis
            # last_day = rates[-1]  # ← BUG: includes today's partial data
            complete_rates = rates[:-1]  # only fully-collected days
            if len(complete_rates) >= 2:
                last_complete = complete_rates[-1]
                avg_prev = sum(complete_rates[:-1]) / len(complete_rates[:-1])
                if avg_prev > 0:
                    ratio = last_complete / avg_prev
                    if ratio > 2.0:
                        signals.append({"type": "SURGE", "ratio": round(ratio, 2), "msg": f"最近完整日速率是前均的{ratio:.1f}倍，疑似事件驱动"})
                    elif ratio < 0.3:
                        signals.append({"type": "DROP", "ratio": round(ratio, 2), "msg": f"最近完整日速率仅为前均的{ratio:.1f}倍，Elon可能沉默"})
    except:
        pass
    return signals

def save_orderbook(tweets, days, prices):
    """保存orderbook快照到JSONL + SQLite"""
    snapshot = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tweets": tweets, "day": round(days, 3),
        "prices": prices
    }
    with open(OB_FILE, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

    # SQLite持久化
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""CREATE TABLE IF NOT EXISTS orderbook (
        ts TEXT, tweets INT, day REAL, bracket TEXT, ask REAL, bid REAL, last_price REAL, volume REAL
    )""")
    ts = snapshot["ts"]
    for br, p in prices.items():
        conn.execute("INSERT INTO orderbook VALUES (?,?,?,?,?,?,?,?)",
            (ts, tweets, round(days,3), br, p["ask"], p["bid"], p["last"], p.get("volume",0)))
    conn.commit()
    conn.close()

# ============================================================
# 三因子模型
# ============================================================

def factor1_rate_momentum(total, days):
    """因子1: 速率动量外推"""
    if days <= 0: return HIST_MEAN, HIST_STD, {}
    rate = total / days
    proj_rate = total + rate * (7 - days)

    # 贝叶斯融合: 越接近结束越信实时
    weight_obs = min(0.85, days / 7)
    proj = weight_obs * proj_rate + (1 - weight_obs) * HIST_MEAN

    # 不确定性随时间收窄
    std = HIST_STD * (1 - weight_obs * 0.7)

    return round(proj), round(std), {
        "rate_per_day": round(rate, 1),
        "proj_rate_only": round(proj_rate),
        "weight_obs": round(weight_obs, 2),
    }

def factor2_trend_analysis(daily_counts):
    """因子2: 趋势分析（加速/减速/稳定）"""
    rates = list(daily_counts.values())
    if len(rates) < 2:
        return "UNKNOWN", 0, {}

    # 排除当前未完成日：只取昨天及以前的数据
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rates_full = [v for k, v in daily_counts.items() if k < today]

    # 兜底：若过滤后不足2天，用全部数据（但至少跳过Day1）
    if len(rates_full) < 2:
        rates_full = rates[1:] if len(rates) > 2 else rates

    # 线性回归斜率
    n = len(rates_full)
    x_mean = (n - 1) / 2
    y_mean = sum(rates_full) / n
    numerator = sum((i - x_mean) * (rates_full[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator > 0 else 0

    # 判定趋势
    if slope > 5:
        trend = "ACCELERATING"
    elif slope < -5:
        trend = "DECELERATING"
    else:
        trend = "STABLE"

    # 用趋势调整预测
    # 如果减速：终点偏低；加速：终点偏高
    adjustment = slope * 3  # 粗略：斜率×剩余天数的一半

    return trend, round(adjustment), {
        "slope": round(slope, 2),
        "daily_rates": rates,
        "rates_analyzed": rates_full,
    }

def factor3_event_signal(news_signals):
    """因子3: 事件驱动信号"""
    adjustment = 0
    confidence_boost = 0

    for sig in news_signals:
        if sig["type"] == "SURGE":
            adjustment += 30  # 事件驱动可能多发30条
            confidence_boost += 0.1
        elif sig["type"] == "DROP":
            adjustment -= 30
            confidence_boost += 0.1

    return adjustment, confidence_boost, news_signals

def compute_bracket_prob(bracket, mean, std):
    """计算某bracket的模型概率"""
    parts = bracket.split("-")
    lo, hi = int(parts[0]), int(parts[1])

    def norm_cdf(x):
        a1,a2,a3,a4,a5 = 0.254829592,-0.284496736,1.421413741,-1.453152027,1.061405429
        p = 0.3275911
        sign = 1 if x >= 0 else -1
        x = abs(x) / math.sqrt(2)
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5*t+a4)*t)+a3)*t+a2)*t+a1)*t*math.exp(-x*x)
        return 0.5*(1.0 + sign*y)

    return norm_cdf((hi + 1 - mean) / std) - norm_cdf((lo - mean) / std)

# ============================================================
# 止盈止损引擎
# ============================================================

def evaluate_stop_rules(days, rate, proj, std, prices, trend, pnl_pct):
    """
    止盈止损决策引擎
    返回: (action, reason, urgency)
    action: HOLD / STOP_LOSS / TAKE_PROFIT / HEDGE
    urgency: LOW / MEDIUM / HIGH / CRITICAL
    """
    actions = []

    # === 止损规则 ===

    # SL1: 预测终点远低于持仓区间 (Day>=4, proj < 250)
    if days >= 4 and proj < 250:
        actions.append(("STOP_LOSS", f"预测{proj}远低于持仓280-319，命中概率极低", "CRITICAL"))

    # SL2: 速率持续递减且Day>=5
    if days >= 5 and rate < 20:
        actions.append(("STOP_LOSS", f"Day{days:.1f}速率仅{rate:.0f}/天，终点大概率<250", "HIGH"))

    # SL3: 持仓bracket的ask跌破0.05（市场已放弃这个区间）
    for br, pos in POSITIONS.items():
        p = prices.get(br, {})
        ask = p.get("ask", pos["entry_price"])
        if ask < 0.05:
            actions.append(("STOP_LOSS", f"{br} ask={ask:.3f}跌破0.05，市场判定概率<5%", "HIGH"))

    # SL4: 总P&L亏损>60%
    if pnl_pct < -60:
        actions.append(("STOP_LOSS", f"总亏损{pnl_pct:.0f}%已超止损线60%", "CRITICAL"))

    # === 止盈规则 ===

    # TP1: 任一bracket价格>0.35 → 已赚1.7倍+
    for br, pos in POSITIONS.items():
        p = prices.get(br, {})
        mid = (p.get("bid",0) + p.get("ask",0)) / 2 if p.get("bid") else p.get("last", pos["entry_price"])
        if mid > 0.35:
            profit_mult = mid / pos["entry_price"]
            actions.append(("TAKE_PROFIT", f"{br}价格{mid:.3f}，已涨{profit_mult:.1f}倍，卖一半锁利", "MEDIUM"))

    # TP2: 总P&L>100% → 翻倍了
    if pnl_pct > 100:
        actions.append(("TAKE_PROFIT", f"总盈利{pnl_pct:.0f}%已翻倍，建议至少卖出成本部分", "HIGH"))

    # === 对冲规则 ===

    # H1: 预测不确定性大(std>60)且Day<5 → 考虑买相邻bracket对冲
    if std > 60 and days < 5:
        actions.append(("HEDGE", f"预测不确定性高(±{std:.0f})，考虑买260-279或320-339对冲", "LOW"))

    # === 趋势加速 → 可能加仓 ===
    if trend == "ACCELERATING" and 280 <= proj <= 340 and pnl_pct > 0:
        actions.append(("HOLD", f"趋势加速+预测在区间内+已盈利，坚定持有", "LOW"))

    # 默认
    if not actions:
        if 270 <= proj <= 330:
            actions.append(("HOLD", f"预测{proj}在持仓区间附近，继续持有", "LOW"))
        elif proj > 330:
            actions.append(("HOLD", f"预测{proj}偏高但仍有可能回落，观察", "LOW"))
        else:
            actions.append(("HOLD", f"预测{proj}偏低但未触止损线，继续观察", "MEDIUM"))

    # 返回最高优先级的action
    urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    actions.sort(key=lambda x: urgency_order.get(x[2], 9))
    return actions[0] if actions else ("HOLD", "无信号", "LOW"), actions

def send_alert(msg):
    try:
        subprocess.run(["openclaw", "message", "send", "--channel", "discord",
                       "--target", DISCORD_CH, "--message", msg],
                      timeout=15, capture_output=True)
    except:
        pass

# ============================================================
# 主流程
# ============================================================

def main():
    now = datetime.now(timezone.utc)
    days = (now - DAY0).total_seconds() / 86400

    # 1. 数据采集
    total, daily = get_tweets()
    prices = get_all_prices()
    news = search_musk_news()

    # 2. 保存orderbook快照
    save_orderbook(total, days, prices)

    # 3. 三因子计算
    proj, std, f1_detail = factor1_rate_momentum(total, days)
    trend, trend_adj, f2_detail = factor2_trend_analysis(daily)
    event_adj, conf_boost, f3_detail = factor3_event_signal(news)

    # 综合预测
    final_proj = proj + trend_adj + event_adj
    final_std = max(20, std - conf_boost * 20)

    # 4. 持仓盈亏
    total_val = 0
    pos_details = {}
    for br, pos in POSITIONS.items():
        p = prices.get(br, {})
        mid = (p.get("bid",0) + p.get("ask",0)) / 2 if p.get("bid") else p.get("last", pos["entry_price"])
        val = pos["shares"] * mid
        pnl = val - pos["cost"]
        total_val += val
        model_p = compute_bracket_prob(br, final_proj, final_std)
        pos_details[br] = {
            "mid": round(mid, 4), "val": round(val, 2), "pnl": round(pnl, 2),
            "model_prob": round(model_p, 3), "edge": round(model_p - p.get("ask", 0), 3),
        }

    total_pnl = total_val - TOTAL_COST
    pnl_pct = total_pnl / TOTAL_COST * 100

    # 5. 止盈止损决策
    rate = total / days if days > 0 else 0
    (action, reason, urgency), all_actions = evaluate_stop_rules(
        days, rate, final_proj, final_std, prices, trend, pnl_pct)

    # 6. 输出状态
    state = {
        "ts": now.isoformat(),
        "day": round(days, 2),
        "tweets": total,
        "daily": daily,
        "factors": {
            "f1_momentum": {"projection": proj, "std": std, **f1_detail},
            "f2_trend": {"trend": trend, "adjustment": trend_adj, **f2_detail},
            "f3_event": {"adjustment": event_adj, "signals": f3_detail},
        },
        "prediction": {"mean": final_proj, "std": final_std, "range": [final_proj - final_std, final_proj + final_std]},
        "positions": pos_details,
        "pnl": {"total_cost": TOTAL_COST, "total_val": round(total_val, 2), "total_pnl": round(total_pnl, 2), "pnl_pct": round(pnl_pct, 1)},
        "decision": {"action": action, "reason": reason, "urgency": urgency},
        "all_signals": [{"action": a, "reason": r, "urgency": u} for a, r, u in all_actions],
    }

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    # 7. 决策日志
    log_entry = {
        "ts": now.isoformat(), "day": round(days,2), "tweets": total,
        "proj": final_proj, "trend": trend, "action": action, "reason": reason,
        "urgency": urgency, "pnl_pct": round(pnl_pct, 1),
    }
    with open(DECISION_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    # 8. 告警（仅HIGH/CRITICAL）
    if urgency in ("HIGH", "CRITICAL"):
        emoji = "🔴" if "STOP" in action else "🟢" if "PROFIT" in action else "⚠️"
        msg = f"[ELON-POLY] {emoji} {action} | Day{days:.1f} | 🐦{total} | 预测{final_proj}±{final_std}\n{reason}\nP&L: ${total_pnl:+.2f} ({pnl_pct:+.1f}%)"
        send_alert(msg)
        print(msg)
    else:
        print(f"OK | Day{days:.1f} | 🐦{total} | 预测{final_proj}±{final_std} | {trend} | {action} | P&L ${total_pnl:+.2f}({pnl_pct:+.1f}%)")

if __name__ == "__main__":
    main()


# ============================================================
# 自动止损执行器（CRITICAL级别自动卖出）
# ============================================================

def auto_execute_stop_loss(prices):
    """当止损信号为CRITICAL时，自动market sell所有持仓"""
    import os
    from dotenv import load_dotenv
    load_dotenv('/root/.openclaw/.env')
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import ApiCreds, OrderArgs, PartialCreateOrderOptions

    client = ClobClient('https://clob.polymarket.com',
        key=os.environ['PRIVATE_KEY'], chain_id=137,
        creds=ApiCreds(
            api_key=os.environ['POLYMARKET_API_KEY'],
            api_secret=os.environ['POLYMARKET_API_SECRET'],
            api_passphrase=os.environ['POLYMARKET_API_PASSPHRASE']),
        signature_type=0)

    results = []
    for br, pos in POSITIONS.items():
        bid = prices.get(br, {}).get("bid", 0)
        if bid <= 0.01:
            bid = prices.get(br, {}).get("last", 0.01)
        if bid <= 0.01:
            results.append(f"❌ {br}: bid太低({bid})，无法卖出")
            continue
        try:
            # 获取正确的token ID
            import re
            gr = requests.get("https://gamma-api.polymarket.com/events/278377", timeout=10)
            for m in gr.json().get("markets", []):
                if br.split("-")[0] in m.get("question","") and br.split("-")[1] in m.get("question",""):
                    import json as jn
                    tok = jn.loads(m.get("clobTokenIds","[]"))[0]
                    break
            else:
                results.append(f"❌ {br}: 找不到token ID")
                continue

            order = OrderArgs(token_id=tok, price=bid, size=pos["shares"], side="SELL")
            options = PartialCreateOrderOptions(neg_risk=True)
            resp = client.create_and_post_order(order, options)
            status = resp.get("status","?")
            results.append(f"✅ {br}: SELL {pos['shares']}股 @ {bid} → {status}")
        except Exception as e:
            results.append(f"❌ {br}: {e}")

    return results


# 在main()最后追加自动执行逻辑
_original_main = main

def main_with_autoexec():
    _original_main()

    # 读取决策结果
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        decision = state.get("decision", {})
        action = decision.get("action", "")
        urgency = decision.get("urgency", "")

        if action == "STOP_LOSS" and urgency == "CRITICAL":
            send_alert("🔴🔴🔴 自动止损触发! 正在卖出全部持仓...")
            prices = state.get("positions", {})
            # 重新获取价格
            all_prices = get_all_prices()
            results = auto_execute_stop_loss(all_prices)
            result_msg = "\n".join(results)
            send_alert(f"[止损执行结果]\n{result_msg}")
            print(f"AUTO STOP LOSS EXECUTED:\n{result_msg}")
    except Exception as e:
        print(f"Auto-exec check error: {e}")

main = main_with_autoexec
