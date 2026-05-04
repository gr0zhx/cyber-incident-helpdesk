# LEMBAR VALIDASI GROUND TRUTH

## Evaluasi Sistem Helpdesk Keamanan Siber Berbasis RAG — Pusdatin Kementan

**Peneliti:** Agry Zharfa
**Lokus Validasi:** Tim Keamanan Siber dan Perlindungan Data Pribadi, Pusdatin Kementan
**Tanggal:** _________________
**Total Pertanyaan:** 20 (10 NIST SP 800-61 + 10 MITRE ATT&CK)

---

## Tujuan

Lembar ini digunakan untuk memvalidasi *ground truth* (jawaban referensi) yang akan dipakai untuk mengevaluasi performa sistem RAG (Retrieval-Augmented Generation) helpdesk keamanan siber. Pertanyaan dibuat menyerupai pertanyaan yang akan diajukan pegawai/staf Pusdatin di lapangan, sehingga representatif terhadap pemakaian nyata. Hasil validasi akan menjadi dasar perhitungan metrik **RAGAS** (Context Relevance, Answer Relevance, Faithfulness).

## Knowledge Base Sistem

Sistem hanya memiliki dua dokumen di basis pengetahuannya:

1. **NIST SP 800-61 Rev 2** — *Computer Security Incident Handling Guide*
2. **MITRE ATT&CK** — Framework taktik, teknik, dan mitigasi serangan siber

Mengikuti praktik penelitian sebelumnya (Aufar 2025, lokus LSPro), distribusi pertanyaan = **10 per dokumen**.

## Petunjuk Pengisian

1. Bacalah **Pertanyaan** dan **Jawaban Referensi (Draft)** pada setiap entri.
2. Pada kolom **Penilaian**, pilih salah satu:
   - **[Setuju]** — jawaban sudah sesuai dengan praktik dan konteks Pusdatin Kementan.
   - **[Perlu Revisi]** — substansi sebagian benar tetapi perlu disesuaikan.
   - **[Tidak Sesuai]** — jawaban tidak akurat atau tidak relevan.
3. Pada kolom **Koreksi/Catatan**, tuliskan revisi atau tambahan informasi sesuai SOP internal.
4. Pertanyaan tambahan dari Bapak/Ibu yang lebih relevan dengan kebutuhan operasional dapat dituliskan pada bagian **Lampiran** di akhir lembar.

---

## BLOK A — NIST SP 800-61 (10 Pertanyaan)

### QA-N01 — Preparation

**Pertanyaan:** Kalau kita mau bentuk tim incident response dari nol, apa aja yang harus disiapkan duluan?

**Jawaban Referensi (Draft):**
Hal-hal dasar yang harus ada sebelum insiden datang: pembentukan tim respons dengan pembagian peran yang jelas (di Pusdatin: SOC sebagai penerima awal, Tim Keamanan Siber & PDP sebagai analis dan koordinator, Tim Infrastruktur untuk takedown/buka blokir, Tim Aplikasi untuk perbaikan), kebijakan dan playbook penanganan, tools (SIEM, kit forensik, jalur komunikasi aman), pelatihan tim dan awareness pegawai, plus kontrol pencegahan teknis seperti patching, hardening, dan segmentasi jaringan.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N02 — Preparation

**Pertanyaan:** Kalau ada insiden masuk, siapa yang harusnya pegang apa? Bingung kalau timnya banyak begini.

**Jawaban Referensi (Draft):**
Pembagian peran biasanya: SOC menerima laporan awal dan triase, Tim Keamanan Siber & PDP melakukan analisis (identifikasi malware, scanning, VA), koordinasi respons, dan validasi pasca-perbaikan. Tim Infrastruktur eksekusi takedown dan buka blokir aset setelah aman. Tim Aplikasi/pemilik sistem yang melakukan perbaikan teknis. CSIRT (kalau dilibatkan) lebih ke koordinatif untuk eskalasi dan red/blue teaming, bukan perbaikan langsung.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N03 — Detection & Analysis

**Pertanyaan:** Dari mana biasanya kita tahu kalau ada insiden? Kadang dapat alert, kadang dapat laporan pegawai — mana yang lebih bisa dipercaya?

**Jawaban Referensi (Draft):**
Indikator insiden bisa datang dari banyak sumber: alert SIEM/IDS/IPS, alert antivirus/EDR, log autentikasi anomali (waktu/lokasi/gagal berulang), laporan pegawai via helpdesk, notifikasi pihak ketiga (vendor, BSSN, regulator), monitoring trafik tidak normal, perubahan integritas file sistem kritis, atau pemantauan OSINT/dark-web. Semua sumber valid; analis harus melakukan korelasi dan verifikasi sebelum eskalasi — laporan pegawai tidak boleh diabaikan, alert otomatis tidak boleh ditelan mentah.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N04 — Detection & Analysis

