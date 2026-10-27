"""RA1: conditional inherent-risk scenarios with observed dependency context."""
import hashlib
import json
from pathlib import Path


def dependency_context(finding, source):
    observations = []
    detail = finding['detail']
    if finding['method'] != 'sca':
        return {'policy': 'CTX1', 'observations': [], 'reason': 'Alur input, kontrol, dan aset SAST belum dapat dipastikan otomatis.'}
    root = Path(source).resolve()
    for path in detail.get('paths') or [finding['path']]:
        target = (root / path).resolve()
        if not target.is_relative_to(root) or target.name != 'package-lock.json' or not target.is_file():
            continue
        try:
            raw = target.read_bytes()
            lock = json.loads(raw.decode('utf-8-sig'))
            if lock.get('lockfileVersion') not in (2, 3) or not isinstance(lock.get('packages'), dict):
                continue
            for location, package in lock['packages'].items():
                name = location.rsplit('node_modules/', 1)[-1]
                if name != detail.get('package') or package.get('version') != detail.get('installed_version'):
                    continue
                # devOptional cannot establish a single environment of use.
                scope = 'unknown' if package.get('devOptional') else 'development' if package.get('dev') is True else 'runtime'
                observations.append({'lockfile': path, 'dependency_path': location, 'scope': scope,
                                     'sha256': hashlib.sha256(raw).hexdigest()})
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
            continue
    return {'policy': 'CTX1', 'observations': observations,
            'reason': 'Scope dari metadata package-lock; bukan bukti pemanggilan fungsi atau penerapan produksi.'}


def assess_risk(detail, confirmed):
    context = detail.get('project_context') or {}
    result = {'model': 'RA1', 'status': 'insufficient_evidence', 'kind': 'conditional_inherent',
              'score': None, 'category': 'unassessed', 'scenarios': [], 'context': context,
              'limitations': 'Estimasi risiko inheren bersyarat, bukan risiko residual, probabilitas serangan, atau bukti eksploitasi.'}
    if not confirmed:
        result['reason'] = 'Bukti statis belum cukup untuk mengonfirmasi temuan dan menyusun skenario risiko berskor.'
        return result
    observations = context.get('observations') or []
    for scope in ('runtime', 'development'):
        evidence = [row for row in observations if row['scope'] == scope]
        if not evidence:
            continue
        for entry in detail.get('cvss') or []:
            vector = entry.get('score', '') if isinstance(entry, dict) else ''
            if not isinstance(vector, str) or not vector.startswith(('CVSS:3.0/', 'CVSS:3.1/')):
                continue
            pairs = [part.split(':', 1) for part in vector.split('/')[1:] if ':' in part]
            parts = dict(pairs)
            allowed = {'AV': 'NALP', 'AC': 'LH', 'PR': 'NLH', 'UI': 'NR', 'S': 'UC', 'C': 'NLH', 'I': 'NLH', 'A': 'NLH'}
            if len(pairs) != len(parts) or any(parts.get(k) not in tuple(v) for k, v in allowed.items()):
                continue
            access = 1 if parts['AV'] in ('L', 'P') or parts['PR'] == 'H' else 3 if (
                parts['AV'] == 'N' and parts['AC'] == 'L' and parts['PR'] == 'N' and parts['UI'] == 'N') else 2
            likelihood = min(access, 2) if scope == 'development' else access
            cia = {name: {'N': 0, 'L': 2, 'H': 3}[parts[key]] for key, name in
                   (('C', 'confidentiality'), ('I', 'integrity'), ('A', 'availability'))}
            impact = max(cia.values())
            if not impact:
                continue
            asset = 'Proses, data, dan artefak lingkungan pengembangan/build' if scope == 'development' else 'Proses layanan serta data yang ditangani aplikasi'
            scenario = {'scope': scope, 'asset': asset, 'evidence': evidence, 'vector': vector,
                        'scenario': f"Masukan berbahaya mencapai fungsi rentan {detail['package']}@{detail['installed_version']} pada lingkungan {scope} dan menimbulkan dampak CIA sesuai advisory.",
                        'assumptions': ['Fungsi rentan benar-benar dipanggil dan seluruh prasyarat advisory terpenuhi.',
                                        'Masukan yang dapat dikendalikan penyerang mencapai fungsi rentan.',
                                        'Scope lockfile sesuai lingkungan penggunaan; kontrol tambahan belum diperhitungkan.'],
                        'likelihood': likelihood, **cia, 'impact': impact, 'score': likelihood * impact,
                        'reason': f'RA1: indikator akses CVSS memberi K={access}; ' +
                                  ('scope development membatasi K maksimum 2. ' if scope == 'development' else 'scope runtime memakai indikator akses tersebut. ') +
                                  f'D={impact} adalah maksimum CIA advisory (N=0, L=2, H=3) pada skenario bersyarat ini.'}
            if scope == 'development':
                scenario['assumptions'].append('Lingkungan pengembangan/build memiliki paparan terbatas dan tidak menyediakan layanan produksi publik; batas K=2 hanya berlaku dengan asumsi ini.')
            if scenario not in result['scenarios']:
                result['scenarios'].append(scenario)
    if result['scenarios']:
        chosen = max(result['scenarios'], key=lambda row: (row['score'], row['impact']))
        result.update(status='estimated', score=chosen['score'], likelihood=chosen['likelihood'], impact=chosen['impact'],
                      category='low' if chosen['score'] <= 2 else 'medium' if chosen['score'] <= 4 else 'high',
                      reason='Skor tertinggi dari satu skenario utuh; seluruh asumsi tetap berlaku. RA1 adalah rubrik operasional, bukan rumus resmi NIST/CVSS.')
    else:
        result['reason'] = 'Scope dependensi atau vektor CVSS v3 lengkap belum tersedia; risiko tidak diberi skor dan tidak dianggap rendah.'
    return result
