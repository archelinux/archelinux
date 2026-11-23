#!/usr/bin/env bash
# Runs only inside the disposable installed-2.0.0 VM before promoting a signed snapshot.
set -euo pipefail
exec > /dev/ttyS0 2>&1
trap 'echo ARCHE_UPGRADE_FAILED' EXIT
set -x
[[ $(systemd-detect-virt --vm) =~ ^(kvm|qemu)$ ]]
snapshot=/var/tmp/arche-candidate
keyring=$(mktemp -d)
gpg --batch --dearmor --output "$keyring/allowed.gpg" /var/tmp/arche-release.asc
gpgv --homedir "$keyring" --keyring "$keyring/allowed.gpg" "$snapshot/arche-enable-rolling.sig" "$snapshot/arche-enable-rolling"
before=$(pacman -Q arche-maintenance)
binding=/home/tester/.config/sway/config
printf '%s\n' 'bindsym Mod4+F10 exec foot' | runuser -u tester -- tee -a "$binding" > /dev/null
checksum=$(sha256sum "$binding")
# The old unsigned local package is taken only from the verified release ISO.
cp /usr/share/arche/repo/arche-maintenance-*.pkg.tar.zst /var/cache/pacman/pkg/
python "$snapshot/arche-enable-rolling" --key /var/tmp/arche-release.asc --server "file://$snapshot"
pacman -Syu --noconfirm
after=$(pacman -Q arche-maintenance)
[[ $(vercmp "${after#* }" "${before#* }") -gt 0 ]]
[[ $(sha256sum "$binding") == "$checksum" ]]
arche-rollback arche-maintenance
[[ $(pacman -Q arche-maintenance) == "$before" ]]
pacman -Syu --noconfirm
[[ $(pacman -Q arche-maintenance) == "$after" && $(sha256sum "$binding") == "$checksum" ]]
systemctl disable arche-test-upgrade.service
sync
trap - EXIT
echo ARCHE_UPGRADE_PASS
