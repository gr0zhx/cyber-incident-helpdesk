# LEMBAR VALIDASI GROUND TRUTH (V6)

## Evaluasi Sistem Helpdesk Keamanan Siber Berbasis RAG - Pusdatin Kementan

**Peneliti:** Agry Zharfa  
**Lokus Validasi:** Tim Keamanan Siber dan Perlindungan Data Pribadi, Pusdatin Kementan  
**Tanggal:** _________________  
**Total Pertanyaan:** 20 (NIST SP 800-61 saja — BLOK A)

---

## Tujuan

V6 difokuskan untuk membuat **BLOK A (NIST SP 800-61)** benar-benar natural dari **POV pegawai non-teknis** (melaporkan gejala yang dialami), namun jawabannya tetap **bisa di-ground** ke:

- `knowledge_base\documents\nist.sp.800-61r2.pdf` (Rev.2 — panduan detail incident handling)
- `knowledge_base\documents\NIST.SP.800-61r3.pdf` (Rev.3 — rekomendasi IR dalam konteks CSF 2.0 & cyber risk management)

---

## Knowledge Base Sistem (Sumber Grounding)

1. **NIST SP 800-61 Rev.2** - `knowledge_base\documents\nist.sp.800-61r2.pdf`
2. **NIST SP 800-61 Rev.3** - `knowledge_base\documents\NIST.SP.800-61r3.pdf`

---

## Catatan Grounding

- **Rujukan halaman memakai “PDF p.X”** = nomor halaman hasil pembacaan PDF (1-based), bukan nomor halaman cetak di dokumen.
- Untuk Rev.2, rujukan biasanya mencantumkan **nomor section + PDF page** (mis. §3.2.5, PDF p.40).

---

## BLOK A - NIST SP 800-61 (20 Pertanyaan, POV Pegawai/User Non-Teknis)

### QA-N01 - (Kejadian vs Insiden)
**Pertanyaan:** Saya bingung, ini cuma error biasa atau sudah termasuk “insiden keamanan”? Kapan saya harus lapor?

**Jawaban Referensi (Draft):** Kalau ada kejadian yang **berdampak negatif** atau mengarah ke akses/aktivitas tidak wajar, sebaiknya tetap **lapor** agar bisa diverifikasi. Di NIST, “event” itu kejadian yang terlihat, sedangkan insiden adalah kejadian keamanan yang perlu penanganan; laporan awal dari pegawai tetap penting untuk validasi.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §2.1 *Events and Incidents* (PDF p.16)
- NIST SP 800-61r2 §3.2.2 *Signs of an Incident* (PDF p.36)
- NIST SP 800-61r2 §3.2.3 (bagian “People… Users… report signs of incidents; important to validate”) (PDF p.38)
- NIST SP 800-61r3 Table 1 (phase “Detection & Analysis” dipetakan ke CSF “Detect”) (PDF p.14)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N02 - (Email mencurigakan)
**Pertanyaan:** Saya dapat email yang kelihatan “mendesak” dan minta saya klik link/lampiran. Saya tidak paham teknis, tapi rasanya janggal. Saya harus ngapain?

**Jawaban Referensi (Draft):** Anggap sebagai indikasi awal dan **laporkan secepatnya** melalui kanal resmi. Jangan meneruskan/menyebarkan kontennya, dan catat detail yang kamu lihat (pengirim, subjek, jam diterima, link/lampiran). Ini membantu tim melakukan analisis dan notifikasi yang tepat.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.1 *Attack Vectors* (kategori “Email”) (PDF p.35)
- NIST SP 800-61r2 §3.2.2 *Signs of an Incident* (PDF p.36)
- NIST SP 800-61r2 §3.2.7 *Incident Notification* (PDF p.43)
- NIST SP 800-61r3 Table 1 (Detection & Analysis → CSF “Detect”) (PDF p.14)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N03 - (Sudah terlanjur klik)
**Pertanyaan:** Saya sudah terlanjur klik link / buka lampiran dari pesan yang mencurigakan. Saya takut bikin tambah parah. Langkah awal saya apa?

