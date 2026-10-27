'use client';

import Link from 'next/link';
import { useResource } from '../components/api';
import { Badge, Empty, ErrorBox, Loading, PageHead, ResultDistribution, ScanTable, Stats } from '../components/ui';

export default function Dashboard() {
  const data = useResource('/dashboard', 10000);
  const result = data.result?.data;
  return <>
    <PageHead eyebrow="VIBESEC / RUANG PENELITIAN" title="Ringkasan keamanan" description="Unggah proyek, lalu terima hasil analisis otomatis." action={<Link className="button" href="/projects/new">＋ Tambah proyek</Link>} />
    {data.error && <ErrorBox message={data.error} retry={data.reload} />}
    {data.loading && <Loading />}
    {result && <>

      <Stats items={[{ label: 'Total proyek', value: result.projects, note: 'Dalam workspace ini' }, { label: 'Scan aktif', value: result.active_scans, note: 'Antre & sedang berjalan' }, { label: 'Temuan terdeteksi', value: result.summary.total, note: 'Scan terbaru setiap proyek' }, { label: 'Critical & High', value: result.summary.severity.critical + result.summary.severity.high, note: 'Severity dari alat pemindai' }]} />
      <section className="card activity"><div className="card-header"><div><div className="card-eyebrow">SCAN ACTIVITY</div><h2>Aktivitas terbaru</h2></div><Link className="text-link" href="/projects">Semua proyek ↗</Link></div>{result.recent.length ? <ScanTable scans={result.recent} projectColumn /> : <Empty title="Belum ada pemindaian" description="Tambahkan proyek pertama, lalu unggah kode sumber dalam format ZIP." action={<Link className="button secondary" href="/projects/new">Tambahkan proyek pertama</Link>} />}</section>
      <details className="card compact-details"><summary>Rekap penelitian</summary><div className="disclosure-body">      <section className="card research-overview"><div className="card-header"><div><div className="section-kicker">BATAS SAMPEL DALAM BAB 1</div><h2>Rancangan 12 sampel penelitian</h2><p className="muted">Empat proyek per kelompok; rekap memakai pemeriksaan utama yang telah dibekukan.</p></div><span className="engine-tag">Next.js · TypeScript · npm</span></div><div className="table-scroll"><table><thead><tr><th>Kelompok aplikasi</th><th>Target</th><th>Tercatat</th><th>Pemeriksaan utama</th><th>SAST unik</th><th>SCA unik</th><th>Terkonfirmasi</th><th>Estimasi risiko tinggi</th><th>Belum dinilai</th></tr></thead><tbody>{result.research_groups?.map(group => <tr key={group.key}><td><strong>{group.label}</strong></td><td>{group.target} proyek</td><td>{group.registered}</td><td>{group.scanned}</td><td>{group.summary.methods.sast}</td><td>{group.summary.methods.sca}</td><td>{group.summary.reviews.confirmed} temuan</td><td>{(group.summary.risk_analysis?.categories.high ?? group.summary.risks.high)}</td><td>{(group.summary.risk_analysis?.categories.unassessed ?? group.summary.risks.unassessed)}</td></tr>)}</tbody></table></div><p className="research-boundary">Analisis deskriptif pada sampel penelitian; tidak digunakan untuk menyimpulkan keamanan seluruh proyek hasil vibe coding.</p></section>      <section className="card detail-card"><h2>Status scan terbaru per proyek</h2><div className="action-group">{Object.entries(result.scans).map(([status, count]) => <span key={status}><Badge value={status} /> {count}</span>)}<span>Belum dipindai: {result.unscanned_projects}</span></div><p className="muted">Setiap proyek dihitung satu kali. Hasil gagal, parsial, dan tidak didukung perlu dibaca sesuai cakupannya.</p></section>
      <section><h2>Distribusi pemeriksaan utama penelitian</h2><ResultDistribution summary={result.research_summary} /></section>
</div></details>
      <details className="card compact-details"><summary>Cara kerja VibeSec dalam 5 langkah</summary>
        <ol><li><strong>Unggah proyek:</strong> simpan salinan kode ZIP yang akan diperiksa.</li><li><strong>Periksa kode dan paket:</strong> Semgrep mencari pola berisiko pada kode (SAST); OSV-Scanner mencocokkan versi paket dengan catatan kerentanan (SCA).</li><li><strong>Rapikan temuan:</strong> gabungkan duplikasi, simpan bukti, dan terjemahkan uraian ke bahasa Indonesia.</li><li><strong>Analisis risiko:</strong> susun skenario, aset, kemungkinan, dan dampak jika bukti memadai. Asumsi ditampilkan; bukti tidak cukup berarti tanpa skor.</li><li><strong>Baca laporan:</strong> telusuri hasil dari ringkasan hingga lokasi kode atau paket dan alasan penilaiannya.</li></ol>
        <p><strong>Tiga hal yang berbeda:</strong> severity adalah keparahan dari alat, status menjelaskan kepastian bukti, dan risiko adalah estimasi bersyarat pada skenario penggunaan.</p>
        <p className="muted">Proyek tidak dijalankan untuk mencoba serangan. Nol temuan tidak menjamin keamanan; kecocokan paket tidak membuktikan eksploitasi.</p>
      </details>
    </>}
  </>;
}
