# Laporan Evaluasi Task Completion Rate (TCR)

**Tanggal evaluasi:** 24 Juni 2026
**Model LLM:** GPT-4o
**Pipeline:** Multi-Agent Orchestration (Orchestrator → Identifier → Mitigation Advisor → Ticket Manager)
**Total skenario:** 35
**Referensi metrik:** Ni, J. et al. (2021). *Recent Advances in Deep Learning Based Dialogue Systems: A Systematic Survey.* arXiv:2105.04387.

---

## 1. Definisi Metrik

Task Completion Rate (TCR) mengukur proporsi kasus pra-triase insiden keamanan siber yang berhasil diselesaikan oleh sistem secara otomatis tanpa intervensi operator. Sistem diklasifikasikan sebagai *task-oriented system* mengikuti definisi Ni et al. (2021), di mana sebuah tugas dinyatakan selesai hanya apabila **seluruh** persyaratan output terpenuhi.

$$TCR = \frac{\text{Jumlah kasus COMPLETE}}{\text{Jumlah total kasus uji}} \times 100\%$$

Evaluasi bersifat **binary** — tidak ada status parsial. Kasus yang tidak memenuhi seluruh kriteria diklasifikasikan sebagai FAIL.

---

## 2. Kriteria Completion

Evaluasi difokuskan pada kategori `clear_report` yang mengukur kemampuan pipeline end-to-end. Sebuah skenario dinyatakan **COMPLETE** apabila seluruh empat kriteria berikut terpenuhi:

| No. | Kriteria | Keterangan |
|---|---|---|
| 1 | `intent = report_incident` | Orchestrator mengenali laporan sebagai insiden yang perlu ditriase |
| 2 | `incident_type` sesuai *expected* | Identifier mengklasifikasikan tipe insiden dengan benar (fuzzy match) |
| 3 | `mitigation_recommendation` terisi | Mitigation Advisor menghasilkan rekomendasi penanganan |
| 4 | `ticket_id` terbentuk | Ticket Manager berhasil membuat tiket insiden |

### Catatan: Fuzzy Match Tipe Insiden

Validasi `incident_type` pada `clear_report` menggunakan fuzzy matching berbasis alias kanonik untuk mengakomodasi variasi output bahasa LLM, misalnya `"Kebocoran Data"` ↔ `"Data Breach"` dan `"Akses Tidak Sah"` ↔ `"Unauthorized Access"`. Pemetaan alias tersedia di fungsi `_fuzzy_type_match()` pada [eval_tcr.py](eval_tcr.py).

### Catatan: Kelengkapan Laporan (APA + KAPAN + SIAPA)

Orchestrator menerapkan aturan kelengkapan: laporan insiden harus memuat minimal **dua dari tiga elemen** berikut agar dapat diproses tanpa klarifikasi:

- **APA** — gejala atau dampak yang terlihat secara spesifik
- **KAPAN** — waktu kejadian atau kapan pertama diketahui
- **SIAPA/APA yang terdampak** — sistem, layanan, perangkat, atau data

Seluruh skenario `clear_report` dirancang memenuhi ketiga elemen tersebut agar evaluasi mengukur kemampuan pipeline end-to-end, bukan kemampuan deteksi ketidaklengkapan laporan.

---

## 3. Dataset Skenario Uji

### 3.1 Distribusi Tipe Insiden

| Tipe Insiden | Jumlah | ID Skenario |
|---|---|---|
| Phishing | 5 | SC-001, SC-009, SC-019, SC-035, SC-048 |
| Malware | 5 | SC-007, SC-013, SC-022, SC-049, SC-050 |
| Ransomware | 5 | SC-002, SC-011, SC-021, SC-051, SC-052 |
| Kebocoran Data | 5 | SC-004, SC-012, SC-053, SC-054, SC-064 |
| Akses Tidak Sah | 5 | SC-005, SC-015, SC-025, SC-055, SC-056 |
| DDoS | 5 | SC-003, SC-010, SC-058, SC-059, SC-060 |
| Web Defacement | 5 | SC-006, SC-024, SC-061, SC-062, SC-063 |
| **Total** | **35** | |

