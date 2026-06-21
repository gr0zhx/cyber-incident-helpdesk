# Laporan Evaluasi RAGAS — Dataset BSSN

**Dokumen sumber:** Peraturan BSSN Nomor 1 Tahun 2024 tentang Pengelolaan Insiden Siber  
**Tanggal evaluasi:** 21 June 2026  
**Jumlah soal:** 10  
**Model LLM:** GPT-4o (via GitHub Models)  
**Pipeline:** Agentic RAG + Hybrid Retrieval (Semantic + BM25) + Reranker

---

## Ringkasan Skor RAGAS

| Metrik | Skor Dataset Ini | Rata-rata 3 Dataset | Keterangan |
|---|---|---|---|
| Faithfulness | **0.9714** | 0.9240 | Jawaban grounded dalam konteks yang di-retrieve |
| Answer Relevancy | **0.8644** | 0.8578 | Jawaban relevan dan fokus terhadap pertanyaan |
| Context Relevance | **1.0000** | 0.9833 | Konteks yang diambil relevan dengan pertanyaan |

---

## Skor Per Pertanyaan

| ID | Faithfulness | Answer Relevancy | Context Relevance |
|---|---|---|---|
| BSSN-001 | 1.00 ✅ | 0.86 ✅ | 1.00 ✅ |
| BSSN-002 | 1.00 ✅ | 0.79 🟡 | 1.00 ✅ |
| BSSN-003 | 1.00 ✅ | 0.81 🟡 | 1.00 ✅ |
| BSSN-004 | 1.00 ✅ | 0.95 ✅ | 1.00 ✅ |
| BSSN-005 | 1.00 ✅ | 0.82 🟡 | 1.00 ✅ |
| BSSN-006 | 1.00 ✅ | 0.81 🟡 | 1.00 ✅ |
| BSSN-007 | 1.00 ✅ | 0.86 ✅ | 1.00 ✅ |
| BSSN-008 | 1.00 ✅ | 0.93 ✅ | 1.00 ✅ |
| BSSN-009 | 0.71 🟡 | 0.89 ✅ | 1.00 ✅ |
| BSSN-010 | 1.00 ✅ | 0.92 ✅ | 1.00 ✅ |

---

## Detail Pertanyaan, Jawaban Sistem, dan Ground Truth

### BSSN-001

**Tipe Insiden:** general | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.86 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Kami ingin tahu cara mengenali kalau komputer atau sistem kantor sedang diserang atau mengalami insiden siber. Tanda-tanda apa yang perlu kami waspadai sehari-hari?

**Jawaban Sistem (Kandidat):**
Untuk mengenali jika komputer atau sistem kantor sedang diserang atau mengalami insiden siber, ada beberapa tanda yang perlu diwaspadai. Pertama, antimalware dapat memberikan peringatan saat mendeteksi host atau media yang terinfeksi malware. Kedua, administrator mungkin melihat adanya file baru dengan nama yang tidak biasa. Ketiga, log pada aplikasi dapat mencatat adanya percobaan login yang banyak dari IP address yang tidak diketahui. Keempat, administrator mungkin melihat banyak surat elektronik yang tertolak oleh sistem dengan konten yang anomali. Tanda-tanda ini dapat menjadi indikasi awal bahwa sistem sedang mengalami insiden siber dan memerlukan perhatian lebih lanjut.

**Ground Truth:**
Tanda-tanda yang mengindikasikan adanya insiden siber antara lain: (1) perangkat antimalware memberi peringatan saat mendeteksi host atau media yang terinfeksi, (2) administrator menemukan file baru dengan nama yang tidak biasa, (3) log aplikasi mencatat banyak percobaan login dari IP address yang tidak dikenal, (4) banyak surat elektronik yang tertolak oleh sistem dengan konten yang anomali, dan (5) IPS/IDS/Firewall pada jaringan memberi peringatan adanya intrusi. Indikasi-indikasi tersebut perlu segera dilaporkan kepada tim pengelola sistem untuk ditindaklanjuti.

