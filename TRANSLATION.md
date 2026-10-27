# Terjemahan otomatis temuan

Worker menerjemahkan judul dan uraian temuan Inggris ke Indonesia sebelum menyimpan hasil SAST/SCA. Model Argos en-id 1.9 dijalankan lokal melalui CTranslate2 (CPU). Teks tidak dikirim ke layanan penerjemah. Teks asli disimpan; hasil Indonesia digunakan oleh daftar temuan, halaman bukti dan laporan serta disertakan pada ekspor JSON.

Cuplikan kode, path, nomor baris, ID advisory, URL, inline code dan blok kode tidak diterjemahkan. Terjemahan mesin membantu membaca; rujuk teks asli bila ada istilah yang kurang tepat. Uraian yang sudah berbahasa Indonesia dari scanner bukan target model Inggris–Indonesia.

Persiapan di WSL dari direktori proyek:

```sh
.venv-linux/bin/pip install -r backend/requirements-translation.txt
mkdir -p storage/translation
curl -L --fail https://data.argosopentech.com/argospm/v1/translate-en_id-1_9.argosmodel -o storage/translation/model-download.zip
.venv-linux/bin/python -c "import zipfile; zipfile.ZipFile('storage/translation/model-download.zip').extractall('storage/translation')"
```

Model dan cache hasil disimpan pada `storage/translation`, di luar snapshot proyek. Untuk menerjemahkan temuan lama, muat konfigurasi database worker lalu jalankan `.venv-linux/bin/python -m backend.translation`. Pemanggilan ulang melewati hasil yang sudah lengkap. Kegagalan penerjemah tidak membatalkan temuan pemindai; aplikasi menampilkan pemberitahuan dan teks sumber. Perbaiki instalasi model lalu jalankan perintah yang sama untuk mencoba lagi.

Model: https://github.com/argosopentech/argospm-index
