# LEMBAR VALIDASI GROUND TRUTH (V4)

## Evaluasi Sistem Helpdesk Keamanan Siber Berbasis RAG — Pusdatin Kementan

**Peneliti:** Agry Zharfa  
**Lokus Validasi:** Tim Keamanan Siber dan Perlindungan Data Pribadi, Pusdatin Kementan  
**Tanggal:** _________________  
**Total Pertanyaan:** 40 (20 NIST SP 800-61 + 20 MITRE ATT&CK)

---

## Tujuan

Lembar ini digunakan untuk memvalidasi *ground truth* (jawaban referensi) untuk evaluasi performa sistem RAG (Context Relevance, Answer Relevance, Faithfulness). Versi V4 dibuat dengan gaya pertanyaan yang lebih natural seperti pertanyaan pegawai/pelapor saat insiden terjadi.

---

## Knowledge Base Sistem (Sumber Grounding)

1. **NIST SP 800-61 Rev.2** — `knowledge_base\documents\nist.sp.800-61r2.pdf`
2. **NIST SP 800-61 Rev.3** — `knowledge_base\documents\NIST.SP.800-61r3.pdf` (referensi penguatan praktik terkini)
3. **MITRE ATT&CK Enterprise** — `knowledge_base\enterprise-attack.json`

---

## Petunjuk Pengisian

1. Baca **Pertanyaan**, **Jawaban Referensi (Draft)**, dan **Sumber Grounding**.
2. Pada kolom **Penilaian**, pilih:
   - **[Setuju]** — substansi sudah tepat untuk konteks operasional Pusdatin.
   - **[Perlu Revisi]** — perlu penyesuaian SOP/teknis lokal.
   - **[Tidak Sesuai]** — tidak akurat/tidak relevan.
3. Isi **Koreksi/Catatan** jika perlu perbaikan.

---

## BLOK A — NIST SP 800-61 (20 Pertanyaan)

### QA-N01 — Preparation
**Pertanyaan:** Kalau kita baru mau ngerapihin proses respons insiden, langkah paling awal yang realistis itu apa dulu?

**Jawaban Referensi (Draft):** Mulai dari menetapkan struktur tim respons insiden, peran tiap fungsi, jalur komunikasi resmi, dan prosedur eskalasi yang disepakati. Setelah itu, siapkan playbook dasar per jenis insiden prioritas tinggi dan daftar kontak darurat yang selalu terbarui.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.1 (Preparation, p.21-24), Rev.3 (incident response capability planning).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N02 — Preparation
**Pertanyaan:** Biar pas kejadian enggak saling lempar, pembagian peran idealnya gimana?

**Jawaban Referensi (Draft):** Peran dipisah jelas: penerima laporan/triase awal, analis teknis, koordinator insiden, eksekutor pemulihan, dan PIC komunikasi. Satu insiden harus punya penanggung jawab utama agar keputusan containment dan eskalasi tidak terlambat.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.1.1 (Preparing to Handle Incidents).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N03 — Preparation
**Pertanyaan:** Sering keburu panik pas insiden. Dokumen minimum yang wajib ada sebelum kejadian itu apa aja?

**Jawaban Referensi (Draft):** Minimal ada: kebijakan incident response, SOP eskalasi, playbook per jenis insiden utama, daftar aset kritikal, dan template pencatatan insiden. Dokumen ini harus diuji lewat simulasi agar tidak hanya jadi arsip.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.1, §3.1.1.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N04 — Preparation
**Pertanyaan:** Untuk kesiapan tim, lebih penting beli tools dulu atau latih orang dulu?

**Jawaban Referensi (Draft):** Keduanya harus jalan bareng, tapi prioritas awal adalah kompetensi tim dan prosedur kerja. Tools tanpa proses dan SDM terlatih sering menghasilkan alert banyak tapi respons lambat dan tidak konsisten.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.1.1, §3.1.2 (Preventing Incidents).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N05 — Preparation
**Pertanyaan:** Gimana cara nentuin insiden mana yang perlu latihan tabletop duluan?