---

### BSSN-002

**Tipe Insiden:** Malware | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.79 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Saat serangan siber masih aktif dan sistem kami terdampak, langkah pengisolasian dan pembatasan apa saja yang harus dilakukan sesuai panduan pengelolaan insiden siber BSSN?

**Jawaban Sistem (Kandidat):**
Saat serangan siber masih aktif dan sistem terdampak, langkah pengisolasian dan pembatasan yang harus dilakukan sesuai panduan pengelolaan insiden siber BSSN meliputi memastikan Insiden Siber diisolasi dan dimitigasi sesuai rencana tanggap Insiden Siber. Selain itu, penting untuk mengumpulkan dan memelihara bukti Insiden Siber dari Sistem Elektronik terdampak. Langkah-langkah ini termasuk mengategorikan informasi mengenai Insiden Siber yang terdeteksi dan menyimpannya sesuai ukuran dampak terkait keamanan, penyebab insiden, dan faktor lainnya yang diperlukan. Juga, melakukan forensik digital terhadap aset informasi yang terdampak untuk menemukenali penyebab Insiden Siber. Pemantauan pada jaringan yang terkena Insiden Siber juga harus dilakukan, dan jika terdapat paket yang dicurigai atau anomali, segera blokir dan dokumentasikan, termasuk mencatat sumber IP, bentuk paket, waktu, dan lainnya.

**Ground Truth:**
Prosedur containment berdasarkan panduan BSSN Nomor 1 Tahun 2024 meliputi: (1) isolasi sistem yang terkena insiden, (2) backup data yang berkaitan dengan insiden seperti log dan screenshot, (3) identifikasi semua layanan dan koneksi yang terhubung, (4) identifikasi metode penyerang saat masuk ke sistem pertama kali melalui log sistem, (5) periksa kode-kode berbahaya yang ada dalam sistem, dan (6) lakukan pemantauan pada jaringan — jika terdapat paket yang dicurigai atau anomali, segera blokir dan dokumentasikan termasuk sumber IP, bentuk paket, dan waktu kejadian.

---

### BSSN-003

**Tipe Insiden:** Malware | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.81 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Apa saja cara penghapusan dan eradikasi penyebab Insiden Siber dari Sistem Elektronik yang terdampak menurut panduan pengelolaan insiden siber BSSN?

**Jawaban Sistem (Kandidat):**
Penghapusan dan eradikasi penyebab Insiden Siber dari Sistem Elektronik yang terdampak dilakukan dengan beberapa cara. Pertama, menentukan tanda dan sebab dari suatu Insiden Siber. Kedua, melakukan restore backup untuk mendapatkan sistem yang baru dan segar. Ketiga, menghapus penyebab Insiden Siber, seperti malware. Keempat, menonaktifkan akun pengguna yang terkena Insiden Siber. Kelima, melakukan reset password jika diperlukan. Terakhir, melakukan mitigasi terhadap kerentanan yang tereksploitasi saat Insiden Siber terjadi.

**Ground Truth:**
Penghapusan atau eradikasi Insiden Siber dilakukan untuk menghilangkan komponen Insiden Siber termasuk penghapusan kerentanan Sistem Elektronik. Penghapusan dilakukan dengan beberapa cara: (1) menentukan tanda dan sebab dari suatu Insiden Siber, (2) melakukan restore backup untuk mendapatkan new fresh system, (3) menghapus penyebab Insiden Siber seperti malware, (4) menonaktifkan akun pengguna yang terkena Insiden Siber, (5) melakukan reset password jika diperlukan, (6) melakukan mitigasi terhadap kerentanan yang tereksploitasi saat Insiden Siber, (7) mengidentifikasi semua host yang terkena Insiden Siber, dan (8) melakukan improvisasi pertahanan dan vulnerability analysis untuk melihat potensi ancaman yang dapat terjadi.

---

### BSSN-004

**Tipe Insiden:** general | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.95 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Apa yang harus kami lakukan untuk mengumpulkan dan memelihara bukti saat terjadi insiden siber di organisasi kami?

