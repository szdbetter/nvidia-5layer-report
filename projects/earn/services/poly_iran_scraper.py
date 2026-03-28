#!/usr/bin/env python3
"""
Polymarket Iran Markets Scraper v2
Uses HTML page scraping to extract embedded JSON with market prices.
No API key needed.
"""
import re, json, sqlite3, urllib.request
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/data/ops.db"
LOG_FILE = "/tmp/poly_iran_scraper.log"
SOURCE_NAME = "polymarket_direct"  # used by both scraper and consumers — must match exactly

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def fetch_event_page(slug):
    """Fetch a Polymarket event page and extract all market data from embedded JSON"""
    url = f"https://polymarket.com/event/{slug}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")
        
        # Extract outcomePrices arrays
        # Format: "outcomePrices":["0.165","0.835"]
        price_arrays = re.findall(r'"outcomePrices"\s*:\s*\[\s*["\']*([0-9.]+)["\']*\s*,\s*["\']*([0-9.]+)["\']*\s*\]', html)
        
        # Extract slug
        slug_data = re.findall(r'"slug"\s*:\s*"([^"]+)"', html)
        
        # Extract bestBid and bestAsk
        bids = re.findall(r'"bestBid"\s*:\s*([0-9.]+)', html)
        asks = re.findall(r'"bestAsk"\s*:\s*([0-9.]+)', html)
        
        # Extract question
        questions = re.findall(r'"question"\s*:\s*"([^"]{10,150})"', html)
        
        # Extract volume
        volumes = re.findall(r'"volume"\s*:\s*([0-9.]+)', html)
        
        # Extract closed status
        closed = re.findall(r'"closed"\s*:\s*(true|false)', html)
        
        # Extract markets array from JSON
        markets_match = re.search(r'"markets"\s*:\s*(\[.*?\])\s*,\s*"tags"', html, re.DOTALL)
        if markets_match:
            try:
                markets = json.loads(markets_match.group(1))
            except:
                markets = []
        else:
            markets = []
        
        return {
            "price_arrays": [(float(a), float(b)) for a, b in price_arrays],
            "slugs": slug_data,
            "questions": questions,
            "bids": [float(b) for b in bids],
            "asks": [float(a) for a in asks],
            "volumes": [float(v) for v in volumes],
            "closed": [c == "true" for c in closed],
            "markets": markets,
        }
    except Exception as e:
        log(f"Error fetching {slug}: {e}")
        return None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS market_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        market_id TEXT NOT NULL,
        market_name TEXT,
        outcome TEXT NOT NULL,
        price REAL NOT NULL,
        spread REAL,
        volume REAL,
        source TEXT DEFAULT 'polymarket_direct',
        ts DATETIME DEFAULT (datetime('now', '+8 hours'))
    )""")
    c.execute("""CREATE INDEX IF NOT EXISTS idx_prices_market_ts
                  ON market_prices(market_id, ts)""")
    conn.commit()
    conn.close()

def save_price(market_id, market_name, price, volume=0, spread=0):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"""INSERT INTO market_prices
                      (market_id, market_name, outcome, price, spread, volume, source, ts)
                      VALUES (?, ?, 'NO', ?, ?, ?, '{SOURCE_NAME}', datetime('now', '+8 hours'))""",
                   (market_id, market_name, price, spread, volume))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log(f"DB error: {e}")
        return False

def parse_markets_from_html(html, page_slug):
    """Parse the markets array from embedded JSON in HTML"""
    markets_data = []
    
    # Find the markets array
    m_arr = re.search(r'"markets"\s*:\s*(\[)', html)
    if m_arr:
        start = m_arr.end() - 1
        bracket_count = 0
        end = start
        for i, ch in enumerate(html[start:], start):
            if ch == '[':
                bracket_count += 1
            elif ch == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end = i + 1
                    break
        if end > start:
            try:
                markets_arr = json.loads(html[start:end])
                for m in markets_arr:
                    slug = m.get("slug", "")
                    question = m.get("question", "")
                    prices = m.get("outcomePrices", [])
                    closed = m.get("closed", False)
                    vol = m.get("volume", 0)
                    bid = m.get("bestBid", 0) or 0
                    ask = m.get("bestAsk", 0) or 0
                    
                    if len(prices) >= 2 and not closed:
                        no_price = float(prices[1])
                        spread = round(ask - bid, 4) if ask and bid else 0
                        markets_data.append({
                            "slug": slug,
                            "question": question,
                            "no_price": no_price,
                            "volume": float(vol) if vol else 0,
                            "spread": spread,
                            "best_bid": float(bid) if bid else None,
                            "best_ask": float(ask) if ask else None,
                        })
            except Exception as e:
                log(f"Markets array parse error: {e}")
    
    return markets_data

def main():
    log("=== Iran market scraper v2 started ===")
    init_db()
    
    # Primary: scrape the main event page which has all sub-markets
    data = fetch_event_page("us-x-iran-ceasefire-by")
    
    if data and data["markets"]:
        markets = data["markets"]
        log(f"Found {len(markets)} markets in embedded JSON")
        saved = 0
        for m in markets:
            slug = m.get("slug", "")
            question = m.get("question", "")
            prices = m.get("outcomePrices", [])
            closed = m.get("closed", False)
            vol = m.get("volume", 0)
            bid = m.get("bestBid") or 0
            ask = m.get("bestAsk") or 0
            
            if len(prices) >= 2 and not closed:
                no_price = float(prices[1])
                spread = round(float(ask) - float(bid), 4) if ask and bid else 0
                save_price(slug, question[:100], no_price, float(vol) if vol else 0, spread)
                log(f"  SAVED: {slug} NO={no_price:.3f} spread={spread:.3f} vol={float(vol) if vol else 0:,.0f}")
                saved += 1
            else:
                log(f"  SKIP: {slug} closed={closed} prices={prices}")
        
        log(f"Saved {saved} price records")
    else:
        log("No markets data found, trying price array parsing...")
        if data:
            price_arrays = data.get("price_arrays", [])
            slugs = data.get("slugs", [])
            log(f"Price arrays: {len(price_arrays)}, Slugs: {len(slugs)}")
            
            saved = 0
            for i, (yes_p, no_p) in enumerate(price_arrays[:10]):
                slug = slugs[i] if i < len(slugs) else f"unknown-{i}"
                if "iran" in slug.lower() or i < 5:  # first few are likely Iran
                    save_price(slug, f"Market {i}", no_p)
                    log(f"  SAVED alt: {slug} NO={no_p:.3f}")
                    saved += 1
            log(f"Saved {saved} alt records")
    
    log("=== Done ===")

if __name__ == "__main__":
    main()
