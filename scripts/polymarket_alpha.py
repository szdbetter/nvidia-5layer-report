import requests

def get_hot_iran_markets():
    url = "https://gamma-api.polymarket.com/events?limit=50&active=true&closed=false&order=volume24hr&dir=desc"
    response = requests.get(url)
    events = response.json()
    
    keywords = ["Iran", "Israel", "Khamenei", "Strike", "Attack"]
    found = False
    
    print("# Polymarket Hot Markets (Geopolitical)\n")
    for event in events:
        title = event.get('title', '')
        if any(kw.lower() in title.lower() for kw in keywords):
            found = True
            vol = event.get('volume24hr', 0)
            print(f"## {title} (24h Vol: ${vol:,.0f})")
            for market in event.get('markets', []):
                # Get current odds/price if available
                outcome_prices = market.get('outcomePrices', [])
                print(f"  - {market['question']}")
                if outcome_prices:
                    print(f"    - Yes: {outcome_prices[0]} | No: {outcome_prices[1]}")
    
    if not found:
        print("No specific Iran/Israel hot markets found in top 50 by volume.")

get_hot_iran_markets()
