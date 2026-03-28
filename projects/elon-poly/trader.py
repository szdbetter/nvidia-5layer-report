#!/usr/bin/env python3
"""
Elon Poly - Main Trader/Monitor Script
Runs every 2 minutes, monitors orderbook and auto-trades (dry_run=True by default)
"""

import os
import json
import time
import subprocess
import traceback
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv

load_dotenv('/root/.openclaw/.env')

# ─── CONFIG ────────────────────────────────────────────────────────────────────
GAMMA_EVENT_ID = 278377
XTRACKER_ID = "d861bacb-6108-45d6-9a14-47b9e58ea095"
EOA_WALLET = "0xcD1862c43F7F276026AA1579eC2b8b9c02c10552"
DISCORD_CHANNEL = "1480446033531240469"
DEADLINE_UTC = datetime(2026, 3, 27, 15, 59, tzinfo=timezone.utc)
DAY0_UTC = datetime(2026, 3, 22, 16, 0, tzinfo=timezone.utc)  # event start (approx)

PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = "/tmp/elon_trader_state.json"
PRICES_FILE = os.path.join(PROJ_DIR, "live_prices.jsonl")
HIST_FILE = os.path.join(PROJ_DIR, "historical_brackets.json")

dry_run = True  # SAFETY: set to False only for live trading
MAX_POSITIONS = 2
MAX_PER_BRACKET = 3.0   # USD
MIN_USDC = 2.0
EDGE_THRESHOLD = 0.12
DAY_ENTER = 5  # Day >= 5 (2026-03-26)

TOKEN_MAP = {
    "280-299": "26832123741726647346552340008883547500117595436210748802218915491448954443297",
    "300-319": "90645738681592007920791857038531312800371774535525054601497834518163839018936",
    "320-339": "12547537570294567682592266581780022308578210689316624477489481456823420966761",
    "340-359": "73712795699983855066686259772340490663241338961547814881655254416441442582954",
    "360-379": "7200026789453746703388655813494351095041529029673870442064146506887486572501",
    "380-399": "19129029159125180324000259892263123632565353973397097558019077031411883001062",
    "400-419": "16284020935514892022998451638073467942811611856826047163432808295515881580380",
}

# Track positions in-memory (persisted via state file)
_positions = {}  # bracket -> {"size": float, "avg_price": float}

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def now_utc():
    return datetime.now(timezone.utc)

def current_day():
    """Days elapsed since DAY0_UTC (Day 1 = first day)"""
    delta = now_utc() - DAY0_UTC
    return max(1, delta.days + 1)

def load_historical():
    try:
        with open(HIST_FILE) as f:
            return json.load(f)
    except Exception:
        return []

def get_xtracker_tweets():
    """Fetch cumulative tweet count from xtracker."""
    try:
        url = f"https://xtracker.polymarket.com/api/trackings/{XTRACKER_ID}?includeStats=true"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # xtracker.polymarket.com response: data.stats.total
            if "data" in data:
                d = data["data"]
                if isinstance(d, dict):
                    stats = d.get("stats", {})
                    if "total" in stats:
                        return int(stats["total"])
                    for key in ["count", "tweet_count", "total"]:
                        if key in d:
                            return int(d[key])
        return None
    except Exception as e:
        print(f"[WARN] xtracker fetch failed: {e}")
        return None

def get_gamma_orderbook():
    """Fetch market data from Gamma API for event 278377."""
    try:
        url = f"https://gamma-api.polymarket.com/events/{GAMMA_EVENT_ID}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        print(f"[WARN] gamma-api fetch failed: {e}")
        return None

def get_clob_orderbook(token_id):
    """Fetch orderbook from CLOB for a specific token."""
    try:
        url = f"https://clob.polymarket.com/book?token_id={token_id}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        print(f"[WARN] CLOB orderbook fetch failed for {token_id[:16]}...: {e}")
        return None

def get_best_ask(token_id):
    """Get best ask price from CLOB orderbook."""
    ob = get_clob_orderbook(token_id)
    if not ob:
        return None
    asks = ob.get("asks", [])
    if not asks:
        return None
    # asks sorted ascending by price
    try:
        prices = [float(a["price"]) for a in asks if float(a["size"]) > 0]
        return min(prices) if prices else None
    except Exception:
        return None

