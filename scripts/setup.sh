#!/bin/bash
# Setup awal sistem helpdesk keamanan siber Pusdatin
set -e

echo "=== Setup Helpdesk Keamanan Siber Pusdatin ==="

# 1. Pastikan .env ada
if [ ! -f .env ]; then
    echo "[ERROR] File .env tidak ditemukan. Salin dari .env.example dan isi variabel yang diperlukan."
    exit 1
fi

# 2. Jalankan semua servis infrastruktur
echo "[1/5] Menjalankan docker compose..."
docker compose up -d db redis qdrant
echo "      Menunggu servis siap..."
sleep 15

# 3. Jalankan migrasi database
echo "[2/5] Menjalankan migrasi database (alembic)..."
docker compose run --rm api alembic upgrade head

# 4. Ingest knowledge base
echo "[3/5] Ingesting knowledge base dokumen..."
DOCS_DIR="knowledge_base/documents"
STIX_FILE="knowledge_base/enterprise-attack.json"

if [ -d "$DOCS_DIR" ] && [ "$(ls -A $DOCS_DIR 2>/dev/null)" ]; then
    docker compose run --rm api python scripts/ingest_knowledge.py --docs-dir "$DOCS_DIR"
else
    echo "      [SKIP] Folder $DOCS_DIR kosong atau tidak ada."
fi

if [ -f "$STIX_FILE" ]; then
    echo "[3b/5] Ingesting MITRE ATT&CK STIX..."
    docker compose run --rm api python scripts/ingest_knowledge.py --stix-only --stix-file "$STIX_FILE"
else
    echo "      [SKIP] File STIX $STIX_FILE tidak ditemukan."
fi

# 5. Jalankan API dan bot
echo "[4/5] Menjalankan API server dan bot Telegram..."
docker compose up -d api telegram-bot

echo "[5/5] Verifikasi health check..."
sleep 5
curl -sf http://localhost:8000/api/v1/health && echo " → API OK" || echo " → API belum siap"

echo ""
echo "=== Setup selesai! ==="
echo "API     : http://localhost:8000"
echo "Docs    : http://localhost:8000/docs"
echo "Qdrant  : http://localhost:6333"
echo ""
echo "Jalankan E2E test: python scripts/e2e_test.py"
echo "Lihat log       : docker compose logs -f api telegram-bot"
