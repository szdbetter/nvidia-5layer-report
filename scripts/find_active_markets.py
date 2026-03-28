import requests

# Find hot/active markets
url = "https://gamma-api.polymarket.com/events?limit=10&active=true&closed=false&order=volume24hr&dir=desc"
response = requests.get(url)
events = response.json()

for event in events:
    print(f"Event: {event['title']}")
    for market in event['markets']:
        print(f"  Question: {market['question']}")
        print(f"  Condition ID: {market['conditionId']}")
        # Get outcomes
        outcomes = eval(market['outcomes']) if isinstance(market['outcomes'], str) else market['outcomes']
        clob_ids = eval(market['clobTokenIds']) if isinstance(market['clobTokenIds'], str) else market['clobTokenIds']
        for i, outcome in enumerate(outcomes):
            print(f"    Outcome: {outcome}, CLOB ID: {clob_ids[i]}")
