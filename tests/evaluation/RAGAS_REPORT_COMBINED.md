# Laporan Evaluasi RAGAS — Gabungan 3 Dataset

**Tanggal evaluasi:** 21 June 2026  
**Model LLM:** GPT-4o (via GitHub Models)  
**Pipeline:** Agentic RAG + Hybrid Retrieval (Semantic + BM25) + Reranker + query_knowledge intent  
**Total soal:** 30 (10 per dataset)

---

## Ringkasan Skor Keseluruhan

| Metrik | BSSN | NIST | MITRE | **Rata-rata** |
|---|---|---|---|---|
| Faithfulness | 0.9714 | 0.9507 | 0.8499 | **0.9240** |
| Answer Relevancy | 0.8644 | 0.8400 | 0.8690 | **0.8578** |
| Context Relevance | 1.0000 | 1.0000 | 0.9500 | **0.9833** |

---

## Skor Per Pertanyaan — Semua Dataset

| ID | Dataset | Faithfulness | Answer Relevancy | Context Relevance |
|---|---|---|---|---|
| BSSN-001 | BSSN | 1.00 ✅ | 0.86 ✅ | 1.00 ✅ |
| BSSN-002 | BSSN | 1.00 ✅ | 0.79 🟡 | 1.00 ✅ |
| BSSN-003 | BSSN | 1.00 ✅ | 0.81 🟡 | 1.00 ✅ |
| BSSN-004 | BSSN | 1.00 ✅ | 0.95 ✅ | 1.00 ✅ |
| BSSN-005 | BSSN | 1.00 ✅ | 0.82 🟡 | 1.00 ✅ |
| BSSN-006 | BSSN | 1.00 ✅ | 0.81 🟡 | 1.00 ✅ |
| BSSN-007 | BSSN | 1.00 ✅ | 0.86 ✅ | 1.00 ✅ |
| BSSN-008 | BSSN | 1.00 ✅ | 0.93 ✅ | 1.00 ✅ |
| BSSN-009 | BSSN | 0.71 🟡 | 0.89 ✅ | 1.00 ✅ |
| BSSN-010 | BSSN | 1.00 ✅ | 0.92 ✅ | 1.00 ✅ |
| QA-001 | NIST | 1.00 ✅ | 0.78 🟡 | 1.00 ✅ |
| QA-002 | NIST | 1.00 ✅ | 0.82 🟡 | 1.00 ✅ |
| QA-003 | NIST | 0.89 ✅ | 0.80 🟡 | 1.00 ✅ |
| QA-004 | NIST | 0.90 ✅ | 0.76 🟡 | 1.00 ✅ |
| QA-005 | NIST | 1.00 ✅ | 0.83 🟡 | 1.00 ✅ |
| QA-006 | NIST | 0.91 ✅ | 0.82 🟡 | 1.00 ✅ |
| QA-007 | NIST | 0.90 ✅ | 0.77 🟡 | 1.00 ✅ |
| QA-008 | NIST | 0.91 ✅ | 0.99 ✅ | 1.00 ✅ |
| QA-009 | NIST | 1.00 ✅ | 0.86 ✅ | 1.00 ✅ |
| QA-010 | NIST | 1.00 ✅ | 0.96 ✅ | 1.00 ✅ |
| QA-011 | MITRE | 1.00 ✅ | 0.83 🟡 | 1.00 ✅ |
| QA-012 | MITRE | 0.88 ✅ | 0.92 ✅ | 1.00 ✅ |
| QA-013 | MITRE | 1.00 ✅ | 0.84 🟡 | 1.00 ✅ |
| QA-014 | MITRE | 0.83 🟡 | 0.91 ✅ | 1.00 ✅ |
| QA-015 | MITRE | 0.67 🔴 | 0.80 🟡 | 0.50 🔴 |
| QA-016 | MITRE | 1.00 ✅ | 0.81 🟡 | 1.00 ✅ |
| QA-017 | MITRE | 0.70 🟡 | 0.88 ✅ | 1.00 ✅ |
| QA-018 | MITRE | 0.86 ✅ | 0.87 ✅ | 1.00 ✅ |
| QA-019 | MITRE | 0.90 ✅ | 0.89 ✅ | 1.00 ✅ |
| QA-020 | MITRE | 0.67 🔴 | 0.93 ✅ | 1.00 ✅ |

---

## Detail Per Dataset

### BSSN — Peraturan BSSN Nomor 1 Tahun 2024 tentang Pengelolaan Insiden Siber

| Metrik | Skor |
|---|---|
| Faithfulness | **0.9714** |
| Answer Relevancy | **0.8644** |
| Context Relevance | **1.0000** |

#### BSSN-001

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.86 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Kami ingin tahu cara mengenali kalau komputer atau sistem kantor sedang diserang atau mengalami insiden siber. Tanda-tanda apa yang perlu kami waspadai sehari-hari?

**Jawaban Sistem:**
Untuk mengenali jika komputer atau sistem kantor sedang diserang atau mengalami insiden siber, ada beberapa tanda yang perlu diwaspadai. Pertama, antimalware dapat memberikan peringatan saat mendeteksi host atau media yang terinfeksi malware. Kedua, administrator mungkin melihat adanya file baru dengan nama yang tidak biasa. Ketiga, log pada aplikasi dapat mencatat adanya percobaan login yang banyak dari IP address yang tidak diketahui. Keempat, administrator mungkin melihat banyak surat elektronik yang tertolak oleh sistem dengan konten yang anomali. Tanda-tanda ini dapat menjadi indikasi awal bahwa sistem sedang mengalami insiden siber dan memerlukan perhatian lebih lanjut.

**Ground Truth:**
Tanda-tanda yang mengindikasikan adanya insiden siber antara lain: (1) perangkat antimalware memberi peringatan saat mendeteksi host atau media yang terinfeksi, (2) administrator menemukan file baru dengan nama yang tidak biasa, (3) log aplikasi mencatat banyak percobaan login dari IP address yang tidak dikenal, (4) banyak surat elektronik yang tertolak oleh sistem dengan konten yang anomali, dan (5) IPS/IDS/Firewall pada jaringan memberi peringatan adanya intrusi. Indikasi-indikasi tersebut perlu segera dilaporkan kepada tim pengelola sistem untuk ditindaklanjuti.

---

#### BSSN-002

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.79 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Saat serangan siber masih aktif dan sistem kami terdampak, langkah pengisolasian dan pembatasan apa saja yang harus dilakukan sesuai panduan pengelolaan insiden siber BSSN?

