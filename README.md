Pindah komputer: [panduan laptop kedua dan konfigurasi lokal](PINDAH_LAPTOP.md).

Panduan presentasi: [penjelasan proyek dan demo untuk penguji](PANDUAN_PENGUJI.md).

Analisis risiko otomatis terbaru: VibeSec mempertahankan fokus judul skripsi melalui estimasi risiko inheren bersyarat RA1, konteks snapshot CTX1, dan skenario dengan bukti serta asumsi eksplisit. Lihat [metode otomatis](AUTOMATIC_ASSESSMENT.md). A1 tetap prioritas teknis terpisah; R1 adalah riwayat penilaian terdahulu. Skor kosong berarti bukti tidak cukup, bukan risiko rendah.

# Mode analisis otomatis

Alur scan terbaru memakai AUTO1 dan prioritas teknis A1 tanpa pengisian validasi manual. Lihat AUTOMATIC_ASSESSMENT.md untuk aturan dan keterbatasan. R1 tetap disimpan sebagai riwayat; metode otomatis ini memerlukan revisi BAB I–III yang masih menetapkan validasi oleh penulis.

## Worker dengan pemulihan otomatis di Windows

Jalankan dari folder proyek menggunakan lingkungan Python proyek:

```powershell
.venv/Scripts/python.exe scripts/start-worker.py
```

Biarkan proses ini berjalan. Peluncur menyiapkan ulang izin MySQL untuk IP WSL saat ini tanpa mengganti kredensial API, menjalankan setup firewall/cgroup, lalu memulai worker. Jika WSL atau worker berhenti, peluncur mencoba kembali setelah 5 detik. Proses Linux juga mencoba kembali saat koneksi MySQL putus. Kunci worker dijaga selama pemindaian melalui heartbeat; kunci koneksi yang terputus akan kedaluwarsa setelah paling lama sekitar 120 detik tanpa aktivitas. Komputer dimulai ulang tetap memerlukan peluncur dijalankan lagi; belum dipasang sebagai layanan startup Windows.

# Pembaruan BAB I sampai BAB III

Lihat [THESIS_ALIGNMENT.md](THESIS_ALIGNMENT.md) untuk protokol R1, pemeriksaan utama, aturan resmi, dan keputusan versi aktual. Jalankan migrasi sebelum menjalankan API/worker. Data uji bukan hasil penelitian.

# VibeSec

Aplikasi lokal untuk analisis SAST dan SCA pada proyek hasil vibe coding. Frontend Next.js, backend Python/FastAPI, MySQL, dan worker Python. Tanpa login dan tanpa Docker. Metode penelitian dan batas implementasi dijelaskan pada [THESIS_ALIGNMENT.md](THESIS_ALIGNMENT.md). Naskah skripsi Word disimpan secara privat dan tidak disertakan dalam repository publik. [PRD_v1.md](PRD_v1.md) tetap menjadi acuan teknis untuk bagian yang tidak berubah. Status penerimaan dan batas pengujian dicatat di [IMPLEMENTATION.md](IMPLEMENTATION.md).

## Status implementasi

- Tahap 1: dashboard, CRUD proyek, MySQL, unggah ZIP, validasi/ekstraksi terbatas, dan metadata snapshot.
- Tahap 2: antrean persisten, worker, integrasi CLI Semgrep/OSV-Scanner v2, status per metode, serta pemulihan scan terputus.
- Tahap 3: filter/detail temuan, peninjauan manual, dan matriks risiko 3 x 3.
- Tahap 4: ekspor JSON/CSV serta laporan cetak browser.
- Tahap 5: tes integrasi, scanner nyata pada fixture rentan/bersih, firewall IPv4/IPv6, CPU/proses dan timeout tersedia. Pengujian sampel penelitian representatif tetap diperlukan.

Aplikasi tidak menggunakan hasil scanner simulasi. Fixture hanya digunakan dalam pengujian. Jika scanner atau konfigurasi belum siap, metode terkait berstatus gagal dengan alasan. Jika tidak ada bahasa/lockfile yang didukung, statusnya tidak didukung. Jalankan worker agar antrean diproses.

