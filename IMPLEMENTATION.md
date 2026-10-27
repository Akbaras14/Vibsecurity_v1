# Perbaikan worker 28 Oktober 2026

Penyebab putus berulang direproduksi pada WSL: proses anak mewarisi socket MySQL milik worker sebelum preexec_fn memindahkannya ke cgroup net_cls. Migrasi cgroup mengklasifikasikan ulang socket bersama, sehingga firewall scanner memblokir koneksi induk. Query SELECT 1 sebelum proses anak berhasil, tetapi setelahnya timeout. process_limits sekarang menutup salinan descriptor socket di proses anak sebelum memasuki cgroup; koneksi induk tetap aktif dan tidak diberikan ke pemindai.

Regresi nyata test_scanner_keeps_parent_database_connection, firewall IPv4/IPv6, dan batas proses/timeout lulus. Enam belas tes offline backend juga lulus. Pengaturan firewall dan batas sumber daya tetap diberlakukan. Riwayat scan terputus dipertahankan; percobaan ulang memakai arsip yang sama dengan SHA-256 terverifikasi.

# Pembaruan 26 Oktober 2026 sesuai BAB I sampai BAB III

Implementasi terbaru menambahkan migrasi 003/004, versi arsip berdasarkan hash, snapshot dokumentasi, pembekuan konfigurasi/sampel utama, riwayat validasi, dan skenario risiko R1 dengan CIA serta ketidakpastian. Rekap penelitian memakai pemeriksaan lengkap pertama yang cocok dengan konfigurasi akhir; aktivitas terbaru tetap terpisah. Aturan SAST resmi lokal terdiri atas 37 aturan tervalidasi, dengan sumber/commit/hash/pengecualian tercatat. Laporan menyajikan riwayat, rekomendasi penulis, mentah/unik, dan persentase dengan penyebut yang benar.

Validasi akhir: 22 tes backend termasuk integrasi MySQL lulus; uji tambahan kegagalan penyimpanan memastikan transaksi menggulung balik dan riwayat tidak bertambah palsu. Build produksi seluruh rute lulus. Pemindaian nyata fixture terkontrol menghasilkan 1 temuan SAST dan 5 SCA, kedua alat completed (SAST 58,03 detik; SCA 24,46 detik). Uji Chrome lulus untuk simpan R1, perubahan status, riwayat skor, layar 390 px, dan cetak laporan. Fixture tidak dimasukkan ke sampel penelitian dan dibersihkan setelah pengujian.

Cadangan data sebelum migrasi disimpan privat di .cache/pre-bab3-migration.json. Data lama tetap tersedia; skor lama memerlukan penilaian ulang R1. Dokumen kesesuaian dan keputusan versi aktual: THESIS_ALIGNMENT.md. Catatan berikut merupakan riwayat implementasi sebelumnya, bukan spesifikasi terbaru.

# Status implementasi terhadap PRD_V1.md

Acuan: `PRD_v1.md` versi 1.3. Status ini membedakan implementasi aplikasi dari validasi scanner dan penelitian yang masih membutuhkan host siap pakai.

## Penyesuaian BAB 1 dan keterbacaan UI pada 20 Oktober 2026

Acuan penelitian terbaru adalah `BAB 1.docx`; pemetaan kebutuhan ada pada `THESIS_ALIGNMENT.md`. Ketentuan lama di bawah bagian ini merupakan catatan pemeriksaan sebelumnya.

