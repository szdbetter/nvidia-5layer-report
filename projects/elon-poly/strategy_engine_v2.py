#!/usr/bin/env python3
"""
Elon Poly 三因子策略引擎 v2
重构: 动态持仓追踪（链上/CLOB API），自动入场逻辑，清除硬编码
"""
import os, json, re, math, requests, subprocess, sqlite3, time
from datetime import datetime, timezone
from collections import defaultdict

PROJ = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = "/tmp/elon_strategy.json"
OB_FILE = os.path.join(PROJ, "orderbook_snapshots.jsonl")
DECISION_LOG = os.path.join(PROJ, "decision_log.jsonl")
TRADE_LOG = os.path.join(PROJ, "trade_log.jsonl")
DB_FILE = os.path.join(PROJ, "elon_data.db")
POSITIONS_FILE = os.path.join(PROJ, "positions.json")
DISCORD_CH = "1480446033531240469"

# 事件参数
DAY0 = datetime(2026, 3, 20, 16, 0, tzinfo=timezone.utc)
DEADLINE = datetime(2026, 3, 27, 16, 0, tzinfo=timezone.utc)
HIST_MEAN = 344
HIST_STD = 80

# 交易参数
DRY_RUN = True  # ⚠️ 默认DRY_RUN=True，必须人工确认才改False
MAX_POSITIONS = 2
MAX_PER_BRACKET = 3.0  # 每bracket最多$3
MIN_RESERVE = 2.00     # 至少保留$2.00 USDC
ENTRY_EDGE_THRESHOLD = 0.10  # 10% edge才入场（严格>，不含等于）
AUTO_ENTRY_ENABLED = True

# 风控硬参数（不可被策略cron覆盖）
SL_PCT = -30           # 单笔止损 -30%
SL_ASK_FLOOR = 0.02    # ask跌破$0.02视为归零
DAILY_DRAWDOWN_LIMIT = -0.30  # 日内总亏损>30%触发熔断
CIRCUIT_BREAKER_FILE = os.path.join(PROJ, "CIRCUIT_BREAKER.lock")

# ============================================================
# 持仓管理（文件持久化，不再硬编码）
# ============================================================

def load_positions():
    """从文件加载持仓"""
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE) as f:
            return json.load(f)
    return {}

def save_positions(positions):
    """持仓写盘"""
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f, indent=2)

def record_trade(action, bracket, shares, price, cost, reason):
    """交易日志"""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action, "bracket": bracket,
        "shares": round(shares, 2), "price": round(price, 4),
        "cost": round(cost, 2), "reason": reason,
    }
    with open(TRADE_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

# ============================================================
# 钱包余额
# ============================================================

def get_usdc_balance():
    """查链上USDC.e余额"""
    EOA = "0xcD1862c43F7F276026AA1579eC2b8b9c02c10552"
    USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    data = "0x70a08231" + EOA[2:].lower().zfill(64)
    try:
        r = requests.post("https://polygon-bor-rpc.publicnode.com",
            json={"jsonrpc":"2.0","method":"eth_call","params":[{"to":USDC_E,"data":data},"latest"],"id":1},
            timeout=10)
        return int(r.json()["result"], 16) / 1e6
    except:
        return None

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
    """获取所有bracket盘口价格 + token IDs"""
    r = requests.get("https://gamma-api.polymarket.com/events/278377", timeout=15)
    prices = {}
    token_map = {}  # bracket -> YES token ID
    for m in r.json().get("markets", []):
        q = m.get("question", "")
        m2 = re.search(r'post (\d+)-(\d+) tweets', q)
        if not m2: continue
        br = f"{m2.group(1)}-{m2.group(2)}"
        tids = json.loads(m.get("clobTokenIds", "[]"))
        prices[br] = {
            "ask": float(m.get("bestAsk") or 0),
            "bid": float(m.get("bestBid") or 0),
            "last": float(m.get("lastTradePrice") or 0),
            "volume": float(m.get("volumeNum") or m.get("volume") or 0),
        }
        if tids:
            token_map[br] = tids[0]  # YES token
    return prices, token_map

def search_musk_news():
    """因子3: 速率突变检测"""
    signals = []
    try:
        total, daily = get_tweets()
        rates = list(daily.values())
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        complete_rates = [v for k, v in daily.items() if k < today]
        if len(complete_rates) >= 2:
            last_complete = complete_rates[-1]
            avg_prev = sum(complete_rates[:-1]) / len(complete_rates[:-1])
            if avg_prev > 0:
                ratio = last_complete / avg_prev
                if ratio > 2.0:
                    signals.append({"type": "SURGE", "ratio": round(ratio, 2), "msg": f"速率突增{ratio:.1f}倍"})
                elif ratio < 0.3:
                    signals.append({"type": "DROP", "ratio": round(ratio, 2), "msg": f"速率骤降至{ratio:.1f}倍"})
    except:
        pass
    return signals

def save_orderbook(tweets, days, prices):
    """保存orderbook快照"""
    snapshot = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tweets": tweets, "day": round(days, 3),
        "prices": prices
    }
    with open(OB_FILE, "a") as f:
        f.write(json.dumps(snapshot) + "\n")
    # SQLite
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
    if days <= 0: return HIST_MEAN, HIST_STD, {}
    rate = total / days
    proj_rate = total + rate * (7 - days)
    weight_obs = min(0.85, days / 7)
    proj = weight_obs * proj_rate + (1 - weight_obs) * HIST_MEAN
    std = HIST_STD * (1 - weight_obs * 0.7)
    return round(proj), round(std), {
        "rate_per_day": round(rate, 1),
        "proj_rate_only": round(proj_rate),
        "weight_obs": round(weight_obs, 2),
    }

