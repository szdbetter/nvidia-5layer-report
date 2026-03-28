import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.clob_types import OrderArgs

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HOST = "https://clob.polymarket.com"

client = ClobClient(HOST, key=PRIVATE_KEY, chain_id=POLYGON)
client.set_api_creds(client.create_or_derive_api_creds())

# Market: Will India’s Unemployment Rate increase in February? (More liquid)
# Outcome: Yes
token_id = "56145484516268883335411321573203112200573339087717431532774952804593913334366"

# Get current price
price_resp = client.get_last_trade_price(token_id)
price = float(price_resp.get('price', 0.87))

# Aim for a small amount: 0.2 USDC worth of shares
size = 0.2 / price

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
