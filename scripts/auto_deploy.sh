#!/bin/bash
# Auto-deploy: cek GitHub, pull + rebuild hanya jika ada commit baru.
# Dipasang sebagai cron job di VPS (lihat docs/DEPLOY_PLUTOLAB.md bagian 8).
set -e

REPO_DIR="$HOME/cyber-incident-helpdesk"
LOG_FILE="$HOME/auto_deploy.log"
LOCK_FILE="/tmp/auto_deploy.lock"

# Cegah dua deploy berjalan bersamaan (build bisa >2 menit)
exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

cd "$REPO_DIR"

git fetch origin main --quiet
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

# Tidak ada commit baru — selesai tanpa log (biar log tidak penuh)
[ "$LOCAL" = "$REMOTE" ] && exit 0

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Commit baru terdeteksi: ${LOCAL:0:7} -> ${REMOTE:0:7}" >> "$LOG_FILE"

git pull --ff-only origin main >> "$LOG_FILE" 2>&1
docker compose up -d --build >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deploy selesai: $(git log -1 --format='%h %s')" >> "$LOG_FILE"