**Jawaban Referensi (Draft):** Pilih skenario yang dampaknya paling besar ke layanan publik, data sensitif, dan reputasi organisasi. Fokus awal biasanya phishing kredensial, ransomware, kebocoran data, dan gangguan layanan.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.1, §3.2.6 (Incident Prioritization, p.32).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N06 — Detection & Analysis
**Pertanyaan:** Kalau ada alert dari sistem tapi user belum ada yang lapor, itu harus dianggap insiden belum?

**Jawaban Referensi (Draft):** Belum otomatis jadi insiden. Alert diperlakukan sebagai indikator yang harus diverifikasi: cek konteks aset, korelasi log, dan dampaknya. Jika indikator valid dan ada potensi gangguan CIA, baru dinaikkan menjadi insiden.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2 (Detection and Analysis, p.25-34).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N07 — Detection & Analysis
**Pertanyaan:** User ngaku akunnya dipakai orang lain, tapi log belum lengkap. Langkah awal analis harus apa?

**Jawaban Referensi (Draft):** Amankan bukti yang ada dulu (timestamp, IP, device, aktivitas akun), lakukan verifikasi cepat, lalu terapkan kontrol sementara seperti reset sesi/token atau pembatasan akses jika risikonya tinggi. Pengumpulan log lanjutan tetap dilanjutkan.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2.2 (Signs of an Incident), §3.2.3 (Sources of Precursors and Indicators).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N08 — Detection & Analysis
**Pertanyaan:** Laporan via WhatsApp sering minim detail. Data minimum apa yang harus kita minta dari pelapor?

**Jawaban Referensi (Draft):** Minta waktu kejadian, akun/perangkat terdampak, gejala yang terlihat, tindakan yang sudah dilakukan, serta bukti awal (screenshot/log singkat). Format minimum ini membantu triase lebih cepat dan mengurangi miskomunikasi.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2.5 (Incident Documentation), §3.2.7 (Incident Notification).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N09 — Detection & Analysis
**Pertanyaan:** Dua insiden datang bersamaan, satu ganggu layanan, satu dugaan bocor data. Yang mana dulu?

**Jawaban Referensi (Draft):** Prioritaskan berdasarkan dampak fungsional layanan, dampak informasi (khususnya data sensitif), dan recoverability. Insiden yang berisiko tinggi ke data sensitif atau melumpuhkan layanan kritikal diprioritaskan paling atas.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2.6 (Incident Prioritization, p.32).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N10 — Detection & Analysis
**Pertanyaan:** Kapan kondisi dianggap cukup buat eskalasi ke pimpinan/CSIRT?

**Jawaban Referensi (Draft):** Eskalasi dilakukan saat ada indikator dampak besar, keterlibatan aset kritikal, potensi kewajiban pelaporan eksternal, atau butuh keputusan lintas unit yang cepat. Kriteria eskalasi harus tertulis agar tidak bergantung intuisi personal.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.2.7 (Incident Notification), Rev.3 (governance and coordination emphasis).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N11 — Containment, Eradication & Recovery
**Pertanyaan:** Saat serangan masih jalan, tindakan paling aman: langsung matiin sistem atau isolasi dulu?

**Jawaban Referensi (Draft):** Umumnya lakukan containment terukur dulu (isolasi host/segmen, blok koneksi berisiko) agar dampak berhenti tanpa merusak bukti penting. Keputusan shutdown total diambil jika manfaatnya lebih besar dari risiko kehilangan bukti/layanan.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.1 (Choosing a Containment Strategy, p.35).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N12 — Containment, Eradication & Recovery
**Pertanyaan:** Kalau ada host terindikasi malware, apakah semua host satu subnet harus diisolasi juga?

**Jawaban Referensi (Draft):** Tidak otomatis semua diisolasi. Lakukan penilaian cepat berbasis bukti penyebaran (IOC serupa, lateral movement, pola koneksi). Jika ada indikasi penyebaran aktif, containment diperluas secara bertahap dan terkontrol.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.1, §3.3.4.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N13 — Containment, Eradication & Recovery
**Pertanyaan:** Bukti digital sering tercecer. Praktik paling aman biar bukti tetap valid itu gimana?