**Pertanyaan:** Tadi ada dua tiket masuk yang sama-sama kelihatan urgent, cara nentuin mana yang harus ditangani duluan gimana?

**Jawaban Referensi (Draft):**
Prioritas insiden ditentukan dari tiga aspek: (1) functional impact ke layanan (none/low/medium/high/kritis), (2) information impact ke data (kerahasiaan/integritas/ketersediaan, terutama kalau menyangkut data pribadi), dan (3) recoverability (waktu dan sumber daya buat pulih). Insiden kritis = layanan publik mati total, ransomware aktif, atau data sensitif massal terekspos — ini didahulukan. Hasil prioritisasi menentukan SLA respons dan jalur eskalasi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N05 — Detection & Analysis

**Pertanyaan:** Tiket insiden yang dibuat sering kosong-kosong informasinya, idealnya isiannya apa aja sih?

**Jawaban Referensi (Draft):**
Minimal harus ada: timestamp deteksi dan timestamp laporan, sumber laporan (SOC/pegawai/eksternal), deskripsi insiden, sistem/aset terdampak, jenis insiden kalau sudah teridentifikasi, severity awal, indikator kompromi (IoC) yang ditemukan, tindakan yang sudah dilakukan beserta PIC, dan status saat ini. Kronologi diperbarui terus sampai tiket ditutup, dan referensi bukti (log, screenshot, image forensik) disimpan terpisah dengan chain of custody.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N06 — Containment, Eradication & Recovery

**Pertanyaan:** Bedanya containment yang sebentar sama yang panjang itu apa? Kapan harus pakai yang mana?

**Jawaban Referensi (Draft):**
Short-term containment = tindakan cepat menghentikan dampak — mis. permohonan takedown aset oleh Tim Infrastruktur, isolasi host dari jaringan, blokir IP/domain di firewall. Long-term containment = solusi sementara yang lebih stabil sebelum perbaikan tuntas — mis. patching darurat, menjalankan sistem cadangan/standby. Pilihan tergantung kritikalitas layanan, ada tidaknya workaround, dan estimasi waktu sampai eradikasi tuntas.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N07 — Containment, Eradication & Recovery

**Pertanyaan:** Workstation yang kena malware udah berhasil diisolasi, langkah lanjutnya gimana biar bener-bener bersih?

**Jawaban Referensi (Draft):**
Tahap eradikasi: (1) identifikasi seluruh artefak malware (file, entry registry, scheduled task, mekanisme persistence), (2) hapus malware dari semua host yang terdampak, (3) tutup vektor masuk — patch vulnerability yang dieksploitasi, ubah seluruh kredensial yang berpotensi bocor, revoke token/sesi, (4) lakukan vulnerability assessment ulang oleh Tim KS-PDP, (5) verifikasi tidak ada lateral movement atau backdoor yang tersisa sebelum lanjut ke recovery.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N08 — Containment, Eradication & Recovery

**Pertanyaan:** Server yang kena insiden kemarin sudah diperbaiki tim aplikasi. Sebelum kita live-kan lagi, syaratnya apa aja?

**Jawaban Referensi (Draft):**
Sebelum live: (1) clean restore dari backup terverifikasi atau rebuild penuh dari image bersih, (2) full scanning dan VA ulang oleh Tim KS-PDP, (3) validasi keamanan formal dengan dokumentasi hasilnya, (4) monitoring intensif paska-recovery (24-72 jam) untuk deteksi reinfection, (5) baru kemudian Tim Infrastruktur diminta buka blokir agar aplikasi live kembali. Kalau perbaikan tidak memungkinkan, lakukan restore backup dulu lalu scanning + VA ulang sebelum live.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N09 — Post-Incident Activity

**Pertanyaan:** Setelah insiden ditutup, perlu meeting evaluasi gak sih? Kalau perlu, bahasnya apa aja?

**Jawaban Referensi (Draft):**
Lessons-learned meeting penting untuk mengevaluasi penyebab insiden, efektivitas respons, dan kesenjangan kontrol/proses. Agenda: kronologi lengkap, apa yang berjalan baik, apa yang gagal, gap pada tools/playbook/SDM, dan rekomendasi konkret (update playbook, kebijakan, training, kontrol teknis, pengajuan budget). Idealnya dilakukan 1-2 minggu setelah penutupan, melibatkan SOC, Tim KS-PDP, Tim Infrastruktur, dan Tim Aplikasi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-N10 — Post-Incident Activity

