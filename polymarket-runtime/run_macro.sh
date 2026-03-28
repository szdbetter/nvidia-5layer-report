#!/bin/bash
export PATH=/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin
export HOME=/Users/ai
cd /Users/ai/.openclaw/workspace/polymarket-runtime
/usr/bin/python3 poly_macro_engine.py >> /tmp/poly_macro_engine.log 2>&1
