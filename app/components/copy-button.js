'use client';

import { useEffect, useState } from 'react';

export default function CopyButton({ value, label = 'Salin' }) {
  const [status, setStatus] = useState('');
  useEffect(() => {
    if (!status) return;
    const timer = setTimeout(() => setStatus(''), 2500);
    return () => clearTimeout(timer);
  }, [status]);
  async function copy() {
    try { await navigator.clipboard.writeText(value); setStatus('Tersalin ✓'); }
    catch { setStatus('Gagal menyalin; coba lagi'); }
  }
  return <button type="button" className="button small secondary copy-button no-print" onClick={copy} aria-label={label}><span role="status">{status || label}</span></button>;
}
