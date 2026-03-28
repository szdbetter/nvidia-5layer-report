#!/bin/bash
# dashboard-mvp 守护进程 — cron 每分钟检查
# 用法: * * * * * /root/.openclaw/workspace/dashboard-mvp/ensure_dashboard.sh

DIR="/root/.openclaw/workspace/dashboard-mvp"
LOG="/tmp/dashboard-mvp.log"
PIDFILE="/tmp/dashboard-mvp.pid"
PORT=1980

# 检查端口是否在监听
if curl -s --max-time 3 -o /dev/null http://127.0.0.1:$PORT/; then
    exit 0
fi

# 服务不可达，重启
echo "[$(date)] dashboard-mvp down, restarting..." >> "$LOG"

# 杀残留进程
pkill -f "node.*dashboard-mvp/server.js" 2>/dev/null
sleep 1

# 启动
cd "$DIR" && nohup node server.js >> "$LOG" 2>&1 &
echo $! > "$PIDFILE"

# 等待启动确认
sleep 3
if curl -s --max-time 3 -o /dev/null http://127.0.0.1:$PORT/; then
    echo "[$(date)] dashboard-mvp restarted OK (pid=$(cat $PIDFILE))" >> "$LOG"
else
    echo "[$(date)] dashboard-mvp FAILED to restart!" >> "$LOG"
fi
