#!/bin/bash
IP="43.167.159.21"
IP_UNDERSCORE="43_167_159_21"
REPO_DIR="/Users/ai/.openclaw/workspace/szdbetter-openclaw"
TARGET_DIR="${REPO_DIR}/openclaw_${IP_UNDERSCORE}"

echo "Starting backup to ${TARGET_DIR}..."

mkdir -p "${TARGET_DIR}/config"
mkdir -p "${TARGET_DIR}/skills"

# Copy essential files
cp /Users/ai/.openclaw/workspace/*.md "${TARGET_DIR}/" 2>/dev/null || true
cp -r /Users/ai/.openclaw/workspace/memory "${TARGET_DIR}/" 2>/dev/null || true
cp -r /Users/ai/.openclaw/workspace/skills/* "${TARGET_DIR}/skills/" 2>/dev/null || true
cp /root/.openclaw/openclaw.json "${TARGET_DIR}/config/" 2>/dev/null || true

# Git commit and push
cd "${REPO_DIR}"
git config user.name "OpenClaw Backup Agent"
git config user.email "bot@openclaw.ai"

git add .
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
git commit -m "Auto Backup: ${TIMESTAMP}"

# Push to origin
git push origin main
echo "Backup completed and pushed."
