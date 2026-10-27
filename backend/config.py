import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env.local', override=False)
STORAGE = Path(os.environ.get('VIBESEC_STORAGE', ROOT / 'storage' / 'vibesec')).resolve()
ORIGINS = tuple(value.strip() for value in os.environ.get(
    'VIBESEC_ORIGINS', 'http://127.0.0.1:3000,http://localhost:3000'
).split(',') if value.strip())
HOSTS = tuple(value.strip() for value in os.environ.get(
    'VIBESEC_HOSTS', '127.0.0.1,localhost'
).split(',') if value.strip())
if '*' in ORIGINS or '*' in HOSTS:
    raise ValueError('VibeSec memerlukan allowlist Host/Origin eksplisit tanpa wildcard.')
MAX_UPLOAD = 100 * 1024 * 1024
MAX_EXPANDED = 200 * 1024 * 1024
MAX_FILE = 10 * 1024 * 1024
MAX_ENTRIES = 10_000
EXCLUDED = {'.git', 'node_modules', 'vendor', 'dist', 'build', '.next', 'out', 'coverage'}


def mysql_settings():
    settings = {
        'host': os.environ.get('VIBESEC_MYSQL_HOST', '127.0.0.1'),
        'port': int(os.environ.get('VIBESEC_MYSQL_PORT', '3306')),
        'user': os.environ.get('VIBESEC_MYSQL_USER', 'vibesec'),
        'password': os.environ.get('VIBESEC_MYSQL_PASSWORD', ''),
        'database': os.environ.get('VIBESEC_MYSQL_DATABASE', 'vibesec'),
        'charset': 'utf8mb4', 'autocommit': False,
        'connect_timeout': 5, 'read_timeout': 30, 'write_timeout': 30,
    }
    if not settings['database'] or not settings['user']:
        raise ValueError('Isi VIBESEC_MYSQL_DATABASE dan VIBESEC_MYSQL_USER.')
    return settings