## Menyiapkan frontend dan backend

Persyaratan: Node.js yang kompatibel dengan Next.js versi di package.json (gunakan Node 22.13+), Python 3.11+, dan pip. Scanner membutuhkan Linux/WSL non-root; UI/API dapat dikembangkan di Windows. Instalasi dependensi membutuhkan internet.

```powershell
npm install
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
```

Di Linux/WSL gunakan `python3 -m venv .venv-linux`, kemudian `.venv-linux/bin/python` dan `.venv-linux/bin/pip` untuk perintah Python/pip. Jangan menggunakan virtual environment Windows pada Linux atau sebaliknya.

Frontend menggunakan `http://127.0.0.1:8000/api` secara default. `NEXT_PUBLIC_API_URL` dapat diisi di `.env.local`; variabel frontend dibekukan saat build. Backend membaca environment proses dan `.env.local`. Daftar variabel tersedia di `.env.example`; kredensial MySQL diperlukan.

## Konfigurasi MySQL dan migrasi

Gunakan MySQL 8.0.16+ (InnoDB, utf8mb4) sebagai layanan native, tanpa Docker. Siapkan database dan akun khusus melalui MySQL client/Workbench dengan akun administrasi Anda:

```sql
CREATE DATABASE vibesec CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'vibesec'@'127.0.0.1' IDENTIFIED BY 'GANTI_DENGAN_PASSWORD_KUAT';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
    ON vibesec.* TO 'vibesec'@'127.0.0.1';
```

Sesuaikan host akun dengan host API/worker. Isi `.env.local` di root proyek (backend memuatnya otomatis, environment proses tetap lebih diutamakan):

```dotenv
VIBESEC_MYSQL_HOST=127.0.0.1
VIBESEC_MYSQL_PORT=3306
VIBESEC_MYSQL_DATABASE=vibesec
VIBESEC_MYSQL_USER=vibesec
VIBESEC_MYSQL_PASSWORD=isi_password_akun_mysql_anda
```

Jangan menaruh kredensial pada variabel `NEXT_PUBLIC_*` atau Git. Akun di atas hanya memiliki izin pada database VibeSec. Bila API/worker berada di WSL dan MySQL di Windows, pastikan alamat host MySQL dapat dijangkau dari WSL dan izin akun sesuai; jangan mengasumsikan localhost WSL selalu menunjuk layanan Windows.

Jalankan dari root proyek:

```powershell
.venv/Scripts/python.exe -m backend.migrate
.venv/Scripts/python.exe -m backend.migrate --status
```

Migrasi berversi disimpan di `backend/migrations/` (001 skema awal, 002 kelompok sampel). Tabel `schema_migrations` menyimpan versi, nama, checksum, status dirty, dan waktu penerapan. Tabel aplikasi: `projects`, `scans`, dan `findings` (data review berada pada findings). Foreign key memakai cascade. Endpoint tidak memiliki login aplikasi; akun MySQL hanya digunakan oleh server Python.

API dan worker memeriksa migrasi saat startup. Named lock MySQL mencegah migrasi bersamaan, dan checksum menolak perubahan berkas migrasi yang sudah diterapkan. Untuk menambah perubahan, buat berkas berikutnya seperti `002_deskripsi.sql`.

DDL MySQL melakukan implicit commit sehingga perubahan skema yang sudah berhasil tidak otomatis dibatalkan jika perintah berikutnya gagal. Migrasi terlebih dahulu mencatat status dirty; kegagalan menghalangi migrasi lanjutan. Hentikan API/worker, periksa skema, pulihkan backup atau selesaikan perubahan secara manual sebelum memperbaiki penanda. Jangan menghapus penanda dirty tanpa memverifikasi skema. Tidak ada downgrade atau perintah repair destruktif otomatis. Rujukan: [MySQL implicit commit](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html).

