# LEMBAR VALIDASI GROUND TRUTH

## Evaluasi Sistem Helpdesk Keamanan Siber Berbasis RAG — Pusdatin Kementan

**Peneliti:** Agry Zharfa
**Lokus Validasi:** Tim Keamanan Siber dan Perlindungan Data Pribadi, Pusdatin Kementan
**Tanggal:** _________________
**Total Pertanyaan:** 20 (10 NIST SP 800-61 + 10 MITRE ATT&CK)

---

## Tujuan

Lembar ini digunakan untuk memvalidasi *ground truth* (jawaban referensi) yang akan dipakai mengevaluasi performa sistem RAG (Retrieval-Augmented Generation) helpdesk keamanan siber. Hasil validasi akan menjadi dasar perhitungan metrik **RAGAS** (Context Relevance, Answer Relevance, Faithfulness).

## Knowledge Base Sistem

Sistem hanya memiliki dua dokumen di basis pengetahuannya:

1. **NIST SP 800-61 Rev 2** — *Computer Security Incident Handling Guide*
2. **MITRE ATT&CK** — Framework taktik, teknik, dan mitigasi serangan siber

Mengikuti praktik penelitian sebelumnya (Aufar 2025, lokus LSPro), distribusi pertanyaan = **10 per dokumen**.

## Petunjuk Pengisian

1. Bacalah **Pertanyaan** dan **Jawaban Referensi (Draft)** pada setiap entri.
2. Pada kolom **Penilaian**, pilih salah satu:
   - **[Setuju]** — jawaban referensi sudah sesuai dengan praktik dan konteks Pusdatin Kementan.
   - **[Perlu Revisi]** — substansi sebagian benar tetapi perlu disesuaikan.
   - **[Tidak Sesuai]** — jawaban referensi tidak akurat atau tidak relevan.
3. Pada kolom **Koreksi/Catatan**, tuliskan revisi atau tambahan informasi sesuai SOP internal.
4. Pertanyaan tambahan dari Bapak/Ibu yang lebih relevan dengan kebutuhan operasional dapat dituliskan pada bagian **Lampiran** di akhir lembar.

---

## BLOK A — NIST SP 800-61 (10 Pertanyaan)

### QA-N01 — Preparation

**Pertanyaan:** Apa saja komponen utama yang perlu dipersiapkan organisasi pada fase preparation incident response?

**Jawaban Referensi (Draft):**
Preparation mencakup: (1) pembentukan tim respons dengan pembagian peran yang jelas (di Pusdatin Kementan: SOC sebagai penerima awal, Tim Keamanan Siber & PDP sebagai analis dan koordinator, Tim Infrastruktur untuk takedown/buka blokir aset, Tim Aplikasi untuk perbaikan); (2) penyusunan kebijakan, prosedur, dan playbook penanganan insiden; (3) penyediaan tools (SIEM, kit forensik, jalur komunikasi aman, jump bag); (4) pelatihan tim dan awareness pegawai; (5) kontrol pencegahan teknis: patching, hardening, segmentasi jaringan.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N02 — Preparation

**Pertanyaan:** Apa pembagian peran tim saat menangani insiden keamanan siber di lingkungan organisasi pemerintah?

**Jawaban Referensi (Draft):**
Tim SOC menerima laporan awal dari internal/eksternal dan melakukan triase. Tim Keamanan Siber & PDP melakukan analisis (identifikasi malware, scanning, Vulnerability Assessment), mengoordinasikan respons, dan melakukan validasi pasca-perbaikan. Tim Infrastruktur melaksanakan takedown aset terdampak dan membuka blokir setelah validasi aman. Tim Aplikasi/pemilik sistem melakukan perbaikan teknis. CSIRT (jika dilibatkan) berperan koordinatif untuk eskalasi serta red/blue teaming, bukan perbaikan langsung pada sistem.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N03 — Detection & Analysis

**Pertanyaan:** Apa saja sumber atau precursor yang dapat menjadi indikator awal terjadinya insiden keamanan?

**Jawaban Referensi (Draft):**
Indikator dapat berasal dari: alert SIEM/IDS/IPS, alert antivirus/EDR, log autentikasi anomali (waktu, lokasi, gagal berulang), laporan pegawai melalui helpdesk/SOC, notifikasi pihak ketiga (vendor, BSSN, regulator), monitoring trafik jaringan tidak normal, perubahan integritas file pada sistem kritis, serta hasil pemantauan OSINT/dark-web atas data instansi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N04 — Detection & Analysis

**Pertanyaan:** Bagaimana cara memprioritaskan tingkat keparahan suatu insiden keamanan?

