#!/usr/bin/env python3
"""Fetch top crypto + politics + macro markets from Polymarket.

Strategy:
- Pull 1000 open markets sorted by volume from Gamma API
- Match against crypto / politics / fed keywords with word-boundary matching
- Sort all matches by volume, take top 80
- Also pull closed high-volume crypto/politics markets as supplementary data
"""
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"
GAMMA_EVENTS_URL = "https://gamma-api.polymarket.com/events"
OUTPUT_PATH = Path("/root/.openclaw/workspace/memory/projects/polymarket-alpha/data/markets_top80.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PolymarketResearchBot/2.0; +https://polymarket.com)"
}
TARGET_COUNT = 80
FETCH_LIMIT = 100

# ── Keywords ─────────────────────────────────────────────────────────
CRYPTO_KEYWORDS = ["bitcoin", "btc", "eth", "ethereum", "crypto", "solana", "sol",
                    "altcoin", "defi", "nft", "stablecoin", "usdc", "usdt", "tether",
                    "xrp", "ripple", "dogecoin", "doge", "cardano", "ada",
                    "bnb", "binance", "coinbase", "microstrategy", "satoshi",
                    "memecoin", "meme coin"]
POLITICS_KEYWORDS = ["trump", "election", "president", "senate", "congress",
                      "political", "us politics", "democrat", "republican",
                      "governor", "vance", "desantis", "biden", "harris",
                      "rfk", "kennedy", "whitehouse", "white house",
                      "impeach", "indictment", "midterm", "primary",
                      "nomination", "inaugural"]
MACRO_KEYWORDS = ["fed", "interest rate", "fomc", "federal reserve",
                   "inflation", "cpi", "gdp", "tariff", "recession"]

ALL_KEYWORDS = CRYPTO_KEYWORDS + POLITICS_KEYWORDS + MACRO_KEYWORDS

# Short keywords that need word-boundary matching to avoid false positives
BOUNDARY_KEYWORDS = {"btc", "eth", "sol", "fed", "ada", "bnb", "xrp", "cpi",
                      "gdp", "nft", "doge", "trump", "senate", "congress",
                      "president", "election", "political", "crypto", "solana",
                      "bitcoin", "ethereum", "rfk"}


