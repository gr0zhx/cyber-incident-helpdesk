# BLOK B — MITRE ATT&CK (Fokus Insiden Umum) — Q&A

## Kata Pengantar
Dokumen ini disusun sebagai **lembar validasi skenario tanya jawab** untuk mendukung penelitian pengembangan sistem **helpdesk keamanan siber berbasis RAG** di lingkungan Pusdatin Kementan. Seluruh pertanyaan dibuat dengan sudut pandang **pegawai kementerian yang belum memiliki latar belakang teknis keamanan siber**, sehingga bentuknya menyerupai laporan kejadian atau keluhan yang realistis.

Jawaban pada setiap skenario disusun sebagai **jawaban referensi (ground truth)** dan **digrounding** ke *knowledge base* MITRE ATT&CK Enterprise pada berkas `knowledge_base\\enterprise-attack.json` (ditandai dengan *Technique ID* `Txxxx`). Dengan pendekatan ini, diharapkan evaluasi relevansi konteks dan jawaban (misalnya untuk pengukuran RAGAS) dapat dilakukan secara lebih objektif dan dapat ditelusuri sumbernya.

Dokumen ini **bukan** SOP penanganan insiden dan **bukan** keputusan diagnosis final. Tujuan utama validasi adalah memastikan bahwa (1) pertanyaan terdengar natural bagi pengguna non-teknis, (2) jawaban jelas dan tidak berlebihan, serta (3) keterkaitan jawaban dengan teknik MITRE yang dirujuk sudah tepat.

## Ruang lingkup kategori (dipersempit)
1. Phishing
2. Malware
3. Ransomware
4. Web defacement
5. Distributed denial-of-service (DDoS)

## Knowledge Base (Sumber Grounding)
- MITRE ATT&CK Enterprise (STIX JSON): `knowledge_base\enterprise-attack.json`

---

## Q&A (20 skenario, hanya 5 kategori di atas)

### QA-B01 (Phishing) — Email minta “login ulang” dengan tautan
**Pertanyaan:** Saya menerima email yang mengatasnamakan unit internal dan meminta saya login ulang lewat tautan karena akun saya disebut “akan dinonaktifkan”. Saya ragu ini email resmi. Ini biasanya termasuk apa?

**Jawaban:** Pola email yang mendorong korban melakukan tindakan tertentu (klik tautan, login ulang, atau memasukkan kredensial) dapat mengarah pada **phishing**, yaitu upaya menipu pengguna agar memberikan akses/ informasi.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1566` (Phishing)

---

### QA-B02 (Phishing) — Lampiran “surat/tanda tangan” yang diminta dibuka
**Pertanyaan:** Ada email masuk dengan lampiran yang katanya “surat tugas/undangan” dan saya diminta segera membuka lampiran itu. Saya khawatir ini jebakan. Ini termasuk pola apa?

**Jawaban:** Phishing juga dapat dilakukan melalui **lampiran** (misalnya dokumen) yang mendorong korban membuka file agar terjadi eksekusi konten berbahaya.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1566.001` (Spearphishing Attachment)

---

### QA-B03 (Phishing) — Tautan dokumen/Google Drive yang terlihat meyakinkan
**Pertanyaan:** Saya dapat pesan email/WhatsApp berisi tautan dokumen (katanya Google Drive/SharePoint). Saat dibuka, saya diminta memasukkan akun kantor. Apakah ini bentuk penipuan tertentu?

**Jawaban:** Tautan yang mengarahkan korban ke halaman tertentu (misalnya halaman login palsu atau situs yang memancing input) merupakan pola **spearphishing melalui tautan**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1566.002` (Spearphishing Link)

---

### QA-B04 (Phishing) — Permintaan lewat email layanan (misalnya helpdesk) yang menyaru
**Pertanyaan:** Saya menerima email dari alamat yang terlihat seperti layanan resmi (misalnya helpdesk), meminta saya melakukan verifikasi akun. Namun formatnya agak janggal. Ini bisa termasuk apa?

**Jawaban:** Phishing dapat memanfaatkan **layanan** atau kanal komunikasi yang terlihat resmi untuk meningkatkan kepercayaan korban, sehingga korban mengikuti instruksi yang berbahaya.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1566.003` (Spearphishing via Service)

---

