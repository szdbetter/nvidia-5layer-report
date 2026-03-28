#!/bin/bash
# 新KOL抓取脚本（在Fiona上运行）
# 目标：zksgu / sanyi_eth_ / SEFATUBA3 / WolfyXBT / kzhang_k / 0xcryptowizard(补抓)
# 时间范围：2025-03 ~ 2026-03（12个月）

BASE=/Users/ai/.openclaw/workspace/projects/digital-twin-advisor/twitter_archives
LOG=/Users/ai/.openclaw/workspace/projects/digital-twin-advisor/twitter_archives/crawl_new_kol.log
cd "$BASE"

USERS=("zksgu" "sanyi_eth_" "SEFATUBA3" "WolfyXBT" "kzhang_k" "0xcryptowizard")
MONTHS=("2025-03-01:2025-04-01" "2025-04-01:2025-05-01" "2025-05-01:2025-06-01" "2025-06-01:2025-07-01" "2025-07-01:2025-08-01" "2025-08-01:2025-09-01" "2025-09-01:2025-10-01" "2025-10-01:2025-11-01" "2025-11-01:2025-12-01" "2025-12-01:2026-01-01" "2026-01-01:2026-02-01" "2026-02-01:2026-03-01")

for user in "${USERS[@]}"; do
  echo "====== @$user START $(date '+%H:%M:%S') ======" | tee -a $LOG
  mkdir -p "$user"
  for month_range in "${MONTHS[@]}"; do
    IFS=':' read -r since until <<< "$month_range"
    month_label="${since:0:7}"
    bird search "from:$user since:$since until:$until" > "$user/${month_label}.txt" 2>&1
    count=$(grep -c "^@" "$user/${month_label}.txt" 2>/dev/null || echo 0)
    echo "  $month_label: $count tweets" | tee -a $LOG
    sleep 3
  done
  cat $(ls "$user"/*.txt 2>/dev/null | grep -v all_tweets | sort -r) > "$user/all_tweets_raw.txt"
  total=$(grep -c "^@" "$user/all_tweets_raw.txt" 2>/dev/null || echo 0)
  echo "  DONE @$user total: $total" | tee -a $LOG
done

echo "ALL DONE $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $LOG
for user in "${USERS[@]}"; do
  f="$BASE/$user/all_tweets_raw.txt"
  count=$([ -f "$f" ] && grep -c "^@" "$f" 2>/dev/null || echo 0)
  echo "RESULT @$user: $count" | tee -a $LOG
done
