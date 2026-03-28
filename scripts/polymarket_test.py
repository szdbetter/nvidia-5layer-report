from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

# Public CLOB API
HOST = "https://clob.polymarket.com"

client = ClobClient(HOST, chain_id=POLYGON)

# Fetch some markets
sampling = client.get_markets()
print(f"Fetched {len(sampling['data'])} markets.")

# Display top 5 markets
for m in sampling['data'][:5]:
    print(f"- {m['question']} (ID: {m['condition_id']})")
