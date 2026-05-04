# LEMBAR VALIDASI GROUND TRUTH (V5)

## Evaluasi Sistem Helpdesk Keamanan Siber Berbasis RAG - Pusdatin Kementan

**Peneliti:** Agry Zharfa  
**Lokus Validasi:** Tim Keamanan Siber dan Perlindungan Data Pribadi, Pusdatin Kementan  
**Tanggal:** _________________  
**Total Pertanyaan:** 40 (20 NIST SP 800-61 + 20 MITRE ATT&CK)

---

## Tujuan

V5 difokuskan untuk membuat **BLOK B (MITRE ATT&CK)** lebih natural seperti bahasa pelapor/pegawai, serta menambahkan **Saran Mitigasi Awal** yang di-*ground* dari knowledge base `knowledge_base\enterprise-attack.json`.

---

## Knowledge Base Sistem (Sumber Grounding)

1. **NIST SP 800-61 Rev.2** - `knowledge_base\documents\nist.sp.800-61r2.pdf`
2. **NIST SP 800-61 Rev.3** - `knowledge_base\documents\NIST.SP.800-61r3.pdf`
3. **MITRE ATT&CK Enterprise** - `knowledge_base\enterprise-attack.json`

---

## Catatan Versi

- **BLOK A (NIST, 20 pertanyaan)**: direvisi ke gaya pertanyaan pegawai/user non-teknis.
- **BLOK B (MITRE, 20 pertanyaan)**: diperbarui agar lebih realistis + ditambah saran mitigasi awal berbasis KB.

---

## BLOK A - NIST SP 800-61 (20 Pertanyaan, Versi Pegawai/User)

### QA-N01 - Preparation
**Pertanyaan:** Kalau saya lihat hal aneh di laptop kantor, saya harus lapor ke mana dulu?

**Jawaban Referensi (Draft):** Lapor secepatnya ke kanal resmi helpdesk/SOC yang ditetapkan instansi. Jalur pelaporan harus jelas agar laporan cepat masuk ke tim yang tepat dan bisa langsung ditriase.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.1 (Preparation), §3.2.7 (Incident Notification).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N02 - Preparation
**Pertanyaan:** Kalau kejadian malam atau hari libur, tetap bisa lapor atau nunggu jam kerja?

**Jawaban Referensi (Draft):** Tetap lapor segera melalui kanal darurat yang sudah disiapkan. Respons insiden butuh jalur komunikasi yang bisa dipakai kapan saja, terutama untuk kejadian berdampak tinggi.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.1.1 (Preparing to Handle Incidents).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N03 - Preparation
**Pertanyaan:** Pas mau lapor, info minimum apa yang harus saya sampaikan supaya tim cepat paham?

**Jawaban Referensi (Draft):** Minimal sebutkan waktu kejadian, perangkat/akun yang terdampak, gejala yang terlihat, dan tindakan yang sudah dilakukan. Kalau ada bukti awal (screenshot/pesan error), sertakan.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2.5 (Incident Documentation).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N04 - Preparation
**Pertanyaan:** Kalau panik, boleh nggak saya langsung matikan laptop/HP kantor yang kena?

**Jawaban Referensi (Draft):** Jangan langsung ambil tindakan drastis kecuali ada instruksi resmi. Keputusan isolasi/shutdown perlu mempertimbangkan dampak layanan dan bukti digital.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.1 (Choosing a Containment Strategy), §3.3.2 (Evidence Handling).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N05 - Preparation
**Pertanyaan:** Kalau saya baru curiga tapi belum yakin, tetap perlu lapor?

**Jawaban Referensi (Draft):** Iya, tetap lapor. Indikasi awal dari user penting untuk deteksi dini dan verifikasi oleh analis, meskipun belum ada bukti lengkap.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2.2 (Signs of an Incident), §3.2.3 (Sources of Indicators).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N06 - Detection & Analysis
**Pertanyaan:** Akun saya tiba-tiba login sendiri dari perangkat/lokasi yang bukan saya. Ini harus dianggap serius?

