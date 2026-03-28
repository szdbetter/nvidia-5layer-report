#!/usr/bin/env python3
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URLS = [
    "https://polymarket.com/faq",
    "https://docs.polymarket.com",
    "https://uma.xyz/faq",
    "https://docs.umaproject.org/uma-tokenholders/umips",
]
OUTPUT_PATH = Path("/root/.openclaw/workspace/memory/projects/polymarket-alpha/data/rules_raw.md")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PolymarketResearchBot/1.0; +https://polymarket.com)"
}


def fetch_with_retry(url, attempts=3, delay=2):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            print(f"[fetch_rules] Request attempt {attempt}/{attempts} -> {url}")
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            last_error = exc
            print(f"[fetch_rules] Attempt {attempt} failed for {url}: {exc}")
            if attempt < attempts:
                time.sleep(delay)
    raise RuntimeError(f"Failed to fetch {url} after {attempts} attempts: {last_error}")


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.find("body") or soup
    text = main.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = []
    prev = None
    for line in lines:
        if line != prev:
            cleaned.append(line)
        prev = line
    return "\n".join(cleaned)


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sections = []

    for idx, url in enumerate(URLS, start=1):
        print(f"[fetch_rules] Processing {idx}/{len(URLS)}: {url}")
        try:
            html = fetch_with_retry(url)
            text = extract_text(html)
            sections.append(f"# Source: {url}\n\n{text}\n")
            print(f"[fetch_rules] Extracted {len(text)} characters from {url}")
        except Exception as exc:
            error_msg = f"[fetch_rules] ERROR for {url}: {exc}"
            print(error_msg)
            sections.append(f"# Source: {url}\n\nERROR: {exc}\n")

    OUTPUT_PATH.write_text("\n\n---\n\n".join(sections), encoding="utf-8")
    print(f"[fetch_rules] Wrote output to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
