'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

function Mark() {
  return <svg width="28" height="32" viewBox="0 0 28 32" fill="none" aria-hidden="true"><path d="M14 2 25 6v9c0 7-5 11-11 15C8 26 3 22 3 15V6L14 2Z" stroke="currentColor" strokeWidth="2" /><path d="m8 14 4 4 8-9" stroke="currentColor" strokeWidth="2" /></svg>;
}

export default function Shell({ children }) {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const menu = useRef(null);
  useEffect(() => {
    if (!open) return;
    const links = [...document.querySelectorAll('#mobile-navigation a')];
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    links[0]?.focus();
    function close(event) {
      if (event.key === 'Escape') { setOpen(false); menu.current?.focus(); }
      if (event.key === 'Tab') {
        if (event.shiftKey && document.activeElement === links[0]) { event.preventDefault(); menu.current?.focus(); }
        else if (!event.shiftKey && document.activeElement === menu.current) { event.preventDefault(); links[0]?.focus(); }
      }
    }
    document.addEventListener('keydown', close);
    function resize() { if (window.matchMedia('(min-width: 651px)').matches) setOpen(false); }
    window.addEventListener('resize', resize);
    return () => { document.removeEventListener('keydown', close); window.removeEventListener('resize', resize); document.body.style.overflow = overflow; };
  }, [open]);
  const nav = [{ href: '/dashboard', label: 'Dashboard', icon: '◫' }, { href: '/projects', label: 'Proyek', icon: '▱' }];
  return <div className="workspace">
    <a className="skip-link" href="#content">Lewati ke konten</a>
    {open && <button className="nav-backdrop" aria-label="Tutup navigasi" onClick={() => { setOpen(false); menu.current?.focus(); }} />}
    <aside id="mobile-navigation" className={`sidebar ${open ? 'is-open' : ''}`}>
      <Link href="/dashboard" className="brand" onClick={() => setOpen(false)}><Mark /><span>vibe<span className="brand-light">sec</span><small>SECURITY WORKSPACE</small></span></Link>
      <div className="nav-caption">WORKSPACE</div>
      <nav aria-label="Navigasi utama">{nav.map(item => <Link key={item.href} href={item.href} onClick={() => setOpen(false)} aria-current={path.startsWith(item.href) ? 'page' : undefined} className={path.startsWith(item.href) ? 'nav-item active' : 'nav-item'}><span aria-hidden="true">{item.icon}</span>{item.label}</Link>)}</nav>
      <div className="sidebar-bottom"><span className="local-dot" /> Workspace lokal<p>Analisis kode & dependensi.<br />Data tersimpan pada instalasi ini.</p><div className="mono version">VIBESEC / MVP 0.1</div></div>
    </aside>
    <div className="main-column"><header className="topbar"><button ref={menu} type="button" className="menu-button" aria-label="Buka atau tutup navigasi" aria-expanded={open} aria-controls="mobile-navigation" onClick={() => setOpen(!open)}>☰</button><span className="topbar-title">Vibe Security <span>/</span> {path.startsWith('/scans') ? 'Analisis' : path.startsWith('/projects') ? 'Proyek' : 'Dashboard'}</span><span className="local-label"><span className="local-dot" /> Lokal · Tanpa login</span></header><main id="content">{children}</main><footer className="footer"><span>VibeSec — Static analysis workspace</span><span>SAST + SCA <span className="footer-separator">/</span> Tinjau bukti sebelum menilai risiko.</span></footer></div>
  </div>;
}
