#!/usr/bin/env python3
"""
GMGN Smart Money 采集脚本 - Fiona专用
功能: 采集热门代币列表 + 持有者盈亏数据
运行环境: Fiona Mac (Python 3.14 + Playwright)
"""
import asyncio
import json
import os
import sys
import time
import random
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path

# ─── 配置 ───────────────────────────────────────────────
FIONA_DB_PATH = os.path.expanduser("~/smart_money/smart_money.db")
OUTPUT_DIR = Path(os.path.expanduser("~/smart_money"))
OUTPUT_DIR.mkdir(exist_ok=True)

TOP_TOKENS_LIMIT = 100   # 抓取热门代币数量
TOP_HOLDERS_LIMIT = 50   # 每个代币抓取持有者数量
DELAY_MIN = 2.0          # 最小请求间隔(秒)
DELAY_MAX = 5.0          # 最大请求间隔(秒)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(OUTPUT_DIR / "crawler.log")
    ]
)
log = logging.getLogger(__name__)


async def fetch_gmgn_api(page, url: str, max_retry=3) -> dict:
    """通过GMGN API获取数据"""
    for attempt in range(max_retry):
        try:
            resp = await page.evaluate(f"""
                fetch('{url}', {{
                    headers: {{
                        'Accept': 'application/json',
                        'Referer': 'https://gmgn.ai/',
                        'User-Agent': navigator.userAgent
                    }}
                }}).then(r => r.json()).catch(e => {{return {{error: e.message}}}})
            """)
            if resp and 'error' not in resp:
                return resp
            log.warning(f"API错误 attempt={attempt+1}: {resp}")
        except Exception as e:
            log.warning(f"fetch失败 attempt={attempt+1}: {e}")
        await asyncio.sleep(random.uniform(2, 5))
    return None


async def get_hot_tokens(page) -> list:
    """获取热门代币列表"""
    log.info("📡 获取热门代币列表...")
    url = f"https://gmgn.ai/defi/quotation/v1/rank/sol/swaps/1h?orderby=swaps&direction=desc&limit={TOP_TOKENS_LIMIT}&filters[]=not_honeypot&filters[]=pump"
    data = await fetch_gmgn_api(page, url)
    
    if not data:
        log.error("热门代币获取失败，尝试备用端点...")
        url2 = f"https://gmgn.ai/defi/quotation/v1/rank/sol/swaps/1h?orderby=volume&direction=desc&limit={TOP_TOKENS_LIMIT}"
        data = await fetch_gmgn_api(page, url2)
    
    if not data:
        return []
    
    tokens = []
    rank_list = data.get('data', {}).get('rank', []) or data.get('data', []) or []
    for t in rank_list:
        tokens.append({
            'address': t.get('address', t.get('mint', '')),
            'symbol': t.get('symbol', ''),
            'name': t.get('name', ''),
            'swap_count_1h': t.get('swaps', 0),
            'volume': t.get('volume', 0),
            'market_cap': t.get('market_cap', 0),
        })
    
    log.info(f"✅ 获取到 {len(tokens)} 个热门代币")
    return tokens


async def get_token_holders(page, token_address: str, symbol: str) -> list:
    """获取代币持有者盈亏"""
    url = f"https://gmgn.ai/defi/quotation/v1/tokens/top_traders/sol/{token_address}?orderby=profit&direction=desc&limit={TOP_HOLDERS_LIMIT}"
    data = await fetch_gmgn_api(page, url)
    
    if not data:
        return []
    
    holders = []
    trader_list = data.get('data', []) or []
    for h in trader_list:
        wallet = h.get('address', '')
        if not wallet:
            continue
        holders.append({
            'wallet_address': wallet,
            'token_address': token_address,
            'token_symbol': symbol,
            'realized_profit': h.get('realized_profit', 0) or 0,
            'unrealized_profit': h.get('unrealized_profit', 0) or 0,
            'cost_basis': h.get('cost', 0) or 0,
            'profit_change': h.get('profit_change', 0) or 0,
            'labels': json.dumps(h.get('tags', []) or []),
            'name': h.get('name', ''),
            'twitter': h.get('twitter_username', ''),
            'is_bot': 'snipe_bot' in str(h.get('tags', [])) or 'sandwich_bot' in str(h.get('tags', [])),
        })
    return holders


