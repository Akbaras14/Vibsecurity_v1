"""Run with the Windows project Python to connect the tested Ubuntu WSL worker."""
import ipaddress
import os
import re
import secrets
import shlex
import subprocess
import sys
import shutil
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.config import mysql_settings
import pymysql
from dotenv import dotenv_values, set_key


def wsl(*arguments):
    return subprocess.check_output(['wsl', '-d', 'Ubuntu-24.04', '--exec', *arguments], text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preserve-credentials', action='store_true')
    args = parser.parse_args()
    route = wsl('ip', '-4', 'route', 'show', 'default').split()
    gateway = str(ipaddress.IPv4Address(route[route.index('via') + 1]))
    address = str(ipaddress.IPv4Address(wsl('hostname', '-I').split()[0]))
    assert ipaddress.ip_address(gateway).is_private and ipaddress.ip_address(address).is_private
    linux_root = wsl('wslpath', '-a', ROOT.as_posix())
    settings = mysql_settings()
    database = settings.pop('database')
    admin_file = ROOT / '.env.mysql.local'
    admin = dotenv_values(admin_file)
    settings.update(host='127.0.0.1', port=3308, user='root',
                    password=admin.get('VIBESEC_MYSQL_PASSWORD', ''))
    assert re.fullmatch(r'[A-Za-z0-9_]+', database), 'Invalid database name.'
    existing_worker = dotenv_values(ROOT / '.env.wsl.local') if args.preserve_credentials else {}
    existing_api = dotenv_values(ROOT / '.env.local') if args.preserve_credentials else {}
    password = existing_worker.get('VIBESEC_MYSQL_PASSWORD') or secrets.token_urlsafe(32)
    api_password = existing_api.get('VIBESEC_MYSQL_PASSWORD') or secrets.token_urlsafe(32)
    admin_password = settings['password'] or secrets.token_urlsafe(32)
    with pymysql.connect(**settings) as db:
        with db.cursor() as cursor:
            cursor.execute('SELECT VERSION()')
            version = cursor.fetchone()[0]
            assert 'MariaDB' not in version and int(version.split('.')[0]) >= 8, 'Use native MySQL 8+.'
            cursor.execute(f'CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
            for user, host, secret in (('vibesec_worker', address, password), ('vibesec_api', 'localhost', api_password)):
                cursor.execute('CREATE USER IF NOT EXISTS %s@%s IDENTIFIED BY %s', (user, host, secret))
                cursor.execute('ALTER USER %s@%s IDENTIFIED BY %s', (user, host, secret))
                cursor.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES ON `{database}`.* TO %s@%s',
                               (user, host))
            cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (admin_password,))
        db.commit()
    admin_file.write_text('VIBESEC_MYSQL_HOST=127.0.0.1\nVIBESEC_MYSQL_PORT=3308\n'
                          f'VIBESEC_MYSQL_USER=root\nVIBESEC_MYSQL_PASSWORD={admin_password}\n', encoding='utf-8')
    environment = ROOT / '.env.local'
    backup = ROOT / '.cache/env-before-wsl.local'
    if environment.exists() and not backup.exists():
        shutil.copyfile(environment, backup)
    for key, value in {'HOST': '127.0.0.1', 'PORT': '3308', 'DATABASE': database,
                       'USER': 'vibesec_api', 'PASSWORD': api_password}.items():
        set_key(environment, 'VIBESEC_MYSQL_' + key, value)
    values = {
        'VIBESEC_MYSQL_HOST': gateway, 'VIBESEC_MYSQL_PORT': '3308',
        'VIBESEC_MYSQL_DATABASE': database, 'VIBESEC_MYSQL_USER': 'vibesec_worker',
        'VIBESEC_MYSQL_PASSWORD': password,
        'VIBESEC_STORAGE': linux_root + '/storage/vibesec',
        'VIBESEC_SEMGREP': '/home/vibesec-scanner/semgrep-venv/bin/semgrep',
        'VIBESEC_OSV_SCANNER': linux_root + '/.cache/osv-scanner_linux_amd64',
        'VIBESEC_OSV_CACHE': linux_root + '/storage/osv',
        'VIBESEC_MEMORY_CGROUP': '/sys/fs/cgroup/memory/vibesec-scanner',
        'VIBESEC_NETWORK_CGROUP': '/sys/fs/cgroup/net_cls/vibesec-scanner',
        'VIBESEC_SCANNER_HOST_READY': '0',
    }
    destination = ROOT / '.env.wsl.local'
    temporary = destination.with_suffix('.tmp')
    temporary.write_text(''.join(f'{key}={shlex.quote(value)}\n' for key, value in values.items()),
                         encoding='utf-8', newline='\n')
    os.replace(temporary, destination)
    print('Konfigurasi WSL disimpan privat. Akun DB hanya diizinkan dari IP WSL saat ini. Jalankan tes host sebelum aktivasi.')


if __name__ == '__main__':
    main()
