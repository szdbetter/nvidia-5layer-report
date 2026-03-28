import requests
url = "https://gamma-api.polymarket.com/events?limit=5&active=true&closed=false&order=volume24hr&dir=desc"
resp = requests.get(url)
events = resp.json()
for e in events:
    if "btc-updown-5m" in e['slug']:
        print(f"Event: {e['title']}")
        print(f"Slug: {e['slug']}")
        print(f"Description: {e.get('description', 'No description')}")
        for m in e['markets']:
            print(f"  Market: {m['question']}")
            print(f"  Condition ID: {m['conditionId']}")
            print(f"  Tokens: {m['clobTokenIds']}")
            # rules are often in 'description' or a separate field
