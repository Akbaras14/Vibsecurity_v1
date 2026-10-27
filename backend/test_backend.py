"""Offline checks plus opt-in MySQL integration checks; see README."""
import hashlib
import asyncio
import io
import json
import os
import re
import uuid
import pymysql
import stat
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from .archive import ArchiveError, inspect_zip
from .main import create_app, LocalGuard, ReviewInput
from . import config
from .config import mysql_settings
from .migrate import migrate
from .scanner import memory_cgroup, network_cgroup, parse_results, run_method, run_process
from .store import connect, finding_dict, risk_category, summary, query
from .worker import claim_scan, overall_status, process_scan, recover_interrupted


def zip_bytes(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for name, content in files.items():
            bundle.writestr(name, content)
    return output.getvalue()


@unittest.skipUnless(os.environ.get('VIBESEC_TEST_MYSQL') == '1', 'Set VIBESEC_TEST_MYSQL=1 for real MySQL integration tests.')
class BackendCheck(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        settings = mysql_settings()
        settings.pop('database')
        self.admin = pymysql.connect(**settings)
        self.database = 'vibesec_test_' + uuid.uuid4().hex
        with self.admin.cursor() as db:
            db.execute(f'CREATE DATABASE `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        self.environment = patch.dict(os.environ, {'VIBESEC_MYSQL_DATABASE': self.database})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.drop_database)
        self.client = TestClient(create_app(self.root), base_url='http://127.0.0.1:8000')
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temporary.cleanup()

    def drop_database(self):
        assert re.fullmatch(r'vibesec_test_[0-9a-f]{32}', self.database)
        with self.admin.cursor() as db:
            db.execute(f'DROP DATABASE `{self.database}`')
        self.admin.close()

    def project(self, name='Proyek uji'):
        response = self.client.post('/api/projects', json={'name': name})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['data']['id']

    def upload(self, project_id, data=None):
        return self.client.post(f'/api/projects/{project_id}/scans', files={
            'file': ('project.zip', data or zip_bytes({'src/app.js': 'eval(input);',
                'package-lock.json': '{"lockfileVersion":3,"packages":{}}'}), 'application/zip')})

    def test_project_lifecycle_origin_and_input(self):
        self.assertEqual(self.client.post('/api/projects', json={'name': ' '}).status_code, 400)
        self.assertEqual(self.client.post('/api/projects', json={'name': 'x', 'owner': 'x'}).status_code, 400)
        project_id = self.project()
        self.assertEqual(self.client.get('/api/projects').json()['meta']['total'], 1)
        self.assertEqual(self.client.get('/api/projects', params={'q': '%'}).json()['meta']['total'], 0)
        self.assertEqual(self.client.get('/api/projects', params={'q': "' OR 1=1 --"}).json()['meta']['total'], 0)
        result = self.client.patch(f'/api/projects/{project_id}', json={'name': 'Revisi', 'ai_tool': 'Codex'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['data']['ai_tool'], 'Codex')
        self.assertEqual(self.client.patch(f'/api/projects/{project_id}', json={'ai_model': 'Model uji'}).status_code, 200)
        self.assertEqual(self.client.patch(f'/api/projects/{project_id}', json={'name': None}).status_code, 400)
        self.assertEqual(self.client.patch(f'/api/projects/{project_id}', json={'sample_group': 'other'}).status_code, 400)
        self.assertEqual(self.client.patch(f'/api/projects/{project_id}', json={'sample_group': 'todo'}).status_code, 200)
        research = self.client.get('/api/dashboard').json()['data']['research_groups']
        self.assertEqual(research[0]['registered'], 1)
        self.assertEqual(research[0]['target'], 4)
        self.assertEqual(research[0]['scanned'], 0)
        self.assertEqual(self.client.get('/api/dashboard').json()['data']['projects'], 1)
        self.assertEqual(self.client.post('/api/projects', json={'name': 'x'}, headers={'Origin': 'https://evil.invalid'}).status_code, 403)
        self.assertEqual(self.client.get('/api/projects', headers={'Host': 'evil.invalid'}).status_code, 403)
        preflight = self.client.options('/api/projects', headers={'Origin': 'http://127.0.0.1:3000', 'Access-Control-Request-Method': 'POST'})
        self.assertEqual(preflight.status_code, 200)
        self.assertEqual(self.client.options('/api/projects', headers={
            'Host': 'evil.invalid', 'Origin': 'http://127.0.0.1:3000',
            'Access-Control-Request-Method': 'POST'}).status_code, 403)
        self.assertEqual(self.client.options('/api/projects', headers={
            'Origin': 'https://evil.invalid', 'Access-Control-Request-Method': 'POST'}).status_code, 403)
        self.assertEqual(self.client.delete(f'/api/projects/{project_id}').status_code, 200)
        self.assertEqual(self.client.get(f'/api/projects/{project_id}').status_code, 404)

    def test_upload_snapshot_and_configuration_failure(self):
        project_id = self.project()
        data = zip_bytes({'src/app.ts': 'eval(input)', 'package-lock.json': '{"lockfileVersion":3}',
                          'node_modules/dependency.js': 'ignored'})
        response = self.upload(project_id, data)
        self.assertEqual(response.status_code, 202, response.text)
        scan = response.json()['data']
        self.assertEqual(scan['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(scan['coverage']['source_files'], 1)
        self.assertIn('node_modules/dependency.js', scan['coverage']['skipped'])
        self.assertEqual(self.client.delete(f'/api/projects/{project_id}').status_code, 409)
        with patch('backend.worker.readiness', return_value={'reasons': ['Scanner belum tersedia.']}):
            process_scan(self.root, claim_scan(self.root))
        result = self.client.get(f"/api/scans/{scan['id']}").json()['data']
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['methods']['sast']['status'], 'failed')
        self.assertIn('Scanner belum', result['methods']['sast']['error'])
        self.assertIsNotNone(result['methods']['sast']['started_at'])
        self.assertIsNotNone(result['methods']['sast']['finished_at'])
        self.assertGreaterEqual(result['methods']['sast']['duration_seconds'], 0)
        self.assertFalse((self.root / 'scans' / scan['id'] / 'extracted').exists())
        self.assertEqual(self.client.delete(f'/api/projects/{project_id}').status_code, 200)
        self.assertFalse((self.root / 'scans' / scan['id']).exists())

    def test_reject_archive_paths_symlinks_sizes_and_malformed_lock(self):
        project_id = self.project()
        for name in ('../escape.js', '/tmp/escape.js', 'C:/escape.js', '..\\escape.js',
                     'AUX.js', 'dir./file.js', 'a//b.js'):
            response = self.upload(project_id, zip_bytes({name: 'x'}))
            self.assertEqual(response.status_code, 400, (name, response.text))
        response = self.upload(project_id, b'not zip')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.upload(project_id, zip_bytes({'package-lock.json': 'oops'})).status_code, 400)
        linked = io.BytesIO()
        with zipfile.ZipFile(linked, 'w') as bundle:
            item = zipfile.ZipInfo('link')
            item.create_system = 3
            item.external_attr = (stat.S_IFLNK | 0o777) << 16
            bundle.writestr(item, '/etc/passwd')
        self.assertEqual(self.upload(project_id, linked.getvalue()).status_code, 400)
        duplicate = io.BytesIO()
        with zipfile.ZipFile(duplicate, 'w') as bundle:
            bundle.writestr('APP.js', 'x')
            bundle.writestr('app.js', 'x')
        self.assertEqual(self.upload(project_id, duplicate.getvalue()).status_code, 400)
        with patch('backend.archive.MAX_FILE', 10):
            self.assertEqual(self.upload(project_id, zip_bytes({'large.js': 'x' * 11})).status_code, 400)
        with patch('backend.config.MAX_UPLOAD', 10):
            self.assertEqual(self.upload(project_id).status_code, 413)
        self.assertEqual(list((self.root / 'scans').iterdir()), [])
        self.assertFalse((self.root / 'escape.js').exists())

    def test_unsupported_partial_and_preserved_history(self):
        project_id = self.project()
        first = self.upload(project_id, zip_bytes({'README.md': 'hello'})).json()['data']
        with patch('backend.worker.readiness', return_value={'reasons': []}):
            process_scan(self.root, claim_scan(self.root))
        self.assertEqual(self.client.get(f"/api/scans/{first['id']}").json()['data']['status'], 'unsupported')
        second = self.upload(project_id, zip_bytes({'app.js': 'const value = 1;'})).json()['data']
        with patch('backend.worker.readiness', return_value={'reasons': []}), patch(
                'backend.worker.run_method', return_value=({'tool': 'fixture', 'version': 'test-only'}, [])):
            process_scan(self.root, claim_scan(self.root))
        self.assertEqual(self.client.get(f"/api/scans/{second['id']}").json()['data']['status'], 'partial')
        self.assertEqual(len(self.client.get(f'/api/projects/{project_id}').json()['data']['scans']), 2)

    def test_failed_scanner_preserves_metadata(self):
        scan = self.upload(self.project()).json()['data']

        def fail(method, source, directory, heartbeat, metadata):
            metadata.update(tool='test-only', version='fixture', config_sha256='a' * 64,
                            raw_output=f'{method}.json')
            raise ValueError('Struktur temuan scanner tidak valid.')

        with patch('backend.worker.readiness', return_value={'reasons': []}), patch(
                'backend.worker.run_method', side_effect=fail):
            process_scan(self.root, claim_scan(self.root))
        result = self.client.get(f"/api/scans/{scan['id']}").json()['data']
        self.assertEqual(result['status'], 'failed')
        for method in result['methods'].values():
            self.assertEqual(method['status'], 'failed')
            self.assertEqual(method['version'], 'fixture')
            self.assertEqual(method['config_sha256'], 'a' * 64)
            self.assertIsNotNone(method['finished_at'])
        self.assertEqual(result['summary']['total'], 0)

    def test_parser_review_exports_and_dashboard_latest_only(self):
        project_id = self.project('=HYPERLINK("https://example.invalid")')
        scan = self.upload(project_id).json()['data']
        payload = {'results': [{'check_id': 'test.eval', 'path': 'app.js', 'start': {'line': 1, 'col': 1},
            'extra': {'message': '<script>example</script>', 'severity': 'ERROR', 'lines': 'eval(input)',
                      'metadata': {'references': ['javascript:alert(1)'], 'cwe': ['CWE-95']}}}], 'errors': []}
        normalized = parse_results('sast', payload, self.root)
        with patch('backend.worker.readiness', return_value={'reasons': []}), patch(
                'backend.worker.run_method', side_effect=[({'version': 'fixture-only'}, normalized), ({'version': 'fixture-only'}, [])]):
            process_scan(self.root, claim_scan(self.root))
        finding = self.client.get(f"/api/scans/{scan['id']}/findings").json()['data'][0]
        self.assertEqual(finding['severity'], 'high')
        self.assertEqual(self.client.get(f"/api/scans/{scan['id']}/findings?q=CWE-95").json()['meta']['total'], 1)
        path = f"/api/scans/{scan['id']}/findings/{finding['id']}/review"
        invalid = {'review_status': 'confirmed', 'review_reason': 'Bukti kode', 'likelihood': 3}
        self.assertEqual(self.client.patch(path, json=invalid).status_code, 400)
        invalid = {'review_status': 'confirmed', 'review_reason': 'Bukti kode', 'risk_reason': ''}
        for likelihood in (1, 2, 3):
            for impact in (1, 2, 3):
                invalid.update(scenarios=[{'scenario': 'Input eksternal', 'asset': 'Data', 'evidence': 'app.js:1', 'likelihood': likelihood, 'confidentiality': impact, 'reason': 'Bukti K dan C'}])
                result = self.client.patch(path, json=invalid)
                self.assertEqual(result.status_code, 200, result.text)
                self.assertEqual(result.json()['data']['risk'], risk_category(likelihood * impact))
        invalid.update(review_status='false_positive')
        self.assertEqual(self.client.patch(path, json=invalid).status_code, 400)
        invalid.update(scenarios=[], risk_reason='')
        self.assertEqual(self.client.patch(path, json=invalid).status_code, 200)
        result = self.client.get(f"/api/scans/{scan['id']}").json()['data']
        self.assertEqual(result['summary']['risks']['high'], 0)
        self.assertEqual(self.client.get(f"/api/scans/{scan['id']}/findings?severity=low").json()['meta']['total'], 0)
        exported = self.client.get(f"/api/scans/{scan['id']}/export?format=json").json()
        self.assertEqual(exported['findings'][0]['review_status'], 'false_positive')
        csv_text = self.client.get(f"/api/scans/{scan['id']}/export?format=csv").text
        self.assertIn("'=HYPERLINK", csv_text)
        other = self.upload(project_id).json()['data']
        self.assertEqual(self.client.get(f"/api/scans/{other['id']}/findings/{finding['id']}").status_code, 404)
        dashboard = self.client.get('/api/dashboard').json()['data']
        self.assertEqual(dashboard['summary']['total'], 0)
        self.assertEqual(dashboard['scans']['queued'], 1)
        self.assertEqual(dashboard['scans']['partial'], 0)
        self.assertEqual(len(dashboard['recent']), 1)
        self.assertEqual(dashboard['recent'][0]['id'], other['id'])
        project = self.client.get(f'/api/projects/{project_id}').json()['data']
        self.assertEqual(project['summary']['total'], 0)
        self.assertEqual(project['summary']['highest_risk'], 'unassessed')

    def test_worker_recovery_and_deletion_retry(self):
        project_id = self.project()
        scan = self.upload(project_id).json()['data']
        claim_scan(self.root)
        self.assertIsNone(claim_scan(self.root))
        with connect() as db:
            query(db, 'UPDATE scans SET heartbeat_at=NULL WHERE id=%s', (scan['id'],))
        recover_interrupted(self.root)
        self.assertEqual(self.client.get(f"/api/scans/{scan['id']}").json()['data']['status'], 'failed')
        with patch('backend.main.shutil.rmtree', side_effect=OSError('test-only')):
            self.assertEqual(self.client.delete(f'/api/projects/{project_id}').status_code, 500)
        self.assertEqual(self.client.get(f'/api/projects/{project_id}').status_code, 409)
        self.assertEqual(self.client.delete(f'/api/projects/{project_id}').status_code, 200)

    def test_migrations_repeat_preserve_data_and_mark_failure(self):
        project_id = self.project()
        self.assertEqual(migrate(self.root), [])
        self.assertEqual(self.client.get(f'/api/projects/{project_id}').status_code, 200)
        with connect() as db:
            self.assertEqual(query(db, 'SELECT version,dirty FROM schema_migrations').fetchone(), {'version': 1, 'dirty': 0})
        scripts = self.root / 'migration-fixtures'
        scripts.mkdir()
        original = Path(__file__).parent / 'migrations' / '001_initial.sql'
        (scripts / '001_initial.sql').write_text(original.read_text(encoding='utf-8'), encoding='utf-8')
        second = Path(__file__).parent / 'migrations' / '002_sample_group.sql'
        (scripts / second.name).write_text(second.read_text(encoding='utf-8'), encoding='utf-8')
        third = Path(__file__).parent / 'migrations' / '003_research_protocol.sql'
        (scripts / third.name).write_text(third.read_text(encoding='utf-8'), encoding='utf-8')
        fourth = Path(__file__).parent / 'migrations' / '004_coverage_review.sql'
        (scripts / fourth.name).write_text(fourth.read_text(encoding='utf-8'), encoding='utf-8')
        (scripts / '005_broken.sql').write_text('CREATE TABLE persisted_ddl(id INT); INVALID SQL;', encoding='utf-8')
        with patch('backend.migrate.MIGRATIONS', scripts), self.assertRaises(pymysql.MySQLError):
            migrate(self.root)
        with connect() as db:
            self.assertEqual(query(db, 'SELECT dirty FROM schema_migrations WHERE version=5').fetchone()['dirty'], 1)
            self.assertEqual(query(db, "SHOW TABLES LIKE 'persisted_ddl'").fetchone() is not None, True)
            self.assertIsNotNone(query(db, 'SELECT id FROM projects WHERE id=%s', (project_id,)).fetchone())
        with patch('backend.migrate.MIGRATIONS', scripts), self.assertRaises(ValueError):
            migrate(self.root)


    def test_automatic_scan_is_idempotent_and_separates_technical_priority(self):
        from .automatic import assess_scan
        project = self.project('Automatic fixture')
        scan = self.upload(project).json()['data']
        finding = uuid.uuid4().hex
        detail = {'package': 'example', 'installed_version': '1', 'osv_ids': ['GHSA-fixture'],
                  'project_context': {'observations': [{'scope': 'runtime', 'lockfile': 'package-lock.json', 'dependency_path': 'node_modules/example', 'sha256': 'a' * 64}]},
                  'translation': {'status': 'completed', 'title': 'Kerentanan uji terjemahan'},
                  'cvss': [{'score': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H'}]}
        with connect() as db:
            query(db, "UPDATE scans SET status='completed' WHERE id=%s", (scan['id'],))
            query(db, "INSERT INTO findings(id,scan_id,method,source_id,title,severity,path,detail,review_reason,risk_reason) VALUES(%s,%s,'sca','GHSA-fixture','Test','high','package-lock.json',%s,'','')", (finding, scan['id'], json.dumps(detail)))
            self.assertEqual(assess_scan(db, scan['id']), 1)
            self.assertEqual(assess_scan(db, scan['id']), 0)
        report = self.client.get(f"/api/scans/{scan['id']}/export").json()
        self.assertEqual(len(report['findings'][0]['history']), 1)
        self.assertEqual(report['findings'][0]['automatic']['priority']['score'], 9)
        self.assertIsNone(report['findings'][0]['risk_score'])
        self.assertEqual(report['summary']['risks']['high'], 0)
        self.assertEqual(report['summary']['automatic']['priorities']['high'], 1)
        self.assertEqual(report['summary']['risk_analysis']['categories']['high'], 1)
        self.assertEqual(report['findings'][0]['automatic']['project_risk']['score'], 9)
        filtered = self.client.get(f"/api/scans/{scan['id']}/findings?risk=high").json()
        self.assertEqual(filtered['meta']['total'], 1)
        self.assertEqual(self.client.get(f"/api/scans/{scan['id']}/findings?q=uji%20terjemahan").json()['meta']['total'], 1)

    def test_worker_finishes_with_automatic_decision(self):
        project = self.project('Automatic worker fixture')
        scan = self.upload(project).json()['data']
        finding = {'id': uuid.uuid4().hex, 'method': 'sca', 'source_id': 'GHSA-fixture', 'title': 'Fixture',
                   'severity': 'high', 'path': 'package-lock.json',
                   'detail': {'package': 'example', 'installed_version': '1', 'osv_ids': ['GHSA-fixture']}}
        with patch('backend.worker.readiness', return_value={'reasons': []}), patch(
                'backend.worker.run_method', side_effect=[({'version': 'fixture'}, []), ({'version': 'fixture'}, [finding])]):
            process_scan(self.root, claim_scan(self.root))
        report = self.client.get(f"/api/scans/{scan['id']}/export").json()
        self.assertEqual(report['scan']['status'], 'completed')
        self.assertEqual(report['findings'][0]['automatic']['engine'], 'AUTO1')
        self.assertEqual(report['findings'][0]['review_status'], 'confirmed')
        self.assertIsNone(report['findings'][0]['automatic']['priority'])

    def test_ra1_freeze_records_risk_policy_and_rejects_changed_hash(self):
        from .research import matches
        project = self.project('RA1 freeze fixture')
        self.client.patch(f'/api/projects/{project}', json={'sample_group': 'todo', 'sample_code': 'TD01',
            'ai_tool': 'ChatGPT', 'development_notes': 'Dokumentasi fixture'})
        scan = self.upload(project, zip_bytes({'app/page.tsx': 'export default ()=>null',
            'package-lock.json': '{"lockfileVersion":3}', 'package.json': '{"dependencies":{"next":"16.3.8"}}'})).json()['data']
        methods = {m: {'status': 'completed', 'tool': m, 'version': 'fixture', 'config_sha256': 'a'*64,
                      'rules_sha256': 'b'*64, 'rules_manifest': {'commit': 'fixture'}, 'database_sha256': 'c'*64,
                      'assessment_policy': 'AUTO1/A1/RA1/CTX1', 'risk_policy_sha256': 'd'*64} for m in ('sast', 'sca')}
        with connect() as db:
            query(db, "UPDATE scans SET status='completed',methods=%s WHERE id=%s", (json.dumps(methods), scan['id']))
        response = self.client.post(f"/api/scans/{scan['id']}/freeze", json={'reason': 'Cakupan fixture diperiksa'})
        self.assertEqual(response.status_code, 200, response.text)
        with connect() as db:
            manifest = json.loads(query(db, 'SELECT manifest FROM research_protocol WHERE id=1').fetchone()['manifest'])
        self.assertEqual(manifest['rubric'], 'RA1')
        self.assertEqual(manifest['methods']['sast']['risk_policy_sha256'], 'd'*64)
        self.assertTrue(matches({'status': 'completed', 'methods': methods}, manifest))
        methods['sast']['risk_policy_sha256'] = 'e'*64
        self.assertFalse(matches({'status': 'completed', 'methods': methods}, manifest))

    def test_r1_history_scenarios_and_main_scan(self):
        project_id = self.project('Uji R1')
        self.client.patch(f'/api/projects/{project_id}', json={'sample_group': 'todo', 'sample_code': 'TD01',
            'ai_tool': 'ChatGPT', 'development_notes': 'Dokumentasi fixture, bukan sampel penelitian'})
        archive = zip_bytes({'app/page.tsx': 'eval(input)', 'package-lock.json': '{"lockfileVersion":3}', 'package.json': '{"dependencies":{"next":"16.3.8"}}'})
        first = self.upload(project_id, archive).json()['data']
        metadata = {'sast': {'status': 'completed', 'tool': 'semgrep', 'version': 'fixture',
                     'config_sha256': 'a'*64, 'rules_sha256': 'b'*64, 'rules_manifest': {'commit': 'fixture'}},
                    'sca': {'status': 'completed', 'tool': 'osv-scanner', 'version': 'fixture',
                     'config_sha256': 'c'*64, 'database_sha256': 'd'*64}}
        finding_id = uuid.uuid4().hex
        with connect() as db:
            query(db, "UPDATE scans SET status='completed',methods=%s WHERE id=%s", (json.dumps(metadata), first['id']))
            query(db, "INSERT INTO findings(id,scan_id,method,source_id,title,severity,path,detail,review_reason,risk_reason) VALUES(%s,%s,'sast','test','Test','high','app.js','{}','','')", (finding_id, first['id']))
        frozen = self.client.post(f"/api/scans/{first['id']}/freeze", json={'reason': 'Cakupan fixture telah diperiksa'})
        self.assertEqual(frozen.status_code, 200, frozen.text)
        self.assertEqual(frozen.json()['data']['main_scan_id'], first['id'])
        second = self.upload(project_id, archive).json()['data']
        self.assertEqual(first['version_id'], second['version_id'])
        self.assertEqual(self.client.get('/api/dashboard').json()['data']['research_groups'][0]['scanned'], 1)
        self.assertEqual(self.client.get(f'/api/projects/{project_id}').json()['data']['main_scan_id'], first['id'])
        self.assertEqual(self.client.patch(f'/api/projects/{project_id}', json={'sample_code': 'TD02'}).status_code, 409)
        url = f"/api/scans/{first['id']}/findings/{finding_id}/review"
        a = {'scenario': 'Satu', 'asset': 'Data', 'evidence': 'app.js:1', 'reason': 'Bukti K dan CIA', 'likelihood': 3, 'confidentiality': 2}
        b = {**a, 'scenario': 'Dua', 'likelihood': 2, 'confidentiality': 3}
        response = self.client.patch(url, json={'review_status': 'confirmed', 'review_reason': 'Bukti sesuai', 'scenarios': [a,b]})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()['data']
        self.assertEqual((result['likelihood'], result['impact'], result['risk_score']), (2,3,6))
        self.assertEqual(len(result['history']), 1)
        response = self.client.patch(url, json={'review_status': 'false_positive', 'review_reason': 'Kontrol membatalkan temuan'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()['data']['risk_score'])
        self.assertEqual(response.json()['data']['history'][0]['scenarios'][1]['score'], 6)
        report = self.client.get(f"/api/scans/{first['id']}/export").json()
        self.assertEqual(len(report['findings'][0]['history']), 2)
        self.assertEqual(report['summary']['risks']['high'], 0)
        self.assertIsNone(report['summary']['risk_percentages']['high'])
        self.assertEqual(report['summary']['review_percentages']['false_positive'], 100)
        original_query = query
        def fail_update(cursor, sql, parameters=None):
            if sql.startswith('UPDATE findings SET'):
                raise pymysql.OperationalError(2013, 'Fixture connection failure')
            return original_query(cursor, sql, parameters)
        with patch('backend.main.query', side_effect=fail_update), self.assertRaises(pymysql.OperationalError):
            self.client.patch(url, json={'review_status': 'investigate', 'review_reason': 'Rollback fixture'})
        stored = self.client.get(f"/api/scans/{first['id']}/findings/{finding_id}").json()['data']
        self.assertEqual(len(stored['history']), 2)
        self.assertEqual(stored['review_status'], 'false_positive')



class OfflineCheck(unittest.TestCase):
    def test_automatic_assessment_requires_evidence_and_complete_vector(self):
        from .automatic import assess
        finding = {'method': 'sca', 'detail': {'package': 'example', 'installed_version': '1.0', 'osv_ids': ['GHSA-example'],
            'cvss': [{'type': 'CVSS_V3', 'score': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H'}]}}
        result = assess(finding)
        self.assertEqual(result['review_status'], 'confirmed')
        self.assertEqual(result['priority']['score'], 9)
        self.assertEqual(result['model'], 'A1')
        self.assertEqual(result['scenarios'], [])
        finding['detail']['cvss'][0]['score'] = 'CVSS:3.1/AV:N'
        self.assertIsNone(assess(finding)['priority'])
        finding['detail']['cvss'] = [{'score': 'CVSS:4.0/AV:N'}]
        self.assertIsNone(assess(finding)['priority'])
        self.assertEqual(assess({'method': 'sast', 'detail': {'snippet': 'eval(input)'}})['review_status'], 'investigate')
        self.assertEqual(assess({'method': 'sca', 'detail': {'package': 'example'}})['review_status'], 'investigate')

    @unittest.skipUnless(os.name == 'nt', 'Windows WSL supervisor')
    def test_supervisor_preserves_credentials_and_propagates_worker_exit(self):
        import runpy
        launcher = runpy.run_path(str(Path(__file__).parent.parent / 'scripts/start-worker.py'))
        failure = subprocess.CalledProcessError(1, 'worker')
        with patch('subprocess.check_output', return_value='/mnt/e/Project_Coding/VibeSec\n'), patch(
                'subprocess.run', side_effect=[None, None, failure]) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                launcher['run_worker']()
        self.assertIn('--preserve-credentials', run.call_args_list[0].args[0])
        self.assertIn('vibesec-scanner', run.call_args_list[-1].args[0])

    def test_worker_retries_database_disconnect(self):
        from .worker import main
        with patch('backend.worker.work_session', side_effect=[pymysql.OperationalError(2013, 'test disconnect'), KeyboardInterrupt]) as session, patch('backend.worker.time.sleep') as sleep:
            main()
        self.assertEqual(session.call_count, 2)
        sleep.assert_called_once_with(5)

    def test_connection_preserves_original_error_when_rollback_fails(self):
        from unittest.mock import MagicMock
        db = MagicMock()
        db.rollback.side_effect = pymysql.InterfaceError(0, 'closed')
        with patch('backend.store.pymysql.connect', return_value=db):
            with self.assertRaisesRegex(ValueError, 'original failure'):
                with connect():
                    raise ValueError('original failure')
        db.close.assert_called_once()

    def test_dedup_preserves_positions_and_sca_locations(self):
        sast = {'check_id': 'r', 'path': 'a.ts', 'start': {'line': 1, 'col': 1},
                'end': {'line': 1, 'col': 4}, 'extra': {'message': 'r', 'severity': 'WARNING'}}
        other = {**sast, 'end': {'line': 1, 'col': 7}}
        self.assertEqual(len(parse_results('sast', {'results': [sast, sast, other]}, Path('.'))), 2)
        package = {'package': {'name': 'x', 'version': '1', 'ecosystem': 'npm'},
                   'vulnerabilities': [{'id': 'GHSA-x'}], 'groups': [{'ids': ['GHSA-x'], 'aliases': ['CVE-x']}]}
        results = [{'source': {'path': p, 'type': 'lockfile'}, 'packages': [package]} for p in ('a/package-lock.json', 'b/package-lock.json')]
        rows = parse_results('sca', {'results': results}, Path('.'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['detail']['paths'], ['a/package-lock.json', 'b/package-lock.json'])

    def test_r1_incomplete_scenarios_and_pairing(self):
        from .research import Scenario, select_scenario
        base = {'scenario': 'S', 'asset': 'A', 'evidence': 'Kode', 'reason': 'Bukti', 'likelihood': 3, 'confidentiality': 1}
        with self.assertRaises(ValueError):
            Scenario(**{**base, 'evidence': ''})
        uncertain = Scenario(**{**base, 'uncertainty': 'Jalur belum jelas'}).model_dump()
        self.assertIsNone(select_scenario([uncertain]))
        chosen = select_scenario([base, {**base, 'likelihood': 1, 'confidentiality': 3}])
        self.assertEqual((chosen['score'], chosen['likelihood'], chosen['impact']), (3,1,3))
        with self.assertRaises(ValueError):
            ReviewInput(review_status='confirmed', review_reason='Bukti')

    def test_sast_evidence_uses_actual_snapshot_lines(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'handler.ts').write_text('function run(input) {\n  return eval(input);\n}\n')
            payload = {'results': [{'check_id': 'test.eval', 'path': 'handler.ts',
                'start': {'line': 2}, 'end': {'line': 2},
                'extra': {'severity': 'ERROR', 'lines': 'requires login'}}]}
            finding = parse_results('sast', payload, root)[0]
            self.assertEqual(finding['detail']['snippet'], '  return eval(input);')
            self.assertEqual(finding['detail']['snippet_source'], 'snapshot')
            (root / 'handler.ts').unlink()
            self.assertIsNone(parse_results('sast', payload, root)[0]['detail']['snippet'])
    def test_osv_exit_zero_with_database_error_is_failed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            cache = root / 'cache'
            (cache / 'osv-scalibr/npm').mkdir(parents=True)
            (cache / 'osv-scalibr/npm/all.zip').write_bytes(b'test-only')
            (cache / 'metadata.json').write_text('{}')
            (source / 'package-lock.json').write_text('{"lockfileVersion":3}')

            def process(arguments, stdout, stderr, cwd, heartbeat, timeout):
                stdout.write_text('osv-scanner version: 2.7.0' if '--version' in arguments else '{"results":[]}')
                stderr.write_text('' if '--version' in arguments else 'Error during extraction: offline database missing')
                return 0

            with patch('backend.scanner.OSV_CACHE', cache), patch('backend.scanner.shutil.which', return_value='osv-scanner'), patch(
                    'backend.scanner.run_process', side_effect=process), self.assertRaisesRegex(ValueError, 'kegagalan'):
                run_method('sca', source, root, lambda: None)

    def test_risk_only_includes_confirmed_findings(self):
        findings = []
        for status in ('unreviewed', 'confirmed', 'false_positive', 'investigate'):
            finding = finding_dict({'detail': '{}', 'review_status': status, 'likelihood': 2,
                                    'impact': 3, 'severity': 'high', 'method': 'sast'})
            self.assertEqual(finding['risk_score'], 6 if status == 'confirmed' else None)
            findings.append(finding)
        result = summary(findings)
        self.assertEqual(result['risks']['high'], 1)
        self.assertEqual(result['excluded_from_risk'], 3)
        self.assertFalse(result['provisional'])
        for status in ('unreviewed', 'false_positive', 'investigate'):
            with self.assertRaises(ValueError):
                ReviewInput(review_status=status, review_reason='Bukti', likelihood=2, impact=3, risk_reason='Konteks')

    def test_network_cgroup_requires_the_scanner_firewall_class(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'cgroup.procs').touch()
            with patch.dict(os.environ, {'VIBESEC_NETWORK_CGROUP': str(root)}):
                for invalid in ('0', '1048578', 'invalid'):
                    (root / 'net_cls.classid').write_text(invalid)
                    with self.assertRaises(ValueError):
                        network_cgroup()
                for valid in ('1048577', '0x100001'):
                    (root / 'net_cls.classid').write_text(valid)
                    self.assertEqual(network_cgroup(), root.resolve())

    def test_memory_cgroup_rejects_unlimited_or_oversized_limits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'cgroup.procs').touch()
            with patch.dict(os.environ, {'VIBESEC_MEMORY_CGROUP': str(root)}):
                for invalid in ('max', '0', str(2 * 1024**3 + 1)):
                    (root / 'memory.max').write_text(invalid)
                    with self.assertRaises(ValueError):
                        memory_cgroup()
                (root / 'memory.max').write_text(str(2 * 1024**3))
                self.assertEqual(memory_cgroup(), root.resolve())
                (root / 'memory.max').unlink()
                (root / 'memory.limit_in_bytes').write_text(str(2 * 1024**3))
                self.assertEqual(memory_cgroup(), root.resolve())
                with patch('backend.scanner.network_cgroup', return_value=root), patch(
                        'backend.scanner.subprocess.Popen', side_effect=subprocess.SubprocessError('preexec')):
                    with self.assertRaises(OSError):
                        run_process(['test-only'], root / 'stdout', root / 'stderr', root, lambda: None)

    def test_all_final_method_status_combinations(self):
        for sast in ('completed', 'failed', 'unsupported'):
            for sca in ('completed', 'failed', 'unsupported'):
                expected = ('completed' if sast == sca == 'completed' else
                            'partial' if 'completed' in (sast, sca) else
                            'failed' if 'failed' in (sast, sca) else 'unsupported')
                self.assertEqual(overall_status({'sast': {'status': sast}, 'sca': {'status': sca}}), expected)
        self.assertEqual(overall_status({'sast': {'status': 'completed'},
                                         'sca': {'status': 'running'}}), 'running')

    def test_sca_only_receives_npm_lockfiles_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'extracted'
            (source / 'nested').mkdir(parents=True)
            (source / 'empty/package-lock.json').mkdir(parents=True)
            (source / 'nested/package-lock.json').write_text('{"lockfileVersion":3}')
            (source / 'requirements.txt').write_text('django==1.0')
            (source / 'yarn.lock').write_text('untrusted')
            (source / '.trivyignore').write_text('CVE-TEST')
            inputs = []

            def scan(method, scoped, directory, heartbeat, metadata):
                inputs.append(scoped)
                self.assertEqual([path.relative_to(scoped).as_posix() for path in scoped.rglob('*')
                                  if path.is_file()], ['nested/package-lock.json'])
                raise ValueError('test failure')

            with patch('backend.scanner._run_method', side_effect=scan), self.assertRaises(ValueError):
                run_method('sca', source, root, lambda: None)
            self.assertFalse(inputs[0].exists())
            self.assertTrue((source / 'requirements.txt').exists())

    def test_upload_100_mb_limit_and_streaming_guard(self):
        self.assertEqual(config.MAX_UPLOAD, 100 * 1024 * 1024)

        async def request(size, declared):
            remaining = size
            sent = []

            async def receive():
                nonlocal remaining
                length = min(remaining, 64 * 1024)
                remaining -= length
                return {'type': 'http.request', 'body': b'x' * length, 'more_body': remaining > 0}

            async def send(message):
                sent.append(message)

            async def app(scope, receive, send):
                total = 0
                while True:
                    message = await receive()
                    total += len(message['body'])
                    if not message.get('more_body'):
                        break
                self.assertEqual(total, size)
                await send({'type': 'http.response.start', 'status': 204})

            guard = LocalGuard(app, ('127.0.0.1',), ('http://127.0.0.1:3001',))
            await guard({'type': 'http', 'path': '/api/projects/test/scans',
                         'headers': [(b'host', b'127.0.0.1'), (b'content-length', str(declared).encode()),
                                     (b'origin', b'http://127.0.0.1:3001')]}, receive, send)
            return sent[0]

        # A ZIP request above the old 20 MB ceiling reaches the application.
        self.assertEqual(asyncio.run(request(21 * 1024 * 1024, 21 * 1024 * 1024))['status'], 204)
        self.assertEqual(asyncio.run(request(0, config.MAX_UPLOAD))['status'], 204)
        self.assertEqual(asyncio.run(request(0, config.MAX_UPLOAD + 2 * 1024 * 1024))['status'], 413)
        # Streaming remains bounded even when Content-Length understates the body.
        with patch('backend.config.MAX_UPLOAD', 1024):
            response = asyncio.run(request(1024 * 1024 + 1025, 0))
        self.assertEqual(response['status'], 413)
        self.assertIn(('access-control-allow-origin', 'http://127.0.0.1:3001'),
                      [(key.decode(), value.decode()) for key, value in response['headers']])

    def test_scanner_config_and_failure_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            metadata = {}

            def process(arguments, stdout, stderr, cwd, heartbeat, timeout):
                self.assertGreater(timeout, 0)
                self.assertLessEqual(timeout, 300)
                stdout.write_text('test-version' if '--version' in arguments else '{}', encoding='utf-8')
                return 0 if '--version' in arguments else 2

            with patch('backend.scanner.shutil.which', return_value='test-semgrep'), patch(
                    'backend.scanner.run_process', side_effect=process):
                with self.assertRaises(ValueError):
                    run_method('sast', source, root, lambda: None, metadata=metadata)
            self.assertEqual(metadata['version'], 'test-version')
            self.assertEqual(metadata['exit_code'], 2)
            self.assertEqual(len(metadata['config_sha256']), 64)
            self.assertEqual(metadata['raw_output'], 'sast.json')
            self.assertTrue((root / 'sast-rules.yml').is_file())
            self.assertNotIn(str(root), json.dumps(metadata))

    def test_parser_invalid_outputs_and_sca_deduplication(self):
        for payload in ({}, [], {'results': 'invalid'}, {'results': [], 'errors': [{'message': 'parse failure'}]},
                        {'results': [None]}, {'results': [{'check_id': 'x'}]},
                        {'results': [{'check_id': 'x', 'path': 'app.js', 'start': {'line': 0}, 'extra': {}}]}):
            with self.assertRaises(ValueError):
                parse_results('sast', payload, Path('.'))
        with self.assertRaises(ValueError):
            parse_results('sca', {}, Path('.'))
        vuln = {'id': 'GHSA-test-1', 'summary': 'Controlled advisory',
                'database_specific': {'severity': 'CRITICAL'}, 'aliases': ['CVE-TEST-1'],
                'affected': [{'package': {'name': 'other', 'ecosystem': 'npm'},
                              'ranges': [{'events': [{'fixed': '9.9.9'}]}]}]}
        bundle = {'package': {'name': 'test', 'version': '1.0', 'ecosystem': 'npm'},
                  'vulnerabilities': [vuln], 'groups': [{'ids': ['GHSA-test-1'],
                  'aliases': ['CVE-TEST-1'], 'max_severity': '9.8'}]}
        payload = {'results': [{'source': {'path': 'package-lock.json', 'type': 'lockfile'},
                                'packages': [bundle, bundle]}]}
        findings = parse_results('sca', payload, Path('.'))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'critical')
        self.assertIsNone(findings[0]['detail']['fixed_version'])
        self.assertIn('CVE-TEST-1', findings[0]['detail']['aliases'])
        self.assertEqual(parse_results('sca', {'results': []}, Path('.')), [])
        self.assertEqual(parse_results('sca', {'experimental_config': {}}, Path('.')), [])
        for invalid in ({}, {'results': 'broken'}, {'results': [None]}):
            with self.assertRaises(ValueError):
                parse_results('sca', invalid, Path('.'))
        bundle['groups'] = []
        with self.assertRaises(ValueError):
            parse_results('sca', payload, Path('.'))

    def test_archive_and_risk_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'test.zip'
            archive.write_bytes(zip_bytes({'src/app.js': 'eval(input)', '.semgrepignore': '*'}))
            coverage = inspect_zip(archive, root / 'source')
            self.assertEqual(coverage['source_files'], 1)
            self.assertIn('.semgrepignore', coverage['skipped'])
            archive.write_bytes(zip_bytes({'../escape.js': 'x'}))
            with self.assertRaises(ArchiveError):
                inspect_zip(archive, root / 'unsafe')
        for likelihood in (1, 2, 3):
            for impact in (1, 2, 3):
                score = likelihood * impact
                self.assertEqual(risk_category(score), 'low' if score <= 2 else 'medium' if score <= 4 else 'high')
        with self.assertRaises(ValueError):
            ReviewInput(review_status='confirmed', review_reason='Bukti', likelihood=3)


if __name__ == '__main__':
    unittest.main()
