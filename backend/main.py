import csv
import hashlib
import io
import json
import logging
import shutil
import tempfile
import uuid
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config
from .archive import ArchiveError, inspect_zip
from .store import connect, finding_dict, initialize, now, query, scan_dict, summary
from .research import Scenario, findings as research_findings, history, select_scenario, main_scans, manifest_hash, matches

logger = logging.getLogger('vibesec')


class LocalGuard:
    """Reject foreign browser origins and bound bodies before multipart parsing."""

    def __init__(self, app, hosts, origins):
        self.app, self.hosts, self.origins = app, hosts, origins

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope['headers'])
        host = headers.get(b'host', b'').decode('latin1').split(':')[0].lower()
        origin = headers.get(b'origin', b'').decode('latin1')
        if host not in self.hosts or (origin and origin not in self.origins):
            return await JSONResponse({'error': {'code': 'forbidden_origin',
                'message': 'Host atau Origin tidak diizinkan.'}}, 403)(scope, receive, send)
        response_headers = {'Access-Control-Allow-Origin': origin, 'Vary': 'Origin'} if origin else {}
        limit = config.MAX_UPLOAD + 1024 * 1024 if scope['path'].endswith('/scans') else 64 * 1024
        if scope['path'].endswith('/review'):
            limit = 512 * 1024
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            length = limit + 1
        if length < 0 or length > limit:
            return await JSONResponse({'error': {'code': 'body_too_large',
                'message': 'Ukuran permintaan melampaui batas.'}}, 413, headers=response_headers)(scope, receive, send)
        with tempfile.SpooledTemporaryFile(max_size=1024 * 1024) as body:
            total = 0
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                chunk = message.get('body', b'')
                total += len(chunk)
                if total > limit:
                    return await JSONResponse({'error': {'code': 'body_too_large',
                        'message': 'Ukuran permintaan melampaui batas.'}}, 413, headers=response_headers)(scope, receive, send)
                body.write(chunk)
                if not message.get('more_body', False):
                    break
            body.seek(0)

            async def bounded_receive():
                data = body.read(64 * 1024)
                return {'type': 'http.request', 'body': data, 'more_body': body.tell() < total}

            await self.app(scope, bounded_receive, send)


class ProjectInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default='', max_length=2000)
    technology: str = Field(default='', max_length=200)
    source: str = Field(default='', max_length=500)
    sample_code: str = Field(default='', max_length=100)
    ai_tool: str = Field(default='', max_length=100)
    ai_model: str = Field(default='', max_length=100)
    development_date: date | None = None
    development_notes: str = Field(default='', max_length=4000)
    sample_group: Literal['', 'todo', 'chatbot', 'catalog'] = ''

    @field_validator('development_date', mode='before')
    @classmethod
    def empty_date(cls, value):
        return None if value == '' else value


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    review_status: Literal['unreviewed', 'confirmed', 'false_positive', 'investigate']
    review_reason: str = Field(min_length=1, max_length=4000)
    likelihood: int | None = Field(default=None, ge=1, le=3, strict=True)
    impact: int | None = Field(default=None, ge=1, le=3, strict=True)
    risk_reason: str = Field(default='', max_length=4000)
    scenarios: list[Scenario] = Field(default_factory=list, max_length=20)
    recommendation: str = Field(default='', max_length=4000)

    @model_validator(mode='after')
    def validate_risk(self):
        if self.likelihood is not None or self.impact is not None:
            raise ValueError('Gunakan skenario R1 dengan penilaian CIA; skor lama tetap tersedia pada riwayat.')
        if self.scenarios and self.review_status != 'confirmed':
            raise ValueError('Skenario risiko hanya untuk temuan terkonfirmasi.')
        if self.review_status == 'confirmed' and not self.scenarios and not self.risk_reason:
            raise ValueError('Catat alasan risiko belum dapat dinilai atau tambahkan skenario R1.')
        return self


