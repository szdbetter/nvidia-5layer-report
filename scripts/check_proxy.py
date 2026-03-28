import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
client = ClobClient("https://clob.polymarket.com", key=PRIVATE_KEY, chain_id=POLYGON)

try:
    proxy_info = client.get_proxy_address()
    print(f"Proxy Address: {proxy_info}")
except Exception as e:
    print(f"No proxy found or error: {e}")

# Check if we can derive API creds (already done, but good to check status)
try:
    creds = client.get_api_credentials()
    print(f"API Key exists: {creds.api_key}")
except:
    print("No API creds found in local session.")
