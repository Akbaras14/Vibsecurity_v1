'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import { api, useResource } from '../../components/api';
import ProjectForm from '../../components/project-form';
import { Empty, ErrorBox, labels, Loading, PageHead, ResultDistribution, riskLabels, groupLabels, ScanTable, Stats } from '../../components/ui';

export default function Project() {
  const { id } = useParams();
  const router = useRouter();
  const data = useResource(`/projects/${encodeURIComponent(id)}`);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const form = useRef(null);
  function chooseFile(candidate) {
    setError('');
    if (candidate && (!candidate.name.toLowerCase().endsWith('.zip') || candidate.size > 100 * 1024 * 1024 || !candidate.size)) {
      setFile(null); setError('Pilih satu ZIP yang tidak kosong dengan ukuran maksimal 100 MB.'); return;
    }
    setFile(candidate || null);
  }
  function drop(event) {
    event.preventDefault(); setDragging(false);
    if (busy) return;
    if (event.dataTransfer.files.length !== 1) { setError('Pilih satu arsip ZIP untuk setiap pemindaian.'); return; }
    chooseFile(event.dataTransfer.files[0]);
  }
  async function upload(event) {
    event.preventDefault(); if (!file) return;
    if (!file.name.toLowerCase().endsWith('.zip') || file.size > 100 * 1024 * 1024) { setError('Pilih ZIP dengan ukuran maksimal 100 MB.'); return; }
    setBusy(true); setError('');
    try {
      const body = new FormData(); body.append('file', file);
      const result = await api(`/projects/${id}/scans`, { method: 'POST', body });
      router.push(`/scans/${result.data.id}`);
    } catch (error) { setError(error.message); } finally { setBusy(false); }
  }
  async function remove() {
    setBusy(true); setError('');
    try { await api(`/projects/${id}`, { method: 'DELETE' }); router.push('/projects'); }
    catch (error) { setError(error.message); } finally { setBusy(false); }
  }
  const project = data.result?.data;
  return <><Link className="back-link" href="/projects">← Daftar proyek</Link><PageHead eyebrow={project?.sample_code || 'DETAIL PROYEK'} title={project?.name || 'Memuat proyek…'} description={project ? `${project.technology || 'Teknologi belum dicatat'} · ${groupLabels[project.sample_group] || 'Belum dikelompokkan'}` : 'Metadata dan riwayat pemindaian'} />{data.error && <ErrorBox message={data.error} retry={data.reload} />}{error && <ErrorBox message={error} />}{data.loading && <Loading />}
    {project && <><section className="card upload-card"><div><h2>Pindai proyek</h2><p className="muted">Unggah ZIP berisi kode dan <code>package-lock.json</code>.</p><p className="fine-print muted">Maksimal 100 MB ZIP · 200 MB ekstraksi<br />Tidak menjalankan kode atau menginstal dependensi.</p></div><form ref={form} onSubmit={upload} className="upload-form"><label className={`upload-zone ${dragging ? 'is-dragging' : ''}`} onDragOver={event => { event.preventDefault(); if (!busy) setDragging(true); }} onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false); }} onDrop={drop}><span className="upload-arrow" aria-hidden="true">↑</span><strong>{file ? file.name : 'Pilih arsip proyek (.zip)'}</strong><span>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB · Siap divalidasi` : 'Tarik ZIP ke sini atau pilih dari komputer'}</span><input type="file" name="file" accept=".zip,application/zip" disabled={busy} onChange={event => chooseFile(event.target.files[0])} /></label>{file && <button type="button" className="button small secondary" disabled={busy} onClick={() => { chooseFile(null); form.current.reset(); }}>Hapus pilihan file</button>}<button className="button" disabled={!file || busy}>{busy ? 'Mengunggah & memvalidasi…' : 'Mulai pemindaian →'}</button></form></section>
    <Stats items={[{ label: 'Status terbaru', value: project.scans.length ? labels[project.scans[0].status] : 'Belum dipindai', note: 'Snapshot terbaru proyek' }, { label: 'Temuan terbaru', value: project.summary.total, note: 'Hasil tersimpan pada snapshot terbaru' }, { label: 'Risiko tertinggi', value: riskLabels[project.summary.risk_analysis?.highest || project.summary.highest_risk], note: 'Estimasi RA1 bersyarat; bukan risiko total' }, { label: 'Belum dinilai', value: (project.summary.risk_analysis?.categories.unassessed ?? project.summary.risks.unassessed), note: 'Konteks atau advisory belum memadai' }]} />
    {project.scans.length > 0 && <details className="card compact-details"><summary>Distribusi temuan</summary><ResultDistribution summary={project.summary} /></details>}
    <details className="card compact-details"><summary>Versi proyek dan pemeriksaan utama</summary><p>Pemeriksaan utama: {project.main_scan_id ? <Link href={`/scans/${project.main_scan_id}`}>{project.main_scan_id}</Link> : 'Belum ditetapkan'}</p><p>Unggah arsip yang sama untuk membuat pemeriksaan ulang pada versi yang sama. Perubahan SHA-256 membentuk versi baru.</p>{project.versions?.map(v => <details key={v.id}><summary>Versi {v.id} · {v.created_at}</summary><p className="mono">SHA-256: {v.sha256}</p><pre>{JSON.stringify(typeof v.documentation === 'string' ? JSON.parse(v.documentation) : v.documentation, null, 2)}</pre></details>)}</details>
    <section className="card activity"><div className="card-header"><h2>Riwayat pemindaian</h2><span className="muted">{project.scans.length} snapshot</span></div>{project.scans.length ? <ScanTable scans={project.scans} /> : <Empty title="Belum ada snapshot" description="Unggah ZIP untuk membuat pemindaian pertama. Setiap unggahan menyimpan riwayat baru." />}</section>
    <details className="card metadata-card"><summary>Ubah informasi proyek</summary><ProjectForm project={project} onSaved={data.reload} /></details>
    <section className="card danger-zone"><div><h2>Hapus proyek</h2><p>Hapus metadata, seluruh snapshot, dan hasil pemindaian. Tindakan ini tidak dapat dibatalkan.</p></div>{confirmDelete ? <div className="delete-confirm"><strong>Hapus semua data proyek ini?</strong><div><button className="button secondary small" disabled={busy} onClick={() => setConfirmDelete(false)}>Batal</button><button className="button danger small" disabled={busy} onClick={remove}>{busy ? 'Menghapus…' : 'Ya, hapus proyek'}</button></div></div> : <button className="button secondary danger-text" onClick={() => setConfirmDelete(true)}>Hapus proyek</button>}</section></>}
    {data.error?.includes('Pembersihan proyek') && <button className="button danger" disabled={busy} onClick={remove}>Ulangi pembersihan proyek</button>}
  </>;
}
