"""Bounded ZIP inspection and extraction. Never execute project content."""
import json
import re
import stat
import zipfile
from pathlib import Path

from .config import EXCLUDED, MAX_ENTRIES, MAX_EXPANDED, MAX_FILE

SCANNER_CONFIGS = {'.semgrepignore', '.semgrep.yml', '.semgrep.yaml', '.trivyignore', '.trivyignore.yaml', 'trivy.yaml', '.trivy.yaml', 'osv-scanner.toml', '.osv-scanner.toml'}


class ArchiveError(ValueError):
    pass


def inspect_zip(archive, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    coverage = {'source_files': 0, 'languages': [], 'lockfiles': [], 'skipped': [],
                'total_files': 0, 'expanded_bytes': 0,
                'sast_reason': None, 'sca_reason': None}
    seen = set()
    try:
        with zipfile.ZipFile(archive) as bundle:
            entries = bundle.infolist()
            if not entries or len(entries) > MAX_ENTRIES:
                raise ArchiveError('ZIP kosong atau jumlah entri melebihi 10.000.')
            declared_total = 0
            for item in entries:
                name = item.orig_filename
                parts = name.replace('\\', '/').rstrip('/').split('/')
                if (not name or '\x00' in name or name.startswith(('/', '\\'))
                        or any(part in ('', '.', '..') or ':' in part for part in parts)
                        or any(part.endswith(('.', ' ')) for part in parts)
                        or any(re.search(r'[<>"|?*\x00-\x1f]', part) for part in parts)
                        or any(re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..*)?', part, re.I) for part in parts)):
                    raise ArchiveError('ZIP mengandung path berbahaya atau nama file tidak valid.')
                relative = '/'.join(parts)
                if relative.casefold() in seen:
                    raise ArchiveError('ZIP mengandung path duplikat atau benturan huruf besar/kecil.')
                seen.add(relative.casefold())
                mode = item.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ArchiveError('ZIP mengandung symlink atau tipe entri khusus.')
                if item.flag_bits & 1:
                    raise ArchiveError('ZIP terenkripsi tidak didukung.')
                if item.file_size > MAX_FILE:
                    raise ArchiveError('Satu file dalam ZIP melebihi 10 MB.')
                declared_total += item.file_size
                if declared_total > MAX_EXPANDED:
                    raise ArchiveError('Total ekstraksi ZIP melebihi 200 MB.')
                target = destination.joinpath(*parts).resolve()
                if not target.is_relative_to(destination) or target == destination:
                    raise ArchiveError('Target ekstraksi keluar dari direktori scan.')
                skipped = next((part for part in parts if part in EXCLUDED), None)
                if skipped or parts[-1] in SCANNER_CONFIGS:
                    coverage['skipped'].append(relative)
                    continue
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                file_bytes = 0
                with bundle.open(item) as source, target.open('xb') as output:
                    while chunk := source.read(64 * 1024):
                        file_bytes += len(chunk)
                        coverage['expanded_bytes'] += len(chunk)
                        if file_bytes > MAX_FILE or coverage['expanded_bytes'] > MAX_EXPANDED:
                            raise ArchiveError('Ekstraksi ZIP melampaui batas ukuran.')
                        output.write(chunk)
                if file_bytes != item.file_size:
                    raise ArchiveError('Ukuran file ZIP tidak konsisten.')
                coverage['total_files'] += 1
                extension = target.suffix.lower()
                if extension in ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'):
                    coverage['source_files'] += 1
                    language = 'TypeScript' if extension in ('.ts', '.tsx') else 'JavaScript'
                    if language not in coverage['languages']:
                        coverage['languages'].append(language)
                if target.name == 'package-lock.json':
                    try:
                        lock = json.loads(target.read_text(encoding='utf-8-sig'))
                        if not isinstance(lock, dict) or lock.get('lockfileVersion') not in (1, 2, 3):
                            raise ValueError()
                    except (ValueError, UnicodeError):
                        raise ArchiveError('package-lock.json rusak atau versinya tidak didukung.') from None
                    coverage['lockfiles'].append(relative)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError) as error:
        raise ArchiveError('ZIP rusak, tidak didukung, atau tidak dapat diekstrak.') from error
    if not coverage['source_files']:
        coverage['sast_reason'] = 'Tidak ditemukan kode JavaScript/TypeScript yang didukung.'
    if not coverage['lockfiles']:
        coverage['sca_reason'] = 'Tidak ditemukan package-lock.json yang didukung.'
    coverage['project_root'] = None
    coverage['nextjs'] = False
    if len(coverage['lockfiles']) == 1:
        project_root = Path(coverage['lockfiles'][0]).parent
        coverage['project_root'] = project_root.as_posix()
        package = destination / project_root / 'package.json'
        if package.is_file():
            try:
                data = json.loads(package.read_text(encoding='utf-8-sig'))
                coverage['nextjs'] = any('next' in (data.get(key) or {}) for key in ('dependencies', 'devDependencies'))
            except (ValueError, AttributeError, TypeError):
                pass
    return coverage
