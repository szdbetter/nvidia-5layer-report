#!/bin/bash
# 合并所有月度推文并生成结构化MD

for user in btcdayu taresky 0xsunnft; do
  echo "处理 $user..."
  # 按时间顺序合并（2024-07到2025-06）
  cat $(ls -r $user/*.txt) > "$user/all_tweets_raw.txt" 2>/dev/null
done
echo "合并完成"