**Jawaban Sistem:**
Saat serangan siber masih aktif dan sistem terdampak, langkah pengisolasian dan pembatasan yang harus dilakukan sesuai panduan pengelolaan insiden siber BSSN meliputi memastikan Insiden Siber diisolasi dan dimitigasi sesuai rencana tanggap Insiden Siber. Selain itu, penting untuk mengumpulkan dan memelihara bukti Insiden Siber dari Sistem Elektronik terdampak. Langkah-langkah ini termasuk mengategorikan informasi mengenai Insiden Siber yang terdeteksi dan menyimpannya sesuai ukuran dampak terkait keamanan, penyebab insiden, dan faktor lainnya yang diperlukan. Juga, melakukan forensik digital terhadap aset informasi yang terdampak untuk menemukenali penyebab Insiden Siber. Pemantauan pada jaringan yang terkena Insiden Siber juga harus dilakukan, dan jika terdapat paket yang dicurigai atau anomali, segera blokir dan dokumentasikan, termasuk mencatat sumber IP, bentuk paket, waktu, dan lainnya.

**Ground Truth:**
Prosedur containment berdasarkan panduan BSSN Nomor 1 Tahun 2024 meliputi: (1) isolasi sistem yang terkena insiden, (2) backup data yang berkaitan dengan insiden seperti log dan screenshot, (3) identifikasi semua layanan dan koneksi yang terhubung, (4) identifikasi metode penyerang saat masuk ke sistem pertama kali melalui log sistem, (5) periksa kode-kode berbahaya yang ada dalam sistem, dan (6) lakukan pemantauan pada jaringan — jika terdapat paket yang dicurigai atau anomali, segera blokir dan dokumentasikan termasuk sumber IP, bentuk paket, dan waktu kejadian.

---

#### BSSN-003

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.81 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Apa saja cara penghapusan dan eradikasi penyebab Insiden Siber dari Sistem Elektronik yang terdampak menurut panduan pengelolaan insiden siber BSSN?

**Jawaban Sistem:**
Penghapusan dan eradikasi penyebab Insiden Siber dari Sistem Elektronik yang terdampak dilakukan dengan beberapa cara. Pertama, menentukan tanda dan sebab dari suatu Insiden Siber. Kedua, melakukan restore backup untuk mendapatkan sistem yang baru dan segar. Ketiga, menghapus penyebab Insiden Siber, seperti malware. Keempat, menonaktifkan akun pengguna yang terkena Insiden Siber. Kelima, melakukan reset password jika diperlukan. Terakhir, melakukan mitigasi terhadap kerentanan yang tereksploitasi saat Insiden Siber terjadi.

**Ground Truth:**
Penghapusan atau eradikasi Insiden Siber dilakukan untuk menghilangkan komponen Insiden Siber termasuk penghapusan kerentanan Sistem Elektronik. Penghapusan dilakukan dengan beberapa cara: (1) menentukan tanda dan sebab dari suatu Insiden Siber, (2) melakukan restore backup untuk mendapatkan new fresh system, (3) menghapus penyebab Insiden Siber seperti malware, (4) menonaktifkan akun pengguna yang terkena Insiden Siber, (5) melakukan reset password jika diperlukan, (6) melakukan mitigasi terhadap kerentanan yang tereksploitasi saat Insiden Siber, (7) mengidentifikasi semua host yang terkena Insiden Siber, dan (8) melakukan improvisasi pertahanan dan vulnerability analysis untuk melihat potensi ancaman yang dapat terjadi.

---

#### BSSN-004

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.95 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Apa yang harus kami lakukan untuk mengumpulkan dan memelihara bukti saat terjadi insiden siber di organisasi kami?

**Jawaban Sistem:**
Untuk mengumpulkan dan memelihara bukti saat terjadi insiden siber di organisasi Anda, langkah-langkah yang harus dilakukan meliputi: mengategorikan informasi mengenai insiden siber yang terdeteksi dan menyimpannya sesuai ukuran dampak terkait keamanan, penyebab insiden, dan faktor lainnya yang diperlukan. Selain itu, lakukan forensik digital terhadap aset informasi yang terdampak insiden siber untuk menemukenali penyebab insiden siber sesuai dengan ketentuan peraturan. Pastikan juga untuk mengumpulkan bukti insiden siber dari sistem elektronik terdampak, termasuk log, screenshot, dan data lainnya yang relevan.

**Ground Truth:**
Pada kegiatan pengumpulan dan pemeliharaan bukti insiden siber, hal-hal yang perlu dilakukan antara lain: (1) mengategorikan informasi mengenai insiden siber yang terdeteksi dan menyimpannya sesuai ukuran dampak terkait keamanan, penyebab insiden, dan faktor lainnya; (2) melakukan forensik digital terhadap aset informasi yang terdampak untuk menemukenali penyebab insiden siber sesuai ketentuan peraturan perundang-undangan; serta (3) mengumpulkan bukti berupa log, screenshot, dan data lain yang berkaitan dengan insiden untuk keperluan analisis lebih lanjut.

---

#### BSSN-005

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.82 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Kami menerima informasi keamanan dari tim siber yang diberi label TLP:AMBER dan TLP:GREEN. Apa arti kedua label itu dan sejauh mana kami boleh menyebarkannya?

**Jawaban Sistem:**
Label TLP:AMBER digunakan ketika informasi memerlukan dukungan untuk ditindaklanjuti secara efektif, namun membawa risiko terhadap privasi, reputasi, atau operasi jika dibagikan di luar organisasi yang terlibat. Penerima dapat membagikan informasi TLP:AMBER dengan anggota organisasi mereka sendiri dan kliennya, tetapi hanya berdasarkan kebutuhan untuk mengetahui guna melindungi organisasi mereka dan kliennya serta mencegah kerugian lebih lanjut. Jika sumber ingin membatasi berbagi hanya untuk organisasi, mereka harus menentukan TLP:AMBER+STRICT. Sementara itu, label TLP:GREEN digunakan ketika informasi berguna untuk meningkatkan kesadaran dalam komunitas yang lebih luas. Penerima dapat berbagi informasi TLP:GREEN dengan rekan dan organisasi mitra dalam komunitas mereka, tetapi tidak melalui saluran yang dapat diakses publik. Informasi TLP:GREEN tidak boleh dibagikan di luar komunitas.

**Ground Truth:**
TLP:AMBER berarti pengungkapan terbatas: penerima hanya dapat menyebarkan informasi berdasarkan kebutuhan untuk mengetahui (need-to-know) di dalam organisasinya dan kliennya, tidak lebih luas dari itu. TLP:GREEN berarti penerima dapat berbagi informasi dengan rekan dan organisasi mitra dalam komunitasnya, tetapi tidak boleh melalui saluran yang dapat diakses publik dan tidak boleh dibagikan di luar komunitas. Sumber menggunakan TLP:GREEN ketika informasi berguna untuk meningkatkan kesadaran dalam komunitas yang lebih luas. Jika lingkup komunitas tidak ditentukan, diasumsikan sebagai komunitas keamanan atau pertahanan siber.

