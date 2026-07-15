#!/bin/bash
# Auto-deploy: cek GitHub, pull + rebuild hanya jika ada commit baru.
# Dipasang sebagai cron job di VPS (lihat docs/DEPLOY_PLUTOLAB.md bagian 8).
set -e

REPO_DIR="$HOME/cyber-incident-helpdesk"
LOG_FILE="$HOME/auto_deploy.log"
LOCK_FILE="/tmp/auto_deploy.lock"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"

# Cegah dua deploy berjalan bersamaan (build bisa >2 menit)
exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

cd "$REPO_DIR"

git fetch origin "$DEPLOY_BRANCH" --quiet
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$DEPLOY_BRANCH")

# Tidak ada commit baru — selesai tanpa log (biar log tidak penuh)
[ "$LOCAL" = "$REMOTE" ] && exit 0

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Commit baru terdeteksi: ${LOCAL:0:7} -> ${REMOTE:0:7}" >> "$LOG_FILE"

git pull --ff-only origin "$DEPLOY_BRANCH" >> "$LOG_FILE" 2>&1
docker compose up -d --build >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deploy selesai: $(git log -1 --format='%h %s')" >> "$LOG_FILE"
