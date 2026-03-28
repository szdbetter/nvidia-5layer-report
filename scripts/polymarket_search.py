from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

HOST = "https://clob.polymarket.com"
client = ClobClient(HOST, chain_id=POLYGON)

# Search for "Iran" or "Israel" or "US strike"
query = "Iran"
results = client.get_markets(next_cursor="") # This is basic list

# Better: use the gamma API or specific search if available
# But let's just filter the list for now
for m in results['data']:
    if "Iran" in m['question'] or "Israel" in m['question']:
        print(f"[{m['active']}] {m['question']} (ID: {m['condition_id']})")
