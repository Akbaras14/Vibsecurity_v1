'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { API, api, useResource } from '../../components/api';
import { Badge, date, Empty, ErrorBox, FindingsTable, labels, Loading, PageHead, ResultDistribution, riskLabels, Stats } from '../../components/ui';

export default function Scan() {
  const { id } = useParams();
  const scan = useResource(`/scans/${encodeURIComponent(id)}`, 3000);
  const [filters, setFilters] = useState({ q: '', method: '', severity: '', risk: '', review: '' });
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  useEffect(() => {
    if (filters.q === search) return;
    const timer = setTimeout(() => { setSearch(filters.q); setPage(1); }, 300);
    return () => clearTimeout(timer);
  }, [filters.q, search]);
  const query = new URLSearchParams(Object.fromEntries(Object.entries(filters).filter(([, value]) => value)));
  query.set('page', page);
  if (search) query.set('q', search); else query.delete('q');
  // Refresh findings while the scan is active so a completed method appears immediately.
  const active = !scan.result || ['queued', 'running'].includes(scan.result.data.status);
  const findings = useResource(`/scans/${encodeURIComponent(id)}/findings?${query}`, active ? 3000 : 0, true);
  const result = scan.result?.data;
  const [freezeError, setFreezeError] = useState('');
  const [coverageReview, setCoverageReview] = useState('');
  const [frozen, setFrozen] = useState('');
  const [freezing, setFreezing] = useState(false);
  async function freeze() {
    setFreezeError('');
    setFreezing(true);
    try { const r = await api(`/scans/${id}/freeze`, { method: 'POST', body: JSON.stringify({ reason: coverageReview }) }); setFrozen(r.data.main_scan_id); }
    catch (e) { setFreezeError(e.message); }
    finally { setFreezing(false); }
  }
  function filter(name, value) { setFilters(previous => ({ ...previous, [name]: value })); if (name !== 'q') setPage(1); }
  const searching = filters.q !== search || findings.updating;
  const filterNames = { q: 'Pencarian', method: 'Metode', severity: 'Severity', risk: 'Risiko', review: 'Status' };
  return <>
    <Link className="back-link" href={result ? `/projects/${result.project_id}` : '/projects'}>← {result?.project.name || 'Proyek'}</Link>
    <PageHead eyebrow="ANALISIS SAMPEL PENELITIAN" title="Hasil pemindaian" description={result ? `${result.filename} · ${date(result.created_at)}` : 'Memuat snapshot…'} action={result && <div className="action-group"><a className="button secondary" href={`${API}/scans/${id}/export?format=json`}>JSON ↓</a><a className="button secondary" href={`${API}/scans/${id}/export?format=csv`}>CSV ↓</a><Link className="button" href={`/scans/${id}/report`}>Laporan ↗</Link></div>} />
    {scan.error && <ErrorBox message={scan.error} retry={scan.reload} />}{scan.loading && <Loading />}
    {result && <>
      <div className="scan-status-line"><Badge value={result.status} /><a className="text-link jump-to-findings" href="#findings">Langsung ke temuan ↓</a></div>
      <ol className="scan-stages" aria-label="Tahapan pemindaian">{['sast', 'sca'].map((method, index) => <li key={method} data-status={result.methods[method].status}><span className="stage-number">{result.methods[method].status === 'completed' ? '✓' : index + 1}</span><span><strong>{method === 'sast' ? 'Pemeriksaan kode' : 'Pemeriksaan dependensi'}</strong><small>{method.toUpperCase()} · {labels[result.methods[method].status]}</small></span></li>)}</ol>
      {result.status === 'queued' && <div className="notice">Menunggu worker memulai pemindaian.</div>}
      {result.status === 'running' && <div className="notice" role="status">Pemindaian berjalan. Status diperbarui otomatis.</div>}
      {['failed', 'partial', 'unsupported'].includes(result.status) && <div className="notice warning">{result.status === 'partial' ? 'Hasil hanya mencakup metode yang berhasil.' : result.status === 'failed' ? 'Pemindaian gagal; jumlah temuan bukan hasil pemeriksaan keamanan yang lengkap.' : 'Snapshot tidak memiliki cakupan yang didukung.'} Lihat status setiap metode di bawah.</div>}
      {result.error && <ErrorBox message={result.error} />}

      <Stats items={[{ label: 'Total temuan', value: result.summary.total, note: 'Dari metode yang berhasil' }, { label: 'Critical & High', value: result.summary.severity.critical + result.summary.severity.high, note: 'Severity alat, bukan skor risiko' }, { label: result.summary.risk_analysis ? 'Estimasi risiko tertinggi' : 'Risiko R1 historis', value: riskLabels[result.summary.risk_analysis ? result.summary.risk_analysis.highest : result.summary.highest_risk], note: result.summary.risk_analysis ? 'RA1 bersyarat; bukan risiko total proyek' : 'Penilaian R1 historis' }, { label: 'Bukti belum memadai', value: result.summary.reviews.investigate, note: 'Hasil akhir penyaringan otomatis' }]} />
      <p className="muted">Risiko dianalisis otomatis melalui skenario, aset, kemungkinan, dan dampak. Estimasi bersyarat RA1 dipisahkan dari severity alat serta prioritas teknis A1.</p>
      <section id="findings" className="card activity findings-section" aria-busy={Boolean(searching)}><div className="card-header"><div><h2>Daftar temuan</h2><p className="muted">Pilih temuan untuk membaca bukti dan hasil otomatis.</p></div><span className="muted" role="status">{searching ? 'Memperbarui hasil…' : `${findings.result?.meta.total ?? 0} hasil`}</span></div><div className="quick-filters" aria-label="Pintasan filter"><button aria-pressed={filters.severity === 'critical'} onClick={() => filter('severity', filters.severity === 'critical' ? '' : 'critical')}>Critical · {result.summary.severity.critical}</button><button aria-pressed={filters.severity === 'high'} onClick={() => filter('severity', filters.severity === 'high' ? '' : 'high')}>High · {result.summary.severity.high}</button><button aria-pressed={filters.review === 'investigate'} onClick={() => filter('review', filters.review === 'investigate' ? '' : 'investigate')}>Bukti belum cukup · {result.summary.reviews.investigate}</button>{Object.values(filters).some(Boolean) && <button className="reset-filters" onClick={() => { setFilters({ q: '', method: '', severity: '', risk: '', review: '' }); setPage(1); }}>Hapus semua filter</button>}</div><div className="compact-filters"><label className="search"><span>Cari kerentanan</span><input type="search" placeholder="Cari nama kerentanan, lokasi, paket, atau ID…" maxLength={200} value={filters.q} onChange={event => filter('q', event.target.value)} /></label><details className="filter-disclosure"><summary>Filter lainnya{Object.entries(filters).filter(([k, v]) => k !== 'q' && v).length > 0 && ' · Aktif'}</summary><div className="filter-options">{[
        ['method', 'Semua metode', [['sast', 'SAST'], ['sca', 'SCA']]],
        ['severity', 'Semua severity', ['critical', 'high', 'medium', 'low', 'unknown'].map(value => [value, value.toUpperCase()])],
        ['risk', 'Semua risiko', Object.entries(riskLabels)],
        ['review', 'Semua peninjauan', [['unreviewed', 'Belum ditinjau'], ['confirmed', 'Terkonfirmasi'], ['false_positive', 'Tidak sesuai'], ['investigate', 'Belum dapat dipastikan']]],
      ].map(([name, label, options]) => <label key={name}><span>{label}</span><select value={filters[name]} onChange={event => filter(name, event.target.value)}><option value="">{label}</option>{options.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></label>)}</div></details></div>
      {Object.values(filters).some(Boolean) && <div className="active-filters" aria-label="Filter aktif">{Object.entries(filters).filter(([, value]) => value).map(([name, value]) => <button type="button" key={name} onClick={() => filter(name, '')} aria-label={`Hapus filter ${filterNames[name]}`}><span>{filterNames[name]}: {name === 'risk' ? riskLabels[value] : labels[value] || value.toUpperCase()}</span><span aria-hidden="true">×</span></button>)}</div>}
      {findings.error && <ErrorBox message={findings.error} retry={findings.reload} />}{findings.loading && <Loading />}{findings.result && <>{findings.result.data.length ? <FindingsTable scanId={id} findings={findings.result.data} /> : <Empty title={result.status === 'completed' ? 'Tidak ada temuan pada tampilan ini' : 'Belum ada temuan yang dapat ditampilkan'} description={result.status === 'completed' ? 'Periksa filter dan cakupan. Nol temuan tidak menjamin proyek bebas kerentanan.' : 'Hasil tersedia setelah metode pemindaian berhasil. Periksa status dan konfigurasi scanner.'} />}<div className="pagination"><span>{findings.result.meta.total ? `${(page - 1) * 25 + 1}–${Math.min(page * 25, findings.result.meta.total)} dari ${findings.result.meta.total} temuan` : '0 temuan'} · Halaman {page}</span><div><button className="button small secondary" disabled={page === 1 || Boolean(searching)} onClick={() => setPage(page - 1)}>Sebelumnya</button><button className="button small secondary" disabled={page * 25 >= findings.result.meta.total || Boolean(searching)} onClick={() => setPage(page + 1)}>Berikutnya</button></div></div></>}</section>
      <details className="card compact-details"><summary>Distribusi hasil</summary><ResultDistribution summary={result.summary} /></details>
      <div className="method-grid">{['sast', 'sca'].map(method => <section className="card method-card" key={method}><div className="section-heading"><div><div className="card-eyebrow">{method.toUpperCase()}</div><h2>{method === 'sast' ? 'Analisis kode sumber' : 'Analisis dependensi'}</h2></div><Badge value={result.methods[method].status} /></div><p>Temuan mentah: {result.methods[method].raw_finding_count ?? 'Tidak tercatat (data lama)'} · Unik: {result.methods[method].unique_finding_count ?? result.summary.methods[method]}</p><p>Temuan tersimpan: {result.summary.methods[method]}</p><p className="muted">{method === 'sast' ? `${result.coverage.source_files} berkas JavaScript/TypeScript pada snapshot` : `${result.coverage.lockfiles.length} lockfile npm pada snapshot`}</p>{result.methods[method].error && <p className="method-error">{result.methods[method].error}</p>}{result.methods[method].version && <small className="mono">{result.methods[method].version} · {result.methods[method].duration_seconds ?? '—'} detik</small>}</section>)}</div>
      {result.status === 'completed' && <details className="card compact-details"><summary>Tetapkan sebagai pemeriksaan utama penelitian</summary><p>Bekukan versi setelah dokumentasi dan cakupannya diperiksa. Rekap memakai pemeriksaan lengkap pertama dengan konfigurasi yang sama.</p>{freezeError && <ErrorBox message={freezeError} />}{(frozen || result.main_scan_id) ? <p role="status">Pemeriksaan utama: {frozen || result.main_scan_id}</p> : <div><label>Catatan pemeriksaan cakupan dan konfigurasi<textarea value={coverageReview} maxLength={4000} onChange={e => setCoverageReview(e.target.value)} placeholder="Catat hasil penelaahan entri dilewati, akar proyek, aturan, dan dokumentasi pembuatan sebelum pembekuan." /></label><button className="button secondary" disabled={!coverageReview.trim() || freezing} onClick={freeze}>{freezing ? 'Menyimpan pemeriksaan utama…' : 'Bekukan versi sebagai sampel utama'}</button></div>}</details>}
      <details className="card coverage"><summary>Cakupan & keterlacakan snapshot</summary><dl className="detail-list"><dt>SHA-256 arsip</dt><dd className="mono">{result.sha256}</dd><dt>Waktu mulai</dt><dd>{date(result.started_at)}</dd><dt>Waktu selesai</dt><dd>{date(result.finished_at)}</dd><dt>Bahasa ditemukan</dt><dd>{result.coverage.languages.join(', ') || 'Tidak ada yang didukung'}</dd><dt>Lockfile</dt><dd>{result.coverage.lockfiles.join(', ') || 'Tidak tersedia'}</dd><dt>Berkas diekstrak</dt><dd>{result.coverage.total_files}</dd><dt>Entri dilewati</dt><dd>{result.coverage.skipped.length}</dd></dl>{result.coverage.skipped.length > 0 && <details><summary>Daftar entri yang dilewati</summary><pre>{result.coverage.skipped.join('\n')}</pre></details>}<details><summary>Metadata scanner</summary><pre>{JSON.stringify(result.methods, null, 2)}</pre></details></details>
    </>}
  </>;
}