Artefak ZIP/hasil mentah tetap berada di `storage/vibesec`; `VIBESEC_STORAGE` hanya mengubah lokasi artefak, bukan database. API, worker, dan migrasi harus menggunakan konfigurasi MySQL yang sama serta lokasi artefak yang sama. File database lama tidak dihapus atau diimpor otomatis.

## Menjalankan aplikasi

Jalankan tiga terminal dari root proyek:

```powershell
# Terminal 1: API Python
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

```powershell
# Terminal 2: frontend Next.js
npm run dev
```

```powershell
# Terminal 3: worker Python
.venv/Scripts/python.exe -m backend.worker
```

Buka `http://127.0.0.1:3000`. API docs lokal: `http://127.0.0.1:8000/docs`. Health: `GET /api/health`. Ketika scanner belum siap, proyek dan unggahan tetap dapat dikelola; worker menyimpan alasan kegagalan yang jelas. Satu worker aktif diperbolehkan per database melalui named lock MySQL.

Pada Windows, worker dapat memproses status tidak didukung atau gagal konfigurasi, tetapi tidak menjalankan scanner tanpa pembatasan OS. Untuk pemindaian nyata gunakan worker WSL/Linux; API dan Next.js boleh tetap di Windows dengan MySQL serta storage yang sama. Jangan menambahkan wildcard CORS atau bind HTTP `0.0.0.0` sebagai jalan pintas.

### Setup Windows + WSL yang tersedia pada proyek ini

Setup teruji memakai Ubuntu-24.04, MySQL native yang tersedia di `C:/Program Files/MySQL/MySQL Server 9.7/bin/mysqld.exe`, dan port khusus **3308**. Data MySQL berada di `storage/mysql-data`, terpisah dari instance pengguna. MySQL hanya bind loopback dan IP adaptor WSL. API tetap loopback port 8000, frontend port 3000. Versi server terpasang: **9.7.0-csa**; versi ini dicatat agar pengujian dapat direproduksi.

```powershell
# Terminal database; inisialisasi direktori kosong hanya pada pemakaian pertama.
./scripts/start-mysql.ps1
```

```powershell
# Sekali setiap boot WSL, sebagai administrator Linux.
wsl -d Ubuntu-24.04 -u root -- apt-get install -y iptables
wsl -d Ubuntu-24.04 -u root -- bash /mnt/e/Project_Coding/VibeSec/scripts/setup-scanner-host.sh

# Saat pertama menghubungkan, atau IP WSL berubah. Hentikan API/worker dahulu:
# perintah ini memperbarui password akun khusus proyek, tanpa memindahkan data.
.venv/Scripts/python.exe scripts/configure-wsl.py
.venv/Scripts/python.exe -m backend.migrate
```

Konfigurasi Windows disimpan pada `.env.local`; konfigurasi worker Linux pada `.env.wsl.local`. Kredensial administrasi instance khusus berada pada `.env.mysql.local` untuk konfigurasi ulang; API/worker memakai akun terpisah dengan izin hanya pada DB VibeSec. Semua file environment privat diabaikan Git. Konfigurasi `.env.local` sebelumnya dicadangkan ke `.cache/env-before-wsl.local`. Server MariaDB/MySQL lain tidak dihapus dan data tidak diimpor otomatis.

```powershell
# Terminal worker; gunakan ini sebagai pengganti worker Windows.
wsl -d Ubuntu-24.04 -u vibesec-scanner -- bash /mnt/e/Project_Coding/VibeSec/scripts/start-worker-wsl.sh
```

Akun Linux `vibesec-scanner` tidak memiliki sudo dan password login. Script host membatasi RAM seluruh pohon scanner menjadi 2 GB dan memasang aturan `iptables-legacy`/`ip6tables-legacy` untuk cgroup scanner saja. Backend legacy dibutuhkan kernel WSL terpasang; backend nft default tidak mendukung aturan yang diperlukan. Worker menguji firewall IPv4/IPv6, batas proses, dan timeout sebelum mengaktifkan kesiapan host. Jika tes gagal, worker tidak dimulai. Aturan ini tidak menghalangi koneksi database worker karena hanya subprocess scanner yang masuk cgroup jaringan.

