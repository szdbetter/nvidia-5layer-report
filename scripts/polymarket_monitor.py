import os
from pathlib import Path
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from web3 import Web3


def load_secret(key):
    val = os.environ.get(key)
    if val:
        return val
    candidates = [
        Path('config/.secrets'),
        Path.home()/'.openclaw'/'workspace'/'config'/'.secrets',
        Path('/root/.openclaw/.env'),
    ]
    for path in candidates:
        try:
            if not path.exists():
                continue
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
        except Exception:
            continue
    return None


def monitor():
    pk = load_secret("PRIVATE_KEY")
    if not pk:
        raise RuntimeError("No PRIVATE_KEY found")

    client = ClobClient("https://clob.polymarket.com", key=pk, chain_id=POLYGON)
    client.set_api_creds(client.create_or_derive_api_creds())

    # Position to track: US x Iran ceasefire by March 31? -> NO
    token_id = "51938013536033607392847872760095315790110510345353215258271180769721415981927"
    entry_price = 0.7216  # weighted cost from confirmed fills

    # 1. Get current price
    price_resp = client.get_last_trade_price(token_id)
    current_price = float(price_resp.get('price', 0))

    # 2. Get balance
    w3 = Web3(Web3.HTTPProvider('https://polygon.drpc.org'))
    addr = '0xcD1862c43F7F276026AA1579eC2b8b9c02c10552'
    ctf_addr = '0x4d97dcd97ec945f40cf65f87097ace5ea0476045'
    ctf_abi = [{"constant": True, "inputs": [{"name": "account", "type": "address"}, {"name": "id", "type": "uint256"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}]
    c_ctf = w3.eth.contract(address=w3.to_checksum_address(ctf_addr), abi=ctf_abi)
    balance = c_ctf.functions.balanceOf(addr, int(token_id)).call() / 10**6

    if balance > 0:
        pnl = (current_price - entry_price) * balance
        roi = ((current_price / entry_price) - 1) * 100
        print(f"--- Polymarket Position Update ---")
        print(f"Market: US x Iran ceasefire by March 31?")
        print(f"Side: NO | Qty: {balance}")
        print(f"Current Price: ${current_price} (Weighted Entry: ${entry_price})")
        print(f"Unrealized PnL: ${pnl:.4f} ({roi:.2f}%)")
    else:
        print("No active positions found.")


if __name__ == "__main__":
    monitor()