- SCA scan baru diganti dari Trivy menjadi **OSV-Scanner 2.7.0**. SHA-256 binary diverifikasi terhadap checksum rilis resmi. Snapshot npm offline berhash `88e0d0fc50cb30a4a4e360069d6d6bff853449bac87ec31b1910c6dcac7e6faa` disimpan privat dengan metadata pengunduhan. Semgrep tetap **1.179.0**, memakai runtime Linux native dengan versi dependensi dicatat pada `backend/requirements-scanner.txt`.
- Scan nyata melalui antrean API/worker selesai dengan **1 temuan SAST** dan **5 advisory OSV** pada fixture terkontrol. Durasi metode SAST 96,11 detik dan SCA 98,49 detik, keduanya dalam anggaran 300 detik. Angka ini bukan hasil sampel penelitian.
- Migrasi `002_sample_group.sql` menambahkan kelompok sampel tanpa mengubah migrasi awal. Dashboard menampilkan target 12 proyek dan data nyata per kelompok (masing-masing target 4). Sampel tidak dibuat otomatis. Ringkasan kelompok hanya memakai scan lengkap Semgrep + OSV.
- API menolak penilaian risiko pada status selain Terkonfirmasi. Validasi tetap mendukung Tidak sesuai dan Belum dapat dipastikan. Ringkasan risiko hanya mencakup temuan terkonfirmasi; alasan penilaian tetap wajib. Matriks 3×3 dari PRD dipertahankan sementara sampai metodologi ditetapkan.
- **19 tes backend lulus** pada MySQL native, termasuk migrasi tambahan, kelompok sampel, normalisasi OSV/alias, kegagalan DB meskipun exit code 0, risiko khusus terkonfirmasi, serta cuplikan baris snapshot asli.
- UI memperbesar teks dan kontras, memindahkan daftar temuan sebelum distribusi, menyediakan filter cepat, lokasi/paket/versi perbaikan, serta tampilan kartu pada layar kecil. Detail memisahkan bukti, langkah penanganan, validasi risiko, dan referensi. CVSS ditampilkan terstruktur; laporan mencantumkan batas penelitian dan metadata alat yang benar-benar dipakai.
- Pengujian browser lokal `scripts/check-reading-ui.mjs` lulus: urutan informasi, simpan/muat ulang validasi, pembatasan form risiko, perubahan ke Belum dapat dipastikan yang mengeluarkan skor risiko, tampilan desktop/mobile tanpa overflow, dashboard penelitian, serta navigasi yang tersembunyi saat cetak. Screenshot pemeriksaan disimpan lokal pada `.cache/screenshots/`.
- Teks pengganti cuplikan dari Semgrep tidak dianggap bukti. Scan baru mengambil baris sumber dari snapshot tervalidasi dan tetap menyimpan keluaran mentah alat. Tampilan menyembunyikan placeholder pada riwayat lama jika cuplikan asli tidak tersedia.
- Pekerjaan UI dilakukan lokal. Pengiriman screenshot ke layanan desain eksternal ditolak pemeriksaan persetujuan otomatis dan tidak diteruskan.

Bab metodologi dan sampel penelitian representatif belum diberikan/ditetapkan. Tidak ada akurasi, hasil validasi substantif, atau kesimpulan penelitian yang direkayasa.

## Pemeriksaan lanjutan 20 Oktober 2026

