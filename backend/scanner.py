import hashlib
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from .config import EXCLUDED

RULES = Path(os.environ.get('VIBESEC_RULES', Path(__file__).parent / 'rules' / 'research.yml')).resolve()
OSV_CACHE = Path(os.environ.get('VIBESEC_OSV_CACHE', Path(__file__).parent.parent / 'storage' / 'osv')).resolve()
TIMEOUT = 300


def memory_cgroup():
    configured = os.environ.get('VIBESEC_MEMORY_CGROUP')
    if not configured:
        raise ValueError('VIBESEC_MEMORY_CGROUP belum disiapkan untuk batas RAM scanner 2 GB.')
    group = Path(configured).resolve()
    limit_file = group / 'memory.max' if (group / 'memory.max').is_file() else group / 'memory.limit_in_bytes'
    try:
        limit = int(limit_file.read_text().strip())
        if not 0 < limit <= 2 * 1024**3 or not os.access(group / 'cgroup.procs', os.W_OK):
            raise ValueError()
    except (OSError, ValueError):
        raise ValueError('Cgroup scanner harus membatasi RAM maksimal 2 GB dan mengizinkan worker bergabung.') from None
    return group


def network_cgroup():
    # shortcut: firewall uses v1 net_cls; add a tested v2 firewall before supporting pure v2 hosts.
    configured = os.environ.get('VIBESEC_NETWORK_CGROUP')
    if not configured:
        raise ValueError('VIBESEC_NETWORK_CGROUP belum disiapkan untuk firewall scanner.')
    group = Path(configured).resolve()
    try:
        if int((group / 'net_cls.classid').read_text().strip(), 0) != 0x100001 or not os.access(group / 'cgroup.procs', os.W_OK):
            raise ValueError()
    except (OSError, ValueError):
        raise ValueError('Cgroup jaringan scanner tidak valid atau tidak dapat diakses.') from None
    return group


def readiness(method=None):
    tools = {name: shutil.which(os.environ.get(f'VIBESEC_{name.upper().replace("-", "_")}', name)) for name in ('semgrep', 'osv-scanner')}
    reasons = []
    if os.name != 'posix':
        reasons.append('Scanner memerlukan host Linux/WSL untuk pembatasan proses OS yang didukung.')
    elif hasattr(os, 'geteuid') and os.geteuid() == 0:
        reasons.append('Worker tidak boleh berjalan sebagai root.')
    if os.name == 'posix':
        try:
            memory_cgroup()
            network_cgroup()
        except ValueError as error:
            reasons.append(str(error))
    if os.environ.get('VIBESEC_SCANNER_HOST_READY') != '1':
        reasons.append('Setup firewall/batas OS host belum dikonfirmasi. Lihat README sebelum mengaktifkan worker.')
    selected = ('semgrep',) if method == 'sast' else ('osv-scanner',) if method == 'sca' else tuple(tools)
    for name in selected:
        executable = tools[name]
        if not executable:
            reasons.append(f'Executable {name} belum terpasang atau tidak ditemukan.')
    if 'semgrep' in selected and not RULES.is_file():
        reasons.append('Ruleset SAST lokal belum tersedia.')
    if 'osv-scanner' in selected and (not (OSV_CACHE / 'osv-scalibr/npm/all.zip').is_file() or not (OSV_CACHE / 'metadata.json').is_file()):
        reasons.append('Snapshot advisory npm OSV belum tersedia. Siapkan sebelum scan offline.')
    return {'ready': not reasons, 'reasons': reasons,
            'tools': {name: bool(path) for name, path in tools.items()}}


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(value, source):
    value = str(value or '').replace('\\', '/')
    path = Path(value)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(source.resolve()).as_posix()
        except ValueError:
            raise ValueError('Scanner mengembalikan path di luar snapshot.') from None
    if '..' in path.parts:
        raise ValueError('Scanner mengembalikan path tidak valid.')
    return value.removeprefix('./')


def parse_results(method, payload, source):
    if method not in ('sast', 'sca'):
        raise ValueError('Metode scanner tidak didukung.')
    try:
        return _parse_results(method, payload, source)
    except (KeyError, TypeError, AttributeError):
        raise ValueError('Struktur temuan scanner tidak valid; hasil tidak dianggap bersih.') from None


