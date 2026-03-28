#!/usr/bin/env python3
"""Decrypt Chrome cookies on macOS using Keychain"""
import sqlite3, os, json, shutil, subprocess, sys

try:
    from Crypto.Cipher import AES
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pycryptodome', '-q'])
    from Crypto.Cipher import AES

def get_chrome_password():
    """Get Chrome Safe Storage password from macOS Keychain"""
    result = subprocess.run(
        ['security', 'find-generic-password', '-wa', 'Chrome Safe Storage'],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def decrypt_cookie(encrypted_value, password):
    """Decrypt Chrome cookie value"""
    try:
        if not encrypted_value or encrypted_value[:3] != b'v10':
            return encrypted_value.decode('utf-8', errors='ignore') if encrypted_value else ''
        
        # Derive key
        import hashlib
        key = hashlib.pbkdf2_hmac('sha1', password.encode(), b'saltysalt', 1003, dklen=16)
        
        # Decrypt
        iv = b' ' * 16
        payload = encrypted_value[3:]
        cipher = AES.new(key, AES.MODE_CBC, IV=iv)
        decrypted = cipher.decrypt(payload)
        
        # Remove padding
        pad_len = decrypted[-1]
        if isinstance(pad_len, int):
            decrypted = decrypted[:-pad_len]
        return decrypted.decode('utf-8', errors='ignore')
    except Exception as e:
        return f'DECRYPT_ERROR:{e}'

# Get password
password = get_chrome_password()
if not password:
    print("ERROR: Cannot get Keychain password (may need user approval)")
    sys.exit(1)
print(f"Got keychain password (len={len(password)})")

# Read cookies
cookie_path = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies')
tmp_path = '/tmp/xianyu_cookies_dec.db'
shutil.copy2(cookie_path, tmp_path)

conn = sqlite3.connect(tmp_path)
c = conn.cursor()
c.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%goofish%' OR host_key LIKE '%taobao%'")

result = {}
for host, name, enc_val in c.fetchall():
    val = decrypt_cookie(enc_val, password)
    result[name] = val
    print(f"{host}\t{name}\t{val[:80]}")

conn.close()

with open('/tmp/xianyu_decrypted_cookies.json', 'w') as f:
    json.dump(result, f)
print(f"\nSaved {len(result)} cookies to /tmp/xianyu_decrypted_cookies.json")
