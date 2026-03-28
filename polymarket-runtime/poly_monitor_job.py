import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from poly_runtime import make_client, get_orderbook_snapshot, POSITION_QTY, WEIGHTED_ENTRY


def run_monitor():
    print("[Poly Monitor] Waking up to check positions...")
    client = make_client()
    snap = get_orderbook_snapshot(client)
    current_price = snap['mid']

    print(f"[Poly Monitor] Current Market Mid-Price: ${current_price:.3f} (Weighted Entry: ${WEIGHTED_ENTRY})")

    if current_price >= 0.85:
        print(f"[ALERT] Take Profit 1 Triggered! Price {current_price} >= 0.85. Consider SELL on {POSITION_QTY} shares.")
    elif current_price <= 0.40:
        print(f"[ALERT] Stop Loss Triggered! Price {current_price} <= 0.40. Consider exit.")
    else:
        print("[Poly Monitor] Price stable. No risk thresholds breached. Sleeping until next cycle.")


if __name__ == "__main__":
    run_monitor()
