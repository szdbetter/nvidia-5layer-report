import os
from pathlib import Path
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from web3 import Web3

HOST = "https://clob.polymarket.com"
TOKEN_NO = "51938013536033607392847872760095315790110510345353215258271180769721415981927"
MARKET_SLUG = "us-x-iran-ceasefire-by"
MARKET_TITLE = "US x Iran ceasefire by March 31?"
WALLET_ADDRESS = "0xcD1862c43F7F276026AA1579eC2b8b9c02c10552"
WEIGHTED_ENTRY = 0.7216
POSITION_QTY = 6.52
CTF_ADDR = "0x4d97dcd97ec945f40cf65f87097ace5ea0476045"
USDC_ADDR = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
RPC_URL = "https://polygon.drpc.org"


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


def make_client():
    pk = load_secret("PRIVATE_KEY")
    if not pk:
        raise RuntimeError("No PRIVATE_KEY found")
    client = ClobClient(HOST, key=pk, chain_id=POLYGON)
    client.set_api_creds(client.create_or_derive_api_creds())
    return client


def get_orderbook_snapshot(client=None, token_id=TOKEN_NO):
    client = client or make_client()
    ob = client.get_order_book(token_id)
    best_bid = max([float(b.price) for b in ob.bids]) if ob.bids else 0.0
    best_ask = min([float(a.price) for a in ob.asks]) if ob.asks else 1.0
    mid = (best_bid + best_ask) / 2
    last = float(client.get_last_trade_price(token_id).get('price', 0) or 0)
    return {
        'best_bid': best_bid,
        'best_ask': best_ask,
        'mid': mid,
        'last': last,
    }


def get_wallet_state(address=WALLET_ADDRESS, token_id=TOKEN_NO):
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    erc20_abi = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]
    erc1155_abi = [{"constant": True, "inputs": [{"name": "account", "type": "address"}, {"name": "id", "type": "uint256"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}]

    usdc = w3.eth.contract(address=w3.to_checksum_address(USDC_ADDR), abi=erc20_abi)
    ctf = w3.eth.contract(address=w3.to_checksum_address(CTF_ADDR), abi=erc1155_abi)

    usdc_balance = usdc.functions.balanceOf(address).call() / 10**6
    no_balance = ctf.functions.balanceOf(address, int(token_id)).call() / 10**6
    return {
        'usdc_balance': usdc_balance,
        'no_balance': no_balance,
    }


def calc_pnl(current_price, qty, entry=WEIGHTED_ENTRY):
    pnl = (current_price - entry) * qty
    roi = ((current_price / entry) - 1) * 100 if entry else 0.0
    return {'pnl': pnl, 'roi': roi}
