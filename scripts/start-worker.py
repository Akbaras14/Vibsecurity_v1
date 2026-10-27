"""Windows supervisor: restore WSL setup and DB access after a worker/WSL restart."""
import logging
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_worker():
    subprocess.run([sys.executable, str(ROOT / 'scripts/configure-wsl.py'), '--preserve-credentials'],
                   cwd=ROOT, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    linux_root = subprocess.check_output(['wsl', '-d', 'Ubuntu-24.04', '--', 'wslpath', '-a', ROOT.as_posix()],
                                        text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
    subprocess.run(['wsl', '-d', 'Ubuntu-24.04', '-u', 'root', '--', 'bash',
                    linux_root + '/scripts/setup-scanner-host.sh'], check=True,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.run(['wsl', '-d', 'Ubuntu-24.04', '-u', 'vibesec-scanner', '--', 'bash',
                    linux_root + '/scripts/start-worker-wsl.sh'], check=True,
                   creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        while True:
            try:
                run_worker()
            except (subprocess.CalledProcessError, OSError):
                logging.warning('Worker berhenti atau lingkungan belum siap; mencoba kembali dalam 5 detik.')
            time.sleep(5)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
