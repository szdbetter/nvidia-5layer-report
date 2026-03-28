import requests
# Get markets for the Iran event
url = "https://gamma-api.polymarket.com/events?slug=us-strikes-iran-by"
resp = requests.get(url)
data = resp.json()

if data:
    for m in data[0]['markets']:
        # Filter for active and relatively high liq
        if m.get('active'):
            print(f"Q: {m['question']}")
            print(f"  Condition ID: {m['conditionId']}")
            print(f"  CLOB IDs: {m['clobTokenIds']}")
            print(f"  Price: {m.get('lastTradePrice')}")
