# Panduan menjelaskan VibeSec kepada penguji

## Pokok penjelasan

VibeSec adalah aplikasi web untuk membantu analisis risiko keamanan pada proyek hasil vibe coding. Kode diperiksa dengan SAST, dependensi diperiksa dengan SCA, kemudian hasilnya diolah menjadi temuan yang dapat ditelusuri beserta estimasi risiko bersyarat dan rekomendasi. Aplikasi membantu analisis; hasil statis tidak membuktikan serangan berhasil.

Judul skripsi tetap menggunakan judul yang sudah disetujui. Fokus penjelasan adalah hubungan antara **proyek → bukti kerentanan → skenario → kemungkinan dan dampak → risiko → rekomendasi**.

## Urutan demonstrasi sekitar lima menit

| Langkah | Yang ditunjukkan | Pokok penjelasan |
| --- | --- | --- |
| 1. Proyek | Identitas, sumber pembuatan dan versi | Objeknya adalah proyek hasil vibe coding. Riwayat prompt dan asal proyek harus didokumentasikan, bukan disimpulkan dari kode. |
| 2. Pemindaian | Unggahan ZIP, status SAST dan SCA | Semgrep memeriksa kode, OSV-Scanner memeriksa versi paket. Worker memproses antrean di lingkungan WSL. |
| 3. Bukti | Satu temuan beserta lokasi atau paket/versi | Tunjukkan apa yang benar-benar ditemukan. Uraian Indonesia membantu membaca; teks asli tetap tersedia. |
| 4. Risiko | Buka satu skenario yang memiliki skor | Jelaskan aset yang dimodelkan, bukti scope dependensi, kemungkinan, dampak, skor, dan asumsi yang belum dibuktikan. |
| 5. Laporan | Ringkasan, kategori, tanpa skor dan ekspor | Hasil dapat ditelusuri. Risiko tertinggi bukan risiko total proyek. Temuan tanpa skor tetap dilaporkan. |

Siapkan satu hasil pemeriksaan lengkap sebelum presentasi. Saat menjelaskan, gunakan hasil tersimpan agar tidak bergantung pada lama antrean. Pemindaian baru dapat didemonstrasikan terpisah; jangan menyebut hasil parsial sebagai pemeriksaan lengkap. Pastikan kedua alat berstatus selesai dan worker aktif sebelum demonstrasi langsung.

## Tiga hasil yang harus dibedakan

| Hasil | Pertanyaan yang dijawab | Batas makna |
| --- | --- | --- |
| Keparahan atau severity | Seberapa parah kelemahan menurut alat/advisory? | Belum mencakup penggunaan proyek. |
| Status temuan | Bukti apa yang sudah dapat dipastikan? | SCA terkonfirmasi pada kecocokan paket dan versi; belum membuktikan fungsi rentan dipanggil. SAST saat ini masih dapat berstatus belum dapat dipastikan. |
| Estimasi risiko proyek | Apa kemungkinan dan dampaknya dalam skenario yang dinyatakan? | Bersyarat pada asumsi yang ditampilkan; bukan risiko residual atau probabilitas serangan. |

Prioritas teknis A1 merupakan informasi tambahan dari indikator CVSS. Penilaian risiko bersyarat RA1 adalah bagian analisis skenario proyek. R1 adalah riwayat metode penilaian sebelumnya. Sebut kode-kode itu sebagai **versi aturan**, bukan metode standar internasional.

## Cara menjelaskan skor

1. Sistem memerlukan kecocokan SCA, scope dependensi dari package-lock.json v2/v3, dan vektor CVSS v3 lengkap.
2. Scope membantu membedakan skenario runtime aplikasi dengan pengembangan/build. Paket pengembangan tetap dapat memiliki risiko.
3. Kemungkinan memakai indikator akses advisory: akses lokal/fisik atau hak tinggi bernilai 1; jaringan dengan kompleksitas rendah, tanpa hak dan interaksi pengguna bernilai 3; kombinasi lainnya bernilai 2. Skenario development membatasi maksimum 2 **dengan asumsi paparannya terbatas dan tidak menyediakan layanan produksi publik**.
4. Dampak memakai CIA advisory: tidak ada dampak = 0, rendah = 2, tinggi = 3. Dampak skenario adalah nilai tertinggi dari ketiga aspek tersebut.
5. Skor = kemungkinan × dampak. Kategori: rendah 1–2, sedang 3–4, tinggi 6–9. Nilai tersebut merupakan aturan operasional, bukan probabilitas atau rumus resmi NIST/CVSS.
6. Bila ada beberapa skenario, dipilih skor tertinggi dari satu skenario utuh; jika sama, dipilih dampak tertinggi. Asumsi pada skenario tetap berlaku.

Contoh ilustratif, bukan hasil penelitian: kemungkinan 2 dan dampak 3 menghasilkan skor 6, kategori tinggi. Penjelasannya harus menyebut dasar kedua nilai serta asumsi skenario; jangan hanya menunjukkan angka.

