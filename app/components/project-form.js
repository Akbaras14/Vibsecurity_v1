'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from './api';
import { ErrorBox, groupLabels } from './ui';

const fields = [{ name: 'name', label: 'Nama proyek', required: true, max: 100, placeholder: 'Contoh: Toko Online AI' },
  { name: 'sample_code', label: 'Kode sampel', max: 100, placeholder: 'Contoh: VC-001' },
  { name: 'technology', label: 'Teknologi', max: 200, placeholder: 'Next.js, TypeScript, npm' },
  { name: 'source', label: 'Sumber proyek', max: 500, placeholder: 'URL atau keterangan asal proyek' },
  { name: 'ai_tool', label: 'Alat AI', max: 100, placeholder: 'Opsional, jika diketahui' },
  { name: 'ai_model', label: 'Model AI', max: 100, placeholder: 'Opsional, jika diketahui' }];

export default function ProjectForm({ project, onSaved }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError(''); setSaved(false);
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const result = await api(project ? `/projects/${project.id}` : '/projects', { method: project ? 'PATCH' : 'POST', body: JSON.stringify(values) });
      if (project) { setSaved(true); onSaved?.(); } else router.push(`/projects/${result.data.id}`);
    } catch (error) { setError(error.message); } finally { setBusy(false); }
  }
  return <form onSubmit={submit} className="project-form">
    {error && <ErrorBox message={error} />}{saved && <div className="notice success" role="status">Metadata proyek tersimpan.</div>}
    <div className="form-grid">{fields.filter(field => ['name', 'technology'].includes(field.name)).map(field => <label key={field.name}>{field.label}{field.required && <span className="required"> *</span>}<input name={field.name} required={field.required} maxLength={field.max} defaultValue={project?.[field.name] || ''} placeholder={field.placeholder} /></label>)}
    <label className="full-width">Deskripsi<textarea name="description" rows={2} maxLength={2000} defaultValue={project?.description || ''} placeholder="Fungsi singkat aplikasi." /></label></div>
    <details className="compact-details"><summary>Data penelitian dan asal proyek (opsional)</summary><p className="muted">Lengkapi sebelum menetapkan sampel utama penelitian.</p><div className="form-grid"><label>Kelompok sampel<select name="sample_group" defaultValue={project?.sample_group || ''}><option value="">Belum dikelompokkan</option>{Object.entries(groupLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>{fields.filter(field => !['name', 'technology'].includes(field.name)).map(field => <label key={field.name}>{field.label}<input name={field.name} maxLength={field.max} defaultValue={project?.[field.name] || ''} placeholder={field.placeholder} /></label>)}
    <label>Tanggal pengembangan<input name="development_date" type="date" defaultValue={project?.development_date || ''} /></label><label className="full-width">Dokumentasi prompt dan proses vibe coding<textarea name="development_notes" rows={4} maxLength={4000} defaultValue={project?.development_notes || ''} placeholder="Catat prompt, alat/model, iterasi, perubahan manual, dan instruksi keamanan bila diketahui." /></label></div></details>
    <div className="form-actions"><p className="muted">* Wajib diisi. Informasi yang belum diketahui boleh dikosongkan.</p><button className="button" disabled={busy}>{busy ? 'Menyimpan…' : project ? 'Simpan perubahan' : 'Buat proyek'}</button></div>
  </form>;
}
