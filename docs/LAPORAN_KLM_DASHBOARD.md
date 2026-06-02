# Laporan Akademik KLM (Keystroke Level Model) pada Dashboard User dan Admin

## 1. Judul

Analisis Keystroke Level Model (KLM) dan Evaluasi Heuristik Nielsen pada Dashboard User dan Admin Sistem Helpdesk Keamanan Siber Pusdatin.

## 2. Latar Belakang

Sistem helpdesk pada proyek ini menyediakan dua antarmuka utama:

1. Dashboard User/Pelapor untuk mengisi identitas, mengirim laporan insiden, mengunggah bukti, dan memeriksa status tiket.
2. Dashboard Admin untuk memantau inbox tiket, membuka detail tiket, memperbarui status, melakukan assignment, eskalasi, serta mengirim notifikasi ke pelapor.

Dalam mata kuliah Interaksi Manusia dan Komputer, analisis KLM berguna untuk memperkirakan waktu penyelesaian tugas berbasis aksi kognitif dan motorik, sedangkan heuristik Nielsen dipakai untuk menilai kualitas usability antarmuka.

## 3. Ruang Lingkup Analisis

Analisis ini disusun berdasarkan observasi antarmuka web berikut:

- Dashboard pelapor: formulir identitas dan halaman chat laporan.
- Dashboard admin: inbox tiket, detail tiket, dan form laporan.

Referensi implementasi yang digunakan sebagai dasar analisis:

- [app/web/templates/pelapor/identitas.html](../app/web/templates/pelapor/identitas.html)
- [app/web/templates/pelapor/chat.html](../app/web/templates/pelapor/chat.html)
- [app/web/templates/admin/inbox.html](../app/web/templates/admin/inbox.html)
- [app/web/templates/admin/tiket_detail.html](../app/web/templates/admin/tiket_detail.html)
- [app/web/templates/admin/report.html](../app/web/templates/admin/report.html)
- [app/web/routes/pelapor.py](../app/web/routes/pelapor.py)
- [app/web/routes/admin_actions.py](../app/web/routes/admin_actions.py)
- [app/web/routes/admin_inbox.py](../app/web/routes/admin_inbox.py)

## 4. Metode KLM

KLM menghitung waktu tugas dari urutan operator dasar berikut:

| Operator | Arti | Waktu standar |
| --- | --- | ---: |
| K | Keystroke atau klik tombol | 0.20 s |
| P | Pointing/mengarahkan kursor | 1.10 s |
| H | Homing/memindahkan tangan | 0.40 s |
| M | Mental preparation | 1.35 s |
| R | System response | bergantung sistem |

R tidak dijumlahkan ke waktu manual karena sangat bergantung pada server, jaringan, dan model AI. Karena itu, hasil KLM di bawah ini adalah estimasi waktu interaksi pengguna sebelum sistem merespons.

## 5. Skenario KLM Dashboard User

### 5.1 Skenario utama

Tugas yang dianalisis pada dashboard user adalah:

1. Mengisi identitas pelapor.
2. Masuk ke halaman chat.
3. Menulis laporan insiden pertama.
4. Mengirim laporan.

### 5.2 Asumsi perhitungan

Karena KLM sangat dipengaruhi panjang input, analisis ini memakai asumsi representatif untuk teks berikut:

- Nama pelapor: 12 karakter.
- Kontak: 12 karakter.
- Unit: 15 karakter.
- Deskripsi insiden awal: 140 karakter.

### 5.3 Rincian operator

| Langkah | Operator | Estimasi waktu |
| --- | --- | ---: |
| Memahami halaman identitas | M | 1.35 |
| Klik field nama | P | 1.10 |
| Mengetik nama (12) | K | 2.40 |
| Klik field kontak | P | 1.10 |
| Mengetik kontak (12) | K | 2.40 |
| Klik field unit | P | 1.10 |
| Mengetik unit (15) | K | 3.00 |
| Klik tombol lanjut/submit | P + K | 1.30 |
| Memahami halaman chat | M | 1.35 |
| Klik area input chat | P | 1.10 |
| Mengetik deskripsi insiden (140) | K | 28.00 |
| Klik tombol kirim | P + K | 1.30 |

