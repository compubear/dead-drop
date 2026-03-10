#!/bin/bash
set -euo pipefail

BACKUP_DIR="/opt/dead-drop/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/deaddrop_${TIMESTAMP}.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "Backing up database to ${BACKUP_FILE}..."

docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-deaddrop}" \
  -d "${POSTGRES_DB:-deaddrop}" \
  | gzip > "${BACKUP_FILE}"

echo "Backup complete: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

# Keep only last 7 backups
echo "Cleaning old backups (keeping last 7)..."
ls -t "${BACKUP_DIR}"/deaddrop_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm -v

echo "Database backup done."
