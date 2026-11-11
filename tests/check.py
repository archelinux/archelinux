"""Source integrity and rollback regression checks without touching the host cache."""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
for recipe in (root / 'pkgs').glob('*/PKGBUILD'):
    text = recipe.read_text()
    sources = re.search(r'^source=\((.*)\)$', text, re.M)[1].split()
    sums = re.search(r'^sha256sums=\((.*)\)$', text, re.M)[1].split()
    assert len(sources) == len(sums)
    for source, digest in zip(sources, sums):
        assert hashlib.sha256((recipe.parent / source.strip("'")).read_bytes()).hexdigest() == digest.strip("'"), recipe

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    cache = tmp / 'cache'
    cache.mkdir()
    # Similar names, duplicates, newer-than-installed versions, and signatures.
    for name in ['foo-1.0-1', 'foo-2.0-1', 'foo-3.0-1', 'foo-10.0-1', 'foo-extra-2.5-1']:
        (cache / (name + '-any.pkg.tar.zst')).touch()
    (cache / 'foo-2.0-1-any.pkg.tar.zst.sig').touch()
    script = tmp / 'rollback'
    script.write_text((root / 'pkgs/arche-base/files/usr/bin/arche-rollback').read_text().replace('/var/cache/pacman/pkg', str(cache)))
    commands = {
        'pacman': '''#!/bin/bash
case $1 in
-Q) echo 'foo 3.0-1';;
-Qp) file=${3##*/}; file=${file%-any.pkg.tar.zst}; echo "${file%-*-*} ${file##foo-}";;
-U) printf '%s\\n' "$*";;
esac
''',
        'vercmp': '''#!/usr/bin/env python3
import sys
parts=lambda s: tuple(int(x) for x in s.replace('-', '.').split('.'))
a,b=map(parts,sys.argv[1:]);print((a>b)-(a<b))
''',
        'sudo': '#!/bin/bash\nexec "$@"\n',
    }
    for name, content in commands.items():
        path = tmp / name
        path.write_text(content)
        path.chmod(0o755)
    env = dict(os.environ, PATH=str(tmp) + ':' + os.environ['PATH'])
    result = subprocess.run(['bash', str(script), 'foo'], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'foo-2.0-1-any.pkg.tar.zst' in result.stdout, result.stdout
    for f in cache.iterdir():
        f.unlink()
    assert subprocess.run(['bash', str(script), 'foo'], env=env, capture_output=True).returncode == 1
    assert subprocess.run(['bash', str(script)], env=env, capture_output=True).returncode == 2
print('Source checksums and rollback regressions passed')
