#!/usr/bin/env python3
"""
Bitfinex USDT 后台监控守护进程
- 每 10 分钟拉取一次行情 + 借贷利率
- 写入 /tmp/bitfinex_status.json 供 Dashboard 读取
- 价格或利率超阈值时推送 Telegram
- 阈值从 /tmp/bitfinex_config.json 读取（用户可在 Dashboard 修改）
"""

import requests
import json
import time
import os
import logging
from datetime import datetime, timezone, timedelta

# ── 配置 ──────────────────────────────────────────────────────────────────────
STATUS_FILE  = "/tmp/bitfinex_status.json"
CONFIG_FILE  = "/tmp/bitfinex_config.json"
LOG_FILE     = "/tmp/bitfinex_daemon.log"
INTERVAL_SEC = 600  # 10 分钟
BJT = timezone(timedelta(hours=8))

DEFAULT_CONFIG = {
    "price_alert_above":  1.0002,   # USDT/USD 价格告警阈值
    "rate_alert_above":   0.00045,  # 日利率告警阈值 (0.045% = 年化约 16.4%)
    "telegram_token":     os.environ.get("TELEGRAM_BOT_TOKEN", ""),
    "telegram_chat_id":   os.environ.get("TELEGRAM_CHAT_ID", ""),
    "interval_sec":       600,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("bitfinex")

# ── 工具函数 ──────────────────────────────────────────────────────────────────
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
            # 补全缺失字段
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    # 写入默认配置
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    return dict(DEFAULT_CONFIG)


def fetch_spot():
    r = requests.get("https://api-pub.bitfinex.com/v2/ticker/tUSTUSD", timeout=10)
    r.raise_for_status()
    d = r.json()
    return {
        "bid": d[0], "ask": d[2], "last": d[6],
        "daily_change": d[4], "daily_chg_pct": round(d[5]*100, 4),
        "high": d[8], "low": d[9], "volume": d[7],
    }


def fetch_funding():
    r = requests.get("https://api-pub.bitfinex.com/v2/ticker/fUST", timeout=10)
    r.raise_for_status()
    d = r.json()
    frr      = d[0]
    ask_rate = d[4]
    last_rate= d[9]
    volume   = d[11]
    high     = d[12]
    low      = d[13]
    def ann(x): return round(x * 365 * 100, 4) if x else None
    return {
        "frr_daily":       frr,      "frr_annual_pct":  ann(frr),
        "ask_daily":       ask_rate, "ask_annual_pct":  ann(ask_rate),
        "last_daily":      last_rate,"last_annual_pct": ann(last_rate),
        "high_daily":      high,     "high_annual_pct": ann(high),
        "low_daily":       low,      "low_annual_pct":  ann(low),
        "volume":          volume,
    }


def send_telegram(token, chat_id, text):
    if not token or not chat_id:
        log.warning("Telegram 未配置，跳过推送")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        log.info("Telegram 推送成功")
    except Exception as e:
        log.error(f"Telegram 推送失败: {e}")


# ── 主循环 ────────────────────────────────────────────────────────────────────
def main():
    log.info("Bitfinex 守护进程启动")
    # 用于去重告警（每次价格超阈值只发一次，直到恢复）
    alerted_price   = False
    alerted_funding = False

    while True:
        cfg = load_config()
        now_bjt = datetime.now(BJT).strftime("%Y-%m-%d %H:%M:%S")
        status = {
            "updated_at": now_bjt,
            "updated_ts": int(time.time()),
            "spot": None,
            "funding": None,
            "alerts": [],
            "error": None,
        }

        try:
            spot    = fetch_spot()
            funding = fetch_funding()
            status["spot"]    = spot
            status["funding"] = funding

            alerts = []

            # 价格告警
            price_thresh = cfg["price_alert_above"]
            if spot["last"] > price_thresh:
                msg = (f"🚨 *Bitfinex USDT 脱锚告警*\n"
                       f"当前价格: `{spot['last']:.5f}`\n"
                       f"告警阈值: `>{price_thresh}`\n"
                       f"时间: {now_bjt} BJT")
                alerts.append({"type": "price", "msg": msg, "value": spot["last"]})
                if not alerted_price:
                    send_telegram(cfg["telegram_token"], cfg["telegram_chat_id"], msg)
                    alerted_price = True
            else:
                alerted_price = False

            # 借贷利率告警
            rate_thresh = cfg["rate_alert_above"]
            ask_rate = funding["ask_daily"]
            if ask_rate and ask_rate > rate_thresh:
                ann = round(ask_rate * 365 * 100, 2)
                msg = (f"📈 *Bitfinex USDT 借贷利率告警*\n"
                       f"当前借出利率: `{ask_rate:.8f}/日` ≈ `{ann}%/年`\n"
                       f"告警阈值: `>{rate_thresh}/日`\n"
                       f"时间: {now_bjt} BJT")
                alerts.append({"type": "funding", "msg": msg, "value": ask_rate})
                if not alerted_funding:
                    send_telegram(cfg["telegram_token"], cfg["telegram_chat_id"], msg)
                    alerted_funding = True
            else:
                alerted_funding = False

            status["alerts"] = alerts
            log.info(f"行情更新 price={spot['last']:.5f}  ask_rate={ask_rate:.8f}/日")

        except Exception as e:
            status["error"] = str(e)
            log.error(f"数据拉取失败: {e}")

        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)

        interval = cfg.get("interval_sec", INTERVAL_SEC)
        time.sleep(interval)


if __name__ == "__main__":
    main()
