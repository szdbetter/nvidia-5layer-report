import requests
url = "https://gamma-api.polymarket.com/events?limit=100&active=true&closed=false&order=volume24hr&dir=desc"
resp = requests.get(url)
for e in resp.json():
    if "btc" in e['slug'] or "bitcoin" in e['slug']:
        print(f"Title: {e['title']} | Slug: {e['slug']}")
