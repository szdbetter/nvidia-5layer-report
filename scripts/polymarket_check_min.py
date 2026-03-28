import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

# Using the provided private key
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HOST = "https://clob.polymarket.com"

client = ClobClient(HOST, key=PRIVATE_KEY, chain_id=POLYGON)
client.set_api_creds(client.create_or_derive_api_creds())

# Get a popular market to test
# "Will Ali Khamenei remain Supreme Leader of Iran through June 30, 2023?" (Actually this might be old)
# Let's search for current ones.
markets = client.get_markets()
for m in markets['data']:
    if m['active']:
        print(f"Market: {m['question']}")
        print(f"Token ID (Yes): {m['tokens'][0]['token_id']}")
        break
