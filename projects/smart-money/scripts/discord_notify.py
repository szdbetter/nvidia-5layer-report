#!/usr/bin/env python3
"""
Smart Money Discord通知
每日SM排行榜 + 实时信号推送
"""
import sqlite3
import json
import os
import sys
import requests
from datetime import datetime, timezone

DB_PATH = os.path.expanduser("~/smart_money/smart_money.db")
WEBHOOK_URL = os.getenv('SM_DISCORD_WEBHOOK', '')
CHANNEL_ID = os.getenv('SM_DISCORD_CHANNEL', '')


def send_webhook(content: str):
    if not WEBHOOK_URL:
        print("⚠️ SM_DISCORD_WEBHOOK未设置，跳过推送")
        return
    resp = requests.post(WEBHOOK_URL, json={'content': content}, timeout=10)
    if resp.status_code not in (200, 204):
        print(f"❌ Webhook失败: {resp.status_code} {resp.text}")


def daily_report(conn):
    """生成每日SM排行榜"""
    c = conn.cursor()
    
    # Top 10 SM
    c.execute("""
        SELECT address, smart_score, tokens_profitable, total_realized_profit, win_rate, labels, name
        FROM wallets
        WHERE status='confirmed' AND is_bot=FALSE
        ORDER BY smart_score DESC LIMIT 10
    """)
    top_sm = c.fetchall()
    
    # 统计
    c.execute("SELECT COUNT(*) FROM wallets WHERE status='confirmed'")
    total_confirmed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tokens")
    total_tokens = c.fetchone()[0]
    c.execute("SELECT MAX(finished_at) FROM crawl_logs WHERE status='success'")
    last_crawl = c.fetchone()[0] or 'N/A'
    
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    lines = [
        f"## 🧠 Smart Money 日报 — {now}",
        f"",
        f"📊 **数据概览**: {total_confirmed} SM确认 | {total_tokens} 代币追踪 | 最后采集: {last_crawl}",
        f"",
        f"### 🏆 Top 10 Smart Money",
        f"```",
        f"{'排名':<4} {'地址':^12} {'Score':>6} {'跨币':>4} {'利润':>10} {'胜率':>6} {'标签'}",
        f"{'─'*60}",
    ]
    
    for i, (addr, score, tokens_p, profit, wr, labels, name) in enumerate(top_sm, 1):
        label_str = ''
        try:
            lbls = json.loads(labels or '[]')
            label_str = ','.join(str(l) for l in lbls[:2])
        except:
            pass
        
        profit_str = f"${profit:,.0f}" if profit else "N/A"
        wr_str = f"{wr*100:.0f}%" if wr else "N/A"
        display = name or addr[:8] + '...'
        
        lines.append(f"{i:<4} {display:<12} {score:>6.1f} {tokens_p:>4} {profit_str:>10} {wr_str:>6} {label_str}")
    
    lines.append("```")
    lines.append(f"\n🔗 Dashboard: http://localhost:1980")
    
    return '\n'.join(lines)


def notify_unread_signals(conn) -> int:
    """推送未通知的信号"""
    c = conn.cursor()
    c.execute("""
        SELECT s.id, s.wallet_address, s.token_symbol, s.action, s.amount_usd,
               s.smart_score, s.detected_at, w.tokens_profitable, w.win_rate
        FROM signals s
        LEFT JOIN wallets w ON w.address = s.wallet_address
        WHERE s.notified=FALSE
        ORDER BY s.detected_at DESC LIMIT 10
    """)
    signals = c.fetchall()
    
    if not signals:
        return 0
    
    for sig in signals:
        sid, addr, symbol, action, amount, score, detected, tp, wr = sig
        action_emoji = "🟢买入" if action == 'buy' else "🔴卖出"
        wr_str = f"{wr*100:.0f}%" if wr else "?"
        amount_str = f"${amount:,.0f}" if amount else "?"
        
        msg = (f"⚡ **SM信号** | {action_emoji} `${symbol}`\n"
               f"地址: `{addr[:8]}...`  Score: **{score:.1f}**  跨{tp}币 胜率{wr_str}\n"
               f"金额: {amount_str}  时间: {detected}")
        
        send_webhook(msg)
        c.execute("UPDATE signals SET notified=TRUE WHERE id=?", (sid,))
    
    conn.commit()
    return len(signals)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'daily'
    
    if not os.path.exists(DB_PATH):
        print(f"❌ DB不存在: {DB_PATH}")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    
    if mode == 'daily':
        report = daily_report(conn)
        print(report)
        send_webhook(report)
    elif mode == 'signals':
        n = notify_unread_signals(conn)
        print(f"推送 {n} 条信号")
    
    conn.close()


if __name__ == '__main__':
    main()