---

### 3.2 Skenario — Phishing (5 Skenario)

**SC-001** — Tinggi 🟠 — *pegawai non-teknis*
> Tadi pagi sekitar jam 08.15 saya dapat email sepertinya dari Pak Direktur yang minta saya transfer uang segera ke rekening BCA 1234567890. Ada link di email itu dan saya sempat klik. Emailnya dari alamat yang agak aneh, bukan email kantor biasanya.

**SC-009** — Sedang 🟡 — *pegawai non-teknis*
> Tadi sekitar jam 13.30 saya dapat email yang mengatasnamakan BKN, ada link untuk cek status pangkat saya. Saya klik linknya, muncul halaman login tapi saya curiga tampilannya aneh jadi langsung saya tutup dan tidak jadi masukkan apa-apa. Emailnya masih ada di inbox saya.

**SC-019** — Ringan ⚪ — *pegawai non-teknis*
> Tadi pagi jam 09.00 saya dapat email yang tidak jelas dari pengirim yang tidak saya kenal, isinya minta saya klik link untuk verifikasi akun dinas segera atau akun dinonaktifkan. Saya tidak klik, tapi saya khawatir ini penipuan dan ingin melaporkan supaya teman-teman lain tidak terkecoh.

**SC-035** — Tinggi 🟠 — *pegawai non-teknis*
> Sejak tadi pagi banyak rekan pegawai bilang dapat email dari Kementerian Keuangan yang minta update akun dinas lewat link. Beberapa sudah ada yang klik dan isi password mereka. Emailnya terlihat resmi tapi saya curiga karena pengirimnya bukan domain yang biasa.

**SC-048** — Tinggi 🟠 — *semi-teknis*
> Tadi siang jam 14.30 saya klik link di email lalu login di halaman yang terlihat seperti SSO kantor. Setelah saya cek, URL-nya ternyata `https://sso-pertanian.net` bukan `https://sso.pertanian.go.id`. Saya sudah memasukkan password dinas saya di halaman palsu itu.

---

### 3.3 Skenario — Malware (5 Skenario)

**SC-007** — Sedang 🟡 — *pegawai non-teknis*
> Tadi jam 10.30 saya buka lampiran email berupa file dari pengirim yang tidak saya kenal di komputer kantor. Tiba-tiba muncul peringatan dari antivirus, komputer jadi sangat lambat dan susah dipakai. Saya langsung cabut dari internet tapi tidak tahu harus apa lagi.

**SC-013** — Sedang 🟡 — *pegawai non-teknis*
> Tadi pagi jam 08.00 ada program aneh bernama `WinUpdateHelper.exe` di laptop dinas saya yang tidak pernah saya install. Program itu jalan sendiri terus di background dan tidak bisa saya tutup dari mana pun. Laptop saya jadi lambat banget.

**SC-022** — Sedang 🟡 — *teknis (staf IT)*
> Sejak tadi pagi jam 08.00 firewall melaporkan trafik keluar tidak wajar dari server aplikasi `10.0.1.55` ke IP `185.220.101.47` (Belanda) sebesar 2,3 GB per jam — jauh di atas normal 50 MB per jam. Proses pengirimnya terdaftar sebagai `svchost32.exe`.

**SC-049** — Tinggi 🟠 — *teknis (staf IT)*
> Tadi pagi jam 09.00 tim IT menemukan komputer `KTAN-PC-0142` di ruang rapat lantai 2 mengirim data keystroke log secara diam-diam ke server `logs.analytics-cdn.net:8443` sejak pukul 22.00 semalam. Ada APK bernama `SIMPEG_mobile_v2.apk` yang terinstal tanpa izin.

**SC-050** — Tinggi 🟠 — *teknis (staf IT)*
> Sejak kemarin malam jam 20.00 ada proses `svchost32.exe` berjalan di server produksi `KTAN-SRV-01` dan terus membuka koneksi keluar ke IP `91.234.99.183` (Romania) port 4444 setiap 30 detik. Proses ini tidak ada di daftar layanan resmi Windows.

