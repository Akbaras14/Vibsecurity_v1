# Analisis risiko otomatis AUTO1 / RA1 dan prioritas teknis A1

Scan baru menyelesaikan unggah, SAST, SCA, normalisasi, penyaringan bukti, penetapan status, prioritas teknis, dan laporan tanpa formulir validasi manual. Tidak ada layanan AI atau unggahan data ke penerjemah/model eksternal.

## Keputusan AUTO1

Hanya scan dengan kedua alat completed yang diproses. SCA terkonfirmasi otomatis pada tingkat kecocokan paket, versi terkunci, dan kelompok advisory OSV yang sudah divalidasi parser. Ini tidak mengonfirmasi keterjangkauan fungsi rentan atau keberhasilan eksploitasi. SAST dan SCA dengan metadata tidak lengkap ditandai belum dapat dipastikan. Tidak ada penetapan false positive otomatis tanpa bukti pembatalan. Status unreviewed diproses sekali secara transaksional; riwayat manual terdahulu tidak ditimpa.

## Prioritas teknis A1

A1 tetap menjadi prioritas teknis terpisah dari estimasi risiko proyek RA1 dan rubrik R1 historis. A1 hanya dihitung pada kecocokan SCA terkonfirmasi yang memiliki vektor CVSS v3.0/v3.1 lengkap dan valid. K teknis = 1 jika AV lokal/fisik atau PR tinggi; = 3 jika AV jaringan, AC rendah, PR tidak diperlukan, dan UI tidak diperlukan; = 2 untuk kombinasi lengkap lainnya. Dampak teknis = maksimum C/I/A, dengan N=0, L=2, H=3. Jika semua dampak N, skor dikosongkan. Skor = K teknis × dampak teknis; prioritas rendah 1–2, sedang 3–4, tinggi 6–9. Dari beberapa vektor dipilih skor tertinggi lalu dampak tertinggi. Vektor asli disimpan di keputusan.

A1 adalah aturan operasional aplikasi, bukan rumus CVSS resmi atau estimasi probabilitas serangan. CVSS v2/v4, metadata yang hilang, dan konteks SAST tidak diberi skor rekaan. Prioritas A1 direkap terpisah dari skor risiko R1 historis; status otomatis tanpa skor tetap merupakan hasil akhir otomatis.

## Estimasi risiko proyek RA1

Judul skripsi tetap “Analisis Risiko Keamanan pada Proyek Hasil Vibe Coding Menggunakan Static Application Security Testing (SAST) dan Software Composition Analysis (SCA) melalui Aplikasi Vibe Security (VibeSec) Berbasis Web”. RA1 menambahkan analisis skenario risiko inheren bersyarat, bukan mengganti label skor A1 menjadi risiko.

### Bukti konteks CTX1

Worker membaca package-lock.json v2/v3 pada snapshot yang sama. Paket dan versi harus sama persis dengan temuan SCA. Tiap lokasi dependensi, path lockfile dan SHA-256 disimpan. Flag dev=true membentuk skenario development/build; dev tidak true membentuk skenario runtime. devOptional menandakan scope tidak pasti dan tidak diberi skor. Kecocokan manifest hanya membuktikan deklarasi lingkungan, bukan pemanggilan fungsi atau lingkungan deployment aktual. Lockfile v1, metadata rusak, atau path di luar snapshot tidak menghasilkan konteks berskor.

### Skenario, aset, dan asumsi

Setiap kombinasi scope dan vektor CVSS v3 lengkap menghasilkan satu skenario utuh. Aset yang dimodelkan adalah proses/data/artefak build untuk development atau proses layanan/data aplikasi untuk runtime. Kejadian ancaman adalah masukan penyerang mencapai fungsi rentan dan menimbulkan konsekuensi CIA advisory. Asumsi eksplisit: fungsi benar-benar dipanggil, prasyarat advisory terpenuhi, input penyerang terjangkau, dan scope sesuai penggunaan. Kontrol deployment yang tidak diketahui tidak dianggap telah diperiksa. Skenario development mengasumsikan paparan terbatas tanpa layanan produksi publik; jika asumsi ini tidak sesuai, hasil skenario tersebut tidak berlaku.