**Jawaban Referensi (Draft):** **Segera lapor** dan sampaikan kronologi singkat (kapan klik, link/lampiran apa, gejala setelahnya). NIST menekankan mulai **mencatat fakta sejak awal** dan memastikan notifikasi ke pihak yang tepat. Hindari tindakan yang berpotensi menghilangkan bukti (mis. menghapus file/pesan) sebelum ada arahan.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.5 *Incident Documentation* (“immediately start recording all facts… documented and timestamped”) (PDF p.40)
- NIST SP 800-61r2 §3.2.7 *Incident Notification* (PDF p.43)
- NIST SP 800-61r2 §3.3.1 *Choosing a Containment Strategy* (pertimbangan containment di awal) (PDF p.45)
- NIST SP 800-61r3 RS.MI *Incident Mitigation* (perlunya kriteria/prosedur containment/eradication) (PDF p.40)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N04 - (Telepon/Chat mengaku “tim IT”)
**Pertanyaan:** Ada yang telepon/chat ngaku dari “tim IT”, minta password/OTP atau minta saya install sesuatu. Saya harus respon gimana?

**Jawaban Referensi (Draft):** Perlakukan ini sebagai indikasi *impersonation* dan **laporkan** lewat kanal resmi. Jangan memberikan kredensial/OTP dan jangan mengikuti instruksi instalasi dari pihak yang tidak terverifikasi. Tim akan memutuskan langkah notifikasi dan tindak lanjut.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.1 *Attack Vectors* (kategori “Impersonation”) (PDF p.35)
- NIST SP 800-61r2 §3.2.7 *Incident Notification* (PDF p.43)
- NIST SP 800-61r3 §1.1 (tujuan: common language untuk komunikasi internal/eksternal terkait IR) (PDF p.11)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N05 - (Notifikasi login/MFA tidak wajar)
**Pertanyaan:** Saya dapat notifikasi login atau permintaan MFA berulang padahal saya tidak sedang login. Apa yang sebaiknya saya lakukan?

**Jawaban Referensi (Draft):** Ini **indikator** yang perlu ditangani serius: segera lapor, catat jam kejadian, aplikasi apa, dan notifikasi apa yang muncul. Dalam penanganan insiden, tindakan eradication bisa mencakup **menonaktifkan akun yang dibobol** setelah containment dilakukan (berdasarkan keputusan tim).

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.2 *Signs of an Incident* (PDF p.36)
- NIST SP 800-61r2 §3.2.5 *Incident Documentation* (PDF p.40)
- NIST SP 800-61r2 §3.3.4 *Eradication and Recovery* (contoh: “disabling breached user accounts”) (PDF p.47)
- NIST SP 800-61r3 RS.MI-02 *Incidents are eradicated* (contoh: “disabling breached user accounts… mitigating exploited vulnerabilities”) (PDF p.41)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N06 - (Perangkat hilang/tertinggal)
**Pertanyaan:** HP/laptop kantor saya hilang atau tertinggal, dan di dalamnya ada akun kerja. Ini termasuk insiden?

**Jawaban Referensi (Draft):** Kehilangan/perampasan perangkat kerja termasuk vektor yang umum dan perlu **pelaporan cepat** agar tim bisa melakukan containment (mis. mengamankan akun/akses) dan menilai dampaknya. Sampaikan kapan dan di mana terakhir perangkat terlihat.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.1 *Attack Vectors* (kategori “Loss or Theft of Equipment”) (PDF p.36)
- NIST SP 800-61r2 §3.2.7 *Incident Notification* (PDF p.43)
- NIST SP 800-61r2 §3.3.1 *Choosing a Containment Strategy* (PDF p.45)
- NIST SP 800-61r3 Table 1 (Containment/Eradication/Recovery → CSF “Respond/Recover”) (PDF p.14)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N07 - (Laptop terasa “aneh”)
**Pertanyaan:** Laptop saya tiba-tiba lambat, muncul pop-up aneh, atau ada aplikasi terbuka sendiri. Ini harus dilaporkan?