**Jawaban Referensi (Draft):**
Prioritas ditentukan dari kombinasi tiga aspek: (1) functional impact terhadap layanan (none/low/medium/high/kritis); (2) information impact terhadap data (kerahasiaan/integritas/ketersediaan, termasuk apakah data pribadi terdampak); (3) recoverability (waktu dan sumber daya yang dibutuhkan untuk pulih). Insiden kritis = layanan publik mati total, ransomware aktif, atau kebocoran data sensitif massal. Hasil ini menentukan SLA respons dan eskalasi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N05 — Detection & Analysis

**Pertanyaan:** Apa saja informasi minimum yang harus didokumentasikan dalam tiket insiden keamanan?

**Jawaban Referensi (Draft):**
Minimal: (1) timestamp deteksi dan timestamp laporan; (2) sumber laporan (SOC, pegawai, pihak eksternal); (3) deskripsi insiden; (4) sistem/aset terdampak; (5) jenis insiden (jika sudah teridentifikasi); (6) severity awal; (7) indikator kompromi (IoC) yang ditemukan; (8) tindakan yang sudah dilakukan beserta PIC; (9) status saat ini. Kronologi diperbarui terus sampai tiket ditutup, dan referensi bukti (log, screenshot, image forensik) disimpan terpisah.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N06 — Containment, Eradication & Recovery

**Pertanyaan:** Apa perbedaan short-term containment dan long-term containment, dan kapan masing-masing digunakan?

**Jawaban Referensi (Draft):**
Short-term containment = tindakan cepat menghentikan dampak (di Pusdatin: permohonan takedown aset oleh Tim Infrastruktur, isolasi host dari jaringan, blokir IP/domain di firewall). Long-term containment = solusi sementara yang stabil sebelum perbaikan tuntas (mis. patching darurat, menjalankan sistem cadangan/standby). Pemilihan tergantung kritikalitas layanan, ketersediaan workaround, dan estimasi waktu eradikasi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N07 — Containment, Eradication & Recovery

**Pertanyaan:** Apa langkah eradikasi setelah serangan malware atau ransomware berhasil dikontain?

**Jawaban Referensi (Draft):**
(1) Identifikasi seluruh artefak malware: file, entry registry, scheduled task, mekanisme persistence; (2) hapus malware dari semua host yang terdampak; (3) tutup vektor masuk: patch vulnerability yang dieksploitasi, ubah seluruh kredensial yang berpotensi bocor, revoke token/sesi; (4) lakukan vulnerability assessment ulang oleh Tim KS-PDP; (5) verifikasi tidak ada lateral movement atau backdoor yang tersisa sebelum lanjut ke recovery.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N08 — Containment, Eradication & Recovery

**Pertanyaan:** Apa yang harus dipastikan sebelum sistem yang terdampak dikembalikan ke produksi?

**Jawaban Referensi (Draft):**
Sistem harus melalui: (1) clean restore dari backup yang terverifikasi atau rebuild penuh dari image bersih; (2) full scanning dan vulnerability assessment ulang oleh Tim KS-PDP; (3) validasi keamanan formal dan dokumentasi hasilnya; (4) monitoring intensif paska-recovery (24-72 jam) untuk mendeteksi reinfection; (5) baru kemudian Tim Infrastruktur diminta untuk membuka blokir agar aplikasi bisa live kembali. Jika perbaikan tidak memungkinkan, lakukan restore backup lalu scanning + VA ulang sebelum live.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N09 — Post-Incident Activity

**Pertanyaan:** Apa tujuan dan agenda lessons-learned meeting setelah insiden ditutup?

**Jawaban Referensi (Draft):**
Tujuan: mengevaluasi penyebab insiden, efektivitas respons, dan kesenjangan kontrol/proses. Agenda mencakup: kronologi lengkap, apa yang berjalan baik, apa yang gagal, gap pada tools/playbook/SDM, serta rekomendasi konkret (update playbook, kebijakan, training, kontrol teknis, pengajuan budget). Sebaiknya dilakukan dalam 1-2 minggu setelah penutupan, melibatkan SOC, Tim KS-PDP, Tim Infrastruktur, dan Tim Aplikasi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N10 — Post-Incident Activity

**Pertanyaan:** Berapa lama bukti insiden (log, image forensik, artefak) harus disimpan organisasi?

**Jawaban Referensi (Draft):**
Mengikuti kebijakan retensi bukti organisasi dan regulasi yang berlaku. Untuk instansi pemerintah Indonesia, minimal sampai investigasi selesai dan kewajiban pelaporan ke instansi pengawas (mis. BSSN) terpenuhi. Umumnya 1-3 tahun, lebih lama jika ada potensi proses hukum, audit, atau insiden bersifat strategis. Bukti disimpan dengan chain of custody yang terdokumentasi dan akses yang dibatasi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

