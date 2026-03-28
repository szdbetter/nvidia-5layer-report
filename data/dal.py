"""
Ops DAL (Data Access Layer) - 统一数据写入接口
所有 Python worker 通过此模块写入 ops.db
时区：北京时间 UTC+8
"""
import sqlite3
import os
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.expanduser("~/.openclaw/workspace/data/ops.db")
BJT = timezone(timedelta(hours=8))

def _now():
    return datetime.now(BJT).strftime("%Y-%m-%d %H:%M:%S")

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
    return c

def log_price(market_id, outcome, price, spread=None, volume=None, market_name=None, source='polymarket'):
    c = _conn()
    c.execute(
        "INSERT INTO market_prices(market_id,market_name,outcome,price,spread,volume,source,ts) VALUES(?,?,?,?,?,?,?,?)",
        (market_id, market_name, outcome, price, spread, volume, source, _now())
    )
    c.commit(); c.close()

def log_signal(source, signal_type, content, confidence=None, impact=None, proof=None):
    c = _conn()
    c.execute(
        "INSERT INTO osint_signals(source,signal_type,content,confidence,impact,proof,ts) VALUES(?,?,?,?,?,?,?)",
        (source, signal_type, content, confidence, impact, proof, _now())
    )
    c.commit(); c.close()

def log_task(agent_name, task_type, task_desc=None, status='pending'):
    now = _now()
    c = _conn()
    cur = c.execute(
        "INSERT INTO agent_tasks(agent_name,task_type,task_desc,status,started_at,created_at) VALUES(?,?,?,?,?,?)",
        (agent_name, task_type, task_desc, status, now, now)
    )
    task_id = cur.lastrowid
    c.commit(); c.close()
    return task_id

def complete_task(task_id, status='done', result=None, proof=None, error=None):
    c = _conn()
    c.execute(
        "UPDATE agent_tasks SET status=?,result=?,proof=?,error=?,completed_at=? WHERE id=?",
        (status, result, proof, error, _now(), task_id)
    )
    c.commit(); c.close()

def log_order(market_id, side, outcome, price, size, order_type='limit', status='pending', tx_hash=None, order_id=None):
    c = _conn()
    c.execute(
        "INSERT INTO trade_orders(market_id,side,outcome,price,size,order_type,status,tx_hash,order_id,ts) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (market_id, side, outcome, price, size, order_type, status, tx_hash, order_id, _now())
    )
    c.commit(); c.close()

def log_alert(message, level='info', source=None):
    c = _conn()
    c.execute(
        "INSERT INTO alerts(level,source,message,ts) VALUES(?,?,?,?)",
        (level, source, message, _now())
    )
    c.commit(); c.close()
