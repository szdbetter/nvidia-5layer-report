#!/usr/bin/env python3
"""
Polymarket Iran Signal Pusher v4
Fixed: queries source='polymarket_direct', uses market_name for matching.
"""
import sqlite3, json, datetime, os

DB_PATH = "/root/.openclaw/workspace/data/ops.db"
LOG_FILE = "/tmp/poly_signal_pusher.log"
STATE_FILE = "/tmp/poly_signal_state.json"
SOURCE_NAME = "polymarket_direct"  # must match scraper's SOURCE_NAME

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def get_latest_markets():
    """Get latest NO prices for Iran markets from polymarket_direct source.
    Use market_name for stable matching since market_id can be corrupted."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Get unique markets by market_name, latest first, only NO outcome
    cur.execute("""
        SELECT market_name, outcome, price, volume, ts
        FROM market_prices
        WHERE source='polymarket_direct'
        AND outcome='NO'
        AND price > 0 AND price < 1
        ORDER BY market_name, ts DESC
    """)
    rows = cur.fetchall()
    conn.close()
    # Deduplicate by market_name (keep first/most recent)
    seen = {}
    for row in rows:
        name = row[0]
        if name not in seen:
            seen[name] = row
    return list(seen.values())

def get_march_no(markets):
    for market_name, outcome, price, volume, ts in markets:
        if "march 31" in market_name.lower():
            return price
    return None

def build_signal_text(markets):
    date_order = ["march 31", "april 7", "april 15", "april 30", "may 31", "june 30", "december 31"]
    labels = {
        "march 31": "🟰 Mar 31", "april 7": "💨 Apr 7",
        "april 15": "📅 Apr 15", "april 30": "📅 Apr 30",
        "may 31": "📅 May 31", "june 30": "📅 Jun 30", "december 31": "📅 Dec 31"
    }
    data = {}
    for market_name, outcome, price, volume, ts in markets:
        for d in date_order:
            if d in market_name.lower():
                if d not in data:
                    data[d] = {"NO": None, "vol": ""}
                data[d]["NO"] = price
                if volume:
                    data[d]["vol"] = f"${volume/1e6:.1f}M"
                break

    lines = ["**Iran Ceasefire — Polymarket Real-Time**\n"]
    lines.append("```")
    lines.append(f"{'Date':<12} {'YES':>8} {'NO':>8} {'Volume':>10}")
    lines.append("-" * 44)
    march_no = None

    for d in date_order:
        if d not in data: continue
        row = data[d]
        if row["NO"] is None: continue
        no_p = f"${row['NO']:.3f}"
        yes_p = "N/A"  # scraper v1 only writes NO
        vol = row["vol"]
        if d == "march 31": march_no = row["NO"]
        lines.append(f"{labels[d]:<12} {yes_p:>8} {no_p:>8} {vol:>10}")

    lines.append("```")

    if march_no:
        ceasefire_prob = 1 - march_no
        signal = "🔴 **停战概率极低，NO仓坚定持有**" if march_no > 0.80 else "🟡 市场偏向不停战"
        today = datetime.datetime.now(datetime.timezone.utc)
        march31 = datetime.datetime(2026, 3, 31, 23, 59, tzinfo=datetime.timezone.utc)
        days_left = max(0, (march31 - today).days)
        lines.append(f"\n**March 31**: NO=${march_no:.3f} → 停战概率 **{ceasefire_prob:.1%}**")
        lines.append(f"**信号**: {signal}")
        lines.append(f"⏰ **到期倒计时**: {days_left} 天")
        if days_left <= 7:
            lines.append("⚠️ **最后1周！3月31日结算**")

    return "\n".join(lines), march_no

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except: pass
    return {"last_push": None, "march_no": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def should_push(state, markets):
    march_no = get_march_no(markets)
    if march_no is None: return False, None
    now = datetime.datetime.now(datetime.timezone.utc)
    last_push = state.get("last_push")
    if not last_push: return True, march_no
    try:
        last_dt = datetime.datetime.fromisoformat(last_push)
    except: return True, march_no
    if (now - last_dt).total_seconds() > 3600: return True, march_no
    last_march_no = state.get("march_no")
    if last_march_no is not None and abs(march_no - last_march_no) > 0.02:
        return True, march_no
    return False, march_no

def main():
    log("=== Signal pusher v4 started ===")
    state = load_state()
    markets = get_latest_markets()
    log(f"Got {len(markets)} markets")
    if not markets:
        log("ERROR: No market data")
        return
    march_no = get_march_no(markets)
    log(f"March31 NO: {march_no}")
    push, current_no = should_push(state, markets)

    if push:
        content, m_no = build_signal_text(markets)
        msg_file = "/tmp/poly_signal_msg.txt"
        with open(msg_file, "w") as f:
            f.write(content)
        log(f"Signal written to {msg_file} (March31 NO={m_no})")
        state["last_push"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        state["march_no"] = current_no
        save_state(state)
    else:
        log(f"No push needed (current March31 NO={current_no}, last={state.get('march_no')})")
    log("=== Done ===")

if __name__ == "__main__":
    main()
