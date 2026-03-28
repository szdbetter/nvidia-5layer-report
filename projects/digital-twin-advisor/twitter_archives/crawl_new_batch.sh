#!/bin/bash
# 抓取任务：5个新KOL + 0xcryptowizard补抓
# 时间范围：2025-03 ~ 2026-03（12个月）
# 执行机器：fiona-mbp2015
# 创建时间：2026-03-16

BASE_DIR="/Users/ai/.openclaw/workspace/projects/digital-twin-advisor/twitter_archives"
cd "$BASE_DIR" || exit 1

USERS=("zksgu" "sanyi_eth_" "SEFATUBA3" "WolfyXBT" "kzhang_k" "0xcryptowizard")

MONTHS=(
  "2025-03-01:2025-04-01"
  "2025-04-01:2025-05-01"
  "2025-05-01:2025-06-01"
  "2025-06-01:2025-07-01"
  "2025-07-01:2025-08-01"
  "2025-08-01:2025-09-01"
  "2025-09-01:2025-10-01"
  "2025-10-01:2025-11-01"
  "2025-11-01:2025-12-01"
  "2025-12-01:2026-01-01"
  "2026-01-01:2026-02-01"
  "2026-02-01:2026-03-01"
)

for user in "${USERS[@]}"; do
  echo "=============================="
  echo "开始抓取: @$user"
  echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
  mkdir -p "$user"

  for month_range in "${MONTHS[@]}"; do
    IFS=':' read -r since until <<< "$month_range"
    month_label="${since:0:7}"
    out_file="$user/${month_label}.txt"
    echo "  抓取 $month_label ..."
    bird search "from:$user since:$since until:$until" > "$out_file" 2>&1
    count=$(grep -c "^@" "$out_file" 2>/dev/null || echo 0)
    echo "    → $count 条推文"
    sleep 3
  done

  # 合并
  all_file="$user/all_tweets_raw.txt"
  cat $(ls -r "$user"/*.txt 2>/dev/null | grep -v all_tweets) > "$all_file" 2>/dev/null
  total=$(grep -c "^@" "$all_file" 2>/dev/null || echo 0)
  echo "  ✅ @$user 合计: $total 条推文"
  echo ""
done

echo "=============================="
echo "全部抓取完成: $(date '+%Y-%m-%d %H:%M:%S')"
echo "结果汇总:"
for user in "${USERS[@]}"; do
  f="$BASE_DIR/$user/all_tweets_raw.txt"
  if [ -f "$f" ]; then
    count=$(grep -c "^@" "$f" 2>/dev/null || echo 0)
    if [ "$count" -ge 200 ]; then
      status="✅ 达标入库"
    elif [ "$count" -ge 180 ]; then
      status="⚠️ 边缘可入库"
    else
      status="❌ 不达标"
    fi
    echo "  @$user: $count 条 → $status"
  else
    echo "  @$user: 文件不存在"
  fi
done
