"""Archelinux choices for the archinstall guided workflow."""
from pathlib import Path
import shutil
import subprocess

from archinstall.lib.menu.helpers import Selection
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType

# Sway's key bindings, bar and session hooks use these companions.
SWAY_SESSION = 'foot fuzzel mako swaybg waybar python iproute2 swayidle swaylock xorg-xwayland xdg-desktop-portal-wlr xdg-desktop-portal-gtk grim slurp wl-clipboard librsvg brightnessctl wireplumber playerctl pipewire pipewire-pulse pipewire-alsa ttf-jetbrains-mono-nerd ttf-nerd-fonts-symbols-mono noto-fonts noto-fonts-emoji'.split()
ALWAYS_INSTALLED = ['arche-workspace-defaults', 'arche-maintenance', 'arche-zsh']
TOOLS = {
    'arche-base': 'Full system profile: Zen and LTS kernels and headers, base-devel, firmware and XFS tuning',
    'arche-tui-stack': 'Full terminal desktop: Sway, terminals, tmux, Neovim, language servers and CLI tools',
    'arche-agentic-core': 'Developer runtimes: Python, uv, Bun, cargo-binstall, ast-grep and tree-sitter CLI',
    'arche-cuda': 'NVIDIA bundle: full base profile, open DKMS driver, CUDA and cuDNN (large Arch downloads)',
    'sway': 'Arche tiling desktop with Foot, Fuzzel, Waybar, audio, screen sharing and locking',
    'arche-swayfx': 'Sway workspace with backdrop blur and rounded window corners (replaces stock Sway)',
    'tmux': 'Terminal multiplexer', 'neovim': 'LazyVim editor with the archevim colorscheme (first launch downloads plugins)',
    'foot': 'Wayland terminal', 'alacritty': 'GPU-accelerated terminal',
    'bat': 'File viewer with syntax highlighting', 'eza': 'Directory listings',
    'ripgrep': 'Search file contents', 'fd': 'Find files', 'fzf': 'Fuzzy finder',
    'zoxide': 'Directory jumping', 'direnv': 'Per-project environments',
    'git': 'Version control', 'git-delta': 'Readable terminal diffs',
    'lazygit': 'Interactive Git client', 'github-cli': 'GitHub CLI (gh)',
    'arche-waybar-github': 'GitHub PR and issue notifications for Waybar (includes gh)',
    'yazi': 'Terminal file manager', 'btop': 'Interactive system monitor',
    'spotify': 'Spotify desktop app (Flathub)',
    'spotify-player': 'Terminal Spotify client (Premium required)',
    'jq': 'JSON queries', 'yq': 'YAML queries',
    'wl-clipboard': 'Wayland clipboard', 'xclip': 'X11 clipboard',
    'base-devel': 'Arch package building tools', 'python': 'Python runtime',
    'uv': 'Python project manager', 'bun': 'JavaScript runtime',
    'cargo-binstall': 'Install Rust binaries', 'ast-grep': 'Structural code search',
    'tree-sitter-cli': 'Parser development tools', 'gopls': 'Go language server',
    'lua-language-server': 'Lua language server', 'basedpyright': 'Python language server',
    'rust-analyzer': 'Rust language server', 'ollama': 'Local model runtime',
    'llama.cpp': 'GGUF inference tools', 'cuda': 'NVIDIA compute toolkit',
    'cudnn': 'NVIDIA neural network library', 'nvidia-open-dkms': 'NVIDIA open kernel modules',
}
DEFAULT_TOOLS = 'arche-swayfx tmux neovim bat eza ripgrep fd fzf zoxide direnv git git-delta lazygit jq base-devel'.split()


def installation_review(config):
    from archinstall.lib.models.config import SummaryLevel
    from archinstall.lib.models.device import DiskLayoutType, EncryptionType

    disk = config.disk_config
    lines = []
    if disk.config_type == DiskLayoutType.Pre_mount:
        lines.append(f'Install into the existing XFS mount at {disk.mountpoint}.')
        lines.append('The existing storage layout determines encryption.')
    else:
        actions = {'create': 'Create', 'modify': 'Reformat', 'delete': 'Delete', 'existing': 'Keep'}
        for device in disk.device_modifications:
            action = 'Erase partition table' if device.wipe else 'Use existing partition table'
            lines.append(f'{device.device_path}   {action}')
            for part in device.partitions:
                detail = [str(part.dev_path or part.start.format_highest() + ' offset'),
                          actions[part.status.value], part.length.format_highest()]
                if part.fs_type:
                    detail.append(part.fs_type.value)
                if part.mountpoint:
                    detail.append(str(part.mountpoint))
                lines.append('  ' + '   '.join(detail))
        if disk.lvm_config:
            lines.extend(disk.lvm_config.summary(SummaryLevel.DETAILED))
        encryption = disk.disk_encryption
        if encryption and encryption.encryption_type != EncryptionType.NO_ENCRYPTION:
            lines.extend(encryption.summary(SummaryLevel.DETAILED))
            for volume in [*encryption.partitions, *encryption.lvm_volumes]:
                lines.append(f'  Encrypt {volume.mountpoint or volume.dev_path or volume.obj_id}')
        else:
            lines.append('Installer disk encryption is off.')

    lines.extend(['', 'New accounts use Zsh with Oh My Zsh.',
                  'Kernels: ' + ', '.join(config.kernels),
                  'Always installed: ' + ', '.join(ALWAYS_INSTALLED),
                  'Arche tools: ' + (', '.join(config.arche_tools) or 'none')])
    lines.append(f'Hostname: {config.hostname}   Time zone: {config.timezone}')
    for settings in (config.auth_config, config.network_config, config.bootloader_config, config.profile_config,
                     config.locale_config, config.swap, config.app_config):
        if settings:
            lines.extend(settings.summary(SummaryLevel.BASIC))
    if config.packages:
        lines.append('Additional packages: ' + ', '.join(config.packages))
    if config.services:
        lines.append('Enable services: ' + ', '.join(config.services))
    if config.custom_commands:
        lines.append(f'Run {len(config.custom_commands)} custom post-install commands from the supplied configuration.')
    lines.append('archelinux packages come from the ISO. Arch dependencies download from mirrors.')
    return '\n'.join(lines)


