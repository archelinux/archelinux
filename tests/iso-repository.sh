#!/usr/bin/env bash
# Inspect the sealed ISO before signing it. Pacman sees only the embedded file repository.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
xorriso -osirrox on -indev "$1" -extract /arch/x86_64/airootfs.erofs "$work/root.erofs"
fsck.erofs --extract="$work/repo" --path=/usr/share/arche/repo "$work/root.erofs"
fsck.erofs --extract="$work/hostname" --path=/etc/hostname "$work/root.erofs"
cmp "$root/airootfs/etc/hostname" "$work/hostname"
diff -qr "$root/pkgs/local-repo" "$work/repo"
mkdir "$work/db"
cat > "$work/pacman.conf" <<CFG
[options]
Architecture = x86_64
SigLevel = Optional TrustAll
[arche]
Server = file://$work/repo
CFG
pm=(pacman --config "$work/pacman.conf" --dbpath "$work/db" --logfile /dev/null --disable-sandbox)
"${pm[@]}" -Sy
for recipe in "$root"/pkgs/*/PKGBUILD; do
  bash -c 'source "$1"; printf "%s\n" "${pkgname[@]}"' _ "$recipe"
done | sort > "$work/expected"
"${pm[@]}" -Slq arche | sort > "$work/actual"
diff -u "$work/expected" "$work/actual"
printf '%s\n' 'The ISO contains the complete archelinux binary repository and expected hostname.'
