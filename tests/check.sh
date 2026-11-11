#!/usr/bin/env bash
set -euo pipefail
for script in profiledef.sh airootfs/root/arche-install pkgs/arche-base/files/usr/bin/arche-rollback scripts/*.sh tests/qemu/*.sh airootfs/root/arche-smoke-test airootfs/root/arche-desktop-smoke pkgs/*/PKGBUILD; do
  bash -n "$script"
done
if command -v shellcheck >/dev/null; then
  shellcheck airootfs/root/arche-install pkgs/arche-base/files/usr/bin/arche-rollback scripts/*.sh tests/qemu/*.sh
fi
python3 tests/check.py
python3 tests/preflight.py
python3 tests/sway.py
bash tests/installer.sh
# Format a sparse regular file, never a host block device.
if command -v mkfs.xfs >/dev/null; then
  image=$(mktemp /tmp/arche-xfs.XXXXXX)
  trap 'rm -f "$image"' EXIT
  truncate -s 16G "$image"
  mkfs.xfs -f -m reflink=1,crc=1 -i size=512 -d agcount=16 "$image"
  xfs_db -r -c 'sb 0' -c 'p agcount inodesize' "$image" | tee "$image.geometry"
  grep -qx 'agcount = 16' "$image.geometry"
  grep -qx 'inodesize = 512' "$image.geometry"
  rm -f "$image.geometry"
fi
