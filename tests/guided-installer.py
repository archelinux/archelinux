"""Run with the staged, patched Arch runtime on PYTHONPATH; no target disks needed."""
from types import SimpleNamespace
from unittest.mock import patch

from archinstall.lib.models.device import DiskLayoutType, EncryptionType, FilesystemType, ModificationStatus
from archinstall.arche import package_plan, root_layout_error
from archinstall.lib.args import ArchConfig, Arguments
from archinstall.lib.global_menu import GlobalMenu
from archinstall.scripts import guided

config = ArchConfig.from_config({}, Arguments())
assert config.hostname == 'archelinux'
assert ArchConfig.from_config({'hostname': 'workstation'}, Arguments()).hostname == 'workstation'
assert {'bat', 'tmux', 'arche-swayfx', 'neovim'} <= set(config.arche_tools)
assert set(config.kernels) == {'linux-zen', 'linux-lts'}
assert {'foot', 'swaylock', 'fuzzel', 'arche-zsh', 'grim', 'slurp', 'wl-clipboard'} <= set(package_plan(config))
assert 'cuda' not in package_plan(config)
assert 'github-cli' not in package_plan(config)
bundles = {'arche-base', 'arche-tui-stack', 'arche-agentic-core', 'arche-cuda'}
assert bundles.isdisjoint(package_plan(config))
for bundle in bundles:
    choice = ArchConfig.from_config({'arche_tools': [bundle], 'kernels': ['linux']}, Arguments())
    plan = package_plan(ArchConfig.from_config(choice.safe_config(), Arguments()))
    assert set(plan) & bundles == {bundle}
    assert ('linux-headers' in plan) == (bundle == 'arche-cuda')
legacy = ArchConfig.from_config({'arche_tools': ['bun-bin', 'basedpyright-bin']}, Arguments())
assert legacy.arche_tools == ['bun', 'basedpyright']
legacy_terminals = ArchConfig.from_config({'arche_tools': ['alacritty', 'foot']}, Arguments())
assert legacy_terminals.arche_tools == ['foot']
assert 'foot' in package_plan(legacy_terminals) and 'alacritty' not in package_plan(legacy_terminals)
config.arche_tools = ['github-cli']
assert 'github-cli' in package_plan(config)
assert ArchConfig.from_config(config.safe_config(), Arguments()).arche_tools == ['github-cli']
for selection in (['arche-swayfx'], ['sway', 'arche-swayfx']):
    config.arche_tools = selection
    plan = package_plan(config)
    assert {'arche-swayfx', 'foot', 'grim', 'waybar'} <= set(plan) and 'sway' not in plan
optional_tools = {'paru', 'yazi', 'btop', 'arche-waybar-github'}
assert optional_tools.isdisjoint(package_plan(ArchConfig.from_config({}, Arguments())))
for name in sorted(optional_tools):
    config.arche_tools = [name]
    restored = ArchConfig.from_config(config.safe_config(), Arguments())
    assert set(package_plan(restored)) & optional_tools == {name}
    assert 'grim' not in package_plan(restored)
for selected in ([], ['spotify'], ['spotify-player'], ['spotify', 'spotify-player']):
    config.arche_tools = selected
    restored = ArchConfig.from_config(config.safe_config(), Arguments())
    assert restored.arche_tools == selected
    plan = package_plan(restored)
    assert 'spotify' not in plan
    assert ('flatpak' in plan) == ('spotify' in selected)
    assert ('spotify-player' in plan) == ('spotify-player' in selected)
config.arche_tools = ['neovim']
assert {'git', 'unzip', 'gcc', 'tree-sitter-cli', 'fd', 'ripgrep', 'arche-neovim-parsers'} <= set(package_plan(config))
# Cancel the first interactive screen. No configuration is written and no disk is touched.
with patch.object(guided.tui, 'run', return_value=None) as render:
    try:
        guided.main(SimpleNamespace(config=config, args=Arguments()))
    except SystemExit as stop:
        assert stop.code == 0
    render.assert_called_once()
    menu = render.call_args.args[0]
    assert isinstance(menu, GlobalMenu) and menu._title == 'archelinux'
for key in ('arche_tools', 'disk_config', 'kernels', 'packages'):
    assert menu._item_group.find_by_key(key).action is not None
config = ArchConfig.from_config({'arche_tools': [], 'kernels': ['linux']}, Arguments())
assert set(package_plan(config)) == {'arche-workspace-defaults', 'arche-maintenance', 'arche-zsh'}
assert ArchConfig.from_config(config.safe_config(), Arguments()).arche_tools == []
config.arche_tools = ['bat', 'nvidia-open-dkms', 'ollama']
assert {'bat', 'linux-headers', 'arche-inference-defaults'} <= set(package_plan(config))
assert not {'sway', 'tmux', 'linux-lts-headers', 'cuda'} & set(package_plan(config))
for invalid in ({'arche_shell': 'fish'}, {'arche_tools': ['missing-package']}):
    try:
        ArchConfig.from_config(invalid, Arguments())
    except ValueError:
        continue
    raise AssertionError(invalid)
layout = SimpleNamespace(config_type=DiskLayoutType.Default, lvm_config=None, device_modifications=[])
assert root_layout_error(layout)
part = SimpleNamespace(status=ModificationStatus.CREATE, fs_type=FilesystemType.XFS, is_root=lambda: True)
layout.device_modifications = [SimpleNamespace(partitions=[part])]
assert root_layout_error(layout) is None
part.fs_type = FilesystemType.EXT4
assert root_layout_error(layout)
print('Arche menus, defaults, XFS validation, saved configs and package plans passed')

# The final interactive review distinguishes whole-disk erase from partition changes.
from archinstall.arche import installation_review

size = SimpleNamespace(format_highest=lambda: '16 GiB')
part = SimpleNamespace(dev_path='/dev/example2', status=ModificationStatus.MODIFY,
                       length=size, fs_type=FilesystemType.XFS, mountpoint='/')
drive = SimpleNamespace(device_path='/dev/example', wipe=False, partitions=[part])
config.disk_config = SimpleNamespace(config_type=DiskLayoutType.Manual, lvm_config=None,
                                     disk_encryption=None, device_modifications=[drive])
review = installation_review(config)
for value in ('Use existing partition table', '/dev/example2', 'Reformat', 'xfs',
              'encryption is off', 'bat', 'linux', 'Oh My Zsh'):
    assert value in review, value
drive.wipe = True
assert 'Erase partition table' in installation_review(config)
config.disk_config.disk_encryption = SimpleNamespace(
    encryption_type=EncryptionType.LUKS, summary=lambda _: ['LUKS'], partitions=[part], lvm_volumes=[],
)
review = installation_review(config)
assert 'Encrypt /' in review and 'encryption is off' not in review
config.disk_config = SimpleNamespace(config_type=DiskLayoutType.Pre_mount, mountpoint='/mnt')
review = installation_review(config)
assert '/mnt' in review and 'Erase partition table' not in review
print('Direct menu entry, title and final disk review passed')
