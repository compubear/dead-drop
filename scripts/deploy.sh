#!/bin/bash
set -euo pipefail

echo "=== Dead Drop Deploy ==="

# 1. Backup
echo "[1/7] Backing up database..."
bash scripts/backup_db.sh

# 2. Pull latest
echo "[2/7] Pulling latest code..."
cd /opt/dead-drop && git pull origin main

# 3. Build
echo "[3/7] Building containers..."
docker compose build --no-cache

# 4. Migrate
echo "[4/7] Running migrations..."
docker compose run --rm pipeline python -m pipeline.db.migrate

# 5. Restart
echo "[5/7] Restarting services..."
docker compose up -d

# 6. Health check
echo "[6/7] Health check..."
sleep 10
curl -sf http://localhost:3000/api/health || { echo "HEALTH CHECK FAILED"; bash scripts/rollback.sh; exit 1; }

# 7. Smoke test
echo "[7/7] Smoke test..."
docker compose exec pipeline python -m tests.smoke || { echo "SMOKE TEST FAILED"; bash scripts/rollback.sh; exit 1; }

# Notify
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHANNEL_ID:-}" ]; then
  curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHANNEL_ID}" \
    -d "text=✅ Dead Drop deployed successfully at $(date)"
fi

echo "=== Deploy Complete ==="
