#!/usr/bin/env bash
set -euxo pipefail
exec > >(tee /run/arche-test/install.log /dev/ttyS0) 2>&1
finish() { printf '%s\n' "$?" > /run/arche-test/install.done; }
trap finish EXIT
# Reuse public package downloads if supplied; keep Arch signature policy intact.
# CacheServer is not used for repository databases and falls back to the mirror.
if compgen -G '/run/arche-test/cache/*.pkg.tar.zst' >/dev/null; then
  sed -i '1i CacheServer = file:///run/arche-test/cache' /etc/pacman.d/mirrorlist
fi
# The harness shares only this test's disposable directory, not the host root.
for _ in {1..60}; do
  if curl --connect-timeout 5 -fsI https://geo.mirror.pkgbuild.com/core/os/x86_64/core.db >/dev/null; then break; fi
  sleep 2
done
/root/arche-install --unattended --disk /dev/vda --erase-disk /dev/vda --username arche --hostname arche-test --locale en_US.UTF-8 --locked-accounts
# Remove the test-only cache URL from the installed system.
sed -i '\|^CacheServer = file:///run/arche-test/cache$|d' /mnt/etc/pacman.d/mirrorlist
# Add a VM-only control service and tty autologin, leaving shipped defaults intact.
install -Dm755 /run/arche-test/guest-control.sh /mnt/usr/local/lib/arche-test-control
cat > /mnt/etc/systemd/system/arche-test-control.service <<'UNIT'
[Unit]
Description=Disposable VM test controller
After=multi-user.target
[Service]
ExecStart=/usr/local/lib/arche-test-control
Restart=on-failure
[Install]
WantedBy=multi-user.target
UNIT
# Avoid ordering cycle with multi-user.target.
sed -i 's/After=multi-user.target/After=local-fs.target/' /mnt/etc/systemd/system/arche-test-control.service
mkdir -p /mnt/etc/systemd/system/multi-user.target.wants
ln -s /etc/systemd/system/arche-test-control.service /mnt/etc/systemd/system/multi-user.target.wants/arche-test-control.service
mkdir -p /mnt/etc/systemd/system/getty@tty1.service.d
cat > /mnt/etc/systemd/system/getty@tty1.service.d/test.conf <<'UNIT'
[Service]
ExecStart=
ExecStart=-/usr/bin/agetty --autologin arche --noclear %I $TERM
UNIT
# Preserve installed options, add diagnostic serial output for the test.
sed -i '/^options /s/$/ console=tty0 console=ttyS0,115200n8/' /mnt/boot/loader/entries/arche-*.conf
sync
umount -R /mnt
echo ARCHE_INSTALL_PASS
