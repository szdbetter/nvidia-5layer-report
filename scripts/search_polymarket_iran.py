import requests

# Search for markets related to Iran, Israel, Strike, or Middle East
queries = ["Iran", "Israel", "Strike", "Middle East", "War"]
found = []

for q in queries:
    url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&q={q}"
    response = requests.get(url)
    data = response.json()
    for m in data:
        if m.get('conditionId'):
            found.append(m)

# Deduplicate
seen = set()
for m in found:
    if m['conditionId'] not in seen:
        seen.add(m['conditionId'])
        print(f"Market: {m['question']}")
        print(f"  Condition ID: {m['conditionId']}")
        clob_ids = eval(m['clobTokenIds']) if isinstance(m['clobTokenIds'], str) else m['clobTokenIds']
        outcomes = eval(m['outcomes']) if isinstance(m['outcomes'], str) else m['outcomes']
        for i, outcome in enumerate(outcomes):
            print(f"    Outcome: {outcome}, CLOB ID: {clob_ids[i]}")