---

#### BSSN-006

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.81 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Kami mendengar istilah Infrastruktur Informasi Vital atau IIV dalam sosialisasi keamanan siber. Apa definisi IIV menurut peraturan BSSN dan apa kewajiban pelaporan insiden siber yang berlaku jika sistem kami masuk kategori tersebut?

**Jawaban Sistem:**
Infrastruktur Informasi Vital (IIV) menurut Peraturan BSSN adalah Sistem Elektronik yang memanfaatkan teknologi informasi dan/atau teknologi operasional, baik berdiri sendiri maupun saling bergantung dengan Sistem Elektronik lainnya dalam menunjang sektor strategis. Jika terjadi gangguan, kerusakan, dan/atau kehancuran pada infrastruktur ini, maka akan berdampak serius terhadap kepentingan umum, pelayanan publik, pertahanan dan keamanan, atau perekonomian nasional. Kewajiban pelaporan insiden siber untuk sistem yang masuk kategori IIV adalah melaporkan insiden tersebut berdasarkan hasil penerapan manajemen risiko pada organisasi, yang berupa hasil analisis risiko berdasarkan dampak insiden siber yang ditimbulkan.

**Ground Truth:**
Infrastruktur Informasi Vital (IIV) adalah infrastruktur informasi yang jika terganggu, rusak, atau hancur dapat berdampak serius terhadap kepentingan umum, kenegaraan, pertahanan dan keamanan nasional, perekonomian nasional, dan/atau penyelenggaraan layanan publik. Jika sistem masuk kategori IIV, Tim Tanggap Insiden Siber organisasi wajib melaporkan insiden yang terjadi kepada TTIS sektoral dengan tembusan TTIS nasional paling lambat 1x24 jam setelah insiden ditemukan. Jika TTIS sektoral belum terbentuk, laporan disampaikan langsung ke Kementerian atau Lembaga sesuai sektornya dengan tembusan TTIS nasional.

---

#### BSSN-007

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.86 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Setelah insiden siber yang menimpa sistem kami selesai ditangani, apakah ada pemeriksaan ulang untuk memastikan sistemnya benar-benar sudah aman dan pulih?

**Jawaban Sistem:**
Setelah insiden siber ditangani, ada pemeriksaan ulang untuk memastikan keamanan sistem. Setiap aset informasi diperiksa keamanannya setelah penanggulangan insiden siber. Pemeriksaan ini dilakukan terhadap seluruh aset informasi yang berhubungan dengan sistem elektronik untuk memastikan bahwa sistem tersebut bersih dari indikasi ancaman atau serangan yang telah terjadi.

**Ground Truth:**
Ya. Setelah penanganan Insiden Siber, setiap aset informasi yang terdampak wajib diperiksa kembali keamanannya. Setelah upaya pemulihan Sistem Elektronik terdampak dilakukan, dilaksanakan kegiatan pengujian ulang terhadap fungsi vital dan fungsi pendukung untuk memastikan capaian pemulihan terpenuhi. Capaian pemulihan dinilai berdasarkan: (1) waktu pemulihan di bawah batas waktu maksimal yang ditetapkan berdasarkan rencana keberlangsungan kegiatan; dan (2) jumlah data yang terpulihkan sesuai dengan batas jumlah data minimal yang ditetapkan berdasarkan rencana keberlangsungan kegiatan.

---

#### BSSN-008

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.93 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Saat insiden siber terjadi, informasi minimum apa yang wajib disampaikan Tim Tanggap Insiden Siber kepada pihak yang terdampak?

**Jawaban Sistem:**
Saat insiden siber terjadi, informasi minimum yang wajib disampaikan Tim Tanggap Insiden Siber kepada pihak yang terdampak meliputi: informasi kontak pelapor, deskripsi insiden siber, kronologi insiden siber, dan dampak serangan.

**Ground Truth:**
Informasi Insiden Siber yang wajib disampaikan kepada pihak terdampak paling sedikit mencakup: (a) jenis indikasi Insiden Siber yang terjadi, (b) kode distribusi informasi, (c) sistem dan aset yang terkena dampak, serta (d) rekomendasi langkah mitigasi yang perlu dilakukan.

---

#### BSSN-009

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.71 🟡 | AR=0.89 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Saat kami menemukan insiden siber, faktor apa saja yang dipertimbangkan untuk menentukan prioritas dan seberapa serius dampaknya bagi organisasi kami?

**Jawaban Sistem:**
Untuk menentukan prioritas dan seberapa serius dampak insiden siber bagi organisasi, beberapa faktor perlu dipertimbangkan. Pertama, kategori Sistem Elektronik yang terdampak harus diketahui. Kedua, ruang lingkup dampak insiden siber harus dianalisis untuk menentukan tim tanggap insiden yang tepat. Ketiga, pemrioritasan insiden siber dilakukan dengan mempertimbangkan kategori Sistem Elektronik dan ruang lingkup dampak insiden tersebut. Selain itu, penting untuk memastikan bahwa insiden siber dikategorikan sesuai kriteria yang telah ditetapkan, dan laporan insiden siber dikumpulkan, dikategorisasikan, serta diprioritaskan berdasarkan dampak risiko terhadap organisasi. Dengan demikian, langkah-langkah ini membantu dalam menentukan prioritas dan tingkat keseriusan dampak insiden siber terhadap organisasi.

**Ground Truth:**
Pemrioritasan insiden siber dilakukan dengan mempertimbangkan tiga hal: (1) kategori Sistem Elektronik yang terdampak, termasuk apakah sistem tersebut termasuk Infrastruktur Informasi Vital (IIV) atau bukan; (2) ruang lingkup dampak insiden siber, yaitu seberapa luas sistem dan pihak yang terdampak; dan (3) identifikasi penyerang yang menyebabkan insiden. Laporan insiden dikumpulkan, dikategorisasikan, dan diprioritaskan sesuai dampak risiko terhadap organisasi oleh Tim Tanggap Insiden Siber.

---

#### BSSN-010

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.92 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Apa saja langkah pelaksanaan rekam cadang data yang harus dilakukan organisasi sesuai panduan pengelolaan Insiden Siber BSSN, termasuk enkripsi dan dokumentasi rekam cadang?

