#!/usr/bin/env python3
"""UEFI live ISO -> fresh qcow2 installation -> Zen/LTS cold-boot acceptance.

Run with sudo on a Linux KVM host. Uses only a dedicated test-directory 9p share.
No host block devices or account credentials are passed to the guest.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


class VM:
    def __init__(self, work, iso=None):
        self.work, self.iso = Path(work), iso
        self.qmp = self.work / "qmp.sock"
        self.process = None

    def start(self, label):
        self.qmp.unlink(missing_ok=True)
        args = [
            "qemu-system-x86_64", "-name", "Arche-Install-Test",
            "-machine", "q35,accel=kvm", "-cpu", "host", "-smp", "2", "-m", "4096",
            "-drive", "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd",
            "-drive", f"if=pflash,format=raw,file={self.work / 'vars.fd'}",
            "-drive", f"if=virtio,format=qcow2,file={self.work / 'target.qcow2'}",
            "-device", "virtio-vga", "-display", "none",
            "-nic", "user,model=virtio-net-pci",
            "-virtfs", f"local,path={self.work / 'share'},mount_tag=archetest,security_model=none",
            "-qmp", f"unix:{self.qmp},server=on,wait=off",
            "-serial", f"file:{self.work / (label + '-serial.log')}",
        ]
        if self.iso:
            args += ["-cdrom", str(self.iso), "-boot", "d"]
        else:
            args += ["-boot", "c"]
        print("QEMU:", " ".join(args), flush=True)
        self.err = open(self.work / (label + "-qemu.log"), "w")
        self.process = subprocess.Popen(args, stdout=self.err, stderr=self.err)
        wait_for(lambda: self.qmp.exists(), 20, "QMP socket")

    def command(self, name, arguments=None):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.connect(str(self.qmp))
            connection.settimeout(15)
            with connection.makefile("rwb") as stream:
                stream.readline()
                def issue(command, args):
                    stream.write((json.dumps({"execute": command, "arguments": args}) + "\n").encode())
                    stream.flush()
                    while True:
                        result = json.loads(stream.readline())
                        if "error" in result:
                            raise RuntimeError(result)
                        if "return" in result:
                            return result["return"]
                issue("qmp_capabilities", {})
                return issue(name, arguments or {})

    def key(self, chord):
        keys = chord.split("-")
        for down, ordered in [(True, keys), (False, list(reversed(keys)))]:
            self.command("input-send-event", {"events": [
                {"type": "key", "data": {"down": down, "key": {"type": "qcode", "data": k}}}
                for k in ordered
            ]})
            time.sleep(.08)

    def type(self, text):
        mapping = {
            " ": "spc", "\n": "ret", "-": "minus", "_": "shift-minus",
            ",": "comma", "/": "slash", ".": "dot", ":": "shift-semicolon", ";": "semicolon",
            "'": "apostrophe", '"': "shift-apostrophe", "=": "equal",
            "|": "shift-backslash", ">": "shift-dot", "@": "shift-2",
        }
        for char in text:
            key = mapping.get(char, "shift-" + char.lower() if char.isupper() else char)
            self.key(key)

    def screenshot(self, name):
        self.command("screendump", {"filename": str(ROOT / "out" / name), "format": "png"})
        print("Screenshot:", name, flush=True)

    def stop(self):
        if self.process and self.process.poll() is None:
            self.command("system_powerdown")
            try:
                self.process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                self.command("quit")
                self.process.wait(timeout=15)
                print("WARNING: ACPI shutdown timed out; QEMU stopped", flush=True)
        if hasattr(self, "err"):
            self.err.close()


def wait_for(predicate, seconds, message):
    start = time.monotonic()
    next_report = start
    while not predicate():
        now = time.monotonic()
        if now - start > seconds:
            raise TimeoutError(message)
        if now >= next_report:
            print("Waiting:", message, flush=True)
            next_report = now + 30
        time.sleep(1)


def job(work, name, script, timeout=180):
    path = work / "share" / "jobs" / (name + ".sh")
    path.parent.mkdir(exist_ok=True)
    if Path(str(path) + ".done").exists():
        raise RuntimeError("Job already exists: " + name)
    temp = path.with_suffix(".tmp")
    temp.write_text("set -euxo pipefail\n" + script + "\n")
    temp.rename(path)
    done = Path(str(path) + ".done")
    wait_for(done.exists, timeout, name)
    print(Path(str(path) + ".log").read_text(), flush=True)
    if done.read_text().strip() != "0":
        raise RuntimeError("Guest job failed: " + name)


def desktop_ready(work, name, username):
    job(work, name, f"""
uid=$(id -u {username})
for attempt in {{1..60}}; do
  socket=$(find /run/user/$uid -name 'sway-ipc.*.sock' -print -quit)
  if [[ -n $socket ]] && pgrep -u "$uid" -x waybar; then break; fi
  sleep 1
