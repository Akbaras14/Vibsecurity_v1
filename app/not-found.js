import Link from 'next/link';

export default function NotFound() {
  return <div className="empty"><div className="eyebrow">404</div><h1>Halaman tidak ditemukan.</h1><p>Periksa alamat atau kembali ke workspace.</p><Link className="button" href="/dashboard">Kembali ke dashboard</Link></div>;
}
