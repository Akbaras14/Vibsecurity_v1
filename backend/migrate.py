"""MySQL migrations with a server lock and a durable failure marker."""
import argparse
import hashlib
from pathlib import Path

import pymysql

from .config import STORAGE, mysql_settings
from .store import connect, now, query

MIGRATIONS = Path(__file__).parent / 'migrations'


def lock_name(purpose):
    return f'vibesec:{purpose}:' + hashlib.sha256(mysql_settings()['database'].encode()).hexdigest()[:32]


def migrate(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'scans').mkdir(exist_ok=True)
    scripts = sorted(MIGRATIONS.glob('[0-9][0-9][0-9]_*.sql'))
    versions = [int(script.name.split('_')[0]) for script in scripts]
    if not scripts or versions != list(range(1, len(scripts) + 1)):
        raise ValueError('Urutan migrasi harus dimulai dari 001 dan berurutan tanpa duplikat.')
    applied = []
    with connect(multi_statements=True) as db:
        name = lock_name('migrate')
        if query(db, 'SELECT GET_LOCK(%s, 30) AS acquired', (name,)).fetchone()['acquired'] != 1:
            raise ValueError('Migrasi lain sedang berjalan; coba lagi setelah selesai.')
        try:
            query(db, '''CREATE TABLE IF NOT EXISTS schema_migrations (
                version INT PRIMARY KEY, name VARCHAR(255) NOT NULL,
                checksum CHAR(64) CHARACTER SET ascii NOT NULL,
                dirty TINYINT NOT NULL, applied_at VARCHAR(40)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
            history = {row['version']: row for row in query(db, 'SELECT * FROM schema_migrations').fetchall()}
            if history and max(history) > versions[-1]:
                raise ValueError('Versi database lebih baru daripada aplikasi.')
            for version, script in zip(versions, scripts):
                sql = script.read_text(encoding='utf-8')
                checksum = hashlib.sha256(sql.encode()).hexdigest()
                existing = history.get(version)
                if existing:
                    if existing['dirty']:
                        raise ValueError(f'Migrasi {existing["name"]} sebelumnya gagal. Periksa skema dan pulihkan sebelum melanjutkan.')
                    if existing['checksum'] != checksum or existing['name'] != script.name:
                        raise ValueError(f'Migrasi {script.name} telah berubah setelah diterapkan.')
                    continue
                query(db, 'INSERT INTO schema_migrations(version,name,checksum,dirty) VALUES(%s,%s,%s,1)',
                      (version, script.name, checksum))
                db.connection.commit()  # DDL implicitly commits: persist the failure marker first.
                query(db, sql)
                while db.nextset():
                    pass
                query(db, 'UPDATE schema_migrations SET dirty=0,applied_at=%s WHERE version=%s', (now(), version))
                db.connection.commit()
                applied.append(script.name)
        finally:
            query(db, 'SELECT RELEASE_LOCK(%s)', (name,))
    return applied


def main():
    parser = argparse.ArgumentParser(description='Migrasi database MySQL VibeSec.')
    parser.add_argument('--status', action='store_true', help='Periksa riwayat tanpa mengubah skema.')
    args = parser.parse_args()
    try:
        if args.status:
            with connect() as db:
                rows = query(db, 'SELECT version,name,dirty,applied_at FROM schema_migrations ORDER BY version').fetchall()
            for row in rows:
                print(f'{row["version"]:03d} {row["name"]}: {"GAGAL/PERLU PEMULIHAN" if row["dirty"] else "diterapkan"}')
            if not rows:
                print('Belum ada migrasi yang diterapkan.')
        else:
            applied = migrate(STORAGE)
            print('Migrasi diterapkan: ' + ', '.join(applied) if applied else 'Database sudah pada versi terbaru.')
    except pymysql.MySQLError as error:
        raise SystemExit(f'MySQL tidak dapat diproses (kode {error.args[0]}). Periksa konfigurasi, layanan, dan izin database.') from None
    except ValueError as error:
        raise SystemExit(str(error)) from None


if __name__ == '__main__':
    main()
