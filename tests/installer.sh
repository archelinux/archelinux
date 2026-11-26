#!/usr/bin/env bash
# Exercise emitted target configuration with mocked system commands.
set -euo pipefail
source airootfs/root/arche-install
CHROOT=$(mktemp -d /tmp/arche-target.XXXXXX)
trap 'rm -rf "$CHROOT"' EXIT
mkdir -p "$CHROOT/etc"
ROOT_PARTITION=/dev/test-root
blkid() { echo 0000-test-root; }
genfstab() {
  printf 'UUID=original / xfs defaults 0 1\nUUID=efi /boot vfat defaults 0 2\n'
}
write_fstab
[[ $(grep -c ' / ' "$CHROOT/etc/fstab") == 1 ]]
grep -Fxq 'UUID=0000-test-root  /  xfs  rw,noatime,nodiratime,logbufs=8,logbsize=256k,allocsize=64M  0  0' "$CHROOT/etc/fstab"
grep -q 'UUID=efi /boot' "$CHROOT/etc/fstab"
arch-chroot() { printf '%s\n' "$*" >> "$CHROOT/chroot-calls"; }
mountpoint() { [[ $* == "-q $CHROOT/boot" ]]; }
mkdir -p "$CHROOT/boot"
for kernel in zen lts; do
  printf kernel > "$CHROOT/boot/vmlinuz-linux-$kernel"
  printf initramfs > "$CHROOT/boot/initramfs-linux-$kernel.img"
done
EFI_PARTITION=/dev/test-efi
setup_bootloader
grep -Fxq "$CHROOT bootctl --esp-path=/boot install" "$CHROOT/chroot-calls"
grep -qx 'default arche-zen.conf' "$CHROOT/boot/loader/loader.conf"
grep -qx 'timeout 2' "$CHROOT/boot/loader/loader.conf"
for kernel in zen lts; do
  grep -qx "linux /vmlinuz-linux-$kernel" "$CHROOT/boot/loader/entries/arche-$kernel.conf"
  grep -qx "initrd /initramfs-linux-$kernel.img" "$CHROOT/boot/loader/entries/arche-$kernel.conf"
  grep -qx 'options root=UUID=0000-test-root rw rootflags=logbufs=8,logbsize=256k,allocsize=64M' "$CHROOT/boot/loader/entries/arche-$kernel.conf"
done
# Reject a missing image before bootctl can create a misleading entry.
rm "$CHROOT/boot/initramfs-linux-lts.img"
if (setup_bootloader) > /dev/null 2>&1; then
  echo 'Missing initramfs was not rejected' >&2
  exit 1
fi
EFI_PARTITION=
DISK=/dev/test-disk
mkdir -p "$CHROOT/etc/grub.d" "$CHROOT/etc/default"
setup_bootloader
bash -n "$CHROOT/etc/grub.d/09_arche"
"$CHROOT/etc/grub.d/09_arche" | grep -q 'vmlinuz-linux-lts'
echo 'Installer fstab and dual-kernel boot configuration checks passed'
# Unattended mode must never infer permission to erase a disk.
if (parse_options --unattended --disk /dev/fake --username arche) >/dev/null 2>&1; then
  echo 'Unattended mode accepted unlocked accounts' >&2; exit 1
fi
if (parse_options --unattended --locked-accounts --disk /dev/fake --username arche) >/dev/null 2>&1; then
  echo 'Unattended mode accepted a missing erase confirmation' >&2; exit 1
fi
# A mounted child must stop partitioning before sfdisk can execute.
lsblk() { printf '/dev/fake\n/dev/fake1\n'; }
findmnt() { [[ $* == *'/dev/fake1'* ]]; }
swapon() { :; }
sfdisk() { echo 'unsafe partitioning' > "$CHROOT/unsafe"; }
DISK=/dev/fake
if (partition_unattended) >/dev/null 2>&1; then
  echo 'Mounted child was not rejected' >&2; exit 1
fi
[[ ! -e $CHROOT/unsafe ]]
echo 'Unattended erase and mounted-disk guards passed'
# Arch locale.gen permits trailing whitespace and commented locale definitions.
printf '#en_US.UTF-8 UTF-8  \n# de_DE.UTF-8 UTF-8\n' > "$CHROOT/locale.gen"
LOCALE=en_US.UTF-8
valid_locale "$CHROOT/locale.gen"
LOCALE=de_DE.UTF-8
valid_locale "$CHROOT/locale.gen"
LOCALE=not_a_locale
if valid_locale "$CHROOT/locale.gen"; then
  echo 'Unknown locale accepted' >&2; exit 1
fi
echo 'Locale whitespace regression passed'

# Only the copy mode carries the live Wi-Fi profiles, with root-only permissions.
live=$(mktemp -d "$CHROOT/live.XXXXXX")
cp -r airootfs/etc "$live/"
mkdir -p "$live/var/lib/iwd" "$CHROOT/bin"
for profile in 'home wifi.psk' work.8021x guest.open ignored.txt; do
  printf '%s\n' "$profile" > "$live/var/lib/iwd/$profile"
done
cat > "$CHROOT/bin/systemctl" <<'SYSTEMCTL'
#!/usr/bin/env bash
[[ $2 == enable && $3 == iwd.service && $4 == systemd-networkd.service && $5 == systemd-resolved.service ]]
SYSTEMCTL
chmod +x "$CHROOT/bin/systemctl"
for mode in copy fresh manual; do
  target="$CHROOT/network-$mode"
  PATH="$CHROOT/bin:$PATH" bash airootfs/usr/share/arche/install-network "$target" "$mode" "$live"
  test -f "$target/etc/tmpfiles.d/arche-resolved.conf"
  if [[ $mode == manual ]]; then
    test -z "$(find "$target/etc/systemd/network" -type f -print -quit)"
  else
    cmp "$live/etc/systemd/network/80-arche-wifi.network" "$target/etc/systemd/network/80-arche-wifi.network"
  fi
  if [[ $mode == copy ]]; then
    test "$(stat -c %a "$target/var/lib/iwd")" = 700
    for profile in 'home wifi.psk' work.8021x guest.open; do
      cmp "$live/var/lib/iwd/$profile" "$target/var/lib/iwd/$profile"
      test "$(stat -c %a "$target/var/lib/iwd/$profile")" = 600
    done
    test ! -e "$target/var/lib/iwd/ignored.txt"
  else
    test ! -e "$target/var/lib/iwd"
  fi
done
echo 'Network defaults, manual mode and Wi-Fi profile transfer checks passed'
