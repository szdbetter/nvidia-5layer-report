import requests

url = "https://gamma-api.polymarket.com/events?limit=20&active=true&closed=false&order=volume24hr&dir=desc"
response = requests.get(url)
data = response.json()

for event in data:
    print(f"[{event.get('volume24hr', 0):,.0f} 24h vol] {event['title']}")
    for market in event['markets']:
        print(f"  - {market['question']} (ID: {market['conditionId']})")
