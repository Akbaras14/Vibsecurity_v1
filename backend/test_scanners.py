"""Opt-in compatibility checks against real offline scanners; never run uploaded code."""
import json
import os
import sys
import socket
import tempfile
import unittest
from pathlib import Path

from .scanner import memory_cgroup, run_method, run_process


@unittest.skipUnless(os.environ.get('VIBESEC_TEST_SCANNERS') == '1',
                     'Set VIBESEC_TEST_SCANNERS=1 on the Linux scanner host.')
class ScannerCheck(unittest.TestCase):
    def test_scanner_keeps_parent_database_connection(self):
        from .store import connect, query
        with connect() as db, tempfile.TemporaryDirectory() as temporary:
            db.connection._read_timeout = 3
            self.assertEqual(query(db, 'SELECT 1 AS ok').fetchone()['ok'], 1)
            root = Path(temporary)
            self.assertEqual(run_process([sys.executable, '-c', 'print(1)'], root / 'out', root / 'err',
                                        root, lambda: None, timeout=5), 0)
            self.assertEqual(query(db, 'SELECT 1 AS ok').fetchone()['ok'], 1)

    def test_memory_limit_is_enforced(self):
        group = memory_cgroup()
        if (group / 'cgroup.procs').read_text().strip():
            self.skipTest('Stop active scanners before the memory enforcement test.')
        control = group / 'memory.oom_control'
        if not control.is_file():
            self.skipTest('This host enforcement check uses the tested cgroup-v1 counters.')
        before = dict(line.split() for line in control.read_text().splitlines())['oom_kill']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            code = run_process([sys.executable, '-c', 'bytearray(3 * 1024**3)'],
                               root / 'stdout', root / 'stderr', root, lambda: None, timeout=30)
            self.assertNotEqual(code, 0, 'Scanner must not allocate more than its 2 GB RAM cap.')
            after = dict(line.split() for line in control.read_text().splitlines())['oom_kill']
            self.assertGreater(int(after), int(before))

    def test_firewall_blocks_ipv4_and_ipv6(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for family, host in ((socket.AF_INET, '127.0.0.1'), (socket.AF_INET6, '::1')):
                with self.subTest(host=host), socket.socket(family) as server:
                    server.bind((host, 0))
                    server.listen(5)
                    port = server.getsockname()[1]
                    with socket.create_connection((host, port), timeout=1):
                        pass
                    code = run_process([sys.executable, '-c',
                        'import socket,sys\n'
                        'try:\n socket.create_connection((sys.argv[1],int(sys.argv[2])),timeout=1)\n'
                        'except TimeoutError:\n sys.exit(0)\n'
                        'sys.exit(1)\n', host, str(port)],
                        root / 'stdout', root / 'stderr', root, lambda: None, timeout=10)
                    self.assertEqual(code, 0, 'Only scanner traffic must be blocked by firewall.')

    def test_process_limits_and_timeout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, errors = root / 'limits.json', root / 'errors.txt'
            code = run_process([sys.executable, '-c',
                'import os,resource; '
                'assert len(os.sched_getaffinity(0)) <= 2; '
                'assert resource.getrlimit(resource.RLIMIT_CPU) == (300,300); '
                'assert resource.getrlimit(resource.RLIMIT_NPROC) == (128,128); '
                'assert "VIBESEC_MYSQL_PASSWORD" not in os.environ'],
                output, errors, root, lambda: None, timeout=10)
            self.assertEqual(code, 0, errors.read_text())
            with self.assertRaises(TimeoutError):
                run_process([sys.executable, '-c',
                    'import subprocess,sys,time; '
                    'child=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"]); '
                    'print(child.pid,flush=True); time.sleep(60)'],
                    output, errors, root, lambda: None, timeout=1)
            child = int(output.read_text().strip())
            status = Path(f'/proc/{child}/stat')
            self.assertTrue(not status.exists() or status.read_text().split()[2] == 'Z',
                            'Timeout must stop child processes too.')

    def test_real_sast_and_sca(self):
        self.assertEqual(os.name, 'posix', 'Use Linux/WSL for process limits.')
        self.assertNotEqual(os.geteuid(), 0, 'Run scanners without root privileges.')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            (source / 'app.js').write_text('eval(location.search);\n', encoding='utf-8')
            (source / 'package-lock.json').write_text(json.dumps({
                'name': 'vibesec-controlled-test', 'version': '1.0.0', 'lockfileVersion': 3,
                'packages': {'': {'name': 'vibesec-controlled-test', 'version': '1.0.0',
                                  'dependencies': {'lodash': '4.17.20'}},
                             'node_modules/lodash': {'version': '4.17.20',
                                 'resolved': 'https://registry.npmjs.org/lodash/-/lodash-4.17.20.tgz'}}
            }), encoding='utf-8')
            for method in ('sast', 'sca'):
                with self.subTest(method=method):
                    output = root / method
                    output.mkdir()
                    try:
                        metadata, findings = run_method(method, source, output, lambda: None)
                    except (ValueError, TimeoutError):
                        # Only controlled fixture output, never uploaded source or credentials.
                        errors = output / f'{method}.stderr'
                        if errors.exists():
                            print(errors.read_text(encoding='utf-8', errors='replace')[-6000:])
                        raise
                    self.assertTrue(metadata['version'])
                    self.assertIn(metadata['exit_code'], (0, 1))
                    self.assertTrue(findings, 'Controlled vulnerable sample must produce findings.')
                    if method == 'sast':
                        self.assertTrue(any(item['source_id'].endswith('detect-eval-with-expression')
                                            and item['detail']['line'] == 1 for item in findings))
                    else:
                        self.assertTrue(any(item['detail']['package'] == 'lodash'
                                            and item['detail']['installed_version'] == '4.17.20'
                                            for item in findings))
                    print(json.dumps({'method': method, 'metadata': metadata,
                                      'finding_count': len(findings)}, ensure_ascii=False))
                    if method == 'sast':
                        (source / 'app.js').write_text('const answer = 42;\n', encoding='utf-8')
                    else:
                        (source / 'package-lock.json').write_text(json.dumps({
                            'name': 'vibesec-clean-test', 'version': '1.0.0', 'lockfileVersion': 3,
                            'packages': {'': {'name': 'vibesec-clean-test', 'version': '1.0.0'}}
                        }), encoding='utf-8')
                    clean_output = root / f'{method}-clean'
                    clean_output.mkdir()
                    clean_metadata, clean_findings = run_method(method, source, clean_output, lambda: None)
                    self.assertEqual(clean_metadata['exit_code'], 0)
                    self.assertEqual(clean_findings, [])


if __name__ == '__main__':
    unittest.main()
