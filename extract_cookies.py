#!/usr/bin/env python3
import sqlite3, os, json, shutil

cookie_path = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies')
tmp_path = '/tmp/xianyu_cookies.db'
shutil.copy2(cookie_path, tmp_path)

conn = sqlite3.connect(tmp_path)
c = conn.cursor()
c.execute("SELECT host_key, name, value FROM cookies WHERE host_key LIKE '%goofish%' OR host_key LIKE '%taobao%' OR host_key LIKE '%aliyuncs%'")
cookies = {}
for host, name, value in c.fetchall():
    cookies[name] = value
    print(f"{host}\t{name}\t{value[:50] if value else 'ENCRYPTED'}")
conn.close()

with open('/tmp/xianyu_cookies.json', 'w') as f:
    json.dump(cookies, f)
print("done, saved to /tmp/xianyu_cookies.json")