Model ini mengasumsikan fungsi rentan dipanggil, prasyarat advisory terpenuhi, dan masukan penyerang mencapai fungsi tersebut. Hal-hal itu belum dibuktikan oleh kecocokan lockfile. Karena itu hasil disebut **estimasi risiko inheren bersyarat**. Jika asumsi tidak sesuai, hasil skenario tersebut tidak berlaku. Skala serta pembatasan development perlu dipertanggungjawabkan dan dievaluasi dalam metode penelitian.

## Pertanyaan yang mungkin diajukan

| Pertanyaan | Inti jawaban |
| --- | --- |
| Apa kontribusi VibeSec jika pemindainya sudah tersedia? | Integrasi proses, snapshot yang dapat ditelusuri, normalisasi/duplikasi, bukti, penerjemahan lokal, analisis skenario bersyarat, riwayat dan laporan dalam satu alur web. Tidak mengklaim menciptakan algoritma SAST/SCA baru. |
| Apa hubungan vibe coding dengan aplikasi? | Vibe coding adalah asal objek penelitian. Asal itu dibuktikan melalui dokumentasi pembuatan proyek. Pemindaian menggunakan Semgrep dan OSV-Scanner; tidak otomatis memakai AI untuk memutuskan kebenaran temuan. |
| Mengapa SAST dan SCA digabung? | Kode aplikasi dan komponen pihak ketiga merupakan sumber temuan yang berbeda. Jumlahnya dilaporkan terpisah karena satuan temuannya berbeda. |
| Apakah terkonfirmasi berarti dapat diretas? | Tidak. Untuk SCA, yang dipastikan adalah kecocokan paket/versi dengan advisory. Keterjangkauan fungsi dan eksploitasi belum dibuktikan. |
| Mengapa ada hasil tanpa skor? | Bukti konteks, kepastian temuan, atau vektor CVSS yang didukung belum memadai. Tanpa skor tidak berarti aman atau berisiko rendah. |
| Apakah otomatis berarti selalu benar? | Tidak. Otomatis berarti proses berjalan menurut aturan yang tercatat. Ketepatan keputusan tetap perlu dievaluasi terhadap acuan independen. |
| Apakah skor 6 dua kali lebih berbahaya dari 3? | Tidak. Skala bersifat ordinal untuk pengelompokan dan pengurutan, bukan perbandingan proporsional. |
| Apakah aplikasi memperbaiki kerentanan? | Aplikasi memberi arah penanganan dan informasi versi perbaikan bila tersedia. Aplikasi tidak otomatis mengubah atau membuktikan keamanan kode yang diperbaiki. |
| Apakah nol temuan berarti aman? | Tidak. Hasil dibatasi cakupan aturan, bahasa, versi alat, data advisory, dan kemampuan analisis statis. |
| Bagaimana hasil dapat ditelusuri? | Ada identitas scan, snapshot dan hash, versi alat/konfigurasi, lokasi bukti, konteks dependensi, alasan, asumsi dan riwayat keputusan. Scan baru RA1 mencatat versi serta hash kebijakan risiko untuk pembekuan seri penelitian. |
| Apa fungsi WSL dan worker? | Worker menjalankan antrean pemindaian. WSL menyediakan lingkungan Linux bagi alat pemindai. Keduanya mendukung pelaksanaan, bukan metode analisis risiko. |
| Bagaimana terjemahan dilakukan? | Model Inggris–Indonesia berjalan lokal. Terjemahan hanya membantu membaca; teks asli, kode dan lokasi dipertahankan. Terjemahan tidak menjadi bukti tambahan kerentanan. |

## Peta komponen sederhana

**Antarmuka web → backend → antrean worker → Semgrep dan OSV-Scanner → pengolahan temuan → analisis risiko → laporan.**

MySQL menyimpan data terstruktur dan keputusan. Penyimpanan privat menyimpan arsip serta keluaran alat. Penerjemah lokal membantu penyajian bahasa. Isi proyek yang diunggah tidak dijalankan untuk mencoba eksploitasi.

## Hal yang harus jujur disampaikan

- Rancangan penelitian menargetkan 12 proyek: empat to-do list, empat chatbot, dan empat katalog/pemesanan. Jumlah serta asal sampel aktual harus sesuai data penelitian; proyek contoh aplikasi bukan otomatis sampel ChatGPT yang sah.
- Pengujian fungsi, database dan tampilan tidak sama dengan pembuktian ketepatan rubrik risiko. Validitas empiris RA1, sensitivitas terhadap asumsi, serta hasil penelitian pada seluruh sampel masih memerlukan evaluasi dan pelaporan nyata.
- Metode aplikasi terbaru otomatis. BAB I–III asli masih menyebut validasi manual dan R1. Salinan revisi di folder skripsi_revisi sudah menjelaskan metode otomatis bersyarat tanpa mengganti judul yang disetujui; gunakan salinan itu saat membahas revisi dengan pembimbing.
- Penelitian tidak membuktikan bahwa ChatGPT menyebabkan kerentanan, tidak mengukur seluruh kerentanan nyata, dan tidak melakukan pentest/DAST.

Rincian teknis aturan tersedia di [AUTOMATIC_ASSESSMENT.md](AUTOMATIC_ASSESSMENT.md). Panduan ini tidak mengubah aturan penilaian atau mengisi hasil penelitian yang belum dilakukan.
