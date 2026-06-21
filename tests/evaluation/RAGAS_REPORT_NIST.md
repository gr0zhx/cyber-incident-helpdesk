# Laporan Evaluasi RAGAS — Dataset NIST

**Dokumen sumber:** NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide  
**Tanggal evaluasi:** 20 June 2026  
**Jumlah soal:** 10  
**Model LLM:** GPT-4o (via GitHub Models)  
**Pipeline:** Agentic RAG + Hybrid Retrieval (Semantic + BM25) + Reranker + query_knowledge intent

---

## Ringkasan Skor RAGAS

| Metrik | Skor Dataset Ini | Rata-rata 3 Dataset | Keterangan |
|---|---|---|---|
| Faithfulness | **0.9507** | 0.9196 | Jawaban grounded dalam konteks yang di-retrieve |
| Answer Relevancy | **0.8400** | 0.8505 | Jawaban relevan dan fokus terhadap pertanyaan |
| Context Relevance | **1.0000** | 0.9833 | Konteks yang diambil relevan dengan pertanyaan |

---

## Skor Per Pertanyaan

| ID | Faithfulness | Answer Relevancy | Context Relevance |
|---|---|---|---|
| QA-001 | 1.00 ✅ | 0.78 🟡 | 1.00 ✅ |
| QA-002 | 1.00 ✅ | 0.82 🟡 | 1.00 ✅ |
| QA-003 | 0.89 ✅ | 0.80 🟡 | 1.00 ✅ |
| QA-004 | 0.90 ✅ | 0.76 🟡 | 1.00 ✅ |
| QA-005 | 1.00 ✅ | 0.83 🟡 | 1.00 ✅ |
| QA-006 | 0.91 ✅ | 0.82 🟡 | 1.00 ✅ |
| QA-007 | 0.90 ✅ | 0.77 🟡 | 1.00 ✅ |
| QA-008 | 0.91 ✅ | 0.99 ✅ | 1.00 ✅ |
| QA-009 | 1.00 ✅ | 0.86 ✅ | 1.00 ✅ |
| QA-010 | 1.00 ✅ | 0.96 ✅ | 1.00 ✅ |

---

## Detail Pertanyaan, Jawaban Sistem, dan Ground Truth

### QA-001

**Tipe Insiden:** Malware | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.78 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Dokumen dan kebijakan (policy) minimum apa yang wajib ada sebagai persiapan sebelum insiden siber terjadi?

**Jawaban Sistem (Kandidat):**
Untuk mempersiapkan diri sebelum insiden siber terjadi, organisasi harus memiliki kebijakan dan dokumen minimum yang mencakup beberapa elemen penting. Pertama, organisasi perlu membuat kebijakan dan rencana respons insiden yang jelas. Kedua, prosedur untuk menangani dan melaporkan insiden harus dikembangkan. Ketiga, panduan untuk berkomunikasi dengan pihak luar terkait insiden harus ditetapkan. Keempat, struktur tim dan model staf harus dipilih dengan tepat. Kelima, hubungan dan jalur komunikasi antara tim respons insiden dan kelompok lain, baik internal seperti departemen hukum maupun eksternal seperti lembaga penegak hukum, harus dibangun. Terakhir, organisasi harus menentukan layanan apa yang harus disediakan oleh tim respons insiden. Semua elemen ini penting untuk memastikan kesiapan dalam menghadapi insiden siber.

**Ground Truth:**
Kembangkan rencana respons insiden berdasarkan kebijakan respons insiden organisasi. Kebijakan harus mencakup pernyataan komitmen manajemen, tujuan dan ruang lingkup kebijakan, serta definisi insiden. Rencana memberikan peta jalan implementasi program respons insiden termasuk tujuan jangka pendek dan panjang serta metrik pengukuran.

---

### QA-002

**Tipe Insiden:** Malware | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.82 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Laporan via WhatsApp/japri sering minim detail. Elemen data minimum apa yang harus dikumpulkan saat menerima laporan insiden dari pelapor?