**Jawaban Sistem:**
Langkah-langkah pelaksanaan rekam cadang data yang harus dilakukan organisasi sesuai panduan pengelolaan Insiden Siber BSSN meliputi beberapa kegiatan penting. Pertama, organisasi harus memastikan media penyimpanan rekam cadang disimpan secara aman. Kedua, sebelum melakukan pemusnahan data yang disimpan pada media rekam cadang, persetujuan dari pimpinan organisasi harus diperoleh. Ketiga, media rekam cadang harus diformat ulang dan dipastikan bahwa data sudah tidak dapat diakses lagi. Selain itu, prosedur rekam cadang harus dilakukan secara optimal dengan memanfaatkan perangkat penyimpanan yang memiliki fitur penjadwalan pekerjaan (job-scheduling). Data yang disimpan pada media penyimpanan rekam cadang juga harus dienkripsi untuk menjaga keamanannya. Terakhir, hasil pelaksanaan rekam cadang data harus didokumentasikan dengan baik untuk memastikan bahwa semua langkah telah dilakukan sesuai dengan ketentuan yang berlaku.

**Ground Truth:**
Pelaksanaan rekam cadang data sesuai panduan BSSN mencakup: (1) melaksanakan simulasi secara periodik terhadap prosedur pemulihan sistem atau data dari media penyimpanan rekam cadang, (2) melakukan prosedur rekam cadang secara optimal dengan memanfaatkan perangkat penyimpanan yang memiliki fitur job-scheduling, (3) melakukan enkripsi terhadap data yang disimpan pada media penyimpanan rekam cadang, (4) menentukan waktu pelaksanaan rekam cadang terhadap data organisasi disesuaikan dengan tingkat kritikalitas data dan kebutuhan organisasi, serta (5) mendokumentasikan hasil pelaksanaan rekam cadang data.

---

### NIST — NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide

| Metrik | Skor |
|---|---|
| Faithfulness | **0.9507** |
| Answer Relevancy | **0.8400** |
| Context Relevance | **1.0000** |

#### QA-001

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.78 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Dokumen dan kebijakan (policy) minimum apa yang wajib ada sebagai persiapan sebelum insiden siber terjadi?

**Jawaban Sistem:**
Untuk mempersiapkan diri sebelum insiden siber terjadi, organisasi harus memiliki kebijakan dan dokumen minimum yang mencakup beberapa elemen penting. Pertama, organisasi perlu membuat kebijakan dan rencana respons insiden yang jelas. Kedua, prosedur untuk menangani dan melaporkan insiden harus dikembangkan. Ketiga, panduan untuk berkomunikasi dengan pihak luar terkait insiden harus ditetapkan. Keempat, struktur tim dan model staf harus dipilih dengan tepat. Kelima, hubungan dan jalur komunikasi antara tim respons insiden dan kelompok lain, baik internal seperti departemen hukum maupun eksternal seperti lembaga penegak hukum, harus dibangun. Terakhir, organisasi harus menentukan layanan apa yang harus disediakan oleh tim respons insiden. Semua elemen ini penting untuk memastikan kesiapan dalam menghadapi insiden siber.

**Ground Truth:**
Kembangkan rencana respons insiden berdasarkan kebijakan respons insiden organisasi. Kebijakan harus mencakup pernyataan komitmen manajemen, tujuan dan ruang lingkup kebijakan, serta definisi insiden. Rencana memberikan peta jalan implementasi program respons insiden termasuk tujuan jangka pendek dan panjang serta metrik pengukuran.

---

#### QA-002

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.82 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Laporan via WhatsApp/japri sering minim detail. Elemen data minimum apa yang harus dikumpulkan saat menerima laporan insiden dari pelapor?

**Jawaban Sistem:**
Ketika menerima laporan insiden, penting untuk mengumpulkan elemen data minimum agar penanganan insiden dapat dilakukan dengan efektif. Elemen data yang harus dikumpulkan meliputi: nama pengguna, ID pengguna, dan informasi kontak seperti nomor telepon dan alamat email. Selain itu, informasi mengenai lokasi workstation, nomor model, nomor seri, nama host, dan alamat IP juga harus dicatat. Tanggal dan waktu kejadian insiden perlu dicatat dengan tepat. Penjelasan langkah demi langkah mengenai apa yang terjadi, termasuk tindakan yang dilakukan terhadap workstation setelah infeksi ditemukan, juga harus disertakan. Penjelasan ini harus rinci, termasuk kata-kata persis dari pesan yang ditampilkan oleh malware atau peringatan dari perangkat lunak antivirus.

**Ground Truth:**
Kumpulkan nama pengguna, ID pengguna, dan informasi kontak pelapor. Dapatkan lokasi, model, nomor seri, hostname, dan alamat IP workstation terdampak. Catat tanggal dan waktu insiden beserta penjelasan langkah demi langkah kejadian termasuk tindakan yang sudah dilakukan sejak insiden ditemukan.

---

#### QA-003

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.89 ✅ | AR=0.80 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Saat dua insiden datang bersamaan, bagaimana cara menentukan prioritas berdasarkan dampak terhadap operasional kantor dan dampak terhadap kerahasiaan data organisasi?

**Jawaban Sistem:**
Untuk menentukan prioritas ketika dua insiden datang bersamaan, organisasi harus mempertimbangkan dampak fungsional dan dampak terhadap informasi. Dampak fungsional merujuk pada bagaimana insiden tersebut mempengaruhi fungsi bisnis yang disediakan oleh sistem IT yang terkena dampak, termasuk dampak negatif terhadap pengguna sistem tersebut. Sementara itu, dampak terhadap informasi mencakup efek insiden pada kerahasiaan, integritas, dan ketersediaan informasi organisasi. Dengan mempertimbangkan kedua faktor ini, organisasi dapat menentukan insiden mana yang memiliki dampak lebih besar dan memerlukan perhatian segera. Panduan tertulis harus dibuat untuk membantu dalam proses ini, memastikan bahwa penanganan insiden tidak dilakukan berdasarkan urutan kedatangan tetapi berdasarkan prioritas yang ditentukan oleh dampak tersebut.

**Ground Truth:**
Prioritaskan penanganan insiden berdasarkan dampak fungsional terhadap sistem IT yang mempengaruhi fungsi bisnis dan dampak terhadap kerahasiaan, integritas, dan ketersediaan informasi organisasi. Gunakan panduan tertulis yang menetapkan seberapa cepat tim harus merespons dan tindakan apa yang harus diambil berdasarkan faktor dampak fungsional, dampak informasi, dan upaya pemulihan.

---

#### QA-004

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.90 ✅ | AR=0.76 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Saat serangan siber masih berjalan, mengapa tindakan containment atau isolasi sistem harus dilakukan terlebih dahulu daripada langsung mematikan sistem?

**Jawaban Sistem:**
Tindakan containment atau isolasi sistem harus dilakukan terlebih dahulu daripada langsung mematikan sistem karena containment mencegah perluasan insiden dan menghindari kerusakan tambahan serta menghindari pembebanan sumber daya organisasi. Containment memberikan waktu untuk mengembangkan strategi remediasi yang disesuaikan. Selain itu, containment memungkinkan pengambilan keputusan yang lebih mudah, seperti mematikan sistem, memutuskan koneksi dari jaringan, atau menonaktifkan fungsi tertentu, jika ada strategi dan prosedur yang telah ditentukan sebelumnya.