**Jawaban Referensi (Draft):** Ya, ini indikator kuat akses tidak sah. Harus segera diverifikasi dan ditangani untuk mencegah penyalahgunaan lanjutan.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2 (Detection and Analysis), §3.2.2.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N07 - Detection & Analysis
**Pertanyaan:** Saya klik email mencurigakan, tapi belum tahu ada dampak atau tidak. Langkah awal apa?

**Jawaban Referensi (Draft):** Segera lapor, beri detail waktu/link/email yang diklik, dan ikuti instruksi tim respons. Informasi cepat membantu tim menilai dampak dan mencegah penyebaran.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2.3, §3.2.5, §3.2.7.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N08 - Detection & Analysis
**Pertanyaan:** Komputer jadi lambat, muncul pop-up aneh, dan file sulit dibuka. Itu cukup buat dianggap insiden?

**Jawaban Referensi (Draft):** Gejala tersebut bisa jadi indikator insiden dan perlu analisis lanjut. Tim akan korelasi dengan log/alert lain sebelum menetapkan status final insiden.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2.2 (Signs), §3.2.4 (Incident Analysis).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N09 - Detection & Analysis
**Pertanyaan:** Kalau saya salah lapor dan ternyata bukan insiden, apakah itu masalah?

**Jawaban Referensi (Draft):** Tidak masalah. Laporan awal tetap berguna untuk validasi. Lebih baik ada laporan yang diverifikasi daripada insiden terlewat.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2 (verifikasi indikator), §3.2.5 (dokumentasi).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N10 - Detection & Analysis
**Pertanyaan:** Saya lihat dua masalah sekaligus di unit kerja. Tim menentukan prioritasnya pakai apa?

**Jawaban Referensi (Draft):** Prioritas ditentukan dari dampak ke layanan, dampak ke data/informasi, dan tingkat kesulitan pemulihan. Kasus berisiko tinggi biasanya ditangani lebih dulu.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2.6 (Incident Prioritization).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N11 - Containment, Eradication & Recovery
**Pertanyaan:** Kenapa setelah saya lapor, akun saya malah dikunci sementara?

**Jawaban Referensi (Draft):** Penguncian sementara bisa jadi langkah containment untuk mencegah penyalahgunaan lebih lanjut saat investigasi masih berjalan.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.1 (Containment Strategy).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N12 - Containment, Eradication & Recovery
**Pertanyaan:** Kenapa perangkat saya diputus dari jaringan kantor, padahal saya lagi butuh kerja?

**Jawaban Referensi (Draft):** Isolasi perangkat adalah langkah containment untuk mencegah penyebaran ancaman ke sistem lain. Ini biasanya sementara sampai kondisi aman.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.1.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N13 - Containment, Eradication & Recovery
**Pertanyaan:** Kenapa saya diminta jangan hapus email/chat/berkas yang mencurigakan?

**Jawaban Referensi (Draft):** Karena itu bisa jadi bukti digital penting. Bukti harus dijaga agar investigasi akurat dan dapat dipertanggungjawabkan.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.2 (Evidence Gathering and Handling).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N14 - Containment, Eradication & Recovery
**Pertanyaan:** Kapan layanan/aplikasi yang sempat ditutup boleh dipakai normal lagi?

**Jawaban Referensi (Draft):** Setelah proses pembersihan dan verifikasi keamanan selesai, celah awal ditutup, dan monitoring pasca-pemulihan dinilai memadai oleh tim penanganan.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.4 (Eradication and Recovery).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N15 - Containment, Eradication & Recovery
**Pertanyaan:** Kalau data kerja saya hilang karena insiden, apakah masih bisa balik?

**Jawaban Referensi (Draft):** Pemulihan data bergantung pada ketersediaan backup yang bersih dan valid. Tim pemulihan akan memprioritaskan data/layanan kritikal sesuai dampak bisnis.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.4.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N16 - Post-Incident Activity
**Pertanyaan:** Kenapa setelah insiden selesai masih ada rapat evaluasi lagi?