**Jawaban Sistem (Kandidat):**
Ketika menerima laporan insiden, penting untuk mengumpulkan elemen data minimum agar penanganan insiden dapat dilakukan dengan efektif. Elemen data yang harus dikumpulkan meliputi: nama pengguna, ID pengguna, dan informasi kontak seperti nomor telepon dan alamat email. Selain itu, informasi mengenai lokasi workstation, nomor model, nomor seri, nama host, dan alamat IP juga harus dicatat. Tanggal dan waktu kejadian insiden perlu dicatat dengan tepat. Penjelasan langkah demi langkah mengenai apa yang terjadi, termasuk tindakan yang dilakukan terhadap workstation setelah infeksi ditemukan, juga harus disertakan. Penjelasan ini harus rinci, termasuk kata-kata persis dari pesan yang ditampilkan oleh malware atau peringatan dari perangkat lunak antivirus.

**Ground Truth:**
Kumpulkan nama pengguna, ID pengguna, dan informasi kontak pelapor. Dapatkan lokasi, model, nomor seri, hostname, dan alamat IP workstation terdampak. Catat tanggal dan waktu insiden beserta penjelasan langkah demi langkah kejadian termasuk tindakan yang sudah dilakukan sejak insiden ditemukan.

---

### QA-003

**Tipe Insiden:** Kebocoran Data | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=0.89 ✅ | Answer Relevancy=0.80 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Saat dua insiden datang bersamaan, bagaimana cara menentukan prioritas berdasarkan dampak terhadap operasional kantor dan dampak terhadap kerahasiaan data organisasi?

**Jawaban Sistem (Kandidat):**
Untuk menentukan prioritas ketika dua insiden datang bersamaan, organisasi harus mempertimbangkan dampak fungsional dan dampak terhadap informasi. Dampak fungsional merujuk pada bagaimana insiden tersebut mempengaruhi fungsi bisnis yang disediakan oleh sistem IT yang terkena dampak, termasuk dampak negatif terhadap pengguna sistem tersebut. Sementara itu, dampak terhadap informasi mencakup efek insiden pada kerahasiaan, integritas, dan ketersediaan informasi organisasi. Dengan mempertimbangkan kedua faktor ini, organisasi dapat menentukan insiden mana yang memiliki dampak lebih besar dan memerlukan perhatian segera. Panduan tertulis harus dibuat untuk membantu dalam proses ini, memastikan bahwa penanganan insiden tidak dilakukan berdasarkan urutan kedatangan tetapi berdasarkan prioritas yang ditentukan oleh dampak tersebut.

**Ground Truth:**
Prioritaskan penanganan insiden berdasarkan dampak fungsional terhadap sistem IT yang mempengaruhi fungsi bisnis dan dampak terhadap kerahasiaan, integritas, dan ketersediaan informasi organisasi. Gunakan panduan tertulis yang menetapkan seberapa cepat tim harus merespons dan tindakan apa yang harus diambil berdasarkan faktor dampak fungsional, dampak informasi, dan upaya pemulihan.

---

### QA-004

**Tipe Insiden:** Malware | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=0.90 ✅ | Answer Relevancy=0.76 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Saat serangan siber masih berjalan, mengapa tindakan containment atau isolasi sistem harus dilakukan terlebih dahulu daripada langsung mematikan sistem?

**Jawaban Sistem (Kandidat):**
Tindakan containment atau isolasi sistem harus dilakukan terlebih dahulu daripada langsung mematikan sistem karena containment mencegah perluasan insiden dan menghindari kerusakan tambahan serta menghindari pembebanan sumber daya organisasi. Containment memberikan waktu untuk mengembangkan strategi remediasi yang disesuaikan. Selain itu, containment memungkinkan pengambilan keputusan yang lebih mudah, seperti mematikan sistem, memutuskan koneksi dari jaringan, atau menonaktifkan fungsi tertentu, jika ada strategi dan prosedur yang telah ditentukan sebelumnya.

