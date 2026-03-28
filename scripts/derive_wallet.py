import os
from eth_account import Account
import sys

# Enable mnemonic features
Account.enable_unaudited_hdwallet_features()

mnemonic = os.getenv("RTC_WALLET_MNEMONIC")
# Standard ETH path
path = "m/44'/60'/0'/0/0"

account = Account.from_mnemonic(mnemonic, account_path=path)
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