**Jawaban Referensi (Draft):** Ya—gejala seperti itu bisa menjadi **tanda insiden** dan perlu diverifikasi. NIST menekankan bahwa analisis tidak selalu mudah (bisa false positive), tetapi laporan pengguna tetap perlu dikumpulkan dan dianalisis.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.2 *Signs of an Incident* (PDF p.36)
- NIST SP 800-61r2 §3.2.4 *Incident Analysis* (tantangan analisis, false positives, user-provided indicators bisa keliru tapi perlu dianalisis) (PDF p.38)
- NIST SP 800-61r3 Table 1 (Detection & Analysis → CSF “Detect”) (PDF p.14)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N08 - (Kalau belum yakin)
**Pertanyaan:** Kalau saya cuma “curiga” tapi belum punya bukti, itu merepotkan nggak kalau lapor?

**Jawaban Referensi (Draft):** Tidak—lebih baik lapor lebih awal. NIST menyebut pengguna dan pihak internal lain bisa menjadi sumber indikator, dan laporan seperti itu tetap harus **divalidasi**. Kamu cukup sampaikan apa yang kamu lihat, tanpa harus “mendiagnosis”.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.3 (bagian “People… Users… report signs of incidents… important to validate all such reports”) (PDF p.38)
- NIST SP 800-61r2 §3.2.2 *Signs of an Incident* (PDF p.36)
- NIST SP 800-61r3 §1.1 (common language untuk komunikasi IR) (PDF p.11)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N09 - (Info minimum saat lapor)
**Pertanyaan:** Waktu lapor, informasi minimum apa yang paling membantu tim biar cepat paham?

**Jawaban Referensi (Draft):** Sampaikan minimal: **waktu kejadian**, perangkat/akun terdampak, gejala yang terlihat, dan tindakan yang sudah dilakukan. NIST menganjurkan pencatatan fakta sedini mungkin dan setiap langkah ditulis serta diberi timestamp.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.5 *Incident Documentation* (“recording all facts… documented and timestamped”) (PDF p.40)
- NIST SP 800-61r2 §3.1.1 *Preparing to Handle Incidents* (tersedianya mekanisme pelaporan insiden oleh pengguna) (PDF p.31)
- NIST SP 800-61r3 §1.1 (common language untuk komunikasi IR) (PDF p.11)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N10 - (Jangan hapus bukti)
**Pertanyaan:** Kenapa saya diminta jangan menghapus email/chat/berkas yang mencurigakan?

**Jawaban Referensi (Draft):** Karena itu bisa menjadi **bukti** dan konteks penting untuk analisis. NIST menekankan dokumentasi sejak awal, dan pada fase containment/recovery bukti perlu dikumpulkan/ditangani dengan jelas karena bisa dibutuhkan untuk proses legal.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.5 *Incident Documentation* (PDF p.40)
- NIST SP 800-61r2 §3.3.2 *Evidence Gathering and Handling* (pentingnya bukti dan dokumentasi penanganannya) (PDF p.46)
- NIST SP 800-61r3 RS.MI (containment/eradication actions dan prosedur) (PDF p.40)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N11 - (Boleh matikan komputer?)
**Pertanyaan:** Kalau panik, boleh nggak saya langsung matikan komputer atau cabut internet?

**Jawaban Referensi (Draft):** Jangan otomatis—tindakan containment seperti memutus koneksi atau shutdown perlu pertimbangan dampak dan bukti. NIST menekankan pemilihan strategi containment dan penanganan bukti secara benar. Kalau ada risiko penyebaran cepat, segera lapor dan ikuti instruksi resmi.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.3.1 *Choosing a Containment Strategy* (PDF p.45)
- NIST SP 800-61r2 §3.3.2 *Evidence Gathering and Handling* (PDF p.46)
- NIST SP 800-61r3 RS.MI (kriteria/prosedur containment & eradication actions) (PDF p.40)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N12 - (Dokumen salah kirim)
**Pertanyaan:** Saya tidak sengaja kirim dokumen internal ke orang/alamat email yang salah. Ini harus dilaporkan sebagai insiden?