**Ground Truth:**
Lakukan containment terlebih dahulu untuk mencegah perluasan insiden sebelum kehabisan sumber daya atau kerusakan meningkat. Containment memberikan waktu untuk mengembangkan strategi remediasi yang tepat. Konfigurasikan teknologi keamanan siber seperti antivirus dan fitur keamanan sistem operasi untuk secara otomatis melakukan tindakan containment seperti mengkarantina malware atau memindahkan endpoint ke jaringan remediasi terisolasi.

---

### QA-005

**Tipe Insiden:** Akses Tidak Sah | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.83 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Bagaimana cara memantau penggunaan akun login yang tidak sah dan perangkat bermasalah agar akses tidak sah dapat dideteksi dan dimitigasi?

**Jawaban Sistem (Kandidat):**
Untuk memantau penggunaan kredensial tidak sah, penting untuk memonitor upaya otentikasi guna mengidentifikasi serangan terhadap kredensial dan penggunaan kredensial yang tidak sah. Selain itu, pemantauan terhadap perangkat keras dan perangkat lunak, termasuk mekanisme perlindungan keamanan siber, harus dilakukan untuk mendeteksi tanda-tanda perusakan, kegagalan, atau kompromi. Untuk endpoint yang bermasalah, seperti yang mengalami masalah kesehatan siber (misalnya, patch yang hilang, infeksi malware, atau perangkat lunak tidak sah), endpoint tersebut harus diarahkan ke lingkungan remediasi sebelum akses diizinkan. Langkah-langkah ini dapat membantu mendeteksi dan memitigasi akses tidak sah secara efektif.

**Ground Truth:**
Pantau penggunaan kredensial yang tidak sah dan pantau konfigurasi perangkat keras maupun lunak untuk penyimpangan dari security baseline. Monitor endpoint untuk masalah kesehatan siber seperti patch yang hilang, infeksi malware, atau perangkat lunak tidak sah, dan arahkan endpoint bermasalah ke lingkungan remediasi sebelum akses diizinkan kembali.

---

### QA-006

**Tipe Insiden:** Phishing | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=0.91 ✅ | Answer Relevancy=0.82 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Setelah mengklik email phishing yang mencurigakan, bagaimana prosedur pelaporan insiden phishing agar tim respons insiden dapat segera menanganinya?

**Jawaban Sistem (Kandidat):**
Setelah mengklik email phishing yang mencurigakan, prosedur pelaporan insiden phishing harus mencakup verifikasi bahwa insiden keamanan siber telah terjadi, kemudian memperkirakan tingkat keparahan insiden dan tingkat urgensi yang diperlukan untuk meresponsnya. Organisasi harus memiliki mekanisme untuk pihak ketiga melaporkan kemungkinan insiden yang melibatkan organisasi. Laporan ini harus dipantau dengan cermat dan ditanggapi dengan serius. Misalnya, organisasi mungkin dihubungi oleh pihak yang mengklaim bahwa sistemnya diserang oleh sistem di organisasi tersebut. Pengguna eksternal dapat melaporkan indikator lain, seperti layanan yang tidak tersedia. Tim respons insiden lainnya juga dapat melaporkan insiden kepada organisasi. Insiden harus dikategorikan dan diprioritaskan untuk memastikan respons yang tepat dan efisien.

**Ground Truth:**
Laporkan insiden untuk memverifikasi apakah insiden siber benar-benar terjadi dan perkirakan tingkat keparahan serta urgensi respons. Pastikan mekanisme pelaporan tersedia agar siapapun dapat melaporkan kemungkinan insiden. Gunakan berbagai metode pelaporan yang tersedia seperti nomor telepon darurat, email, atau formulir web sesuai urgensi dan sensitivitas insiden.

---

### QA-007

