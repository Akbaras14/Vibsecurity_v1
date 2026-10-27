#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
source .env.wsl.local
set +a
VIBESEC_TEST_SCANNERS=1 .venv-linux/bin/python -m unittest \
  backend.test_scanners.ScannerCheck.test_firewall_blocks_ipv4_and_ipv6 \
  backend.test_scanners.ScannerCheck.test_scanner_keeps_parent_database_connection \
  backend.test_scanners.ScannerCheck.test_process_limits_and_timeout
export VIBESEC_SCANNER_HOST_READY=1
exec .venv-linux/bin/python -m backend.worker
