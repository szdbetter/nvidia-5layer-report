import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.clob_types import OrderArgs

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HOST = "https://clob.polymarket.com"

client = ClobClient(HOST, key=PRIVATE_KEY, chain_id=POLYGON)
client.set_api_creds(client.create_or_derive_api_creds())

# Attempt a tiny limit order at a very low price to see if it's accepted
# Token: Positive on Ethereum ETF Flows (just as a test)
token_id = "107907839032063680544714138349106971073540980824987497271537691352739861473939"

try:
    signed_order = client.create_order(OrderArgs(
        price=0.1,
        size=1, 
        side="BUY",
        token_id=token_id
    ))
    resp = client.post_order(signed_order)
    print(f"Post order response: {resp}")
except Exception as e:
    print(f"Order failed: {e}")