class ProjectPatch(ProjectInput):
    name: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode='after')
    def reject_null_name(self):
        if 'name' in self.model_fields_set and self.name is None:
            raise ValueError('Nama proyek tidak boleh null.')
        return self


class CoverageReview(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    reason: str = Field(min_length=1, max_length=4000)


def create_app(root=config.STORAGE):
    root = root.resolve()

    @asynccontextmanager
    async def lifespan(app):
        initialize(root)
        yield

    app = FastAPI(title='VibeSec API', version='0.1.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(config.ORIGINS),
                       allow_methods=['GET', 'POST', 'PATCH', 'DELETE'],
                       allow_headers=['Content-Type'], expose_headers=['Content-Disposition'])
    app.add_middleware(LocalGuard, hosts=config.HOSTS, origins=config.ORIGINS)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, error):
        detail = error.detail if isinstance(error.detail, dict) else {
            'code': f'http_{error.status_code}', 'message': str(error.detail)}
        return JSONResponse({'error': detail}, status_code=error.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        fields = [{'field': '.'.join(map(str, item['loc'][1:])), 'message': item['msg']}
                  for item in error.errors()]
        return JSONResponse({'error': {'code': 'invalid_input',
            'message': 'Periksa kembali data yang diisi.', 'fields': fields}}, status_code=400)

    @app.exception_handler(Exception)
    async def internal_error(request, error):
        logger.error('API error: %s', type(error).__name__)
        return JSONResponse({'error': {'code': 'internal_error',
            'message': 'Terjadi kesalahan internal. Periksa layanan dan ruang penyimpanan.'}}, 500)

    def project_record(db, project_id, include_deleting=False, lock=False):
        row = query(db, 'SELECT * FROM projects WHERE id=%s' + (' FOR UPDATE' if lock else ''), (project_id,)).fetchone()
        if row is None:
            raise HTTPException(404, 'Proyek tidak ditemukan.')
        if row['deleting'] and not include_deleting:
            raise HTTPException(409, 'Pembersihan proyek belum selesai. Ulangi penghapusan.')
        return dict(row)

    def scan_record(db, scan_id):
        row = query(db, 'SELECT * FROM scans WHERE id=%s', (scan_id,)).fetchone()
        if row is None:
            raise HTTPException(404, 'Pemindaian tidak ditemukan.')
        project_record(db, row['project_id'])
        return scan_dict(row)

    def all_findings(db, scan_id):
        return research_findings(db, scan_id)

    @app.get('/api/health')
    def health():
        from .scanner import readiness
        with connect() as db:
            active = query(db, "SELECT COUNT(*) AS total FROM scans WHERE status IN ('queued','running')").fetchone()['total']
        return {'data': {'status': 'ok', 'scanner': readiness(), 'pending_scans': active}}

    @app.get('/api/dashboard')
    def dashboard():
        with connect() as db:
            projects = query(db, 'SELECT COUNT(*) AS total FROM projects WHERE deleting=0').fetchone()['total']
            latest = [scan_dict(row) for row in query(db, '''SELECT s.*, p.name AS project_name, p.sample_group
                FROM scans s JOIN projects p ON p.id=s.project_id WHERE p.deleting=0
                AND s.id=(SELECT id FROM scans WHERE project_id=p.id ORDER BY created_at DESC,id DESC LIMIT 1)
                ORDER BY s.created_at DESC,s.id DESC''')]
            findings_by_scan = {scan['id']: all_findings(db, scan['id']) for scan in latest}
            findings = [finding for items in findings_by_scan.values() for finding in items]
            primary = main_scans(db)
            groups = []
            for key, label in (('todo', 'To-do list'), ('chatbot', 'Chatbot sederhana'), ('catalog', 'Katalog / pemesanan')):
                registered = query(db, 'SELECT COUNT(*) AS total FROM projects WHERE deleting=0 AND sample_group=%s', (key,)).fetchone()['total']
                samples = [scan for scan in primary if scan['sample_group'] == key]
                groups.append({'key': key, 'label': label, 'target': 4, 'registered': registered,
                               'scanned': sum(scan['status'] == 'completed' for scan in samples),
                               'summary': summary([finding for scan in samples for finding in all_findings(db, scan['id'])])})
            counts = {status: sum(scan['status'] == status for scan in latest) for status in
                      ('queued', 'running', 'completed', 'partial', 'failed', 'unsupported')}
            active = query(db, "SELECT COUNT(*) AS total FROM scans WHERE status IN ('queued','running')").fetchone()['total']
            research_summary = summary([f for s in primary for f in all_findings(db, s['id'])])
        return {'data': {'projects': projects, 'scans': counts, 'summary': summary(findings),
                         'research_summary': research_summary,
                         'active_scans': active, 'unscanned_projects': projects - len(latest),
                         'recent': latest[:6], 'research_groups': groups, 'main_scan_ids': [s['id'] for s in primary]}}

    @app.get('/api/projects')
    def projects(q: str = Query('', max_length=100), page: int = Query(1, ge=1),
                 pageSize: int = Query(25, ge=1, le=100)):
        with connect() as db:
            pattern = '%' + q.replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%'
            total = query(db, "SELECT COUNT(*) AS total FROM projects WHERE name LIKE %s ESCAPE '!'", (pattern,)).fetchone()['total']
            rows = query(db, '''SELECT p.*, (SELECT status FROM scans WHERE project_id=p.id ORDER BY created_at DESC LIMIT 1) AS latest_status,
                (SELECT COUNT(*) FROM scans WHERE project_id=p.id) AS scan_count FROM projects p
                WHERE name LIKE %s ESCAPE '!' ORDER BY created_at DESC LIMIT %s OFFSET %s''',
                (pattern, pageSize, (page - 1) * pageSize)).fetchall()
        return {'data': [dict(row) for row in rows], 'meta': {'total': total, 'page': page, 'pageSize': pageSize}}

    @app.post('/api/projects', status_code=201)
    def create_project(payload: ProjectInput):
        data = payload.model_dump(mode='json')
        data.update(id=uuid.uuid4().hex, created_at=now(), updated_at=now())
        with connect() as db:
            fields = ','.join(data)
            query(db, f"INSERT INTO projects ({fields}) VALUES ({','.join('%s' for _ in data)})", tuple(data.values()))
        return {'data': data}

    @app.get('/api/projects/{project_id}')
    def project(project_id: str):
        with connect() as db:
            data = project_record(db, project_id)
            data['scans'] = [scan_dict(row) for row in query(db, 
                'SELECT * FROM scans WHERE project_id=%s ORDER BY created_at DESC,id DESC', (project_id,))]
            data['versions'] = [dict(row) for row in query(db, 'SELECT * FROM project_versions WHERE project_id=%s ORDER BY created_at', (project_id,)).fetchall()]
            data['main_scan_id'] = next((s['id'] for s in main_scans(db) if s['project_id'] == project_id), None)
            data['summary'] = summary(all_findings(db, data['scans'][0]['id']) if data['scans'] else [])
        return {'data': data}

    @app.patch('/api/projects/{project_id}')
    def update_project(project_id: str, payload: ProjectPatch):
        updates = payload.model_dump(mode='json', exclude_unset=True)
        updates['updated_at'] = now()
        with connect() as db:
            project_record(db, project_id, lock=True)
            if query(db, 'SELECT 1 FROM research_samples WHERE project_id=%s', (project_id,)).fetchone():
                raise HTTPException(409, 'Metadata sampel utama telah dibekukan.')
            query(db, f"UPDATE projects SET {','.join(f'{field}=%s' for field in updates)} WHERE id=%s",
                       (*updates.values(), project_id))
            data = project_record(db, project_id)
        return {'data': data}

    @app.post('/api/scans/{scan_id}/freeze')
    def freeze_sample(scan_id: str, payload: CoverageReview):
        with connect() as db:
            scan = scan_record(db, scan_id)
            project = project_record(db, scan['project_id'], lock=True)
            expected = {'todo': 'TD', 'chatbot': 'CB', 'catalog': 'KP'}.get(project['sample_group'])
            if not expected or project['sample_code'] not in [f'{expected}{n:02d}' for n in range(1, 5)]:
                raise HTTPException(400, 'Gunakan kode TD01–TD04, CB01–CB04, atau KP01–KP04 sesuai kelompok.')
            if not project['development_notes'] or project['ai_tool'].casefold() != 'chatgpt':
                raise HTTPException(400, 'Catat dokumentasi pembuatan melalui ChatGPT sebelum pembekuan.')
            if len(scan['coverage']['lockfiles']) != 1 or scan['coverage'].get('sast_reason'):
                raise HTTPException(400, 'Sampel utama memerlukan kode dan satu package-lock.json pada akar proyek.')
            if 'TypeScript' not in scan['coverage']['languages'] or not scan['coverage'].get('nextjs'):
                raise HTTPException(400, 'Sampel utama harus memuat TypeScript dan package.json dengan dependensi Next.js.')
            if scan['status'] != 'completed' or not scan['methods']['sast'].get('rules_manifest'):
                raise HTTPException(400, 'Jalankan pemeriksaan lengkap memakai aturan resmi dan manifest penelitian.')
            required = {'sast': ('tool', 'version', 'config_sha256', 'rules_sha256'),
                        'sca': ('tool', 'version', 'config_sha256', 'database_sha256')}
            if any(not scan['methods'].get(m, {}).get(k) for m, keys in required.items() for k in keys):
                raise HTTPException(400, 'Metadata konfigurasi belum lengkap; pindai ulang sebelum pembekuan.')
            manifest = {'rubric': 'R1', 'methods': {m: {k: scan['methods'][m][k] for k in keys} for m, keys in
                [('sast', ('tool', 'version', 'config_sha256', 'rules_sha256')),
                 ('sca', ('tool', 'version', 'config_sha256', 'database_sha256'))]}}
            if all(scan['methods'][m].get('assessment_policy') == 'AUTO1/A1/RA1/CTX1' for m in ('sast', 'sca')):
                manifest['rubric'] = 'RA1'
                for method in ('sast', 'sca'):
                    for key in ('assessment_policy', 'risk_policy_sha256'):
                        if not scan['methods'][method].get(key):
                            raise HTTPException(400, 'Identitas kebijakan risiko belum lengkap; pindai ulang sebelum pembekuan.')
                        manifest['methods'][method][key] = scan['methods'][method][key]
            protocol = query(db, 'SELECT * FROM research_protocol WHERE id=1 FOR UPDATE').fetchone()
            if protocol and json.loads(protocol['manifest']) != manifest:
                raise HTTPException(409, 'Konfigurasi berbeda dari seri penelitian yang dibekukan. Pindai ulang dengan konfigurasi yang sama.')
            if not protocol:
                query(db, 'INSERT INTO research_protocol(id,manifest,sha256,created_at) VALUES(1,%s,%s,%s)',
                      (json.dumps(manifest), manifest_hash(manifest), now()))
            if query(db, 'SELECT 1 FROM research_samples WHERE project_id=%s', (project['id'],)).fetchone():
                raise HTTPException(409, 'Versi sampel sudah dibekukan; pemeriksaan ulang tidak mengganti versi utama.')
            if query(db, 'SELECT 1 FROM research_samples r JOIN projects p ON p.id=r.project_id WHERE p.sample_code=%s',
                     (project['sample_code'],)).fetchone():
                raise HTTPException(409, 'Kode sampel sudah digunakan dalam penelitian.')
            query(db, 'INSERT INTO research_samples(project_id,version_id,protocol_id,coverage_review) VALUES(%s,%s,1,%s)',
                  (project['id'], scan['version_id'], payload.reason))
            primary = next(item for item in main_scans(db) if item['project_id'] == project['id'])
        return {'data': {'main_scan_id': primary['id'], 'manifest_sha256': manifest_hash(manifest)}}

    @app.delete('/api/projects/{project_id}')
    def delete_project(project_id: str):
        with connect() as db:
            project_record(db, project_id, include_deleting=True, lock=True)
            if query(db, "SELECT 1 FROM scans WHERE project_id=%s AND status IN ('queued','running')", (project_id,)).fetchone():
                raise HTTPException(409, 'Proyek masih memiliki scan antre/berjalan. Tunggu worker menyelesaikannya.')
            query(db, 'UPDATE projects SET deleting=1 WHERE id=%s', (project_id,))
            scan_ids = [row['id'] for row in query(db, 'SELECT id FROM scans WHERE project_id=%s', (project_id,))]
        try:
            for scan_id in scan_ids:
                directory = (root / 'scans' / scan_id).resolve()
                if directory.parent != (root / 'scans').resolve():
                    raise OSError('Invalid internal path')
                if directory.exists():
                    shutil.rmtree(directory)
        except OSError:
            raise HTTPException(500, 'Pembersihan file gagal. Proyek ditandai untuk dihapus; ulangi penghapusan.') from None
        with connect() as db:
            query(db, 'DELETE FROM research_samples WHERE project_id=%s', (project_id,))
            query(db, 'DELETE FROM scans WHERE project_id=%s', (project_id,))
            query(db, 'DELETE FROM project_versions WHERE project_id=%s', (project_id,))
            query(db, 'DELETE FROM projects WHERE id=%s', (project_id,))
        return {'data': {'deleted': True}}

    @app.post('/api/projects/{project_id}/scans', status_code=202)
    def upload_scan(project_id: str, file: UploadFile = File(...)):
        with connect() as db:
            project_record(db, project_id)
        if not file.filename or not file.filename.lower().endswith('.zip'):
            raise HTTPException(400, 'Unggah proyek dalam format ZIP.')
        scan_id = uuid.uuid4().hex
        directory = root / 'scans' / scan_id
        directory.mkdir()
        saved = False
        try:
            digest, size = hashlib.sha256(), 0
            with (directory / 'source.zip').open('xb') as output:
                while chunk := file.file.read(64 * 1024):
                    size += len(chunk)
                    if size > config.MAX_UPLOAD:
                        raise HTTPException(413, 'ZIP melebihi batas 100 MB.')
                    digest.update(chunk)
                    output.write(chunk)
            with tempfile.TemporaryDirectory(dir=directory, prefix='validate-') as extracted:
                coverage = inspect_zip(directory / 'source.zip', extracted)
            stamp = now()
            methods = {method: {'status': 'queued'} for method in ('sast', 'sca')}
            with connect() as db:
                project_record(db, project_id, lock=True)
                version = query(db, 'SELECT id FROM project_versions WHERE project_id=%s AND sha256=%s', (project_id, digest.hexdigest())).fetchone()
                version_id = version['id'] if version else uuid.uuid4().hex
                if not version:
                    documentation = project_record(db, project_id)
                    query(db, 'INSERT INTO project_versions(id,project_id,sha256,documentation,created_at) VALUES(%s,%s,%s,%s,%s)',
                          (version_id, project_id, digest.hexdigest(), json.dumps(documentation), stamp))
                query(db, '''INSERT INTO scans(id,project_id,filename,sha256,size,status,created_at,coverage,methods,version_id)
                    VALUES(%s,%s,%s,%s,%s,'queued',%s,%s,%s,%s)''',
                    (scan_id, project_id, file.filename.replace('\\', '/').split('/')[-1][:200], digest.hexdigest(), size,
                     stamp, json.dumps(coverage), json.dumps(methods), version_id))
                data = scan_record(db, scan_id)
            saved = True
            return {'data': data}
        except ArchiveError as error:
            raise HTTPException(400, str(error)) from None
        finally:
            file.file.close()
            if not saved:
                shutil.rmtree(directory)

    @app.get('/api/scans/{scan_id}')
    def scan(scan_id: str):
        with connect() as db:
            data = scan_record(db, scan_id)
            data['project'] = project_record(db, data['project_id'])
            data['main_scan_id'] = next((s['id'] for s in main_scans(db) if s['project_id'] == data['project_id']), None)
            data['summary'] = summary(all_findings(db, scan_id))
        return {'data': data}

    @app.get('/api/scans/{scan_id}/findings')
    def findings(scan_id: str, q: str = Query('', max_length=200),
                 method: Literal['sast', 'sca'] | None = None,
                 severity: Literal['critical', 'high', 'medium', 'low', 'unknown'] | None = None,
                 risk: Literal['high', 'medium', 'low', 'unassessed'] | None = None,
                 review: Literal['unreviewed', 'confirmed', 'false_positive', 'investigate'] | None = None,
                 page: int = Query(1, ge=1), pageSize: int = Query(25, ge=1, le=100)):
        with connect() as db:
            scan_record(db, scan_id)
            data = all_findings(db, scan_id)
        data = [item for item in data if (not method or item['method'] == method)
                and (not severity or item['severity'] == severity) and (not risk or ((item.get('automatic') or {}).get('project_risk') or {}).get('category', item['risk']) == risk)
                and (not review or item['review_status'] == review)
                and q.casefold() in (' '.join(str(item.get(key, '')) for key in
                    ('path', 'source_id', 'title', 'package', 'aliases', 'cwe')) + ' ' + str((item.get('translation') or {}).get('title', ''))).casefold()]
        return {'data': data[(page - 1) * pageSize:page * pageSize],
                'meta': {'total': len(data), 'page': page, 'pageSize': pageSize}}

    @app.get('/api/scans/{scan_id}/findings/{finding_id}')
    def finding(scan_id: str, finding_id: str):
        with connect() as db:
            scan_record(db, scan_id)
            row = query(db, 'SELECT * FROM findings WHERE scan_id=%s AND id=%s', (scan_id, finding_id)).fetchone()
        if row is None:
            raise HTTPException(404, 'Temuan tidak ditemukan pada scan ini.')
        with connect() as db:
            result = next(item for item in research_findings(db, scan_id, True) if item['id'] == finding_id)
        return {'data': result}

    @app.patch('/api/scans/{scan_id}/findings/{finding_id}/review')
    def review_finding(scan_id: str, finding_id: str, payload: ReviewInput):
        decision = payload.model_dump()
        stamp, validation_id = now(), uuid.uuid4().hex
        selected = select_scenario(decision['scenarios'])
        data = {key: decision[key] for key in ('review_status', 'review_reason', 'risk_reason')}
        data.update(likelihood=selected['likelihood'] if selected else None,
                    impact=selected['impact'] if selected else None, reviewed_at=stamp)
        with connect() as db:
            scan_data = scan_record(db, scan_id)
            if scan_data['status'] != 'completed':
                raise HTTPException(409, 'Validasi penelitian memerlukan kedua alat selesai lengkap.')
            row = query(db, 'SELECT id FROM findings WHERE id=%s AND scan_id=%s FOR UPDATE', (finding_id, scan_id)).fetchone()
            if not row:
                raise HTTPException(404, 'Temuan tidak ditemukan pada scan ini.')
            query(db, 'INSERT INTO validation_history(id,finding_id,decision,created_at) VALUES(%s,%s,%s,%s)',
                  (validation_id, finding_id, json.dumps(decision), stamp))
            for position, scenario in enumerate(decision['scenarios']):
                values = dict(id=uuid.uuid4().hex, validation_id=validation_id, position=position, rubric='R1', **scenario)
                query(db, f"INSERT INTO risk_scenarios ({','.join(values)}) VALUES ({','.join('%s' for _ in values)})", tuple(values.values()))
            query(db, f"UPDATE findings SET {','.join(f'{key}=%s' for key in data)} WHERE id=%s", (*data.values(), finding_id))
            result = next(item for item in research_findings(db, scan_id, True) if item['id'] == finding_id)
        return {'data': result}

    @app.get('/api/scans/{scan_id}/export')
    def export(scan_id: str, format: Literal['csv', 'json'] = 'json'):
        with connect() as db:
            scan_data = scan_record(db, scan_id)
            project_data = project_record(db, scan_data['project_id'])
            items = research_findings(db, scan_id, True)
            version = query(db, 'SELECT * FROM project_versions WHERE id=%s', (scan_data['version_id'],)).fetchone()
            primary_id = next((s['id'] for s in main_scans(db) if s['project_id'] == scan_data['project_id']), None)
            sample = query(db, 'SELECT r.*,c.manifest,c.sha256 AS manifest_sha256 FROM research_samples r JOIN research_protocol c ON c.id=r.protocol_id WHERE r.project_id=%s', (scan_data['project_id'],)).fetchone()
            if sample:
                sample['manifest'] = json.loads(sample['manifest'])
        report = {'sample': sample, 'version': {**version, 'documentation': json.loads(version['documentation'])} if version else None, 'main_scan_id': primary_id, 'project': project_data, 'scan': scan_data, 'summary': summary(items),
                  'findings': items, 'research_protocol': {'reference': 'Analisis Risiko Keamanan pada Proyek Hasil Vibe Coding Menggunakan SAST dan SCA melalui Aplikasi VibeSec Berbasis Web', 'rubric': 'RA1 estimasi risiko inheren bersyarat; A1 prioritas teknis; R1 historis', 'assessment_engine': 'AUTO1', 'context_policy': 'CTX1', 'sample_target': 12,
                    'groups': {'todo': 4, 'chatbot': 4, 'catalog': 4},
                    'methods': {'sast': 'Semgrep Community Edition', 'sca': 'OSV-Scanner versi 2'},
                    'risk_eligibility': 'RA1: kecocokan SCA terkonfirmasi, scope lockfile v2/v3, CVSS v3 lengkap; asumsi pemanggilan dan masukan penyerang dinyatakan eksplisit. SAST atau bukti tidak lengkap tanpa skor.',
                    'analysis': 'Deskriptif terhadap sampel; tanpa pentest, DAST, atau perbandingan model AI.'},
                  'limitations': 'Nol temuan tidak menjamin keamanan. SCA tidak membuktikan reachability atau eksploitabilitas. Analisis deskriptif berlaku pada sampel penelitian dan tidak digeneralisasi ke seluruh proyek hasil vibe coding.'}
        if format == 'json':
            content = json.dumps(report, ensure_ascii=False, indent=2)
            media_type = 'application/json'
        else:
            output = io.StringIO(newline='')
            writer = csv.writer(output)
            writer.writerow(['scan_id', 'project', 'sha256', 'status', 'metadata_json', 'finding_json'])
            metadata = json.dumps({key: value for key, value in report.items() if key != 'findings'}, ensure_ascii=False)
            for item in items or [None]:
                values = [scan_id, project_data['name'], scan_data['sha256'], scan_data['status'], metadata,
                          json.dumps(item, ensure_ascii=False) if item else '']
                writer.writerow(["'" + value if value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value
                                 for value in values])
            content, media_type = '\ufeff' + output.getvalue(), 'text/csv'
        return Response(content, media_type=media_type,
                        headers={'Content-Disposition': f'attachment; filename="vibesec-{scan_id}.{format}"'})

    return app


app = create_app()