### QA-B05 (Malware) — Saya tanpa sengaja menjalankan file yang dikirim orang lain
**Pertanyaan:** Saya sempat mengunduh dan menjalankan file yang dikirim lewat chat karena dikira dokumen kerja. Setelah itu laptop terasa lambat dan muncul pop-up aneh. Ini biasanya mengarah ke apa?

**Jawaban:** Ketika korban **menjalankan** file yang sebenarnya berbahaya, itu selaras dengan pola penyerang yang mengandalkan **aksi pengguna** untuk mengeksekusi kode berbahaya.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1204` (User Execution)

---

### QA-B06 (Malware) — Ada file asing muncul setelah saya membuka sesuatu
**Pertanyaan:** Setelah saya membuka sebuah file/tautan, tiba-tiba ada berkas baru yang tidak saya kenal muncul di folder Download atau Temp. Apakah ini pertanda ada program berbahaya masuk?

**Jawaban:** Munculnya file/alat yang tidak dikenal dapat mengarah pada skenario penyerang **memindahkan tool** ke perangkat target untuk digunakan lebih lanjut.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1105` (Ingress Tool Transfer)

---

### QA-B07 (Malware) — Nama aplikasinya seperti aplikasi kantor, tapi terasa “palsu”
**Pertanyaan:** Di laptop kantor saya ada aplikasi yang namanya mirip aplikasi resmi (misalnya mirip nama aplikasi meeting atau office), tapi ikonnya berbeda dan lokasinya tidak biasa. Ini pola apa?

**Jawaban:** Penyerang dapat menyamarkan file/proses agar terlihat sah supaya pengguna tidak curiga. Pola ini selaras dengan teknik **masquerading**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1036` (Masquerading)

---

### QA-B08 (Malware) — Ada aktivitas “command” yang tidak pernah saya lakukan
**Pertanyaan:** Saya tidak pernah membuka command prompt/terminal, tapi tim TI bilang ada aktivitas perintah yang berjalan di perangkat saya. Ini bisa mengarah ke apa?

**Jawaban:** Eksekusi perintah melalui interpreter (misalnya command shell atau skrip) sering digunakan untuk menjalankan tindakan lanjutan di perangkat korban. Hal ini selaras dengan penggunaan **command and scripting interpreter**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1059` (Command and Scripting Interpreter)

---

### QA-B09 (Ransomware) — File berubah ekstensi dan tidak bisa dibuka
**Pertanyaan:** Tiba-tiba banyak file kerja saya tidak bisa dibuka dan ekstensi file berubah. Ada catatan yang meminta tebusan. Ini mengarah ke insiden apa?

**Jawaban:** Perubahan file menjadi tidak dapat diakses dan adanya pesan tebusan sangat kuat mengarah pada **ransomware**, yaitu pola **enkripsi data untuk memberikan dampak**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1486` (Data Encrypted for Impact)

---

### QA-B10 (Ransomware) — System restore/backup lokal seperti tidak bisa dipakai
**Pertanyaan:** Saat kejadian file tidak bisa dibuka, saya mencoba pemulihan (restore/backup lokal), tapi fitur pemulihan seperti tidak tersedia atau gagal. Ini biasanya bagian dari apa?

**Jawaban:** Pelaku dapat menghambat pemulihan sistem (misalnya mempengaruhi mekanisme recovery) agar korban lebih sulit mengembalikan data dan layanan. Pola ini selaras dengan **menghambat pemulihan sistem**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1490` (Inhibit System Recovery)

---

### QA-B11 (Ransomware) — Banyak layanan berhenti mendadak bersamaan
**Pertanyaan:** Beberapa layanan penting (misalnya layanan file sharing atau aplikasi) tiba-tiba berhenti bersamaan tanpa perubahan resmi. Ini bisa terkait pola ransomware?

**Jawaban:** Pada beberapa insiden, pelaku dapat menghentikan layanan untuk mengganggu operasi, mempercepat dampak, atau mengurangi hambatan terhadap aksinya. Hal ini selaras dengan teknik **menghentikan layanan**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1489` (Service Stop)

---

### QA-B12 (Ransomware) — Ada file yang awalnya “acak”, lalu diproses jadi terbaca oleh program tertentu
**Pertanyaan:** Tim TI menemukan ada berkas yang awalnya tampak acak/tidak terbaca, lalu setelah ada program berjalan, berkas tersebut jadi “terbaca” oleh program lain. Ini mengarah ke apa?

**Jawaban:** Perubahan dari data tersamarkan menjadi bisa digunakan dapat selaras dengan upaya pelaku melakukan **decode/deobfuscate** informasi sebagai bagian dari rangkaian malware/ransomware.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1140` (Deobfuscate/Decode Files or Information)