**Tipe Insiden:** Malware | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=0.90 ✅ | Answer Relevancy=0.77 🟡 | Context Relevance=1.00 ✅

**Pertanyaan:**
> Komputer jadi lambat, muncul pop-up aneh, dan file sulit dibuka. Apa yang harus dilakukan tim untuk merespons kemungkinan insiden malware ini?

**Jawaban Sistem (Kandidat):**
Ketika komputer mengalami gejala seperti menjadi lambat, muncul pop-up aneh, dan file sulit dibuka, ini bisa menjadi indikasi adanya insiden malware. Langkah pertama yang harus dilakukan adalah menggunakan perangkat lunak antivirus untuk mendeteksi dan mengidentifikasi malware yang mungkin telah menginfeksi sistem. Jika ditemukan bahwa sistem telah terinfeksi, penting untuk segera membersihkan semua efek dari insiden tersebut, termasuk infeksi malware, materi yang tidak pantas, file Trojan horse, dan perubahan lain yang dibuat oleh insiden. Jika sistem telah sepenuhnya dikompromikan, pertimbangkan untuk membangun ulang sistem dari awal atau memulihkannya dari cadangan yang diketahui baik. Selain itu, identifikasi dan mitigasi semua kerentanan yang dieksploitasi oleh insiden tersebut sangat penting untuk mencegah terulangnya insiden yang sama di masa depan. Ini termasuk kerentanan dalam sistem operasi atau aplikasi yang digunakan. Dengan melakukan langkah-langkah ini, tim dapat merespons insiden malware dengan lebih efektif dan mencegah kerusakan lebih lanjut pada sistem.

**Ground Truth:**
Identifikasi dan mitigasi semua kerentanan yang dieksploitasi oleh malware. Hapus malware, materi yang tidak sesuai, dan komponen berbahaya lainnya dari sistem yang terdampak. Jika ditemukan host lain yang terinfeksi, ulangi langkah deteksi dan analisis untuk mengidentifikasi semua host terpengaruh, kemudian lakukan containment dan eradikasi untuk setiap host tersebut.

---

### QA-008

**Tipe Insiden:** Kebocoran Data | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=0.91 ✅ | Answer Relevancy=0.99 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Bagaimana prosedur yang benar untuk menangani dan mendokumentasikan bukti digital, termasuk rantai penguasaan bukti, selama penanganan insiden keamanan siber?

**Jawaban Sistem (Kandidat):**
Prosedur yang benar untuk menangani dan mendokumentasikan bukti digital selama penanganan insiden keamanan siber melibatkan beberapa langkah penting. Pertama, semua informasi harus mulai direkam segera setelah tim mencurigai bahwa insiden telah terjadi. Setiap langkah yang diambil, dari saat insiden terdeteksi hingga penyelesaiannya, harus didokumentasikan dan diberi cap waktu. Informasi ini dapat digunakan sebagai bukti di pengadilan jika penuntutan hukum dilakukan. Selain itu, data insiden harus dilindungi karena sering kali mengandung informasi sensitif mengenai kerentanan, pelanggaran keamanan, dan pengguna yang mungkin telah melakukan tindakan yang tidak pantas. Akses ke data insiden harus dibatasi dengan tepat, baik secara logis maupun fisik. Tim juga harus mengikuti prosedur yang telah ditetapkan untuk pengumpulan dan penanganan bukti, serta mendokumentasikan bagaimana semua bukti telah dipertahankan. Bukti harus selalu terhitung dan tim harus bertemu dengan staf hukum dan lembaga penegak hukum untuk mendiskusikan penanganan bukti, kemudian mengembangkan prosedur berdasarkan diskusi tersebut.

**Ground Truth:**
Dapatkan, jaga, amankan, dan dokumentasikan bukti yang terkait insiden. Buat salinan file log yang berisi bukti terkait insiden dari sistem yang terdampak. Setiap kali bukti berpindah tangan, dokumentasikan perpindahan tersebut dalam formulir chain of custody sesuai prosedur hukum yang berlaku agar bukti dapat diterima di pengadilan.