**Jawaban Referensi (Draft):** Rapat evaluasi diperlukan untuk melihat apa yang berjalan baik, apa yang kurang, dan perbaikan apa yang wajib dilakukan agar insiden serupa tidak terulang.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.4.1 (Lessons Learned).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N17 - Post-Incident Activity
**Pertanyaan:** Saya diminta isi kronologi detail, padahal kejadian sudah lewat. Untuk apa?

**Jawaban Referensi (Draft):** Kronologi detail membantu analisis akar masalah, penyusunan perbaikan, dan menjadi referensi jika terjadi pola serupa di masa depan.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.4.1, §3.4.2.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N18 - Post-Incident Activity
**Pertanyaan:** Kenapa log dan bukti insiden disimpan lama? Bukannya bikin storage penuh?

**Jawaban Referensi (Draft):** Bukti perlu disimpan sesuai kebijakan agar mendukung audit, investigasi lanjutan, dan pembelajaran organisasi. Retensi diatur agar tetap proporsional dan terkontrol.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.2, §3.4.2.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N19 - Post-Incident Activity
**Pertanyaan:** Setelah kejadian seperti ini, biasanya apa yang diperbaiki biar nggak kejadian lagi?

**Jawaban Referensi (Draft):** Umumnya dilakukan perbaikan SOP/playbook, peningkatan kontrol teknis, pelatihan pengguna, dan pembaruan kebijakan berdasarkan temuan insiden.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.4 (Post-Incident Activity), Rev.3 (continuous improvement orientation).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N20 - Post-Incident Activity
**Pertanyaan:** Dari sisi pegawai, gimana cara tahu insiden ini sudah benar-benar ditutup aman?

**Jawaban Referensi (Draft):** Penutupan insiden dilakukan setelah verifikasi pemulihan selesai, risiko sisa diterima, dan dokumentasi penanganan lengkap. Hasil akhirnya sebaiknya dikomunikasikan ke pihak terdampak.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.4, §3.2.7; Rev.3 (communication and governance).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

## BLOK B - MITRE ATT&CK (20 Pertanyaan, Versi Natural + Mitigasi Awal)

### QA-M01 - Phishing (T1566)
**Pertanyaan:** Saya menerima email yang mengatasnamakan atasan dan meminta saya melakukan login ulang melalui tautan. Apakah ini perlu dilaporkan sebagai dugaan phishing?

**Jawaban Referensi (Draft):** Ya, ini indikasi kuat phishing. Pola mendesak + ajakan klik/login ulang adalah ciri umum upaya pencurian kredensial.

