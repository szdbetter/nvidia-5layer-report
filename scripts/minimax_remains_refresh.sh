#!/bin/bash
# MiniMax Token Plan 额度刷新脚本
# 读取 API 并写入 /tmp/minimax_remains.json

source ~/.openclaw/.env 2>/dev/null

RESULT=$(curl -s 'https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains' \
  -H "Authorization: Bearer $MINIMAX_API_KEY")

if [ $? -eq 0 ] && echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['base_resp']['status_code']==0" 2>/dev/null; then
  # 提取 MiniMax-M* 模型的剩余额度
  SUMMARY=$(echo "$RESULT" | python3 -c "
import json, sys, time
d = json.load(sys.stdin)
models = d.get('model_remains', [])
out = {'updated_at': int(time.time()), 'models': {}}
for m in models:
    name = m['model_name']
    total = m['current_interval_total_count']
    used = m['current_interval_usage_count']
    remains = total - used
    end_ts = m.get('end_time', 0) // 1000
    out['models'][name] = {
        'total': total,
        'used': used,
        'remains': remains,
        'reset_in_sec': max(0, end_ts - int(time.time()))
    }
print(json.dumps(out))
")
  echo "$SUMMARY" > /tmp/minimax_remains.json
  echo "OK: $(date)"
else
  echo "ERROR: API call failed"
  exit 1
fi
