#!/bin/bash
# 按月抓取近一年推文

MONTHS=(
  "2024-07-01:2024-08-01"
  "2024-08-01:2024-09-01"
  "2024-09-01:2024-10-01"
  "2024-10-01:2024-11-01"
  "2024-11-01:2024-12-01"
  "2024-12-01:2025-01-01"
  "2025-01-01:2025-02-01"
  "2025-02-01:2025-03-01"
  "2025-03-01:2025-04-01"
  "2025-04-01:2025-05-01"
  "2025-05-01:2025-06-01"
)

USERS=("btcdayu" "taresky" "0xsunnft")

for month_range in "${MONTHS[@]}"; do
  IFS=':' read -r since until <<< "$month_range"
  echo "=== 抓取 $since - $until ==="
  
  for user in "${USERS[@]}"; do
    echo "  - $user"
    bird search "from:$user since:$since until:$until" > "$user/${since:0:7}.txt" 2>&1
    sleep 3
  done
  
  sleep 2
done

echo "=== 全部完成 ==="
