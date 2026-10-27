'use client';
import { Badge, date } from './ui';

export function ScenarioList({ scenarios = [] }) {
  return scenarios.map((s, i) => <div className="card detail-card" key={s.id || i}><h3>Skenario {i + 1} · R1</h3><p>{s.scenario}</p><p><strong>Aset:</strong> {s.asset}</p><p><strong>Bukti:</strong> {s.evidence || 'Belum memadai'}</p><p>K: {s.likelihood ?? '—'} · C: {s.confidentiality ?? 'N/A'} · I: {s.integrity ?? 'N/A'} · A: {s.availability ?? 'N/A'} · D: {s.impact ?? '—'} · Skor: {s.score ?? 'Belum dapat dinilai'}</p><p>{s.reason}</p>{s.uncertainty && <p className="notice warning">{s.uncertainty}</p>}</div>);
}
export function ProjectRisk({ assessment }) {
  if (!assessment) return <p className="muted">Analisis risiko proyek belum tersedia pada pemeriksaan ini.</p>;
  return <section className="card detail-card project-risk"><h3>Analisis risiko proyek</h3>
    <p><strong>{assessment.status === 'estimated' ? `Estimasi risiko bersyarat: ${assessment.score} / 9` : 'Risiko belum dapat diberi skor'}</strong></p>
    <p>{assessment.reason}</p><p className="notice">{assessment.limitations}</p>
    <p className="muted">Skor risiko = kemungkinan × dampak. Rendah: 1–2 · Sedang: 3–4 · Tinggi: 6–9. Aturan penilaian versi RA1.</p>
    {assessment.scenarios.map((s, i) => <details key={i}><summary>Skenario {i + 1} · {s.scope === 'development' ? 'Pengembangan / build' : 'Runtime aplikasi'} · skor {s.score}</summary>
      <p>{s.scenario}</p><p><strong>Aset yang dimodelkan:</strong> {s.asset}</p>
      <p>Kemungkinan ({s.likelihood}) × dampak ({s.impact}) = skor {s.score}</p><p>Kerahasiaan: {s.confidentiality} · Integritas: {s.integrity} · Ketersediaan: {s.availability}. Nilai 0 berarti tidak ada dampak pada aspek tersebut menurut advisory.</p><p>{s.reason}</p>
      <p><strong>Bukti yang diamati:</strong></p><ul>{s.evidence.map((e, n) => <li key={n}><code>{e.lockfile}</code> · <code>{e.dependency_path}</code> · {e.scope === 'development' ? 'Dipakai untuk pengembangan / build' : 'Dependensi runtime aplikasi'}<small className="mono">Sidik berkas (SHA-256): {e.sha256}</small></li>)}</ul>
      <p><strong>Asumsi yang belum dibuktikan:</strong></p><ul>{s.assumptions.map(a => <li key={a}>{a}</li>)}</ul><code>{s.vector}</code>
    </details>)}
    {!assessment.scenarios.length && <p>{assessment.context?.reason || 'Konteks snapshot belum tersedia.'}</p>}
  </section>;
}
export default function ResearchReview({ finding }) {
  const result = finding.automatic;
  return <><div className="notice">Analisis otomatis: status temuan, estimasi risiko proyek bersyarat, dan rekomendasi. Bukti yang diamati dipisahkan dari asumsi skenario.</div>
    <p><strong>Cara membaca:</strong> periksa bukti → lihat status → baca skenario risiko dan asumsi → tentukan tindak lanjut.</p>
    <p><strong>Status:</strong> <Badge value={finding.review_status} /></p>
    <p>{finding.review_reason || 'Hasil otomatis tersedia setelah kedua pemindai selesai.'}</p>
    <ProjectRisk assessment={result?.project_risk} />
    <details><summary>Rincian prioritas teknis dari advisory (A1)</summary>{result?.priority ? <section className="card detail-card"><h3>Prioritas teknis otomatis · A1</h3><p>Skor {result.priority.score} / 9 · indikator akses {result.priority.likelihood} × dampak teknis {result.priority.impact}</p><p>{result.priority.basis}</p><code>{result.priority.vector}</code></section> : <p className="muted">Skor teknis tidak tersedia: bukti atau vektor CVSS v3 lengkap belum tersedia. Proses otomatis tetap selesai.</p>}</details>
    {!result?.project_risk && <p>{finding.risk_reason}</p>}<p><strong>Rekomendasi:</strong> {result?.recommendation || 'Lihat rekomendasi pemindai.'}</p>
    <details><summary>Riwayat keputusan ({finding.history?.length || 0})</summary>{finding.history?.map(h => <section className="detail-card" key={h.id}><p>{date(h.created_at)} <Badge value={h.decision.review_status} /> · {h.decision.engine || 'Manual / historis'}</p><p>{h.decision.review_reason}</p><p>{h.decision.risk_reason}</p><p>{h.decision.recommendation}</p><ScenarioList scenarios={h.scenarios} /></section>)}</details>
  </>;
}