**Jawaban Referensi (Draft):** Bukti harus dikumpulkan, dicatat, disimpan, dan diakses secara terkendali dengan *chain of custody* yang jelas. Perubahan terhadap bukti harus bisa ditelusuri agar tetap dapat dipertanggungjawabkan saat audit/investigasi.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.2 (Evidence Gathering and Handling, p.36).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N14 — Containment, Eradication & Recovery
**Pertanyaan:** Setelah malware dihapus, kapan kita yakin sudah benar-benar bersih?

**Jawaban Referensi (Draft):** Tidak cukup hanya hapus file berbahaya. Harus ada verifikasi ulang: scanning lanjutan, cek persistence mechanism, validasi patch/konfigurasi, dan monitoring pasca-perbaikan untuk memastikan tidak ada reinfeksi.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.4 (Eradication and Recovery, p.37).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N15 — Containment, Eradication & Recovery
**Pertanyaan:** Sebelum layanan dibuka lagi ke publik, checklist minimalnya apa?

**Jawaban Referensi (Draft):** Pastikan pemulihan dari sumber tepercaya, validasi keamanan selesai, celah awal sudah ditutup, dan monitoring ketat sudah aktif. Layanan baru dibuka setelah risiko residual dinilai dapat diterima oleh penanggung jawab insiden.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.3.4; Rev.3 (risk-informed recovery).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N16 — Post-Incident Activity
**Pertanyaan:** Setelah insiden beres, apa cukup tutup tiket aja?

**Jawaban Referensi (Draft):** Tidak cukup. Harus ada *lessons learned* untuk menilai akar masalah, respons yang efektif/tidak, dan perbaikan proses/teknologi agar insiden serupa tidak terulang dengan dampak sama.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.4.1 (Lessons Learned, p.38).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N17 — Post-Incident Activity
**Pertanyaan:** Post-mortem yang bagus itu isinya apa, biar bukan sekadar formalitas?

**Jawaban Referensi (Draft):** Isi minimal: timeline kejadian, keputusan penting, dampak nyata, akar penyebab, gap kontrol, biaya/waktu pemulihan, dan aksi perbaikan yang jelas PIC serta tenggatnya.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.4.1, §3.4.2.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N18 — Post-Incident Activity
**Pertanyaan:** Data insiden yang sudah terkumpul enaknya dipakai buat apa selain arsip?

**Jawaban Referensi (Draft):** Data insiden dipakai untuk tren serangan, evaluasi efektivitas kontrol, perbaikan playbook, bahan awareness, dan dasar prioritas investasi keamanan yang lebih berbasis bukti.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.4.2 (Using Collected Incident Data, p.39).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N19 — Post-Incident Activity
**Pertanyaan:** Metrik apa yang paling relevan buat ngukur apakah respons insiden kita makin matang?

**Jawaban Referensi (Draft):** Gunakan metrik operasional seperti waktu deteksi, waktu containment, waktu pemulihan, tingkat insiden berulang, serta kepatuhan terhadap SLA dan prosedur dokumentasi.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.4.2; Rev.3 (measurement and improvement orientation).

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N20 — Post-Incident Activity
**Pertanyaan:** Kapan hasil insiden perlu diangkat jadi update kebijakan atau SOP baru?

**Jawaban Referensi (Draft):** Jika insiden menunjukkan kelemahan berulang, celah tata kelola, atau kontrol yang tidak lagi efektif, maka temuan wajib diterjemahkan ke update kebijakan, SOP, dan pelatihan agar perubahan benar-benar permanen.

**Sumber Grounding (KB):** NIST SP 800-61 Rev.2 §3.4 (continuous improvement setelah insiden), Rev.3 recommendations.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

## BLOK B — MITRE ATT&CK (20 Pertanyaan)

### QA-M01 — Phishing (T1566)
**Pertanyaan:** Kalau pegawai bilang dapat email mencurigakan yang minta klik cepat, itu masuk kategori apa?

