#!/bin/bash
# 重新抓取所有KOL（按月分页抓取，避免默认10条限制）

set -euo pipefail

USERS=("0xcryptowizard" "Phyrex_Ni" "DoctorMbitcoin" "haze0x" "kiki520_eth" "cishanjia" "KuiGas" "0xAA_Science" "jason_chen998" "Wuhuoqiu" "btcdayu" "taresky" "0xsunnft")
if [[ -n "${TARGET_USERS:-}" ]]; then
  IFS=',' read -r -a USERS <<< "${TARGET_USERS}"
fi

# 时间范围：2025-02 至 2026-02（含 2026-02 当月）
MONTHS=(
  "2025-02-01:2025-03-01"
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

MAX_PAGES="${MAX_PAGES:-30}"   # 可通过环境变量覆盖，如 MAX_PAGES=50 ./recrawl_all.sh
SLEEP_SEC="${SLEEP_SEC:-2}"

if ! bird whoami --plain >/dev/null 2>&1; then
  echo "❌ bird 未登录或无法读取 X 凭据（auth_token/ct0）。"
  echo "请先确保浏览器已登录 x.com，或先导出 AUTH_TOKEN / CT0 后再执行。"
  exit 1
fi

echo "=== 重新抓取所有KOL (2025-02 至 2026-03) ==="
echo "抓取模式: bird search --all --max-pages ${MAX_PAGES}"
echo ""

for user in "${USERS[@]}"; do
  echo "=== 开始抓取 $user ==="
  mkdir -p "$user"
  
  # 按月抓取
  for month_range in "${MONTHS[@]}"; do
    IFS=':' read -r since until <<< "$month_range"
    month_key=${since:0:7}
    out_file="$user/${month_key}.txt"
    tmp_file="$user/.${month_key}.tmp.txt"

    echo "  -> ${month_key}"
    # 使用分页抓取，避免默认仅10条；失败时不覆盖旧文件
    if bird search --all --max-pages "${MAX_PAGES}" "from:$user since:$since until:$until" > "${tmp_file}" 2>&1; then
      if rg -q "Missing required credentials|Missing auth_token|Missing ct0" "${tmp_file}"; then
        echo "     ⚠️ 凭据失效，保留旧文件: ${out_file}"
        rm -f "${tmp_file}"
      else
        mv "${tmp_file}" "${out_file}"
        month_cnt=$(awk '/📅 /{n++} END{print n+0}' "${out_file}")
        echo "     月度条数: ${month_cnt}"
      fi
    else
      echo "     ⚠️ 抓取失败，保留旧文件: ${out_file}"
      rm -f "${tmp_file}"
    fi
    sleep "${SLEEP_SEC}"
  done
  
  # 合并所有月份
  cat $(ls -r "$user"/20*.txt 2>/dev/null) > "$user/all_tweets_raw.txt" 2>/dev/null || true
  total_tweets=$(awk '/📅 /{n++} END{print n+0}' "$user/all_tweets_raw.txt" 2>/dev/null || echo "0")
  
  echo "  ✅ 完成: ${total_tweets} 条推文"
  echo ""
done

echo "=== 全部完成 ==="