async def select_tools(preset):
    group = MenuItemGroup([MenuItem(f'{name}  {description}', value=name)
                           for name, description in TOOLS.items()], sort_items=False)
    group.set_selected_by_value(preset)
    result = await Selection(group, header='Space toggles a tool. Sway includes Foot, Fuzzel, Waybar, audio, screen sharing and locking. Clear all selections for a console install.',
                             multi=True, enable_filter=True, allow_skip=True, allow_reset=True).show()
    if result.type_ == ResultType.Reset:
        return []
    return result.get_values() if result.type_ == ResultType.Selection else preset


def normalize_tools(tools):
    if not isinstance(tools, list) or not all(isinstance(name, str) for name in tools):
        raise ValueError('Invalid Arche software selection')
    aliases = {'bun-bin': 'bun', 'basedpyright-bin': 'basedpyright'}
    return list(dict.fromkeys(aliases.get(name, name) for name in tools))


def validate_tools(tools):
    if not isinstance(tools, list) or any(name not in TOOLS for name in tools):
        raise ValueError('Invalid Arche software selection')


def root_layout_error(layout):
    """Reject incompatible plans before archinstall performs disk operations."""
    from archinstall.lib.models.device import DiskLayoutType, FilesystemType, ModificationStatus

    if layout is None:
        return None
    if layout.config_type == DiskLayoutType.Pre_mount:
        mounted = subprocess.run(
            ['findmnt', '--noheadings', '--output', 'FSTYPE', '--mountpoint', str(layout.mountpoint)],
            capture_output=True, text=True, check=False,
        )
        if mounted.returncode == 0 and mounted.stdout.strip() == 'xfs':
            return None
        return 'Mount an XFS root filesystem at the installation mountpoint.'
    volumes = [part for device in layout.device_modifications for part in device.partitions]
    if layout.lvm_config:
        volumes.extend(layout.lvm_config.get_all_volumes())
    roots = [vol for vol in volumes if vol.status != ModificationStatus.DELETE and vol.is_root()]
    if len(roots) != 1 or roots[0].fs_type != FilesystemType.XFS:
        return 'Archelinux requires one XFS root filesystem mounted at /.'
    return None


def package_plan(config):
    validate_tools(config.arche_tools)
    tools = ['flatpak' if name == 'spotify' else name for name in config.arche_tools]
    packages = [*ALWAYS_INSTALLED, *tools]
    if 'arche-swayfx' in packages and 'sway' in packages:
        packages.remove('sway')
    if {'sway', 'arche-swayfx'}.intersection(packages):
        packages.extend(SWAY_SESSION)
    if {'ollama', 'llama.cpp'}.intersection(packages + config.packages):
        packages.append('arche-inference-defaults')
    if 'neovim' in packages or 'neovim' in config.packages:
        packages.extend(['arche-neovim-parsers', 'git', 'gcc', 'tree-sitter-cli', 'ripgrep', 'fd'])
        packages.extend('tree-sitter-' + lang for lang in ('lua', 'c', 'vim', 'vimdoc', 'query', 'python', 'rust'))
    if {'arche-cuda', 'nvidia-open-dkms'}.intersection(packages + config.packages):
        packages.extend(kernel + '-headers' for kernel in config.kernels)
        packages.append('nvidia-utils')
    return list(dict.fromkeys(packages))


def prepare_target(installation, config):
    target = installation.target
    repo = Path('/usr/share/arche/repo')
    shutil.copytree(repo, target / repo.relative_to('/'), dirs_exist_ok=True)
    installation.add_additional_packages(package_plan(config))
    if 'spotify' in config.arche_tools:
        installation.arch_chroot('flatpak remote-add --system --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo')
        installation.arch_chroot('flatpak install --system --noninteractive flathub com.spotify.Client')
    shutil.copytree(target / 'usr/share/arche/skel', target / 'etc/skel', dirs_exist_ok=True)
    # /etc/os-release can be a vendor symlink. Replace the link itself.
    identity = target / 'etc/os-release'
    identity.unlink(missing_ok=True)
    shutil.copyfile('/etc/os-release', identity)
    shutil.copyfile(target / 'usr/share/arche/zshrc', target / 'etc/skel/.zshrc')
    installation.arch_chroot('useradd -D -s /bin/zsh')
    installation.enable_service('paccache.timer')
