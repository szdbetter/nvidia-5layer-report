import requests
url = "https://gamma-api.polymarket.com/events?active=true&closed=false&q=Bitcoin%20Up%20or%20Down"
resp = requests.get(url)
events = resp.json()
for e in events:
    if "5m" in e['slug'] or "5-minute" in e['title'].lower():
        print(f"--- Event: {e['title']} ---")
        print(f"Slug: {e['slug']}")
        print(f"Description: {e.get('description')}")
        for m in e['markets']:
             print(f"  Q: {m['question']}")
             print(f"  ID: {m['conditionId']}")
             print(f"  Tokens: {m['clobTokenIds']}")
