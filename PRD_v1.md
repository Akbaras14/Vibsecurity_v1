# PRD VibeSec - Panduan Implementasi Proyek dengan Vibe Coding

| Atribut | Keterangan |
| --- | --- |
| Nama produk | Vibe Security (VibeSec) |
| Bentuk produk | Aplikasi berbasis web |
| Versi dokumen | 1.3 |
| Tanggal | 7 Oktober 2026 |
| Status | Spesifikasi MVP untuk pengembangan aplikasi |
| Bahasa aplikasi | Bahasa Indonesia |
| Frontend | Next.js App Router dan React |
| Backend | Python dengan FastAPI |
| Autentikasi | Tanpa login, registrasi, akun, atau sesi pengguna |
| Operasional | Proses lokal langsung, tanpa Docker/container |

## 1. Tujuan Dokumen dan Konteks Proyek

Dokumen ini adalah spesifikasi untuk membangun aplikasi VibeSec menggunakan bantuan AI coding agent. Gunakan kebutuhan, kontrak data, alur halaman, dan kriteria penerimaan di bawah sebagai acuan implementasi frontend, backend, integrasi scanner, serta pengujian.

Produk yang dibangun adalah **VibeSec**, aplikasi web untuk memeriksa keamanan proyek hasil vibe coding melalui SAST dan SCA. Proyek yang diunggah merupakan objek pemindaian. PRD ini mengatur pembangunan VibeSec; spesifikasi fitur aplikasi yang menjadi objek pemindaian berada pada proyek masing-masing.

Konteks pengembangan adalah skripsi dengan judul berikut:

**ANALISIS RISIKO KEAMANAN PADA PROYEK HASIL VIBE CODING MENGGUNAKAN STATIC APPLICATION SECURITY TESTING (SAST) DAN SOFTWARE COMPOSITION ANALYSIS (SCA) MELALUI APLIKASI VIBE SECURITY (VIBESEC) BERBASIS WEB**

## 2. Ringkasan Produk

VibeSec membantu peneliti dan pengembang menganalisis potensi risiko keamanan pada proyek perangkat lunak hasil vibe coding. Pengguna mengunggah arsip kode sumber, menjalankan SAST dan SCA, kemudian meninjau temuan, menentukan prioritas penanganan, dan mengekspor hasil analisis.

Dalam dokumen ini, vibe coding dioperasionalkan sebagai proses pembuatan atau perubahan kode dengan bantuan AI melalui instruksi bahasa alami. Status tersebut berasal dari dokumentasi proses pengembangan atau pernyataan pembuat proyek, bukan hasil deteksi otomatis terhadap kode.

SAST digunakan untuk mendeteksi pola kerentanan pada kode sumber. SCA digunakan untuk mengidentifikasi kerentanan yang diketahui pada dependensi dengan versi yang dapat diidentifikasi. Hasil keduanya disajikan bersama, tetapi asal dan cakupan setiap temuan tetap dapat ditelusuri.

VibeSec merupakan alat pendukung penelitian. Temuan otomatis merupakan indikasi yang perlu ditinjau; hasil tanpa temuan tidak membuktikan bahwa proyek bebas dari kerentanan.

## 3. Masalah Pengguna

Pengguna membutuhkan satu aplikasi untuk mengunggah proyek, memeriksa kode dan dependensi, lalu membaca serta meninjau hasilnya. Pengguna tidak perlu menjalankan perintah scanner secara manual untuk setiap proyek.

Masalah yang hendak ditangani:

1. Pemeriksaan kode dan dependensi menghasilkan keluaran yang terpisah sehingga sulit dianalisis secara konsisten.
2. Jumlah temuan belum menjelaskan tingkat prioritas penanganan dan konteks dampaknya.
3. Temuan otomatis dapat mengandung false positive dan perlu bukti serta catatan peninjauan.
4. Analisis penelitian membutuhkan data yang dapat ditelusuri ke artefak proyek, konfigurasi alat, dan waktu pemindaian.

## 4. Tujuan dan Ukuran Keberhasilan

| Tujuan | Ukuran keberhasilan MVP |
| --- | --- |
| Mengintegrasikan SAST dan SCA | Satu pemindaian menghasilkan status dan hasil terpisah untuk kedua metode |
| Memudahkan peninjauan | Setiap temuan memiliki lokasi atau identitas dependensi, sumber, severity, dan status peninjauan |
| Mendukung analisis risiko | Temuan yang dinilai memiliki likelihood, impact, skor, kategori, dan alasan penilaian |
| Menjaga keterlacakan | Setiap pemindaian mencatat hash artefak, versi alat, konfigurasi, waktu, dan cakupan |
| Mendukung pelaporan skripsi | CSV, JSON, dan laporan yang dapat dicetak memuat data yang konsisten dengan tampilan aplikasi |
| Menangani kegagalan secara benar | Pemindaian gagal, parsial, dan tidak didukung tidak ditampilkan sebagai hasil bersih |

Target performa pada bagian kebutuhan nonfungsional merupakan target penerimaan yang harus diukur, bukan hasil pengujian yang telah diperoleh.

## 5. Pengguna dan Skenario Penggunaan

| Pengguna | Kebutuhan |
| --- | --- |
| Peneliti/mahasiswa | Mengelola sampel, menjalankan analisis, memvalidasi temuan, dan mengumpulkan data penelitian |
| Pengembang proyek | Memahami temuan dan menentukan urutan perbaikan |
| Dosen/penguji | Membaca laporan, menelusuri bukti, dan mengevaluasi metode analisis |

MVP menggunakan satu workspace bersama pada satu instalasi lokal. Aplikasi langsung membuka dashboard tanpa login. Semua pengguna yang dapat mengakses instalasi tersebut dapat melihat dan mengubah data yang sama; tidak ada kepemilikan data per akun. Administrasi organisasi dan pengaturan peran berada di luar cakupan awal.

