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

# Tokens
USDC_NATIVE = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# Uniswap V3 Router on Polygon
ROUTER_ADDR = "0xE592427A0AEce92De3Edee1F18E0157C05861564"

# ABI for approve and swap
ERC20_ABI = [{"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]
ROUTER_ABI = [{"inputs":[{"components":[{"internalType":"bytes","name":"path","type":"bytes"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMinimum","type":"uint256"}],"name":"params","type":"tuple"}],"name":"exactInput","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"payable","type":"function"}]

def swap():
    if not w3.is_connected():
        print("Failed to connect")
        return

    usdc_contract = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVE), abi=ERC20_ABI)
    router_contract = w3.eth.contract(address=w3.to_checksum_address(ROUTER_ADDR), abi=ROUTER_ABI)

    amount_in = int(2.0 * 10**6) # Swap ~2 USDC
    
    print("Approving Uniswap Router...")
    nonce = w3.eth.get_transaction_count(address)
    approve_tx = usdc_contract.functions.approve(ROUTER_ADDR, amount_in).build_transaction({
        'chainId': 137, 'gas': 100000, 'gasPrice': w3.eth.gas_price, 'nonce': nonce
    })
    signed_approve = w3.eth.account.sign_transaction(approve_tx, pk)
    w3.eth.send_raw_transaction(signed_approve.raw_transaction)
    time.sleep(10) # Wait for confirmation
    
    print("Executing Swap...")
    # Path: USDC -> USDC.e (0.01% fee or 0.05% fee)
    # USDC and USDC.e usually have a very low fee pool
    fee = 100 # 0.01%
    path = Web3.to_checksum_address(USDC_NATIVE) + fee.to_bytes(3, 'big').hex() + Web3.to_checksum_address(USDC_E)[2:]
    path_bytes = bytes.fromhex(path.replace('0x', ''))

    nonce = w3.eth.get_transaction_count(address)
    swap_tx = router_contract.functions.exactInput({
        "path": path_bytes,
        "recipient": address,
        "deadline": int(time.time()) + 600,
        "amountIn": amount_in,
        "amountOutMinimum": 0
    }).build_transaction({
        'chainId': 137, 'gas': 300000, 'gasPrice': w3.eth.gas_price, 'nonce': nonce
    })
    
    signed_swap = w3.eth.account.sign_transaction(swap_tx, pk)
    tx_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
    print(f"Swap Tx Hash: {tx_hash.hex()}")

swap()
