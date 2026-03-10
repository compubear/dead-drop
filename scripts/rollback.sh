#!/bin/bash
set -euo pipefail

echo "=== Dead Drop Rollback ==="

cd /opt/dead-drop

# Get the previous commit
PREV_COMMIT=$(git log --format="%H" -2 | tail -1)
echo "[1/4] Rolling back to commit: ${PREV_COMMIT}"

# Revert to previous commit
git checkout "${PREV_COMMIT}"

# Rebuild and restart
echo "[2/4] Rebuilding containers..."
docker compose build

echo "[3/4] Restarting services..."
docker compose up -d

# Health check
echo "[4/4] Health check..."
sleep 10
curl -sf http://localhost:3000/api/health || { echo "ROLLBACK HEALTH CHECK FAILED — MANUAL INTERVENTION REQUIRED"; exit 1; }

# Notify
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHANNEL_ID:-}" ]; then
  curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHANNEL_ID}" \
    -d "text=⚠️ Dead Drop ROLLED BACK to ${PREV_COMMIT} at $(date)"
fi

echo "=== Rollback Complete ==="
