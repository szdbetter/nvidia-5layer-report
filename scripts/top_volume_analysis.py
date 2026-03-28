import requests
url = "https://gamma-api.polymarket.com/events?limit=30&active=true&closed=false&order=volume24hr&dir=desc"
resp = requests.get(url)
events = resp.json()

print(f"{'Event Title':<50} | {'Vol24h':<10} | {'Slug'}")
print("-" * 80)
for e in events:
    print(f"{e['title'][:48]:<50} | {e.get('volume24hr', 0):>10.0f} | {e['slug']}")
