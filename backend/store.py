import json
import pymysql
from contextlib import contextmanager
from datetime import datetime, timezone
from .config import mysql_settings


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect(*, multi_statements=False):
    flags = pymysql.constants.CLIENT.MULTI_STATEMENTS if multi_statements else 0
    db = pymysql.connect(**mysql_settings(), cursorclass=pymysql.cursors.DictCursor, client_flag=flags)
    try:
        with db.cursor() as cursor:
            yield cursor
        db.commit()
    except BaseException:
        try:
            db.rollback()
        except pymysql.MySQLError:
            pass  # Preserve the original error when the connection is already lost.
        raise
    finally:
        db.close()


def query(cursor, sql, parameters=None):
    cursor.execute(sql, parameters)
    return cursor


def initialize(root):
    from .migrate import migrate
    return migrate(root)


def scan_dict(row):
    result = dict(row)
    result['coverage'] = json.loads(result['coverage'])
    result['methods'] = json.loads(result['methods'])
    return result


def finding_dict(row):
    result = dict(row)
    result.update(json.loads(result.pop('detail')))
    score = result['likelihood'] * result['impact'] if result['review_status'] == 'confirmed' and result['likelihood'] and result['impact'] else None
    result['risk_score'] = score
    result['risk'] = risk_category(score)
    return result


def risk_category(score):
    if score is None:
        return 'unassessed'
    return 'low' if score <= 2 else 'medium' if score <= 4 else 'high'


def summary(findings):
    severity = {key: 0 for key in ('critical', 'high', 'medium', 'low', 'unknown')}
    methods = {'sast': 0, 'sca': 0}
    reviews = {key: 0 for key in ('unreviewed', 'confirmed', 'false_positive', 'investigate')}
    risks = {key: 0 for key in ('high', 'medium', 'low', 'unassessed')}
    for finding in findings:
        severity[finding['severity']] += 1
        methods[finding['method']] += 1
        reviews[finding['review_status']] += 1
        if finding['review_status'] == 'confirmed':
            risks[finding['risk']] += 1
    highest = next((key for key in ('high', 'medium', 'low') if risks[key]), 'unassessed')
    automatic = [f['automatic'] for f in findings if f.get('automatic')]
    priorities = {k: 0 for k in ('high', 'medium', 'low', 'unassessed')}
    for decision in automatic:
        priorities[risk_category(decision['priority']['score'] if decision.get('priority') else None)] += 1
    project_risks = {k: 0 for k in ('high', 'medium', 'low', 'unassessed')}
    for finding in findings:
        assessment = (finding.get('automatic') or {}).get('project_risk') or {}
        project_risks[assessment.get('category', 'unassessed')] += 1
    estimated = sum(project_risks[k] for k in ('high', 'medium', 'low'))

    return {'risk_analysis': {'model': 'RA1', 'categories': project_risks, 'estimated': estimated, 'percentages': {k: round(project_risks[k] / estimated * 100, 2) if estimated else None for k in ('high', 'medium', 'low')}, 'highest': next((k for k in ('high', 'medium', 'low') if project_risks[k]), 'unassessed'), 'conditional': True} if any(item.get('project_risk') for item in automatic) else None, 'automatic': {'processed': len(automatic), 'priorities': priorities, 'highest_priority': next((k for k in ('high', 'medium', 'low') if priorities[k]), 'unassessed')}, 'total': len(findings), 'severity': severity, 'methods': methods,
            'reviews': reviews, 'risks': risks, 'highest_risk': highest,
            'review_percentages': {k: round(v / (len(findings) - reviews['unreviewed']) * 100, 2) if len(findings) != reviews['unreviewed'] else None for k, v in reviews.items() if k != 'unreviewed'},
            'risk_percentages': {k: round(v / sum(risks[r] for r in ('high', 'medium', 'low')) * 100, 2) if sum(risks[r] for r in ('high', 'medium', 'low')) else None for k, v in risks.items() if k != 'unassessed'},
            'provisional': bool(risks['unassessed']), 'excluded_from_risk': len(findings) - reviews['confirmed']}
