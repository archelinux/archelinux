#!/usr/bin/env bash
set -euxo pipefail
expected=$1
systemctl is-system-running --wait
test -d /sys/firmware/efi
uname -a
pacman -Q arche-base arche-tui-stack arche-agentic-core linux-zen linux-lts
uname -r | grep -q -- "-$expected"
test "$(findmnt -no FSTYPE /)" = xfs
test "$(findmnt -no FSTYPE /boot)" = vfat
test "$(findmnt -no SOURCE /)" = /dev/vda2
test "$(findmnt -no SOURCE /boot)" = /dev/vda1
test "$(blockdev --getsize64 /dev/vda1)" = 1073741824
xfs_info / | tee /tmp/xfs-info
for pattern in 'agcount=16' 'reflink=1' 'crc=1' 'isize=512'; do grep -q "$pattern" /tmp/xfs-info; done
findmnt -no OPTIONS /
cat /etc/fstab
if grep -q 'arche-test/cache' /etc/pacman.d/mirrorlist; then exit 1; fi
python - <<'PY'
import subprocess
opts=set(subprocess.check_output(['findmnt','-no','OPTIONS','/'],text=True).strip().split(','))
assert {'noatime','nodiratime','logbufs=8','logbsize=256k'} <= opts, opts
# Linux reports allocsize in KiB even when fstab specifies MiB.
assert opts & {'allocsize=64M','allocsize=65536k'}, opts
root=next(line.split() for line in open('/etc/fstab') if not line.startswith('#') and len(line.split())>1 and line.split()[1]=='/')
assert {'rw','noatime','nodiratime','logbufs=8','logbsize=256k','allocsize=64M'} <= set(root[3].split(','))
PY
reflink_dir=$(mktemp -d /var/tmp/arche-reflink.XXXXXX)
trap 'rm -rf -- "$reflink_dir"' EXIT
printf 'Arche reflink verification\n' >"$reflink_dir/source"
cp --reflink=always "$reflink_dir/source" "$reflink_dir/copy"
cmp "$reflink_dir/source" "$reflink_dir/copy"
bootctl list --no-pager
grep -Fx 'default arche-zen.conf' /boot/loader/loader.conf
grep -Fx 'timeout 2' /boot/loader/loader.conf
for kernel in zen lts; do
  test -s "/boot/vmlinuz-linux-$kernel"
  test -s "/boot/initramfs-linux-$kernel.img"
  grep -Fx "linux /vmlinuz-linux-$kernel" "/boot/loader/entries/arche-$kernel.conf"
done
cat /proc/cmdline
grep -q 'rootflags=logbufs=8,logbsize=256k,allocsize=64M' /proc/cmdline
zramctl
python - <<'PY'
from pathlib import Path
mem=int(next(x.split()[1] for x in open('/proc/meminfo') if x.startswith('MemTotal:')))*1024
size=int(Path('/sys/block/zram0/disksize').read_text())
assert abs(size-mem)<2*1024*1024, (size,mem)
assert '[zstd]' in Path('/sys/block/zram0/comp_algorithm').read_text()
assert '/dev/zram0' in Path('/proc/swaps').read_text()
PY
test "$(sysctl -n vm.swappiness)" = 180
test "$(sysctl -n vm.watermark_boost_factor)" = 0
test "$(sysctl -n vm.watermark_scale_factor)" = 125
test "$(sysctl -n vm.page-cluster)" = 0
test "$(sysctl -n vm.dirty_background_ratio)" = 5
test "$(sysctl -n vm.dirty_ratio)" = 10
test "$(sysctl -n fs.inotify.max_user_watches)" = 524288
test "$(sysctl -n fs.inotify.max_user_instances)" = 1024
systemctl is-active NetworkManager paccache.timer
systemctl is-enabled NetworkManager paccache.timer
test -z "$(find /home/arche/.config \( ! -user arche -o ! -group arche \) -print -quit)"
ls -l /home/arche/.config/sway/config /home/arche/.config/waybar/config.jsonc
grep -Fx 'output * bg /usr/share/arche/wallpaper.svg fill' /home/arche/.config/sway/config
cmp /usr/share/arche/wallpaper.svg /run/arche-test/wallpaper.svg
cmp /usr/share/arche/logo.svg /run/arche-test/logo.svg
for package in arche-base arche-tui-stack arche-agentic-core; do
  if pacman -Ql "$package" | grep ' /etc/skel/'; then exit 1; fi
done
test "$(passwd -S root | awk '{print $2}')" = L
test "$(passwd -S arche | awk '{print $2}')" = L
uid=$(id -u arche)
runuser -u arche -- env XDG_RUNTIME_DIR="/run/user/$uid" nvim --headless -i NONE -u /home/arche/.config/nvim/init.lua -l /run/arche-test/arche-smoke.lua
runuser -u arche -- env XDG_RUNTIME_DIR="/run/user/$uid" nvim --headless -i NONE -c 'lua if not vim.lsp.is_enabled("lua_ls") then vim.cmd("cquit") end' -c checkhealth -c qa
for unit in ollama llama-server; do
  test ! -e "/etc/systemd/user/default.target.wants/$unit.service"
  test ! -e "/home/arche/.config/systemd/user/default.target.wants/$unit.service"
done
# Correct installed module directories exist for the running kernel.
test -d "/usr/lib/modules/$(uname -r)"
modprobe xfs
systemctl --failed --no-pager
test -z "$(systemctl --failed --no-legend)"
echo "ARCHE_VERIFY_PASS $expected"
