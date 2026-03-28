#!/usr/bin/env python3
"""Polymarket 盘口实时价格 ticker - 每分钟更新一次"""
import json, urllib.request, os
from datetime import datetime, timezone

RESULT_FILE = "/tmp/poly_macro_result.json"
MARKETS = [
    {"slug": "us-x-iran-ceasefire-by-march-31", "key": "march31", "label": "3月31日停战"},
    {"slug": "us-x-iran-ceasefire-by-april-30-194", "key": "april30", "label": "4月30日停战"},
]

def fetch_market(slug):
    url = f"https://gamma-api.polymarket.com/markets?slug={slug}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=10).read())
    if data:
        m = data[0]
        prices = json.loads(m.get("outcomePrices", "[]"))
        return {
            "yes": round(float(prices[0]), 4) if prices else None,
            "no": round(float(prices[1]), 4) if len(prices) > 1 else None,
            "volume": round(float(m.get("volume", 0))),
            "url": f"https://polymarket.com/event/{m.get('slug', slug)}",
        }
    return None

def main():
    # 读取现有结果文件
    result = {}
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE) as f:
            result = json.load(f)

    # 更新 Polymarket 盘口
    pm = result.get("polymarket", {})
    for m in MARKETS:
        try:
            data = fetch_market(m["slug"])
            if data:
                pm[m["key"]] = data
        except Exception as e:
            pass  # 保留旧值

    result["polymarket"] = pm
    result["polymarket_updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    with open(RESULT_FILE, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