User stories utama:

- Sebagai peneliti, saya ingin mencatat asal dan proses pembuatan proyek agar sampel dapat dipertanggungjawabkan.
- Sebagai pengguna, saya ingin mengunggah proyek sekali untuk menjalankan SAST dan SCA.
- Sebagai pengembang, saya ingin melihat lokasi masalah serta saran perbaikan yang terkait dengan temuan.
- Sebagai peneliti, saya ingin membedakan temuan otomatis, hasil validasi, dan penilaian risiko.
- Sebagai peneliti, saya ingin mengekspor hasil dengan identitas pemindaian agar dapat digunakan dalam analisis skripsi.

## 6. Ruang Lingkup

### 6.1 Fitur MVP

1. Dashboard yang dapat dibuka langsung tanpa login.
2. Pengelolaan metadata proyek penelitian.
3. Unggah kode sumber melalui ZIP.
4. Validasi dan ekstraksi arsip secara aman.
5. Pemindaian SAST dan SCA.
6. Ringkasan hasil, filter, dan detail temuan.
7. Peninjauan temuan dan penilaian risiko manual terstruktur.
8. Riwayat pemindaian dan pemindaian ulang.
9. Ekspor CSV, JSON, serta laporan HTML yang dapat dicetak ke PDF melalui browser.
10. Penghapusan data proyek dan artefaknya.

### 6.2 Batas Dukungan Awal

- SAST: JavaScript dan TypeScript, termasuk berkas JSX/TSX yang didukung konfigurasi alat.
- SCA: ekosistem npm dengan `package-lock.json` yang didukung versi alat terpilih.
- `package.json` digunakan sebagai metadata; tanpa lockfile yang dapat diproses, SCA ditandai tidak didukung untuk input tersebut.
- Tidak menjalankan instalasi dependensi, build, skrip proyek, atau aplikasi yang diunggah.
- Dukungan bahasa dan package manager lain ditambahkan setelah ada kebutuhan sampel penelitian dan pengujian kompatibilitas.

### 6.3 Di Luar Cakupan MVP

- Login, logout, registrasi, pengelolaan akun, dan sesi pengguna.
- Docker, Docker Compose, dan runtime container lainnya.
- DAST, pentest aktif, dan pembuktian eksploitasi otomatis.
- Perbaikan kode otomatis atau rekomendasi berbasis layanan AI.
- Integrasi GitHub/GitLab, pemindaian CI/CD, dan monitoring berkelanjutan.
- Deteksi otomatis apakah suatu kode dibuat oleh AI.
- Penilaian lisensi, malware dependensi, dan keamanan infrastruktur/cloud.
- Pemindaian aplikasi yang sedang berjalan, container image, atau target jaringan.
- Klaim sertifikasi keamanan atau kepatuhan.

## 7. Alur Pengguna

1. Operator membuka dashboard secara langsung.
2. Operator membuat proyek dan mencatat nama, deskripsi, teknologi, serta informasi proses vibe coding yang tersedia.
3. Operator mengunggah ZIP dan melihat hasil validasi serta cakupan yang dapat dipindai.
4. Operator memulai pemindaian. Sistem menyimpan artefak sebagai snapshot untuk pemindaian tersebut.
5. Sistem mengekstrak arsip, menjalankan SAST dan SCA, lalu menyimpan hasil dan metadata alat.
6. Operator melihat ringkasan serta status masing-masing metode.
7. Operator membuka temuan, mencatat validasi, dan memberikan penilaian risiko jika bukti memadai.
8. Operator mengekspor laporan atau mengunggah revisi proyek untuk pemindaian berikutnya.

Jika satu metode gagal, hasil metode yang berhasil tetap dapat dibaca dengan penanda hasil parsial. Sistem tidak mengubah kegagalan menjadi nol temuan.

## 8. Kebutuhan Fungsional

| ID | Kebutuhan | Kriteria penerimaan |
| --- | --- | --- |
| FR-01 | Akses langsung | Dashboard, halaman, dan API dapat digunakan tanpa login; tidak ada halaman autentikasi atau pengalihan ke login |
| FR-02 | Pengelolaan proyek | Operator dapat membuat, melihat, mengubah metadata, dan menghapus proyek pada workspace bersama |
| FR-03 | Metadata penelitian | Tersedia kode sampel, sumber proyek, alat/model AI jika diketahui, tanggal pembuatan, dan catatan proses pengembangan; informasi yang tidak diketahui dapat ditandai demikian |
| FR-04 | Unggah ZIP | Sistem menerima ZIP valid sesuai batas, memberi identitas internal, dan menyimpan SHA-256 arsip |
| FR-05 | Validasi arsip | Arsip tidak valid, terenkripsi, mengandung traversal/symlink, atau melampaui batas ditolak dengan alasan yang jelas |
| FR-06 | Deteksi cakupan | Sistem menampilkan bahasa, lockfile yang ditemukan, direktori yang dilewati, dan alasan bagian yang tidak didukung |
| FR-07 | Jalankan SAST | Sistem menggunakan aturan server yang ditetapkan, menyimpan hasil terstruktur dan metadata konfigurasi |
| FR-08 | Jalankan SCA | Sistem memeriksa versi dependensi dari lockfile, menyimpan advisory dan metadata basis data kerentanan |
| FR-09 | Status pemindaian | Pengguna melihat antre, berjalan, selesai, parsial, gagal, atau tidak didukung beserta waktu dan alasan |
| FR-10 | Normalisasi hasil | Temuan memiliki sumber alat, identitas asli, severity asli dan normalisasi; severity tak dikenal tetap ditampilkan sebagai Unknown |
| FR-11 | Daftar dan filter | Temuan dapat difilter menurut metode, severity, kategori risiko, dan status peninjauan; pencarian mendukung path, paket, dan ID temuan |
| FR-12 | Detail SAST | Menampilkan rule ID, deskripsi, path relatif, baris, cuplikan jika tersedia, referensi, serta saran dari aturan jika tersedia |
| FR-13 | Detail SCA | Menampilkan nama dan versi paket, path lockfile, ID advisory/CVE jika tersedia, severity, versi perbaikan jika tersedia, dan referensi |
| FR-14 | Validasi temuan | Operator dapat memilih Belum ditinjau, Terkonfirmasi, False positive, atau Perlu investigasi; perubahan menyimpan alasan dan waktu |
| FR-15 | Penilaian risiko | Likelihood dan impact dipilih secara eksplisit; kategori dihitung dari matriks dan alasan wajib diisi |
| FR-16 | Ringkasan | Jumlah temuan per metode/severity, status peninjauan, cakupan, dan risiko yang telah dinilai sesuai data detail |
| FR-17 | Riwayat | Pemindaian baru tidak menimpa hasil lama; setiap hasil menunjuk snapshot dan konfigurasi yang digunakan |
| FR-18 | Ekspor | CSV/JSON dan laporan cetak menyertakan identitas proyek/pemindaian, cakupan, kegagalan, temuan, peninjauan, dan risiko |
| FR-19 | Hapus data | Setelah konfirmasi, proyek beserta scan, hasil, arsip, dan direktori ekstraksi dihapus; kegagalan pembersihan dilaporkan dan dapat dicoba ulang |

