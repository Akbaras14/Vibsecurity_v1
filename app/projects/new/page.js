import Link from 'next/link';
import ProjectForm from '../../components/project-form';
import { PageHead } from '../../components/ui';

export default function NewProject() {
  return <><Link className="back-link" href="/projects">← Daftar proyek</Link><PageHead eyebrow="PROYEK BARU" title="Buat proyek" description="Isi informasi dasar, lalu unggah ZIP untuk dipindai." /><section className="card form-card"><h2>Informasi proyek</h2><ProjectForm /></section></>;
}
