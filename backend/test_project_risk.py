import json
import tempfile
import unittest
from pathlib import Path
from .automatic import assess
from .project_risk import dependency_context


class ProjectRiskCheck(unittest.TestCase):
    def finding(self):
        return {'method': 'sca', 'path': 'package-lock.json', 'detail': {'package': 'example', 'installed_version': '1.0',
                'osv_ids': ['GHSA-test'], 'cvss': [{'score': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:H'}]}}

    def test_scope_changes_scenario_and_score_without_changing_cvss_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            finding = self.finding()
            lock = {'lockfileVersion': 3, 'packages': {'node_modules/example': {'version': '1.0', 'dev': True}}}
            for development, expected in ((True, 6), (False, 9)):
                lock['packages']['node_modules/example']['dev'] = development
                (root / 'package-lock.json').write_text(json.dumps(lock))
                finding['detail']['project_context'] = dependency_context(finding, root)
                decision = assess(finding)
                risk = decision['project_risk']
                self.assertEqual(risk['score'], expected)
                self.assertEqual(decision['priority']['score'], 9)
                self.assertTrue(risk['scenarios'][0]['assumptions'])
                self.assertEqual(risk['scenarios'][0]['integrity'], 0)
                self.assertEqual(len(risk['scenarios'][0]['evidence'][0]['sha256']), 64)
                self.assertIn('build' if development else 'layanan', risk['scenarios'][0]['asset'])

    def test_missing_or_ambiguous_context_and_other_cvss_versions_stay_unscored(self):
        finding = self.finding()
        self.assertIsNone(assess(finding)['project_risk']['score'])
        finding['detail']['project_context'] = {'observations': [{'scope': 'unknown'}]}
        self.assertIsNone(assess(finding)['project_risk']['score'])
        finding['detail']['project_context'] = {'observations': [{'scope': 'runtime'}]}
        for vector in ('CVSS:4.0/AV:N', 'CVSS:3.1/AV:N', 'CVSS:3.1/AV:N/AV:L/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H'):
            finding['detail']['cvss'] = [{'score': vector}]
            self.assertIsNone(assess(finding)['project_risk']['score'])
        finding['method'] = 'sast'
        self.assertIsNone(assess(finding)['project_risk']['score'])

    def test_exact_version_scope_and_archive_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            finding = self.finding()
            lock = {'lockfileVersion': 3, 'packages': {'node_modules/example': {'version': '2.0'}}}
            (root / 'package-lock.json').write_text(json.dumps(lock))
            self.assertEqual(dependency_context(finding, root)['observations'], [])
            finding['path'] = '../package-lock.json'
            self.assertEqual(dependency_context(finding, root)['observations'], [])
