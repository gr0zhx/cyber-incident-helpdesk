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
git clone https://github.com/gr0zhx/cyber-incident-helpdesk.git
cd cyber-incident-helpdesk
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
scp -r knowledge_base/documents ubuntu@192.168.100.129:~/cyber-incident-helpdesk/knowledge_base/
scp knowledge_base/enterprise-attack.json ubuntu@192.168.100.129:~/cyber-incident-helpdesk/knowledge_base/
```

## 5. Jalankan aplikasi

```bash
bash scripts/setup.sh
docker compose exec api python scripts/seed_admin.py
```

`scripts/setup.sh` otomatis menjalankan docker compose, migrasi database, dan
ingest knowledge base (dari folder yang sudah di-copy di langkah 4).

## 6. Alur kerja: dua repo terpisah

Repo kerja sehari-hari (`pusdatin-help`, riwayat commit lengkap) **beda**
dengan repo yang di-clone di VPS (`cyber-incident-helpdesk`, snapshot untuk
deploy). Jadi `git push` biasa ke `pusdatin-help` **tidak** otomatis sampai
ke VPS — perlu satu langkah sync tambahan.

**Sekali saja**, tambahkan remote kedua di repo lokal:

```bash
git remote add deploy https://github.com/gr0zhx/cyber-incident-helpdesk.git
```

Setiap kali siap deploy versi terbaru:

```bash
# 1. Kerja seperti biasa di pusdatin-help
git add .
git commit -m "..."
git push origin main

# 2. Kalau sudah siap di-deploy, mirror ke repo VPS
#    (--force karena riwayat commit kedua repo beda, ini menimpa history
#    cyber-incident-helpdesk supaya selalu sama persis dengan pusdatin-help)
git push deploy main:main --force
```

Setelah langkah 2, VPS akan otomatis `git pull` + rebuild dalam ≤2 menit
(lihat bagian 8) — tidak perlu SSH manual lagi.

**Alternatif kalau bagian 8 (cron) belum dipasang:** SSH manual ke VPS dan
jalankan sendiri:

```bash
ssh ubuntu@192.168.100.129
cd cyber-incident-helpdesk
git pull
docker compose up -d --build
```

## 7. Verifikasi

```bash
curl -I https://cyber-helpdesk.plutolab.my.id/api/v1/health
```

Kalau dapat `HTTP/2 200`, aplikasi sudah bisa diakses publik dan siap dipakai
untuk sesi SUS testing.

## 8. Auto-deploy: push dari laptop, server update sendiri

Karena VPS berada di jaringan lab (GitHub tidak bisa SSH masuk), auto-deploy
memakai pola **pull-based**: cron job di VPS mengecek GitHub tiap 2 menit dan
otomatis pull + rebuild kalau ada commit baru.

Setup satu kali di VPS:

```bash
# 1. Pastikan script deploy bisa dieksekusi
chmod +x ~/cyber-incident-helpdesk/scripts/auto_deploy.sh

# 2. Daftarkan ke cron (cek tiap 2 menit)
( crontab -l 2>/dev/null; echo "*/2 * * * * /home/ubuntu/cyber-incident-helpdesk/scripts/auto_deploy.sh" ) | crontab -

# 3. Verifikasi cron terpasang
crontab -l
```

Setelah itu alur kerja sehari-hari cukup dari laptop:

```bash
git add . && git commit -m "..." && git push
# tunggu maksimal 2 menit — server otomatis pull + rebuild
```

Cek riwayat deploy di VPS: `cat ~/auto_deploy.log`

Catatan:

- Script memakai lock file, jadi build yang lama tidak akan tumpang tindih
  dengan pengecekan berikutnya.
- `git pull --ff-only` berarti kalau history di GitHub di-force-push, deploy
  berhenti dengan error di log — sengaja, supaya server tidak menimpa dirinya
  dengan history yang aneh. Perbaiki manual dengan SSH kalau itu terjadi.
- Perubahan pada `.env` atau `knowledge_base/documents/` **tidak** ikut
  auto-deploy (tidak ada di git) — untuk itu tetap perlu `scp`/SSH manual,
  lalu jalankan ulang ingest bila dokumen berubah.

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
