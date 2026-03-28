#!/usr/bin/env python3
"""
Polymarket Iran Arbitrage & Mispricing Detector
Monitors the Iran ceasefire time-structure for:
1. Arbitrage: April7 > April15 price (impossible - nearer date should be cheaper)
2. Mispricing: deviation from theoretical decay curve
3. Extreme signals: NO > $0.90 (panic) or NO < $0.30 (euphoria)

Run via cron or on-demand. Writes alerts to /tmp/poly_arb_alert.json
"""
import sqlite3, json, sys
from datetime import datetime, timezone

DB_PATH = "/root/.openclaw/workspace/data/ops.db"
ALERT_FILE = "/tmp/poly_arb_alert.json"
SOURCE_NAME = "polymarket_direct"  # must match scraper's SOURCE_NAME

# Expected NO prices if market were perfectly rational (discounting over time)
# BASELINE updated 2026-03-25 UTC from scraper live data (Mar31 run)
# These trigger MISPRICING alerts when deviation > 0.05
BASELINE = {
    "Mar31": 0.805,   # 2026-03-25 live: $0.805, $26.2M ⚡主战场
    "Apr7":  None,    # air market, skip baseline
    "Apr15": 0.605,   # 2026-03-25 live: $0.605, $4.0M
    "Apr30": 0.515,   # 2026-03-25 live: $0.515, $4.8M
    "May31": 0.395,   # 2026-03-25 live: $0.395, $1.7M
    "Jun30": 0.355,   # 2026-03-25 live: $0.355, $1.9M
    "Dec31": 0.225,   # 2026-03-25 live: $0.225, $0.3M
}

def load_latest_prices():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Use polymarket source (written by scraper)
    # Match by market_name for stability
    c.execute(f"""
        SELECT market_name, outcome, price, volume, ts
        FROM market_prices
        WHERE source='{SOURCE_NAME}'
        AND outcome='NO'
        AND price > 0 AND price < 1
        ORDER BY market_name, ts DESC
    """)
    rows = c.fetchall()
    conn.close()

    # Deduplicate by market_name (keep latest)
    seen = {}
    for r in rows:
        name = r[0]
        if name not in seen:
            seen[name] = r

    prices = {}
    for name, outcome, price, volume, ts in seen.values():
        vol = volume or 0
        n = name.lower()
        if "march 31" in n or "march-31" in n: key = "Mar31"
        elif "april 7" in n or "april-7" in n: key = "Apr7"
        elif "april 15" in n or "april-15" in n: key = "Apr15"
        elif "april 30" in n or "april-30" in n: key = "Apr30"
        elif "may 31" in n or "may-31" in n: key = "May31"
        elif "june 30" in n or "june-30" in n: key = "Jun30"
        elif "december 31" in n or "december-31" in n: key = "Dec31"
        else: key = name[-20:]

        prices[key] = {"price": price, "volume": vol, "ts": ts}

    return prices
    
    return prices

def detect_arbitrage(prices):
    """Check for price inversions (April7 > April15 means mispricing)"""
    alerts = []
    
    # Arbitrage check: later dates should have LOWER NO prices
    ordered_keys = ["Mar31", "Apr7", "Apr15", "Apr30", "May31", "Jun30", "Dec31"]
    for i in range(len(ordered_keys) - 1):
        key1, key2 = ordered_keys[i], ordered_keys[i+1]
        if key1 not in prices or key2 not in prices:
            continue
        p1 = prices[key1]["price"]
        p2 = prices[key2]["price"]
        if p1 < p2:
            alerts.append({
                "type": "ARBITRAGE",
                "severity": "HIGH",
                "msg": f"🔺 价格倒挂！{key1}=${p1:.3f} < {key2}=${p2:.3f} — 违反时间价值规律",
                "buy": key2,   # buy the cheaper one (later date)
                "sell": key1,  # sell the expensive one (nearer date)
                "spread": round(p2 - p1, 4),
            })
    
    return alerts

def detect_mispricing(prices):
    """Compare current prices to baseline decay curve"""
    alerts = []
    ordered_keys = ["Mar31", "Apr15", "Apr30", "May31", "Jun30", "Dec31"]
    
    for key in ordered_keys:
        if key not in prices:
            continue
        current = prices[key]["price"]
        baseline = BASELINE.get(key)
        if baseline is None:
            continue
        deviation = current - baseline
        if abs(deviation) > 0.05:
            direction = "↑高估" if deviation > 0 else "↓低估"
            alerts.append({
                "type": "MISPRICING",
                "severity": "MEDIUM" if abs(deviation) < 0.10 else "HIGH",
                "msg": f"📊 {key} 偏离基准: ${current:.3f} vs ${baseline:.3f} ({direction} {abs(deviation):.3f})",
                "key": key,
                "current": current,
                "baseline": baseline,
                "deviation": round(deviation, 4),
            })
    
    return alerts

def detect_extreme(prices):
    """Extreme signal detection"""
    alerts = []
    for key, data in prices.items():
        p = data["price"]
        vol = data["volume"]
        if p >= 0.90:
            alerts.append({
                "type": "EXTREME_PANIC",
                "severity": "HIGH",
                "msg": f"🚨 {key} 极度恐慌！NO=${p:.3f}（战争概率极高）",
                "price": p,
                "key": key,
            })
        elif p <= 0.30:
            alerts.append({
                "type": "EXTREME_EUPHORIA",
                "severity": "HIGH",
                "msg": f"🎉 {key} 市场乐观！NO=${p:.3f}（停战预期强烈）",
                "price": p,
                "key": key,
            })
    return alerts

def main():
    ts = datetime.now(timezone.utc).isoformat()
    prices = load_latest_prices()
    
    print(f"[{ts}] Iran Arbitrage Check:")
    for k, v in prices.items():
        print(f"  {k}: NO=${v['price']:.3f} vol={v['volume']:,.0f}")
    
    all_alerts = []
    all_alerts += detect_arbitrage(prices)
    all_alerts += detect_mispricing(prices)
    all_alerts += detect_extreme(prices)
    
    result = {
        "ts": ts,
        "prices": {k: {"price": v["price"], "volume": round(v["volume"], 2), "ts": v["ts"]} for k, v in prices.items()},
        "alerts": all_alerts,
        "ok": len(all_alerts) == 0,
    }
    
    with open(ALERT_FILE, "w") as f:
        json.dump(result, f, indent=2)
    
    if all_alerts:
        print(f"\n🚨 ALERTS ({len(all_alerts)}):")
        for a in all_alerts:
            print(f"  [{a['severity']}] {a['msg']}")
    else:
        print("\n✅ No alerts - market structure normal")
    
    return result

if __name__ == "__main__":
    main()
