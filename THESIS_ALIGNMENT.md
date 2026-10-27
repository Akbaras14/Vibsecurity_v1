# Naskah yang disederhanakan

Salinan BAB I–III yang mengikuti metode aplikasi saat ini tersedia di `skripsi_revisi/BAB_1_Revisi.docx`, `BAB_2_Revisi.docx`, dan `BAB_3_Revisi.docx`. Judul tetap dipertahankan; dokumen asli tidak diubah. Naskah menekankan empat pertanyaan: objek yang diperiksa, bukti temuan, cara analisis risiko, serta batas kesimpulan. Bagian evaluasi merupakan rencana penelitian, bukan klaim bahwa pengukuran empiris sudah dilaksanakan.

# Penyesuaian terhadap judul yang sudah disetujui

Judul tetap dipertahankan. Implementasi terbaru menambahkan analisis risiko inheren bersyarat RA1 dengan konteks dependensi CTX1 dari snapshot, skenario ancaman, aset yang dimodelkan, kemungkinan, dampak CIA, alasan dan asumsi. Ini memperluas A1 yang hanya mengurutkan prioritas teknis. Uraian lengkap dan batas metode terdapat di AUTOMATIC_ASSESSMENT.md.

Kesesuaian dengan fokus judul tidak berarti BAB I–III lama otomatis sesuai: bab tersebut masih menetapkan validasi manual dan R1 kontekstual oleh penulis. Penjelasan metode perlu diperbarui menjadi analisis otomatis bersyarat, tanpa mengubah judul. RA1 tidak membuktikan reachability atau risiko residual. Ketepatan empiris rubrik dan hasil pada 12 sampel belum dibuktikan oleh pengujian perangkat lunak.

Bagian berikut merupakan catatan implementasi terdahulu; ketentuan metode terbaru di atas dan AUTOMATIC_ASSESSMENT.md berlaku untuk scan baru.

# Perubahan metode menjadi otomatis

Atas permintaan pengguna, mode terbaru menggunakan AUTO1 untuk penyaringan otomatis serta A1 untuk prioritas teknis berbasis CVSS v3. Tidak ada keputusan manual yang diperlukan pada alur scan baru. Keputusan otomatis tetap dapat berakhir belum dapat dipastikan, dan skor teknis dapat kosong jika bukti tidak memadai. A1 bukan penilaian risiko penggunaan proyek menurut R1.

BAB I–III asli belum diubah dan masih menetapkan validasi manual serta penilaian R1 oleh penulis. Karena itu implementasi terbaru tidak boleh diklaim sepenuhnya sesuai metode naskah lama. Lihat AUTOMATIC_ASSESSMENT.md untuk aturan, batas, serta penyesuaian penelitian yang diperlukan. Pemetaan berikut adalah riwayat kesesuaian sebelum perubahan metode ini.

# Kesesuaian VibeSec dengan BAB I sampai BAB III

Acuan: Bab_1.docx, Bab_2.docx, dan Bab_3.docx yang tersedia pada 26 Oktober 2026. Dokumen skripsi asli tidak diubah. Implementasi mendukung pelaksanaan penelitian; pengujian fixture bukan hasil penelitian pada 12 sampel.

