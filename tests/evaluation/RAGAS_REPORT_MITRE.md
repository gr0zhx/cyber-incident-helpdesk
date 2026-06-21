# Laporan Evaluasi RAGAS — Dataset MITRE ATT&CK

**Dokumen sumber:** MITRE ATT&CK Framework — Teknik Serangan dan Mitigasi  
**Tanggal evaluasi:** 21 June 2026  
**Jumlah soal:** 10  
**Model LLM:** GPT-4o (via GitHub Models)  
**Pipeline:** Agentic RAG + Hybrid Retrieval (Semantic + BM25) + Reranker + query_knowledge intent

---

## Ringkasan Skor RAGAS

| Metrik | Skor Dataset Ini | Rata-rata 3 Dataset | Keterangan |
|---|---|---|---|
| Faithfulness | **0.8499** | 0.9252 | Jawaban grounded dalam konteks yang di-retrieve |
| Answer Relevancy | **0.8690** | 0.8499 | Jawaban relevan dan fokus terhadap pertanyaan |
| Context Relevance | **0.9500** | 0.9833 | Konteks yang diambil relevan dengan pertanyaan |

---

## Skor Per Pertanyaan

| ID | Faithfulness | Answer Relevancy | Context Relevance |
|---|---|---|---|
| QA-011 | 1.00 ✅ | 0.83 🟡 | 1.00 ✅ |
| QA-012 | 0.88 ✅ | 0.92 ✅ | 1.00 ✅ |
| QA-013 | 1.00 ✅ | 0.84 🟡 | 1.00 ✅ |
| QA-014 | 0.83 🟡 | 0.91 ✅ | 1.00 ✅ |
| QA-015 | 0.67 🔴 | 0.80 🟡 | 0.50 🔴 |
| QA-016 | 1.00 ✅ | 0.81 🟡 | 1.00 ✅ |
| QA-017 | 0.70 🟡 | 0.88 ✅ | 1.00 ✅ |
| QA-018 | 0.86 ✅ | 0.87 ✅ | 1.00 ✅ |
| QA-019 | 0.90 ✅ | 0.89 ✅ | 1.00 ✅ |
| QA-020 | 0.67 🔴 | 0.93 ✅ | 1.00 ✅ |

---

## Detail Pertanyaan, Jawaban Sistem, dan Ground Truth

### QA-011

**Tipe Insiden:** Phishing | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.83 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Apa program pelatihan keamanan yang bisa kami terapkan untuk melindungi pegawai dari serangan phishing melalui email dengan tautan login palsu?

**Jawaban Sistem (Kandidat):**
Untuk melindungi pegawai dari serangan phishing melalui email dengan tautan login palsu, program pelatihan keamanan yang dapat diterapkan meliputi beberapa langkah. Pertama, edukasi pegawai tentang cara mengenali upaya phishing, termasuk email yang mencurigakan dan tautan login palsu. Kedua, buat program pelatihan komprehensif yang mencakup modul tentang phishing, manajemen kata sandi, dan pelaporan insiden. Ketiga, gunakan latihan simulasi phishing untuk mengukur kerentanan pengguna dan memberikan pelatihan lanjutan yang ditargetkan. Keempat, libatkan metode pembelajaran interaktif seperti kuis dan tantangan yang digamifikasi untuk meningkatkan keterlibatan. Kelima, masukkan pelatihan keamanan siber sebagai bagian dari proses orientasi bagi pegawai baru dan sediakan materi yang mudah dipahami tentang kebijakan penggunaan yang dapat diterima dan prosedur pelaporan. Terakhir, pastikan semua pegawai menyelesaikan kursus penyegaran berkala untuk tetap mendapatkan informasi terbaru tentang ancaman yang muncul dan teknik yang digunakan oleh penyerang.

**Ground Truth:**
Laksanakan program User Training untuk mendidik karyawan dalam mengenali, melaporkan, dan mencegah ancaman phishing seperti email spearphishing dengan tautan palsu. Desain modul pelatihan yang mencakup topik phishing, pengelolaan kata sandi, dan pelaporan insiden. Gunakan simulasi phishing untuk melatih respons pengguna terhadap serangan rekayasa sosial.

---

### QA-012

**Tipe Insiden:** Malware | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=0.88 ✅ | Answer Relevancy=0.92 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Perangkat terinfeksi malware setelah membuka lampiran email berbahaya. Apa langkah mitigasi malware dari lampiran email yang harus segera diambil?

