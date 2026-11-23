#!/usr/bin/env bash
# Stage our downstream changes over the official runtime, including its translations.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
version=$(pacman -Q archinstall)
[[ $version == 'archinstall 4.5-'* ]] || { echo "Expected archinstall 4.5, found $version" >&2; exit 1; }
lib=$(python3 -c 'import sysconfig; print(sysconfig.get_path("purelib"))')
dest="$root/airootfs/usr/share/arche/installer"
mkdir -p "$dest"
[[ ! -e $dest/archinstall ]] || { echo "Installer staging directory already populated: $dest" >&2; exit 1; }
cp -r "$lib/archinstall" "$dest/"
find "$dest/archinstall" -name __pycache__ -type d -prune -exec rm -rf {} +
patch --batch --fuzz=0 -d "$dest" -p1 < "$root/installer/archinstall-4.5.patch"
install -m644 "$root/installer/arche.py" "$dest/archinstall/arche.py"
