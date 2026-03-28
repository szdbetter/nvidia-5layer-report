import os
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

# Using the provided private key
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HOST = "https://clob.polymarket.com"

client = ClobClient(HOST, key=PRIVATE_KEY, chain_id=POLYGON)

try:
    # This derives or creates API credentials. 
    # Note: If it's the first time, it might need to sign a message.
    creds = client.create_or_derive_api_creds()
    print("API Credentials successfully derived/created.")
    print(f"API Key: {creds.api_key}")
    # Don't print secret/passphrase for security, but verify they exist
    if creds.api_secret and creds.api_passphrase:
        print("API Secret and Passphrase generated.")
except Exception as e:
    print(f"Authentication failed: {e}")
