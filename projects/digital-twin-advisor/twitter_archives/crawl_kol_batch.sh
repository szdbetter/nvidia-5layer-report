#!/bin/bash
# 批量抓取11位KOL的推文

USERS=("0xcryptowizard" "Phyrex_Ni" "DoctorMbitcoin" "haze0x" "kiki520_eth" "0x0xFeng" "cryptocishanjia" "KuiGas" "0xAA_Science" "jason_chen998" "Wuhuoqiu")
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

for user in "${USERS[@]}"; do
  echo "=== 开始抓取 $user ==="
  for month_range in "${MONTHS[@]}"; do
    IFS=':' read -r since until <<< "$month_range"
    bird search "from:$user since:$since until:$until" > "$user/${since:0:7}.txt" 2>&1
    sleep 2
  done
  # 合并所有月份
  cat $(ls -r $user/*.txt 2>/dev/null) > "$user/all_tweets_raw.txt" 2>/dev/null
  wc -l "$user/all_tweets_raw.txt" 2>/dev/null | awk '{print $2 ": " $1 " lines"}'
  echo ""
done

echo "=== 全部完成 ==="
