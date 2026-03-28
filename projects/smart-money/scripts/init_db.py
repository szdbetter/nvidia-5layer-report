#!/usr/bin/env python3
"""
Smart Money DB - VPS SQLite初始化
路径: /root/smart_money/init_db.py
"""
import sqlite3
import os

DB_PATH = os.path.expanduser("~/smart_money/smart_money.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.executescript("""
-- 代币表
CREATE TABLE IF NOT EXISTS tokens (
    address TEXT PRIMARY KEY,
    symbol TEXT,
    name TEXT,
    chain TEXT DEFAULT 'sol',
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    swap_count_1h INTEGER,
    volume REAL,
    market_cap REAL,
    last_seen TIMESTAMP
);

-- 钱包表
CREATE TABLE IF NOT EXISTS wallets (
    address TEXT PRIMARY KEY,
    smart_score REAL DEFAULT 0,
    total_realized_profit REAL DEFAULT 0,
    tokens_profitable INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0,
    labels TEXT DEFAULT '[]',
    is_bot BOOLEAN DEFAULT FALSE,
    name TEXT,
    twitter TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP,
    status TEXT DEFAULT 'candidate'
);

-- 钱包-代币盈亏快照
CREATE TABLE IF NOT EXISTS wallet_token_profits (
    wallet_address TEXT,
    token_address TEXT,
    token_symbol TEXT,
    realized_profit REAL DEFAULT 0,
    unrealized_profit REAL DEFAULT 0,
    cost_basis REAL DEFAULT 0,
    profit_change REAL DEFAULT 0,
    snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (wallet_address, token_address)
);

-- 交易信号
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_address TEXT,
    token_address TEXT,
    token_symbol TEXT,
    action TEXT,
    amount_usd REAL,
    smart_score REAL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified BOOLEAN DEFAULT FALSE
);

-- 采集任务日志
CREATE TABLE IF NOT EXISTS crawl_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT,
    status TEXT,
    tokens_crawled INTEGER DEFAULT 0,
    wallets_found INTEGER DEFAULT 0,
    error TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP
);

-- 历史评分快照（用于趋势分析）
CREATE TABLE IF NOT EXISTS wallet_score_history (
    wallet_address TEXT,
    smart_score REAL,
    tokens_profitable INTEGER,
    total_profit REAL,
    snapshot_date DATE,
    PRIMARY KEY (wallet_address, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_wallets_score ON wallets(smart_score DESC);
CREATE INDEX IF NOT EXISTS idx_wallets_status ON wallets(status);
CREATE INDEX IF NOT EXISTS idx_wtp_wallet ON wallet_token_profits(wallet_address);
CREATE INDEX IF NOT EXISTS idx_signals_detected ON signals(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_notified ON signals(notified);
""")

conn.commit()
conn.close()
print(f"✅ DB初始化完成: {DB_PATH}")
