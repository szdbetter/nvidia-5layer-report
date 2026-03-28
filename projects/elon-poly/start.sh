#!/bin/bash
# Start Elon Poly trader and dashboard API in background

PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJ_DIR"

echo "[START] Launching Elon Poly system from $PROJ_DIR"

# Kill existing if running
if [ -f /tmp/elon_trader.pid ]; then
    OLD_PID=$(cat /tmp/elon_trader.pid)
    kill "$OLD_PID" 2>/dev/null && echo "[START] Killed old trader PID $OLD_PID"
fi
if [ -f /tmp/elon_api.pid ]; then
    OLD_PID=$(cat /tmp/elon_api.pid)
    kill "$OLD_PID" 2>/dev/null && echo "[START] Killed old API PID $OLD_PID"
fi

# Start trader
nohup python3 "$PROJ_DIR/trader.py" >> /tmp/elon_trader.log 2>&1 &
TRADER_PID=$!
echo $TRADER_PID > /tmp/elon_trader.pid
echo "[START] trader.py started (PID=$TRADER_PID)"

# Start dashboard API
nohup python3 "$PROJ_DIR/dashboard_api.py" >> /tmp/elon_api.log 2>&1 &
API_PID=$!
echo $API_PID > /tmp/elon_api.pid
echo "[START] dashboard_api.py started (PID=$API_PID)"

echo "[START] Done. Logs: /tmp/elon_trader.log | /tmp/elon_api.log"
echo "[START] API: http://localhost:8899/api/elon"
