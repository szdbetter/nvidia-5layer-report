#!/bin/bash
# KOL Twitter Crawler - Monthly slice strategy
# Usage: ./crawl_kol.sh <handle> [months_back]

HANDLE="${1:-0xcryptowizard}"
MONTHS_BACK="${2:-13}"

export AUTH_TOKEN="TWITTER_AUTH_TOKEN_REDACTED"
export CT0="TWITTER_CT0_REDACTED"

OUTPUT_DIR="/Users/ai/.openclaw/workspace/data/kol/${HANDLE}"
mkdir -p "$OUTPUT_DIR"

ALL_TWEETS_FILE="${OUTPUT_DIR}/all_tweets.json"
PROGRESS_FILE="${OUTPUT_DIR}/progress.txt"

echo "[]" > "$ALL_TWEETS_FILE"
echo "Starting crawl for @${HANDLE} - $(date)" | tee "$PROGRESS_FILE"

TOTAL=0

for i in $(seq 0 52); do
  # Calculate dates (weekly)
  SINCE=$(date -d "-$((i+1)) weeks" +%Y-%m-%d 2>/dev/null || date -v-$((i+1))w +%Y-%m-%d)
  UNTIL=$(date -d "-${i} weeks" +%Y-%m-%d 2>/dev/null || date -v-${i}w +%Y-%m-%d)
  
  echo "[$(date +%H:%M:%S)] Crawling ${HANDLE}: ${SINCE} to ${UNTIL}" | tee -a "$PROGRESS_FILE"
  
  # Run bird search with weekly slice
  bird search "from:${HANDLE} since:${SINCE} until:${UNTIL}" --all --max-pages 20 --json 2>/dev/null > "temp_week.json"
  
  # Count tweets this week
  COUNT=$(cat "temp_week.json" 2>/dev/null | python3 -c "import sys,json; data=json.load(sys.stdin); tweets=data.get('tweets', []); print(len(tweets))" 2>/dev/null || echo 0)
  TOTAL=$((TOTAL + COUNT))
  
  echo "  → ${COUNT} tweets (total: ${TOTAL})" | tee -a "$PROGRESS_FILE"
  
  # Merge into all_tweets
  python3 -c "
import json, sys
try:
    with open('$ALL_TWEETS_FILE') as f:
        all_t = json.load(f)
    with open('temp_week.json') as f:
        data = json.load(f)
    month_t = data.get('tweets', [])
    if isinstance(month_t, list):
        # Deduplicate while merging
        existing_ids = {t['id'] for t in all_t}
        for t in month_t:
            if t['id'] not in existing_ids:
                all_t.append(t)
    with open('$ALL_TWEETS_FILE', 'w') as f:
        json.dump(all_t, f, ensure_ascii=False, indent=2)
except Exception as e:
    print(f'Merge error: {e}', file=sys.stderr)
" 2>>"$PROGRESS_FILE"
  
  # Rate limit protection
  sleep 1
done

echo "" | tee -a "$PROGRESS_FILE"
echo "✅ Crawl complete for @${HANDLE}: ${TOTAL} total tweets" | tee -a "$PROGRESS_FILE"
echo "Output: ${ALL_TWEETS_FILE}" | tee -a "$PROGRESS_FILE"