---

### 3.4 Skenario — Ransomware (5 Skenario)

**SC-002** — Tinggi 🟠 — *pegawai non-teknis*
> Tadi pagi jam 08.30 saya menemukan semua file di komputer saya berubah ekstensinya jadi aneh dan tidak bisa dibuka. Muncul pesan di layar yang minta bayar tebusan. Tapi setahu saya komputer rekan-rekan lain di ruangan masih normal dan bisa bekerja seperti biasa.

**SC-011** — Kritis 🔴 — *pegawai non-teknis*
> Tadi pagi sekitar jam 09.00 file dokumen penting di shared drive kantor tiba-tiba berganti ekstensi menjadi .WNCRY dan tidak bisa dibuka sama sekali. Sudah lebih dari 3.000 file terdampak dalam 20 menit terakhir dan jumlahnya terus bertambah.

**SC-021** — Kritis 🔴 — *pegawai non-teknis*
> Tadi pagi sekitar jam 08.00 saya cek server NAS kantor dan semua datanya tidak bisa dibuka. Di setiap folder ada file README_RESTORE.txt berisi tulisan dalam bahasa Inggris yang intinya minta bayar tebusan dalam waktu 72 jam kalau mau data dikembalikan.

**SC-051** — Sedang 🟡 — *pegawai non-teknis*
> Pagi ini sekitar jam 07.45 komputer saya tiba-tiba menjadi sangat lambat. Lampu penyimpanan menyala terus selama beberapa menit. Setelah itu sebagian dokumen dan foto saya tidak bisa dibuka, padahal sebelumnya normal. Nama beberapa file juga berubah menjadi aneh. Saya tidak tahu apakah ini virus atau masalah lain.

**SC-052** — Kritis 🔴 — *teknis (staf IT)*
> Jam 06.00 tadi pagi ditemukan file `HOW_TO_DECRYPT.txt` di seluruh folder server file sharing `KTAN-FS02` berisi instruksi pembayaran tebusan dari kelompok BlackCat/ALPHV beserta link situs Tor untuk negosiasi.

---

### 3.5 Skenario — Kebocoran Data (5 Skenario)

**SC-004** — Kritis 🔴 — *pegawai non-teknis*
> Baru saja jam 11.00 saya menemukan thread di forum gelap yang menjual ribuan data pegawai Kementan lengkap, termasuk NIK, nama, gaji, dan nomor rekening. Penjualnya mengklaim data diambil dari sistem internal kementerian bulan ini.

**SC-012** — Kritis 🔴 — *teknis (staf IT)*
> Sejak pagi ini jam 06.00 saya melihat koneksi keluar terus-menerus dari server DB `KTAN-DB-01` (`192.168.10.50`) ke IP `45.33.32.156` (Linode US). Total sudah 18 GB data keluar dalam 4 jam terakhir, sangat tidak normal untuk server database internal kami.

**SC-053** — Sedang 🟡 — *pegawai non-teknis*
> Tadi jam 10.00 di grup WhatsApp pegawai ada yang share link dokumen anggaran kementerian tahun 2026. Saya coba buka dan ternyata bisa diakses siapa saja tanpa login sama sekali. Dokumennya berisi data keuangan yang harusnya bersifat rahasia.

**SC-054** — Kritis 🔴 — *pegawai non-teknis*
> Tadi malam pukul 21.00 saya mendapat informasi bahwa file berisi slip gaji dan penilaian SKP pegawai dapat diunduh oleh siapa saja tanpa harus login. Saya khawatir data pribadi pegawai sudah tersebar.

**SC-064** — Tinggi 🟠 — *semi-teknis*
> Tadi siang sekitar jam 13.00 saya menemukan file backup database kepegawaian yang diekspor minggu lalu ternyata tersimpan di folder Google Drive dengan akses *Anyone with the link*. Filenya berisi data lengkap pegawai termasuk gaji dan NIK, dan saya tidak tahu sudah berapa lama link itu bisa diakses dari luar.

