import requests
# Search specifically for Iran
url = "https://gamma-api.polymarket.com/events?active=true&closed=false&q=Iran"
resp = requests.get(url)
events = resp.json()
for e in events:
    print(f"Event: {e['title']} | Vol: {e.get('volume', 0)} | Slug: {e['slug']}")