**Jawaban Sistem (Kandidat):**
Langkah mitigasi malware dari lampiran email yang harus segera diambil meliputi beberapa tindakan. Pertama, isolasi sistem yang terkena insiden untuk mencegah penyebaran lebih lanjut. Selanjutnya, lakukan backup data yang berkaitan dengan insiden, seperti log dan screenshot, untuk keperluan analisis lebih lanjut. Identifikasi semua layanan dan koneksi yang terhubung untuk memastikan tidak ada jalur lain yang dapat digunakan oleh malware. Selain itu, identifikasi metode penyerang ketika masuk ke sistem pertama kali dengan melihat log pada sistem. Setelah itu, lakukan penghapusan penyebab insiden siber, seperti malware, dan jika diperlukan, lakukan reset password untuk akun pengguna yang terkena insiden. Terakhir, lakukan mitigasi terhadap kerentanan yang tereksploitasi saat insiden siber terjadi untuk mencegah kejadian serupa di masa depan.

**Ground Truth:**
Pasang dan perbarui perangkat lunak Antivirus/Antimalware di semua perangkat untuk mendeteksi dan memblokir malware dari lampiran email berbahaya. Gunakan pencegahan perilaku pada endpoint untuk mendeteksi dan memblokir aktivitas mencurigakan berdasarkan analisis perilaku proses. Terapkan isolasi aplikasi dan sandboxing untuk menjalankan lampiran email dalam lingkungan terkontrol sehingga kode berbahaya tidak mempengaruhi sistem utama.

---

### QA-013

**Tipe Insiden:** Ransomware | **Tingkat Keparahan:** 🔴 Kritis  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.84 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Terjadi serangan ransomware yang mengenkripsi file pada server dan muncul pesan permintaan tebusan. Apa langkah mitigasi ransomware yang harus segera dilakukan?

**Jawaban Sistem (Kandidat):**
Langkah mitigasi ransomware yang harus segera dilakukan meliputi beberapa tindakan penting. Pertama, isolasi sistem yang terkena insiden untuk mencegah penyebaran lebih lanjut. Kedua, lakukan backup data yang berkaitan dengan insiden, seperti hasil pengumpulan bukti berbentuk log dan screenshot. Ketiga, identifikasi semua layanan dan koneksi yang terhubung untuk memahami ruang lingkup serangan. Keempat, identifikasi metode penyerang ketika masuk ke sistem pertama kali dengan memeriksa log pada sistem. Selain itu, penting untuk memeriksa kode-kode berbahaya yang ada dalam sistem dan melakukan pemantauan pada jaringan yang terkena insiden siber. Jika terdapat paket yang dicurigai atau anomali, segera blokir dan dokumentasikan. Terakhir, pastikan setiap aset informasi diperiksa keamanannya setelah penanggulangan insiden siber untuk memastikan tidak ada ancaman yang tersisa.

**Ground Truth:**
Lakukan backup data secara teratur dan simpan di lokasi yang terisolasi dari jaringan korporat untuk memastikan pemulihan dari serangan ransomware yang mengenkripsi data. Jadwalkan backup incremental harian dan backup penuh mingguan untuk semua server dan sistem kritis. Pastikan proses backup mencakup pengerasan sistem backup dan solusi penyimpanan yang aman.

---

### QA-014

**Tipe Insiden:** Web Defacement | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=0.83 🟡 | Answer Relevancy=0.91 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Langkah backup data apa yang harus diterapkan organisasi untuk memulihkan sistem setelah insiden web defacement atau kerusakan data?

**Jawaban Sistem (Kandidat):**
Untuk memulihkan sistem setelah insiden web defacement atau kerusakan data, organisasi harus menerapkan langkah-langkah backup data yang meliputi: melakukan prosedur pemulihan sistem/data dari media penyimpanan apabila terjadi keadaan darurat, melaksanakan simulasi secara periodik terhadap prosedur pemulihan sistem/data dari media penyimpanan rekam cadang, dan melakukan prosedur rekam cadang secara optimal. Selain itu, organisasi juga harus memastikan setiap aset informasi diperiksa keamanannya setelah penanggulangan insiden siber dan memastikan bersih dari indikasi ancaman atau serangan yang telah terjadi.

**Ground Truth:**
Pulihkan konten website dari backup data yang tersimpan di lokasi terisolasi dari jaringan korporat untuk memulihkan integritas halaman yang terdeface. Terapkan jadwal backup data secara teratur termasuk backup incremental harian dan backup penuh mingguan untuk semua server web kritis.

---

### QA-015

**Tipe Insiden:** Akses Tidak Sah | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=0.67 🔴 | Answer Relevancy=0.80 🟡 | Context Relevance=0.50 🔴

**Pertanyaan:**
> Beberapa pegawai kantor kami pernah menerima telepon dari seseorang yang mengaku teknisi IT dan meminta password atau akses ke komputer mereka. Bagaimana cara melindungi pegawai dari jenis penipuan semacam ini?

