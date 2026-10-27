# Menjalankan VibeSec di laptop kedua

GitHub menyimpan kode, dependensi yang dideklarasikan, aturan scanner, contoh konfigurasi, dan dokumentasi. File `.env.local`, `.env.mysql.local`, `.env.wsl.local`, database, model terjemahan, snapshot OSV, hasil pemindaian, dan dokumen skripsi tetap bersifat lokal. File lokal pada laptop pertama tidak dihapus saat mengunggah kode.

## Kode dan lingkungan baru

1. Clone repository pada laptop kedua. Pasang Node.js yang sesuai dengan Next.js di package.json, Python, MySQL native, dan WSL Ubuntu-24.04.
2. Jalankan `npm ci`, buat virtual environment Windows `.venv`, lalu pasang `backend/requirements-dev.txt`. Buat virtual environment Linux `.venv-linux` terpisah untuk worker. Jangan menyalin virtual environment atau node_modules dari laptop pertama.
3. Salin `.env.example` menjadi `.env.local` dan isi akun MySQL laptop kedua. Jika memakai konfigurasi khusus Windows/WSL proyek, baca bagian setup pada README serta periksa path MySQL di `scripts/start-mysql.ps1`; instalasi MySQL mungkin berada pada lokasi berbeda.
4. Untuk mempertahankan konfigurasi lama, pindahkan `.env.local`, `.env.mysql.local`, dan `.env.wsl.local` secara privat, misalnya melalui media penyimpanan pribadi. Ketiganya berisi kredensial dan tidak dimasukkan ke repository publik. Path, alamat WSL, dan akun database perlu disesuaikan untuk laptop kedua; menyalin env saja tidak membuat database atau akun MySQL.
5. Siapkan pembatasan scanner, akun Linux `vibesec-scanner`, Semgrep, OSV-Scanner, serta salinan database npm mengikuti README. Jalankan konfigurasi WSL di laptop kedua setelah MySQL dan lingkungan tersedia agar alamat dan kredensial koneksi sesuai. Jangan menjalankannya pada laptop pertama hanya untuk memindahkan kode.
6. Siapkan penerjemah lokal mengikuti TRANSLATION.md. Model dan cache tidak disertakan di GitHub. Jalankan migrasi, API, frontend, dan supervisor worker sesuai README.

## Jika data pemindaian lama juga diperlukan

Ekspor database menggunakan fasilitas backup MySQL dan impor ke instance laptop kedua. Pindahkan juga direktori `storage/vibesec` agar arsip serta keluaran mentah tetap cocok dengan metadata database. Direktori `storage/osv` dan `storage/translation` dapat dipindahkan secara privat atau disiapkan kembali. Untuk perbandingan penelitian, gunakan snapshot OSV dengan hash yang sama.

Jangan menyalin direktori data MySQL saat server aktif. Backup kredensial, database, dan artefak tidak boleh diunggah sebagai file atau release publik. Laptop kedua memerlukan penyesuaian jaringan/firewall WSL setempat; kode tidak otomatis mengonfigurasi perangkat yang belum disiapkan.
