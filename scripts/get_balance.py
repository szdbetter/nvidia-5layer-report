from web3 import Web3
# Polygon RPC
w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
balance = w3.eth.get_balance("0xcD1862c43F7F276026AA1579eC2b8b9c02c10552")
print(f"Polygon Balance (Wei): {balance}")
