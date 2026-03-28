import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
client = ClobClient("https://clob.polymarket.com", key=PRIVATE_KEY, chain_id=POLYGON)
client.set_api_creds(client.create_or_derive_api_creds())

# US x Iran ceasefire by March 31?
# NO token
token_no = "51938013536033607392847872760095315790110510345353215258271180769721415981927"
# YES token
token_yes = "5708561660601459805512817131601230493971589760294984590237789749933853841330"

def get_depth(tid, label):
    try:
        book = client.get_order_book(tid)
        print(f"[{label}] Best Bid: {book.bids[0].price if book.bids else 'N/A'} | Best Ask: {book.asks[0].price if book.asks else 'N/A'}")
    except:
        print(f"[{label}] No depth found.")

get_depth(token_yes, "YES")
get_depth(token_no, "NO")
