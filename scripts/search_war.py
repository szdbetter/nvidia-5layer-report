import requests
queries = ["Epic Fury", "Iran", "Israel", "Strike", "Attack"]
for q in queries:
    url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&q={q}"
    resp = requests.get(url)
    for m in resp.json():
        if "strike" in m['question'].lower() or "attack" in m['question'].lower() or "iran" in m['question'].lower() or "israel" in m['question'].lower():
            print(f"Q: {m['question']}")
            print(f"  Price: {m.get('lastTradePrice')}")
            print(f"  ID: {m.get('conditionId')}")
            print(f"  Tokens: {m.get('clobTokenIds')}")