**Ground Truth:**
Lakukan containment terlebih dahulu untuk mencegah perluasan insiden sebelum kehabisan sumber daya atau kerusakan meningkat. Containment memberikan waktu untuk mengembangkan strategi remediasi yang tepat. Konfigurasikan teknologi keamanan siber seperti antivirus dan fitur keamanan sistem operasi untuk secara otomatis melakukan tindakan containment seperti mengkarantina malware atau memindahkan endpoint ke jaringan remediasi terisolasi.

---

#### QA-005

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.83 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Bagaimana cara memantau penggunaan akun login yang tidak sah dan perangkat bermasalah agar akses tidak sah dapat dideteksi dan dimitigasi?

**Jawaban Sistem:**
Untuk memantau penggunaan kredensial tidak sah, penting untuk memonitor upaya otentikasi guna mengidentifikasi serangan terhadap kredensial dan penggunaan kredensial yang tidak sah. Selain itu, pemantauan terhadap perangkat keras dan perangkat lunak, termasuk mekanisme perlindungan keamanan siber, harus dilakukan untuk mendeteksi tanda-tanda perusakan, kegagalan, atau kompromi. Untuk endpoint yang bermasalah, seperti yang mengalami masalah kesehatan siber (misalnya, patch yang hilang, infeksi malware, atau perangkat lunak tidak sah), endpoint tersebut harus diarahkan ke lingkungan remediasi sebelum akses diizinkan. Langkah-langkah ini dapat membantu mendeteksi dan memitigasi akses tidak sah secara efektif.

**Ground Truth:**
Pantau penggunaan kredensial yang tidak sah dan pantau konfigurasi perangkat keras maupun lunak untuk penyimpangan dari security baseline. Monitor endpoint untuk masalah kesehatan siber seperti patch yang hilang, infeksi malware, atau perangkat lunak tidak sah, dan arahkan endpoint bermasalah ke lingkungan remediasi sebelum akses diizinkan kembali.

---

#### QA-006

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.91 ✅ | AR=0.82 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Setelah mengklik email phishing yang mencurigakan, bagaimana prosedur pelaporan insiden phishing agar tim respons insiden dapat segera menanganinya?

**Jawaban Sistem:**
Setelah mengklik email phishing yang mencurigakan, prosedur pelaporan insiden phishing harus mencakup verifikasi bahwa insiden keamanan siber telah terjadi, kemudian memperkirakan tingkat keparahan insiden dan tingkat urgensi yang diperlukan untuk meresponsnya. Organisasi harus memiliki mekanisme untuk pihak ketiga melaporkan kemungkinan insiden yang melibatkan organisasi. Laporan ini harus dipantau dengan cermat dan ditanggapi dengan serius. Misalnya, organisasi mungkin dihubungi oleh pihak yang mengklaim bahwa sistemnya diserang oleh sistem di organisasi tersebut. Pengguna eksternal dapat melaporkan indikator lain, seperti layanan yang tidak tersedia. Tim respons insiden lainnya juga dapat melaporkan insiden kepada organisasi. Insiden harus dikategorikan dan diprioritaskan untuk memastikan respons yang tepat dan efisien.

**Ground Truth:**
Laporkan insiden untuk memverifikasi apakah insiden siber benar-benar terjadi dan perkirakan tingkat keparahan serta urgensi respons. Pastikan mekanisme pelaporan tersedia agar siapapun dapat melaporkan kemungkinan insiden. Gunakan berbagai metode pelaporan yang tersedia seperti nomor telepon darurat, email, atau formulir web sesuai urgensi dan sensitivitas insiden.

---

#### QA-007

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.90 ✅ | AR=0.77 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Komputer jadi lambat, muncul pop-up aneh, dan file sulit dibuka. Apa yang harus dilakukan tim untuk merespons kemungkinan insiden malware ini?

**Jawaban Sistem:**
Ketika komputer mengalami gejala seperti menjadi lambat, muncul pop-up aneh, dan file sulit dibuka, ini bisa menjadi indikasi adanya insiden malware. Langkah pertama yang harus dilakukan adalah menggunakan perangkat lunak antivirus untuk mendeteksi dan mengidentifikasi malware yang mungkin telah menginfeksi sistem. Jika ditemukan bahwa sistem telah terinfeksi, penting untuk segera membersihkan semua efek dari insiden tersebut, termasuk infeksi malware, materi yang tidak pantas, file Trojan horse, dan perubahan lain yang dibuat oleh insiden. Jika sistem telah sepenuhnya dikompromikan, pertimbangkan untuk membangun ulang sistem dari awal atau memulihkannya dari cadangan yang diketahui baik. Selain itu, identifikasi dan mitigasi semua kerentanan yang dieksploitasi oleh insiden tersebut sangat penting untuk mencegah terulangnya insiden yang sama di masa depan. Ini termasuk kerentanan dalam sistem operasi atau aplikasi yang digunakan. Dengan melakukan langkah-langkah ini, tim dapat merespons insiden malware dengan lebih efektif dan mencegah kerusakan lebih lanjut pada sistem.

**Ground Truth:**
Identifikasi dan mitigasi semua kerentanan yang dieksploitasi oleh malware. Hapus malware, materi yang tidak sesuai, dan komponen berbahaya lainnya dari sistem yang terdampak. Jika ditemukan host lain yang terinfeksi, ulangi langkah deteksi dan analisis untuk mengidentifikasi semua host terpengaruh, kemudian lakukan containment dan eradikasi untuk setiap host tersebut.

---

#### QA-008

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.91 ✅ | AR=0.99 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Bagaimana prosedur yang benar untuk menangani dan mendokumentasikan bukti digital, termasuk rantai penguasaan bukti, selama penanganan insiden keamanan siber?

**Jawaban Sistem:**
Prosedur yang benar untuk menangani dan mendokumentasikan bukti digital selama penanganan insiden keamanan siber melibatkan beberapa langkah penting. Pertama, semua informasi harus mulai direkam segera setelah tim mencurigai bahwa insiden telah terjadi. Setiap langkah yang diambil, dari saat insiden terdeteksi hingga penyelesaiannya, harus didokumentasikan dan diberi cap waktu. Informasi ini dapat digunakan sebagai bukti di pengadilan jika penuntutan hukum dilakukan. Selain itu, data insiden harus dilindungi karena sering kali mengandung informasi sensitif mengenai kerentanan, pelanggaran keamanan, dan pengguna yang mungkin telah melakukan tindakan yang tidak pantas. Akses ke data insiden harus dibatasi dengan tepat, baik secara logis maupun fisik. Tim juga harus mengikuti prosedur yang telah ditetapkan untuk pengumpulan dan penanganan bukti, serta mendokumentasikan bagaimana semua bukti telah dipertahankan. Bukti harus selalu terhitung dan tim harus bertemu dengan staf hukum dan lembaga penegak hukum untuk mendiskusikan penanganan bukti, kemudian mengembangkan prosedur berdasarkan diskusi tersebut.

