#!/bin/bash
# 闲鱼 IM 自动回复守护进程
# 每30秒扫描一次新消息并自动回复
echo "[$(date)] 闲鱼 bot 启动"
while true; do
  node /tmp/xianyu_bot.js >> /tmp/xianyu_bot.log 2>&1
  echo "[$(date)] 扫描完成，等待30秒..." >> /tmp/xianyu_bot.log
  sleep 30
done
