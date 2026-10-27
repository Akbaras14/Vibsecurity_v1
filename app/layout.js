import './globals.css';
import Shell from './components/shell';

export const metadata = {
  title: { default: 'VibeSec — Analisis Keamanan Proyek', template: '%s | VibeSec' },
  description: 'Workspace lokal untuk analisis keamanan kode sumber dan dependensi melalui SAST dan SCA.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <body><Shell>{children}</Shell></body>
    </html>
  );
}
