import os
from web3 import Web3
import json

# RPC and Addresses
RPC_URL = "https://1rpc.io/matic"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

address = "0xcD1862c43F7F276026AA1579eC2b8b9c02c10552"
pk = os.getenv("PRIVATE_KEY")

USDC_NATIVE = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
CTF_EXCHANGE = "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e"

# Minimal ERC20 ABI for approval
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

def approve():
    if not w3.is_connected():
        print("Failed to connect to Polygon")
        return

    contract = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVE), abi=ERC20_ABI)
    
    # Approve a large amount for future convenience (or just the 0.5 for now)
    # Let's do 1000 USDC to avoid repeating this
    amount = 1000 * 10**6
    
    nonce = w3.eth.get_transaction_count(address)
    
    txn = contract.functions.approve(
        w3.to_checksum_address(CTF_EXCHANGE),
        amount
    ).build_transaction({
        'chainId': 137,
        'gas': 100000, # Approximate
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    })
    
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=pk)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Approval Tx Hash: {w3.to_hex(tx_hash)}")
    
    # Wait for receipt
    print("Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Status: {receipt['status']} (1 is success)")

approve()
