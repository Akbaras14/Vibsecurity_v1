"""BAB III R1: paired scenarios, immutable decisions and frozen main scans."""
import hashlib
import json
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .store import query, finding_dict, scan_dict


class Scenario(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    scenario: str = Field(min_length=1, max_length=2000)
    asset: str = Field(min_length=1, max_length=1000)
    evidence: str = Field(default='', max_length=4000)
    likelihood: int | None = Field(default=None, ge=1, le=3, strict=True)
    confidentiality: int | None = Field(default=None, ge=1, le=3, strict=True)
    integrity: int | None = Field(default=None, ge=1, le=3, strict=True)
    availability: int | None = Field(default=None, ge=1, le=3, strict=True)
    reason: str = Field(default='', max_length=4000)
    uncertainty: str = Field(default='', max_length=2000)

    @model_validator(mode='after')
    def complete(self):
        impact = max((v or 0 for v in (self.confidentiality, self.integrity, self.availability)))
        if self.likelihood is not None and impact and not self.uncertainty:
            if not self.evidence or not self.reason:
                raise ValueError('Skenario lengkap memerlukan bukti jalur/prasyarat dan alasan K serta CIA.')
        elif not self.uncertainty:
            raise ValueError('Catat alasan ketidakpastian untuk skenario yang belum dapat dinilai.')
        return self


def scenario_result(data):
    result = dict(data)
    impact = max((data.get(key) or 0 for key in ('confidentiality', 'integrity', 'availability')))
    complete = data.get('likelihood') and impact and not data.get('uncertainty')
    result.update(impact=impact or None, score=data['likelihood'] * impact if complete else None)
    return result


def select_scenario(scenarios):
    complete = [scenario_result(item) for item in scenarios]
    return max((item for item in complete if item['score'] is not None),
               key=lambda item: (item['score'], item['impact']), default=None)


def history(db, finding_id):
    rows = query(db, 'SELECT * FROM validation_history WHERE finding_id=%s ORDER BY created_at,id', (finding_id,)).fetchall()
    for row in rows:
        row['decision'] = json.loads(row['decision'])
        row['scenarios'] = [scenario_result(item) for item in query(db,
            'SELECT * FROM risk_scenarios WHERE validation_id=%s ORDER BY position', (row['id'],)).fetchall()]
    return rows


def findings(db, scan_id, include_history=False):
    rows = [finding_dict(row) for row in query(db, 'SELECT * FROM findings WHERE scan_id=%s', (scan_id,)).fetchall()]
    for row in rows:
        decisions = history(db, row['id'])
        row['scenarios'] = decisions[-1]['scenarios'] if decisions else []
        row['automatic'] = decisions[-1]['decision'] if decisions and decisions[-1]['decision'].get('engine') == 'AUTO1' else None
        if include_history:
            row['history'] = decisions
    def priority(row):
        risk = (row.get('automatic') or {}).get('project_risk') or {}
        if risk:
            return (risk.get('score') or 0, risk.get('impact') or 0)
        automatic = (row.get('automatic') or {}).get('priority')
        return (automatic['score'], automatic['impact']) if automatic else (row['risk_score'] or 0, row['impact'] or 0)
    return sorted(rows, key=lambda row: (-priority(row)[0], -priority(row)[1], row['method'], row['path'], row['source_id'], row['id']))


def manifest_hash(manifest):
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def matches(scan, manifest):
    return scan['status'] == 'completed' and all(
        all(scan['methods'].get(method, {}).get(key) == value for key, value in settings.items())
        for method, settings in manifest['methods'].items())


def main_scans(db):
    result = []
    samples = query(db, '''SELECT r.*,p.sample_group,p.name AS project_name,c.manifest FROM research_samples r
        JOIN projects p ON p.id=r.project_id JOIN research_protocol c ON c.id=r.protocol_id WHERE p.deleting=0''').fetchall()
    for sample in samples:
        manifest = json.loads(sample['manifest'])
        for row in query(db, 'SELECT * FROM scans WHERE version_id=%s ORDER BY created_at,id', (sample['version_id'],)).fetchall():
            scan = scan_dict(row)
            if matches(scan, manifest):
                scan.update(sample_group=sample['sample_group'], project_name=sample['project_name'])
                result.append(scan)
                break
    return result
