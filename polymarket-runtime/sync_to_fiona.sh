#!/usr/bin/env bash
set -euo pipefail
REMOTE="ai@100.90.1.48"  # Tailscale IP updated 2026-03-17 (was 100.101.75.22 / fiona-mbp2015.local)
REMOTE_DIR="~/.openclaw/workspace/polymarket-runtime"
mkdir -p polymarket-runtime
scp polymarket-runtime/poly_runtime.py "$REMOTE:$REMOTE_DIR/"
scp polymarket-runtime/poly_unified_engine.py "$REMOTE:$REMOTE_DIR/"
scp polymarket-runtime/poly_monitor_job.py "$REMOTE:$REMOTE_DIR/"
echo "sync complete -> $REMOTE:$REMOTE_DIR"
