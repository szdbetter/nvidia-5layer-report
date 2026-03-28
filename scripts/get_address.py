import os
from pathlib import Path
from eth_account import Account


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


pk = load_secret("PRIVATE_KEY") or load_secret("RTC_WALLET_PRIVATE_KEY")
if not pk:
    raise RuntimeError("No private key found in env/config/.secrets//root/.openclaw/.env")
acc = Account.from_key(pk)
print(acc.address)