**Jawaban Sistem (Kandidat):**
Untuk mengumpulkan dan memelihara bukti saat terjadi insiden siber di organisasi Anda, langkah-langkah yang harus dilakukan meliputi: mengategorikan informasi mengenai insiden siber yang terdeteksi dan menyimpannya sesuai ukuran dampak terkait keamanan, penyebab insiden, dan faktor lainnya yang diperlukan. Selain itu, lakukan forensik digital terhadap aset informasi yang terdampak insiden siber untuk menemukenali penyebab insiden siber sesuai dengan ketentuan peraturan. Pastikan juga untuk mengumpulkan bukti insiden siber dari sistem elektronik terdampak, termasuk log, screenshot, dan data lainnya yang relevan.

**Ground Truth:**
Pada kegiatan pengumpulan dan pemeliharaan bukti insiden siber, hal-hal yang perlu dilakukan antara lain: (1) mengategorikan informasi mengenai insiden siber yang terdeteksi dan menyimpannya sesuai ukuran dampak terkait keamanan, penyebab insiden, dan faktor lainnya; (2) melakukan forensik digital terhadap aset informasi yang terdampak untuk menemukenali penyebab insiden siber sesuai ketentuan peraturan perundang-undangan; serta (3) mengumpulkan bukti berupa log, screenshot, dan data lain yang berkaitan dengan insiden untuk keperluan analisis lebih lanjut.

---

### BSSN-005

**Tipe Insiden:** general | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.82 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Kami menerima informasi keamanan dari tim siber yang diberi label TLP:AMBER dan TLP:GREEN. Apa arti kedua label itu dan sejauh mana kami boleh menyebarkannya?

**Jawaban Sistem (Kandidat):**
Label TLP:AMBER digunakan ketika informasi memerlukan dukungan untuk ditindaklanjuti secara efektif, namun membawa risiko terhadap privasi, reputasi, atau operasi jika dibagikan di luar organisasi yang terlibat. Penerima dapat membagikan informasi TLP:AMBER dengan anggota organisasi mereka sendiri dan kliennya, tetapi hanya berdasarkan kebutuhan untuk mengetahui guna melindungi organisasi mereka dan kliennya serta mencegah kerugian lebih lanjut. Jika sumber ingin membatasi berbagi hanya untuk organisasi, mereka harus menentukan TLP:AMBER+STRICT. Sementara itu, label TLP:GREEN digunakan ketika informasi berguna untuk meningkatkan kesadaran dalam komunitas yang lebih luas. Penerima dapat berbagi informasi TLP:GREEN dengan rekan dan organisasi mitra dalam komunitas mereka, tetapi tidak melalui saluran yang dapat diakses publik. Informasi TLP:GREEN tidak boleh dibagikan di luar komunitas.

**Ground Truth:**
TLP:AMBER berarti pengungkapan terbatas: penerima hanya dapat menyebarkan informasi berdasarkan kebutuhan untuk mengetahui (need-to-know) di dalam organisasinya dan kliennya, tidak lebih luas dari itu. TLP:GREEN berarti penerima dapat berbagi informasi dengan rekan dan organisasi mitra dalam komunitasnya, tetapi tidak boleh melalui saluran yang dapat diakses publik dan tidak boleh dibagikan di luar komunitas. Sumber menggunakan TLP:GREEN ketika informasi berguna untuk meningkatkan kesadaran dalam komunitas yang lebih luas. Jika lingkup komunitas tidak ditentukan, diasumsikan sebagai komunitas keamanan atau pertahanan siber.

---

### BSSN-006

**Tipe Insiden:** general | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.81 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Kami mendengar istilah Infrastruktur Informasi Vital atau IIV dalam sosialisasi keamanan siber. Apa definisi IIV menurut peraturan BSSN dan apa kewajiban pelaporan insiden siber yang berlaku jika sistem kami masuk kategori tersebut?

