#!/usr/bin/env python3
"""
Fiona → VPS 数据同步
将Fiona本地DB增量同步到VPS
运行环境: Fiona Mac
"""
import sqlite3
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# ─── 配置（从环境变量读取）───────────────────────────────
VPS_HOST = os.getenv('SM_VPS_HOST', 'root@your-vps-ip')
VPS_DB_PATH = os.getenv('SM_VPS_DB_PATH', '~/smart_money/smart_money.db')
FIONA_DB_PATH = os.path.expanduser("~/smart_money/smart_money.db")
SYNC_STATE_FILE = Path(os.path.expanduser("~/smart_money/.sync_state.json"))


def load_sync_state() -> dict:
    if SYNC_STATE_FILE.exists():
        return json.loads(SYNC_STATE_FILE.read_text())
    return {'last_sync': None, 'last_wallet_rowid': 0, 'last_profit_rowid': 0}


def save_sync_state(state: dict):
    SYNC_STATE_FILE.write_text(json.dumps(state, indent=2))


def export_delta(conn, state: dict) -> dict:
    """导出增量数据"""
    c = conn.cursor()
    
    # 增量钱包（按rowid）
    c.execute("""
        SELECT rowid, address, smart_score, total_realized_profit, tokens_profitable,
               win_rate, labels, is_bot, name, twitter, first_seen, last_active, status
        FROM wallets WHERE rowid > ?
        ORDER BY rowid
    """, (state.get('last_wallet_rowid', 0),))
    wallets = [dict(zip([d[0] for d in c.description], row)) for row in c.fetchall()]
    last_wallet_rowid = wallets[-1]['rowid'] if wallets else state.get('last_wallet_rowid', 0)
    
    # 更新的盈亏记录（按snapshot_at）
    since = state.get('last_sync') or '2000-01-01'
    c.execute("""
        SELECT wallet_address, token_address, token_symbol, realized_profit,
               unrealized_profit, cost_basis, profit_change, snapshot_at
        FROM wallet_token_profits WHERE snapshot_at > ?
        ORDER BY snapshot_at
    """, (since,))
    profits = [dict(zip([d[0] for d in c.description], row)) for row in c.fetchall()]
    
    # 代币
    c.execute("""
        SELECT address, symbol, name, chain, swap_count_1h, volume, market_cap, last_seen
        FROM tokens WHERE last_seen > ?
    """, (since,))
    tokens = [dict(zip([d[0] for d in c.description], row)) for row in c.fetchall()]
    
    return {
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'wallets': wallets,
        'profits': profits,
        'tokens': tokens,
        'last_wallet_rowid': last_wallet_rowid,
    }


def sync_to_vps(delta: dict) -> bool:
    """通过SSH将delta JSON传给VPS执行导入"""
    if not delta['wallets'] and not delta['profits'] and not delta['tokens']:
        print("✅ 无新数据，跳过同步")
        return True
    
    print(f"📤 同步: {len(delta['wallets'])}钱包 {len(delta['profits'])}盈亏记录 {len(delta['tokens'])}代币")
    
    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(delta, f)
        tmp_path = f.name
    
    vps_tmp = f"/tmp/sm_delta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        # SCP上传
        ret = subprocess.run(['scp', '-o', 'StrictHostKeyChecking=no', tmp_path, f"{VPS_HOST}:{vps_tmp}"],
                             capture_output=True, text=True, timeout=60)
        if ret.returncode != 0:
            print(f"❌ SCP失败: {ret.stderr}")
            return False
        
        # 远程执行导入
        import_script = f"""
python3 -c "
import sqlite3, json, os
data = json.load(open('{vps_tmp}'))
db = os.path.expanduser('{VPS_DB_PATH}')
os.makedirs(os.path.dirname(db), exist_ok=True)
conn = sqlite3.connect(db)
c = conn.cursor()

# 初始化表（幂等）
c.executescript('''
CREATE TABLE IF NOT EXISTS tokens (address TEXT PRIMARY KEY, symbol TEXT, name TEXT, chain TEXT DEFAULT \\'sol\\', discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, swap_count_1h INTEGER, volume REAL, market_cap REAL, last_seen TIMESTAMP);
CREATE TABLE IF NOT EXISTS wallets (address TEXT PRIMARY KEY, smart_score REAL DEFAULT 0, total_realized_profit REAL DEFAULT 0, tokens_profitable INTEGER DEFAULT 0, win_rate REAL DEFAULT 0, labels TEXT DEFAULT \\'[]\\', is_bot BOOLEAN DEFAULT FALSE, name TEXT, twitter TEXT, first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_active TIMESTAMP, status TEXT DEFAULT \\'candidate\\');
CREATE TABLE IF NOT EXISTS wallet_token_profits (wallet_address TEXT, token_address TEXT, token_symbol TEXT, realized_profit REAL DEFAULT 0, unrealized_profit REAL DEFAULT 0, cost_basis REAL DEFAULT 0, profit_change REAL DEFAULT 0, snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (wallet_address, token_address));
''')

for t in data.get('tokens', []):
    conn.execute(\\"INSERT OR REPLACE INTO tokens VALUES (:address,:symbol,:name,:chain,:swap_count_1h,:volume,:market_cap,:last_seen)\\", {{**t, 'chain': t.get('chain','sol'), 'discovered_at': None}})
for w in data.get('wallets', []):
    w.pop('rowid', None)
    conn.execute(\\"INSERT OR REPLACE INTO wallets (address,smart_score,total_realized_profit,tokens_profitable,win_rate,labels,is_bot,name,twitter,last_active,status) VALUES (:address,:smart_score,:total_realized_profit,:tokens_profitable,:win_rate,:labels,:is_bot,:name,:twitter,:last_active,:status)\\", w)
for p in data.get('profits', []):
    conn.execute(\\"INSERT OR REPLACE INTO wallet_token_profits VALUES (:wallet_address,:token_address,:token_symbol,:realized_profit,:unrealized_profit,:cost_basis,:profit_change,:snapshot_at)\\", p)

conn.commit()
conn.close()
import os; os.remove('{vps_tmp}')
wc=len(data['wallets']); pc=len(data['profits']); print('VPS导入: '+str(wc)+'钱包 '+str(pc)+'记录')"
"""
        ret = subprocess.run(['ssh', '-o', 'StrictHostKeyChecking=no', VPS_HOST, import_script],
                             capture_output=True, text=True, timeout=120)
        if ret.returncode != 0:
            print(f"❌ VPS导入失败: {ret.stderr}")
            return False
        print(ret.stdout.strip())
        return True
    
    finally:
        os.unlink(tmp_path)


def main():
    if not os.path.exists(FIONA_DB_PATH):
        print(f"❌ Fiona DB不存在: {FIONA_DB_PATH}")
        sys.exit(1)
    
    conn = sqlite3.connect(FIONA_DB_PATH)
    state = load_sync_state()
    
    delta = export_delta(conn, state)
    conn.close()
    
    ok = sync_to_vps(delta)
    
    if ok:
        state['last_sync'] = datetime.now(timezone.utc).isoformat()
        state['last_wallet_rowid'] = delta.get('last_wallet_rowid', state.get('last_wallet_rowid', 0))
        save_sync_state(state)
    
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
