"""Run with: python -m backend.worker. One durable queue, one active scan."""
import json
import logging
import shutil
import time
import pymysql
from datetime import datetime, timedelta, timezone

from .archive import inspect_zip
from .config import STORAGE, ROOT
from .migrate import lock_name
from .scanner import readiness, run_method, sha256
from .store import connect, initialize, now, query
from .automatic import assess_scan
from .translation import translate_finding
from .project_risk import dependency_context

logger = logging.getLogger('vibesec.worker')


def overall_status(methods):
    statuses = [method['status'] for method in methods.values()]
    if 'running' in statuses or 'queued' in statuses:
        return 'running'
    if all(status == 'completed' for status in statuses):
        return 'completed'
    if 'completed' in statuses:
        return 'partial'
    return 'failed' if 'failed' in statuses else 'unsupported'


def recover_interrupted(root):
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=45)).isoformat()
    with connect() as db:
        for scan in query(db, "SELECT * FROM scans WHERE status='running' AND (heartbeat_at IS NULL OR heartbeat_at<%s)", (cutoff,)).fetchall():
            methods = json.loads(scan['methods'])
            for method in methods.values():
                if method['status'] in ('running', 'queued'):
                    method.update(status='failed', error='Worker terputus. Unggah snapshot untuk mencoba ulang.')
            error = 'Worker terputus.'
            directory = (root / 'scans' / scan['id'] / 'extracted').resolve()
            if directory.is_relative_to((root / 'scans').resolve()) and directory.exists():
                try:
                    shutil.rmtree(directory)
                except OSError:
                    error += ' Pembersihan direktori sementara gagal; periksa izin filesystem.'
            query(db, 'UPDATE scans SET status=%s, methods=%s, error=%s, finished_at=%s WHERE id=%s',
                       (overall_status(methods), json.dumps(methods), error, now(), scan['id']))


def claim_scan(root):
    with connect() as db:
        # ponytail: one active scan per installation; add per-worker leases for parallel scanning.
        if query(db, "SELECT 1 FROM scans WHERE status='running'").fetchone():
            return None
        row = query(db, "SELECT * FROM scans WHERE status='queued' ORDER BY created_at LIMIT 1 FOR UPDATE").fetchone()
        if row:
            query(db, "UPDATE scans SET status='running',started_at=%s,heartbeat_at=%s WHERE id=%s", (now(), now(), row['id']))
            return dict(row)
    return None


