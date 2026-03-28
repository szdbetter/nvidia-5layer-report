#!/bin/bash
# 最终增强版运维守护 (Sodium Labs Infra Watchdog V2)
LOG_FILE="/Users/ai/.openclaw/workspace/logs/health_events.log"
CHANNEL_ID="1472858439591002211"

send_alert() {
    # 使用 openclaw 原生 CLI 发送消息
    openclaw message send --channel discord --target $CHANNEL_ID --message "$1"
}

# 初始上线汇报
send_alert "🤖 [System Alert] 守护进程已上线，正在监控网关..."

while true; do
    openclaw gateway status > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        send_alert "🚨 [System Alert] 网关假死，正在执行自动重启..."
        openclaw gateway restart --reason "health-check-failure"
        sleep 30 # 等待重启缓冲
        send_alert "✅ [System Alert] 网关已自动重启并恢复在线。"
    fi
    sleep 60
done