| Ketentuan | Implementasi dan bukti |
| --- | --- |
| BAB I: 12 proyek ChatGPT, 4 per kelompok | Metadata kelompok dan kode TD01–TD04, CB01–CB04, KP01–KP04. Pembekuan memeriksa kode, catatan pembuatan, Next.js, TypeScript, dan satu package-lock.json. Asal proyek serta ketiadaan instruksi keamanan harus dibuktikan penulis melalui dokumentasi nyata. |
| BAB II: severity berbeda dari risiko | Severity asli/CVSS disimpan terpisah. Risiko hanya dari temuan terkonfirmasi berdasarkan skenario R1. Konfirmasi tidak membuktikan eksploitasi. |
| 3.3, 3.4: proyek, versi, pemeriksaan | project_versions mengidentifikasi arsip unik per proyek berdasarkan SHA-256 dan menyimpan salinan metadata. Unggahan arsip sama membentuk scan baru pada versi sama. Pelaksanaan SAST/SCA disimpan dalam dua entri methods pada pemeriksaan, berikut status, waktu, konfigurasi, keluaran mentah, dan manifest.json. |
| 3.4.5, 3.6: riwayat keputusan | validation_history bersifat append-only melalui API. Setiap perubahan merupakan keputusan baru. risk_scenarios merujuk ke keputusan, bukan menimpa penilaian sebelumnya. Status lain mengeluarkan skor dari ringkasan aktif. |
| 3.5.1: satu pemeriksaan utama | Pembekuan versi menyimpan manifest konfigurasi akhir dan catatan penelaahan cakupan. Rekap memilih pemeriksaan lengkap pertama pada versi tersebut yang cocok dengan seluruh versi/hash konfigurasi. Scan baru, gagal, atau parsial tidak menggantinya. |
| 3.5.2: aturan SAST resmi lokal | backend/rules/research.yml berisi pilihan 37 aturan resmi. research-manifest.json menyimpan repositori, commit, kelompok, hash sumber, ID, dan dua pengecualian untuk ditelaah. Seluruh 37 aturan lolos validasi Semgrep CE. Berkas pengabaian sampel tidak mengubah konfigurasi; node_modules, .next, .git, dist, build, out, coverage dikecualikan. |
| 3.5.3: SCA luring | OSV-Scanner 2.7.0 memakai snapshot npm lokal dan konfigurasi tanpa suppression, tanpa instalasi/resolusi dependensi/call analysis. Hash sebelum/sesudah diperiksa. Perubahan konfigurasi atau DB tidak dimasukkan ke rekap utama yang telah dibekukan. |
| 3.5.4: normalisasi dan duplikasi | SAST memakai rule, path, posisi awal dan akhir. SCA memakai kelompok alias, npm, nama, versi; seluruh lokasi lockfile digabung dan ID sumber disimpan. Keluaran mentah tetap tersedia di storage privat. Jumlah mentah dan unik dicatat per alat pada scan baru; data lama yang tidak mencatatnya ditampilkan tidak tersedia. |
| 3.7: rubrik R1 | Setiap skenario menyimpan aset, bukti jalur/prasyarat, K, C/I/A, alasan, serta ketidakpastian. D adalah maksimum aspek relevan. Ketidakpastian membatalkan skor skenario. Temuan memilih skor tertinggi, lalu D tertinggi pada skor sama. Tidak mengambil K dan D dari skenario berbeda. |
| 3.7.4: prioritas | K × D, rendah 1–2, sedang 3–4, tinggi 6–9. Temuan diurutkan menurut skor lalu dampak; pasangan sama memiliki prioritas setara. |
| 3.8: pengujian | backend/test_backend.py menguji unggahan, traversal, status, keluaran, duplikasi, matriks, skenario, riwayat, pemeriksaan utama, ekspor, dan migrasi. scripts/check-reading-ui.mjs menguji penyimpanan R1, riwayat, tampilan ponsel, dan laporan. Pengujian WSL menguji firewall dan batas proses. |
| 3.9: laporan deskriptif | Jumlah SAST/SCA terpisah, mentah/unik, status validasi, persentase dari yang ditinjau, risiko dari skor lengkap, penyebut nol menjadi tidak dapat dihitung. Temuan tanpa skor dan alasannya tetap dilaporkan. Risiko tertinggi bukan risiko total proyek. |

## Keputusan konfigurasi aktual

Tabel 3.3 menyatakan versi sebagai pilihan awal yang boleh disesuaikan sebelum pemeriksaan utama. Konfigurasi yang sudah diuji menggunakan Semgrep CE 1.179.0, OSV-Scanner 2.7.0, MySQL 9.7.0-csa, dan PyMySQL 1.1.2. PyMySQL dipertahankan karena penghubung yang sudah digunakan aplikasi dan diuji transaksi/kueri berparameter. BAB II/III menyebut MySQL Connector/Python dan pilihan awal MySQL 8.4 serta Semgrep 1.182.0; catatan implementasi skripsi perlu menyatakan penyesuaian aktual ini. Tidak ada klaim bahwa versi rancangan awal telah terpasang.

Aplikasi web menggunakan Next.js dengan komponen JavaScript; persyaratan Next.js/TypeScript/npm untuk sampel diperiksa saat pembekuan. Backend Windows dan worker WSL memakai runtime masing-masing. Catat versi patch, perangkat keras, kernel, dan distribusi aktual pada laporan penelitian sebelum menetapkan pemeriksaan utama.

## Penggunaan

1. Lengkapi metadata proyek dan dokumentasi interaksi ChatGPT yang nyata.
2. Unggah arsip sampel. SHA-256 yang sama memakai versi yang sama, tetapi pemeriksaannya tetap memiliki ID baru.
3. Periksa keluaran dan cakupan kedua alat. Lengkapi catatan penelaahan cakupan pada halaman scan, lalu bekukan versi sebagai sampel utama. Pembekuan pertama menetapkan konfigurasi akhir yang harus sama pada seluruh sampel.
4. Tinjau temuan hanya pada pemeriksaan lengkap. Pilih status, tulis bukti/alasan/rujukan. Untuk temuan terkonfirmasi, tambahkan skenario R1 atau alasan belum dapat dinilai.
5. Catat K menurut K3 lalu K2 lalu K1, CIA sesuai bukti, dan ketidakpastian. Simpan keputusan. Riwayat dapat dibaca di detail dan laporan/ekspor.
6. Gunakan rekap pemeriksaan utama untuk analisis 12 sampel. Hasil dengan konfigurasi lain tetap menjadi pemeriksaan terpisah dan tidak dicampur ke seri utama.

## Data lama dan batas kesimpulan

Migrasi menyalin keputusan lama ke riwayat. Skor sebelum R1 dikosongkan pada ringkasan aktif dan ditandai perlu penilaian ulang; bukti serta nilai lama tidak dihapus. Arsip lama memperoleh identitas versi berdasarkan hash, dengan dokumentasi historis yang tidak tersedia ditandai legacy.

Aplikasi tidak menetapkan kebenaran penilaian manusia, menghasilkan 12 sampel, mengarang riwayat prompt, membuktikan eksploitasi, menghitung recall, atau menyimpulkan ChatGPT menyebabkan kerentanan. Kelengkapan bukti, pelaksanaan seluruh sampel, validasi substantif, dan kesimpulan tetap merupakan pekerjaan penelitian penulis.
