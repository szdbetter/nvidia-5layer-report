#!/bin/bash
# Stop Elon Poly trader and dashboard API

echo "[STOP] Stopping Elon Poly system..."

if [ -f /tmp/elon_trader.pid ]; then
    PID=$(cat /tmp/elon_trader.pid)
    if kill "$PID" 2>/dev/null; then
        echo "[STOP] Killed trader PID $PID"
    else
        echo "[STOP] Trader PID $PID not running"
    fi
    rm -f /tmp/elon_trader.pid
fi

if [ -f /tmp/elon_api.pid ]; then
    PID=$(cat /tmp/elon_api.pid)
    if kill "$PID" 2>/dev/null; then
        echo "[STOP] Killed API PID $PID"
    else
        echo "[STOP] API PID $PID not running"
    fi
    rm -f /tmp/elon_api.pid
fi

echo "[STOP] Done."
