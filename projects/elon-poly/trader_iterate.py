#!/usr/bin/env python3
"""
Elon Poly - LLM Iteration Analysis (runs every 30min via cron)
Reads recent prices + state, calls MiniMax, appends to iterate_log.jsonl
"""

import os
import json
import time
import traceback
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv('/root/.openclaw/.env')

PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = "/tmp/elon_trader_state.json"
PRICES_FILE = os.path.join(PROJ_DIR, "live_prices.jsonl")
ITERATE_LOG = os.path.join(PROJ_DIR, "iterate_log.jsonl")

MINIMAX_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"
MINIMAX_MODEL = "MiniMax-M2.7"

# Doubao fallback
DOUBAO_KEY = os.getenv("ARK_API_KEY") or os.getenv("VOLCENGINE_API_KEY")
DOUBAO_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DOUBAO_MODEL = "doubao-seed-2.0-lite"


def load_recent_prices(n=20):
    try:
        if not os.path.exists(PRICES_FILE):
            return []
        with open(PRICES_FILE) as f:
            lines = f.readlines()
        records = []
        for line in lines[-n:]:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
        return records
    except Exception as e:
        print(f"[WARN] load_recent_prices: {e}")
        return []


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def call_llm(prompt):
    """Try MiniMax first, fallback to Doubao."""
    # Try MiniMax
    if MINIMAX_KEY:
        try:
            r = requests.post(MINIMAX_URL, headers={
                "Authorization": f"Bearer {MINIMAX_KEY}",
                "Content-Type": "application/json",
            }, json={"model": MINIMAX_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 800}, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if data.get("base_resp", {}).get("status_code", 0) == 0:
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", ""), "minimax"
        except Exception as e:
            print(f"[WARN] MiniMax failed: {e}")

    # Fallback: Gemini (google generativeai, accessible from VPS)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30
            )
            if r.status_code == 200:
                parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", ""), "gemini-flash"
        except Exception as e:
            print(f"[WARN] Gemini failed: {e}")

    return None, None


def build_prompt(state, recent_prices):
    ts = state.get("ts", "unknown")
    day = state.get("day", "?")
    tweets = state.get("cumulative_tweets", "?")
    predicted = state.get("predicted_final", "?")
    usdc = state.get("usdc_balance", "?")
    positions = state.get("positions", {})

    # Summarize bracket prices
    bracket_summary = ""
    if recent_prices:
        latest = recent_prices[-1]
        brackets = latest.get("brackets", {})
        for b, info in brackets.items():
            ask = info.get("best_ask")
            edge = info.get("edge")
            p = info.get("p_model")
            bracket_summary += f"  {b}: ask={ask} edge={edge} p_model={p}\n"

    prompt = f"""You are an algorithmic trading analyst for Polymarket prediction markets.

Current status (as of {ts}):
- Event: "How many tweets will Elon Musk post this week?" (Event 278377)
- Day: {day} | Deadline: 2026-03-27 15:59 UTC
- Cumulative tweets so far: {tweets}
- Projected final count: {predicted}
- USDC balance: ${usdc}
- Open positions: {list(positions.keys()) if positions else 'None'}

Recent bracket market prices (last 2 hours):
{bracket_summary}

Recent data points (last {len(recent_prices)} readings):
{json.dumps([{"ts": r.get("ts"), "tweets": r.get("cumulative_tweets"), "predicted": r.get("predicted_final")} for r in recent_prices[-5:]], indent=2)}

Please provide:
1. Quick assessment: Is the tweet trajectory on track for which bracket(s)?
2. Best value bracket to hold/buy right now, with reasoning
3. Any regime change signals (pace acceleration/slowdown)
4. Recommended action (hold / enter bracket X / take profit)
Keep response under 200 words, actionable, no fluff.
"""
    return prompt


def main():
    print(f"[ITERATE] {datetime.now(timezone.utc).isoformat()} - Starting LLM iteration")

    state = load_state()
    recent_prices = load_recent_prices(20)

    if not state and not recent_prices:
        print("[ITERATE] No data available, skipping")
        return

    prompt = build_prompt(state, recent_prices)
    analysis, model_used = call_llm(prompt)

    if analysis is None:
        print("[ITERATE] All LLMs unavailable, skipping analysis")
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "model": "skipped",
            "analysis": None,
            "state_snapshot": {
                "day": state.get("day"),
                "tweets": state.get("cumulative_tweets"),
                "predicted_final": state.get("predicted_final"),
            }
        }
    else:
        print(f"[ITERATE] MiniMax response:\n{analysis}")
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "model": model_used or "unknown",
            "analysis": analysis,
            "state_snapshot": {
                "day": state.get("day"),
                "tweets": state.get("cumulative_tweets"),
                "predicted_final": state.get("predicted_final"),
                "positions": state.get("positions", {}),
                "usdc_balance": state.get("usdc_balance"),
            }
        }

    try:
        with open(ITERATE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"[ITERATE] Logged to {ITERATE_LOG}")
    except Exception as e:
        print(f"[ERROR] Could not write iterate_log: {e}")


if __name__ == "__main__":
    main()
