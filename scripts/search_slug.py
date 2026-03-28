import requests
slug = "us-strikes-iran-by"
url = f"https://gamma-api.polymarket.com/events?slug={slug}"
resp = requests.get(url)
data = resp.json()
if isinstance(data, list) and len(data) > 0:
    event = data[0]
    print(f"Event: {event['title']}")
    for m in event['markets']:
        print(f"  Q: {m['question']} | ID: {m['conditionId']}")
        print(f"  Tokens: {m['clobTokenIds']}")
        print(f"  Outcomes: {m['outcomes']}")
elif isinstance(data, dict):
    print(f"Event: {data.get('title')}")
else:
    print("Not found")
