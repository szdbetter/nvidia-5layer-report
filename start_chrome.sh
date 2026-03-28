#!/bin/bash
# Wake display first
caffeinate -u -t 5 &
sleep 2
# Kill any existing Chrome without debug port, keep login data
pkill -f "Google Chrome" 2>/dev/null || true
sleep 2
# Start Chrome with debug port using existing profile (keeps cookies/login)
open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="/Users/ai/Library/Application Support/Google/Chrome"
sleep 5
# Verify
curl -s --noproxy '*' http://localhost:9222/json/version | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK:', d.get('Browser','?'))" 2>/dev/null || echo "port not ready yet"