**Pertanyaan:** Log dan image forensik insiden kemarin sampai kapan harus disimpan? Sayang kalau kelamaan makan storage.

**Jawaban Referensi (Draft):**
Retensi mengikuti kebijakan internal organisasi dan regulasi yang berlaku. Untuk instansi pemerintah Indonesia, minimal sampai investigasi selesai dan kewajiban pelaporan ke instansi pengawas (mis. BSSN) terpenuhi. Praktik umum 1-3 tahun, lebih lama kalau ada potensi proses hukum, audit, atau insiden bersifat strategis. Bukti disimpan dengan chain of custody yang terdokumentasi dan akses terbatas, sehingga storage cost tidak boleh jadi alasan menghapus prematur.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

## BLOK B — MITRE ATT&CK (10 Pertanyaan)

### QA-M01 — Phishing (T1566)

**Pertanyaan:** Phishing itu cuma lewat email aja kan? Atau ada bentuk lain yang perlu diwaspadai?

**Jawaban Referensi (Draft):**
Phishing (T1566) di MITRE ATT&CK punya beberapa sub-teknik: (1) Spearphishing Attachment (T1566.001) — lampiran malicious, (2) Spearphishing Link (T1566.002) — tautan ke situs malicious atau credential harvesting, (3) Spearphishing via Service (T1566.003) — lewat WhatsApp, Telegram, LinkedIn yang sering bypass kontrol email gateway. Mitigasinya: M1017 User Training, M1031 Network Intrusion Prevention, M1049 Antivirus/Antimalware, dan M1054 Software Configuration (mis. disable macro Office).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M02 — Phishing (T1566.002)

**Pertanyaan:** Pegawai sering banget kena email berisi link aneh. Selain ngingetin terus, apa yang bisa dipasang teknisnya biar berkurang?

**Jawaban Referensi (Draft):**
Untuk Spearphishing Link (T1566.002): (1) user awareness training mengenali URL palsu dan domain serupa (M1017), (2) email gateway dengan URL rewriting, sandboxing, dan filter ancaman, (3) DNS filtering atau web proxy untuk blok domain malicious, (4) browser isolation untuk akses link mencurigakan, (5) MFA pada semua akun agar credential phishing tidak otomatis berakibat takeover. Setiap email mencurigakan dilaporkan ke SOC untuk analisis IoC dan dipush ke control.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M03 — Ransomware (T1486)

**Pertanyaan:** Kalau ransomware nyerang dan file-file dienkripsi, kontrol apa yang sebenarnya bisa nahan dampaknya?

**Jawaban Referensi (Draft):**
Data Encrypted for Impact (T1486) = adversary mengenkripsi data sistem/jaringan untuk menghentikan ketersediaan, biasanya disertai tuntutan tebusan. Mitigasi yang bekerja: (1) backup terisolasi (offline/air-gapped) yang diuji restore-nya secara berkala (M1053 Data Backup), (2) behavior monitoring untuk mendeteksi enkripsi massal pada file system, (3) application control / allow-listing biar binary tidak dikenal tidak bisa eksekusi, (4) least privilege agar penyebaran lateral terbatas, (5) network segmentation memisahkan zona produksi dan workstation.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M04 — Ransomware (T1490)

**Pertanyaan:** Katanya ransomware modern juga ngerusak backup. Itu beneran? Kalau iya, gimana cara cegahnya?

**Jawaban Referensi (Draft):**
Bener, ini namanya Inhibit System Recovery (T1490). Adversary menonaktifkan/menghapus mekanisme pemulihan: Volume Shadow Copies via vssadmin, restore points, backup catalog, fitur recovery OS — supaya korban tidak bisa pulih tanpa bayar tebusan. Mitigasi: backup off-host atau offline yang tidak bisa dijangkau dari host yang dikompromis, pembatasan hak modifikasi terhadap repository backup, monitoring command yang menyentuh vssadmin/wbadmin/bcdedit/wmic, dan tamper-proof / immutable backup repository.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M05 — Malware (T1204)

**Pertanyaan:** Banyak malware masuk gara-gara user iseng klik file. Selain ngomelin user, apa yang bisa dipasang biar lebih aman?

**Jawaban Referensi (Draft):**
Untuk User Execution (T1204): (1) user awareness training (M1017), terutama bahaya membuka lampiran/menjalankan file dari sumber tidak dikenal, (2) email gateway dengan sandboxing lampiran sebelum delivery, (3) application control / allow-listing (M1038), (4) disable macro Office secara default dan blok macro dari internet, (5) endpoint detection & response (EDR) untuk menangkap eksekusi mencurigakan paska user click, (6) web proxy untuk blok download executable berisiko.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M06 — Web Defacement (T1491)