---

### QA-B13 (Web defacement) — Tampilan website berubah jadi konten asing
**Pertanyaan:** Halaman depan website unit kami tiba-tiba berubah (ada tulisan/gambar yang bukan dari kami). Ini termasuk insiden apa?

**Jawaban:** Perubahan tampilan konten website menjadi konten yang tidak sah selaras dengan **defacement**, yaitu pengubahan tampilan/isi untuk memberikan dampak atau pesan tertentu.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1491` (Defacement)

---

### QA-B14 (Web defacement) — Halaman internal aplikasi (intranet) berubah
**Pertanyaan:** Yang berubah bukan website publik, tapi halaman internal/intranet yang hanya bisa diakses pegawai. Apakah ini juga termasuk defacement?

**Jawaban:** Ya, pengubahan konten pada sistem internal juga dapat merupakan **defacement internal**, meskipun tidak terlihat publik.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1491.001` (Internal Defacement)

---

### QA-B15 (Web defacement) — Website publik berubah dan dilihat masyarakat
**Pertanyaan:** Website publik berubah dan sudah dilihat masyarakat (ada screenshot beredar). Ini masuk kategori apa?

**Jawaban:** Jika pengubahan konten terjadi pada aset yang dapat diakses publik dan berdampak ke pihak luar, hal itu selaras dengan **external defacement**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1491.002` (External Defacement)

---

### QA-B16 (Web defacement) — Ada dugaan celah pada aplikasi yang menghadap internet
**Pertanyaan:** Tim pengelola menduga perubahan website terjadi karena ada celah pada aplikasi web yang bisa diakses dari internet. Ini mengarah ke teknik apa (secara umum)?

**Jawaban:** Salah satu cara pelaku mendapatkan akses awal ke aplikasi web yang menghadap internet adalah dengan **mengeksploitasi aplikasi yang dapat diakses publik**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1190` (Exploit Public-Facing Application)

---

### QA-B17 (DDoS) — Website sangat lambat atau tidak bisa diakses saat jam tertentu
**Pertanyaan:** Website layanan kami mendadak sangat lambat atau tidak bisa diakses, terutama pada waktu tertentu. Tim jaringan bilang trafiknya tinggi tidak wajar. Ini mengarah ke apa?

**Jawaban:** Lonjakan trafik jaringan yang bertujuan membuat layanan tidak tersedia dapat selaras dengan **network denial of service**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1498` (Network Denial of Service)

---

### QA-B18 (DDoS) — Trafik “banjir” langsung ke server dari banyak sumber
**Pertanyaan:** Tim TI menyebut ada “banjir paket” langsung ke alamat server layanan, datang dari banyak sumber. Ini termasuk pola apa?

**Jawaban:** Serangan yang membanjiri target secara langsung dengan trafik besar selaras dengan **direct network flood**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1498.001` (Direct Network Flood)

---

### QA-B19 (DDoS) — Serangan memanfaatkan pantulan/amplifikasi
**Pertanyaan:** Tim jaringan mengatakan serangan ke layanan kami seperti memanfaatkan server lain sebagai “pantulan” sehingga trafiknya menjadi sangat besar. Ini pola apa?

**Jawaban:** Serangan yang meningkatkan volume trafik melalui mekanisme pantulan/amplifikasi selaras dengan **reflection amplification**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1498.002` (Reflection Amplification)

---

### QA-B20 (DDoS) — Aplikasi/layanan “kehabisan resource” dan berhenti melayani
**Pertanyaan:** Layanan kami tidak selalu down karena bandwidth penuh, tapi server terlihat kehabisan resource (CPU/memori) sehingga aplikasi berhenti merespons. Ini bisa termasuk apa?

**Jawaban:** Membuat layanan tidak bisa merespons dengan cara menguras resource pada layanan (misalnya request berlebihan hingga service jenuh) selaras dengan **service exhaustion flood**.

**Sumber grounding (KB):** `enterprise-attack.json` — Technique `T1499.002` (Service Exhaustion Flood)
