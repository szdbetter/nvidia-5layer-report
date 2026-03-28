import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.clob_types import OrderArgs

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HOST = "https://clob.polymarket.com"

client = ClobClient(HOST, key=PRIVATE_KEY, chain_id=POLYGON)
client.set_api_creds(client.create_or_derive_api_creds())

# Market: Ethereum ETF Flows on March 2?
# Outcome: Positive
token_id = "107907839032063680544714138349106971073540980824987497271537691352739861473939"

price_resp = client.get_last_trade_price(token_id)
price = float(price_resp.get('price', 0.98))

# Try placing a  order
size = 1.0 / price

try:
    signed_order = client.create_order(OrderArgs(
        price=price,
        size=round(size, 2),
        side="BUY",
        token_id=token_id
    ))
    resp = client.post_order(signed_order)
    print(f"ORDER SUCCESS: {resp}")
except Exception as e:
    print(f"ORDER FAILED: {e}")
