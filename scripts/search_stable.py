import requests
url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&q=USDT"
resp = requests.get(url)
for m in resp.json():
    print(f"Q: {m['question']}")
    print(f"  Price: {m.get('lastTradePrice')}")
    print(f"  Tokens: {m.get('clobTokenIds')}")