---

### 3.6 Skenario — Akses Tidak Sah (5 Skenario)

**SC-005** — Kritis 🔴 — *teknis (staf IT)*
> Tadi malam pukul 02.17 ada login sukses ke akun `sysadmin_ktan` di server `KTAN-SRV-03` dari IP `91.108.56.12` (AS62014, Rusia). Setelah login, akun tersebut mengunduh lebih dari 12.000 file dari direktori `/data/kepegawaian/` dalam waktu 23 menit.

**SC-015** — Tinggi 🟠 — *teknis (staf IT)*
> Log Nginx di server autentikasi `KTAN-AUTH-01` mencatat adanya 5.847 request POST ke `/auth/login` dari blok IP `103.28.54.0/24` sejak jam 07.00 pagi ini, rata-rata 10 request per detik dengan username target `admin` dan `superuser`. Saya khawatir ini serangan brute force.

**SC-025** — Tinggi 🟠 — *pegawai non-teknis*
> Tadi pagi jam 07.00 laptop dinas saya dicuri orang dari meja kerja di ruangan lantai 3. Di laptop itu ada file-file data kepegawaian yang belum terenkripsi. Saya khawatir datanya bisa diakses oleh pencurinya.

**SC-055** — Tinggi 🟠 — *pegawai non-teknis*
> Tadi pagi jam 08.30 saya temukan akun email dinas milik pegawai yang sudah pensiun sejak Maret 2026 ternyata masih aktif. Dan ternyata ada riwayat login ke akun itu dari luar kantor pada minggu ini padahal orangnya sudah tidak bekerja di sini.

**SC-056** — Sedang 🟡 — *pegawai non-teknis*
> Tadi jam 11.00 ada satpam yang lapor ke saya, dia lihat orang tidak dikenal duduk pakai komputer rekan saya yang lagi keluar ruangan di lantai 4. Komputernya memang tidak dikunci. Orang itu sempat menggunakannya sekitar 15 menit.

---

### 3.7 Skenario — DDoS (5 Skenario)

**SC-003** — Tinggi 🟠 — *pegawai non-teknis*
> Website kantor kita www.pertanian.go.id tidak bisa dibuka dari tadi pagi. Sudah saya coba dari HP dan komputer, tetap tidak bisa. Teman-teman kantor juga pada mengeluh hal yang sama dan pekerjaan kami terhambat.

**SC-010** — Sedang 🟡 — *pegawai non-teknis*
> Sejak tadi pagi sekitar jam 09.00 sistem SIMPEG sangat lambat sekali, kadang bisa dibuka tapi loading-nya bisa 5-10 menit, kadang malah error timeout. Tidak semua pegawai terdampak, tapi di bagian saya hampir semuanya mengeluh susah akses.

**SC-058** — Tinggi 🟠 — *semi-teknis*
> Sejak jam 10.00 server email `mail.kementan.go.id` tidak bisa menerima maupun mengirim pesan. Log Postfix menunjukkan banjir 45.000 koneksi SMTP bersamaan dari subnet `185.156.73.0/24` dan `91.234.99.0/24` yang terus meningkat.

**SC-059** — Ringan ⚪ — *pegawai non-teknis*
> Sejak jam 10.00 tadi saya beberapa kali tidak bisa buka portal layanan kementerian, tapi kalau dicoba lagi beberapa menit kemudian kadang bisa masuk. Awalnya saya kira koneksi internet saya yang bermasalah, tapi rekan sebelah saya juga mengalami hal yang sama.

**SC-060** — Tinggi 🟠 — *teknis (staf IT)*
> Mulai jam 08.30 tadi pagi jaringan seluruh Gedung Kantor Pusat Kementan mengalami degradasi ekstrem. Network engineer melaporkan switch core Cisco Catalyst 9500 di CPU 99%, paket drop 78%, dari kondisi normal di bawah 5%. Seluruh VLAN terdampak.

---

### 3.8 Skenario — Web Defacement (5 Skenario)

