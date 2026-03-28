import requests
# Search for active Middle East escalation markets
url = "https://gamma-api.polymarket.com/events?limit=20&active=true&closed=false&q=Iran"
resp = requests.get(url)
events = resp.json()

for event in events:
    print(f"Event: {event['title']} | Slug: {event['slug']}")
    for m in event['markets']:
        print(f"  Q: {m['question']} | Price: {m.get('lastTradePrice')}")
        print(f"  ID: {m.get('conditionId')} | Tokens: {m.get('clobTokenIds')}")
