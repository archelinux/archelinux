"""Check trust isolation, portable recipe inputs and CI runner/device requirements."""
import importlib.util
from pathlib import Path
import re
import subprocess
import tempfile
import yaml

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('configure_repo', root / 'scripts/configure-repo.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fixture = '''[options]
SigLevel = Required DatabaseOptional
[arche]
SigLevel = Never
Server = file:///old
[core]
Include = /etc/pacman.d/mirrorlist
[extra]
SigLevel = Required DatabaseOptional
Include = /etc/pacman.d/mirrorlist
'''
configured = module.configure(fixture, '/new/repo')
assert configured.count('[arche]') == 1
assert '[core]\nInclude = /etc/pacman.d/mirrorlist' in configured
assert '[extra]\nSigLevel = Required DatabaseOptional' in configured
assert '[arche]\nSigLevel = Optional TrustAll\nServer = file:///new/repo' in configured
assert module.configure(configured, '/new/repo') == configured
for filename, server in [('pacman.conf', '/workspace/pkgs/local-repo'), ('airootfs/etc/pacman.conf', '/usr/share/arche/repo')]:
    text = (root / filename).read_text()
    assert re.search(r'^SigLevel\s*=\s*Required DatabaseOptional$', text, re.M)
    assert '[arche]\nSigLevel = Optional TrustAll\nServer = file://' in text
    if filename.startswith('airootfs'):
        assert 'Server = file://' + server in text

for path in (root / '.github/workflows').glob('*.yml'):
    workflow = yaml.safe_load(path.read_text())
    assert workflow.get('jobs'), path
    for job in workflow['jobs'].values():
        assert job['runs-on'] == 'ubuntu-latest'
        assert isinstance(job['steps'], list)
iso = yaml.safe_load((root / '.github/workflows/build-iso.yml').read_text())['jobs']['iso']
assert 'container' not in iso
command = next(step['run'] for step in iso['steps'] if step.get('name') == 'Build Archelinux ISO')
for required in ['docker run --rm --privileged', '-v /dev:/dev', '-w /workspace', '-o /workspace/out', './scripts/build-repo.sh']:
    assert required in command, required
assert iso['steps'][-1]['with']['path'] == 'out/*.iso'
release = yaml.safe_load((root / '.github/workflows/release-pkgs.yml').read_text())
assert release['jobs']['build']['steps'][-1]['with']['path'] == 'pkgs/local-repo/*.pkg.tar.zst'

# Source trusted local recipes to read arrays rather than matching their formatting.
# Each recipe is also copied with dereferenced inputs, as in the real builder.
for recipe in (root / 'pkgs').glob('*/PKGBUILD'):
    source_list = subprocess.check_output(['bash', '-c', 'source "$1"; printf "%s\\n" "${source[@]}"', 'bash', str(recipe)], text=True).splitlines()
    for source in filter(None, source_list):
        assert not source.startswith('/'), (recipe, source)
        assert (recipe.parent / source).is_file(), (recipe, source)
        assert not (recipe.parent / source).resolve().is_relative_to(root / 'airootfs/usr'), \
            'Package-owned /usr files must not be pre-created by the live overlay'
    with tempfile.TemporaryDirectory() as temp:
        subprocess.run(['cp', '-rL', str(recipe.parent) + '/.', temp], check=True)
        for source in filter(None, source_list):
            assert (Path(temp) / source).is_file()
print('Repository trust, portable PKGBUILD inputs and workflow pre-flight checks passed')

# The live installer needs an enabled mirror, not pacman-mirrorlist's commented defaults.
mirror = (root / 'airootfs/etc/pacman.d/mirrorlist').read_text()
assert any(line.startswith('Server = https://') and '$repo' in line and '$arch' in line
           for line in mirror.splitlines()), 'Live ISO has no enabled HTTPS Arch mirror'
