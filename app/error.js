'use client';

export default function ErrorPage({ reset }) {
  return <div className="empty" role="alert"><h1>Halaman tidak dapat ditampilkan.</h1><p>Coba muat ulang halaman. Data proyek tetap tersimpan pada backend.</p><button className="button" onClick={reset}>Coba lagi</button></div>;
}