**Jawaban Referensi (Draft):** Ini minimal “adverse event” terkait keamanan (berpotensi paparan data) dan sebaiknya **dilaporkan** agar ditentukan statusnya (event vs incident) serta siapa yang perlu diberi notifikasi. Yang penting: catat detail (dokumen apa, ke siapa, kapan).

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §2.1 *Events and Incidents* (adverse events, ruang lingkup kejadian keamanan) (PDF p.16)
- NIST SP 800-61r2 §3.2.5 *Incident Documentation* (PDF p.40)
- NIST SP 800-61r2 §3.2.7 *Incident Notification* (PDF p.43)
- NIST SP 800-61r3 §1.1 (komunikasi IR internal/eksternal) (PDF p.11)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N13 - (File tiba-tiba terenkripsi / “tebusan”)
**Pertanyaan:** File saya tiba-tiba tidak bisa dibuka, namanya berubah, atau muncul pesan “tebusan”. Langkah aman awal apa?

**Jawaban Referensi (Draft):** Segera lapor karena ini indikasi kuat insiden berdampak besar. Fokus awal adalah **containment** agar tidak menyebar, sambil menjaga bukti dan mendokumentasikan gejala yang terlihat. Rev.3 juga menekankan perlunya kriteria/prosedur supaya containment/eradication bisa dipilih cepat.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.3.1 *Choosing a Containment Strategy* (PDF p.45)
- NIST SP 800-61r2 §3.3.2 *Evidence Gathering and Handling* (PDF p.46)
- NIST SP 800-61r3 RS.MI *Incident Mitigation* (contoh kasus: “user endpoint ransomware infection”; kriteria/prosedur containment/eradication) (PDF p.40)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N14 - (Akun dikunci sementara)
**Pertanyaan:** Setelah saya lapor, kenapa akun saya malah dikunci sementara atau akses saya dibatasi?

**Jawaban Referensi (Draft):** Itu bisa menjadi bagian dari **containment/eradication** untuk mencegah penyalahgunaan lebih lanjut saat investigasi berjalan. NIST memberi contoh bahwa setelah containment, eradication dapat mencakup menghapus malware dan **menonaktifkan akun yang dibobol**.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.3.1 *Choosing a Containment Strategy* (PDF p.45)
- NIST SP 800-61r2 §3.3.4 *Eradication and Recovery* (“disabling breached user accounts”) (PDF p.47)
- NIST SP 800-61r3 RS.MI-02 *Incidents are eradicated* (contoh tindakan: disable breached accounts, mitigasi vulnerabilities) (PDF p.41)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N15 - (Siapa yang diberitahu)
**Pertanyaan:** Kalau terjadi hal seperti ini, siapa saja yang biasanya perlu diberi tahu?

**Jawaban Referensi (Draft):** Setelah insiden dianalisis dan diprioritaskan, tim perlu melakukan **incident notification** ke pihak-pihak yang relevan agar semua yang perlu terlibat menjalankan perannya (sesuai kebijakan internal). Sebagai pelapor, kamu cukup memastikan laporan masuk kanal resmi.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.7 *Incident Notification* (PDF p.43)
- NIST SP 800-61r2 §3.2.6 *Incident Prioritization* (sebelum notifikasi, insiden dianalisis & diprioritaskan) (PDF p.42)
- NIST SP 800-61r3 §1.1 (common language untuk komunikasi IR internal/eksternal) (PDF p.11)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N16 - (Prioritas penanganan)
**Pertanyaan:** Kalau ada beberapa kejadian sekaligus (misalnya banyak pegawai kena), tim menentukan mana yang didahulukan dari apa?