**Jawaban Sistem (Kandidat):**
Infrastruktur Informasi Vital (IIV) menurut Peraturan BSSN adalah Sistem Elektronik yang memanfaatkan teknologi informasi dan/atau teknologi operasional, baik berdiri sendiri maupun saling bergantung dengan Sistem Elektronik lainnya dalam menunjang sektor strategis. Jika terjadi gangguan, kerusakan, dan/atau kehancuran pada infrastruktur ini, maka akan berdampak serius terhadap kepentingan umum, pelayanan publik, pertahanan dan keamanan, atau perekonomian nasional. Kewajiban pelaporan insiden siber untuk sistem yang masuk kategori IIV adalah melaporkan insiden tersebut berdasarkan hasil penerapan manajemen risiko pada organisasi, yang berupa hasil analisis risiko berdasarkan dampak insiden siber yang ditimbulkan.

**Ground Truth:**
Infrastruktur Informasi Vital (IIV) adalah infrastruktur informasi yang jika terganggu, rusak, atau hancur dapat berdampak serius terhadap kepentingan umum, kenegaraan, pertahanan dan keamanan nasional, perekonomian nasional, dan/atau penyelenggaraan layanan publik. Jika sistem masuk kategori IIV, Tim Tanggap Insiden Siber organisasi wajib melaporkan insiden yang terjadi kepada TTIS sektoral dengan tembusan TTIS nasional paling lambat 1x24 jam setelah insiden ditemukan. Jika TTIS sektoral belum terbentuk, laporan disampaikan langsung ke Kementerian atau Lembaga sesuai sektornya dengan tembusan TTIS nasional.

---

### BSSN-007

**Tipe Insiden:** general | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.86 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Setelah insiden siber yang menimpa sistem kami selesai ditangani, apakah ada pemeriksaan ulang untuk memastikan sistemnya benar-benar sudah aman dan pulih?

**Jawaban Sistem (Kandidat):**
Setelah insiden siber ditangani, ada pemeriksaan ulang untuk memastikan keamanan sistem. Setiap aset informasi diperiksa keamanannya setelah penanggulangan insiden siber. Pemeriksaan ini dilakukan terhadap seluruh aset informasi yang berhubungan dengan sistem elektronik untuk memastikan bahwa sistem tersebut bersih dari indikasi ancaman atau serangan yang telah terjadi.

**Ground Truth:**
Ya. Setelah penanganan Insiden Siber, setiap aset informasi yang terdampak wajib diperiksa kembali keamanannya. Setelah upaya pemulihan Sistem Elektronik terdampak dilakukan, dilaksanakan kegiatan pengujian ulang terhadap fungsi vital dan fungsi pendukung untuk memastikan capaian pemulihan terpenuhi. Capaian pemulihan dinilai berdasarkan: (1) waktu pemulihan di bawah batas waktu maksimal yang ditetapkan berdasarkan rencana keberlangsungan kegiatan; dan (2) jumlah data yang terpulihkan sesuai dengan batas jumlah data minimal yang ditetapkan berdasarkan rencana keberlangsungan kegiatan.

---

### BSSN-008

**Tipe Insiden:** general | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.93 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Saat insiden siber terjadi, informasi minimum apa yang wajib disampaikan Tim Tanggap Insiden Siber kepada pihak yang terdampak?

**Jawaban Sistem (Kandidat):**
Saat insiden siber terjadi, informasi minimum yang wajib disampaikan Tim Tanggap Insiden Siber kepada pihak yang terdampak meliputi: informasi kontak pelapor, deskripsi insiden siber, kronologi insiden siber, dan dampak serangan.

**Ground Truth:**
Informasi Insiden Siber yang wajib disampaikan kepada pihak terdampak paling sedikit mencakup: (a) jenis indikasi Insiden Siber yang terjadi, (b) kode distribusi informasi, (c) sistem dan aset yang terkena dampak, serta (d) rekomendasi langkah mitigasi yang perlu dilakukan.

---

### BSSN-009

