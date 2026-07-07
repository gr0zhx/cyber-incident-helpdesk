# Tutorial Deploy ke Server Lab Pluto (Proxmox)

Panduan ini untuk deploy sistem helpdesk ke VPS Ubuntu di lab Pluto (Proxmox),
supaya bisa diakses lewat subdomain publik untuk keperluan SUS testing.
Kodingan tetap dikembangkan di laptop lokal — VPS hanya untuk menjalankan versi
yang sudah di-push ke GitHub.

## 0. Info deployment

- **Subdomain**: `cyber-helpdesk.plutolab.my.id` (sudah didaftarkan ke admin,
  diarahkan ke port `8000`)
- **IP lokal VPS**: `192.168.100.129`
- **User OS**: `ubuntu` (password disimpan sendiri, jangan taruh di file
  manapun di repo)
- Terkoneksi ke **jaringan kabel Lab Pluto** dulu — IP lokal VPS hanya bisa
  dijangkau dari jaringan ini, bukan dari WiFi luar/rumah.
- Tunnel/reverse proxy ke subdomain publik **dikelola terpusat oleh admin**
  lab (routing subdomain → port sudah didaftarkan lewat form permintaan
  subdomain) — kamu tidak perlu install `cloudflared` sendiri di VPS, cukup
  pastikan aplikasi benar-benar jalan di port `8000`.

## 1. SSH ke VPS

Dari laptop yang sudah konek ke jaringan kabel lab:

```bash
ssh ubuntu@192.168.100.129
```

## 2. Install Docker (kalau belum ada)

```bash
docker --version || curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# logout lalu login ulang supaya grup docker aktif
```

## 3. Clone aplikasi

```bash
git clone https://github.com/gr0zhx/pusdatin-help.git
cd pusdatin-help
cp .env.example .env
nano .env   # isi GITHUB_TOKEN/OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, dst
            # (nilai sama seperti di .env laptop, generate baru untuk
            # WEB_SESSION_SECRET & WEB_CSRF_SECRET: openssl rand -hex 32)
```

## 4. Transfer dokumen knowledge base (PENTING — tidak ikut git clone)

`knowledge_base/documents/` dan `knowledge_base/enterprise-attack.json` sengaja
di-`.gitignore` (dokumen sumber, bukan kode), jadi **tidak ada** setelah clone
di atas. Tanpa langkah ini, `setup.sh` akan diam-diam skip ingest dan sistem
RAG jalan tanpa basis pengetahuan sama sekali.

Dari laptop (masih di jaringan lab yang sama), copy folder itu ke VPS:

```bash
scp -r knowledge_base/documents ubuntu@192.168.100.129:~/pusdatin-help/knowledge_base/
scp knowledge_base/enterprise-attack.json ubuntu@192.168.100.129:~/pusdatin-help/knowledge_base/
```

## 5. Jalankan aplikasi

```bash
bash scripts/setup.sh
docker compose exec api python scripts/seed_admin.py
```

`scripts/setup.sh` otomatis menjalankan docker compose, migrasi database, dan
ingest knowledge base (dari folder yang sudah di-copy di langkah 4).

## 6. Alur kerja: tetap koding di laptop, deploy ke VPS

```bash
# di laptop — seperti biasa
git add .
git commit -m "..."
git push

# lalu SSH ke VPS untuk deploy versi terbaru
ssh ubuntu@192.168.100.129
cd pusdatin-help
git pull
docker compose up -d --build
```

Bisa disederhanakan jadi satu script `deploy.sh` di VPS:

```bash
#!/bin/bash
set -e
cd ~/pusdatin-help
git pull
docker compose up -d --build
echo "Deploy selesai: $(date)"
```

## 7. Verifikasi

```bash
curl -I https://cyber-helpdesk.plutolab.my.id/api/v1/health
```

Kalau dapat `HTTP/2 200`, aplikasi sudah bisa diakses publik dan siap dipakai
untuk sesi SUS testing.

## Catatan keamanan & file pribadi

- File yang **sengaja tidak ikut** deploy (sudah di `.gitignore`, jangan
  pernah dipaksa commit): `.env` (secrets), `TA (Progress Saya)/`,
  `TA Rujukan/`, `Skill/`, `.superpowers/` (materi pribadi TA), `web_uploads/`
  (lampiran asli dari pelapor — mulai kosong di VPS, itu benar).
- Ganti `WEB_SESSION_SECRET` dan `WEB_CSRF_SECRET` dengan nilai baru khusus
  untuk deployment ini, jangan pakai ulang dari `.env` lokal laptop.
- Password login Proxmox/OS **jangan pernah** ditulis ke file di repo
  (termasuk dokumen ini) — simpan terpisah (password manager/catatan pribadi).
- Setelah masa SUS testing selesai, pertimbangkan matikan container
  (`docker compose down`) supaya server tidak menganggur online tanpa perlu.
