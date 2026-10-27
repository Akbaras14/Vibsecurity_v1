'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useResource } from '../components/api';
import { Badge, date, Empty, ErrorBox, Loading, PageHead, groupLabels } from '../components/ui';

export default function Projects() {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const data = useResource(`/projects?q=${encodeURIComponent(query)}&page=${page}`);
  return <><PageHead eyebrow="PROJECT LIBRARY" title="Proyek Anda" description="Kelola snapshot dan riwayat analisis setiap proyek dalam satu tempat." action={<Link className="button" href="/projects/new">＋ Tambah proyek</Link>} />
    <section className="card"><div className="card-header"><h2>Daftar proyek</h2><label className="search"><span className="sr-only">Cari nama proyek</span><input type="search" value={query} onChange={event => { setQuery(event.target.value); setPage(1); }} placeholder="Cari nama proyek…" /></label></div>{data.error && <ErrorBox message={data.error} retry={data.reload} />}{data.loading && <Loading />}{data.result && <>{data.result.data.length ? <div className="table-scroll"><table><thead><tr><th>Nama proyek</th><th>Kelompok sampel</th><th>Teknologi</th><th>Scan</th><th>Status terbaru</th><th>Dibuat</th></tr></thead><tbody>{data.result.data.map(project => <tr key={project.id}><td><Link className="project-name" href={`/projects/${project.id}`}>{project.name}</Link><small>{project.sample_code || 'Tanpa kode sampel'}{project.deleting ? ' · Pembersihan tertunda' : ''}</small></td><td>{groupLabels[project.sample_group] || 'Belum dikelompokkan'}</td><td>{project.technology || 'Belum dicatat'}</td><td>{project.scan_count}</td><td>{project.latest_status ? <Badge value={project.latest_status} /> : <span className="muted">Belum dipindai</span>}</td><td>{date(project.created_at)}</td></tr>)}</tbody></table></div> : <Empty title={query ? 'Proyek tidak ditemukan' : 'Workspace masih kosong'} description={query ? 'Coba kata kunci nama proyek lain.' : 'Buat proyek pertama untuk memulai analisis keamanan.'} action={!query && <Link className="button secondary" href="/projects/new">Tambah proyek</Link>} />}
    <div className="pagination"><span>{data.result.meta.total} proyek · Halaman {page}</span><div><button className="button small secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>Sebelumnya</button><button className="button small secondary" disabled={page * 25 >= data.result.meta.total} onClick={() => setPage(page + 1)}>Berikutnya</button></div></div></>}</section></>;
}