def fetch_with_retry(url: str, params: Dict[str, Any] | None = None, attempts: int = 3, delay: int = 2):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(delay)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(normalize_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(normalize_text(v) for v in value.values())
    return str(value).lower()


def volume_num(item: Dict[str, Any]) -> float:
    for key in ("volumeNum", "volume", "volumeClob"):
        value = item.get(key)
        if value is None:
            continue
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            continue
    return 0.0


def market_haystack(market: Dict[str, Any]) -> str:
    parts = [
        market.get("question"),
        market.get("description"),
        market.get("category"),
        market.get("slug"),
        market.get("groupItemTitle"),
        market.get("tags"),
        market.get("clobTags"),
    ]
    for event in market.get("events", []):
        if isinstance(event, dict):
            parts.append(event.get("title"))
            parts.append(event.get("description"))
            for series in event.get("series", []) or []:
                if isinstance(series, dict):
                    parts.append(series.get("title"))
                    parts.append(series.get("slug"))
    return " ".join(normalize_text(p) for p in parts)


def keyword_in_text(keyword: str, haystack: str) -> bool:
    if keyword in BOUNDARY_KEYWORDS:
        return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", haystack) is not None
    return keyword in haystack


def classify_market(market: Dict[str, Any]) -> Tuple[bool, List[str], str]:
    """Returns (matched, keywords, category_label).
    
    Priority: macro > politics > crypto (to avoid misclassifying political
    markets that happen to mention crypto keywords tangentially).
    Only classify as "crypto" if question/slug directly mentions crypto terms.
    """
    haystack = market_haystack(market)
    matches = [kw for kw in ALL_KEYWORDS if keyword_in_text(kw, haystack)]
    if not matches:
        return False, [], ""

    has_macro = any(kw in MACRO_KEYWORDS for kw in matches)
    has_politics = any(kw in POLITICS_KEYWORDS for kw in matches)

    # For crypto classification, only check question + slug (not nested event text)
    question_haystack = normalize_text(market.get("question")) + " " + normalize_text(market.get("slug"))
    has_crypto_direct = any(keyword_in_text(kw, question_haystack) for kw in CRYPTO_KEYWORDS)

    if has_macro:
        cat = "macro"
    elif has_politics:
        cat = "politics"
    elif has_crypto_direct:
        cat = "crypto"
    else:
        # Crypto signal only in nested event data — still count but mark as crypto
        has_crypto_any = any(kw in CRYPTO_KEYWORDS for kw in matches)
        if has_crypto_any:
            cat = "crypto"
        else:
            return False, [], ""
    return True, sorted(set(matches)), cat


def extract_rules(market: Dict[str, Any]) -> str:
    return (
        market.get("resolutionRules")
        or market.get("resolutionCriteria")
        or market.get("resolution_criteria")
        or market.get("rules")
        or ""
    )


def fetch_gamma_pages(closed: str = "false", pages: int = 10) -> List[Dict[str, Any]]:
    collected, seen = [], set()
    for offset in range(0, FETCH_LIMIT * pages, FETCH_LIMIT):
        params = {"limit": FETCH_LIMIT, "offset": offset, "closed": closed,
                  "order": "volumeNum", "ascending": "false"}
        page = fetch_with_retry(GAMMA_MARKETS_URL, params=params)
        if not isinstance(page, list) or not page:
            break
        for market in page:
            mid = market.get("id") or market.get("conditionId")
            if mid in seen:
                continue
            seen.add(mid)
            collected.append(market)
        if len(page) < FETCH_LIMIT:
            break
    return collected


def to_output_item(market: Dict[str, Any], matched_keywords: List[str], cat: str) -> Dict[str, Any]:
    event_titles = [e.get("title") for e in market.get("events", []) if isinstance(e, dict) and e.get("title")]
    category = market.get("category") or (event_titles[0] if event_titles else None)
    return {
        "id": market.get("id"),
        "question": market.get("question"),
        "description": market.get("description"),
        "category": category,
        "themeCategory": cat,
        "matchedKeywords": matched_keywords,
        "volume": volume_num(market),
        "closed": market.get("closed", False),
        "endDate": market.get("endDate"),
        "outcomePrices": market.get("outcomePrices"),
        "outcomes": market.get("outcomes"),
        "resolutionSource": market.get("resolutionSource"),
        "resolutionRules": extract_rules(market),
        "slug": market.get("slug"),
    }


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 1) Fetch open markets (10 pages = 1000)
    print("[fetch_markets] Fetching open markets...")
    open_markets = fetch_gamma_pages(closed="false", pages=10)
    print(f"[fetch_markets] Open markets fetched: {len(open_markets)}")

    # 2) Also fetch top closed markets (for high-volume crypto/politics history)
    print("[fetch_markets] Fetching closed markets...")
    closed_markets = fetch_gamma_pages(closed="true", pages=5)
    print(f"[fetch_markets] Closed markets fetched: {len(closed_markets)}")

    # 3) Merge & deduplicate
    seen_ids = set()
    all_markets = []
    for m in open_markets + closed_markets:
        mid = m.get("id") or m.get("conditionId")
        if mid not in seen_ids:
            seen_ids.add(mid)
            all_markets.append(m)
    print(f"[fetch_markets] Total unique markets: {len(all_markets)}")

    # 4) Classify
    crypto_matches, politics_matches, macro_matches = [], [], []
    for market in all_markets:
        matched, keywords, cat = classify_market(market)
        if not matched:
            continue
        entry = (volume_num(market), market, keywords, cat)
        if cat == "crypto":
            crypto_matches.append(entry)
        elif cat == "politics":
            politics_matches.append(entry)
        elif cat == "macro":
            macro_matches.append(entry)

    crypto_matches.sort(key=lambda x: x[0], reverse=True)
    politics_matches.sort(key=lambda x: x[0], reverse=True)
    macro_matches.sort(key=lambda x: x[0], reverse=True)

    print(f"[fetch_markets] Crypto matches: {len(crypto_matches)}")
    print(f"[fetch_markets] Politics matches: {len(politics_matches)}")
    print(f"[fetch_markets] Macro matches: {len(macro_matches)}")

    # 5) Build balanced top-80: ensure at least 20 crypto, 20 politics, rest by volume
    MIN_CRYPTO = 20
    MIN_POLITICS = 20
    result_entries = []

    # Guarantee minimums
    for entry in crypto_matches[:MIN_CRYPTO]:
        result_entries.append(entry)
    for entry in politics_matches[:MIN_POLITICS]:
        result_entries.append(entry)

    # Fill remaining slots from all matches by volume
    used_ids = {e[1].get("id") for e in result_entries}
    remaining = [e for e in crypto_matches + politics_matches + macro_matches if e[1].get("id") not in used_ids]
    remaining.sort(key=lambda x: x[0], reverse=True)
    for entry in remaining:
        if len(result_entries) >= TARGET_COUNT:
            break
        result_entries.append(entry)

    # Sort final by volume
    result_entries.sort(key=lambda x: x[0], reverse=True)

    result = [to_output_item(m, kw, cat) for _, m, kw, cat in result_entries]
    OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # Stats
    cats = {"crypto": 0, "politics": 0, "macro": 0}
    open_count = sum(1 for r in result if not r.get("closed"))
    for r in result:
        cats[r["themeCategory"]] = cats.get(r["themeCategory"], 0) + 1

    print(f"\n[fetch_markets] ✅ Wrote {len(result)} markets to {OUTPUT_PATH}")
    print(f"[fetch_markets] Category breakdown: {cats}")
    print(f"[fetch_markets] Open: {open_count} | Closed: {len(result) - open_count}")
    print("[fetch_markets] Top 5 by volume:")
    for idx, item in enumerate(result[:5], start=1):
        print(f"  {idx}. [{item['themeCategory']}] {item['question'][:80]} | vol=${item['volume']:,.0f}")


if __name__ == "__main__":
    main()
