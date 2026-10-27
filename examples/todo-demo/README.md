# Contoh proyek to-do list untuk VibeSec

Proyek ini dibuat melalui Codex atas permintaan pengguna untuk menguji aplikasi VibeSec. Ini bukan salah satu dari 12 sampel penelitian yang dibuat melalui ChatGPT. Tidak ada kerentanan yang sengaja ditanamkan; hasil pemindai harus dibaca berdasarkan cakupan dan divalidasi manual.

Fitur: tambah tugas, tandai selesai, hapus, filter, dan penyimpanan lokal browser. Teknologi: Next.js App Router, TypeScript, React, npm, package-lock.json. Tidak ada akun, basis data, atau kunci API.

## Menjalankan contoh

```powershell
npm ci
npm run dev
```

Buka http://127.0.0.1:3001. Port 3000 tetap digunakan VibeSec.

## Memeriksa kode

```powershell
npm run typecheck
npm run build
```

## Menguji melalui VibeSec

Unggah arsip ZIP yang menyertakan app/, package.json, package-lock.json, tsconfig.json, dan next-env.d.ts. Jangan sertakan node_modules, .next, atau berkas lingkungan. Daftarkan sebagai contoh uji dengan kelompok sampel kosong. Nol temuan tidak membuktikan aplikasi bebas kerentanan.