**Jawaban Sistem (Kandidat):**
Untuk melindungi pegawai dari penipuan yang melibatkan seseorang yang mengaku sebagai teknisi IT dan meminta password atau akses ke komputer, penting untuk memberikan edukasi kepada pegawai tentang cara mengidentifikasi upaya phishing dan menjaga keamanan informasi. Edukasi ini dapat mencakup cara mengenali tanda-tanda penipuan, seperti permintaan informasi sensitif yang tidak biasa, dan langkah-langkah yang harus diambil jika mereka menerima permintaan semacam itu. Selain itu, pegawai harus diajarkan untuk tidak memberikan informasi sensitif melalui telepon atau email tanpa verifikasi yang tepat. Dengan meningkatkan kesadaran dan pemahaman pegawai tentang ancaman ini, organisasi dapat mengurangi risiko terjadinya insiden keamanan siber yang disebabkan oleh penipuan semacam ini.

**Ground Truth:**
Laksanakan program pelatihan keamanan dan kesadaran (User Training) untuk mendidik pegawai agar tidak pernah memberikan informasi sensitif seperti password atau akses sistem kepada siapapun melalui telepon, termasuk yang mengaku sebagai staf IT. Pelatihan harus mencakup cara mengenali teknik rekayasa sosial, prosedur verifikasi identitas yang benar sebelum memberikan akses, dan cara melaporkan percobaan penipuan kepada tim keamanan.

---

### QA-016

**Tipe Insiden:** Akses Tidak Sah | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.81 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Terdeteksi penyalahgunaan akun — ada login berhasil menggunakan kredensial pegawai tanpa sepengetahuan pemiliknya. Apa langkah mitigasi akun yang dikompromikan ini?

**Jawaban Sistem (Kandidat):**
Untuk menangani penyalahgunaan akun yang dikompromikan, langkah-langkah mitigasi yang dapat diambil meliputi menonaktifkan akun pengguna yang terkena insiden siber dan melakukan reset password jika diperlukan. Selain itu, penting untuk melakukan analisis insiden siber guna mengetahui sistem elektronik yang terkena dan ruang lingkup dampaknya. Setelah penanggulangan insiden, pastikan setiap aset informasi diperiksa keamanannya untuk memastikan tidak ada indikasi ancaman atau serangan yang tersisa.

**Ground Truth:**
Implementasikan Multi-Factor Authentication untuk memastikan setiap login memerlukan verifikasi tambahan selain password, mencegah penyalahgunaan kredensial yang bocor. Terapkan kebijakan pengelolaan akun istimewa untuk membatasi akses dan memantau penggunaan akun dengan hak istimewa. Terapkan kebijakan kata sandi yang kuat termasuk persyaratan kompleksitas dan perubahan kata sandi segera.

---

### QA-017

**Tipe Insiden:** DDoS | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=0.70 🟡 | Answer Relevancy=0.88 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Layanan publik mengalami gangguan akibat serangan DDoS — trafik jaringan mendadak meledak hingga layanan tidak tersedia. Apa langkah mitigasi serangan DDoS yang tepat?

**Jawaban Sistem (Kandidat):**
Untuk mengatasi serangan DDoS yang menyebabkan gangguan pada layanan publik, langkah-langkah mitigasi yang tepat meliputi: pertama, isolasi sistem yang terkena insiden untuk mencegah penyebaran lebih lanjut. Kedua, lakukan backup data yang berkaitan dengan insiden, seperti log dan screenshot, untuk keperluan analisis lebih lanjut. Ketiga, identifikasi semua layanan dan koneksi yang terhubung untuk mengetahui sumber serangan. Keempat, identifikasi metode penyerang ketika masuk ke sistem pertama kali dengan memeriksa log pada sistem. Kelima, periksa kode-kode berbahaya yang ada dalam sistem. Terakhir, lakukan pemantauan pada jaringan yang terkena insiden siber, dan jika terdapat paket yang dicurigai atau anomali, segera blokir dan dokumentasikan informasi seperti sumber IP, bentuk paket, dan waktu kejadian. Langkah-langkah ini akan membantu dalam menahan dan mengurangi dampak dari serangan DDoS tersebut.

**Ground Truth:**
Gunakan perangkat jaringan dan perangkat lunak endpoint untuk memfilter lalu lintas jaringan masuk, keluar, dan lateral guna mencegah dampak serangan DDoS pada layanan publik. Konfigurasikan filter jaringan untuk membatasi akses hanya dari sumber yang diotorisasi ke server yang menghadap publik.

---

### QA-018

