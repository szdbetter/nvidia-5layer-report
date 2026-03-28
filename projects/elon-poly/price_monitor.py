#!/usr/bin/env python3
"""
每30分钟抓取：
1. xtracker 推文实时累计数（+每日明细）
2. Polymarket 盘口各档位 bestBid/bestAsk/lastTrade
写入 live_prices.jsonl（追加）
"""
import requests, json, datetime, os, sys

LIVE_FILE = '/root/.openclaw/workspace/projects/elon-poly/live_prices.jsonl'
TRACKING_ID = "d861bacb-6108-45d6-9a14-47b9e58ea095"
EVENT_ID = 278377

def fetch():
    ts = datetime.datetime.utcnow().isoformat()

    # 推文数
    r1 = requests.get(f"https://xtracker.polymarket.com/api/trackings/{TRACKING_ID}?includeStats=true", timeout=10)
    stats = r1.json().get('data', {}).get('stats', {})
    tweet_total = stats.get('total', stats.get('cumulative', None))
    daily_raw = stats.get('daily', [])
    daily_agg = {}
    for h in daily_raw:
        dt = h.get('date','')[:10]
        daily_agg[dt] = daily_agg.get(dt, 0) + h.get('count', 0)

    # 盘口价格
    r2 = requests.get(f"https://gamma-api.polymarket.com/events/{EVENT_ID}", timeout=10)
    markets = r2.json().get('markets', [])
    prices = {}
    for m in markets:
        title = m.get('groupItemTitle', '').strip()
        prices[title] = {
            'bid': m.get('bestBid'),
            'ask': m.get('bestAsk'),
            'last': m.get('lastTradePrice'),
            'volume': m.get('volume')
        }

    row = {
        'ts': ts,
        'tweet_total': tweet_total,
        'tweet_daily': daily_agg,
        'prices': prices
    }

    with open(LIVE_FILE, 'a') as f:
        f.write(json.dumps(row) + '\n')

    print(f"[{ts}] tweets={tweet_total} | 档位={len(prices)}")
    # 打印最高流动性档位
    liquid = [(k, v) for k, v in prices.items() if v.get('last') and float(v['last']) > 0.01]
    liquid.sort(key=lambda x: -float(x[1]['last']))
    for bracket, p in liquid[:5]:
        print(f"  [{bracket}] ask={p['ask']} last={p['last']}")

if __name__ == '__main__':
    fetch()
