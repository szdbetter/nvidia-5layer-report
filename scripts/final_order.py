import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.clob_types import OrderArgs

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
client = ClobClient("https://clob.polymarket.com", key=PRIVATE_KEY, chain_id=POLYGON)
client.set_api_creds(client.create_or_derive_api_creds())

# US x Iran ceasefire by March 31? -> NO
token_id = "51938013536033607392847872760095315790110510345353215258271180769721415981927"

try:
    # Get quote
    book = client.get_order_book(token_id)
    price = float(book.asks[0].price) if book.asks else 0.55
    print(f"Current Ask for NO: {price}")
    
    # Place order for 1.5 USDC.e worth to be safe with balance
    size = 1.5 / price
    print(f"Buying {round(size, 2)} shares at {price}")
    
    signed_order = client.create_order(OrderArgs(
        price=price,
        size=round(size, 2),
        side="BUY",
        token_id=token_id
    ))
    resp = client.post_order(signed_order)
    print(f"SUCCESS: {resp}")
except Exception as e:
    print(f"FAILED: {e}")