## BLOK B — MITRE ATT&CK (10 Pertanyaan)

### QA-M01 — Phishing (T1566)

**Pertanyaan:** Apa saja sub-teknik utama dari Phishing (T1566) menurut MITRE ATT&CK dan mitigasi yang direkomendasikan?

**Jawaban Referensi (Draft):**
Sub-teknik utama: (1) Spearphishing Attachment (T1566.001) — lampiran malicious; (2) Spearphishing Link (T1566.002) — tautan ke situs malicious atau credential harvesting; (3) Spearphishing via Service (T1566.003) — via WhatsApp, Telegram, LinkedIn yang sering bypass kontrol email gateway. Mitigasi yang dipetakan ATT&CK: M1017 User Training, M1031 Network Intrusion Prevention, M1049 Antivirus/Antimalware, M1054 Software Configuration (mis. disable macro).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M02 — Phishing (T1566.002)

**Pertanyaan:** Apa langkah mitigasi yang direkomendasikan MITRE ATT&CK untuk Spearphishing Link (T1566.002)?

**Jawaban Referensi (Draft):**
(1) User awareness training mengenali URL palsu dan domain serupa (M1017); (2) email gateway dengan URL rewriting, sandboxing, dan filter ancaman; (3) DNS filtering atau web proxy untuk blok domain malicious yang dikenal; (4) browser isolation untuk akses link yang mencurigakan; (5) MFA pada semua akun agar credential phishing tidak otomatis berakibat takeover. Setiap email mencurigakan dilaporkan ke SOC untuk analisis IoC dan dipush ke control.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M03 — Ransomware (T1486)

**Pertanyaan:** Bagaimana MITRE ATT&CK mendefinisikan Data Encrypted for Impact (T1486) dan apa mitigasinya?

**Jawaban Referensi (Draft):**
T1486 = adversary mengenkripsi data pada sistem atau jaringan untuk menghentikan ketersediaan, biasanya disertai tuntutan tebusan (ransomware). Mitigasi: (1) backup terisolasi (offline/air-gapped) yang diuji restore-nya secara berkala (M1053 Data Backup); (2) behavior monitoring untuk mendeteksi enkripsi massal pada file system; (3) application control / allow-listing untuk mencegah eksekusi binary tidak dikenal; (4) least privilege agar penyebaran lateral terbatas; (5) network segmentation memisahkan zona produksi dan workstation.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M04 — Ransomware (T1490)

**Pertanyaan:** Apa itu Inhibit System Recovery (T1490) dan kenapa sering dikombinasikan dengan ransomware?

**Jawaban Referensi (Draft):**
T1490 = adversary menonaktifkan atau menghapus mekanisme pemulihan (Volume Shadow Copies via vssadmin, restore points, backup catalog, fitur recovery OS) agar korban tidak bisa pulih tanpa membayar tebusan. Mitigasi: backup off-host atau offline yang tidak dapat dijangkau dari host yang dikompromis; pembatasan hak modifikasi terhadap repository backup; monitoring command yang menyentuh vssadmin/wbadmin/bcdedit/wmic; tamper-proof / immutable backup repository.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M05 — Malware (T1204)

**Pertanyaan:** Bagaimana mitigasi User Execution (T1204) yang sering menjadi vektor awal infeksi malware?

**Jawaban Referensi (Draft):**
(1) User awareness training (M1017), terutama bahaya membuka lampiran atau menjalankan file dari sumber tidak dikenal; (2) email gateway dengan sandboxing lampiran sebelum delivery; (3) application control / allow-listing (M1038); (4) disable macro Office secara default dan blok macro dari internet; (5) endpoint detection & response (EDR) untuk menangkap eksekusi mencurigakan paska user click; (6) web proxy untuk blok download executable berisiko.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M06 — Web Defacement (T1491)

**Pertanyaan:** Apa langkah mitigasi MITRE ATT&CK untuk teknik Defacement (T1491) pada server web?

**Jawaban Referensi (Draft):**
(1) Patch dan hardening web server, framework, dan CMS secara rutin (M1051 Update Software); (2) Web Application Firewall (WAF) dengan rule set OWASP Top 10; (3) File Integrity Monitoring (FIM) untuk mendeteksi perubahan file web yang tidak terotorisasi; (4) backup statis konten halaman untuk pemulihan cepat; (5) least privilege pada akun service web dan akun admin CMS; (6) MFA wajib untuk akses panel admin; (7) audit log akses CMS secara berkala.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M07 — DDoS (T1498)

