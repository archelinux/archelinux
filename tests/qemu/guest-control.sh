#!/usr/bin/env bash
# Test fixture only: never shipped in the ISO or packages.
set -uo pipefail
mkdir -p /run/arche-test
mountpoint -q /run/arche-test || mount -t 9p -o trans=virtio,version=9p2000.L archetest /run/arche-test
while true; do
  for job in /run/arche-test/jobs/*.sh; do
    [[ -e $job && ! -e $job.done ]] || continue
    bash "$job" > "$job.log" 2>&1
    status=$?
    cat "$job.log" >/dev/ttyS0
    printf '%s\n' "$status" > "$job.done"
  done
  sleep 1
done
