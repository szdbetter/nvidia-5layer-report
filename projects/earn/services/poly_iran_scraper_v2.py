#!/usr/bin/env python3
"""
Polymarket Iran Markets Scraper v2
Uses Polymarket gamma API (no key needed, reliable).
Scrapes all Iran ceasefire sub-markets and writes to ops.db.
"""
import re, json, sqlite3, urllib.request
from datetime import datetime, timezone, timedelta

DB_PATH = "/root/.openclaw/workspace/data/ops.db"
LOG_FILE = "/tmp/poly_iran_scrape.log"
STATE_FILE = "/tmp/poly_iran_scrape_state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def fetch_gamma(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"Fetch error {url}: {e}")
        return None

def get_all_iran_events():
    """Fetch all Iran ceasefire events from Polymarket gamma API"""
    data = fetch_gamma("https://gamma-api.polymarket.com/events?slug=us-x-iran-ceasefire-by")
    if not data:
        return []
    events = data if isinstance(data, list) else [data]
    return events

def parse_markets(event):
    """Extract all sub-market data from an event"""
    markets = event.get("markets", [])
    slug = event.get("slug", "")
    title = event.get("title", "")
    result = []
    for m in markets:
        question = m.get("question", "")
        prices_raw = m.get("outcomePrices", "[]")
        if isinstance(prices_raw, str):
            prices = json.loads(prices_raw)
        else:
            prices = prices_raw
        if len(prices) < 2:
            continue
        # outcomePrices = [YES, NO] in dollars
        yes_price = float(prices[0])
        no_price = float(prices[1])
        best_bid = m.get("bestBid", "")
        best_ask = m.get("bestAsk", "")
        volume = float(m.get("volume", 0) or 0)
        outcome = m.get("outcomes", '["Yes","No"]')
        try:
            outcomes = json.loads(outcome)
        except:
            outcomes = ["Yes", "No"]
        
        # Determine which price is "Yes" and which is "No"
        # YES price is typically lower for ceasefire (YES = ceasefire happens)
        # But we store both explicitly
        result.append({
            "slug": slug,
            "question": question,
            "yes_price": yes_price,
            "no_price": no_price,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "volume": volume,
            "outcomes": outcomes,
            "title": title,
        })
    return result

def upsert_to_db(markets):
    """Insert or update market prices in ops.db"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    inserted = 0
    for m in markets:
        market_id = m["slug"]
        # Map question text to sub-market key
        q = m["question"]
        if "March 31" in q:
            sub_key = "iran_ceasefire_march31"
        elif "April 30" in q:
            sub_key = "iran_ceasefire_april30"
        elif "April 15" in q:
            sub_key = "iran_ceasefire_april15"
        elif "May 31" in q:
            sub_key = "iran_ceasefire_may31"
        elif "June 30" in q:
            sub_key = "iran_ceasefire_june30"
        elif "December 31" in q:
            sub_key = "iran_ceasefire_dec31"
        elif "April 7" in q:
            sub_key = "iran_ceasefire_april7"
        else:
            sub_key = market_id
        
        full_market_id = f"{market_id}|{sub_key}"
        
        cur.execute("""
            INSERT INTO market_prices (market_id, market_name, outcome, price, spread, volume, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            full_market_id,
            m["title"],
            "YES",
            m["yes_price"],
            abs(m["yes_price"] - m["no_price"]) if m["yes_price"] and m["no_price"] else None,
            m["volume"],
            "gamma_api"
        ))
        inserted += 1
        
        cur.execute("""
            INSERT INTO market_prices (market_id, market_name, outcome, price, spread, volume, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            full_market_id,
            m["title"],
            "NO",
            m["no_price"],
            abs(m["yes_price"] - m["no_price"]) if m["yes_price"] and m["no_price"] else None,
            m["volume"],
            "gamma_api"
        ))
        inserted += 1
    
    conn.commit()
    conn.close()
    return inserted

def main():
    log("=== Iran scraper v2 started (gamma API) ===")
    events = get_all_iran_events()
    if not events:
        log("ERROR: No Iran events found")
        return
    
    all_markets = []
    for event in events:
        markets = parse_markets(event)
        all_markets.extend(markets)
    
    if not all_markets:
        log("ERROR: No markets parsed")
        return
    
    inserted = upsert_to_db(all_markets)
    log(f"Inserted {inserted} records from {len(all_markets)} sub-markets")
    
    # Summary
    for m in all_markets:
        q = m["question"]
        if "March 31" in q:
            log(f"  [MARCH31] YES={m['yes_price']} NO={m['no_price']} vol=${m['volume']/1e6:.1f}M")
    
    # Save state
    state = {
        "ts": datetime.utcnow().isoformat(),
        "markets_count": len(all_markets),
        "main_volume": all_markets[0]["volume"] if all_markets else 0
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    
    log("=== Done ===")

if __name__ == "__main__":
    main()