**Ground Truth:**
Dapatkan, jaga, amankan, dan dokumentasikan bukti yang terkait insiden. Buat salinan file log yang berisi bukti terkait insiden dari sistem yang terdampak. Setiap kali bukti berpindah tangan, dokumentasikan perpindahan tersebut dalam formulir chain of custody sesuai prosedur hukum yang berlaku agar bukti dapat diterima di pengadilan.

---

#### QA-009

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.86 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Apa langkah pembersihan dan pemulihan sistem yang terdampak insiden siber menurut NIST SP 800-61, termasuk restorasi dari backup dan penerapan patch keamanan?

**Jawaban Sistem:**
Langkah eradikasi dan pemulihan sistem yang terdampak insiden siber menurut NIST SP 800-61 mencakup beberapa tindakan penting. Pertama, semua efek dari insiden harus dihapus, termasuk infeksi malware, materi yang tidak sesuai, file Trojan horse, dan perubahan lain yang dibuat oleh insiden. Jika sistem telah sepenuhnya dikompromikan, maka perlu dibangun ulang dari awal atau dipulihkan dari backup yang diketahui baik. Selanjutnya, identifikasi dan mitigasi semua kerentanan yang dieksploitasi sangat penting agar insiden tidak terulang. Dalam proses pemulihan, personel harus mengembalikan sistem ke operasi normal, memastikan bahwa sistem berfungsi dengan baik, dan jika perlu, memperbaiki kerentanan untuk mencegah insiden serupa. Operasi pemulihan termasuk memulihkan sistem dari backup yang bersih, membangun ulang sistem, mengganti file yang dikompromikan dengan versi yang bersih, menginstal patch, mengganti kata sandi, dan memperketat kontrol keamanan.

**Ground Truth:**
Selama pemulihan, personel memulihkan sistem ke operasi normal dengan merestorasi dari backup yang bersih, merekonstruksi sistem, mengganti file yang terkompromi dengan versi bersih, memasang patch, dan memperketat kontrol keamanan. Eradikasi dan pemulihan dilakukan secara bertahap dengan perubahan bernilai tinggi di fase awal untuk mencegah insiden berulang.

---

#### QA-010

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.96 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Bagaimana cara meningkatkan kesadaran dan edukasi pengguna agar mampu mendeteksi dan melaporkan serangan phishing serta social engineering?

**Jawaban Sistem:**
Untuk meningkatkan kesadaran dan edukasi pengguna dalam mendeteksi dan melaporkan serangan phishing serta social engineering, penting untuk mengedukasi pengguna mengenai kebijakan dan prosedur penggunaan jaringan, sistem, dan aplikasi yang tepat. Pelajaran yang relevan dari insiden sebelumnya juga harus dibagikan kepada pengguna agar mereka dapat memahami bagaimana tindakan mereka dapat mempengaruhi organisasi. Dengan meningkatkan kesadaran pengguna mengenai insiden, frekuensi insiden dapat dikurangi. Selain itu, staf IT harus dilatih agar dapat memelihara jaringan, sistem, dan aplikasi sesuai dengan standar keamanan organisasi. Edukasi dan kesadaran adalah pengganda sumber daya—semakin banyak pengguna dan staf teknis yang mengetahui tentang cara mendeteksi, melaporkan, dan merespons insiden, semakin sedikit beban yang terjadi pada organisasi.

**Ground Truth:**
Laporkan insiden ini melalui saluran resmi organisasi agar tim menentukan apakah ini merupakan insiden siber. Tingkatkan edukasi dan kesadaran pengguna — semakin banyak yang memahami cara mendeteksi, melaporkan, dan merespons insiden social engineering, semakin rendah dampaknya. Pastikan hanya satu grup resmi dalam organisasi yang mendistribusikan advisori keamanan untuk menghindari informasi yang bertentangan.

---

### MITRE — MITRE ATT&CK Framework — Teknik Serangan dan Mitigasi

| Metrik | Skor |
|---|---|
| Faithfulness | **0.8499** |
| Answer Relevancy | **0.8690** |
| Context Relevance | **0.9500** |

#### QA-011

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.83 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Apa program pelatihan keamanan yang bisa kami terapkan untuk melindungi pegawai dari serangan phishing melalui email dengan tautan login palsu?

**Jawaban Sistem:**
Untuk melindungi pegawai dari serangan phishing melalui email dengan tautan login palsu, program pelatihan keamanan yang dapat diterapkan meliputi beberapa langkah. Pertama, edukasi pegawai tentang cara mengenali upaya phishing, termasuk email yang mencurigakan dan tautan login palsu. Kedua, buat program pelatihan komprehensif yang mencakup modul tentang phishing, manajemen kata sandi, dan pelaporan insiden. Ketiga, gunakan latihan simulasi phishing untuk mengukur kerentanan pengguna dan memberikan pelatihan lanjutan yang ditargetkan. Keempat, libatkan metode pembelajaran interaktif seperti kuis dan tantangan yang digamifikasi untuk meningkatkan keterlibatan. Kelima, masukkan pelatihan keamanan siber sebagai bagian dari proses orientasi bagi pegawai baru dan sediakan materi yang mudah dipahami tentang kebijakan penggunaan yang dapat diterima dan prosedur pelaporan. Terakhir, pastikan semua pegawai menyelesaikan kursus penyegaran berkala untuk tetap mendapatkan informasi terbaru tentang ancaman yang muncul dan teknik yang digunakan oleh penyerang.

**Ground Truth:**
Laksanakan program User Training untuk mendidik karyawan dalam mengenali, melaporkan, dan mencegah ancaman phishing seperti email spearphishing dengan tautan palsu. Desain modul pelatihan yang mencakup topik phishing, pengelolaan kata sandi, dan pelaporan insiden. Gunakan simulasi phishing untuk melatih respons pengguna terhadap serangan rekayasa sosial.

---

#### QA-012

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.88 ✅ | AR=0.92 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Perangkat terinfeksi malware setelah membuka lampiran email berbahaya. Apa langkah mitigasi malware dari lampiran email yang harus segera diambil?