def get_usdc_balance():
    """Get USDC balance via py-clob-client."""
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
        pk = os.getenv('PRIVATE_KEY')
        client = ClobClient('https://clob.polymarket.com', key=pk, chain_id=137)
        creds = client.create_or_derive_api_creds()
        client = ClobClient('https://clob.polymarket.com', key=pk, chain_id=137, creds=creds)
        bal = client.get_balance_allowance(BalanceAllowanceParams(asset_type=AssetType.COLLATERAL))
        return int(bal['balance']) / 1e6
    except Exception as e:
        print(f"[WARN] USDC balance fetch failed: {e}")
        return None

# ─── MODEL ────────────────────────────────────────────────────────────────────

def compute_model_probability(bracket, cumulative_tweets, day):
    """
    Three-factor model:
    1. Historical conditional probability (from historical_brackets.json)
    2. Current rate momentum
    3. Regime (early/late in event)
    Returns P(bracket resolves YES)
    """
    hist = load_historical()

    # Factor 1: Historical base rate for this bracket
    bracket_wins = 0
    bracket_total = 0
    for event in hist:
        for b in event.get("brackets", []):
            bname = b.get("bracket", "")
            # Rough match: same bracket label
            if bname == bracket:
                bracket_total += 1
                if b.get("yes_price", 0) == 1.0:
                    bracket_wins += 1
    base_prob = bracket_wins / bracket_total if bracket_total > 0 else 0.14

    # Factor 2: Momentum - project final count from current rate
    if cumulative_tweets and day and day > 0:
        rate_per_day = cumulative_tweets / day
        total_days = (DEADLINE_UTC - DAY0_UTC).days
        projected_final = rate_per_day * total_days
    else:
        projected_final = None

    # Parse bracket bounds
    try:
        if bracket.startswith("<"):
            lo, hi = 0, int(bracket[1:]) - 1
        elif bracket.endswith("+"):
            lo, hi = int(bracket[:-1]), 9999
        else:
            parts = bracket.split("-")
            lo, hi = int(parts[0]), int(parts[1])
    except Exception:
        lo, hi = 0, 9999

    momentum_prob = base_prob
    if projected_final is not None:
        # Gaussian-like score: peak when projected falls in bracket
        mid = (lo + hi) / 2 if hi < 9999 else lo + 20
        spread = 30
        import math
        dist = abs(projected_final - mid)
        # Probability peaks at 0.85 when perfectly centered, falls off
        momentum_prob = 0.85 * math.exp(-0.5 * (dist / spread) ** 2)
        momentum_prob = max(0.03, min(0.92, momentum_prob))

    # Factor 3: Regime - late in event → trust momentum more
    days_remaining = max(1, (DEADLINE_UTC - now_utc()).days)
    total_event_days = (DEADLINE_UTC - DAY0_UTC).days
    elapsed_frac = 1 - (days_remaining / total_event_days)
    regime_weight = min(0.9, 0.3 + elapsed_frac * 0.6)

    # Blend
    p_model = (1 - regime_weight) * base_prob + regime_weight * momentum_prob
    return round(p_model, 4), projected_final

def send_discord_alert(msg):
    """Send Discord alert via openclaw CLI."""
    try:
        subprocess.run(
            ["openclaw", "message", "send",
             "--channel", "discord",
             "--target", DISCORD_CHANNEL,
             "--message", msg],
            timeout=15, capture_output=True
        )
        print(f"[ALERT] Discord sent: {msg[:80]}")
    except Exception as e:
        print(f"[WARN] Discord send failed: {e}")

def place_order(token_id, bracket, price, size_usdc):
    """Place a limit buy order (or dry-run)."""
    if dry_run:
        print(f"[DRY RUN] Would BUY {bracket}: size=${size_usdc:.2f} at {price:.3f} | token={token_id[:16]}...")
        return True
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import OrderArgs, OrderType
        pk = os.getenv('PRIVATE_KEY')
        client = ClobClient('https://clob.polymarket.com', key=pk, chain_id=137)
        creds = client.create_or_derive_api_creds()
        client = ClobClient('https://clob.polymarket.com', key=pk, chain_id=137, creds=creds)
        size = size_usdc / price  # shares
        order_args = OrderArgs(
            token_id=token_id,
            price=price,
            size=round(size, 2),
            side="BUY",
        )
        resp = client.create_and_post_order(order_args)
        print(f"[ORDER] {bracket} BUY placed: {resp}")
        return True
    except Exception as e:
        print(f"[ERROR] Order failed for {bracket}: {e}")
        return False

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────

