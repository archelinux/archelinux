"""Boot the release ISO, install to a fresh VM disk, then boot that disk."""
from pathlib import Path
import shutil
import subprocess
import sys
import time

from run import VM, wait_for

iso = Path(sys.argv[1]).resolve(strict=True)
work = Path(sys.argv[2]).resolve()
work.mkdir()
share = work / 'share'
share.mkdir()
shutil.copyfile(Path(__file__).with_name('guided-live.sh'), share / 'install.sh')
shutil.copyfile('/usr/share/OVMF/OVMF_VARS_4M.fd', work / 'vars.fd')
subprocess.run(['qemu-img', 'create', '-f', 'qcow2', str(work / 'target.qcow2'), '24G'], check=True)

vm = VM(work, iso)
try:
    vm.start('live')
    time.sleep(55)
    vm.command('screendump', {'filename': str(work / 'installer.png'), 'format': 'png'})
    vm.key('ctrl-alt-f2')
    time.sleep(3)
    vm.type('root\n')
    time.sleep(2)
    vm.type('mkdir -p /run/arche-test\n')
    vm.type('mount -t 9p -o trans=virtio,version=9p2000.L archetest /run/arche-test\n')
    vm.type('bash /run/arche-test/install.sh\n')
    wait_for((share / 'status').exists, 1800, 'guided installation')
    if (share / 'status').read_text().strip() != '0':
        raise RuntimeError((share / 'install.log').read_text(errors='replace')[-10000:])
finally:
    vm.stop()

vm = VM(work)
try:
    vm.start('installed')
    log = work / 'installed-serial.log'
    wait_for(lambda: 'ARCHE_DESKTOP_READY' in log.read_text(errors='replace'), 180, 'installed SwayFX desktop')
    vm.command('screendump', {'filename': str(work / 'desktop.png'), 'format': 'png'})
finally:
    vm.stop()
print('Verified UEFI boot, guided XFS installation, default hostname and SwayFX first login.')
