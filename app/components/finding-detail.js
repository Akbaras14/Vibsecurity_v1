'use client';

import ResearchReview from './research-review';
import CopyButton from './copy-button';
import { findingText } from './finding-language.mjs';
import { Badge, date, riskLabels } from './ui';

export function References({ values }) {
  const links = (Array.isArray(values) ? values : []).filter(value => typeof value === 'string' && /^https?:\/\//i.test(value));
  return links.length ? <ul className="references">{links.map((value, index) => <li key={`${value}-${index}`}><a href={value} target="_blank" rel="noopener noreferrer">{value} ↗</a></li>)}</ul> : <p className="muted">Referensi tidak tersedia dari pemindai.</p>;
}

export function CvssDetails({ finding }) {
  const rows = Array.isArray(finding.cvss)
    ? finding.cvss.map((value, index) => ({ source: value.type || `Sumber ${index + 1}`, score: null, vector: value.score }))
    : Object.entries(finding.cvss || {}).map(([source, value]) => ({ source, score: value.V3Score ?? value.V2Score, vector: value.V3Vector || value.V2Vector }));
  return rows.length ? <>{finding.cvss_score != null && <p>Skor CVSS maksimum kelompok advisory: <strong>{finding.cvss_score}</strong></p>}<div className="table-scroll cvss-table"><table><thead><tr><th>Sumber / standar</th><th>Skor dari sumber</th><th>Vektor dari advisory</th></tr></thead><tbody>{rows.map((row, index) => <tr key={index}><td>{row.source}</td><td>{row.score ?? (finding.cvss_score != null ? 'Lihat skor kelompok' : 'Tidak tersedia')}</td><td><code>{row.vector || 'Tidak tersedia'}</code></td></tr>)}</tbody></table></div></> : <p className="muted">Skor CVSS tidak tersedia dari sumber.</p>;
}

export default function FindingDetail({ finding, scanId, reload }) {
  const text = findingText(finding);
  const dependency = finding.method === 'sca';
  const snippet = finding.snippet === 'requires login' ? null : finding.snippet;
  return <>
    <div className="finding-meta"><Badge value={finding.severity} /><span className="engine-tag">{finding.method.toUpperCase()}</span><Badge value={finding.review_status} /><span className="muted">ID sumber: <code>{finding.source_id}</code></span></div>

    <div className="finding-layout"><div className="finding-main">
      <section id="evidence" className="card detail-card finding-section"><div className="section-kicker">01 / PAHAMI TEMUAN</div><h2>Bukti dan lokasi kerentanan</h2>
        {text.translated && <p className="muted">{text.automatic ? 'Diterjemahkan otomatis ke bahasa Indonesia. Teks asli dan bukti kode tetap tersedia.' : 'Penjelasan ringkas bahasa Indonesia berdasarkan advisory. Uraian lengkap dari sumber tetap tersedia di bawah.'}</p>}
        {finding.translation?.status === 'failed' && <p className="notice">Terjemahan otomatis belum tersedia. Teks sumber ditampilkan agar bukti tetap dapat dibaca.</p>}
        <p className="finding-description" lang={text.translated ? 'id' : undefined}>{text.description}</p>
        {text.translated && <details><summary>Lihat teks asli dari pemindai</summary><p className="finding-description" lang="en">{finding.description || finding.title}</p></details>}
        <div className="evidence-location"><span>{dependency ? 'Dependensi yang terdeteksi' : 'Lokasi kode yang perlu diperiksa'}</span>{dependency && <strong>{finding.package} <code>@{finding.installed_version}</code></strong>}<code>{finding.path}{finding.line ? `:${finding.line}` : ''}</code><div className="evidence-actions"><CopyButton value={`${finding.path}${finding.line ? `:${finding.line}` : ''}`} label="Salin lokasi" /><CopyButton value={`${finding.source_id}\n${finding.path}${finding.line ? `:${finding.line}` : ''}\n${text.title}\n${text.description}`} label="Salin ringkasan bukti" />{snippet && <CopyButton value={snippet} label="Salin kode" />}</div></div>
        {snippet && <div className="source-evidence"><div className="source-toolbar"><span>{finding.snippet_source === 'snapshot' ? 'Cuplikan kode pada snapshot' : 'Cuplikan dari pemindai'}</span><span>{finding.line ? `Mulai baris ${finding.line}` : 'Baris tidak tersedia'}</span></div><pre className="code-block"><code>{snippet.split('\n').map((line, index) => <span className="code-line" key={index}><span className="line-number" aria-hidden="true">{finding.line ? finding.line + index : '·'}</span><span>{line || ' '}</span></span>)}</code></pre></div>}
        {!snippet && !dependency && <p className="muted">Cuplikan tidak disediakan pemindai. Periksa berkas asli pada lokasi di atas.</p>}
        <dl className="detail-list"><dt>Jenis kelemahan (CWE)</dt><dd>{Array.isArray(finding.cwe) ? finding.cwe.join(', ') || 'Tidak tersedia' : finding.cwe || 'Tidak tersedia'}</dd><dt>Tingkat keparahan asli</dt><dd>{finding.severity_original || 'Tidak tersedia'}</dd>{finding.aliases?.length > 0 && <><dt>ID advisory terkait</dt><dd className="mono">{finding.aliases.join(' · ')}</dd></>}</dl>
        {dependency && <p className="notice">SCA menemukan kecocokan versi paket dengan advisory. Temuan ini belum membuktikan bahwa fungsi rentan digunakan atau dapat dieksploitasi pada aplikasi.</p>}
      </section>
      <details id="remediation" className="card detail-card finding-section compact-details"><summary>Rekomendasi dan langkah pemeriksaan</summary>
        {dependency && <div className="version-comparison"><div><span>Versi terpasang</span><strong>{finding.installed_version || 'Tidak tersedia'}</strong></div><span aria-hidden="true">→</span><div><span>Versi perbaikan di advisory</span><strong>{finding.fixed_version || 'Belum tersedia'}</strong></div></div>}
        <p>{finding.remediation || (finding.fixed_version ? `Tinjau pembaruan ke versi perbaikan yang tercantum (${finding.fixed_version}), lalu periksa kompatibilitas aplikasi.` : 'Pemindai tidak menyediakan saran khusus. Gunakan bukti dan referensi untuk menentukan penanganan.')}</p>
        <ol className="reading-steps"><li>{dependency ? 'Periksa advisory dan penggunaan paket dalam proyek.' : 'Periksa alur input dan penggunaan kode pada lokasi temuan.'}</li><li>Sistem mencocokkan bukti yang tersedia dan mencatat keterbatasannya.</li><li>Prioritas teknis dihitung otomatis jika vektor CVSS v3 lengkap tersedia.</li></ol>
      </details>
      <section id="review" className="card form-card finding-section"><div className="section-kicker">03 / HASIL OTOMATIS</div><div className="section-heading"><h2>Hasil analisis otomatis</h2><span className="muted">Disimpan: {date(finding.reviewed_at)}</span></div><p className="muted">Status dan rekomendasi disusun otomatis setelah pemindaian. Kekurangan bukti dicatat sebagai ketidakpastian.</p>
        <ResearchReview finding={finding} scanId={scanId} reload={reload} />
      </section>
      <details id="references" className="card detail-card finding-section compact-details"><summary>Referensi dan advisory</summary><References values={finding.references} />{dependency && <><h3>CVSS dari sumber advisory</h3><p className="muted">Sumber severity: {finding.severity_source || 'Tidak tersedia'}. CVSS merupakan keparahan teknis, bukan hasil penilaian risiko proyek.</p><CvssDetails finding={finding} /></>}</details>
    </div><aside className="finding-aside"><section className="card reading-guide"><div className="section-kicker">PANDUAN MEMBACA</div><h2>Panduan penilaian</h2><div className="reading-measure"><span>Severity pemindai</span><Badge value={finding.severity} /><p>Keparahan teknis dari aturan atau advisory.</p></div><div className="reading-measure"><span>{finding.automatic?.project_risk ? 'Estimasi risiko proyek RA1' : 'Risiko R1 historis'}</span><strong>{riskLabels[finding.automatic?.project_risk?.category || finding.risk]}</strong><p>Estimasi risiko inheren bersyarat memakai scope dependensi dan advisory. Asumsi penggunaan belum membuktikan eksploitasi.</p></div><hr /><h3>Alur peninjauan</h3><p>Unggah → pindai → penyaringan otomatis → laporan.</p><p className="muted">Analisis bersifat deskriptif terhadap sampel. Temuan otomatis bukan pembuktian eksploitasi.</p></section></aside></div>
  </>;
}
