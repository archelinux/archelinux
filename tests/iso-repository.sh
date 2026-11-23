#!/usr/bin/env bash
# Verify the sealed netinstall image and the separate build-time package repository.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
xorriso -osirrox on -indev "$1" -extract /arch/x86_64/airootfs.erofs "$work/root.erofs"
fsck.erofs --extract="$work/arche" --path=/usr/share/arche "$work/root.erofs"
cmp "$root/keys/archelinux-release.asc" "$work/arche/archelinux-release.asc"
test ! -e "$work/arche/repo"
fsck.erofs --extract="$work/helper" --path=/usr/bin/arche-enable-rolling "$work/root.erofs"
cmp "$root/pkgs/arche-base/files/usr/bin/arche-enable-rolling" "$work/helper"
xorriso -indev "$1" -find /arch/boot/x86_64 -type f -exec echo -- > "$work/boot-files"
grep -Fq /vmlinuz-linux-lts "$work/boot-files"
grep -Fq /initramfs-linux-lts.img "$work/boot-files"
if grep -q linux-zen "$work/boot-files"; then exit 1; fi
fsck.erofs --extract="$work/hostname" --path=/etc/hostname "$work/root.erofs"
cmp "$root/airootfs/etc/hostname" "$work/hostname"

mkdir "$work/db"
cat > "$work/pacman.conf" <<CFG
[options]
Architecture = x86_64
SigLevel = Optional TrustAll
[arche]
Server = file://$root/pkgs/local-repo
CFG
pm=(pacman --config "$work/pacman.conf" --dbpath "$work/db" --logfile /dev/null --disable-sandbox)
"${pm[@]}" -Sy
for recipe in "$root"/pkgs/*/PKGBUILD; do
  bash -c 'source "$1"; printf "%s\n" "${pkgname[@]}"' _ "$recipe"
done | sort > "$work/expected"
"${pm[@]}" -Slq arche | sort > "$work/actual"
diff -u "$work/expected" "$work/actual"
printf '%s\n' 'Verified the LTS installer, release key, channel helper and complete build repository.'