**Jawaban Sistem:**
Langkah mitigasi malware dari lampiran email yang harus segera diambil meliputi beberapa tindakan. Pertama, isolasi sistem yang terkena insiden untuk mencegah penyebaran lebih lanjut. Selanjutnya, lakukan backup data yang berkaitan dengan insiden, seperti log dan screenshot, untuk keperluan analisis lebih lanjut. Identifikasi semua layanan dan koneksi yang terhubung untuk memastikan tidak ada jalur lain yang dapat digunakan oleh malware. Selain itu, identifikasi metode penyerang ketika masuk ke sistem pertama kali dengan melihat log pada sistem. Setelah itu, lakukan penghapusan penyebab insiden siber, seperti malware, dan jika diperlukan, lakukan reset password untuk akun pengguna yang terkena insiden. Terakhir, lakukan mitigasi terhadap kerentanan yang tereksploitasi saat insiden siber terjadi untuk mencegah kejadian serupa di masa depan.

**Ground Truth:**
Pasang dan perbarui perangkat lunak Antivirus/Antimalware di semua perangkat untuk mendeteksi dan memblokir malware dari lampiran email berbahaya. Gunakan pencegahan perilaku pada endpoint untuk mendeteksi dan memblokir aktivitas mencurigakan berdasarkan analisis perilaku proses. Terapkan isolasi aplikasi dan sandboxing untuk menjalankan lampiran email dalam lingkungan terkontrol sehingga kode berbahaya tidak mempengaruhi sistem utama.

---

#### QA-013

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.84 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Terjadi serangan ransomware yang mengenkripsi file pada server dan muncul pesan permintaan tebusan. Apa langkah mitigasi ransomware yang harus segera dilakukan?

**Jawaban Sistem:**
Langkah mitigasi ransomware yang harus segera dilakukan meliputi beberapa tindakan penting. Pertama, isolasi sistem yang terkena insiden untuk mencegah penyebaran lebih lanjut. Kedua, lakukan backup data yang berkaitan dengan insiden, seperti hasil pengumpulan bukti berbentuk log dan screenshot. Ketiga, identifikasi semua layanan dan koneksi yang terhubung untuk memahami ruang lingkup serangan. Keempat, identifikasi metode penyerang ketika masuk ke sistem pertama kali dengan memeriksa log pada sistem. Selain itu, penting untuk memeriksa kode-kode berbahaya yang ada dalam sistem dan melakukan pemantauan pada jaringan yang terkena insiden siber. Jika terdapat paket yang dicurigai atau anomali, segera blokir dan dokumentasikan. Terakhir, pastikan setiap aset informasi diperiksa keamanannya setelah penanggulangan insiden siber untuk memastikan tidak ada ancaman yang tersisa.

**Ground Truth:**
Lakukan backup data secara teratur dan simpan di lokasi yang terisolasi dari jaringan korporat untuk memastikan pemulihan dari serangan ransomware yang mengenkripsi data. Jadwalkan backup incremental harian dan backup penuh mingguan untuk semua server dan sistem kritis. Pastikan proses backup mencakup pengerasan sistem backup dan solusi penyimpanan yang aman.

---

#### QA-014

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.83 🟡 | AR=0.91 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Langkah backup data apa yang harus diterapkan organisasi untuk memulihkan sistem setelah insiden web defacement atau kerusakan data?

**Jawaban Sistem:**
Untuk memulihkan sistem setelah insiden web defacement atau kerusakan data, organisasi harus menerapkan langkah-langkah backup data yang meliputi: melakukan prosedur pemulihan sistem/data dari media penyimpanan apabila terjadi keadaan darurat, melaksanakan simulasi secara periodik terhadap prosedur pemulihan sistem/data dari media penyimpanan rekam cadang, dan melakukan prosedur rekam cadang secara optimal. Selain itu, organisasi juga harus memastikan setiap aset informasi diperiksa keamanannya setelah penanggulangan insiden siber dan memastikan bersih dari indikasi ancaman atau serangan yang telah terjadi.

**Ground Truth:**
Pulihkan konten website dari backup data yang tersimpan di lokasi terisolasi dari jaringan korporat untuk memulihkan integritas halaman yang terdeface. Terapkan jadwal backup data secara teratur termasuk backup incremental harian dan backup penuh mingguan untuk semua server web kritis.

---

#### QA-015

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.67 🔴 | AR=0.80 🟡 | CR=0.50 🔴

**Pertanyaan:**
> Beberapa pegawai kantor kami pernah menerima telepon dari seseorang yang mengaku teknisi IT dan meminta password atau akses ke komputer mereka. Bagaimana cara melindungi pegawai dari jenis penipuan semacam ini?

**Jawaban Sistem:**
Untuk melindungi pegawai dari penipuan yang melibatkan seseorang yang mengaku sebagai teknisi IT dan meminta password atau akses ke komputer, penting untuk memberikan edukasi kepada pegawai tentang cara mengidentifikasi upaya phishing dan menjaga keamanan informasi. Edukasi ini dapat mencakup cara mengenali tanda-tanda penipuan, seperti permintaan informasi sensitif yang tidak biasa, dan langkah-langkah yang harus diambil jika mereka menerima permintaan semacam itu. Selain itu, pegawai harus diajarkan untuk tidak memberikan informasi sensitif melalui telepon atau email tanpa verifikasi yang tepat. Dengan meningkatkan kesadaran dan pemahaman pegawai tentang ancaman ini, organisasi dapat mengurangi risiko terjadinya insiden keamanan siber yang disebabkan oleh penipuan semacam ini.

**Ground Truth:**
Laksanakan program pelatihan keamanan dan kesadaran (User Training) untuk mendidik pegawai agar tidak pernah memberikan informasi sensitif seperti password atau akses sistem kepada siapapun melalui telepon, termasuk yang mengaku sebagai staf IT. Pelatihan harus mencakup cara mengenali teknik rekayasa sosial, prosedur verifikasi identitas yang benar sebelum memberikan akses, dan cara melaporkan percobaan penipuan kepada tim keamanan.

---

#### QA-016

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=1.00 ✅ | AR=0.81 🟡 | CR=1.00 ✅

**Pertanyaan:**
> Terdeteksi penyalahgunaan akun — ada login berhasil menggunakan kredensial pegawai tanpa sepengetahuan pemiliknya. Apa langkah mitigasi akun yang dikompromikan ini?

**Jawaban Sistem:**
Untuk menangani penyalahgunaan akun yang dikompromikan, langkah-langkah mitigasi yang dapat diambil meliputi menonaktifkan akun pengguna yang terkena insiden siber dan melakukan reset password jika diperlukan. Selain itu, penting untuk melakukan analisis insiden siber guna mengetahui sistem elektronik yang terkena dan ruang lingkup dampaknya. Setelah penanggulangan insiden, pastikan setiap aset informasi diperiksa keamanannya untuk memastikan tidak ada indikasi ancaman atau serangan yang tersisa.

