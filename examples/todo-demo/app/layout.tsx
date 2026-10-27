import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './style.css';

export const metadata: Metadata = {
  title: 'Daftar Tugas — Contoh Uji VibeSec',
  description: 'Proyek contoh untuk menguji unggah dan pemindaian VibeSec.'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="id"><body>{children}</body></html>;
}
