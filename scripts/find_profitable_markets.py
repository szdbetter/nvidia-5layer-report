import requests
import json

def get_hot_markets():
    # Fetch trending events
    url = "https://gamma-api.polymarket.com/events?limit=50&active=true&closed=false&order=volume24hr&dir=desc"
    resp = requests.get(url)
    events = resp.json()
    
    analysis_pool = []
    for e in events:
        title = e.get('title', '').lower()
        # Look for logic-driven or OSINT-trackable categories
        if any(kw in title for kw in ["strike", "iran", "israel", "military", "war", "fed", "inflation", "cpi", "openai", "gpt", "launch"]):
            for m in e.get('markets', []):
                if m.get('active'):
                    analysis_pool.append({
                        'event': e['title'],
                        'question': m['question'],
                        'price': m.get('lastTradePrice'),
                        'id': m['conditionId'],
                        'tokens': m.get('clobTokenIds')
                    })
    return analysis_pool

markets = get_hot_markets()
for m in markets:
    print(f"Event: {m['event']}")
    print(f"  Q: {m['question']}")
    print(f"  Price: {m['price']} | ID: {m['id']}")
