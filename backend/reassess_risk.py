"""Add RA1 to existing automatic results without replacing manual decisions or frozen samples."""
import json
import tempfile
import uuid
from pathlib import Path
from .archive import inspect_zip
from .automatic import assess
from .config import STORAGE
from .project_risk import dependency_context
from .scanner import sha256
from .store import connect, query, now


def main():
    with connect() as db:
        scans = query(db, """SELECT s.* FROM scans s WHERE s.status='completed' AND NOT EXISTS
            (SELECT 1 FROM research_samples r WHERE r.version_id=s.version_id)""").fetchall()
    updated = 0
    for scan in scans:
        archive = STORAGE / 'scans' / scan['id'] / 'source.zip'
        if not archive.is_file() or sha256(archive) != scan['sha256']:
            continue
        with tempfile.TemporaryDirectory(prefix='risk-', dir=STORAGE) as directory:
            source = Path(directory)
            inspect_zip(archive, source)
            with connect() as db:
                rows = query(db, 'SELECT * FROM findings WHERE scan_id=%s FOR UPDATE', (scan['id'],)).fetchall()
                for row in rows:
                    previous = query(db, 'SELECT decision FROM validation_history WHERE finding_id=%s ORDER BY created_at DESC,id DESC LIMIT 1', (row['id'],)).fetchone()
                    if not previous or json.loads(previous['decision']).get('engine') != 'AUTO1':
                        continue
                    row['detail'] = json.loads(row['detail'])
                    row['detail']['project_context'] = dependency_context(row, source)
                    decision = assess(row)
                    if json.loads(previous['decision']).get('project_risk') == decision['project_risk']:
                        continue
                    query(db, 'UPDATE findings SET detail=%s,risk_reason=%s,reviewed_at=%s WHERE id=%s',
                          (json.dumps(row['detail']), decision['risk_reason'], now(), row['id']))
                    query(db, 'INSERT INTO validation_history(id,finding_id,decision,created_at) VALUES(%s,%s,%s,%s)',
                          (uuid.uuid4().hex, row['id'], json.dumps(decision), now()))
                    updated += 1
    print(f'Analisis RA1 ditambahkan: {updated}. Keputusan manual dan sampel beku dipertahankan.')


if __name__ == '__main__':
    main()
