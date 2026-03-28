import requests
url = "https://gamma-api.polymarket.com/events?active=true&closed=false&order=volume24hr&dir=desc&limit=20"
resp = requests.get(url)
for e in resp.json():
    print(f"Event: {e['title']} | Vol24h: {e.get('volume24hr', 0):,.0f} | Slug: {e['slug']}")
