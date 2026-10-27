'use client';

import { useEffect, useState, type FormEvent } from 'react';

type Task = { id: string; text: string; done: boolean };
type Filter = 'all' | 'active' | 'done';
const storageKey = 'vibesec-todo-demo-v1';

function isTask(value: unknown): value is Task {
  if (!value || typeof value !== 'object') return false;
  const task = value as Record<string, unknown>;
  return typeof task.id === 'string' && typeof task.text === 'string'
    && task.text.length > 0 && task.text.length <= 200 && typeof task.done === 'boolean';
}

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [text, setText] = useState('');
  const [filter, setFilter] = useState<Filter>('all');
  const [ready, setReady] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    try {
      const saved: unknown = JSON.parse(localStorage.getItem(storageKey) || '[]');
      if (!Array.isArray(saved) || !saved.every(isTask) || saved.length > 500) {
        setMessage('Data tersimpan tidak valid. Daftar dimulai kosong.');
      } else setTasks(saved);
    } catch { setMessage('Data lokal tidak dapat dibaca. Daftar dimulai kosong.'); }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try { localStorage.setItem(storageKey, JSON.stringify(tasks)); }
    catch { setMessage('Penyimpanan browser tidak tersedia. Perubahan hanya bertahan selama halaman terbuka.'); }
  }, [tasks, ready]);

  function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = text.trim();
    if (!value || !ready) return;
    if (tasks.length >= 500) { setMessage('Batas 500 tugas tercapai. Hapus tugas yang sudah tidak diperlukan.'); return; }
    setTasks(previous => [...previous, { id: crypto.randomUUID(), text: value, done: false }]);
    setText('');
  }

  const remaining = tasks.filter(task => !task.done).length;
  const visible = tasks.filter(task => filter === 'all' || (filter === 'done' ? task.done : !task.done));
  return <main>
    <p className="eyebrow">CONTOH UJI VIBESEC · BUKAN SAMPEL SKRIPSI</p>
    <h1>Daftar tugas</h1>
    <p className="intro">Catat hal yang ingin dikerjakan, lalu selesaikan satu per satu.</p>
    <section className="panel" aria-label="Pengelolaan tugas">
      <form onSubmit={add}>
        <label htmlFor="task">Tugas baru</label>
        <div className="entry"><input id="task" value={text} onChange={event => setText(event.target.value)} maxLength={200} required placeholder="Contoh: Unggah proyek ke VibeSec" disabled={!ready} /><button disabled={!ready || !text.trim()}>Tambah</button></div>
      </form>
      <div className="toolbar"><p aria-live="polite">{ready ? `${remaining} belum selesai · ${tasks.length} total` : 'Memuat tugas…'}</p><label>Tampilkan<select value={filter} onChange={event => setFilter(event.target.value as Filter)}><option value="all">Semua</option><option value="active">Belum selesai</option><option value="done">Selesai</option></select></label></div>
      {message && <p className="message" role="status">{message}</p>}
      <ul>{visible.map(task => <li key={task.id}><label className={task.done ? 'done' : ''}><input type="checkbox" checked={task.done} onChange={() => setTasks(previous => previous.map(item => item.id === task.id ? { ...item, done: !item.done } : item))} /><span>{task.text}</span></label><button className="remove" aria-label={`Hapus tugas: ${task.text}`} onClick={() => setTasks(previous => previous.filter(item => item.id !== task.id))}>Hapus</button></li>)}</ul>
      {ready && !visible.length && <p className="empty">{tasks.length ? 'Tidak ada tugas pada filter ini.' : 'Belum ada tugas. Tambahkan tugas pertama di atas.'}</p>}
    </section>
    <p className="note">Data disimpan di browser ini. Tidak memerlukan akun atau koneksi layanan lain.</p>
  </main>;
}
