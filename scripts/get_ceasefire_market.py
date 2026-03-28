import requests
slug = "us-x-iran-ceasefire-by"
url = f"https://gamma-api.polymarket.com/events?slug={slug}"
resp = requests.get(url)
data = resp.json()

if data:
    for m in data[0]['markets']:
        if m.get('active'):
            print(f"Q: {m['question']}")
            print(f"  Condition ID: {m['conditionId']}")
            print(f"  CLOB IDs: {m['clobTokenIds']}")
            print(f"  Price: {m.get('lastTradePrice')}")
            print(f"  Outcomes: {m['outcomes']}")