---

### QA-009

**Tipe Insiden:** Ransomware | **Tingkat Keparahan:** 🟡 Sedang  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.86 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Apa langkah pembersihan dan pemulihan sistem yang terdampak insiden siber menurut NIST SP 800-61, termasuk restorasi dari backup dan penerapan patch keamanan?

**Jawaban Sistem (Kandidat):**
Langkah eradikasi dan pemulihan sistem yang terdampak insiden siber menurut NIST SP 800-61 mencakup beberapa tindakan penting. Pertama, semua efek dari insiden harus dihapus, termasuk infeksi malware, materi yang tidak sesuai, file Trojan horse, dan perubahan lain yang dibuat oleh insiden. Jika sistem telah sepenuhnya dikompromikan, maka perlu dibangun ulang dari awal atau dipulihkan dari backup yang diketahui baik. Selanjutnya, identifikasi dan mitigasi semua kerentanan yang dieksploitasi sangat penting agar insiden tidak terulang. Dalam proses pemulihan, personel harus mengembalikan sistem ke operasi normal, memastikan bahwa sistem berfungsi dengan baik, dan jika perlu, memperbaiki kerentanan untuk mencegah insiden serupa. Operasi pemulihan termasuk memulihkan sistem dari backup yang bersih, membangun ulang sistem, mengganti file yang dikompromikan dengan versi yang bersih, menginstal patch, mengganti kata sandi, dan memperketat kontrol keamanan.

**Ground Truth:**
Selama pemulihan, personel memulihkan sistem ke operasi normal dengan merestorasi dari backup yang bersih, merekonstruksi sistem, mengganti file yang terkompromi dengan versi bersih, memasang patch, dan memperketat kontrol keamanan. Eradikasi dan pemulihan dilakukan secara bertahap dengan perubahan bernilai tinggi di fase awal untuk mencegah insiden berulang.

---

### QA-010

**Tipe Insiden:** Phishing | **Tingkat Keparahan:** 🔴 Tinggi  
**Skor:** Faithfulness=1.00 ✅ | Answer Relevancy=0.96 ✅ | Context Relevance=1.00 ✅

**Pertanyaan:**
> Bagaimana cara meningkatkan kesadaran dan edukasi pengguna agar mampu mendeteksi dan melaporkan serangan phishing serta social engineering?

**Jawaban Sistem (Kandidat):**
Untuk meningkatkan kesadaran dan edukasi pengguna dalam mendeteksi dan melaporkan serangan phishing serta social engineering, penting untuk mengedukasi pengguna mengenai kebijakan dan prosedur penggunaan jaringan, sistem, dan aplikasi yang tepat. Pelajaran yang relevan dari insiden sebelumnya juga harus dibagikan kepada pengguna agar mereka dapat memahami bagaimana tindakan mereka dapat mempengaruhi organisasi. Dengan meningkatkan kesadaran pengguna mengenai insiden, frekuensi insiden dapat dikurangi. Selain itu, staf IT harus dilatih agar dapat memelihara jaringan, sistem, dan aplikasi sesuai dengan standar keamanan organisasi. Edukasi dan kesadaran adalah pengganda sumber daya—semakin banyak pengguna dan staf teknis yang mengetahui tentang cara mendeteksi, melaporkan, dan merespons insiden, semakin sedikit beban yang terjadi pada organisasi.

**Ground Truth:**
Laporkan insiden ini melalui saluran resmi organisasi agar tim menentukan apakah ini merupakan insiden siber. Tingkatkan edukasi dan kesadaran pengguna — semakin banyak yang memahami cara mendeteksi, melaporkan, dan merespons insiden social engineering, semakin rendah dampaknya. Pastikan hanya satu grup resmi dalam organisasi yang mendistribusikan advisori keamanan untuk menghindari informasi yang bertentangan.

---