**Jawaban Referensi (Draft):** Itu selaras dengan teknik **Phishing (T1566)**: upaya rekayasa sosial melalui kanal elektronik untuk memancing user membuka jalan akses attacker, biasanya lewat link atau lampiran.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1566`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M02 — Spearphishing Attachment (T1566.001)
**Pertanyaan:** Kalau lampiran dokumen yang dikirim kelihatan normal tapi ternyata bawa malware, itu teknik yang mana?

**Jawaban Referensi (Draft):** Itu cocok dengan **Spearphishing Attachment (T1566.001)**, yaitu pengiriman file berbahaya yang memanfaatkan kepercayaan user agar mengeksekusi konten berbahaya.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1566.001`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M03 — Spearphishing Link (T1566.002)
**Pertanyaan:** Link yang dikirim ngarah ke halaman login palsu, ini masuk teknik apa?

**Jawaban Referensi (Draft):** Ini sesuai **Spearphishing Link (T1566.002)**: korban diarahkan ke URL berbahaya atau halaman tiruan untuk pencurian kredensial/token.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1566.002`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M04 — Spearphishing via Service (T1566.003)
**Pertanyaan:** Penipu kirim pesan lewat chat kerja/medsos, bukan email. Tetap phishing juga?

**Jawaban Referensi (Draft):** Ya, itu selaras dengan **Spearphishing via Service (T1566.003)**, yakni phishing lewat layanan pihak ketiga (chat, sosial media, platform kolaborasi) untuk bypass kontrol email tradisional.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1566.003`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M05 — User Execution (T1204)
**Pertanyaan:** Kalau malware aktif setelah user klik file/link sendiri, ini termasuk apa?

**Jawaban Referensi (Draft):** Ini sesuai **User Execution (T1204)**: attacker mengandalkan tindakan user untuk mengeksekusi payload, sering sebagai lanjutan phishing.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1204`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M06 — Data Encrypted for Impact (T1486)
**Pertanyaan:** File kantor tiba-tiba terenkripsi massal dan gak bisa dibuka, ini identik sama teknik apa?

**Jawaban Referensi (Draft):** Ini selaras dengan **Data Encrypted for Impact (T1486)**, yaitu enkripsi data untuk menghentikan ketersediaan layanan/data dan biasanya dipakai dalam skenario ransomware.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1486`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M07 — Inhibit System Recovery (T1490)
**Pertanyaan:** Kenapa pas ransomware, backup lokal kadang ikut rusak atau hilang?

**Jawaban Referensi (Draft):** Karena attacker bisa menjalankan **Inhibit System Recovery (T1490)**: menonaktifkan/menghapus mekanisme pemulihan (misalnya shadow copy/restore path) agar korban sulit pulih.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1490`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M08 — Defacement (T1491)
**Pertanyaan:** Kalau halaman web kementerian berubah tampilan tanpa izin, itu teknik apa di ATT&CK?

**Jawaban Referensi (Draft):** Itu cocok dengan **Defacement (T1491)**: modifikasi konten visual situs/aplikasi secara tidak sah yang berdampak ke integritas konten.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1491`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M09 — Exploit Public-Facing Application (T1190)
**Pertanyaan:** Situs bisa diambil alih gara-gara celah aplikasi publik, ini masuk teknik mana?

**Jawaban Referensi (Draft):** Ini selaras dengan **Exploit Public-Facing Application (T1190)**: eksploitasi kerentanan aplikasi/layanan yang terekspos internet untuk mendapatkan akses awal.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1190`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M10 — Network Denial of Service (T1498)
**Pertanyaan:** Trafik mendadak meledak sampai layanan publik ngedrop, itu indikasi teknik apa?

**Jawaban Referensi (Draft):** Ini cocok dengan **Network Denial of Service (T1498)**: serangan yang menghabiskan kapasitas jaringan sehingga layanan jadi lambat atau tidak tersedia.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1498`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M11 — Endpoint Denial of Service (T1499)
**Pertanyaan:** Bedanya DDoS jaringan sama server/aplikasi yang dipaksa crash itu apa?

