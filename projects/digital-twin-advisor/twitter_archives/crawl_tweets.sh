#!/bin/bash
# 推特抓取脚本 - 按月分片绕过深度限制

USERS=("btcdayu" "taresky" "0xsunnft")
BASE_DIR="/Users/ai/.openclaw/workspace/twitter_archives"

# 生成过去12个月的月份范围（从2024年7月到2025年6月）
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
  "2025-06-01:2025-07-01"
)

for user in "${USERS[@]}"; do
  echo "=== 开始抓取 @$user ==="
  mkdir -p "$BASE_DIR/$user"
  
  for month_range in "${MONTHS[@]}"; do
    IFS=':' read -r since until <<< "$month_range"
    echo "抓取 $since 到 $until 的推文..."
    
    # 使用 bird search 抓取
    bird search "from:$user since:$since until:$until" >> "$BASE_DIR/$user/tweets_raw.txt" 2>&1
    
    # 添加延迟避免触发限制
    sleep 3
  done
  
  echo "✓ @$user 抓取完成"
done

echo "全部抓取完成！"
