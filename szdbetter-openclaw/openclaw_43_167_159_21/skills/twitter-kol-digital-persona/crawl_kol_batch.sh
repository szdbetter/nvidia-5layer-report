#!/bin/bash
# Twitter KOL批量抓取脚本
# 用法: ./crawl_kol_batch.sh [用户列表文件]

# 默认用户列表
DEFAULT_USERS=("btcdayu" "taresky" "0xsunnft")

# 读取用户列表
if [ -f "$1" ]; then
    mapfile -t USERS < "$1"
else
    USERS=("${DEFAULT_USERS[@]}")
fi

# 月份范围（近12个月）
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

echo "=== Twitter KOL批量抓取开始 ==="
echo "目标用户: ${USERS[*]}"
echo ""

for user in "${USERS[@]}"; do
    echo "=== 开始抓取 $user ==="
    
    # 创建用户目录
    mkdir -p "$user"
    
    # 按月抓取
    for month_range in "${MONTHS[@]}"; do
        IFS=':' read -r since until <<< "$month_range"
        month_key=${since:0:7}
        
        echo "  抓取 $month_key..."
        bird search "from:$user since:$since until:$until" > "$user/${month_key}.txt" 2>&1
        
        # 检查是否有数据
        line_count=$(wc -l < "$user/${month_key}.txt" 2>/dev/null || echo "0")
        if [ "$line_count" -lt 5 ]; then
            echo "    ⚠️ 数据较少 ($line_count 行)"
        fi
        
        sleep 2
    done
    
    # 合并所有月份
    cat $(ls -r $user/20*.txt 2>/dev/null) > "$user/all_tweets_raw.txt" 2>/dev/null
    total_lines=$(wc -l < "$user/all_tweets_raw.txt" 2>/dev/null || echo "0")
    
    echo "  ✅ 完成: $total_lines 行数据"
    echo ""
done

echo "=== 全部完成 ==="
echo ""
echo "数据位置: $(pwd)/[用户名]/all_tweets_raw.txt"
echo "下一步: 基于数据生成数字分身档案"
