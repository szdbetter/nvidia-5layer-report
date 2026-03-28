#!/bin/bash

# Log file
LOG_FILE="/Users/ai/.openclaw/workspace/scripts/watchdog.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Timestamp
ts() { date +"%Y-%m-%d %H:%M:%S"; }

# Path to openclaw on this Linux VPS
OPENCLAW="/root/.nvm/versions/node/v24.13.1/bin/openclaw"

# Check OpenClaw Gateway Status
if ! $OPENCLAW gateway status > /dev/null 2>&1; then
    echo "[$(ts)] ⚠️ Gateway is DOWN! Attempting restart..." >> "$LOG_FILE"
    
    # Try restart
    $OPENCLAW gateway restart
    
    # Wait and verify
    sleep 10
    if $OPENCLAW gateway status > /dev/null 2>&1; then
        echo "[$(ts)] ✅ Gateway successfully restarted." >> "$LOG_FILE"
    else
        echo "[$(ts)] ❌ Gateway restart FAILED. Manual intervention required." >> "$LOG_FILE"
    fi
else
    # echo "[$(ts)] Gateway is alive." >> "$LOG_FILE"
    :
fi