**Pertanyaan:** Website kementerian rawan diretas tampilannya. Selain WAF, apa lagi yang bisa kita pasang biar aman dari defacement?

**Jawaban Referensi (Draft):**
Untuk Defacement (T1491): (1) patch dan hardening web server, framework, dan CMS secara rutin (M1051 Update Software), (2) WAF dengan rule set OWASP Top 10, (3) File Integrity Monitoring (FIM) untuk mendeteksi perubahan file web tidak terotorisasi, (4) backup statis konten halaman untuk pemulihan cepat, (5) least privilege pada akun service web dan akun admin CMS, (6) MFA wajib untuk akses panel admin, (7) audit log akses CMS secara berkala.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M07 — DDoS (T1498)

**Pertanyaan:** Lagi diserang DDoS dan trafik membludak, apa aja yang bisa dilakukan biar layanan tetap nyala?

**Jawaban Referensi (Draft):**
Untuk Network Denial of Service (T1498): (1) filter trafik di edge dengan layanan anti-DDoS atau scrubbing center (M1037 Filter Network Traffic), (2) rate limiting dan connection throttling pada layer aplikasi, (3) load balancer dengan auto-scaling untuk menyerap lonjakan trafik, (4) blackhole atau sinkhole IP sumber serangan, (5) koordinasi dengan ISP/penyedia hosting untuk mitigasi upstream, (6) baseline trafik dan alert anomali untuk deteksi dini, (7) playbook komunikasi krisis ke publik kalau layanan terganggu.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M08 — Akses Tidak Sah (T1078)

**Pertanyaan:** Akun pegawai bisa dipakai penyerang kalau passwordnya bocor. Apa yang bisa dipasang biar password doang gak cukup buat masuk?

**Jawaban Referensi (Draft):**
Untuk Valid Accounts (T1078): (1) MFA wajib pada semua akun, terutama akun admin dan akses jarak jauh (M1032), (2) Privileged Access Management (PAM) dan just-in-time access untuk akun istimewa, (3) monitoring login anomali (lokasi/waktu/perangkat tidak biasa) di SIEM, (4) password policy kuat, rotation berkala, dan deteksi password yang sudah bocor, (5) audit dan review hak akses berkala, (6) immediate offboarding (deaktivasi + revoke token) untuk pegawai keluar atau mutasi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M09 — Kebocoran Data (T1567)

**Pertanyaan:** Insider atau attacker bisa upload data internal ke layanan cloud kayak mega atau anonfiles. Cara cegahnya gimana?

**Jawaban Referensi (Draft):**
Untuk Exfiltration Over Web Service (T1567): (1) web proxy dan DLP yang inspeksi trafik keluar serta blok upload ke layanan cloud tidak resmi (M1057 Data Loss Prevention), (2) network segmentation dan firewall egress rules yang restrictive, (3) monitoring volume transfer ke domain eksternal dengan alert anomali, (4) restrict akses ke layanan file-sharing publik (mega.nz, anonfiles, pastebin, ngrok, transfer.sh), (5) endpoint DLP untuk klasifikasi dan blok data sensitif berdasarkan label, (6) audit kegiatan upload pada akun cloud resmi instansi.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

### QA-M10 — Brute Force (T1110)

**Pertanyaan:** Login gagal berkali-kali dari IP yang sama, itu kena brute force ya? Cara cegahnya apa aja?

**Jawaban Referensi (Draft):**
Iya, itu indikasi Brute Force (T1110). Mitigasi: (1) account lockout policy setelah N kegagalan login berturut-turut (M1027 Password Policies), (2) MFA agar password saja tidak cukup untuk autentikasi (M1032), (3) password policy kuat dan blocking dictionary/breached password, (4) CAPTCHA pada endpoint login publik, (5) rate limiting di IDP atau authentication endpoint, (6) monitoring dan alerting pada lonjakan login gagal di SIEM, (7) minimisasi exposure layanan autentikasi ke internet (gunakan VPN, jump host, atau model zero trust).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai
**Koreksi/Catatan:**
_____________________________________________________________________
_____________________________________________________________________

---

## LAMPIRAN — Pertanyaan Tambahan dari Validator

Bapak/Ibu dapat mengusulkan pertanyaan tambahan yang lebih relevan dengan kebutuhan operasional Tim KS-PDP Pusdatin Kementan. Pertanyaan yang sering diajukan pegawai di lapangan akan sangat berharga untuk memperkaya dataset evaluasi.

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