### 5.4 Estimasi total

Total waktu manual dashboard user:

1.35 + 1.10 + 2.40 + 1.10 + 2.40 + 1.10 + 3.00 + 1.30 + 1.35 + 1.10 + 28.00 + 1.30 = 44.50 detik

Jika beberapa input dilakukan dengan keyboard shortcut yang lebih efisien, waktu dapat lebih kecil. Namun sebagai estimasi akademik, angka 44.5 detik sudah mencerminkan beban interaksi awal pengguna.

### 5.5 Interpretasi

Dashboard user cukup efisien untuk pelaporan karena:

- Form identitas sederhana dan langsung mengarahkan ke chat.
- Placeholder dan panduan membantu pengguna memahami apa yang harus diketik.
- Tombol reset sesi memberi kontrol bila pengguna ingin mengulang.

Faktor yang masih menambah waktu adalah kebutuhan mengetik deskripsi insiden yang cukup panjang. Ini wajar untuk sistem pelaporan yang menuntut informasi detail.

## 6. Skenario KLM Dashboard Admin

### 6.1 Skenario utama

Tugas yang dianalisis pada dashboard admin adalah:

1. Login ke sistem.
2. Membuka inbox tiket.
3. Memfilter tiket dan membuka detail tiket.
4. Mengubah status tiket.
5. Assign tiket ke admin tertentu.
6. Menentukan escalation level.
7. Mengirim notifikasi ke pelapor.

### 6.2 Asumsi perhitungan

Untuk skenario ini diasumsikan admin sudah berhasil login dan berada di inbox. Analisis fokus pada proses operasional sehari-hari setelah dashboard terbuka.

### 6.3 Rincian operator

| Langkah | Operator | Estimasi waktu |
| --- | --- | ---: |
| Memahami inbox tiket | M | 1.35 |
| Pilih filter status | P | 1.10 |
| Pilih nilai filter | K | 0.20 |
| Pindah ke kotak pencarian | P | 1.10 |
| Mengetik kata kunci pencarian (8) | K | 1.60 |
| Klik baris tiket | P + K | 1.30 |
| Memahami detail tiket | M | 1.35 |
| Pilih status baru | P + K | 1.30 |
| Isi assignee (8 karakter) | P + K | 2.70 |
| Pilih escalation level | P + K | 1.30 |
| Klik tombol notifikasi | P + K | 1.30 |

### 6.4 Estimasi total

Total waktu manual dashboard admin:

1.35 + 1.10 + 0.20 + 1.10 + 1.60 + 1.30 + 1.35 + 1.30 + 2.70 + 1.30 + 1.30 = 14.60 detik

Catatan: jika proses login dimasukkan ke dalam analisis, waktu total akan bertambah signifikan karena ada input username dan password. Namun untuk evaluasi operasional panel kerja, skenario di atas lebih representatif.

### 6.5 Interpretasi

Dashboard admin relatif cepat dipakai untuk tugas rutin karena:

- Informasi tiket tersusun dalam tabel yang mudah dipindai.
- Filter status, severity, dan search mempercepat pencarian tiket.
- Aksi operasional utama tersedia langsung di halaman detail tiket.

Namun, beban tugas admin bertambah ketika harus melakukan beberapa tindakan berurutan di detail tiket. Ini menunjukkan perlunya optimasi alur kerja, misalnya pengelompokan aksi yang sering dilakukan.

## 7. Perbandingan Singkat User vs Admin

