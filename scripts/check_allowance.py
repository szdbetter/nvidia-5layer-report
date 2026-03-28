from web3 import Web3
import json

RPC_URL = "https://polygon.drpc.org"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

address = "0xcD1862c43F7F276026AA1579eC2b8b9c02c10552"
USDC_NATIVE = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
CTF_EXCHANGE = "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e"

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

def check():
    if not w3.is_connected():
        print("Failed")
        return
    contract = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVE), abi=ERC20_ABI)
    allowance = contract.functions.allowance(address, w3.to_checksum_address(CTF_EXCHANGE)).call()
    print(f"Allowance: {allowance / 10**6} USDC")

check()
