import requests
# Search for active Middle East military/escalation markets
url = "https://gamma-api.polymarket.com/events?active=true&closed=false&order=volume24hr&dir=desc&limit=50"
resp = requests.get(url)
events = resp.json()

military_keywords = ["strike", "iran", "israel", "military", "war", "ceasefire", "hezbollah", "houthi"]

for e in events:
    title = e['title'].lower()
    if any(k in title for k in military_keywords):
        print(f"Event: {e['title']} | Vol24h: {e.get('volume24hr', 0):,.0f}")
        for m in e['markets']:
            if m.get('active'):
                print(f"  Q: {m['question']} | Price: {m.get('lastTradePrice')} | ID: {m['conditionId']}")