## 9. Mesin Pemindaian

### 9.1 Pilihan Awal

Pilihan implementasi awal adalah **Semgrep Community Edition untuk SAST** dan **Trivy filesystem vulnerability scanning untuk SCA**. Keduanya diinstal langsung pada host scanner dan dipanggil oleh worker Python melalui subprocess tanpa Docker. Versi executable dipatok dan dicatat setelah uji kompatibilitas; PRD ini tidak menetapkan versi yang belum diuji.

Semgrep CE dapat menganalisis kode lokal dan menyediakan keluaran JSON/SARIF. Trivy filesystem dapat mendeteksi kerentanan berdasarkan lockfile. Rujukan kapabilitas: [Semgrep Community Edition](https://semgrep.dev/products/community-edition) dan [Trivy filesystem](https://trivy.dev/docs/latest/target/filesystem/).

Konfigurasi MVP:

- SAST menggunakan ruleset keamanan JavaScript/TypeScript yang dipilih peneliti dan disimpan bersama hash/versinya.
- Konfigurasi dan aturan dari proyek unggahan tidak dipercaya dan tidak digunakan sebagai perintah pemindaian.
- SCA hanya mengaktifkan pemindaian vulnerability untuk menjaga batas metode penelitian.
- Direktori `.git`, `node_modules`, `vendor`, `dist`, `build`, dan `.next` dilewati secara eksplisit dan dicatat dalam laporan.
- Aturan, snapshot basis data, versi alat, serta kebijakan pengecualian dijaga konsisten dalam satu rangkaian eksperimen.
- Pembaruan basis data dilakukan melalui proses terkontrol. Kegagalan pembaruan tidak disembunyikan; snapshot yang digunakan tetap dicatat.
- Temuan dibaca dari keluaran terstruktur. Exit code ditafsirkan sesuai alat karena keberadaan temuan tidak selalu berarti proses gagal.

SCA menunjukkan keterkaitan versi dependensi dengan advisory yang diketahui. MVP tidak membuktikan bahwa fungsi rentan dipanggil atau dapat dieksploitasi pada aplikasi tersebut.

### 9.2 Status Setiap Metode

| Status | Makna |
| --- | --- |
| Queued | Menunggu giliran |
| Running | Proses alat sedang berjalan |
| Completed | Proses selesai dengan keluaran valid, termasuk jika nol temuan |
| Unsupported | Tidak ada input atau cakupan yang didukung untuk metode tersebut |
| Failed | Timeout, kesalahan alat, keluaran rusak, atau kegagalan infrastruktur |

Status keseluruhan diturunkan dari kedua metode: `completed` jika keduanya selesai; `partial` jika satu selesai dan lainnya gagal/tidak didukung; `failed` jika tidak ada yang selesai dan ada kegagalan; `unsupported` jika keduanya tidak didukung. Status aktif tetap `queued` atau `running` hingga metode yang dijadwalkan selesai.

## 10. Severity dan Analisis Risiko

### 10.1 Pemisahan Severity dan Risiko

Severity merupakan tingkat temuan dari alat atau sumber advisory. Risiko merupakan hasil penilaian likelihood dan impact dalam konteks proyek. Keduanya disimpan terpisah; severity tidak otomatis dianggap sebagai probabilitas eksploitasi.

Normalisasi untuk tampilan:

| Sumber | Nilai asli | Nilai tampilan |
| --- | --- | --- |
| Semgrep | ERROR | High |
| Semgrep | WARNING | Medium |
| Semgrep | INFO | Low |
| Trivy | CRITICAL / HIGH / MEDIUM / LOW | Critical / High / Medium / Low |
| Keduanya | Tidak ada atau tidak dikenal | Unknown |

Pemetaan Semgrep merupakan kebijakan tampilan VibeSec, bukan kesetaraan CVSS. Nilai asli tetap tersedia. Skor CVSS dan sumbernya ditampilkan hanya jika tersedia pada hasil SCA.

### 10.2 Matriks Risiko Penelitian

MVP menggunakan matriks ordinal 3 × 3 sebagai metode operasional penelitian. Metode ini perlu disepakati dengan pembimbing sebelum pengumpulan data utama dan tidak diklaim sebagai standar tersertifikasi.

**Skor prioritas risiko = Likelihood × Impact.**

| Nilai | Likelihood | Impact |
| --- | --- | --- |
| 1 | Rendah: prasyarat khusus, akses terbatas, atau jalur pemicu belum jelas | Rendah: dampak terbatas pada fungsi/data nonkritis |
| 2 | Sedang: jalur pemicu masuk akal tetapi memerlukan kondisi atau hak tertentu | Sedang: dapat mengganggu fungsi utama atau memengaruhi data terbatas |
| 3 | Tinggi: jalur pemicu jelas dengan prasyarat rendah berdasarkan bukti peninjauan | Tinggi: dapat memengaruhi data sensitif, hak istimewa, atau layanan secara luas |

| Likelihood \\ Impact | 1 | 2 | 3 |
| --- | --- | --- | --- |
| 1 | 1 — Rendah | 2 — Rendah | 3 — Sedang |
| 2 | 2 — Rendah | 4 — Sedang | 6 — Tinggi |
| 3 | 3 — Sedang | 6 — Tinggi | 9 — Tinggi |

Aturan penilaian:

- Temuan baru berstatus **Belum dinilai**, bukan risiko rendah.
- Alasan likelihood dan impact wajib mengacu pada bukti serta asumsi konteks proyek.
- Jika informasi belum cukup, operator mempertahankan status Belum dinilai atau Perlu investigasi.
- False positive tidak dimasukkan ke ringkasan risiko aktif, tetapi tetap disimpan dan dilaporkan.
- Ringkasan proyek menggunakan kategori tertinggi dari temuan aktif yang telah dinilai, disertai jumlah temuan yang belum dinilai.
- Jika belum ada penilaian, ringkasan menyatakan **Risiko belum dinilai**. Jika sebagian temuan belum dinilai, ringkasan diberi label **Sementara**.
- Skor ordinal tidak dirata-ratakan menjadi persentase keamanan. Jumlah temuan tetap ditampilkan menurut kategori dan metode.

## 11. Struktur Data Minimum

| Entitas | Data utama |
| --- | --- |
| Project | ID, kode sampel, nama, deskripsi, teknologi, sumber, metadata vibe coding, waktu pembuatan |
| Scan | ID, project ID, lokasi artefak privat, SHA-256 ZIP, status, waktu mulai/selesai, profil alat, cakupan, ringkasan kesalahan |
| ScanMethod | Scan ID, metode, alat/versi, hash konfigurasi, identitas/tanggal basis data jika relevan, status, durasi, lokasi keluaran mentah |
| Finding | ID, scan ID, metode, ID sumber, path/baris atau identitas paket, deskripsi, severity asli/normalisasi, referensi, remediasi jika tersedia |
| FindingReview | Finding ID, status validasi, alasan, likelihood, impact, skor/kategori turunan, waktu pembaruan |

Temuan SAST dibedakan berdasarkan rule, path, dan lokasi. Temuan SCA dibedakan berdasarkan advisory, paket, versi, dan path lockfile. Temuan dari metode berbeda tidak digabung otomatis. Peninjauan tidak dipindahkan ke pemindaian baru tanpa verifikasi.

## 12. Halaman Aplikasi

| Halaman | Isi utama |
| --- | --- |
| Dashboard | Proyek, status scan terbaru, dan ringkasan temuan dengan konteks cakupan |
| Daftar proyek | Pencarian, pembuatan proyek, dan akses detail |
| Detail proyek | Metadata penelitian, unggah ZIP, dan riwayat scan |
| Detail pemindaian | Status per metode, konfigurasi, cakupan, ringkasan, filter, dan daftar temuan |
| Detail temuan | Bukti, referensi, remediasi, peninjauan, dan penilaian risiko |
| Laporan | Hasil terstruktur, batas analisis, ekspor data, dan tampilan cetak |

Status harus memiliki label teks, bukan hanya warna. Daftar kosong membedakan belum dipindai, nol temuan, hasil parsial, dan input tidak didukung.

## 13. Kebutuhan Nonfungsional dan Keamanan

| ID | Kebutuhan | Target/kriteria penerimaan |
| --- | --- | --- |
| NFR-01 | Batas unggahan | Maksimum ZIP 100 MB, total ekstraksi 200 MB, 10.000 entri, dan satu berkas ekstraksi 10 MB; batas diperiksa saat streaming/ekstraksi |
| NFR-02 | Keamanan ekstraksi | Tolak path absolut, traversal, symlink/hardlink dan tipe entri khusus; semua target harus berada dalam direktori scan |
| NFR-03 | Pembatasan proses | Worker Python dan scanner berjalan sebagai proses OS terpisah dengan akun OS tanpa hak administrator/root, direktori kerja per scan, timeout, serta batas CPU/memori/proses melalui fasilitas OS yang diuji; tanpa container |
| NFR-04 | Tidak mengeksekusi input | Tidak menjalankan package scripts/build, tidak mengekstrak arsip bersarang otomatis, dan tidak memuat konfigurasi eksekusi dari unggahan |
| NFR-05 | Akses jaringan | Scanner menggunakan ruleset dan DB lokal yang disiapkan sebelum scan; blokir jaringan keluar proses scanner melalui firewall OS yang diuji, bukan melalui Docker |
| NFR-06 | Pemanggilan alat | Argumen proses diberikan sebagai array tanpa shell; nama/path dari pengguna tidak menjadi bagian perintah shell |
| NFR-07 | Penyimpanan nonpublik | Arsip, ekstraksi, dan keluaran mentah berada di luar direktori public; unduhan laporan hanya melalui endpoint backend dengan validasi ID dan path, tanpa pemeriksaan akun |
| NFR-08 | Keamanan web lokal | Frontend dan backend bind ke loopback secara default; backend memvalidasi Host dan Origin terhadap allowlist eksplisit, menolak origin asing untuk mutasi, menggunakan CORS tanpa wildcard, validasi input, dan escaping keluaran; CORS bukan autentikasi |
| NFR-09 | Keamanan ekspor | CSV menetralkan formula spreadsheet; HTML mencetak kode sebagai teks; referensi eksternal hanya memakai skema URL yang diizinkan |
| NFR-10 | Batas proses | Target timeout awal 5 menit per metode; proses anak dibersihkan saat timeout dan status gagal disimpan |
| NFR-11 | Kapasitas MVP | Satu scan aktif per instalasi; permintaan lain disimpan dalam antrean basis data agar dapat dipulihkan |
| NFR-12 | Performa web | Target p95 respons metadata dan halaman tanpa pemindaian di bawah 2 detik pada lingkungan uji yang dicatat |
| NFR-13 | Observabilitas | Log mencatat ID scan, fase, durasi, dan kesalahan; tidak mencatat token, kata sandi, isi proyek, atau cuplikan kode sensitif |
| NFR-14 | Retensi | Ekstraksi sementara dibersihkan setelah scan berakhir; arsip dan hasil disimpan privat sampai proyek dihapus; kegagalan pembersihan dapat dipulihkan |
| NFR-15 | Aksesibilitas | Form berlabel, navigasi keyboard, fokus terlihat, dan status tidak hanya mengandalkan warna |
| NFR-16 | Pemulihan | Scan yang terputus karena worker mati ditandai gagal/interrupted setelah pemeriksaan ulang; pengguna dapat menjalankan scan baru |

Target batas sumber daya scanner awal adalah 2 CPU logis dan 2 GB RAM, diterapkan dengan fasilitas OS pada host yang dipilih dan diuji sebelum dinyatakan terpenuhi. Subprocess atau virtual environment Python tidak dianggap sebagai sandbox keamanan. Target waktu dan batas kapasitas perlu diuji terhadap sampel nyata; perubahan konfigurasi dicatat agar eksperimen tetap dapat dibandingkan.

Tanpa login, batas akses MVP berada pada host lokal. Instalasi tidak dipublikasikan langsung ke internet. Pengguna yang memiliki akses jaringan ke instalasi memiliki akses workspace yang sama. Pembatasan proses OS mengurangi dampak input berbahaya tetapi tidak setara dengan isolasi container/VM.

## 14. Rancangan Teknis Awal

Repositori berfokus pada aplikasi analisis keamanan VibeSec dengan frontend Next.js/React, backend Python/FastAPI, dan penyimpanan MySQL.

Arsitektur minimum yang direncanakan:

1. **Frontend Next.js/React:** halaman, form unggahan, polling status, tabel hasil, dan tampilan laporan cetak. Next.js tidak menjalankan scanner atau mengakses basis data secara langsung.
2. **Backend Python/FastAPI:** REST API, validasi input, unggahan, metadata proyek, hasil scan, peninjauan, perhitungan risiko, dan ekspor CSV/JSON.
3. **MySQL 8.0.16+ melalui PyMySQL:** metadata proyek, scan, antrean, temuan, dan peninjauan. Hanya backend dan worker Python mengakses DB.
4. **Penyimpanan filesystem nonpublik:** ZIP, hasil mentah, dan direktori sementara dengan ID internal.
5. **Worker Python terpisah:** mengambil scan dari antrean DB, memanggil executable Semgrep/Trivy menggunakan `subprocess` dengan `shell=False`, dan menyimpan hasil.

Frontend berjalan pada `127.0.0.1:3000` dan backend pada `127.0.0.1:8000` secara default. Frontend menggunakan URL API yang dikonfigurasi; backend mengizinkan origin frontend secara eksplisit. API dan worker memakai database MySQL yang sama dan berbagi lokasi penyimpanan artefak. MySQL dijalankan sebagai layanan native tanpa Docker. Antrean menggunakan tabel scan; Redis/Celery belum diperlukan untuk satu scan aktif. Pemindaian tidak bergantung pada masa hidup request HTTP atau proses frontend.

Struktur awal yang dituju: `app/` untuk frontend yang sudah ada, `backend/` untuk API, worker, aturan, dan pengujian Python, serta `storage/` untuk artefak runtime yang diabaikan Git. Data aplikasi disimpan pada server MySQL; storage bukan lokasi database. Pisahkan dependensi Python melalui virtual environment; jangan menyimpan virtual environment di Git.

Target host scanner awal adalah Linux atau WSL yang telah diuji, dengan Python, Semgrep, dan Trivy diinstal langsung. Pada pengembangan Windows, Next.js dapat berjalan di Windows sementara backend dan worker berjalan di WSL; uji koneksi loopback frontend/API pada setup tersebut. Jangan mengasumsikan semua scanner mendukung Windows native. Tidak ada Dockerfile, Compose, atau kewajiban memasang Docker. Backend membutuhkan proses berumur panjang dan filesystem persisten.

### 14.1 Konfigurasi dan Migrasi MySQL

- Gunakan InnoDB, charset utf8mb4, foreign key cascade, dan query berparameter PyMySQL (`%s`).
- Konfigurasi `VIBESEC_MYSQL_HOST`, `VIBESEC_MYSQL_PORT`, `VIBESEC_MYSQL_DATABASE`, `VIBESEC_MYSQL_USER`, dan `VIBESEC_MYSQL_PASSWORD` disimpan di environment atau `.env.local` sisi server.
- Database dan akun MySQL disiapkan terlebih dahulu. `python -m backend.migrate` menerapkan skema; `--status` membaca riwayat.
- Migrasi SQL berversi berada di `backend/migrations/`; tabel `schema_migrations` menyimpan versi, nama, checksum, dan penanda kegagalan.
- Migrasi memakai named lock MySQL untuk mencegah proses bersamaan. DDL MySQL dapat melakukan implicit commit; jangan menjanjikan rollback seluruh perubahan skema ketika migrasi gagal.
- Migrasi yang gagal ditandai dirty dan menghalangi kelanjutan sampai skema dipulihkan. Migrasi yang telah diterapkan tidak boleh diedit.
- Worker memakai named lock per database, sedangkan unggah/penghapusan memakai row lock pada proyek untuk menjaga konsistensi.
- API dan worker menggunakan database serta direktori artefak yang sama. Perpindahan dari penyimpanan lama tidak menghapus atau mengimpor data secara otomatis.

## 15. Spesifikasi Implementasi Halaman dan API

### 15.1 Rute Halaman

| Rute | Perilaku dan aksi utama |
| --- | --- |
| `/` | Alihkan langsung ke `/dashboard` tanpa login |
| `/dashboard` | Jumlah proyek, status scan terbaru, distribusi severity scan terbaru per proyek; tombol Tambah Proyek |
| `/projects` | Daftar proyek dengan pencarian nama dan tombol Tambah Proyek |
| `/projects/new` | Form nama wajib, deskripsi, teknologi, sumber, dan metadata vibe coding opsional |
| `/projects/[id]` | Metadata yang dapat diubah, form unggah ZIP, tombol Mulai Pemindaian, riwayat, dan Hapus Proyek |
| `/scans/[id]` | Status per metode, waktu, cakupan, ringkasan severity/risiko, tabel temuan, pencarian/filter, dan ekspor |
| `/scans/[id]/findings/[findingId]` | Bukti SAST/SCA, referensi, remediasi jika tersedia, form validasi dan penilaian risiko |
| `/scans/[id]/report` | Laporan cetak dengan metadata, ringkasan, temuan, penilaian, dan batas analisis |

Gunakan label Indonesia di antarmuka. Severity dan ID alat boleh mempertahankan istilah aslinya. Desktop menggunakan navigasi samping; layar kecil menyediakan navigasi yang dapat dibuka melalui tombol berlabel. Tabel lebar dapat digulir horizontal tanpa membuat seluruh halaman melebar.

Setiap halaman data memiliki keadaan loading, kosong, berhasil, dan gagal dengan aksi Coba Lagi jika relevan. Tombol submit dinonaktifkan selama permintaan berlangsung. Jangan membuat tombol yang hanya menampilkan notifikasi tanpa menjalankan aksi sebenarnya.

### 15.2 Kontrak Endpoint Minimum

Semua endpoint diimplementasikan pada backend Python/FastAPI dengan prefix `/api`. Endpoint tidak memerlukan login, cookie sesi, bearer token, atau ID pemilik. Endpoint detail tetap memvalidasi keberadaan data dan hubungan proyek, scan, dan finding sebelum mengembalikan hasil. Pembatasan Host/Origin dan loopback mengikuti NFR-08.

| Metode | Endpoint | Input/hasil |
| --- | --- | --- |
| GET | `/api/projects` | Daftar proyek; parameter `q`, `page`, `pageSize` |
| POST | `/api/projects` | Metadata proyek; mengembalikan proyek baru |
| GET | `/api/projects/[id]` | Metadata dan ringkasan riwayat scan |
| PATCH | `/api/projects/[id]` | Pembaruan field metadata yang diizinkan |
| DELETE | `/api/projects/[id]` | Penghapusan metadata serta artefak; ditolak dengan 409 jika scan masih antre/berjalan |
| POST | `/api/projects/[id]/scans` | Multipart berisi ZIP; validasi, simpan snapshot, buat scan antre; kembalikan 202 dan scan ID |
| GET | `/api/scans/[id]` | Status, cakupan, metadata alat, dan ringkasan |
| GET | `/api/scans/[id]/findings` | Filter metode, severity, risiko, review, `q`, `page`, dan `pageSize` |
| GET | `/api/scans/[id]/findings/[findingId]` | Detail temuan dan peninjauan |
| PATCH | `/api/scans/[id]/findings/[findingId]/review` | Status, alasan validasi, likelihood/impact opsional, serta alasan risiko |
| GET | `/api/scans/[id]/export?format=csv\|json` | Unduhan privat untuk seluruh hasil scan, terlepas dari filter halaman |

Respons JSON berhasil menggunakan `{ data, meta? }`; kesalahan menggunakan `{ error: { code, message, fields? } }`. Gunakan 400 untuk input salah, 403 untuk Host/Origin yang ditolak, 404 untuk sumber yang tidak ditemukan atau hubungan ID yang tidak sesuai, 409 untuk konflik status, 413 untuk ukuran berlebih, dan 500 untuk kesalahan internal tanpa stack trace ke pengguna. Seragamkan kesalahan validasi FastAPI ke kontrak ini. Daftar memiliki default 25 item per halaman dan maksimum 100; parameter divalidasi backend Python.

### 15.3 Alur Upload dan Worker

1. Pengguna memilih ZIP secara lokal. Tampilkan nama, ukuran, batas input, dan tombol Mulai Pemindaian; satu klik mengunggah sekaligus membuat scan.
2. Backend Python memvalidasi Host/Origin dan metadata, membatasi aliran unggahan, serta menyimpan ZIP dengan ID acak di luar direktori publik.
3. Validasi arsip dilakukan dengan batas ekstraksi. Arsip tidak valid dihapus dan tidak dimasukkan ke antrean.
4. Server menghitung SHA-256 dan menyimpan scan dengan status `queued`. Halaman beralih ke detail scan setelah menerima 202.
5. Worker mengklaim satu scan secara atomik, menandai `running`, lalu mengekstrak ulang secara terbatas ke direktori sementara.
6. Worker menentukan cakupan dan menjalankan alat secara berurutan dengan konfigurasi server. Setiap metode menyimpan statusnya sendiri.
7. Worker memvalidasi dan menormalisasi keluaran, menyimpan temuan secara transaksional per metode, kemudian menghitung status akhir.
8. Direktori sementara dibersihkan dalam blok cleanup, termasuk pada kegagalan. ZIP dan hasil tetap privat hingga proyek dihapus.
9. Halaman memeriksa status setiap 3 detik saat scan aktif; polling berhenti pada status akhir atau saat halaman ditutup. Jangan menampilkan persentase progres yang tidak tersedia dari worker.

Unggahan ulang membuat scan baru. Jangan memulai scan dengan request GET. Peninjauan tidak boleh mengubah keluaran mentah alat. Gunakan status penghapusan yang dapat dipulihkan agar kegagalan filesystem tidak meninggalkan data yang dianggap telah terhapus.

### 15.4 Validasi Form dan Konsistensi Data

- Nama proyek wajib, 1-100 karakter setelah trim; deskripsi maksimal 2.000 karakter.
- Metadata opsional boleh kosong dan tidak diganti dengan informasi AI yang ditebak.
- Status peninjauan hanya menerima enum yang ditentukan pada FR-14.
- Likelihood dan impact harus keduanya kosong atau keduanya bilangan bulat 1-3; alasan penilaian wajib saat keduanya diisi.
- Skor dan kategori risiko dihitung server, tidak dipercaya dari request browser.
- Perubahan status validasi memerlukan alasan. False positive tetap tersimpan, tetapi dikeluarkan dari ringkasan risiko aktif.
- Nilai yang tidak tersedia ditampilkan sebagai Tidak tersedia, bukan angka nol atau versi perbaikan rekaan.
- Dashboard menggunakan scan terbaru per proyek agar pemindaian ulang tidak menggandakan jumlah temuan; detail scan selalu hanya memuat data scan tersebut.

### 15.5 Isi Laporan

Laporan memuat nama/kode proyek, metadata vibe coding yang tersedia, ID scan, SHA-256, waktu, versi alat, hash aturan/DB, cakupan, pengecualian, status per metode, jumlah temuan, bukti, review, risiko, dan referensi. Sembunyikan navigasi serta tombol saat dicetak. Sertakan jumlah temuan belum dinilai dan batas bahwa nol temuan tidak menjamin keamanan.

## 16. Rencana Pengujian dan Penerimaan

| Skenario | Hasil yang diharapkan |
| --- | --- |
| ZIP JavaScript/TypeScript dengan kasus SAST terkontrol | Aturan yang ditargetkan menghasilkan temuan dengan lokasi yang benar |
| Lockfile dengan paket rentan yang tercakup dalam snapshot DB uji | SCA menampilkan paket, versi, dan advisory yang sesuai |
| Sampel tanpa temuan pada konfigurasi uji | Status selesai dan nol temuan, disertai batas cakupan |
| ZIP tanpa kode atau lockfile yang didukung | Metode terkait berstatus tidak didukung dengan alasan |
| Satu alat gagal/timeout | Hasil keseluruhan parsial jika metode lain berhasil; hasil yang ada tetap dapat dibaca |
| Kedua alat gagal atau keluaran tidak valid | Status gagal; dashboard tidak menyatakan proyek aman |
| Arsip traversal, symlink, atau ZIP bomb | Ditolak tanpa penulisan di luar direktori scan dan tanpa melampaui batas ekstraksi |
| Nama file atau konten berupa payload shell/HTML/CSV | Tidak mengeksekusi perintah, skrip browser, atau formula spreadsheet |
| Dashboard/API diakses langsung dari lingkungan lokal yang diizinkan | Dapat digunakan tanpa login, akun, token, atau sesi |
| Mutasi dikirim dari origin asing atau Host tidak diizinkan | Ditolak sesuai kebijakan Host/Origin |
| Host tidak memiliki Docker | Web, API, worker, dan scanner tetap dapat berjalan melalui instalasi langsung yang didokumentasikan |
| Peninjauan dan matriks risiko | Seluruh sembilan kombinasi menghasilkan kategori yang benar; False positive dikecualikan dari risiko aktif |
| Pemindaian ulang | Scan lama tetap utuh dan scan baru memiliki metadata snapshot sendiri |
| Restart worker di tengah scan | Scan tidak tertinggal selamanya dalam status berjalan dan dapat dipindai ulang |
| Ekspor laporan | Hitungan, identitas, status, bukti, dan penilaian sesuai data yang tersimpan |
| Penghapusan proyek | Metadata serta artefak privat terhapus; kegagalan penghapusan tidak dilaporkan sebagai berhasil |

Data uji kerentanan menggunakan fixture lokal yang tidak dijalankan sebagai aplikasi. Versi alat, ruleset, DB uji, dan spesifikasi host dicatat agar pemeriksaan dapat diulang. Untuk pengukuran performa, gunakan sampel representatif serta catat jumlah dan distribusi percobaan.

## 17. Tahapan Implementasi

| Tahap | Hasil yang harus tersedia |
| --- | --- |
| 1. Fondasi dan input | Frontend Next.js, backend Python/FastAPI, MySQL, dashboard tanpa login, metadata proyek, unggah dan ekstraksi aman |
| 2. Pemindaian | Worker Python, scanner CLI tanpa Docker, pembatasan proses OS, pencatatan konfigurasi, status parsial/gagal, dan pemulihan |
| 3. Analisis | Daftar/detail temuan, normalisasi, peninjauan, matriks risiko, dan riwayat |
| 4. Pelaporan | Ekspor data dan laporan cetak dengan keterlacakan serta batas cakupan |
| 5. Validasi penelitian | Uji fungsional/keamanan, pengukuran performa, uji sampel, dan pembekuan konfigurasi eksperimen |

Estimasi jadwal disusun setelah jumlah sampel, ketersediaan lingkungan scanner, dan tenggat skripsi diketahui.

## 18. Risiko Produk dan Mitigasi

| Risiko | Mitigasi |
| --- | --- |
| False positive/false negative | Sediakan bukti, peninjauan manual, cakupan eksplisit, dan batas interpretasi |
| Versi dependensi tidak dapat diidentifikasi | Wajibkan lockfile yang didukung; laporkan tidak didukung jika tidak tersedia |
| Hasil berubah karena ruleset/DB berubah | Catat versi/hash dan gunakan snapshot konsisten dalam eksperimen |
| Input berbahaya atau konsumsi sumber daya berlebih | Validasi arsip, akun OS terbatas, batas sumber daya OS, direktori scan terpisah, dan timeout |
| Kebocoran kode atau data sensitif | Bind lokal, penyimpanan nonpublik, allowlist Host/Origin, jaringan scanner dibatasi, dan penghapusan yang teruji |
| Akses tanpa pembatasan akun | Gunakan sebagai workspace lokal bersama; jangan mengandalkan ID acak atau CORS sebagai autentikasi |
| Penilaian risiko subjektif | Gunakan rubrik tertulis, alasan wajib, dan tinjauan pembimbing/penilai tambahan bila tersedia |
| Salah mengatribusikan kerentanan pada vibe coding | Dokumentasikan asal sampel dan batasi kesimpulan sesuai desain penelitian |

## 19. Instruksi untuk AI Coding Agent

1. Baca PRD dan kode yang ada sebelum mengubah implementasi. Gunakan Next.js App Router/React untuk frontend dan Python/FastAPI untuk seluruh logika backend serta API, dengan database MySQL.
2. Bangun per tahap pada bagian 17. Selesaikan satu alur dari halaman sampai penyimpanan dan uji sebelum melanjutkan.
3. Batasi repositori pada aplikasi VibeSec. Input pemindaian berasal dari unggahan ZIP melalui antarmuka web dan API yang ditentukan.
4. Gunakan komponen dan fungsi yang sudah ada. Utamakan modul standar Python seperti `zipfile`, `hashlib`, dan `subprocess`; validasi arsip dan batas ekstraksi tetap wajib. Tambahkan dependensi hanya jika diperlukan, termasuk FastAPI dan server ASGI.
5. Jangan membuat halaman login, registrasi, logout, tabel pengguna, sesi, JWT, atau middleware autentikasi. Semua data merupakan workspace bersama pada instalasi lokal.
6. Simpan secret dalam environment server, sediakan `.env.example` tanpa nilai rahasia, dan abaikan storage privat serta DB dari Git.
7. Gunakan hasil scanner nyata untuk fitur produksi. Data contoh hanya boleh berada pada fixture pengujian atau mode demo yang diberi label eksplisit.
8. Jangan menggunakan Docker atau container untuk web, API, DB, maupun scanner. Bila executable scanner, ruleset, atau DB belum tersedia, tampilkan kesalahan konfigurasi yang jelas; jangan mengembalikan hasil simulasi sebagai scan berhasil.
9. Patok versi dependensi, scanner, dan konfigurasi yang telah diuji. Dokumentasikan instalasi langsung, environment Python, pembatasan OS, serta penyiapan DB sebelum scanner offline dijalankan.
10. Tinggalkan pemeriksaan runnable untuk logika status scan, parsing hasil, matriks risiko, keamanan arsip, dan akses endpoint. Gunakan alat uji yang tersedia sebelum menambah framework baru.
11. Perbarui README dengan instalasi frontend/backend, inisialisasi/migrasi MySQL, worker Python, instalasi dan pembaruan scanner/DB, menjalankan ketiga proses tanpa Docker, pengujian, dan pemulihan.
12. Laporkan fitur yang selesai, hasil pemeriksaan, dan hambatan nyata. Jangan menyatakan aplikasi selesai jika hanya antarmuka atau data demo yang berjalan.

Keputusan Next.js untuk frontend, Python/FastAPI untuk backend, MySQL, workspace lokal tanpa login, satu worker Python, dan instalasi langsung tanpa Docker berlaku untuk MVP. Cakupan awal objek scan tetap JavaScript/TypeScript dengan lockfile npm; bahasa implementasi backend VibeSec tidak otomatis menambah cakupan pemindaian Python. Rubrik risiko dapat dikonfirmasi bersama pembimbing sebelum pengambilan data skripsi utama.

## 20. Definition of Done MVP

MVP dinyatakan selesai apabila:

- Seluruh FR-01 sampai FR-19 terpenuhi pada cakupan bahasa dan lockfile yang ditetapkan.
- Frontend Next.js dan backend Python terhubung; alur utama berjalan tanpa login dan tanpa Docker.
- Pengujian keamanan input, pembatasan akses lokal/Origin, batas proses OS, timeout, dan ekspor lulus.
- Hasil SAST/SCA dapat ditelusuri ke snapshot, alat, konfigurasi, dan basis data yang digunakan.
- Peninjauan serta penilaian risiko konsisten antara detail, ringkasan, dan laporan.
- Kegagalan, hasil parsial, dan input tidak didukung ditampilkan secara eksplisit.
- Prosedur instalasi, pemindaian, pembaruan DB, dan pemulihan terdokumentasi.
- Tidak ada hasil penelitian, skor akurasi, atau klaim keamanan yang direkayasa.
