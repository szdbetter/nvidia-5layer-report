import requests
markets = [
    {"q": "US strikes Iran by March 31, 2026?", "id": "0x4b02efe53e631ada84681303fd66d79ad615f3d2b6a28b4633d43d935f89af58", "yes": "114073431155826730926052468626599502581519892859155799641358176120253844422606"},
    {"q": "US strikes Iran by March 4, 2026?", "id": "0xeea3c1ef1764cffd540a50c7c85513ede593ce3d4bfe452aec6a0bce3e3b4d62", "yes": "99914143954422372570989334419429036132940588491368679949212413490892830952914"}
]

for m in markets:
    url = f"https://clob.polymarket.com/price?token_id={m['yes']}&side=buy"
    resp = requests.get(url)
    print(f"Q: {m['q']} | YES Buy Price: {resp.json().get('price')}")