def factor2_trend_analysis(daily_counts):
    rates = list(daily_counts.values())
    if len(rates) < 2:
        return "UNKNOWN", 0, {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rates_full = [v for k, v in daily_counts.items() if k < today]
    if len(rates_full) < 2:
        rates_full = rates[1:] if len(rates) > 2 else rates
    n = len(rates_full)
    x_mean = (n - 1) / 2
    y_mean = sum(rates_full) / n
    numerator = sum((i - x_mean) * (rates_full[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator > 0 else 0
    if slope > 5: trend = "ACCELERATING"
    elif slope < -5: trend = "DECELERATING"
    else: trend = "STABLE"
    adjustment = slope * 3
    return trend, round(adjustment), {
        "slope": round(slope, 2), "daily_rates": rates, "rates_analyzed": rates_full,
    }

def factor3_event_signal(news_signals):
    adjustment = 0
    confidence_boost = 0
    for sig in news_signals:
        if sig["type"] == "SURGE":
            adjustment += 30; confidence_boost += 0.1
        elif sig["type"] == "DROP":
            adjustment -= 30; confidence_boost += 0.1
    return adjustment, confidence_boost, news_signals

def compute_bracket_prob(bracket, mean, std):
    lo, hi = map(int, bracket.split("-"))
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
# 交易执行
# ============================================================

def get_clob_client():
    from dotenv import load_dotenv
    load_dotenv('/root/.openclaw/.env')
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import ApiCreds
    return ClobClient('https://clob.polymarket.com',
        key=os.environ['PRIVATE_KEY'], chain_id=137,
        creds=ApiCreds(
            api_key=os.environ['POLYMARKET_API_KEY'],
            api_secret=os.environ['POLYMARKET_API_SECRET'],
            api_passphrase=os.environ['POLYMARKET_API_PASSPHRASE']),
        signature_type=0)

def execute_buy(bracket, token_id, price, size_usd):
    """执行买入"""
    from py_clob_client.clob_types import OrderArgs, PartialCreateOrderOptions
    shares = round(size_usd / price, 1)
    if DRY_RUN:
        result = {"status": "DRY_RUN", "shares": shares, "price": price}
        record_trade("BUY_DRY", bracket, shares, price, size_usd, "dry run")
        return True, result

    try:
        client = get_clob_client()
        order = OrderArgs(token_id=token_id, price=price, size=shares, side="BUY")
        options = PartialCreateOrderOptions(neg_risk=True)
        resp = client.create_and_post_order(order, options)
        status = resp.get("status", "?") if isinstance(resp, dict) else str(resp)
        record_trade("BUY", bracket, shares, price, size_usd, f"CLOB: {status}")
        send_alert(f"🟢 BUY {bracket} | {shares}股 @ ${price} = ${size_usd} | {status}")
        return "MATCHED" in str(status).upper() or "LIVE" in str(status).upper(), resp
    except Exception as e:
        record_trade("BUY_FAIL", bracket, shares, price, size_usd, str(e))
        send_alert(f"❌ BUY FAILED {bracket}: {e}")
        return False, str(e)

def execute_sell(bracket, token_id, price, shares):
    """执行卖出"""
    from py_clob_client.clob_types import OrderArgs, PartialCreateOrderOptions
    if DRY_RUN:
        record_trade("SELL_DRY", bracket, shares, price, shares*price, "dry run")
        return True, {"status": "DRY_RUN"}

    try:
        client = get_clob_client()
        order = OrderArgs(token_id=token_id, price=price, size=shares, side="SELL")
        options = PartialCreateOrderOptions(neg_risk=True)
        resp = client.create_and_post_order(order, options)
        status = resp.get("status", "?") if isinstance(resp, dict) else str(resp)
        record_trade("SELL", bracket, shares, price, shares*price, f"CLOB: {status}")
        send_alert(f"🔴 SELL {bracket} | {shares}股 @ ${price} | {status}")
        return True, resp
    except Exception as e:
        record_trade("SELL_FAIL", bracket, shares, price, shares*price, str(e))
        return False, str(e)

# ============================================================
# 止盈止损 + 自动入场引擎
# ============================================================

def evaluate_decisions(days, rate, proj, std, prices, token_map, trend, positions):
    """
    综合决策引擎：止盈止损 + 新entry机会
    返回: list of (action, bracket, reason, urgency, params)
    """
    decisions = []
    total_cost = sum(p.get("cost", 0) for p in positions.values())

    # === 止盈止损：逐仓评估 ===
    for br, pos in positions.items():
        p = prices.get(br, {})
        mid = (p.get("bid",0) + p.get("ask",0)) / 2 if p.get("bid") else p.get("last", pos.get("entry_price", 0))
        val = pos["shares"] * mid
        cost = pos.get("cost", 0)
        pnl_pct = (val - cost) / cost * 100 if cost > 0 else 0

        # SL1: 单笔亏损超阈值
        if pnl_pct < SL_PCT:
            decisions.append(("STOP_LOSS", br, f"{br}亏损{pnl_pct:.0f}% (阈值{SL_PCT}%)", "CRITICAL", {"shares": pos["shares"], "bid": p.get("bid", 0)}))

        # SL2: ask跌破地板价（市场已放弃）
        if 0 < p.get("ask", 0) < SL_ASK_FLOOR:
            decisions.append(("STOP_LOSS", br, f"{br} ask={p['ask']:.3f}<{SL_ASK_FLOOR} 市场已放弃", "CRITICAL", {"shares": pos["shares"], "bid": p.get("bid", 0)}))

        # SL3: 预测远离bracket（结构性止损）
        lo, hi = map(int, br.split("-"))
        if days >= 4 and proj < lo - std:
            decisions.append(("STOP_LOSS", br, f"预测{proj}±{std}远低于{br}", "CRITICAL", {"shares": pos["shares"], "bid": p.get("bid", 0)}))

        # TP: 翻倍
        if pnl_pct > 100:
            decisions.append(("TAKE_PROFIT", br, f"{br}盈利{pnl_pct:.0f}%，卖出一半", "MEDIUM", {"shares": pos["shares"] / 2, "bid": p.get("bid", 0)}))

        # TP: bracket价格>0.40
        if mid > 0.40:
            decisions.append(("TAKE_PROFIT", br, f"{br}价格{mid:.3f}，锁利", "MEDIUM", {"shares": pos["shares"] / 2, "bid": p.get("bid", 0)}))

    # === 新Entry机会 ===
    if AUTO_ENTRY_ENABLED and len(positions) < MAX_POSITIONS:
        usdc = get_usdc_balance()
        available = (usdc - MIN_RESERVE) if usdc else 0

        if available > 1.0:
            # 扫描所有有意义的brackets
            candidates = []
            for br, p in prices.items():
                ask = p.get("ask", 0)
                if ask < 0.01 or ask > 0.50: continue
                if br in positions: continue  # 已持仓

                model_prob = compute_bracket_prob(br, proj, std)
                edge = model_prob - ask
                if edge > ENTRY_EDGE_THRESHOLD:  # 严格大于，消除边界触发
                    ev = model_prob / ask  # EV multiplier
                    candidates.append((br, ask, model_prob, edge, ev))

            # 按edge排序，取top 2
            candidates.sort(key=lambda x: -x[3])
            for br, ask, model_p, edge, ev in candidates[:2]:
                alloc = min(available / min(2, len(candidates)), MAX_PER_BRACKET)
                if alloc < 1.0: continue
                decisions.append(("ENTRY", br, f"edge={edge:.1%} model={model_p:.1%} ask={ask:.3f} EV={ev:.1f}x",
                    "MEDIUM", {"ask": ask, "size_usd": round(alloc, 2), "token_id": token_map.get(br)}))
                available -= alloc

    # 默认HOLD
    if not decisions:
        decisions.append(("HOLD", "ALL", f"预测{proj}±{std}, 无信号触发", "LOW", {}))

    return decisions

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

def check_circuit_breaker():
    """熔断检查：如果lock文件存在，拒绝所有交易"""
    if os.path.exists(CIRCUIT_BREAKER_FILE):
        with open(CIRCUIT_BREAKER_FILE) as f:
            reason = f.read().strip()
        return True, reason
    return False, ""

def trigger_circuit_breaker(reason):
    """触发熔断：写lock文件 + 告警"""
    with open(CIRCUIT_BREAKER_FILE, "w") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} | {reason}")
    send_alert(f"[ELON] 🚨🚨 熔断触发: {reason}\n所有交易已停止，需人工解除 CIRCUIT_BREAKER.lock")

def verify_positions_onchain(positions, token_map):
    """链上验证持仓，清除phantom持仓"""
    EOA = "0xcD1862c43F7F276026AA1579eC2b8b9c02c10552"
    CTF = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
    verified = {}
    for br, pos in positions.items():
        tid = token_map.get(br)
        if not tid: continue
        try:
            import eth_abi
            data = "0x00fdd58e" + eth_abi.encode(['address','uint256'], [EOA, int(tid)]).hex()
            r = requests.post("https://polygon-bor-rpc.publicnode.com",
                json={"jsonrpc":"2.0","method":"eth_call","params":[{"to":CTF,"data":data},"latest"],"id":1}, timeout=10)
            onchain_shares = int(r.json()["result"], 16) / 1e6
            if onchain_shares > 0.1:  # 有实际持仓
                pos_copy = dict(pos)
                pos_copy["shares"] = onchain_shares  # 以链上为准
                verified[br] = pos_copy
            # 链上为0 → 不加入verified，等于自动清除phantom
        except:
            verified[br] = pos  # RPC失败时保留本地数据
    return verified

def main():
    now = datetime.now(timezone.utc)
    days = (now - DAY0).total_seconds() / 86400

    # 熔断检查
    tripped, reason = check_circuit_breaker()
    if tripped:
        print(f"⛔ 熔断中: {reason}")
        return

    # 过期检查
    if now >= DEADLINE:
        print("EVENT ENDED. Daemon should stop.")
        return

    # 1. 数据采集
    total, daily = get_tweets()
    prices, token_map = get_all_prices()
    news = search_musk_news()

    # 2. 保存orderbook
    save_orderbook(total, days, prices)

    # 3. 三因子
    proj, std, f1_detail = factor1_rate_momentum(total, days)
    trend, trend_adj, f2_detail = factor2_trend_analysis(daily)
    event_adj, conf_boost, f3_detail = factor3_event_signal(news)
    final_proj = proj + trend_adj + event_adj
    final_std = max(20, std - conf_boost * 20)

    # 4. 加载持仓 + 链上验证
    positions = load_positions()
    positions = verify_positions_onchain(positions, token_map)
    save_positions(positions)  # 回写链上验证后的数据

    # 5. 持仓盈亏
    total_cost = sum(p.get("cost", 0) for p in positions.values())
    total_val = 0
    pos_details = {}
    for br, pos in positions.items():
        p = prices.get(br, {})
        mid = (p.get("bid",0) + p.get("ask",0)) / 2 if p.get("bid") else p.get("last", pos.get("entry_price", 0))
        val = pos["shares"] * mid
        pnl = val - pos.get("cost", 0)
        total_val += val
        model_p = compute_bracket_prob(br, final_proj, final_std)
        pos_details[br] = {
            "shares": pos["shares"], "entry_price": pos.get("entry_price", 0),
            "mid": round(mid, 4), "val": round(val, 2), "pnl": round(pnl, 2),
            "model_prob": round(model_p, 3), "edge": round(model_p - p.get("ask", 0), 3),
        }

    total_pnl = total_val - total_cost if total_cost > 0 else 0
    pnl_pct = total_pnl / total_cost * 100 if total_cost > 0 else 0

    # 5b. 日内熔断检查
    if total_cost > 0 and pnl_pct / 100 < DAILY_DRAWDOWN_LIMIT:
        trigger_circuit_breaker(f"日内亏损{pnl_pct:.1f}% 超过阈值{DAILY_DRAWDOWN_LIMIT*100:.0f}%")
        # 强制全仓平仓
        for br, pos in list(positions.items()):
            tid = token_map.get(br)
            bid = prices.get(br, {}).get("bid", 0)
            if tid and bid > 0.001 and not DRY_RUN:
                execute_sell(br, tid, bid, pos["shares"])
            del positions[br]
        save_positions(positions)
        return

    # 6. 决策引擎
    rate = total / days if days > 0 else 0
    decisions = evaluate_decisions(days, rate, final_proj, final_std, prices, token_map, trend, positions)

    # 7. 执行决策
    executed = []
    for action, bracket, reason, urgency, params in decisions:
        if action == "ENTRY" and params.get("token_id"):
            ok, resp = execute_buy(bracket, params["token_id"], params["ask"], params["size_usd"])
            if ok:
                shares = round(params["size_usd"] / params["ask"], 1)
                positions[bracket] = {
                    "shares": shares, "entry_price": params["ask"],
                    "cost": params["size_usd"], "ts": now.isoformat(),
                }
                save_positions(positions)
                executed.append(f"✅ BUY {bracket} {shares}股@{params['ask']}")
            else:
                executed.append(f"❌ BUY {bracket} FAILED: {resp}")

        elif action in ("STOP_LOSS", "TAKE_PROFIT") and bracket in positions:
            tid = token_map.get(bracket)
            if tid and params.get("bid", 0) > 0.005:
                shares_to_sell = params.get("shares", positions[bracket]["shares"])
                ok, resp = execute_sell(bracket, tid, params["bid"], shares_to_sell)
                if ok:
                    if shares_to_sell >= positions[bracket]["shares"]:
                        del positions[bracket]
                    else:
                        positions[bracket]["shares"] -= shares_to_sell
                    save_positions(positions)
                    executed.append(f"✅ {action} {bracket} {shares_to_sell}股@{params['bid']}")

    # 8. 输出状态
    usdc = get_usdc_balance()
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
        "position_count": len(positions),
        "pnl": {"total_cost": round(total_cost, 2), "total_val": round(total_val, 2),
                "total_pnl": round(total_pnl, 2), "pnl_pct": round(pnl_pct, 1)},
        "usdc_balance": usdc,
        "decisions": [{"action": a, "bracket": b, "reason": r, "urgency": u} for a, b, r, u, _ in decisions],
        "executed": executed,
        "dry_run": DRY_RUN,
    }

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    # 9. 决策日志
    log_entry = {
        "ts": now.isoformat(), "day": round(days, 2), "tweets": total,
        "proj": final_proj, "std": final_std, "trend": trend,
        "positions": len(positions), "pnl_pct": round(pnl_pct, 1),
        "decisions": [f"{a}:{b}" for a, b, _, _, _ in decisions],
        "executed": executed,
    }
    with open(DECISION_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    # 10. 告警
    has_critical = any(u in ("HIGH", "CRITICAL") for _, _, _, u, _ in decisions)
    if has_critical or executed:
        emoji = "🔴" if any("STOP" in a for a, _, _, _, _ in decisions) else "🟢" if executed else "⚠️"
        exec_str = " | ".join(executed) if executed else "无执行"
        msg = f"[ELON] {emoji} Day{days:.1f} | 🐦{total} | 预测{final_proj}±{final_std} | {trend}\n持仓{len(positions)}个 | USDC ${usdc:.2f}\n{exec_str}"
        send_alert(msg)
        print(msg)
    else:
        p_str = f"持仓{len(positions)}" if positions else "空仓"
        print(f"OK | Day{days:.1f} | 🐦{total} | 预测{final_proj}±{final_std} | {trend} | {p_str} | USDC ${usdc:.2f}")

if __name__ == "__main__":
    main()
