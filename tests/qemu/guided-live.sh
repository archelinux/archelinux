#!/usr/bin/env bash
set -euo pipefail
share=/run/arche-test
exec >"$share/install.log" 2>&1
trap 'echo "$?" > "$share/status"' EXIT
set -x
[[ $(systemd-detect-virt --vm) =~ ^(kvm|qemu)$ ]]
[[ $(lsblk -bndo SIZE /dev/vda) == 25769803776 ]]
[[ $(lsblk -nrpo NAME /dev/vda | wc -l) == 1 ]]
[[ $(cat /etc/hostname) == archelinux ]]
test -d /sys/firmware/efi
export PYTHONPATH=/usr/share/arche/installer
python -P - <<'PY'
import asyncio
import json
from pathlib import Path
from archinstall.lib.disk.device_handler import device_handler
from archinstall.lib.disk.default_layouts import suggest_single_disk_layout
from archinstall.lib.models.device import DiskLayoutConfiguration, DiskLayoutType

device = device_handler.get_device(Path('/dev/vda'))
layout = asyncio.run(suggest_single_disk_layout(device, separate_home=False))
config = {
    'kernels': ['linux-lts'],
    'bootloader_config': {'bootloader': 'Systemd-boot', 'uki': False, 'removable': False},
    'users': [{'username': 'tester', 'sudo': True, 'enc_password': '!'}],
    'network_config': {'type': 'nm'},
    'disk_config': DiskLayoutConfiguration(DiskLayoutType.Default, [layout]).json(),
}
Path('/run/arche-qa.json').write_text(json.dumps(config))
PY
/root/arche-install --silent --config /run/arche-qa.json --skip-ntp --skip-wkd --skip-wifi-check --skip-version-check
[[ $(findmnt -no FSTYPE --mountpoint /mnt) == xfs ]]
[[ $(cat /mnt/etc/hostname) == archelinux ]]
arch-chroot /mnt pacman -Q arche-swayfx swayfx arche-zsh neovim
arch-chroot /mnt pacman -Si arche/arche-cuda
if arch-chroot /mnt pacman -Q cuda; then exit 1; fi
cmp /mnt/usr/share/arche/skel/.config/nvim/colors/archevim.lua /mnt/home/tester/.config/nvim/colors/archevim.lua
arch-chroot /mnt getent passwd tester | grep -F /bin/zsh

# Autologin and the serial probe belong only to this disposable guest.
mkdir -p /mnt/etc/systemd/system/getty@tty1.service.d
cat > /mnt/etc/systemd/system/getty@tty1.service.d/test.conf <<'GETTY'
[Service]
ExecStart=
ExecStart=-/usr/bin/agetty --autologin tester --noclear %I $TERM
GETTY
cat > /mnt/usr/local/bin/arche-qa-desktop <<'CHECK'
#!/usr/bin/env bash
set -eu
exec > /dev/ttyS0 2>&1
[[ $(hostname) == archelinux ]]
XDG_RUNTIME_DIR=/run/user/$(id -u tester)
export XDG_RUNTIME_DIR
for _ in {1..100}; do
  SWAYSOCK=$(find "$XDG_RUNTIME_DIR" -name 'sway-ipc.*.sock' -print -quit 2>/dev/null || true)
  if [[ -S $SWAYSOCK ]] && pgrep -u tester -x waybar; then break; fi
  sleep 1
done
test -S "$SWAYSOCK"
pgrep -u tester -x waybar
runuser -u tester -- env XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" SWAYSOCK="$SWAYSOCK" swaymsg -t get_outputs
echo ARCHE_DESKTOP_READY
CHECK
chmod 755 /mnt/usr/local/bin/arche-qa-desktop
cat > /mnt/etc/systemd/system/arche-test-desktop.service <<'UNIT'
[Unit]
After=systemd-user-sessions.service
[Service]
Type=oneshot
ExecStart=/usr/local/bin/arche-qa-desktop
[Install]
WantedBy=multi-user.target
UNIT
arch-chroot /mnt systemctl enable arche-test-desktop.service
sync