**Pertanyaan:** Apa mitigasi yang direkomendasikan MITRE ATT&CK untuk Network Denial of Service (T1498)?

**Jawaban Referensi (Draft):**
(1) Filter trafik di edge dengan layanan anti-DDoS atau scrubbing center (M1037 Filter Network Traffic); (2) rate limiting dan connection throttling pada layer aplikasi; (3) load balancer dengan auto-scaling untuk menyerap lonjakan trafik; (4) blackhole atau sinkhole IP sumber serangan; (5) koordinasi dengan ISP/penyedia hosting untuk mitigasi upstream sebelum mencapai jaringan instansi; (6) baseline trafik dan alert anomali untuk deteksi dini; (7) playbook komunikasi krisis ke publik jika layanan terganggu.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M08 — Akses Tidak Sah (T1078)

**Pertanyaan:** Bagaimana ATT&CK menyarankan mitigasi penyalahgunaan Valid Accounts (T1078)?

**Jawaban Referensi (Draft):**
(1) Multi-factor authentication wajib pada semua akun, terutama akun admin dan akses jarak jauh (M1032); (2) Privileged Access Management (PAM) dan just-in-time access untuk akun istimewa; (3) monitoring login anomali (lokasi, waktu, perangkat tidak biasa) di SIEM; (4) password policy kuat, rotation berkala, dan deteksi password yang sudah bocor; (5) audit dan review hak akses berkala; (6) immediate offboarding (deaktivasi + revoke token) untuk pegawai keluar atau mutasi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M09 — Kebocoran Data (T1567)

**Pertanyaan:** Apa mitigasi MITRE ATT&CK untuk Exfiltration Over Web Service (T1567)?

**Jawaban Referensi (Draft):**
(1) Web proxy dan DLP yang menginspeksi trafik keluar serta blok upload ke layanan cloud yang tidak resmi (M1057 Data Loss Prevention); (2) network segmentation dan firewall egress rules yang restrictive; (3) monitoring volume transfer ke domain eksternal (alert anomali); (4) restrict akses ke layanan file-sharing publik (mega.nz, anonfiles, pastebin, ngrok, transfer.sh); (5) endpoint DLP untuk klasifikasi dan blok data sensitif berdasarkan label; (6) audit kegiatan upload pada akun cloud resmi instansi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M10 — Brute Force (T1110)

**Pertanyaan:** Apa mitigasi Brute Force (T1110) menurut MITRE ATT&CK?

**Jawaban Referensi (Draft):**
(1) Account lockout policy setelah N kegagalan login berturut-turut (M1027 Password Policies); (2) MFA agar password saja tidak cukup untuk autentikasi (M1032); (3) password policy kuat dan blocking dictionary/breached password; (4) CAPTCHA pada endpoint login publik; (5) rate limiting di IDP atau authentication endpoint; (6) monitoring dan alerting pada lonjakan login gagal di SIEM; (7) minimisasi exposure layanan autentikasi ke internet (gunakan VPN, jump host, atau model zero trust).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

## LAMPIRAN — Pertanyaan Tambahan dari Validator

Bapak/Ibu dapat mengusulkan pertanyaan tambahan yang lebih relevan dengan kebutuhan operasional Tim KS-PDP Pusdatin Kementan. Pertanyaan-pertanyaan ini akan dipertimbangkan untuk memperkaya dataset evaluasi.

| No | Pertanyaan | Jawaban Referensi | Sumber (NIST 800-61 / MITRE ATT&CK) |
|----|------------|-------------------|--------------------------------------|
| 1  |            |                   |                                      |
| 2  |            |                   |                                      |
| 3  |            |                   |                                      |

---

## CATATAN UMUM VALIDATOR

(Komentar terhadap dataset secara keseluruhan, kesesuaian dengan SOP Pusdatin, atau hal lain yang perlu disampaikan kepada peneliti)

_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________

---

## PERNYATAAN VALIDASI

Dengan ini menyatakan bahwa validasi terhadap *ground truth* di atas dilakukan secara objektif berdasarkan pengetahuan teknis dan SOP yang berlaku di Pusdatin Kementan.

<br>

| Peneliti | Validator |
|:--------:|:---------:|
| <br><br><br><br> | <br><br><br><br> |
| **Agry Zharfa** | **( ___________________________ )** |
| Mahasiswa Politeknik Siber dan Sandi Negara | Tim Keamanan Siber dan Perlindungan Data Pribadi<br>Pusdatin Kementan |
