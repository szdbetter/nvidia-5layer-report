import os
from web3 import Web3
import json
import time

# Polygon RPC
RPC_URL = "https://polygon.drpc.org"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# User details
address = "0xcD1862c43F7F276026AA1579eC2b8b9c02c10552"
pk = os.getenv("PRIVATE_KEY")

# USDC.e and CTF Exchange
USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
CTF_EXCHANGE = "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e"

# ABI for approve
ERC20_ABI = [{"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]

def approve():
    if not w3.is_connected():
        print("Failed to connect")
        return

    usdc_contract = w3.eth.contract(address=w3.to_checksum_address(USDC_E), abi=ERC20_ABI)
    
    amount = 1000 * 10**6 # 1000 USDC.e
    
    print("Approving USDC.e for Polymarket...")
    nonce = w3.eth.get_transaction_count(address)
    spender = w3.to_checksum_address(CTF_EXCHANGE)
    txn = usdc_contract.functions.approve(spender, amount).build_transaction({
        'chainId': 137,
        'gas': 100000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    })
    
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=pk)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Approval Tx Hash: {tx_hash.hex()}")

approve()
