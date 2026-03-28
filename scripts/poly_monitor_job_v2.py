"""
Polymarket Monitor Job v2 - DAL-integrated
Reads market data via CLOB API, writes to SQLite via DAL.
Sends Discord alerts only on threshold breach.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
sys.path.append(str(Path(__file__).resolve().parent.parent / 'data'))

from poly_runtime import (
    make_client, get_orderbook_snapshot, get_wallet_state,
    calc_pnl, POSITION_QTY, WEIGHTED_ENTRY, MARKET_SLUG, MARKET_TITLE, TOKEN_NO
)
from dal import log_price, log_alert

# Thresholds
TP1 = 0.85
SL1 = 0.40


def run_monitor():
    client = make_client()
    snap = get_orderbook_snapshot(client)
    mid = snap['mid']
    bid = snap['best_bid']
    ask = snap['best_ask']
    spread = ask - bid

    # Write price to DB
    log_price(
        market_id=MARKET_SLUG,
        outcome='NO',
        price=mid,
        spread=spread,
        volume=None,
        market_name=MARKET_TITLE,
        source='polymarket_clob'
    )

    # Check thresholds
    if mid >= TP1:
        msg = f"[TP1] NO mid ${mid:.3f} >= ${TP1}. Entry ${WEIGHTED_ENTRY}. Consider SELL {POSITION_QTY} shares."
        log_alert(msg, level='critical', source='poly_monitor')
        print(f"[ALERT] {msg}")
    elif mid <= SL1:
        msg = f"[SL] NO mid ${mid:.3f} <= ${SL1}. Consider exit."
        log_alert(msg, level='critical', source='poly_monitor')
        print(f"[ALERT] {msg}")
    else:
        pnl = calc_pnl(mid, POSITION_QTY)
        print(f"[OK] NO mid=${mid:.3f} | spread={spread:.3f} | PnL=${pnl['pnl']:.2f} ({pnl['roi']:.1f}%)")


if __name__ == "__main__":
    run_monitor()