## Menyiapkan scanner sesuai BAB 1 tanpa Docker

Scan baru menggunakan **Semgrep Community Edition 1.179.0** untuk SAST dan **OSV-Scanner 2.7.0** untuk SCA. OSV-Scanner versi 2 menggantikan Trivy sesuai BAB 1. Riwayat lama dipertahankan dengan identitas alat aslinya; jangan mencampur hasil alat lama ke rangkaian eksperimen baru.

Siapkan akun dan cgroup/firewall dengan `scripts/setup-scanner-host.sh` seperti bagian setup WSL. Runtime Semgrep ditempatkan di filesystem Linux untuk menghindari startup lambat akibat akses banyak berkas lintas filesystem Windows:

```powershell
wsl -d Ubuntu-24.04 -u root -- python3 -m venv /home/vibesec-scanner/semgrep-venv
wsl -d Ubuntu-24.04 -u root -- /home/vibesec-scanner/semgrep-venv/bin/pip install -r /mnt/e/Project_Coding/VibeSec/backend/requirements-scanner.txt
wsl -d Ubuntu-24.04 -- bash /mnt/e/Project_Coding/VibeSec/scripts/prepare-osv.sh
```

`prepare-osv.sh` mengunduh executable OSV dari rilis resmi v2.7.0, memeriksa SHA-256 terhadap checksum rilis, dan menyiapkan advisory npm resmi. Jalankan sebagai langkah setup/pembaruan yang disengaja saat worker berhenti. Jangan memperbarui snapshot di tengah rangkaian eksperimen. Metadata waktu pengunduhan, sumber, ekosistem, dan hash disimpan pada `storage/osv/metadata.json`.

Konfigurasi worker Linux pada `.env.wsl.local`:

```bash
VIBESEC_SEMGREP=/home/vibesec-scanner/semgrep-venv/bin/semgrep
VIBESEC_OSV_SCANNER=/mnt/e/Project_Coding/VibeSec/.cache/osv-scanner_linux_amd64
VIBESEC_OSV_CACHE=/mnt/e/Project_Coding/VibeSec/storage/osv
VIBESEC_MEMORY_CGROUP=/sys/fs/cgroup/memory/vibesec-scanner
VIBESEC_NETWORK_CGROUP=/sys/fs/cgroup/net_cls/vibesec-scanner
```

OSV 2.7 memakai cache `storage/osv/osv-scalibr/npm/all.zip`, yang diverifikasi terhadap implementasi versi terpasang. Worker memberikan path eksplisit, mode `--offline`, `--no-resolve`, `--no-call-analysis=all`, seluruh advisory, serta konfigurasi server tanpa suppression. Hanya salinan `package-lock.json` yang masuk SCA; kode, manifest lain, dan konfigurasi unggahan tidak dipakai. Tidak ada instalasi dependensi, build, atau eksekusi proyek.

OSV dapat mengembalikan exit code 1 ketika menemukan kerentanan. Status berhasil tetap mensyaratkan JSON valid dan tidak adanya kesalahan ekstraksi/pemuatan DB pada stderr; exit code 0 dengan kesalahan DB tidak dianggap hasil bersih. Kelompok alias advisory dihitung satu kali per paket/versi/lockfile. Severity mengambil skor maksimum kelompok OSV atau label advisory yang tersedia; nilai tak dikenal tetap Unknown. Versi perbaikan hanya diambil dari advisory untuk paket/ekosistem yang sesuai.

Worker menerapkan RAM 2 GB untuk seluruh pohon proses, maksimal 2 CPU logis, CPU time 300 detik, output 32 MB, serta batas 128 proses per UID. Semua subprocess scanner masuk cgroup jaringan yang diblokir firewall IPv4/IPv6. Worker sendiri tetap dapat mengakses MySQL. Script startup menguji firewall dan timeout sebelum mengaktifkan kesiapan host. Pembaca batas RAM menerima v1/v2; profil firewall teruji saat ini memakai `net_cls` v1, sehingga host pure cgroup v2 memerlukan profil lain yang diuji.

