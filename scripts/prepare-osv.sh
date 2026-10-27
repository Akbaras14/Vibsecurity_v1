#!/usr/bin/env bash
# Explicit setup/update step. Stop the worker before replacing an experiment snapshot.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .cache storage/osv/osv-scalibr/npm
curl -fL https://github.com/google/osv-scanner/releases/download/v2.7.0/osv-scanner_linux_amd64 -o .cache/osv-scanner_linux_amd64
curl -fsSL https://github.com/google/osv-scanner/releases/download/v2.7.0/osv-scanner_SHA256SUMS -o .cache/osv-scanner_SHA256SUMS
(cd .cache && sha256sum --ignore-missing -c osv-scanner_SHA256SUMS)
chmod 755 .cache/osv-scanner_linux_amd64
.cache/osv-scanner_linux_amd64 --version | grep 'osv-scanner version: 2.7.0'
curl -fL https://osv-vulnerabilities.storage.googleapis.com/npm/all.zip -o storage/osv/osv-scalibr/npm/all.zip
.venv-linux/bin/python - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
from backend.scanner import sha256
db = Path('storage/osv/osv-scalibr/npm/all.zip')
metadata = {'ecosystem': 'npm', 'downloaded_at': datetime.now(timezone.utc).isoformat(),
            'source': 'https://osv-vulnerabilities.storage.googleapis.com/npm/all.zip',
            'sha256': sha256(db), 'scanner': 'OSV-Scanner 2.7.0'}
Path('storage/osv/metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
PY
