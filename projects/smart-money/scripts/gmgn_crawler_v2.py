#!/usr/bin/env python3
"""
GMGN Smart Money 采集脚本 v2 - 网络拦截模式
通过Playwright拦截XHR请求获取数据，绕过CloudFlare直接调用限制
运行环境: Fiona Mac (Python 3.9 + Playwright)
"""
import asyncio
import json
import os
import sys
import time
import random
import sqlite3
import logging
import math
from datetime import datetime, timezone
from pathlib import Path

# ─── 配置 ───────────────────────────────────────────────
FIONA_DB_PATH = os.path.expanduser("~/smart_money/smart_money.db")
OUTPUT_DIR = Path(os.path.expanduser("~/smart_money"))
OUTPUT_DIR.mkdir(exist_ok=True)

TOP_TOKENS_LIMIT = 100
TOP_HOLDERS_LIMIT = 50
PAGE_DELAY = (3, 7)  # 页面间延迟

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(OUTPUT_DIR / "crawler.log"))
    ]
)
log = logging.getLogger(__name__)


def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript("""
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


async def crawl_with_intercept():
    from playwright.async_api import async_playwright

    conn = init_db(FIONA_DB_PATH)
    log_id = conn.execute(
        "INSERT INTO crawl_logs (task, status) VALUES ('v2_intercept', 'running')"
    ).lastrowid
    conn.commit()

    intercepted_data = {}
    token_list = []
    total_wallet_records = 0
    error_msg = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # 拦截API响应
        async def handle_response(resp):
            url = resp.url
            if "gmgn.ai/defi/quotation" not in url:
                return
            try:
                body = await resp.body()
                data = json.loads(body)
                intercepted_data[url] = data
                if "rank" in url:
                    log.info(f"[拦截] 热门代币 {len(body)} bytes")
                elif "top_traders" in url or "holders" in url:
                    log.info(f"[拦截] 持有者 {url.split('/')[-2][:12]}... {len(body)} bytes")
            except Exception as e:
                pass

        page = await ctx.new_page()
        page.on("response", handle_response)

        # 1. 访问GMGN主页触发热门代币API
        log.info("访问GMGN主页...")
        await page.goto("https://gmgn.ai/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # 查找热门代币数据
        for url, data in intercepted_data.items():
            if "rank" in url:
                rank_data = data.get("data", {}).get("rank", []) or data.get("data", []) or []
                for t in rank_data:
                    token_list.append({
                        "address": t.get("address", t.get("mint", "")),
                        "symbol": t.get("symbol", ""),
                        "name": t.get("name", ""),
                        "swap_count_1h": t.get("swaps", 0),
                        "volume": t.get("volume", 0),
                        "market_cap": t.get("market_cap", t.get("mc", 0)),
                    })
                log.info(f"从拦截数据获取 {len(token_list)} 个热门代币")
                break

        if not token_list:
            # 手动触发热门代币请求
            log.info("手动触发热门代币请求...")
            await page.evaluate("""
                fetch('https://gmgn.ai/defi/quotation/v1/rank/sol/swaps/1h?orderby=swaps&direction=desc&limit=100&filters[]=not_honeypot', {
                    credentials: 'include',
                    headers: {'Referer': 'https://gmgn.ai/'}
                })
            """)
            await asyncio.sleep(3)

            for url, data in intercepted_data.items():
                if "rank" in url and not token_list:
                    rank_data = data.get("data", {}).get("rank", []) or []
                    for t in rank_data:
                        token_list.append({
                            "address": t.get("address", ""),
                            "symbol": t.get("symbol", ""),
                            "name": t.get("name", ""),
                            "swap_count_1h": t.get("swaps", 0),
                            "volume": t.get("volume", 0),
                            "market_cap": t.get("market_cap", t.get("mc", 0)),
                        })

        if not token_list:
            error_msg = "热门代币获取失败"
            log.error(error_msg)
            conn.execute("UPDATE crawl_logs SET status='error', error=?, finished_at=CURRENT_TIMESTAMP WHERE id=?",
                         (error_msg, log_id))
            conn.commit()
            await browser.close()
            return False

        # 写入代币
        for t in token_list[:TOP_TOKENS_LIMIT]:
            conn.execute("""
                INSERT OR REPLACE INTO tokens (address, symbol, name, swap_count_1h, volume, market_cap, last_seen)
                VALUES (:address, :symbol, :name, :swap_count_1h, :volume, :market_cap, CURRENT_TIMESTAMP)
            """, t)
        conn.commit()
        log.info(f"写入 {len(token_list)} 个代币")

        # 2. 逐个访问代币页面，触发持有者API
        for i, token in enumerate(token_list[:TOP_TOKENS_LIMIT]):
            addr = token["address"]
            symbol = token["symbol"] or addr[:8]
            if not addr:
                continue

            log.info(f"[{i+1}/{min(len(token_list), TOP_TOKENS_LIMIT)}] 访问 {symbol} 页面...")
            prev_count = len(intercepted_data)

            try:
                await page.goto(
                    f"https://gmgn.ai/sol/token/{addr}",
                    wait_until="domcontentloaded",
                    timeout=20000
                )
                await asyncio.sleep(random.uniform(*PAGE_DELAY))

                # 手动触发top_traders API
                await page.evaluate(f"""
                    fetch('https://gmgn.ai/defi/quotation/v1/tokens/top_traders/sol/{addr}?orderby=profit&direction=desc&limit={TOP_HOLDERS_LIMIT}', {{
                        credentials: 'include',
                        headers: {{'Referer': 'https://gmgn.ai/sol/token/{addr}'}}
                    }})
                """)
                await asyncio.sleep(2)

                # 从拦截数据中找该代币的持有者
                holders_found = 0
                for url, data in list(intercepted_data.items()):
                    if addr in url and ("top_traders" in url or "holders" in url):
                        trader_list = data.get("data", []) or []
                        for h in trader_list:
                            w_addr = h.get("address", "")
                            if not w_addr:
                                continue
                            is_bot = any(t in str(h.get("tags", [])) for t in ["snipe_bot", "sandwich_bot", "mev_bot"])
                            labels = json.dumps(h.get("tags", []))
                            
                            conn.execute("""
                                INSERT OR IGNORE INTO wallets (address, labels, name, twitter, is_bot, last_active)
                                VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)
                            """, (w_addr, labels, h.get("name", ""), h.get("twitter_username", ""), is_bot))
                            conn.execute("""
                                UPDATE wallets SET last_active=CURRENT_TIMESTAMP WHERE address=?
                            """, (w_addr,))
                            conn.execute("""
                                INSERT OR REPLACE INTO wallet_token_profits
                                (wallet_address, token_address, token_symbol, realized_profit,
                                 unrealized_profit, cost_basis, profit_change, snapshot_at)
                                VALUES (?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                            """, (w_addr, addr, symbol,
                                  h.get("realized_profit", 0) or 0,
                                  h.get("unrealized_profit", 0) or 0,
                                  h.get("cost", 0) or 0,
                                  h.get("profit_change", 0) or 0))
                            holders_found += 1
                            total_wallet_records += 1
                        
                        del intercepted_data[url]  # 清理已处理
                        break

                if holders_found > 0:
                    conn.commit()
                    log.info(f"  → {holders_found} 个持有者")
                else:
                    log.warning(f"  → 未获取到持有者数据")

            except Exception as e:
                log.warning(f"  → 跳过 {symbol}: {e}")
                continue

        await browser.close()

    # 运行评分
    log.info("运行SM评分...")
    try:
        run_scoring(conn)
    except Exception as e:
        log.warning(f"评分失败: {e}")

    conn.execute("""
        UPDATE crawl_logs SET status='success', tokens_crawled=?, wallets_found=?, finished_at=CURRENT_TIMESTAMP WHERE id=?
    """, (len(token_list), total_wallet_records, log_id))
    conn.commit()
    conn.close()

    log.info(f"✅ 采集完成: {len(token_list)} 代币, {total_wallet_records} 持有者记录")
    return True


def run_scoring(conn):
    """内嵌评分逻辑"""
    c = conn.cursor()
    c.execute("""
        SELECT wallet_address,
               COUNT(DISTINCT token_address) as total_tokens,
               SUM(CASE WHEN realized_profit > 0 THEN 1 ELSE 0 END) as profitable_tokens,
               SUM(realized_profit) as total_profit
        FROM wallet_token_profits GROUP BY wallet_address
    """)
    rows = c.fetchall()
    
    for wallet_addr, total, profitable, profit in rows:
        win_rate = profitable / total if total > 0 else 0
        score = min(profitable / 10, 1.0) * 30
        if profit and profit > 0:
            score += min(math.log10(max(profit, 1)) / 5, 1.0) * 25
        score += win_rate * 20 + 10
        
        c.execute("SELECT is_bot, labels FROM wallets WHERE address=?", (wallet_addr,))
        row = c.fetchone()
        if not row:
            continue
        is_bot, labels = row
        
        try:
            lbls = json.loads(labels or "[]")
        except:
            lbls = []
        
        for lbl in lbls:
            if str(lbl).lower() in {"kol", "axiom", "bullx", "photon"}:
                score += 3
            if str(lbl).lower() in {"snipe_bot", "sandwich_bot", "mev_bot"}:
                score -= 20
        
        score = max(0, min(100, score))
        status = "blacklisted" if is_bot else ("confirmed" if profitable >= 3 else "candidate")
        
        c.execute("""
            UPDATE wallets SET tokens_profitable=?, total_realized_profit=?, win_rate=?,
            smart_score=?, status=? WHERE address=?
        """, (profitable, profit or 0, win_rate, score, status, wallet_addr))
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM wallets WHERE status='confirmed'")
    confirmed = c.fetchone()[0]
    log.info(f"评分完成: {confirmed} 个确认SM")


def main():
    ok = asyncio.run(crawl_with_intercept())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