**Ground Truth:**
Implementasikan Multi-Factor Authentication untuk memastikan setiap login memerlukan verifikasi tambahan selain password, mencegah penyalahgunaan kredensial yang bocor. Terapkan kebijakan pengelolaan akun istimewa untuk membatasi akses dan memantau penggunaan akun dengan hak istimewa. Terapkan kebijakan kata sandi yang kuat termasuk persyaratan kompleksitas dan perubahan kata sandi segera.

---

#### QA-017

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.70 🟡 | AR=0.88 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Layanan publik mengalami gangguan akibat serangan DDoS — trafik jaringan mendadak meledak hingga layanan tidak tersedia. Apa langkah mitigasi serangan DDoS yang tepat?

**Jawaban Sistem:**
Untuk mengatasi serangan DDoS yang menyebabkan gangguan pada layanan publik, langkah-langkah mitigasi yang tepat meliputi: pertama, isolasi sistem yang terkena insiden untuk mencegah penyebaran lebih lanjut. Kedua, lakukan backup data yang berkaitan dengan insiden, seperti log dan screenshot, untuk keperluan analisis lebih lanjut. Ketiga, identifikasi semua layanan dan koneksi yang terhubung untuk mengetahui sumber serangan. Keempat, identifikasi metode penyerang ketika masuk ke sistem pertama kali dengan memeriksa log pada sistem. Kelima, periksa kode-kode berbahaya yang ada dalam sistem. Terakhir, lakukan pemantauan pada jaringan yang terkena insiden siber, dan jika terdapat paket yang dicurigai atau anomali, segera blokir dan dokumentasikan informasi seperti sumber IP, bentuk paket, dan waktu kejadian. Langkah-langkah ini akan membantu dalam menahan dan mengurangi dampak dari serangan DDoS tersebut.

**Ground Truth:**
Gunakan perangkat jaringan dan perangkat lunak endpoint untuk memfilter lalu lintas jaringan masuk, keluar, dan lateral guna mencegah dampak serangan DDoS pada layanan publik. Konfigurasikan filter jaringan untuk membatasi akses hanya dari sumber yang diotorisasi ke server yang menghadap publik.

---

#### QA-018

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.86 ✅ | AR=0.87 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Bagaimana cara memfilter lalu lintas jaringan untuk mencegah eksfiltrasi data dari sistem organisasi ke layanan eksternal yang tidak diotorisasi?

**Jawaban Sistem:**
Untuk memfilter lalu lintas jaringan dan mencegah eksfiltrasi data dari sistem organisasi ke layanan eksternal yang tidak diotorisasi, organisasi dapat melakukan pemantauan pada jaringan yang terkena Insiden Siber. Jika terdapat paket yang dicurigai atau anomali, langkah yang harus diambil adalah segera memblokir dan mendokumentasikan paket tersebut. Dokumentasi dapat mencakup sumber IP, bentuk paket, waktu, dan informasi relevan lainnya. Selain itu, organisasi harus mengidentifikasi semua layanan dan koneksi yang terhubung untuk memastikan tidak ada jalur yang tidak diotorisasi yang dapat digunakan untuk eksfiltrasi data. Langkah-langkah ini merupakan bagian dari prosedur penahanan insiden yang harus didokumentasikan dengan jelas untuk memfasilitasi pengambilan keputusan yang tepat.

**Ground Truth:**
Terapkan filter lalu lintas jaringan untuk membatasi akses ke layanan berbagi file publik yang tidak diotorisasi dan mencegah eksfiltrasi data lebih lanjut. Konfigurasikan kebijakan penggunaan akun dan terapkan prinsip hak akses minimum agar hanya pengguna yang berwenang yang dapat mengakses dan mentransfer dokumen sensitif ke layanan eksternal.

---

#### QA-019

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.90 ✅ | AR=0.89 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Ditemukan malware atau tool berbahaya yang diduga ditanam penyerang di perangkat. Apa langkah mitigasi untuk mendeteksi dan memblokir tool berbahaya tersebut?

**Jawaban Sistem:**
Untuk mendeteksi dan memblokir tool berbahaya seperti malware yang ditanam oleh penyerang, langkah mitigasi yang dapat dilakukan meliputi penggunaan antimalware yang dapat memberikan peringatan saat mendeteksi host atau media yang terinfeksi malware. Selain itu, penting untuk memantau log pada aplikasi untuk mencatat adanya tindakan percobaan login yang banyak dari IP address yang tidak diketahui. Administrator juga harus waspada terhadap file baru dengan nama yang tidak biasa dan surat elektronik yang tertolak oleh sistem dengan konten yang anomali. Analisis insiden siber juga perlu dilakukan untuk mengetahui sistem elektronik yang terkena insiden dan ruang lingkup dampaknya. Deteksi sumber insiden siber dapat dilakukan dengan mengidentifikasi informasi seperti lokasi, nomor serial, nomor model, hostname, MAC address, dan IP address dari komputer yang digunakan, serta log pada sistem operasi dan aplikasi. Penggunaan IPS/IDS/Firewall pada jaringan juga penting untuk memberikan peringatan saat terjadi intrusi pada jaringan.

**Ground Truth:**
Gunakan perangkat lunak Antivirus/Antimalware untuk mendeteksi dan memblokir tool berbahaya yang ditransfer penyerang ke sistem. Terapkan pencegahan perilaku pada endpoint untuk menganalisis dan memblokir eksekusi skrip atau tool yang tidak dikenal berdasarkan pola perilaku mencurigakan.

---

#### QA-020

**Tipe Insiden:** - | **Tingkat Keparahan:** -  
**Skor:** F=0.67 🔴 | AR=0.93 ✅ | CR=1.00 ✅

**Pertanyaan:**
> Perangkat lunak keamanan apa yang harus dipasang di endpoint untuk mendeteksi dan memblokir malware yang dijalankan pengguna dari file berbahaya?

**Jawaban Sistem:**
Perangkat lunak keamanan yang harus dipasang di endpoint untuk mendeteksi dan memblokir malware adalah perangkat lunak antimalware. Perangkat lunak ini harus diterapkan di seluruh organisasi, termasuk pada level host seperti sistem operasi server dan workstation, level server aplikasi seperti server email dan proxy web, serta level klien aplikasi seperti klien email dan klien pesan instan. Dengan demikian, perangkat lunak ini dapat mendeteksi dan menghentikan malware yang dijalankan pengguna dari file berbahaya.

**Ground Truth:**
Gunakan perangkat lunak Antivirus/Antimalware untuk mendeteksi dan memblokir malware yang terinstal dari file berbahaya yang dijalankan pengguna. Terapkan pencegahan perilaku pada endpoint untuk mendeteksi dan menghentikan proses mencurigakan yang berjalan sebagai akibat dari eksekusi file berbahaya tersebut.

---
