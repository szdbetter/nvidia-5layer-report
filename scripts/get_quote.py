import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
import json

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
client = ClobClient("https://clob.polymarket.com", key=PRIVATE_KEY, chain_id=POLYGON)
client.set_api_creds(client.create_or_derive_api_creds())

# March 31 strike YES token
token_id = "114073431155826730926052468626599502581519892859155799641358176120253844422606"

try:
    book = client.get_order_book(token_id)
    print(f"Bids: {book.bids[0].price if book.bids else 'N/A'}")
    print(f"Asks: {book.asks[0].price if book.asks else 'N/A'}")
except Exception as e:
    print(f"Error: {e}")