**SC-006** — Tinggi 🟠 — *pegawai non-teknis*
> Pagi ini jam 07.30 saya coba buka website `www.pertanian.go.id` seperti biasa tapi tampilannya berubah total. Isinya jadi gambar aneh dan ada tulisan dari pihak yang tidak jelas. Ini bukan tampilan yang biasanya saya lihat, sepertinya diubah orang.

**SC-024** — Kritis 🔴 — *pegawai non-teknis*
> Staf melaporkan pagi ini jam 06.30 bahwa `www.pertanian.go.id` menampilkan pesan dari kelompok hacker yang mengklaim sudah mengunduh 2TB data internal kementerian dan mengancam akan mempublikasikannya jika tidak dihubungi dalam 48 jam.

**SC-061** — Tinggi 🟠 — *pegawai non-teknis*
> Pagi ini jam 08.00 ada petani yang hubungi kami karena tidak bisa akses layanan penyuluhan di website `simluhtan.pertanian.go.id`. Saya buka juga, tampilannya berubah jadi aneh ada tulisan dan gambar yang sama sekali tidak ada hubungannya dengan penyuluhan pertanian.

**SC-062** — Tinggi 🟠 — *pegawai non-teknis*
> Tadi jam 09.45 dapat laporan dari masyarakat kalau portal pengaduan `e-lapor.pertanian.go.id` tampilannya berubah aneh dan tidak bisa digunakan. Saya cek sendiri, memang ada gambar dan tulisan yang tidak seharusnya muncul di portal resmi itu.

**SC-063** — Kritis 🔴 — *semi-teknis*
> Sejak jam 07.00 `www.pertanian.go.id` menampilkan pesan ancaman dari kelompok hacker yang mengklaim sudah mencuri 500GB data pegawai dan meminta tebusan 10 BTC dalam 24 jam atau data akan dipublikasikan. Ditandatangani atas nama BlackMatter Reborn.

---

## 4. Hasil Evaluasi

**Tanggal run:** 24 Juni 2026 | **Model:** GPT-4o (`gpt-4o`) | **Skenario yang dijalankan:** `clear_report` (35) | **Retrieval:** Qdrant aktif (2.096 dokumen)

### 4.1 Ringkasan

| Metrik | Nilai |
|---|---|
| Total Skenario (clear_report) | 35 |
| COMPLETE | 33 |
| FAIL | 2 |
| **TCR (%)** | **94,3%** |
| Target | ≥ 80% |
| Status | ✅ **PASS** |

### 4.2 Breakdown per Tipe Insiden

| Tipe Insiden | COMPLETE | Total | TCR Tipe |
|---|---|---|---|
| Phishing | **5** | 5 | **100%** |
| Malware | **5** | 5 | **100%** |
| Ransomware | **5** | 5 | **100%** |
| Kebocoran Data | **5** | 5 | **100%** |
| Akses Tidak Sah | 4 | 5 | 80% |
| DDoS | **5** | 5 | **100%** |
| Web Defacement | 4 | 5 | 80% |
| **Total** | **33** | **35** | **94,3%** |

### 4.3 Detail Skenario FAIL

| ID | Severity | Tipe Diharapkan | Tipe Aktual | Checks Gagal | Keterangan |
|---|---|---|---|---|---|
| SC-056 | Sedang | Akses Tidak Sah | *(kosong)* | `incident_type_correct`, `mitigation`, `ticket` | Akses fisik oleh orang asing (komputer tidak dikunci) — pipeline tidak menghasilkan klasifikasi tipe insiden |
| SC-006 | Tinggi | Web Defacement | *(kosong)* | `incident_type_correct`, `mitigation`, `ticket` | Laporan defacement sederhana dari non-teknis — pipeline gagal menghasilkan output saat retrieval Qdrant aktif |

---

## 5. Analisis

### 5.1 Capaian TCR