**Saran Mitigasi Awal (Draft):**  
1. Isolasi email dan blok domain/URL mencurigakan di gateway (**M1031 Network Intrusion Prevention**, **M1021 Restrict Web-Based Content**).  
2. Edukasi cepat ke user terdampak agar tidak klik tautan serupa (**M1017 User Training**).  
3. Perkuat filter email dan proteksi endpoint (**M1049 Antivirus/Antimalware**, **M1054 Software Configuration**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1566`; mitigations `M1017, M1021, M1031, M1049, M1054`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M02 - Spearphishing Attachment (T1566.001)
**Pertanyaan:** Saya menerima email dari pengirim yang tidak dikenal dengan lampiran (misalnya "invoice"). Setelah dibuka, perangkat menjadi tidak normal. Apakah ini perlu ditangani sebagai dugaan serangan melalui lampiran berbahaya?

**Jawaban Referensi (Draft):** Ini konsisten dengan spearphishing attachment: file berbahaya disamarkan sebagai dokumen kerja.

**Saran Mitigasi Awal (Draft):**  
1. Karantina endpoint yang membuka lampiran dan hentikan penyebaran file serupa (**M1049 Antivirus/Antimalware**, **M1031 Network Intrusion Prevention**).  
2. Batasi tipe file berisiko tinggi dari email/web (**M1021 Restrict Web-Based Content**).  
3. Sosialisasi ulang prosedur buka lampiran aman (**M1017 User Training**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1566.001`; mitigations `M1017, M1021, M1031, M1049`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M03 - Spearphishing Link (T1566.002)
**Pertanyaan:** Saya membuka tautan "dokumen rapat" lalu diarahkan ke halaman login yang sangat mirip portal resmi kantor. Apakah ini indikasi upaya pencurian kredensial?

**Jawaban Referensi (Draft):** Ya, ini indikasi spearphishing link dengan tujuan mengambil akun/token.

**Saran Mitigasi Awal (Draft):**  
1. Blok URL/domain target dan sebar IOC ke tim terkait (**M1021 Restrict Web-Based Content**).  
2. Wajibkan reset sesi/kredensial akun terdampak dan review aktivitasnya (**M1018 User Account Management**).  
3. Perkuat awareness URL tiruan/homograph (**M1017 User Training**) dan kebijakan konfigurasi browser/email (**M1054 Software Configuration**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1566.002`; mitigations `M1017, M1018, M1021, M1054`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M04 - Spearphishing via Service (T1566.003)
**Pertanyaan:** Saya menerima pesan WhatsApp/Telegram yang mengatasnamakan vendor dan meminta verifikasi akun dinas melalui tautan. Apakah ini termasuk upaya phishing melalui layanan pesan?

**Jawaban Referensi (Draft):** Termasuk. Phishing tidak hanya lewat email, tapi juga lewat layanan pesan pihak ketiga.

**Saran Mitigasi Awal (Draft):**  
1. Terapkan kanal resmi verifikasi identitas pihak eksternal dan larang verifikasi akun lewat chat pribadi (**M1017 User Training**).  
2. Terapkan kontrol akses akun yang lebih ketat (**M1018 User Account Management**).  
3. Tingkatkan proteksi endpoint pengguna terhadap konten berbahaya (**M1049 Antivirus/Antimalware**, **M1021 Restrict Web-Based Content**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1566.003`; mitigations `M1017, M1018, M1021, M1049`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M05 - User Execution (T1204)
**Pertanyaan:** Saya menerima laporan dari pegawai bahwa setelah membuka file tertentu, perangkat menjalankan proses yang tidak dikenal secara otomatis. Dugaan penyebab awal apa yang perlu dipertimbangkan?

**Jawaban Referensi (Draft):** Ini pola User Execution: payload berjalan karena ada aksi pengguna (klik/buka/jalankan).

**Saran Mitigasi Awal (Draft):**  
1. Batasi eksekusi aplikasi tidak dikenal (**M1038 Execution Prevention**, **M1033 Limit Software Installation**).  
2. Aktifkan proteksi perilaku di endpoint (**M1040 Behavior Prevention on Endpoint**).  
3. Edukasi user dan batasi konten web/unduhan berisiko (**M1017 User Training**, **M1021 Restrict Web-Based Content**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1204`; mitigations `M1017, M1021, M1033, M1038, M1040`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M06 - Data Encrypted for Impact (T1486)
**Pertanyaan:** File pada shared drive tiba-tiba tidak dapat diakses dan muncul pesan permintaan tebusan. Langkah awal apa yang sebaiknya saya lakukan sambil menunggu arahan tim?

**Jawaban Referensi (Draft):** Ini indikasi ransomware tipe enkripsi data untuk mengganggu ketersediaan layanan.

**Saran Mitigasi Awal (Draft):**  
1. Isolasi host terdampak dan hentikan proses enkripsi lanjutan (**M1040 Behavior Prevention on Endpoint**).  
2. Siapkan pemulihan dari backup bersih yang terverifikasi (**M1053 Data Backup**).  
3. Bekukan akun/sesi yang dicurigai jadi jalur awal serangan (operasional lokal).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1486`; mitigations `M1040, M1053`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M07 - Inhibit System Recovery (T1490)
**Pertanyaan:** Setelah kejadian ransomware, saya mendapati restore point/backup lokal ikut hilang atau tidak dapat digunakan. Apakah hal tersebut dapat disengaja oleh pelaku?

**Jawaban Referensi (Draft):** Bisa. Pelaku sering menonaktifkan mekanisme recovery agar korban sulit pulih.

**Saran Mitigasi Awal (Draft):**  
1. Lindungi jalur recovery dengan konfigurasi OS yang ketat (**M1028 Operating System Configuration**).  
2. Batasi eksekusi tool/skrip destruktif recovery (**M1038 Execution Prevention**).  
3. Pastikan backup offline/off-host siap dipakai (**M1053 Data Backup**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1490`; mitigations `M1018, M1028, M1038, M1053`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M08 - Defacement (T1491)
**Pertanyaan:** Halaman depan situs web instansi berubah tanpa perubahan resmi dan menampilkan pesan tidak wajar. Apakah ini perlu diprioritaskan sebagai insiden?

**Jawaban Referensi (Draft):** Ya, ini indikasi defacement dan berdampak langsung pada integritas serta reputasi layanan publik.

**Saran Mitigasi Awal (Draft):**  
1. Takedown sementara halaman terdampak dan aktifkan halaman cadangan darurat.  
2. Pulihkan konten dari sumber tepercaya/backup bersih (**M1053 Data Backup**).  
3. Simpan artefak perubahan untuk investigasi lanjutan.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1491`; mitigation `M1053`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M09 - Exploit Public-Facing Application (T1190)
**Pertanyaan:** Aplikasi layanan publik yang menghadap internet menunjukkan indikasi akses tidak sah, sementara tidak ada aktivitas admin yang sah. Kemungkinan jalur masuk yang umum apa?

**Jawaban Referensi (Draft):** Salah satu kemungkinan utama: eksploitasi celah aplikasi publik untuk akses awal.

**Saran Mitigasi Awal (Draft):**  
1. Lakukan scan kerentanan dan patch prioritas kritikal (**M1016 Vulnerability Scanning**).  
2. Segmentasi layanan publik dari jaringan internal (**M1030 Network Segmentation**).  
3. Terapkan filtering trafik dan isolasi aplikasi bila perlu (**M1037 Filter Network Traffic**, **M1048 Application Isolation and Sandboxing**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1190`; mitigations `M1016, M1030, M1037, M1048`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M10 - Network Denial of Service (T1498)
**Pertanyaan:** Trafik jaringan meningkat tajam dari banyak sumber dan layanan menjadi tidak dapat diakses. Apakah indikasinya mengarah ke serangan DDoS?

**Jawaban Referensi (Draft):** Ya, ini sesuai pola Network DoS/DDoS pada kapasitas jaringan.

**Saran Mitigasi Awal (Draft):**  
1. Aktifkan filter trafik/upstream mitigation secepatnya (**M1037 Filter Network Traffic**).  
2. Koordinasi dengan ISP/CDN/scrubbing provider.  
3. Terapkan rate limit sementara pada endpoint kritikal.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1498`; mitigation `M1037`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M11 - Endpoint Denial of Service (T1499)
**Pertanyaan:** Bandwidth jaringan terlihat normal, namun aplikasi/layanan pada server sering hang atau crash akibat request tidak wajar. Apakah ini termasuk serangan DoS pada layanan (bukan saturasi jaringan)?

**Jawaban Referensi (Draft):** Bisa berbeda. Ini cenderung ke endpoint/service DoS, bukan murni saturasi bandwidth jaringan.

**Saran Mitigasi Awal (Draft):**  
1. Terapkan filtering trafik/pola request anomali di perimeter maupun aplikasi (**M1037 Filter Network Traffic**).  
2. Isolasi endpoint terdampak untuk stabilisasi layanan.  
3. Aktifkan proteksi threshold pada service kritikal.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1499`; mitigation `M1037`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M12 - Valid Accounts (T1078)
**Pertanyaan:** Terdapat login berhasil menggunakan akun pegawai, tetapi pemilik akun menyatakan tidak pernah melakukan login. Apakah ini perlu diperlakukan sebagai dugaan kompromi akun?

**Jawaban Referensi (Draft):** Ya, ini indikasi penyalahgunaan akun valid.

**Saran Mitigasi Awal (Draft):**  
1. Nonaktifkan sementara/suspend sesi aktif akun terdampak (**M1018 User Account Management**).  
2. Perketat kebijakan password dan kredensial (**M1027 Password Policies**).  
3. Tinjau hak akses istimewa akun terkait (**M1026 Privileged Account Management**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1078`; mitigations `M1018, M1026, M1027`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M13 - Cloud Accounts (T1078.004)
**Pertanyaan:** Di layanan/tenant cloud, terlihat aktivitas login dari lokasi atau perangkat yang tidak biasa pada akun internal. Apakah ini indikasi penyalahgunaan akun cloud?

**Jawaban Referensi (Draft):** Ya, ini cocok dengan penyalahgunaan akun valid pada lingkungan cloud.

**Saran Mitigasi Awal (Draft):**  
1. Paksa MFA dan reset sesi/token akun terdampak (**M1032 Multi-factor Authentication**, **M1018 User Account Management**).  
2. Audit role dan hak akses cloud yang berlebihan (**M1026 Privileged Account Management**).  
3. Perketat kebijakan password dan identitas (**M1027 Password Policies**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1078.004`; mitigations `M1018, M1026, M1027, M1032`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M14 - Brute Force (T1110)
**Pertanyaan:** Log menunjukkan percobaan login gagal berulang dari alamat IP yang sama dalam waktu singkat. Apakah ini cukup untuk dikategorikan sebagai upaya brute force?

**Jawaban Referensi (Draft):** Indikasinya kuat mengarah ke brute force terhadap autentikasi.

**Saran Mitigasi Awal (Draft):**  
1. Terapkan lockout/pengetatan kebijakan akun (**M1018 User Account Management**, **M1036 Account Use Policies**).  
2. Perkuat kebijakan password (**M1027 Password Policies**).  
3. Aktifkan MFA untuk menurunkan risiko takeover (**M1032 Multi-factor Authentication**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1110`; mitigations `M1018, M1027, M1032, M1036`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M15 - Password Spraying (T1110.003)
**Pertanyaan:** Terdapat pola percobaan login menggunakan satu kata sandi yang sama ke banyak akun berbeda. Pola serangan seperti ini biasanya disebut apa?

**Jawaban Referensi (Draft):** Ini pola password spraying.

**Saran Mitigasi Awal (Draft):**  
1. Terapkan kebijakan pembatasan percobaan login dan kontrol penggunaan akun (**M1036 Account Use Policies**).  
2. Wajibkan MFA pada akses penting (**M1032 Multi-factor Authentication**).  
3. Terapkan kebijakan password kuat dan tidak umum (**M1027 Password Policies**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1110.003`; mitigations `M1027, M1032, M1036`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M16 - Password Guessing (T1110.001)
**Pertanyaan:** Terdapat percobaan login berulang pada satu akun tertentu dengan berbagai variasi kata sandi. Apakah ini berbeda dengan password spraying?

**Jawaban Referensi (Draft):** Ya. Ini lebih dekat ke password guessing pada akun target spesifik.

**Saran Mitigasi Awal (Draft):**  
1. Terapkan password policy yang kuat dan anti-kamus (**M1027 Password Policies**).  
2. Aktifkan MFA pada akun target berisiko tinggi (**M1032 Multi-factor Authentication**).  
3. Terapkan aturan penggunaan akun dan pembatasan percobaan login (**M1036 Account Use Policies**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1110.001`; mitigations `M1027, M1032, M1036`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M17 - Password Cracking (T1110.002)
**Pertanyaan:** Kami menerima informasi kemungkinan terjadi kebocoran data kredensial (misalnya hash kata sandi) yang dapat dicoba di luar sistem. Risiko apa yang perlu segera diantisipasi?

**Jawaban Referensi (Draft):** Jika yang bocor berupa hash/kredensial, pelaku dapat mencoba melakukan pemecahan kata sandi secara offline (cracking) lalu menggunakan hasilnya untuk login. Risiko utamanya adalah pengambilalihan akun dan akses tidak sah lebih lanjut.

**Saran Mitigasi Awal (Draft):**  
1. Terapkan kebijakan password kuat dan rotasi terkontrol (**M1027 Password Policies**).  
2. Aktifkan MFA agar password tunggal tidak cukup untuk autentikasi (**M1032 Multi-factor Authentication**).  
3. Lakukan reset paksa untuk akun yang diduga terdampak dump/hash leak.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1110.002`; mitigations `M1027, M1032`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M18 - Exfiltration Over Web Service (T1567)
**Pertanyaan:** Saya melihat adanya unggahan dokumen internal ke layanan berbagi file publik tanpa persetujuan. Apakah ini dapat mengindikasikan kebocoran data?

**Jawaban Referensi (Draft):** Ya, ini selaras dengan exfiltration melalui layanan web.

**Saran Mitigasi Awal (Draft):**  
1. Terapkan pembatasan akses ke web service berisiko tinggi (**M1021 Restrict Web-Based Content**).  
2. Aktifkan kontrol DLP pada trafik keluar (**M1057 Data Loss Prevention**).  
3. Audit akun/endpoint yang melakukan upload.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1567`; mitigations `M1021, M1057`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M19 - Exfiltration Over C2 Channel (T1041)
**Pertanyaan:** Kami mendapati trafik keluar dari perangkat ke domain/layanan yang tidak dikenal secara berkala, dan diduga ada pengiriman data secara tersembunyi. Langkah awal apa yang sebaiknya dilakukan?

**Jawaban Referensi (Draft):** Ini pola exfiltration lewat kanal C2.

**Saran Mitigasi Awal (Draft):**  
1. Blok komunikasi C2 dan pola jaringan mencurigakan (**M1031 Network Intrusion Prevention**).  
2. Terapkan DLP untuk mendeteksi kebocoran data outbound (**M1057 Data Loss Prevention**).  
3. Isolasi endpoint yang terindikasi menjadi kanal exfiltration.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1041`; mitigations `M1031, M1057`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M20 - Command and Scripting Interpreter (T1059)
**Pertanyaan:** Terdapat eksekusi skrip/PowerShell yang tidak biasa di luar jam kerja pada endpoint. Apakah hal ini perlu dicurigai sebagai aktivitas berbahaya dan dilaporkan sebagai insiden?

**Jawaban Referensi (Draft):** Ya, eksekusi script interpreter sering dipakai untuk menjalankan perintah lanjutan, persistence, atau pengiriman payload.

**Saran Mitigasi Awal (Draft):**  
1. Batasi eksekusi skrip/aplikasi yang tidak diizinkan (**M1038 Execution Prevention**, **M1033 Limit Software Installation**).  
2. Aktifkan pencegahan berbasis perilaku endpoint (**M1040 Behavior Prevention on Endpoint**).  
3. Nonaktifkan fitur/program yang tidak dibutuhkan di endpoint sensitif (**M1042 Disable or Remove Feature or Program**).

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `T1059`; mitigations `M1021, M1026, M1033, M1038, M1040, M1042`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

## LAMPIRAN - Pertanyaan Tambahan dari Validator

| No | Pertanyaan | Jawaban Referensi | Sumber (NIST / MITRE) |
|----|------------|-------------------|------------------------|
| 1  |            |                   |                        |
| 2  |            |                   |                        |
| 3  |            |                   |                        |
| 4  |            |                   |                        |
| 5  |            |                   |                        |

---

## CATATAN UMUM VALIDATOR

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