| Aspek | Dashboard User | Dashboard Admin |
| --- | --- | --- |
| Fokus tugas | Mengirim laporan insiden | Menangani tiket dan tindak lanjut |
| Beban input teks | Tinggi | Rendah-sedang |
| Banyak klik/fokus | Sedang | Sedang-tinggi |
| Risiko kesalahan | Salah isi identitas atau deskripsi | Salah update status atau assignment |
| Kelebihan utama | Chat guided dan reset sesi | Tabel tiket dan kontrol operasional |

## 8. Ringkasan Heuristik Nielsen

Status digunakan dalam bentuk: **Baik**, **Cukup**, dan **Perlu Perbaikan**.

| Heuristik | Status | Catatan / Masalah |
| --- | --- | --- |
| 1. Visibility of system status | Baik | Ada indikator online, typing indicator, badge status tiket, dan notifikasi hasil aksi admin. Informasi sistem cukup terlihat. |
| 2. Match between system and real world | Baik | Istilah seperti tiket, pelapor, severity, assign, dan eskalasi mudah dipahami dalam konteks helpdesk. Campuran istilah Inggris masih ada, tetapi tidak mengganggu utama. |
| 3. User control and freedom | Cukup | Pelapor bisa reset sesi, namun kontrol batal/undo pada beberapa aksi admin belum menonjol. Aksi penting masih cenderung langsung eksekusi. |
| 4. Consistency and standards | Baik | Pola kartu, tombol, badge, dan navigasi relatif konsisten. Namun campuran istilah Indonesia-Inggris perlu dijaga agar tetap seragam. |
| 5. Error prevention | Baik | Ada validasi form, CSRF, pembatasan jenis file, dan pembatasan ukuran/jenis input. Ini membantu mencegah kesalahan sejak awal. |
| 6. Recognition rather than recall | Baik | Label, placeholder, badge status, filter, dan panduan di sisi layar membantu pengguna mengenali fungsi tanpa harus mengingat banyak langkah. |
| 7. Flexibility and efficiency of use | Baik | Penggunaan HTMX, Enter untuk kirim chat, filter inbox, dan tab detail tiket mendukung penggunaan cepat bagi pengguna berpengalaman. |
| 8. Aesthetic and minimalist design | Cukup | Tampilan sudah bersih dan fokus, tetapi ada area yang cukup padat informasi. Perlu dijaga agar tidak terlalu banyak elemen dalam satu layar. |
| 9. Help users recognize, diagnose, and recover from errors | Cukup | Pesan error sudah muncul, tetapi belum semuanya memberi saran pemulihan yang sangat spesifik. Contoh: login gagal dan upload error sudah informatif, namun masih bisa diperjelas. |
| 10. Help and documentation | Cukup | Ada panduan singkat di halaman pelapor dan deskripsi fungsi di halaman laporan, tetapi belum ada pusat bantuan yang komprehensif untuk semua alur. |

## 9. Kesimpulan

Secara keseluruhan, dashboard user dan admin pada proyek ini sudah cukup baik untuk digunakan sebagai studi kasus IMK. Dari hasil KLM, dashboard user memiliki beban interaksi lebih besar karena banyak teks yang harus diketik saat pelaporan, sedangkan dashboard admin lebih efisien untuk pekerjaan operasional yang berulang. Dari sisi heuristik Nielsen, sistem menunjukkan kekuatan pada visibilitas status, konsistensi antarmuka, pencegahan error, dan fleksibilitas. Area yang masih bisa ditingkatkan adalah dukungan help/documentation, pemulihan error yang lebih presisi, serta penyederhanaan beberapa alur aksi admin.

## 10. Saran Pengembangan

1. Tambahkan ringkasan progres saat pelapor sedang mengisi form agar beban mental lebih ringan.
2. Sediakan konfirmasi sebelum aksi admin yang bersifat kritis, seperti status final atau eskalasi tinggi.
3. Buat bantuan kontekstual singkat di tiap halaman utama.
4. Pertahankan konsistensi istilah Indonesia agar terminologi lebih seragam untuk pengguna non-teknis.