def process_scan(root, scan, lease=None):
    scan_id = scan['id']
    directory = root / 'scans' / scan_id
    methods = json.loads(scan['methods'])
    logger.info('scan=%s phase=started', scan_id)

    def heartbeat():
        if lease is not None:
            query(lease, 'SELECT 1').fetchone()
        with connect() as db:
            query(db, 'UPDATE scans SET heartbeat_at=%s WHERE id=%s', (now(), scan_id))

    def save_methods():
        with connect() as db:
            query(db, 'UPDATE scans SET methods=%s,heartbeat_at=%s WHERE id=%s', (json.dumps(methods), now(), scan_id))

    try:
        if sha256(directory / 'source.zip') != scan['sha256']:
            raise ValueError('Hash arsip berubah; snapshot tidak dapat dipercaya.')
        source = directory / 'extracted'
        if source.exists():
            shutil.rmtree(source)
        coverage = inspect_zip(directory / 'source.zip', source)
        with connect() as db:
            query(db, 'UPDATE scans SET coverage=%s WHERE id=%s', (json.dumps(coverage), scan_id))
        for method in ('sast', 'sca'):
            started = time.monotonic()
            metadata = {'started_at': now(), 'assessment_policy': 'AUTO1/A1/RA1/CTX1',
                        'risk_policy_sha256': sha256(ROOT / 'backend' / 'project_risk.py')}
            heartbeat()
            reasons = readiness(method)['reasons']
            if coverage[f'{method}_reason']:
                methods[method] = {'status': 'unsupported', 'error': coverage[f'{method}_reason']}
            elif reasons:
                methods[method] = {'status': 'failed', 'error': ' '.join(reasons)}
            else:
                methods[method] = {'status': 'running'}
                save_methods()
                try:
                    result_metadata, findings = run_method(method, source, directory, heartbeat, metadata=metadata)
                    metadata.update(result_metadata)
                    for finding in findings:
                        finding['detail']['project_context'] = dependency_context(finding, source)
                        translate_finding(finding, heartbeat)
                    with connect() as db:
                        for finding in findings:
                            query(db, '''INSERT INTO findings(id,scan_id,method,source_id,title,severity,path,detail,review_reason,risk_reason)
                                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'','')''',
                                (finding['id'], scan_id, finding['method'], finding['source_id'], finding['title'],
                                 finding['severity'], finding['path'], json.dumps(finding['detail'])))
                        methods[method] = {'status': 'completed', **metadata, 'finding_count': len(findings)}
                        query(db, 'UPDATE scans SET methods=%s,heartbeat_at=%s WHERE id=%s', (json.dumps(methods), now(), scan_id))
                except (ValueError, KeyError, TypeError, OSError, TimeoutError) as error:
                    # Parser/config errors are safe summaries; never publish raw stderr or environment.
                    message = str(error) if isinstance(error, (ValueError, TimeoutError)) else 'Keluaran scanner tidak valid atau proses tidak dapat dijalankan.'
                    methods[method] = {'status': 'failed', **metadata, 'error': message[:1000]}
            methods[method].update(started_at=metadata['started_at'], finished_at=now(),
                                   duration_seconds=round(time.monotonic() - started, 2))
            logger.info('scan=%s phase=%s status=%s duration_seconds=%s', scan_id, method,
                        methods[method]['status'], methods[method]['duration_seconds'])
            save_methods()
    except (ValueError, OSError) as error:
        message = str(error) if isinstance(error, ValueError) else 'Artefak scan tidak dapat dibaca atau diekstrak.'
        for method in methods.values():
            if method['status'] in ('queued', 'running'):
                method.update(status='failed', error=message[:1000])
    finally:
        cleanup_error = None
        try:
            if (directory / 'extracted').exists():
                shutil.rmtree(directory / 'extracted')
        except OSError:
            cleanup_error = 'Pembersihan direktori sementara gagal; periksa izin filesystem.'
        manifest = {'scan_id': scan_id, 'version_id': scan.get('version_id'), 'archive_sha256': scan['sha256'],
                    'methods': methods, 'assessment_policy': 'AUTO1/A1/RA1', 'contextual_risk': 'conditional_inherent', 'context_policy': 'CTX1'}
        try:
            (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        except OSError:
            cleanup_error = 'Manifest pemeriksaan gagal disimpan; jangan gunakan sebagai pemeriksaan utama.'
        with connect() as db:
            query(db, 'UPDATE scans SET status=%s,methods=%s,finished_at=%s,error=%s WHERE id=%s',
                       ('failed' if cleanup_error else overall_status(methods), json.dumps(methods), now(), cleanup_error, scan_id))
            assess_scan(db, scan_id)
        logger.info('scan=%s phase=finished status=%s cleanup_failed=%s',
                    scan_id, overall_status(methods), bool(cleanup_error))


def work_session():
    initialize(STORAGE)
    # A MySQL session lock covers all workers connected to the same database.
    with connect() as lease:
        query(lease, 'SET SESSION wait_timeout=120')
        if query(lease, 'SELECT GET_LOCK(%s, 5) AS acquired', (lock_name('worker'),)).fetchone()['acquired'] != 1:
            logger.warning('Menunggu kunci worker lain dilepas.')
            return
        # We hold the exclusive worker lock: any remaining running scan is interrupted.
        with connect() as db:
            query(db, "UPDATE scans SET heartbeat_at=NULL WHERE status='running'")
        recover_interrupted(STORAGE)
        print('VibeSec worker aktif. Satu scan diproses setiap giliran.', flush=True)
        try:
            while True:
                query(lease, 'SELECT 1').fetchone()
                scan = claim_scan(STORAGE)
                if scan:
                    process_scan(STORAGE, scan, lease=lease)
                    print(f"Scan {scan['id']} selesai diproses.", flush=True)
                else:
                    time.sleep(2)
        except KeyboardInterrupt:
            print('Worker berhenti. Scan terputus dipulihkan saat restart.', flush=True)
            raise


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        while True:
            try:
                work_session()
            except (pymysql.OperationalError, pymysql.InterfaceError):
                logger.warning('Koneksi MySQL terputus/tidak tersedia; mencoba kembali dalam 5 detik.')
            time.sleep(5)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