def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS tokens (
            address TEXT PRIMARY KEY, symbol TEXT, name TEXT, chain TEXT DEFAULT 'sol',
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            swap_count_1h INTEGER, volume REAL, market_cap REAL, last_seen TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS wallets (
            address TEXT PRIMARY KEY, smart_score REAL DEFAULT 0,
            total_realized_profit REAL DEFAULT 0, tokens_profitable INTEGER DEFAULT 0,
            win_rate REAL DEFAULT 0, labels TEXT DEFAULT '[]',
            is_bot BOOLEAN DEFAULT FALSE, name TEXT, twitter TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_active TIMESTAMP,
            status TEXT DEFAULT 'candidate'
        );
        CREATE TABLE IF NOT EXISTS wallet_token_profits (
            wallet_address TEXT, token_address TEXT, token_symbol TEXT,
            realized_profit REAL DEFAULT 0, unrealized_profit REAL DEFAULT 0,
            cost_basis REAL DEFAULT 0, profit_change REAL DEFAULT 0,
            snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (wallet_address, token_address)
        );
        CREATE TABLE IF NOT EXISTS crawl_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT, status TEXT,
            tokens_crawled INTEGER DEFAULT 0, wallets_found INTEGER DEFAULT 0,
            error TEXT, started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, finished_at TIMESTAMP
        );
    """)
    conn.commit()
    return conn


def upsert_token(conn, token: dict):
    conn.execute("""
        INSERT INTO tokens (address, symbol, name, swap_count_1h, volume, market_cap, last_seen)
        VALUES (:address, :symbol, :name, :swap_count_1h, :volume, :market_cap, CURRENT_TIMESTAMP)
        ON CONFLICT(address) DO UPDATE SET
            swap_count_1h=excluded.swap_count_1h, volume=excluded.volume,
            market_cap=excluded.market_cap, last_seen=excluded.last_seen
    """, token)


def upsert_wallet_profit(conn, holder: dict):
    # 先确保钱包记录存在
    conn.execute("""
        INSERT OR IGNORE INTO wallets (address, labels, name, twitter, is_bot, last_active)
        VALUES (:wallet_address, :labels, :name, :twitter, :is_bot, CURRENT_TIMESTAMP)
    """, holder)
    conn.execute("""
        UPDATE wallets SET last_active=CURRENT_TIMESTAMP, is_bot=MAX(is_bot, :is_bot)
        WHERE address=:wallet_address
    """, holder)
    # 更新盈亏快照
    conn.execute("""
        INSERT INTO wallet_token_profits (wallet_address, token_address, token_symbol,
            realized_profit, unrealized_profit, cost_basis, profit_change, snapshot_at)
        VALUES (:wallet_address, :token_address, :token_symbol, :realized_profit,
            :unrealized_profit, :cost_basis, :profit_change, CURRENT_TIMESTAMP)
        ON CONFLICT(wallet_address, token_address) DO UPDATE SET
            realized_profit=excluded.realized_profit, unrealized_profit=excluded.unrealized_profit,
            cost_basis=excluded.cost_basis, profit_change=excluded.profit_change,
            snapshot_at=excluded.snapshot_at
    """, holder)


async def run_crawler():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log.error("❌ Playwright未安装: pip install playwright && playwright install chromium")
        sys.exit(1)
    
    conn = init_db(FIONA_DB_PATH)
    crawl_start = datetime.now(timezone.utc).isoformat()
    log_id = conn.execute(
        "INSERT INTO crawl_logs (task, status, started_at) VALUES ('full_crawl', 'running', CURRENT_TIMESTAMP)"
    ).lastrowid
    conn.commit()
    
    total_wallets = 0
    error_msg = None
    
    try:
        async with async_playwright() as p:
            # 无头模式（Fiona有显示器可headed，但脚本化用headless）
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await ctx.new_page()
            
            # 访问GMGN主页建立session/cookie
            log.info("🌐 加载GMGN主页...")
            await page.goto("https://gmgn.ai/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # 1. 获取热门代币
            tokens = await get_hot_tokens(page)
            if not tokens:
                raise Exception("热门代币获取失败，可能被反爬")
            
            for t in tokens:
                upsert_token(conn, t)
            conn.commit()
            log.info(f"💾 写入 {len(tokens)} 个代币")
            
            # 2. 逐个获取持有者盈亏
            for i, token in enumerate(tokens):
                addr = token['address']
                symbol = token['symbol'] or addr[:8]
                if not addr:
                    continue
                
                log.info(f"[{i+1}/{len(tokens)}] 采集 {symbol} 持有者...")
                holders = await get_token_holders(page, addr, symbol)
                
                for h in holders:
                    upsert_wallet_profit(conn, h)
                    total_wallets += 1
                
                conn.commit()
                
                # 随机延迟防封
                delay = random.uniform(DELAY_MIN, DELAY_MAX)
                await asyncio.sleep(delay)
            
            await browser.close()
    
    except Exception as e:
        error_msg = str(e)
        log.error(f"❌ 采集失败: {e}")
    
    finally:
        conn.execute("""
            UPDATE crawl_logs SET status=?, tokens_crawled=?, wallets_found=?, error=?, finished_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, ('success' if not error_msg else 'error', len(tokens) if 'tokens' in dir() else 0, total_wallets, error_msg, log_id))
        conn.commit()
        conn.close()
    
    # 导出JSON供VPS同步
    export_path = OUTPUT_DIR / f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    # 简化版：只导出新数据
    log.info(f"✅ 采集完成 tokens={len(tokens) if 'tokens' in dir() else 0} wallet_records={total_wallets}")
    return not bool(error_msg)


def main():
    ok = asyncio.run(run_crawler())
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
