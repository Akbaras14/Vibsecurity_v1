"""AUTO1 triage, A1 technical priority, and RA1 conditional project-risk analysis."""
import json
import uuid
from .store import query, now
from .project_risk import assess_risk


def assess(finding):
    detail = finding.get('detail', {})
    if isinstance(detail, str):
        detail = json.loads(detail)
    dependency = finding['method'] == 'sca'
    confirmed = dependency and all(detail.get(k) for k in ('package', 'installed_version', 'osv_ids'))
    decision = {
        'engine': 'AUTO1', 'model': 'A1',
        'review_status': 'confirmed' if confirmed else 'investigate',
        'review_reason': ('Kecocokan paket npm, versi terkunci, dan kelompok advisory terdeteksi oleh OSV-Scanner. '
                          'Konfirmasi otomatis ini terbatas pada kecocokan dependensi, bukan keterjangkauan atau eksploitasi.' if confirmed else
                          'Temuan statis diproses otomatis. Keluaran alat belum cukup untuk memastikan alur masukan, kontrol keamanan, dan kesesuaian kondisi rentan.'),
        'risk_reason': 'Risiko penggunaan proyek tidak dinilai otomatis. Keterjangkauan, aset, dan dampak aktual belum dibuktikan.',
        'recommendation': detail.get('remediation') or (
            'Tinjau versi perbaikan pada advisory dan kompatibilitas dependensi.' if dependency else
            'Periksa sumber masukan dan kontrol keamanan pada lokasi kode yang ditunjukkan.'),
        'scenarios': [], 'priority': None,
    }
    # A1 supports complete CVSS v3 base vectors only; absent/other versions stay unscored.
    for entry in detail.get('cvss') or []:
        if not isinstance(entry, dict):
            continue
        vector = entry.get('score', '')
        if not confirmed or not isinstance(vector, str) or not vector.startswith(('CVSS:3.0/', 'CVSS:3.1/')):
            continue
        parts = dict(part.split(':', 1) for part in vector.split('/')[1:] if ':' in part)
        allowed = {'AV': 'NALP', 'AC': 'LH', 'PR': 'NLH', 'UI': 'NR', 'S': 'UC', 'C': 'NLH', 'I': 'NLH', 'A': 'NLH'}
        if any(parts.get(k) not in tuple(v) for k, v in allowed.items()):
            continue
        likelihood = 1 if parts['AV'] in ('L', 'P') or parts['PR'] == 'H' else 3 if (
            parts['AV'] == 'N' and parts['AC'] == 'L' and parts['PR'] == 'N' and parts['UI'] == 'N') else 2
        impact = max({'N': 0, 'L': 2, 'H': 3}[parts[k]] for k in ('C', 'I', 'A'))
        if not impact:
            continue
        candidate = {'likelihood': likelihood, 'impact': impact, 'score': likelihood * impact,
                     'vector': vector, 'basis': 'A1: indikator akses dan CIA advisory CVSS v3; bukan risiko kontekstual R1.'}
        if decision['priority'] is None or (candidate['score'], impact) > (decision['priority']['score'], decision['priority']['impact']):
            decision['priority'] = candidate
    decision['project_risk'] = assess_risk(detail, confirmed)
    decision['risk_reason'] = decision['project_risk']['reason']
    return decision


def assess_scan(db, scan_id):
    scan = query(db, 'SELECT status FROM scans WHERE id=%s FOR UPDATE', (scan_id,)).fetchone()
    if not scan or scan['status'] != 'completed':
        return 0
    rows = query(db, "SELECT * FROM findings WHERE scan_id=%s AND review_status='unreviewed' FOR UPDATE", (scan_id,)).fetchall()
    for finding in rows:
        decision = assess(finding)
        query(db, 'INSERT INTO validation_history(id,finding_id,decision,created_at) VALUES(%s,%s,%s,%s)',
              (uuid.uuid4().hex, finding['id'], json.dumps(decision), now()))
        query(db, '''UPDATE findings SET review_status=%s,review_reason=%s,risk_reason=%s,reviewed_at=%s
                     WHERE id=%s''', (decision['review_status'], decision['review_reason'], decision['risk_reason'], now(), finding['id']))
    return len(rows)