- Instance MySQL native **9.7.0-csa** khusus VibeSec berjalan di port **3308**, dengan data privat `storage/mysql-data`. Migrasi `001_initial.sql` diterapkan. Server pengguna port 3306/3307 tidak diperbaiki, dihapus, atau diimpor. Konfigurasi sebelumnya dicadangkan privat.
- API Windows dan worker WSL Ubuntu-24.04 terhubung ke database yang sama dengan akun DB terpisah serta storage yang sama. Worker berjalan sebagai akun OS khusus `vibesec-scanner`, tanpa sudo/password login. Script setup dan startup berada di `scripts/`.
- Build produksi Next.js lulus. Uji browser Chrome desktop/mobile dengan `TEST_REQUIRE_SCANNERS=1` lulus: buat proyek, upload, kedua scanner nyata **completed**, ekspor JSON, laporan cetak, navigasi mobile, serta hapus proyek/artefak sementara. SAST menghasilkan satu temuan; SCA lima advisory. Durasi metode pada scan browser: SAST 147,85 detik dan SCA 37,55 detik, keduanya di bawah timeout 300 detik.
- SCA dibatasi ke salinan lockfile npm; manifest ekosistem lain tidak dipindai. Ignorefile Trivy dinonaktifkan. Tes memastikan salinan dibersihkan saat gagal tanpa menghapus sumber asli.
- Parser SCA menerima keluaran filesystem Trivy schema 2 yang sah tanpa `Results` (proyek tanpa dependensi); objek tanpa identitas keluaran atau tipe hasil yang rusak tetap ditolak.
- **16 tes backend lulus**: 15 tes termasuk integrasi dijalankan pada MySQL native 9.7.0-csa; tes tambahan kelas firewall cgroup lulus terpisah. Cakupan meliputi sembilan kombinasi status akhir, cakupan SCA, dan validasi cgroup v1/v2.
- Pemeriksaan versi scanner diberi waktu hingga 60 detik; keseluruhan metode tetap memiliki anggaran 300 detik. Pesan timeout mencantumkan batas proses sebenarnya.
- Tes scanner nyata tersedia di `backend/test_scanners.py`, diaktifkan dengan `VIBESEC_TEST_SCANNERS=1` pada Linux/WSL non-root. Fixture hanya berupa teks dan lockfile, tanpa instalasi atau eksekusi proyek.
- Kegagalan scanner akibat batas address-space diperbaiki dengan cgroup RAM maksimal 2 GB untuk seluruh pohon proses. Grup khusus disiapkan pada host WSL2. Semgrep **1.179.0** menghasilkan satu temuan eval; Trivy **0.75.0** menghasilkan lima advisory lodash **4.17.20**, keduanya exit code 0. Hash ruleset `36af527f8e62bf5392e9e33a1d69ec0371a1a1ae9ed74e6bf93069865003ec72`; hash DB `5f4b978a55284b1997dc31e9f2fc3f4f1abae80829f51451ade221d5675a69b9`. Snapshot DB bertanggal 7 Oktober 2026; tidak diperbarui otomatis.
- Uji host nyata untuk affinity maksimal 2 CPU, CPU time 300 detik, batas proses 128, penghilangan kredensial dari environment scanner, serta timeout yang menghentikan proses anak **lulus**.
- Firewall `iptables-legacy` dan `ip6tables-legacy` memblokir koneksi scanner IPv4/IPv6, termasuk loopback, melalui cgroup `net_cls` khusus. Tes membuktikan koneksi parent berhasil dan koneksi child scanner ke listener yang sama timeout. Worker tetap dapat mengakses database. Script startup menjalankan tes firewall dan timeout sebelum mengambil antrean.
- Uji RAM nyata **lulus**: alokasi 3 GB dalam cgroup scanner 2 GB dihentikan kernel; penghitung `oom_kill` bertambah. Pemakaian memori tertinggi tercatat sekitar batas 2 GB. Uji ini dijalankan saat tidak ada scanner aktif.
- Sampel bersih JS dan lockfile tanpa dependensi **lulus** pada scanner nyata dengan nol temuan. Keluaran Trivy tanpa `Results` dinormalisasi dengan validasi identitas schema filesystem.
- Pengukuran API lokal: 30 request berurutan per endpoint pada workspace kosong setelah smoke cleanup, Windows 10 build 19045 dan MySQL 9.7.0-csa port 3308. p95 `/api/projects` **20,28 ms** dan `/api/dashboard` **30,61 ms**. Data mentah ringkas ada di `.cache/performance.json`. Ini baseline workspace kosong, bukan penerimaan performa pada sampel penelitian representatif.

Alur aplikasi dengan scanner nyata berjalan. Penerimaan penelitian masih membutuhkan sampel representatif, pengukuran performa pada sampel tersebut, dan pembekuan konfigurasi eksperimen. Tidak ada angka akurasi atau klaim keamanan penelitian yang dibuat. Cgroup/firewall harus disiapkan kembali setelah boot WSL; perubahan IP WSL memerlukan konfigurasi koneksi ulang dan restart API/worker sesuai README.

## Fitur aplikasi

