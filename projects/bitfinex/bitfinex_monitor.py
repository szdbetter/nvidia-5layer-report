#!/usr/bin/env python3
"""
Bitfinex USDT/USD 汇率 + 借贷利率监控脚本
API Docs: https://docs.bitfinex.com/reference/rest-public-ticker
"""

import requests
import json
from datetime import datetime, timezone, timedelta

BASE_URL = "https://api-pub.bitfinex.com/v2"
BJT = timezone(timedelta(hours=8))


def get_usdt_usd_price():
    """获取 UST/USD 现货交易对行情 (tUSTUSD)"""
    url = f"{BASE_URL}/ticker/tUSTUSD"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    # [BID, BID_SIZE, ASK, ASK_SIZE, DAILY_CHANGE, DAILY_CHANGE_PERC, LAST_PRICE, VOLUME, HIGH, LOW]
    return {
        "bid":          data[0],
        "ask":          data[2],
        "last":         data[6],
        "daily_change": data[4],
        "daily_chg_pct": round(data[5] * 100, 4),
        "high":         data[8],
        "low":          data[9],
        "volume":       data[7],
    }


def get_usdt_funding_rate():
    """获取 UST 借贷市场利率 (fUST) — 日利率，年化需 x365"""
    url = f"{BASE_URL}/ticker/fUST"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    # Funding ticker: [FRR, BID, BID_PERIOD, BID_SIZE, ASK, ASK_PERIOD, ASK_SIZE,
    #                  DAILY_CHANGE, DAILY_CHANGE_PERC, LAST_RATE, LAST_PERIOD, VOLUME,
    #                  HIGH, LOW, ?, PLACEHOLDER, FRR_AMOUNT_AVAILABLE]
    frr        = data[0]   # Flash Return Rate (每日)
    ask_rate   = data[4]   # 当前最优借出利率 (每日)
    last_rate  = data[9]   # 最新成交利率 (每日)
    volume     = data[11]  # 成交量
    high       = data[12]  # 24h 最高利率
    low        = data[13]  # 24h 最低利率

    def to_annual(daily_rate):
        return round(daily_rate * 365 * 100, 4)

    return {
        "frr_daily":         frr,
        "frr_annual_pct":    to_annual(frr),
        "ask_daily":         ask_rate,
        "ask_annual_pct":    to_annual(ask_rate),
        "last_daily":        last_rate,
        "last_annual_pct":   to_annual(last_rate),
        "high_daily":        high,
        "high_annual_pct":   to_annual(high) if high else None,
        "low_daily":         low,
        "low_annual_pct":    to_annual(low) if low else None,
        "volume":            volume,
    }


def main():
    now = datetime.now(BJT).strftime("%Y-%m-%d %H:%M:%S BJT")
    print(f"\n{'='*50}")
    print(f"  Bitfinex USDT 监控  |  {now}")
    print(f"{'='*50}")

    # --- 现货汇率 ---
    try:
        spot = get_usdt_usd_price()
        print(f"\n📊 UST/USD 现货行情")
        print(f"  最新价:  {spot['last']:.5f}")
        print(f"  买一:    {spot['bid']:.5f}   卖一: {spot['ask']:.5f}")
        print(f"  24h 涨跌: {spot['daily_change']:+.5f}  ({spot['daily_chg_pct']:+.4f}%)")
        print(f"  24h 高:  {spot['high']:.5f}   低: {spot['low']:.5f}")
        print(f"  24h 成交量: {spot['volume']:,.2f} UST")
    except Exception as e:
        print(f"❌ 现货行情获取失败: {e}")

    # --- 借贷利率 ---
    try:
        fr = get_usdt_funding_rate()
        print(f"\n💰 UST 借贷市场利率 (fUST)")
        print(f"  FRR (闪回率):      {fr['frr_daily']:.8f}/日  ≈ {fr['frr_annual_pct']:.2f}%/年")
        print(f"  最优借出价 (Ask):  {fr['ask_daily']:.8f}/日  ≈ {fr['ask_annual_pct']:.2f}%/年")
        print(f"  最新成交利率:      {fr['last_daily']:.8f}/日  ≈ {fr['last_annual_pct']:.2f}%/年")
        if fr['high_annual_pct']:
            print(f"  24h 最高:          {fr['high_daily']:.8f}/日  ≈ {fr['high_annual_pct']:.2f}%/年")
        if fr['low_annual_pct']:
            print(f"  24h 最低:          {fr['low_daily']:.8f}/日  ≈ {fr['low_annual_pct']:.2f}%/年")
        print(f"  24h 成交量:        {fr['volume']:,.2f} UST")
    except Exception as e:
        print(f"❌ 借贷利率获取失败: {e}")

    print(f"\n{'='*50}\n")

    # 输出 JSON 供外部程序消费
    result = {
        "timestamp": now,
        "spot": spot if 'spot' in locals() else None,
        "funding": fr if 'fr' in locals() else None,
    }
    return result


if __name__ == "__main__":
    result = main()
    # 可选：写入 JSON 文件
    # with open("/tmp/bitfinex_usdt.json", "w") as f:
    #     json.dump(result, f, indent=2)
