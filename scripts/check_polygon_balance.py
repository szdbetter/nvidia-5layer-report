from web3 import Web3
import json

# Public RPC (Try multiple if one fails)
RPC_URL = "https://1rpc.io/matic"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

address = "0xcD1862c43F7F276026AA1579eC2b8b9c02c10552"

def check():
    if not w3.is_connected():
        print("Failed to connect to Polygon RPC")
        return

    # Native MATIC balance
    balance_matic = w3.eth.get_balance(address)
    print(f"MATIC Balance: {Web3.from_wei(balance_matic, 'ether')} MATIC")

    # USDC (Native)
    USDC_NATIVE = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
    # USDC (Bridged)
    USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

    ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]')

    def get_token_balance(token_addr, name):
        contract = w3.eth.contract(address=w3.to_checksum_address(token_addr), abi=ERC20_ABI)
        balance = contract.functions.balanceOf(address).call()
        decimals = contract.functions.decimals().call()
        print(f"{name} Balance: {balance / (10**decimals)}")

    try:
        get_token_balance(USDC_NATIVE, "Native USDC")
    except Exception as e:
        print(f"Failed to check Native USDC: {e}")

    try:
        get_token_balance(USDC_BRIDGED, "Bridged USDC")
    except Exception as e:
        print(f"Failed to check Bridged USDC: {e}")

check()
