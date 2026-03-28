import requests
# Event slug: us-strikes-iran-by
url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&q=strikes%20Iran"
resp = requests.get(url)
for m in resp.json():
    print(f"Q: {m['question']}")
    print(f"  ID: {m['conditionId']}")
    print(f"  Price: {m.get('lastTradePrice')}")
    print(f"  Tokens: {m.get('clobTokenIds')}")