def _parse_results(method, payload, source):
    """Accept structured output only; malformed output never becomes a clean scan."""
    findings, seen, source_lines = [], {}, {}

    def append(source_id, title, severity, path, detail, identity):
        if not all(isinstance(value, str) and value for value in (source_id, title, path)):
            raise ValueError('Identitas atau lokasi temuan scanner tidak valid.')
        if identity in seen:
            if method == 'sca':
                previous = seen[identity]['detail']
                previous['paths'] = sorted(set(previous['paths']) | {path})
                previous['aliases'] = sorted(set(previous['aliases']) | set(detail['aliases']))
            return
        finding = {'id': uuid.uuid4().hex, 'method': method, 'source_id': source_id,
                   'title': title, 'severity': severity, 'path': path, 'detail': detail}
        seen[identity] = finding
        findings.append(finding)

    if not isinstance(payload, dict):
        raise ValueError('Keluaran scanner bukan objek JSON.')
    if method == 'sast':
        if not isinstance(payload.get('results'), list) or not isinstance(payload.get('errors', []), list):
            raise ValueError('Struktur keluaran Semgrep tidak valid.')
        if payload.get('errors'):
            raise ValueError('Semgrep melaporkan error analisis. Periksa keluaran mentah sebelum mengulang scan.')
        for result in payload['results']:
            rule = result['check_id']
            path = relative_path(result['path'], source)
            extra, line = result['extra'], result['start']['line']
            if type(line) is not int or line < 1:
                raise ValueError('Nomor baris temuan scanner tidak valid.')
            severity = {'ERROR': 'high', 'WARNING': 'medium', 'INFO': 'low'}.get(extra.get('severity'), 'unknown')
            metadata = extra.get('metadata') or {}
            snippet = extra.get('lines')
            snippet_source = 'scanner'
            target = (source / path).resolve()
            if target.is_relative_to(source.resolve()) and target.is_file():
                if path not in source_lines:
                    source_lines[path] = target.read_text(encoding='utf-8', errors='replace').splitlines()
                end = result.get('end', {}).get('line', line)
                end = end if type(end) is int and end >= line else line
                snippet = '\n'.join(source_lines[path][line - 1:min(end, line + 19)])[:8000]
                snippet_source = 'snapshot'
            elif snippet == 'requires login':
                snippet = None
            append(rule, extra.get('message', rule), severity, path,
                   {'line': line, 'start_col': result['start'].get('col'), 'end_col': result.get('end', {}).get('col'), 'end_line': result.get('end', {}).get('line'),
                    'snippet': snippet, 'snippet_source': snippet_source, 'severity_original': extra.get('severity'),
                    'references': metadata.get('references', []), 'cwe': metadata.get('cwe', []),
                    'remediation': extra.get('fix') or metadata.get('remediation')},
                   (rule, path, line, result['start'].get('col'), result.get('end', {}).get('line'), result.get('end', {}).get('col')))
    else:
        results = payload.get('results')
        if results is None and isinstance(payload.get('experimental_config'), dict):
            results = []
        if not isinstance(results, list):
            raise ValueError('Struktur keluaran OSV-Scanner tidak valid.')
        for result in results:
            path = relative_path(result['source']['path'], source)
            if result['source']['type'] != 'lockfile' or not isinstance(result['packages'], list):
                raise ValueError('Sumber keluaran OSV tidak sesuai cakupan lockfile.')
            for bundle in result['packages']:
                package = bundle['package']['name']
                version = bundle['package']['version']
                if bundle['package']['ecosystem'] != 'npm' or not all(isinstance(value, str) and value for value in (package, version)):
                    raise ValueError('Identitas paket OSV tidak valid atau di luar cakupan npm.')
                vulnerabilities = bundle.get('vulnerabilities') or []
                groups = bundle.get('groups') or []
                if not isinstance(vulnerabilities, list) or not isinstance(groups, list):
                    raise ValueError('Daftar advisory OSV tidak valid.')
                by_id = {vuln['id']: vuln for vuln in vulnerabilities}
                covered = set()
                for group in groups:
                    ids = group['ids']
                    if not isinstance(ids, list) or not ids or any(value not in by_id for value in ids):
                        raise ValueError('Kelompok alias advisory OSV tidak valid.')
                    covered.update(ids)
                    advisory = ids[0]
                    vuln = by_id[advisory]
                    originals = [by_id[value] for value in ids]
                    raw_severity = (vuln.get('database_specific') or {}).get('severity')
                    severity = {'CRITICAL': 'critical', 'HIGH': 'high', 'MODERATE': 'medium', 'MEDIUM': 'medium', 'LOW': 'low'}.get(str(raw_severity).upper(), 'unknown')
                    score = group.get('max_severity')
                    if score == '':
                        score = None
                    if score not in (None, ''):
                        score = float(score)
                        if not 0 <= score <= 10:
                            raise ValueError('Skor CVSS OSV tidak valid.')
                        severity = 'critical' if score >= 9 else 'high' if score >= 7 else 'medium' if score >= 4 else 'low'
                    fixed = sorted({event['fixed'] for item in originals for affected in item.get('affected', [])
                                    if affected.get('package', {}).get('name') == package and affected['package'].get('ecosystem') == 'npm'
                                    for span in affected.get('ranges', []) for event in span.get('events', []) if event.get('fixed')})
                    aliases = sorted(set(group.get('aliases') or []) | set(ids))
                    append(advisory, vuln.get('summary') or advisory, severity, path,
                           {'package': package, 'ecosystem': 'npm', 'paths': [path], 'installed_version': version, 'fixed_version': ', '.join(fixed) or None,
                            'severity_original': raw_severity, 'description': vuln.get('details'), 'aliases': aliases,
                            'references': sorted({ref['url'] for item in originals for ref in item.get('references', [])}),
                            'cvss': [entry for item in originals for entry in item.get('severity', [])], 'cvss_score': score,
                            'severity_source': 'OSV-Scanner group.max_severity' if score is not None else 'OSV database_specific.severity',
                            'cwe': sorted({value for item in originals for value in (item.get('database_specific') or {}).get('cwe_ids', [])}),
                            'advisory_modified': vuln.get('modified'), 'advisory_published': vuln.get('published'), 'osv_ids': ids},
                           (tuple(sorted(ids)), 'npm', package, version))
                if covered != set(by_id):
                    raise ValueError('Tidak semua advisory OSV tercakup kelompok alias.')
    return findings


