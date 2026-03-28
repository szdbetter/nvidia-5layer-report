import requests
import json

def get_geo_markets():
    # Use Gamma API to find geopolitical markets
    # Categories: Geopolitics, Military, International
    url = "https://gamma-api.polymarket.com/events?limit=50&active=true&closed=false&order=volume24hr&dir=desc"
    response = requests.get(url)
    events = response.json()
    
    geo_keywords = ["Iran", "Israel", "Strike", "Attack", "War", "Middle East", "Military", "Ceasefire", "Strike", "Hezbollah", "Houthis"]
    
    found = []
    for event in events:
        text = (event.get('title', '') + ' ' + event.get('description', '')).lower()
        if any(kw.lower() in text for kw in geo_keywords):
            for market in event.get('markets', []):
                found.append({
                    'question': market['question'],
                    'id': market['conditionId'],
                    'clobTokenIds': market['clobTokenIds'],
                    'outcomes': market['outcomes'],
                    'price': market.get('lastTradePrice')
                })
    return found

markets = get_geo_markets()
for m in markets:
    print(f"Market: {m['question']}")
    print(f"  Price: {m['price']}")
    print(f"  ID: {m['id']}")
    print(f"  Tokens: {m['clobTokenIds']}")