**Jawaban Referensi (Draft):** NIST menekankan bahwa penanganan insiden tidak boleh sekadar “siapa duluan lapor”. Prioritas diputuskan berdasarkan dampak, urgensi, dan ketersediaan sumber daya, supaya kerusakan tidak meluas.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.6 *Incident Prioritization* (PDF p.42)
- NIST SP 800-61r3 Table 1 (mengaitkan respons & pemulihan dengan CSF “Respond/Recover”) (PDF p.14)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N17 - (Laporan dari pihak luar)
**Pertanyaan:** Kalau ada pihak luar (misalnya warga/vendor) bilang website/aplikasi kita aneh atau tidak bisa diakses, itu harus dianggap serius?

**Jawaban Referensi (Draft):** Ya—laporan eksternal perlu ditanggapi serius dan divalidasi. NIST menyebut laporan dari luar organisasi bisa berupa indikator seperti layanan tidak tersedia atau halaman web berubah (defaced), dan tetap perlu penanganan yang terstruktur.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.3 (bagian “People from other organizations… report indicators… defaced web page or unavailable service”) (PDF p.38)
- NIST SP 800-61r2 §3.2.4 *Incident Analysis* (validasi/analisis indikator) (PDF p.38)
- NIST SP 800-61r3 §1.1 (komunikasi IR internal/eksternal) (PDF p.11)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N18 - (Kapan boleh normal lagi)
**Pertanyaan:** Kapan perangkat/aplikasi saya boleh dipakai normal lagi setelah ada kejadian seperti ini?

**Jawaban Referensi (Draft):** Setelah containment selesai dan langkah eradication/recovery yang diperlukan sudah dilakukan serta diverifikasi oleh tim. NIST menjelaskan bahwa setelah insiden ditahan (contained), eradication dan recovery bisa diperlukan untuk menghilangkan komponen insiden dan memulihkan kondisi aman.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.3 *Containment, Eradication, and Recovery* (PDF p.45)
- NIST SP 800-61r2 §3.3.4 *Eradication and Recovery* (PDF p.47)
- NIST SP 800-61r3 RS.MI dan RS.MI-02 (containment/eradication actions) (PDF p.40–41)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N19 - (Kenapa ada evaluasi setelah selesai)
**Pertanyaan:** Kenapa setelah insiden selesai masih ada evaluasi/rapat pembelajaran?

**Jawaban Referensi (Draft):** Karena “lessons learned” adalah bagian penting agar organisasi **belajar dan membaik**. NIST menekankan kegiatan pembelajaran sering diabaikan padahal penting, dan hasilnya dipakai untuk menyesuaikan kebijakan/proses agar kejadian serupa tidak terulang.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.4.1 *Lessons Learned* (PDF p.48)
- NIST SP 800-61r3 §3.1 *Preparation and Lessons Learned* (PDF p.19)
- NIST SP 800-61r3 Table 1 (Post-Incident Activity → CSF Identify (Improvement)) (PDF p.14)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---

### QA-N20 - (Kenapa bukti & catatan disimpan)
**Pertanyaan:** Kenapa bukti/log/catatan insiden disimpan, dan apa manfaatnya untuk organisasi?

**Jawaban Referensi (Draft):** Dokumentasi membantu penanganan yang lebih sistematis, dan data insiden yang terkumpul berguna untuk pembelajaran dan justifikasi perbaikan (misalnya kebutuhan dukungan/funding). NIST juga menekankan perlunya kebijakan **retensi bukti** (berapa lama disimpan) agar terkelola.

**Sumber Grounding (KB):**
- NIST SP 800-61r2 §3.2.5 *Incident Documentation* (PDF p.40)
- NIST SP 800-61r2 §3.4.2 *Using Collected Incident Data* (PDF p.49)
- NIST SP 800-61r2 §3.4.3 *Evidence Retention* (PDF p.51)
- NIST SP 800-61r3 §3.1 *Preparation and Lessons Learned* (PDF p.19)

**Penilaian:** [ ] Setuju &nbsp; [ ] Perlu Revisi &nbsp; [ ] Tidak Sesuai  
**Koreksi/Catatan:**  
_____________________________________________________________________  
_____________________________________________________________________

---