### Rubrik operasional

K awal = 1 untuk AV lokal/fisik atau PR tinggi; = 3 untuk AV jaringan, AC rendah, PR tidak diperlukan, dan UI tidak diperlukan; = 2 untuk kombinasi lengkap lainnya. Pada skenario development dengan asumsi paparan terbatas, K maksimum 2. Ini merupakan batas operasional penelitian, bukan bukti bahwa dependensi dev selalu lebih aman. CIA dimodelkan dari advisory: N=0, L=2, H=3. D = maksimum CIA. Skor risiko bersyarat = K × D; kategori rendah 1–2, sedang 3–4, tinggi 6–9. Skor tertinggi dipilih dari satu skenario utuh, dengan D sebagai pembanding berikutnya; nilai dari skenario berbeda tidak dicampur.

RA1 bukan rumus resmi NIST, bukan skor CVSS Environmental, bukan probabilitas serangan dan bukan risiko residual. Tanpa seluruh prasyarat penilaian, risiko tetap tanpa skor. SAST tetap mendapat uraian keterbatasan dan rekomendasi tanpa skor risiko karena analisis alur, kontrol, aset, serta dampak belum terbukti otomatis. Advisory tanpa CVSS v3 lengkap juga tanpa skor; A1 tersedia terpisah bila memenuhi syaratnya.

Ringkasan dan filter risiko memakai RA1; risiko R1 historis dan prioritas A1 tetap disimpan terpisah. Ringkasan adalah risiko bersyarat tertinggi di antara temuan berskor, bukan risiko total proyek. Temuan tanpa skor selalu dicantumkan. JSON/CSV dan laporan menyertakan konteks, asumsi, vektor, alasan K/D, dan riwayat. Scan baru mencatat versi kebijakan dan SHA-256 kode rubrik pada metadata alat; pembekuan RA1 memasukkannya ke manifest agar perubahan kebijakan tidak tercampur dalam seri utama. Perintah `python -m backend.reassess_risk` menambah keputusan baru pada hasil AUTO1 lama; tidak menimpa keputusan manual atau mengubah sampel penelitian yang sudah dibekukan. Pemanggilan ulang idempoten.

### Verifikasi dan batas penelitian

Pengujian perangkat lunak memeriksa pasangan scope/versi, batas path, vektor tidak lengkap/duplikat, pemisahan A1/RA1/R1, perhitungan skenario, penyimpanan, ekspor, dan filter. Pengujian itu belum membuktikan validitas empiris rubrik atau ketepatan klasifikasi terhadap kerentanan nyata. Sebelum menyatakan hasil penelitian final, evaluasi ketepatan dan sensitivitas rubrik terhadap acuan penilaian independen, serta laporkan kecocokan dan pelanggaran asumsi pada sampel. Penilaian acuan untuk evaluasi tidak menjadi langkah wajib pada alur penggunaan aplikasi.

Dasar pembedaan keparahan dan risiko serta pencatatan asumsi/ketidakpastian: FIRST CVSS v3.1 User Guide (https://www.first.org/cvss/v3.1/user-guide), NIST SP 800-30 Rev.1 (https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-30r1.pdf). Skala, pemetaan dan batas RA1 adalah keputusan operasional aplikasi yang masih memerlukan evaluasi.

## Perubahan skripsi yang diperlukan

BAB I: ubah rumusan, batasan, dan tujuan yang menetapkan validasi/penilaian oleh penulis. BAB II: jelaskan penyaringan otomatis, ketidakpastian, perbedaan prioritas teknis dan risiko kontekstual. BAB III: dokumentasikan AUTO1/A1/RA1 dan CTX1, versi kebijakan, aturan keputusan, penanganan data yang hilang, dan evaluasi ketepatan terhadap acuan penilaian manusia. Jangan menyebut skor A1 sebagai penilaian risiko R1 atau mengklaim validasi manusia sudah dilakukan. Dokumen bab asli tidak diubah dalam pekerjaan ini.
