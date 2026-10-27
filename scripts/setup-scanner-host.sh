#!/usr/bin/env bash
# Run as root on the tested WSL2 cgroup-v1 host. Does not change other traffic.
set -euo pipefail
test "$(id -u)" = 0
command -v iptables-legacy >/dev/null
command -v ip6tables-legacy >/dev/null
if ! id vibesec-scanner >/dev/null 2>&1; then
  useradd --system --create-home --shell /bin/bash vibesec-scanner
fi
scanner_uid=$(id -u vibesec-scanner)
scanner_gid=$(id -g vibesec-scanner)
memory=/sys/fs/cgroup/memory/vibesec-scanner
network=/sys/fs/cgroup/net_cls/vibesec-scanner
mkdir -p "$memory" "$network"
printf 2147483648 > "$memory/memory.limit_in_bytes"
printf 2147483648 > "$memory/memory.memsw.limit_in_bytes"
printf 0x100001 > "$network/net_cls.classid"
chown "$scanner_uid:$scanner_gid" "$memory/cgroup.procs" "$network/cgroup.procs"
for firewall in iptables-legacy ip6tables-legacy; do
  if ! "$firewall" -C OUTPUT -m cgroup --cgroup 0x100001 -j DROP 2>/dev/null; then
    "$firewall" -I OUTPUT 1 -m cgroup --cgroup 0x100001 -j DROP
  fi
done
echo 'Cgroup RAM dan firewall IPv4/IPv6 scanner siap; jalankan tes host sebelum worker.'