Uji scanner nyata memakai fixture terkontrol. Hentikan worker sebelum uji RAM, lalu jalankan sebagai akun `vibesec-scanner` dari root proyek di WSL:

```bash
set -a
source .env.wsl.local
set +a
VIBESEC_TEST_SCANNERS=1 .venv-linux/bin/python -m unittest backend.test_scanners -v
```

Ruleset lokal berada di `backend/rules/research.yml` (asal, commit, ID, dan hash: `backend/rules/research-manifest.json`); hash disimpan per scan. Tidak ada pembuktian eksploitasi atau klaim bebas kerentanan. Referensi teknis: [OSV offline](https://github.com/google/osv-scanner/blob/v2.7.0/docs/offline-mode.md), [OSV output](https://google.github.io/osv-scanner/output/), dan [Semgrep CLI](https://semgrep.dev/docs/cli-reference).

## Batas input dan akses

- ZIP maksimal 100 MB, hasil ekstraksi maksimal 200 MB, satu file maksimal 10 MB, dan maksimal 10.000 entri.
- Tolak ZIP rusak/terenkripsi, traversal path, symlink/tipe entri khusus, path duplikat, serta nama file tidak aman lintas platform.
- Direktori `.git`, `node_modules`, `vendor`, `dist`, `build`, `.next`, `out`, dan `coverage` dilewati; pengecualian dicatat.
- SAST: JS/JSX/TS/TSX/MJS/CJS. SCA: `package-lock.json` versi 1/2/3 yang dapat diproses oleh OSV-Scanner versi 2 yang dipatok. Tanpa lockfile, SCA tidak didukung.
- Bind frontend/API ke loopback. Tidak ada akun atau kepemilikan data: siapa pun yang dapat mengakses instalasi dapat membaca/mengubah seluruh workspace. Jangan mempublikasikannya langsung ke internet.
- Host/Origin dibatasi, termasuk penolakan origin browser asing. CORS bukan autentikasi. Storage tidak disajikan sebagai static/public directory.

## Peninjauan dan laporan

Severity dari alat disimpan terpisah dari risiko manual. Risiko = likelihood x impact; 1-2 rendah, 3-4 sedang, 6-9 tinggi. Temuan tanpa penilaian berstatus belum dinilai. Hasil validasi adalah Terkonfirmasi, Tidak sesuai, atau Belum dapat dipastikan; keadaan awal Belum ditinjau. Hanya temuan terkonfirmasi dengan bukti memadai yang boleh memiliki penilaian risiko. Hasil lain tetap dilaporkan, tetapi tidak masuk hitungan risiko penelitian. Dashboard menggunakan scan terbaru per proyek agar riwayat tidak menggandakan jumlah temuan.

Distribusi severity, peninjauan, dan risiko aktif tersedia di dashboard, detail proyek, detail scan, dan laporan. Status dashboard serta aktivitas terbaru memakai satu snapshot terbaru per proyek; jumlah antrean aktif tetap menghitung semua scan yang menunggu/berjalan. Proyek tanpa snapshot ditampilkan sebagai belum dipindai. Ringkasan risiko yang belum lengkap diberi label Sementara.

Setiap metode mencatat waktu mulai/selesai dan durasi, termasuk kegagalan konfigurasi. Metadata yang sempat diperoleh sebelum scanner gagal tetap tersimpan. Konfigurasi argumen dan pengecualian memiliki hash; ruleset SAST disalin per scan agar hash sesuai aturan yang dijalankan. Lokasi keluaran mentah berupa nama relatif privat, bukan URL publik. Perubahan snapshot OSV selama pemindaian menyebabkan kegagalan, sehingga operator harus membekukan snapshot DB selama eksperimen. Worker mencatat ID scan, fase, status, dan durasi tanpa isi kode atau kredensial.

Unduhan JSON memuat metadata, cakupan, hasil, review, dan risiko. CSV menggunakan kolom identitas plus JSON metadata/finding agar seluruh data tetap tersedia; nilai yang dapat menjadi formula spreadsheet dinetralkan. Laporan dapat dicetak ke PDF menggunakan dialog browser, bukan generator PDF server.

## Pengujian dan build

```powershell
.venv/Scripts/python.exe -m unittest backend.test_backend -v
npm run build
```

Pemeriksaan offline parser, arsip, dan risiko tidak membutuhkan database atau scanner. Pemeriksaan integrasi memakai database MySQL sementara yang dibuat/dihapus khusus untuk setiap test; tidak menggunakan emulasi MySQL. Cakupannya mencakup migrasi/penanda kegagalan DDL, CRUD, Host/Origin, snapshot, penolakan arsip berbahaya, status scan, parser, peninjauan, risiko, ekspor, recovery, dan penghapusan.

Untuk mengaktifkan seluruh tes integrasi MySQL, gunakan server test dan akun yang boleh membuat/menghapus database sementara. Nama database selalu `vibesec_test_<UUID>`; database aplikasi tidak dipakai atau dihapus. Konfigurasi koneksi tetap melalui `VIBESEC_MYSQL_*`.

```powershell
$env:VIBESEC_TEST_MYSQL = '1'
.venv/Scripts/python.exe -m unittest backend.test_backend -v
```

Pada setup instance khusus port 3308, gunakan konfigurasi administrasi privat hanya untuk tes pembuat database sementara (API/worker tetap memakai akun terbatas):

```powershell
.venv/Scripts/python.exe -c 'from dotenv import load_dotenv; load_dotenv(".env.mysql.local",override=True); import os,unittest; os.environ["VIBESEC_TEST_MYSQL"]="1"; unittest.main(module="backend.test_backend",verbosity=2)'
```

Tanpa flag tersebut, tes integrasi ditandai skipped secara eksplisit. Tes kegagalan migrasi memastikan DDL yang sempat berhasil tetap terdeteksi dan penanda dirty menghalangi kelanjutan.

Pemeriksaan browser opsional menggunakan Playwright. Setelah web, API, dan worker aktif:

```powershell
npx playwright install chromium
npm run test:web
```

Smoke test membuat proyek berlabel `[SMOKE]`, mengunggah ZIP terkontrol, menunggu status akhir, memeriksa ekspor/laporan cetak dan navigasi mobile, lalu menghapus proyek tersebut. Screenshot berada di `.cache/screenshots/`. Gunakan database MySQL test terpisah melalui `VIBESEC_MYSQL_DATABASE` serta lokasi `VIBESEC_STORAGE` yang sama pada API/worker. Untuk port lain, set `TEST_WEB_URL` dan `TEST_API_URL` pada proses test, `NEXT_PUBLIC_API_URL` pada frontend, serta `VIBESEC_ORIGINS` pada backend. `TEST_CHROMIUM` dapat menunjuk executable Chromium lokal yang sudah terpasang. Script hanya menerima host loopback.

## Pemulihan

- Worker berhenti: jalankan kembali. Scan berjalan dari worker lama ditandai terputus; hasil metode yang sudah berhasil dipertahankan. Unggah snapshot kembali untuk scan baru.
- Metode gagal: baca alasan di detail scan, periksa executable/ruleset/DB, dan ulangi menggunakan unggahan baru. Keluaran mentah tersimpan secara lokal, tidak dipublikasikan.
- Penghapusan file gagal: proyek diberi penanda pembersihan tertunda; gunakan tombol Ulangi pembersihan proyek. Proyek tidak dilaporkan berhasil terhapus sebelum file dibersihkan.
- Arsip berada di `storage/` dan metadata di MySQL; cadangkan keduanya sesuai kebutuhan. Kredensial server tetap berada di `.env.local`, bukan laporan.