def process_limits(group, network):
    import resource
    # net_cls can reclassify inherited sockets: close child copies before joining it.
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            socket = os.readlink(descriptor).startswith('socket:')
        except FileNotFoundError:
            continue
        if socket:
            os.close(int(descriptor.name))
    # Limit resident memory for the entire scanner tree, not virtual address mappings.
    (group / 'cgroup.procs').write_text(str(os.getpid()))
    (network / 'cgroup.procs').write_text(str(os.getpid()))
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT, TIMEOUT))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NPROC, (128, 128))
    if hasattr(os, 'sched_getaffinity'):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])


def run_process(arguments, stdout, stderr, cwd, heartbeat, timeout=TIMEOUT):
    # Worker is a single-threaded process; preexec_fn only runs on Linux/WSL.
    environment = {key: value for key, value in os.environ.items()
                   if key in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'VIRTUAL_ENV', 'TMPDIR', 'SSL_CERT_FILE')}
    environment.update(SEMGREP_SEND_METRICS='off', SEMGREP_ENABLE_VERSION_CHECK='0', OMP_NUM_THREADS='2')
    group = memory_cgroup()
    network = network_cgroup()
    with stdout.open('wb') as output, stderr.open('wb') as errors:
        try:
            process = subprocess.Popen(arguments, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                                       cwd=cwd, env=environment, shell=False,
                                       start_new_session=True, preexec_fn=lambda: process_limits(group, network))
        except subprocess.SubprocessError:
            raise OSError('Pembatasan proses scanner tidak dapat diterapkan.') from None
        started = time.monotonic()
        try:
            while process.poll() is None:
                heartbeat()
                if time.monotonic() - started > timeout:
                    raise TimeoutError(f'Proses scanner melampaui batas {timeout:g} detik.')
                time.sleep(1)
            return process.returncode
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()


def run_method(method, source, directory, heartbeat, metadata=None):
    if method not in ('sast', 'sca'):
        raise ValueError('Metode scanner tidak didukung.')
    if method == 'sast':
        return _run_method(method, source, directory, heartbeat, metadata)
    # Only npm lockfiles enter SCA; other manifests cannot expand research scope.
    lockfiles = [path for path in source.rglob('package-lock.json') if path.is_file()]
    with tempfile.TemporaryDirectory(prefix='sca-input-', dir=source) as temporary:
        scoped = Path(temporary)
        for lockfile in lockfiles:
            target = scoped / lockfile.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(lockfile, target)
        return _run_method(method, scoped, directory, heartbeat, metadata)