**Tipe Insiden:** Kebocoran Data | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=0.86 ✅ | Answer Relevancy=0.87 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Bagaimana cara memfilter lalu lintas jaringan untuk mencegah eksfiltrasi data dari sistem organisasi ke layanan eksternal yang tidak diotorisasi?

**Jawaban Sistem (Kandidat):**
Untuk memfilter lalu lintas jaringan dan mencegah eksfiltrasi data dari sistem organisasi ke layanan eksternal yang tidak diotorisasi, organisasi dapat melakukan pemantauan pada jaringan yang terkena Insiden Siber. Jika terdapat paket yang dicurigai atau anomali, langkah yang harus diambil adalah segera memblokir dan mendokumentasikan paket tersebut. Dokumentasi dapat mencakup sumber IP, bentuk paket, waktu, dan informasi relevan lainnya. Selain itu, organisasi harus mengidentifikasi semua layanan dan koneksi yang terhubung untuk memastikan tidak ada jalur yang tidak diotorisasi yang dapat digunakan untuk eksfiltrasi data. Langkah-langkah ini merupakan bagian dari prosedur penahanan insiden yang harus didokumentasikan dengan jelas untuk memfasilitasi pengambilan keputusan yang tepat.

**Ground Truth:**
Terapkan filter lalu lintas jaringan untuk membatasi akses ke layanan berbagi file publik yang tidak diotorisasi dan mencegah eksfiltrasi data lebih lanjut. Konfigurasikan kebijakan penggunaan akun dan terapkan prinsip hak akses minimum agar hanya pengguna yang berwenang yang dapat mengakses dan mentransfer dokumen sensitif ke layanan eksternal.

---

### QA-019

**Tipe Insiden:** Malware | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=0.90 ✅ | Answer Relevancy=0.89 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Ditemukan malware atau tool berbahaya yang diduga ditanam penyerang di perangkat. Apa langkah mitigasi untuk mendeteksi dan memblokir tool berbahaya tersebut?

**Jawaban Sistem (Kandidat):**
Untuk mendeteksi dan memblokir tool berbahaya seperti malware yang ditanam oleh penyerang, langkah mitigasi yang dapat dilakukan meliputi penggunaan antimalware yang dapat memberikan peringatan saat mendeteksi host atau media yang terinfeksi malware. Selain itu, penting untuk memantau log pada aplikasi untuk mencatat adanya tindakan percobaan login yang banyak dari IP address yang tidak diketahui. Administrator juga harus waspada terhadap file baru dengan nama yang tidak biasa dan surat elektronik yang tertolak oleh sistem dengan konten yang anomali. Analisis insiden siber juga perlu dilakukan untuk mengetahui sistem elektronik yang terkena insiden dan ruang lingkup dampaknya. Deteksi sumber insiden siber dapat dilakukan dengan mengidentifikasi informasi seperti lokasi, nomor serial, nomor model, hostname, MAC address, dan IP address dari komputer yang digunakan, serta log pada sistem operasi dan aplikasi. Penggunaan IPS/IDS/Firewall pada jaringan juga penting untuk memberikan peringatan saat terjadi intrusi pada jaringan.

**Ground Truth:**
Gunakan perangkat lunak Antivirus/Antimalware untuk mendeteksi dan memblokir tool berbahaya yang ditransfer penyerang ke sistem. Terapkan pencegahan perilaku pada endpoint untuk menganalisis dan memblokir eksekusi skrip atau tool yang tidak dikenal berdasarkan pola perilaku mencurigakan.

---

### QA-020

**Tipe Insiden:** Malware | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=0.67 🔴 | Answer Relevancy=0.93 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Perangkat lunak keamanan apa yang harus dipasang di endpoint untuk mendeteksi dan memblokir malware yang dijalankan pengguna dari file berbahaya?

**Jawaban Sistem (Kandidat):**
Perangkat lunak keamanan yang harus dipasang di endpoint untuk mendeteksi dan memblokir malware adalah perangkat lunak antimalware. Perangkat lunak ini harus diterapkan di seluruh organisasi, termasuk pada level host seperti sistem operasi server dan workstation, level server aplikasi seperti server email dan proxy web, serta level klien aplikasi seperti klien email dan klien pesan instan. Dengan demikian, perangkat lunak ini dapat mendeteksi dan menghentikan malware yang dijalankan pengguna dari file berbahaya.

**Ground Truth:**
Gunakan perangkat lunak Antivirus/Antimalware untuk mendeteksi dan memblokir malware yang terinstal dari file berbahaya yang dijalankan pengguna. Terapkan pencegahan perilaku pada endpoint untuk mendeteksi dan menghentikan proses mencurigakan yang berjalan sebagai akibat dari eksekusi file berbahaya tersebut.

---
