import { findingText } from './finding-language.mjs';
import Link from 'next/link';

export const labels = {
  queued: 'Antre', running: 'Berjalan', completed: 'Selesai', partial: 'Parsial', failed: 'Gagal', unsupported: 'Tidak didukung',
  critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low', unknown: 'Unknown',
  unreviewed: 'Belum ditinjau', confirmed: 'Terkonfirmasi', false_positive: 'Tidak sesuai', investigate: 'Belum dapat dipastikan',
};
export const groupLabels = { todo: 'To-do list', chatbot: 'Chatbot sederhana', catalog: 'Katalog / pemesanan sederhana' };
export const riskLabels = { high: 'Tinggi', medium: 'Sedang', low: 'Rendah', unassessed: 'Belum dinilai' };
export function Badge({ value, children }) { return <span className={`badge badge-${value}`}>{children || labels[value] || value}</span>; }
export function date(value) { return value ? new Date(value).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' }) : 'Tidak tersedia'; }
export function PageHead({ eyebrow, title, description, action }) {
  return <div className="page-head"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</div>;
}
export function ErrorBox({ message, retry }) { return <div className="notice error" role="alert"><div>{message}</div>{retry && <button className="button small secondary" onClick={retry}>Coba lagi</button>}</div>; }
export function Loading() { return <div className="loading" role="status"><span className="loading-dot" />Memuat data workspace…</div>; }
export function Empty({ title, description, action }) {
  return <div className="empty"><div className="empty-icon">＋</div><h3>{title}</h3><p>{description}</p>{action}</div>;
}
export function Stats({ items }) { return <div className="stats">{items.map(item => <div className="stat" key={item.label}><span>{item.label}</span><strong>{item.value}</strong><small>{item.note}</small></div>)}</div>; }
export function ResultDistribution({ summary }) {
  return <section className="card detail-card"><h2>Distribusi hasil</h2><div className="report-distribution"><div><h3>Severity dari pemindai</h3>{Object.entries(summary.severity).map(([key, count]) => <p key={key}><Badge value={key} /><strong>{count}</strong></p>)}</div><div><h3>Status analisis</h3>{Object.entries(summary.reviews).map(([key, count]) => <p key={key}><Badge value={key} /><strong>{count}</strong></p>)}</div><div><h3>{summary.risk_analysis ? 'Estimasi risiko proyek' : 'Risiko R1 historis'}</h3>{Object.entries(summary.risk_analysis ? summary.risk_analysis.categories : summary.risks).map(([key, count]) => <p key={key}><span>{riskLabels[key]}</span><strong>{count}</strong></p>)}</div></div><p className="muted">{summary.risk_analysis ? 'Risiko merupakan estimasi bersyarat berdasarkan konteks dependensi dan catatan kerentanan; asumsi dapat diperiksa pada setiap skenario. ' : summary.highest_risk === 'unassessed' ? 'Risiko belum dinilai.' : `Risiko tertinggi: ${riskLabels[summary.highest_risk]}.`}{summary.provisional && ' Sementara: ada temuan terkonfirmasi yang belum dinilai.'} Hanya temuan terkonfirmasi dengan bukti memadai yang dinilai risikonya.</p></section>;
}
export function ScanTable({ scans, projectColumn = false }) {
  return <div className="table-scroll"><table><thead><tr><th>{projectColumn ? 'Proyek' : 'Snapshot'}</th><th>Status</th><th>Metode</th><th>Waktu unggah</th><th><span className="sr-only">Aksi</span></th></tr></thead>
    <tbody>{scans.map(scan => <tr key={scan.id}><td><strong>{projectColumn ? scan.project_name : scan.filename}</strong><small className="mono">{scan.id.slice(0, 12)}</small></td><td><Badge value={scan.status} /></td><td><div className="method-label">SAST <Badge value={scan.methods.sast.status} /></div><div className="method-label">SCA <Badge value={scan.methods.sca.status} /></div></td><td>{date(scan.created_at)}</td><td><Link className="text-link" href={`/scans/${scan.id}`}>Lihat hasil ↗</Link></td></tr>)}</tbody></table></div>;
}
export function FindingsTable({ scanId, findings }) {
  return <div className="table-scroll findings-table"><table><thead><tr><th>Severity</th><th>Kerentanan & sumber</th><th>Lokasi / dependensi</th><th>Perbaikan tersedia</th><th>Status otomatis</th><th>Risiko proyek</th></tr></thead><tbody>{findings.map(finding => <tr key={finding.id}>
    <td data-label="Severity"><Badge value={finding.severity} /></td>
    <td data-label="Kerentanan" className="finding-title"><Link href={`/scans/${scanId}/findings/${finding.id}`}>{findingText(finding).title}</Link><small><span className="engine-tag">{finding.method.toUpperCase()}</span> <code>{finding.source_id}</code></small><Link className="text-link finding-open" href={`/scans/${scanId}/findings/${finding.id}`}>Baca bukti & langkah penanganan →</Link></td>
    <td data-label="Lokasi / dependensi" className="finding-location">{finding.package && <strong>{finding.package} <code>{finding.installed_version}</code></strong>}<code>{finding.path}</code>{finding.line && <small>Baris {finding.line}{finding.end_line > finding.line ? `–${finding.end_line}` : ''}</small>}</td>
    <td data-label="Perbaikan">{finding.fixed_version ? <><span>Versi perbaikan</span><code className="fixed-version">{finding.fixed_version}</code></> : finding.remediation ? <span>Lihat rekomendasi aturan</span> : <span className="muted">Belum tersedia dari sumber</span>}</td>
    <td data-label="Status"><Badge value={finding.review_status} />{finding.automatic && <small>AUTO1</small>}</td><td data-label="Risiko proyek">{finding.automatic?.project_risk ? <><strong>{riskLabels[finding.automatic.project_risk.category]}</strong><small>{finding.automatic.project_risk.score != null ? `${finding.automatic.project_risk.score} / 9 · RA1 bersyarat` : 'Bukti belum cukup'}</small></> : finding.automatic ? <><strong>{finding.automatic.priority ? `${finding.automatic.priority.score} / 9` : 'Tanpa skor'}</strong><small>Teknis A1</small></> : <><span className={`risk-text risk-${finding.risk}`}>{riskLabels[finding.risk]}</span><small>R1 historis</small></>}</td>
  </tr>)}</tbody></table></div>;
}
