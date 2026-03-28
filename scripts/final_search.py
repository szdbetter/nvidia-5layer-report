import requests
queries = ["Ali Khamenei", "Netanyahu", "Hezbollah", "Strike on Iran", "Strike on Israel", "IAEA"]
for q in queries:
    url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&q={q}"
    resp = requests.get(url)
    for m in resp.json():
        print(f"Q: {m['question']} | ID: {m.get('conditionId')}")
