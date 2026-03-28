#!/usr/bin/env python3
"""
Elon Poly 持仓监控 — 每30分钟运行
输出: JSON 状态写入 /tmp/elon_poly_monitor.json
告警: 重大变化时发 Discord
"""
import os, json, requests, re, math, subprocess
from datetime import datetime, timezone

POSITIONS = {
    "280-299": {"shares": 23.1, "cost_price": 0.13, "cost_usd": 3.00},
    "300-319": {"shares": 17.6, "cost_price": 0.17, "cost_usd": 2.99},
}
STATE_FILE = "/tmp/elon_poly_monitor.json"
DISCORD_CHANNEL = "1480446033531240469"

def get_tweets():
    r = requests.get("https://xtracker.polymarket.com/api/trackings/d861bacb-6108-45d6-9a14-47b9e58ea095?includeStats=true", timeout=10)
    return r.json()['data']['stats']['total']

def get_prices():
    gr = requests.get("https://gamma-api.polymarket.com/events/278377", timeout=10)
    prices = {}
    for m in gr.json().get("markets", []):
        q = m.get("question","")
        m2 = re.search(r'post (\d+)-(\d+) tweets', q)
        if m2:
            br = f"{m2.group(1)}-{m2.group(2)}"
            prices[br] = {
                "ask": float(m.get("bestAsk") or 0),
                "bid": float(m.get("bestBid") or 0),
                "last": float(m.get("lastTradePrice") or 0),
            }
    return prices

def predict(total, days_elapsed):
    DAY0 = datetime(2026, 3, 20, 16, 0, tzinfo=timezone.utc)
    days_remaining = 7 - days_elapsed
    rate = total / days_elapsed if days_elapsed > 0 else 0
    proj_rate = total + rate * days_remaining
    proj_bayes = 0.4 * proj_rate + 0.6 * 344
    return round(proj_bayes), round(rate, 1)

def send_alert(msg):
    try:
        subprocess.run(["openclaw", "message", "send", "--channel", "discord",
                       "--target", DISCORD_CHANNEL, "--message", msg],
                      timeout=15, capture_output=True)
    except:
        pass

def main():
    now = datetime.now(timezone.utc)
    DAY0 = datetime(2026, 3, 20, 16, 0, tzinfo=timezone.utc)
    days = (now - DAY0).total_seconds() / 86400

    tweets = get_tweets()
    prices = get_prices()
    proj, rate = predict(tweets, days)

    # 计算持仓盈亏
    total_cost = 0
    total_val = 0
    pos_details = {}
    for br, pos in POSITIONS.items():
        p = prices.get(br, {})
        mid = (p.get("bid",0) + p.get("ask",0)) / 2 if p.get("bid") else p.get("last", pos["cost_price"])
        val = pos["shares"] * mid
        pnl = val - pos["cost_usd"]
        total_cost += pos["cost_usd"]
        total_val += val
        pos_details[br] = {"mid": mid, "val": round(val,2), "pnl": round(pnl,2)}

    total_pnl = total_val - total_cost
    pnl_pct = total_pnl / total_cost * 100 if total_cost > 0 else 0

    # 模型概率
    STD = 50
    model_probs = {}
    for br in POSITIONS:
        lo, hi = map(int, br.split("-"))
        mid_br = (lo + hi) / 2
        p = max(0.02, 0.85 * math.exp(-0.5 * ((proj - mid_br) / STD) ** 2))
        model_probs[br] = round(p, 3)

    state = {
        "ts": now.isoformat(),
        "day": round(days, 2),
        "tweets": tweets,
        "rate_per_day": rate,
        "predicted_final": proj,
        "positions": pos_details,
        "model_probs": model_probs,
        "total_cost": round(total_cost, 2),
        "total_val": round(total_val, 2),
        "total_pnl": round(total_pnl, 2),
        "pnl_pct": round(pnl_pct, 1),
    }

    # 写状态文件
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    # 告警条件
    prev = {}
    try:
        with open(STATE_FILE + ".prev") as f:
            prev = json.load(f)
    except:
        pass

    alerts = []
    # 推文突变 (±20条/小时)
    if prev.get("tweets") and abs(tweets - prev["tweets"]) > 20:
        alerts.append(f"⚡ 推文突变: {prev['tweets']}→{tweets} (+{tweets-prev['tweets']})")
    # P&L 大幅变动 (±30%)
    if prev.get("pnl_pct") and abs(pnl_pct - prev["pnl_pct"]) > 30:
        alerts.append(f"💰 P&L突变: {prev['pnl_pct']:+.1f}%→{pnl_pct:+.1f}%")
    # 预测终点偏离持仓区间
    if proj < 260 or proj > 340:
        alerts.append(f"⚠️ 预测{proj}已偏离持仓区间280-319")

    # === 止盈止损规则 ===
    # 止损: Day>=5 且 速率<20/天 → 预测终点远低于持仓区间
    if days >= 5 and rate < 20:
        alerts.append(f"🔴 止损信号! 速率{rate:.0f}/天, 预测{proj}, 建议 market sell 退出")
    # 止盈: 任一持仓bracket的mid价>0.35 → 已赚2倍+
    for br, pos in POSITIONS.items():
        p = prices.get(br, {})
        mid_price = (p.get("bid",0) + p.get("ask",0)) / 2 if p.get("bid") else p.get("last", pos["cost_price"])
        if mid_price > 0.35:
            alerts.append(f"🟢 止盈信号! {br} 价格{mid_price:.3f} > 0.35, 已涨{(mid_price/pos['cost_price']-1)*100:.0f}%, 考虑卖一半")

    # === 每小时 orderbook 快照 ===
    snapshot = {"ts": now.isoformat(), "tweets": tweets, "day": round(days,2), "prices": {}}
    for br_name, pr_data in prices.items():
        snapshot["prices"][br_name] = pr_data
    ob_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orderbook_snapshots.jsonl")
    with open(ob_path, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

    if alerts:
        msg = f"[ELON-POLY] Day{days:.1f} | 🐦{tweets}条 | 预测{proj} | P&L ${total_pnl:+.2f}({pnl_pct:+.1f}%)\n" + "\n".join(alerts)
        send_alert(msg)
        print(msg)
    else:
        print(f"OK | Day{days:.1f} | 🐦{tweets} | 预测{proj} | P&L ${total_pnl:+.2f}({pnl_pct:+.1f}%)")

    # 保存 prev
    with open(STATE_FILE + ".prev", "w") as f:
        json.dump(state, f)

if __name__ == "__main__":
    main()