def run_once():
    global _positions

    ts = now_utc().isoformat()
    day = current_day()
    print(f"\n{'='*60}")
    print(f"[{ts}] Day={day} | Elon Poly Trader Loop")

    # Load saved positions from state
    try:
        with open(STATE_FILE) as f:
            saved = json.load(f)
            _positions = saved.get("positions", {})
    except Exception:
        _positions = {}

    # 1. Get tweet count
    cumulative_tweets = get_xtracker_tweets()
    print(f"  Cumulative tweets: {cumulative_tweets}")

    # 2. Get USDC balance
    usdc_balance = get_usdc_balance()
    print(f"  USDC balance: {usdc_balance}")

    # 3. Get Gamma event for context
    gamma_data = get_gamma_orderbook()

    # 4. Build per-bracket analysis
    bracket_results = {}
    alert_msgs = []
    predicted_final = None

    active_positions = len(_positions)

    for bracket, token_id in TOKEN_MAP.items():
        try:
            best_ask = get_best_ask(token_id)
            p_model, proj = compute_model_probability(bracket, cumulative_tweets, day)
            if proj is not None:
                predicted_final = proj

            edge = round(p_model - (best_ask or 0.5), 4) if best_ask else None

            bracket_results[bracket] = {
                "token_id": token_id[:16] + "...",
                "best_ask": best_ask,
                "p_model": p_model,
                "edge": edge,
            }
            print(f"  [{bracket}] ask={best_ask} p_model={p_model} edge={edge}")

            # Entry signal
            if (edge is not None and edge > EDGE_THRESHOLD
                    and day >= DAY_ENTER
                    and bracket not in _positions
                    and active_positions < MAX_POSITIONS
                    and usdc_balance and usdc_balance > MIN_USDC
                    and best_ask is not None):

                size = min(MAX_PER_BRACKET, usdc_balance - 0.5)
                msg = (f"🎯 [ELON-POLY] ENTRY SIGNAL {bracket} | "
                       f"edge={edge:.1%} ask={best_ask:.3f} p={p_model:.3f} | "
                       f"size=${size:.2f} | Day={day}")
                alert_msgs.append(msg)
                print(f"  {msg}")

                ok = place_order(token_id, bracket, best_ask, size)
                if ok:
                    _positions[bracket] = {"size": size, "avg_price": best_ask}
                    active_positions += 1

        except Exception as e:
            print(f"  [ERROR] bracket {bracket}: {e}")
            traceback.print_exc()

    # 5. Write state
    state = {
        "ts": ts,
        "cumulative_tweets": cumulative_tweets,
        "day": day,
        "predicted_final": round(predicted_final, 1) if predicted_final else None,
        "positions": _positions,
        "usdc_balance": usdc_balance,
        "brackets": bracket_results,
        "ok": True,
        "alert": None,
        "dry_run": dry_run,
    }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[WARN] State write failed: {e}")

    # 6. Append to live_prices.jsonl
    try:
        with open(PRICES_FILE, "a") as f:
            f.write(json.dumps(state) + "\n")
    except Exception as e:
        print(f"[WARN] live_prices append failed: {e}")

    # 7. Send Discord alerts
    for msg in alert_msgs:
        send_discord_alert(msg)

    print(f"  Done. positions={list(_positions.keys())} alerts={len(alert_msgs)}")
    return state

def main():
    print(f"[TRADER] Starting Elon Poly trader. dry_run={dry_run}")
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[ERROR] Loop exception: {e}")
            traceback.print_exc()
            # Write error state
            try:
                with open(STATE_FILE, "w") as f:
                    json.dump({
                        "ts": now_utc().isoformat(),
                        "ok": False,
                        "alert": str(e),
                        "cumulative_tweets": None,
                        "day": current_day(),
                        "predicted_final": None,
                        "positions": _positions,
                        "usdc_balance": None,
                    }, f)
            except Exception:
                pass
        time.sleep(120)

if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        run_once()
    else:
        main()
