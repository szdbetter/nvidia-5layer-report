import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from poly_runtime import make_client, get_orderbook_snapshot

client = make_client()
snap = get_orderbook_snapshot(client)
print(f"Last trade price for 'No': {snap['last']}")
print(f"Best Ask: {snap['best_ask']}")
print(f"Best Bid: {snap['best_bid']}")
print(f"Mid: {snap['mid']}")
