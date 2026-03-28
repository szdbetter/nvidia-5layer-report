import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HOST = "https://clob.polymarket.com"

client = ClobClient(HOST, key=PRIVATE_KEY, chain_id=POLYGON)
client.set_api_creds(client.create_or_derive_api_creds())

token_id = "107907839032063680544714138349106971073540980824987497271537691352739861473939"

price = client.get_last_trade_price(token_id)
print(f"Last trade price for 'Positive': {price.get('price')}")

book = client.get_order_book(token_id)
if book.asks:
    print(f"Best Ask: {book.asks[0].price}")
if book.bids:
    print(f"Best Bid: {book.bids[0].price}")