done
test -n "$socket"
pgrep -u "$uid" -x swaybg
runuser -u {username} -- env SWAYSOCK="$socket" XDG_RUNTIME_DIR="/run/user/$uid" swaymsg -t get_outputs
""", 120)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iso", type=Path)
    parser.add_argument("--work", type=Path, default=ROOT / "out/e2e")
    parser.add_argument("--resume-installed", action="store_true")
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run with sudo; no host disks are exposed to QEMU")
    work = args.work.resolve()
    share = work / "share"
    share.mkdir(parents=True, exist_ok=True)
    (share / "jobs").mkdir(exist_ok=True)
    for filename in ("guest-control.sh", "guest-live.sh", "verify-installed.sh"):
        shutil.copyfile(ROOT / "tests/qemu" / filename, share / filename)
    shutil.copyfile(ROOT / "airootfs/root/arche-smoke.lua", share / "arche-smoke.lua")
    shutil.copyfile(ROOT / "assets/arche-wallpaper-4k.svg", share / "wallpaper.svg")
    shutil.copyfile(ROOT / "assets/arche-logo.svg", share / "logo.svg")
    vm = None
    try:
        if not args.resume_installed:
            if (work / "target.qcow2").exists():
                parser.error("Refusing to overwrite existing virtual disk; use a fresh work directory")
            subprocess.run(["qemu-img", "create", "-f", "qcow2", str(work / "target.qcow2"), "25G"], check=True)
            shutil.copyfile("/usr/share/OVMF/OVMF_VARS_4M.fd", work / "vars.fd")
            vm = VM(work, args.iso.resolve())
            vm.start("live")
            # Stock ISO intentionally starts the interactive installer on tty1.
            # Start isolated test fixtures through QMP; all subsequent work is automated.
            print("Allowing 60 seconds for the live ISO to reach tty1", flush=True)
            time.sleep(60)
            vm.screenshot("e2e-live-boot.png")
            vm.key("ctrl-c")
            vm.type("mkdir -p /run/arche-test\nmount -t 9p -o trans=virtio,version=9p2000.L archetest /run/arche-test\n")
            vm.type("systemd-run --unit=arche-test-control bash /run/arche-test/guest-control.sh\n")
            job(work, "live-user", """
useradd -m -U -k /usr/share/arche/skel -G video,input -s /bin/zsh archepreview
mkdir -p /etc/systemd/system/getty@tty1.service.d
printf '[Service]\\nExecStart=\\nExecStart=-/usr/bin/agetty --autologin archepreview --noclear %%I $TERM\\n' > /etc/systemd/system/getty@tty1.service.d/override.conf
systemctl daemon-reload
systemctl restart getty@tty1
""")
            desktop_ready(work, "live-desktop-ready", "archepreview")
            time.sleep(3)
            vm.screenshot("e2e-live-desktop.png")
            job(work, "start-install", "systemd-run --unit=arche-install-test bash /run/arche-test/guest-live.sh")
            done = share / "install.done"
            wait_for(done.exists, 3600, "disk installation")
            print((share / "install.log").read_text(), flush=True)
            if done.read_text().strip() != "0":
                raise RuntimeError("Installation failed")
            vm.stop()

        vm = VM(work)
        vm.start("zen")
        job(work, "verify-zen", "bash /run/arche-test/verify-installed.sh zen", 300)
        desktop_ready(work, "installed-desktop-ready", "arche")
        time.sleep(3)
        vm.screenshot("e2e-installed-desktop.png")
        vm.key("meta_l-ret")
        time.sleep(3)
        vm.type("nvim /usr/share/arche/logo.svg\n")
        time.sleep(3)
        vm.key("esc")
        vm.type(":vsplit /usr/share/arche/wallpaper.svg\n")
        time.sleep(2)
        vm.key("meta_l-d")
        time.sleep(2)
        vm.screenshot("e2e-fuzzel-neovim.png")
        vm.key("esc")
        vm.key("meta_l-shift-q")
        vm.key("meta_l-ret")
        time.sleep(2)
        vm.type("clear\nuname -sr\nxfs_info /\nzramctl\n")
        time.sleep(2)
        vm.screenshot("e2e-storage-terminal.png")
        job(work, "select-lts", "bootctl set-oneshot arche-lts.conf\nsync")
        vm.stop()
        vm = VM(work)
        vm.start("lts")
        job(work, "verify-lts", "bash /run/arche-test/verify-installed.sh lts", 300)
        desktop_ready(work, "lts-desktop-ready", "arche")
        time.sleep(2)
        vm.screenshot("e2e-lts-desktop.png")
        print("ARCHE_E2E_PASS: installation, Zen cold boot, LTS cold boot, desktop", flush=True)
    finally:
        if vm:
            vm.stop()


if __name__ == "__main__":
    main()