**Tipe Insiden:** general | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=0.71 🟡 | Answer Relevancy=0.89 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Saat kami menemukan insiden siber, faktor apa saja yang dipertimbangkan untuk menentukan prioritas dan seberapa serius dampaknya bagi organisasi kami?

**Jawaban Sistem (Kandidat):**
Untuk menentukan prioritas dan seberapa serius dampak insiden siber bagi organisasi, beberapa faktor perlu dipertimbangkan. Pertama, kategori Sistem Elektronik yang terdampak harus diketahui. Kedua, ruang lingkup dampak insiden siber harus dianalisis untuk menentukan tim tanggap insiden yang tepat. Ketiga, pemrioritasan insiden siber dilakukan dengan mempertimbangkan kategori Sistem Elektronik dan ruang lingkup dampak insiden tersebut. Selain itu, penting untuk memastikan bahwa insiden siber dikategorikan sesuai kriteria yang telah ditetapkan, dan laporan insiden siber dikumpulkan, dikategorisasikan, serta diprioritaskan berdasarkan dampak risiko terhadap organisasi. Dengan demikian, langkah-langkah ini membantu dalam menentukan prioritas dan tingkat keseriusan dampak insiden siber terhadap organisasi.

**Ground Truth:**
Pemrioritasan insiden siber dilakukan dengan mempertimbangkan tiga hal: (1) kategori Sistem Elektronik yang terdampak, termasuk apakah sistem tersebut termasuk Infrastruktur Informasi Vital (IIV) atau bukan; (2) ruang lingkup dampak insiden siber, yaitu seberapa luas sistem dan pihak yang terdampak; dan (3) identifikasi penyerang yang menyebabkan insiden. Laporan insiden dikumpulkan, dikategorisasikan, dan diprioritaskan sesuai dampak risiko terhadap organisasi oleh Tim Tanggap Insiden Siber.

---

### BSSN-010

**Tipe Insiden:** general | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.92 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Apa saja langkah pelaksanaan rekam cadang data yang harus dilakukan organisasi sesuai panduan pengelolaan Insiden Siber BSSN, termasuk enkripsi dan dokumentasi rekam cadang?

**Jawaban Sistem (Kandidat):**
Langkah-langkah pelaksanaan rekam cadang data yang harus dilakukan organisasi sesuai panduan pengelolaan Insiden Siber BSSN meliputi beberapa kegiatan penting. Pertama, organisasi harus memastikan media penyimpanan rekam cadang disimpan secara aman. Kedua, sebelum melakukan pemusnahan data yang disimpan pada media rekam cadang, persetujuan dari pimpinan organisasi harus diperoleh. Ketiga, media rekam cadang harus diformat ulang dan dipastikan bahwa data sudah tidak dapat diakses lagi. Selain itu, prosedur rekam cadang harus dilakukan secara optimal dengan memanfaatkan perangkat penyimpanan yang memiliki fitur penjadwalan pekerjaan (job-scheduling). Data yang disimpan pada media penyimpanan rekam cadang juga harus dienkripsi untuk menjaga keamanannya. Terakhir, hasil pelaksanaan rekam cadang data harus didokumentasikan dengan baik untuk memastikan bahwa semua langkah telah dilakukan sesuai dengan ketentuan yang berlaku.

**Ground Truth:**
Pelaksanaan rekam cadang data sesuai panduan BSSN mencakup: (1) melaksanakan simulasi secara periodik terhadap prosedur pemulihan sistem atau data dari media penyimpanan rekam cadang, (2) melakukan prosedur rekam cadang secara optimal dengan memanfaatkan perangkat penyimpanan yang memiliki fitur job-scheduling, (3) melakukan enkripsi terhadap data yang disimpan pada media penyimpanan rekam cadang, (4) menentukan waktu pelaksanaan rekam cadang terhadap data organisasi disesuaikan dengan tingkat kritikalitas data dan kebutuhan organisasi, serta (5) mendokumentasikan hasil pelaksanaan rekam cadang data.

---
