#!/bin/bash
# 自动更新 openclaw 和 openviking 文档
SCRIPT_DIR="/root/.openclaw/workspace/scripts/get_github_files"
LOG_FILE="/root/.openclaw/docs/update.log"
echo "[$(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)] 开始文档更新" >> "$LOG_FILE"
echo "openclaw/openclaw" | python3 "$SCRIPT_DIR/get_github_files.py" >> "$LOG_FILE" 2>&1
echo "[$(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)] openclaw 完成" >> "$LOG_FILE"
echo "volcengine/OpenViking" | python3 "$SCRIPT_DIR/get_github_files.py" >> "$LOG_FILE" 2>&1
echo "[$(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)] openviking 完成" >> "$LOG_FILE"
echo "[$(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)] 文档更新全部完成" >> "$LOG_FILE"