def _run_method(method, source, directory, heartbeat, metadata=None):
    method_started = time.monotonic()
    tool = 'semgrep' if method == 'sast' else 'osv-scanner'
    executable = shutil.which(os.environ.get(f'VIBESEC_{tool.upper().replace("-", "_")}', tool))
    raw, errors = directory / f'{method}.json', directory / f'{method}.stderr'
    version_file = directory / f'{method}.version.txt'
    metadata = metadata if metadata is not None else {}
    metadata.update(tool=tool, raw_output=raw.name, stderr_output=errors.name,
                    excluded_directories=sorted(EXCLUDED))
    code = run_process([executable, '--version'], version_file, errors, directory, heartbeat,
                       timeout=min(60, TIMEOUT))
    if code != 0:
        raise ValueError(f'Versi {tool} tidak dapat dibaca.')
    metadata['version'] = version_file.read_text(encoding='utf-8')[:1000].strip()
    if method == 'sca' and 'osv-scanner version: 2.' not in metadata['version']:
        raise ValueError('Penelitian memerlukan OSV-Scanner versi 2.')
    if method == 'sast':
        rules_snapshot = directory / 'sast-rules.yml'
        shutil.copyfile(RULES, rules_snapshot)
        metadata['rules_sha256'] = sha256(rules_snapshot)
        manifest_path = RULES.with_name('research-manifest.json')
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            if manifest['sha256'] != metadata['rules_sha256']:
                raise ValueError('Hash aturan berbeda dari manifest penelitian.')
            metadata['rules_manifest'] = manifest
        arguments = [executable, 'scan', '--config', str(rules_snapshot), '--json', '--metrics=off',
                     '--disable-version-check', '--no-git-ignore', '--disable-nosem',
                     '--max-target-bytes', str(10 * 1024 * 1024), '--strict', '--jobs', '2', str(source)]
    else:
        db = OSV_CACHE / 'osv-scalibr/npm/all.zip'
        metadata.update(database_sha256=sha256(db), database_metadata=json.loads(
            (OSV_CACHE / 'metadata.json').read_text(encoding='utf-8')))
        config = directory / 'osv-scanner.toml'
        config.write_text('# Server configuration: no suppressions.\n', encoding='utf-8')
        arguments = [executable, 'scan', 'source', '--offline', '--local-db-path', str(OSV_CACHE),
                     '--no-resolve', '--no-call-analysis=all', '--no-ignore', '--all-packages', '--all-vulns', '--allow-no-lockfiles',
                     '--format', 'json', '--config', str(config), '--recursive', str(source)]
    replacements = {str(source): '<snapshot>', str(OSV_CACHE): '<osv-cache>', str(directory / 'osv-scanner.toml'): '<server-osv-config>',
                    str(directory / 'sast-rules.yml'): '<server-rules>'}
    metadata['arguments'] = [tool] + [replacements.get(str(value), value) for value in arguments[1:]]
    metadata['config_sha256'] = hashlib.sha256(json.dumps(
        {'arguments': metadata['arguments'], 'excluded_directories': metadata['excluded_directories']},
        sort_keys=True).encode()).hexdigest()
    started = time.monotonic()
    remaining = TIMEOUT - (time.monotonic() - method_started)
    if remaining <= 0:
        raise TimeoutError('Pemindaian melampaui batas 5 menit.')
    code = run_process(arguments, raw, errors, directory, heartbeat, timeout=remaining)
    metadata['exit_code'] = code
    metadata['duration_seconds'] = round(time.monotonic() - started, 2)
    if code not in ((0, 1) if method == 'sca' else (0,)):
        raise ValueError(f'{tool} berhenti dengan exit code {code}; scan tidak dianggap bersih.')
    if method == 'sca' and any(marker in errors.read_text(encoding='utf-8', errors='replace').lower()
                               for marker in ('error during extraction', 'could not load db', 'unable to fetch osv database')):
        raise ValueError('OSV-Scanner melaporkan kegagalan ekstraksi/advisory; hasil tidak dianggap bersih.')
    if method == 'sca' and sha256(db) != metadata['database_sha256']:
        raise ValueError('Snapshot database OSV berubah selama scan. Ulangi dengan database yang dibekukan.')
    payload = json.loads(raw.read_text(encoding='utf-8'))
    metadata['raw_finding_count'] = len(payload.get('results', [])) if method == 'sast' else sum(len(p.get('vulnerabilities', [])) for r in payload.get('results', []) for p in r.get('packages', []))
    metadata['skipped_targets'] = payload.get('paths', {}).get('skipped', []) if method == 'sast' else []
    findings = parse_results(method, payload, source)
    metadata['unique_finding_count'] = len(findings)
    return metadata, findings
