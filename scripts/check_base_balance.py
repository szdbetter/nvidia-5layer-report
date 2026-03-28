from web3 import Web3
import json

# Base RPC
RPC_URL = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

address = "0xcD1862c43F7F276026AA1579eC2b8b9c02c10552"

def check():
    if not w3.is_connected():
        print("Failed to connect to Base RPC")
        return

    # Native ETH balance
    balance_eth = w3.eth.get_balance(address)
    print(f"Base ETH Balance: {Web3.from_wei(balance_eth, 'ether')} ETH")

    # USDC on Base
    USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

    ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]')

    def get_token_balance(token_addr, name):
        contract = w3.eth.contract(address=w3.to_checksum_address(token_addr), abi=ERC20_ABI)
        balance = contract.functions.balanceOf(address).call()
        decimals = contract.functions.decimals().call()
        print(f"{name} Balance: {balance / (10**decimals)}")

    try:
        get_token_balance(USDC_BASE, "Base USDC")
    except Exception as e:
        print(f"Failed to check Base USDC: {e}")

check()