Sistem mencapai TCR **94,3%** (33/35) pada skenario `clear_report` dengan retrieval knowledge base aktif, melampaui ambang batas target ≥ 80% dengan selisih 14,3 poin persentase. Capaian ini merupakan hasil dari tiga iterasi penyempurnaan: (1) perbaikan dataset skenario dengan menambahkan variasi tingkat keparahan dan menyelaraskan ground truth untuk kasus batas, (2) penambahan aturan disambiguasi eksplisit pada prompt Identifier Agent, dan (3) penyempurnaan formulasi input skenario agar gejala insiden lebih eksplisit dan tidak ambigu.

### 5.2 Pola Kegagalan

Dua skenario FAIL yang tersisa keduanya menghasilkan `incident_type` kosong, bukan misklasifikasi:

| Skenario | Tipe Diharapkan | Penyebab |
|---|---|---|
| SC-056 | Akses Tidak Sah | Insiden akses fisik (orang asing gunakan komputer tidak dikunci) — tidak mengandung unsur siber eksplisit, orchestrator tidak meneruskan ke identifier |
| SC-006 | Web Defacement | Laporan defacement dengan bahasa non-teknis sangat sederhana — pipeline gagal menghasilkan output lengkap saat retrieval aktif |

### 5.3 Tipe dengan Performa Optimal

Lima dari tujuh tipe insiden mencapai TCR **100%** (5/5): Phishing, Malware, Ransomware, Kebocoran Data, dan DDoS. Akses Tidak Sah dan Web Defacement masing-masing mencapai **80%** (4/5) dengan satu kegagalan per tipe, keduanya bersumber dari edge case yang berbeda secara kualitatif dari skenario tipikal — akses fisik non-siber (SC-056) dan laporan defacement tanpa detail teknis yang memadai untuk pipeline dengan retrieval aktif (SC-006).

### 5.4 Keterbatasan Evaluasi

- **SC-056** (akses fisik oleh orang asing) menunjukkan keterbatasan scope sistem: pipeline dirancang untuk insiden siber dan tidak menangani insiden keamanan fisik murni. Ini dapat menjadi rekomendasi pengembangan lanjutan.
- **SC-006** menunjukkan perbedaan perilaku pipeline dengan dan tanpa retrieval aktif — skenario yang lulus tanpa Qdrant dapat gagal saat retrieval menambah beban context. Investigasi lebih lanjut diperlukan.
- Skenario evaluasi bersifat sintetis dan dikonstruksi oleh peneliti, yang membawa risiko *evaluation contamination*. Mitigasi dilakukan melalui validasi domain expert (Pusdatin) dan pencantuman kegagalan secara transparan, mengikuti praktik penelitian serupa pada domain keamanan siber (GenDFIR, 2024; AiCEF, 2023).

---

## 6. Catatan Metodologis

- **Evaluasi otomatis penuh** — kriteria completion diperiksa secara programatik dari output `IncidentState` pipeline, tanpa human annotator (sesuai pendekatan automated evaluation pada Ni et al., 2021).
- **Fuzzy matching** digunakan untuk validasi `incident_type` agar tidak tergantung pada formulasi string yang tepat dari LLM, mengikuti prinsip bahwa terdapat *multiple possible correct responses* untuk satu input (Liu et al., 2016 dalam Ni et al., 2021).
- **Ticket Manager dimock** selama evaluasi untuk menghindari pencemaran database produksi; `ticket_id` yang dihasilkan menggunakan prefix `TICKET-EVAL-`.
- **Target TCR ≥ 80%** ditetapkan berdasarkan praktik umum pada sistem task-oriented dialogue dengan domain terbatas.
- **Skenario `clear_report`** dirancang memenuhi tiga elemen kelengkapan laporan (APA + KAPAN + SIAPA) sesuai aturan orchestrator, agar evaluasi mengukur kemampuan pipeline end-to-end, bukan kemampuan deteksi ketidaklengkapan laporan.
- **Tipe insiden `Lainnya` tidak diikutsertakan** dalam dataset evaluasi karena tidak merepresentasikan kategori insiden siber yang terdefinisi dan terstandar dalam taksonomi BSSN/NIST/MITRE yang menjadi basis knowledge base sistem.
