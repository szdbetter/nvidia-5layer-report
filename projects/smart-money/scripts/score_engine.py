#!/usr/bin/env python3
"""
SM评分引擎 - VPS端
计算Smart Score并更新wallets表
可定时运行: 每小时跑一次
"""
import sqlite3
import json
import os
import math
from datetime import datetime, timezone

DB_PATH = os.path.expanduser("~/smart_money/smart_money.db")


def compute_smart_score(wallet_data: dict) -> float:
    """
    评分公式（满分100）:
    - 跨币盈利数 (30%) — tokens_profitable / max归一化
    - 累计已实现盈利 (25%) — log scale
    - 胜率 (20%) — profitable / total tokens
    - 活跃度 (15%) — 最近active时间
    - 标签信誉 (10%) — 优质标签加分
    """
    score = 0.0
    
    # 1. 跨币盈利数 (30分)
    tp = wallet_data.get('tokens_profitable', 0)
    cross_score = min(tp / 10, 1.0) * 30  # 10个币=满分
    score += cross_score
    
    # 2. 累计利润 (25分)
    profit = wallet_data.get('total_realized_profit', 0)
    if profit > 0:
        # log scale: $1K=10分, $10K=17分, $100K=25分
        profit_score = min(math.log10(max(profit, 1)) / 5, 1.0) * 25
        score += profit_score
    
    # 3. 胜率 (20分)
    win_rate = wallet_data.get('win_rate', 0)
    score += win_rate * 20
    
    # 4. 活跃度 (15分) — 简化：有last_active就给10分基础分
    if wallet_data.get('last_active'):
        score += 10
    
    # 5. 标签信誉 (10分)
    labels = wallet_data.get('labels', '[]')
    if isinstance(labels, str):
        try:
            labels = json.loads(labels)
        except:
            labels = []
    
    good_labels = {'kol', 'axiom', 'bullx', 'photon', 'insider'}
    bad_labels = {'snipe_bot', 'sandwich_bot', 'mev_bot', 'bundle_bot'}
    
    for lbl in labels:
        lbl_lower = str(lbl).lower()
        if lbl_lower in good_labels:
            score += 3
        if lbl_lower in bad_labels:
            score -= 20  # 直接降权
    
    return max(0.0, min(100.0, score))


def update_wallet_stats(conn):
    """基于wallet_token_profits更新wallet统计"""
    c = conn.cursor()
    
    # 计算每个钱包的盈利统计
    c.execute("""
        SELECT
            wallet_address,
            COUNT(DISTINCT token_address) as total_tokens,
            SUM(CASE WHEN realized_profit > 0 THEN 1 ELSE 0 END) as profitable_tokens,
            SUM(realized_profit) as total_profit
        FROM wallet_token_profits
        GROUP BY wallet_address
    """)
    
    rows = c.fetchall()
    updated = 0
    
    for wallet_addr, total, profitable, profit in rows:
        win_rate = profitable / total if total > 0 else 0
        
        # 获取标签和is_bot
        c.execute("SELECT labels, is_bot FROM wallets WHERE address=?", (wallet_addr,))
        row = c.fetchone()
        if not row:
            continue
        labels, is_bot = row
        
        wallet_data = {
            'tokens_profitable': profitable,
            'total_realized_profit': profit or 0,
            'win_rate': win_rate,
            'labels': labels,
            'last_active': True,
        }
        
        score = compute_smart_score(wallet_data)
        
        # Bot直接降为blacklisted
        status = 'blacklisted' if is_bot else (
            'confirmed' if profitable >= 3 else 'candidate'
        )
        
        c.execute("""
            UPDATE wallets SET
                tokens_profitable=?, total_realized_profit=?, win_rate=?,
                smart_score=?, status=?, last_active=CURRENT_TIMESTAMP
            WHERE address=?
        """, (profitable, profit or 0, win_rate, score, status, wallet_addr))
        updated += 1
    
    conn.commit()
    print(f"✅ 评分更新完成: {updated} 个钱包")
    return updated


def get_top_sm(conn, limit=20) -> list:
    """获取Top SM排行榜"""
    c = conn.cursor()
    c.execute("""
        SELECT address, smart_score, tokens_profitable, total_realized_profit,
               win_rate, labels, name, last_active, status
        FROM wallets
        WHERE status='confirmed' AND is_bot=FALSE
        ORDER BY smart_score DESC
        LIMIT ?
    """, (limit,))
    
    cols = ['address', 'smart_score', 'tokens_profitable', 'total_profit',
            'win_rate', 'labels', 'name', 'last_active', 'status']
    return [dict(zip(cols, row)) for row in c.fetchall()]


def get_stats(conn) -> dict:
    """获取数据库统计"""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM wallets WHERE status='confirmed'")
    confirmed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM wallets WHERE status='candidate'")
    candidate = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM wallets WHERE is_bot=TRUE")
    bots = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tokens")
    tokens = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM wallet_token_profits")
    records = c.fetchone()[0]
    c.execute("SELECT MAX(finished_at) FROM crawl_logs WHERE status='success'")
    last_crawl = c.fetchone()[0]
    
    return {
        'confirmed_sm': confirmed,
        'candidates': candidate,
        'bots_filtered': bots,
        'tokens_tracked': tokens,
        'profit_records': records,
        'last_crawl': last_crawl,
    }


if __name__ == '__main__':
    conn = sqlite3.connect(DB_PATH)
    update_wallet_stats(conn)
    
    stats = get_stats(conn)
    print(f"\n📊 数据库统计:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    top = get_top_sm(conn, 10)
    print(f"\n🏆 Top 10 Smart Money:")
    for i, w in enumerate(top, 1):
        profit = f"${w['total_profit']:,.0f}" if w['total_profit'] else "N/A"
        print(f"  {i}. {w['address'][:8]}... score={w['smart_score']:.1f} 跨{w['tokens_profitable']}币 {profit}")
    
    conn.close()
