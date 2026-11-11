"""Sway login guards and packaged theme regressions, without launching a compositor."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
skel = root / 'pkgs/arche-tui-stack/files/usr/share/arche/skel'
sway = (skel / '.config/sway/config').read_text()
assert 'default_border none' in sway
assert 'default_floating_border none' in sway
assert 'for_window [all] border none' in sway
assert 'output * bg /usr/share/arche/wallpaper.svg fill' in sway
assert 'output eDP-1' not in sway
bar = json.loads((skel / '.config/waybar/config.jsonc').read_text())
assert bar['position'] == 'top' and bar['modules-center'][0] == 'sway/workspaces'
assert '@import url("litho-dark.css")' in (skel / '.config/waybar/style.css').read_text()
with tempfile.TemporaryDirectory() as directory:
    directory = Path(directory)
    for name, script in {
        'tty': '#!/bin/sh\nprintf "%s\\n" "${TEST_TTY:-/dev/tty1}"\n',
        'id': '#!/bin/sh\necho "${TEST_UID:-1000}"\n',
        'grep': '#!/bin/sh\ntest "${TEST_GPU:-no}" = yes\n',
        'sway': '#!/bin/sh\nprintf "START:%s:%s\\n" "$*" "${WLR_NO_HARDWARE_CURSORS:-}"\n',
    }.items():
        path = directory / name
        path.write_text(script)
        path.chmod(0o755)
    baseline = dict(os.environ, PATH=str(directory)+':'+os.environ['PATH'], XDG_VTNR='1')
    for key in ['WAYLAND_DISPLAY', 'DISPLAY', 'SSH_CONNECTION', 'WLR_NO_HARDWARE_CURSORS']:
        baseline.pop(key, None)
    cases = [({}, 'START::'), ({'TEST_GPU':'yes'}, 'START:--unsupported-gpu:1')]
    cases += [(change, '') for change in [
        {'XDG_VTNR':str(vt)} for vt in range(2,7)
    ] + [{'XDG_VTNR':''}, {'XDG_VTNR':'bad'}, {'WAYLAND_DISPLAY':'wayland-1'},
         {'DISPLAY':':0'}, {'SSH_CONNECTION':'remote'}, {'TEST_UID':'0'}, {'TEST_TTY':'/dev/pts/0'}]]
    for change, expected in cases:
        result = subprocess.run(['bash', str(root/'pkgs/arche-tui-stack/files/usr/share/arche/start-sway.sh')],
                                env=baseline | change, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == expected, (change, result.stdout)
print('Sway: TTY1/NVIDIA launch, recovery VTs, SSH/root guards and theme checks passed')
