import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from poly_runtime import make_client, get_orderbook_snapshot, get_wallet_state, calc_pnl, WEIGHTED_ENTRY

client = make_client()
snap = get_orderbook_snapshot(client)
wallet = get_wallet_state()
stats = calc_pnl(snap['last'], wallet['no_balance'], WEIGHTED_ENTRY)

print(f"Current NO Price: {snap['last']}")
print(f"Best Bid: {snap['best_bid']}")
print(f"Best Ask: {snap['best_ask']}")
print(f"Mid Price: {snap['mid']}")
print(f"USDC.e Balance: {wallet['usdc_balance']}")
print(f"NO Token Balance: {wallet['no_balance']}")
print(f"Weighted Entry: {WEIGHTED_ENTRY}")
print(f"Estimated Unrealized PnL: {stats['pnl']} USDC")
print(f"Estimated ROI: {stats['roi']}%")