**Jawaban Referensi (Draft):** Jika target utama adalah kapasitas jaringan, itu T1498. Jika penyerang mematikan ketersediaan endpoint/aplikasi langsung (proses crash/hang), itu lebih dekat ke **Endpoint Denial of Service (T1499)**.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1499`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M12 — Valid Accounts (T1078)
**Pertanyaan:** Kalau akun valid pegawai dipakai orang lain buat masuk, kategorinya apa?

**Jawaban Referensi (Draft):** Ini sesuai **Valid Accounts (T1078)**: penyalahgunaan kredensial akun yang sah untuk akses, pergerakan lateral, atau eskalasi tanpa malware yang mencolok.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1078`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M13 — Cloud Accounts (T1078.004)
**Pertanyaan:** Kalau yang dibajak akun cloud/tenant, tetap satu keluarga dengan T1078?

**Jawaban Referensi (Draft):** Ya. Untuk konteks cloud, ATT&CK memetakan sebagai **Cloud Accounts (T1078.004)**, yaitu penyalahgunaan kredensial valid pada lingkungan cloud.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1078.004`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M14 — Brute Force (T1110)
**Pertanyaan:** Login gagal berulang dari satu/sedikit sumber, itu indikasi teknik apa?

**Jawaban Referensi (Draft):** Ini selaras dengan **Brute Force (T1110)**: percobaan menebak kredensial secara berulang sampai menemukan kombinasi yang valid.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1110`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M15 — Password Spraying (T1110.003)
**Pertanyaan:** Kalau satu password dicoba ke banyak akun sekaligus, itu namanya apa?

**Jawaban Referensi (Draft):** Itu termasuk **Password Spraying (T1110.003)**, subteknik brute force yang menekan risiko lockout dengan mencoba password umum ke banyak akun.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1110.003`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M16 — Password Guessing (T1110.001)
**Pertanyaan:** Kalau attacker nebak-nebak password akun tertentu terus-terusan, subtekniknya apa?

**Jawaban Referensi (Draft):** Ini sesuai **Password Guessing (T1110.001)**, yaitu percobaan berulang terhadap akun tertentu dengan dugaan password yang umum/terkait profil korban.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1110.001`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M17 — Password Cracking (T1110.002)
**Pertanyaan:** Kalau hash password yang bocor dipecahin offline, itu masih keluarga brute force?

**Jawaban Referensi (Draft):** Ya, itu termasuk **Password Cracking (T1110.002)**, yaitu pemecahan hash secara offline tanpa mencoba login langsung ke layanan target.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1110.002`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M18 — Exfiltration Over Web Service (T1567)
**Pertanyaan:** Data sensitif di-upload ke layanan web publik biar lolos monitoring, ini teknik apa?

**Jawaban Referensi (Draft):** Ini cocok dengan **Exfiltration Over Web Service (T1567)**: pemindahan data keluar melalui layanan web yang terlihat “legitimate” untuk menyamarkan aktivitas.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1567`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M19 — Exfiltration Over C2 Channel (T1041)
**Pertanyaan:** Kalau data dicuri lewat kanal command-and-control, bukan upload manual user, itu disebut apa?

**Jawaban Referensi (Draft):** Ini selaras dengan **Exfiltration Over C2 Channel (T1041)**, yaitu data dikeluarkan melalui kanal C2 yang dipakai malware/implant.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1041`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-M20 — Command and Scripting Interpreter (T1059)
**Pertanyaan:** Kenapa command shell/skrip sering jadi petunjuk penting saat investigasi malware?

**Jawaban Referensi (Draft):** Karena attacker sering memakai **Command and Scripting Interpreter (T1059)** untuk eksekusi perintah, download payload, persistence, dan movement. Aktivitas shell/script menjadi indikator penting untuk deteksi dan forensic timeline.

**Sumber Grounding (KB):** `enterprise-attack.json` attack-pattern `external_id: T1059`.

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

## LAMPIRAN — Pertanyaan Tambahan dari Validator

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

