import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.clob_types import OrderArgs

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HOST = "https://clob.polymarket.com"

client = ClobClient(HOST, key=PRIVATE_KEY, chain_id=POLYGON)
client.set_api_creds(client.create_or_derive_api_creds())

# Market: US x Iran ceasefire by March 31?
# Outcome: No
token_id = "51938013536033607392847872760095315790110510345353215258271180769721415981927"

# Get current price for NO
price_resp = client.get_last_trade_price(token_id)
price = float(price_resp.get('price', 0.54)) # If Yes is 0.46, No should be ~0.54

print(f"Targeting NO at price {price}")

# Order 1 USDC worth
size = 1.0 / price

try:
    signed_order = client.create_order(OrderArgs(
        price=price,
        size=round(size, 2),
        side="BUY",
        token_id=token_id
    ))
    resp = client.post_order(signed_order)
    print(f"TRADE SUCCESS: {resp}")
except Exception as e:
    print(f"TRADE FAILED: {e}")