| Kebutuhan | Implementasi dan pemeriksaan |
| --- | --- |
| FR-01–03 | Dashboard tanpa login, CRUD dan metadata penelitian; API FastAPI dan form Next.js. Tes integrasi memeriksa validasi, mutasi, dan akses lokal. |
| FR-04–06 | Unggah ZIP, snapshot SHA-256, ekstraksi terbatas, bahasa/lockfile/pengecualian. Tes memeriksa traversal, symlink, benturan path, ukuran, dan input rusak. |
| FR-07–08 | Integrasi subprocess Semgrep/Trivy, ruleset server, DB lokal, versi/hash dan keluaran privat. Fixture rentan/bersih dan alur browser dengan worker Linux/MySQL/firewall telah lulus. |
| FR-09–10 | Antrean MySQL, status per metode/overall, normalisasi severity, deduplikasi, penolakan keluaran rusak, serta metadata kegagalan. Tes menggunakan fixture yang hanya berada dalam pengujian. |
| FR-11–13 | Filter/pencarian/paginasi temuan dan detail bukti SAST/SCA, advisory, referensi, CVSS serta remediasi jika tersedia. Data tidak tersedia tidak direkayasa. |
| FR-14–15 | Peninjauan manual, alasan wajib, likelihood/impact eksplisit dan sembilan kombinasi matriks risiko; hasil dihitung server. |
| FR-16 | Distribusi severity/review/risiko konsisten melalui satu komponen di dashboard, detail proyek/scan, dan laporan. Ringkasan proyek memakai snapshot terbaru, mengecualikan false positive dari risiko aktif, dan menandai penilaian sementara. |
| FR-17 | Unggahan baru membuat scan baru; snapshot/temuan/peninjauan lama tidak ditimpa. Status dashboard hanya menghitung scan terbaru per proyek. |
| FR-18 | CSV/JSON seluruh hasil dan laporan cetak; identitas, cakupan, kegagalan, bukti, review, risiko, CVSS dan referensi. CSV menetralkan formula. |
| FR-19 | Konfirmasi hapus, konflik saat scan aktif, cascade metadata serta penghapusan artefak; kegagalan dapat dicoba ulang. |

Tidak diperlukan perubahan skema untuk penyesuaian ini. `001_initial.sql` dipertahankan agar checksum migrasi database yang sudah diterapkan tetap valid. Repositori hanya memuat aplikasi analisis keamanan VibeSec.

## Pemeriksaan runnable

```powershell
# Pemeriksaan offline; tes MySQL ditandai skipped jika flag tidak diaktifkan.
.venv/Scripts/python.exe -m unittest backend.test_backend -v

# Gunakan server test dan akun yang boleh membuat/menghapus database sementara.
# Isi VIBESEC_MYSQL_* untuk server test di environment proses, bukan server produksi.
$env:VIBESEC_TEST_MYSQL = '1'
.venv/Scripts/python.exe -m unittest backend.test_backend -v

npm run build
# Setelah frontend, API dan worker test berjalan:
npm run test:web
```

Tes integrasi membuat database acak `vibesec_test_<UUID>` dan menghapusnya setelah selesai. Keluaran fixture scanner tidak menjadi hasil produksi. Smoke browser memeriksa alur membuat proyek, upload, status akhir, ekspor, cetak, mobile, dan hapus; jika scanner tidak tersedia, status gagal merupakan hasil yang diharapkan.

Hasil pemeriksaan 7 Oktober 2026: **11 tes Python lulus** pada MySQL 8.0.36 sementara (62,773 detik), build produksi Next.js lulus, dan smoke browser desktop/mobile lulus. Browser juga memeriksa distribusi hasil serta ringkasan risiko proyek. Scan browser berakhir gagal konfigurasi karena scanner belum tersedia; ini bukan bukti keberhasilan SAST/SCA nyata. Server test menggunakan port 3308 dan direktori `.cache/mysql-test/data`, terpisah dari MySQL pengguna di port 3306.

## Validasi yang belum terpenuhi

- **Operasional setelah reboot:** jalankan ulang script host untuk cgroup/firewall; bila IP WSL berubah, konfigurasi ulang koneksi sebelum restart API/worker.
- **Tahap 5:** validasi sampel penelitian nyata. Hasil fixture terkontrol dan smoke UI membuktikan kompatibilitas alur, bukan akurasi atau keamanan sampel penelitian.
- **NFR-12:** ukur p95 pada host dan sampel yang dicatat. Tidak ada angka performa atau akurasi penelitian yang diklaim.
- **Operasional:** backend memerlukan kredensial MySQL valid. Antrean dan halaman data tidak dapat digunakan bila koneksi DB gagal. `.env.local` harus diisi oleh operator; database pengguna tidak diubah sebagai bagian pengujian.

Penerimaan tahap validasi penelitian belum dinyatakan selesai sampai pengujian sampel representatif dan pembekuan konfigurasi eksperimen terpenuhi. Next.js, FastAPI, MySQL, tanpa login, dan tanpa Docker tetap menjadi arsitektur yang diwajibkan PRD.
