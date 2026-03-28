#!/usr/bin/env python3
"""
Sync Fiona's ops.db market_prices to VPS ops.db via JSON dump.
Called with JSON array on stdin.
"""
import sys, json, sqlite3

DB_PATH = "/root/.openclaw/workspace/data/ops.db"

def sync(rows):
    c = sqlite3.connect(DB_PATH)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
    
    # Get last ts in VPS DB
    last = c.execute("SELECT MAX(ts) FROM market_prices").fetchone()[0]
    
    inserted = 0
    for r in rows:
        market_id, market_name, outcome, price, spread, volume, source, ts = r
        if last and ts <= last:
            continue
        c.execute(
            "INSERT INTO market_prices(market_id,market_name,outcome,price,spread,volume,source,ts) VALUES(?,?,?,?,?,?,?,?)",
            (market_id, market_name, outcome, price, spread, volume, source, ts)
        )
        inserted += 1
    
    c.commit()
    total = c.execute("SELECT COUNT(*) FROM market_prices").fetchone()[0]
    c.close()
    print(f"Inserted {inserted} new rows. Total: {total}")

if __name__ == "__main__":
    data = json.load(sys.stdin)
    sync(data)
