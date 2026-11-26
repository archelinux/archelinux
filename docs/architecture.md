# Architecture and maintenance

An Arch-based system for Neovim, tmux, and local agent workflows. TTY1 starts Sway on normal user login, with a titlebar-free Litho Dark desktop with a one-pixel focus outline and a subtle Arche logo over dark violet gradients. TTY2–6 remain console recovery sessions. The new installer provisions Zsh with Oh My Zsh. Local model services are opt-in.

## Guided installer in new builds

The live console starts a downstream adaptation of Arch's [archinstall 4.5 source](https://github.com/archlinux/archinstall/tree/78982a624824aa415f59bf88c515676a589e3c55). During the build, `scripts/prepare-installer.sh` copies the official Python runtime and translations into the ISO and applies the patch in `installer/`. Upstream handles partitioning, encryption, bootloader setup and credentials. The Arche menu adds software choices, which are included in the saved configuration and final review. Guided layouts use XFS, including when encrypted. New accounts use the packaged `arche-zsh` environment. Its pinned Oh My Zsh sources and license are packaged locally, and updates go through pacman. The ISO carries the Arche repository and obtains selected Arch packages over the network.

The guided path installs `arche-workspace-defaults` for user configuration and `arche-maintenance` for package recovery. Neither requires a desktop or pins a kernel. The complete compatibility packages remain available. Selecting local inference also installs the optional service definitions. Selecting NVIDIA DKMS installs headers for the selected kernels.

The fixed XFS layout, mount tuning and unattended QEMU path described below refer to the earlier installer. Its explicit `--unattended` interface remains available to existing callers.

## Architecture

- **Storage:** XFS with reflink and CRC enabled, 512-byte inodes, 16 allocation groups. Root mounts with `rw,noatime,nodiratime,logbufs=8,logbsize=256k,allocsize=64M` and fstab dump/fsck fields `0 0`.
- **Kernels:** Arch's `linux-zen` and matching headers, plus `linux-lts` and headers. Zen is the permitted performance-kernel fallback; no CachyOS repository is required. LTS provides a recovery boot choice, not a security-hardening guarantee.
- **Boot:** systemd-boot on UEFI (provided by `systemd`), GRUB on BIOS; Zen default, explicit LTS entry, two-second timeout. The live USB boots LTS.
- **Memory:** RAM-sized zstd ZRAM at priority 100; the requested VM, dirty-page and inotify tuning lives in `airootfs/etc/sysctl.d/99-arche-perf.conf`.
- **Recovery:** weekly `paccache.timer` and a transaction hook retain three cached versions. `arche-rollback PACKAGE` selects the newest cached version older than the installed version using pacman's metadata and version ordering. It rejects prefix matches and missing history. This is package recovery, not a filesystem backup; related libraries may need coordinated downgrades. Only versions actually downloaded remain available.

## Packages and configuration

| Package | Contents |
| --- | --- |
| `arche-base` | Base development tools, both kernels, firmware, XFS, ZRAM, iwd, cache retention and rollback |
| `paru` | AUR helper built against Arch’s current pacman libraries |
| `arche-tui-stack` | Paru, Sway, top Waybar, Fuzzel, Mako, fonts/audio controls, tmux, Foot, CLI tools, shells, Neovim and preinstalled language servers |
| `arche-agentic-core` | uv, Bun from Arch extra, cargo-binstall, ast-grep, tree-sitter-cli, disabled inference user units |
| `arche-cuda` | Optional nvidia-open-dkms, nvidia-utils, Arch's `cuda` toolkit and cudnn |

`pkgs/*/PKGBUILD` are the canonical dependency lists. `packages.x86_64` defines the live console image. The ISO carries the optional arche-cuda metapackage in its local repository. The driver, toolkit and cuDNN download from Arch mirrors when selected. `arche-maintenance` provides `paccache-hook` with a locally maintained hook backed by `pacman-contrib`; there is no additional AUR hook dependency.

Live configuration overrides and package-owned files are linked into package sources with SHA-256 checksums. Package-owned `/usr` files live in `pkgs/*/files/`, outside the live overlay, so archiso does not pre-create files that pacman must install. After changing an overlay source, update its PKGBUILD checksum (`updpkgsums` from `pacman-contrib`). Package templates live under `/usr/share/arche/skel` to avoid colliding with Bash-owned skeleton files. The installer copies these into `/etc/skel` before creating the user. Installing metapackages on an existing Arch system does not overwrite user dotfiles; copy the templates explicitly.

The TUI package generates `zoxide init --cmd cd SHELL` and `direnv hook SHELL` once at build time and compiles the Zsh hook loader. Shell startup sources those files, sets `EDITOR=nvim` and `FZF_DEFAULT_COMMAND`, when the relevant tools are installed. The guided install initializes Oh My Zsh before loading these hooks. Rebuild the package when upgrading hook generators to refresh their output. Interactive prompt hooks still perform the intended directory tracking and environment checks.

Neovim starts LazyVim with the dark `archevim` colorscheme. On first launch, lazy.nvim downloads plugins into the user’s data directory. Language servers are available through the installer and Mason. LazyVim uses the system Lua language server when present and can install it through Mason otherwise. Lua, C, Vim, Vimdoc, query, Go, Python and Rust parsers are installed. Go, Python and Rust have baseline highlight queries. The recommended software includes the Go compiler and formatter, with `gopls` for Neovim. Inside Wayland, Neovim uses wl-copy/wl-paste for system clipboard synchronization. In console/SSH sessions, OSC 52 copies through supported terminals/tmux and paste uses the local yank register. Ctrl-h/j/k/l navigates Neovim windows and adjacent tmux panes.

## Build

Use a disposable privileged **Arch Linux** container or Arch build host with several tens of GiB free. The scripts install build dependencies and require network access to Arch mirrors and the upstream SwayFX and Basedpyright releases.

```sh
pacman -Syu --needed archiso grub git python python-yaml shellcheck xfsprogs
bash tests/check.sh
bash scripts/build-repo.sh
mkarchiso -v -w /tmp/archiso-tmp -o /tmp/archiso-out .
PYTHONPATH="$PWD/airootfs/usr/share/arche/installer" python -P tests/guided-installer.py
```

Run these from the repository root. `build-repo.sh` builds and lints the repository's PKGBUILDs as an unprivileged user. SwayFX uses the upstream tagged source archive. Basedpyright uses its upstream npm release and Arch provides Bun. The builder verifies source checksums and indexes the resulting binary packages in `pkgs/local-repo/arche.db.tar.zst`. The empty optional CUDA metapackage validates its dependency transaction with `pacman -Sp --needed` and packages metadata with `makepkg --nodeps`, avoiding GPU-driver installation and DKMS execution on the builder. The default packages use full dependency installation. Root invocations create a temporary builder with passwordless sudo for pacman only; normal users use their existing sudo access. The builder and its sudoers rule are removed at exit, and the build host pacman configuration is restored. The build rewrites the `[arche]` stanza in the profile's `pacman.conf` to point at the generated local repository for mkarchiso. Run it again after moving the checkout. Use fresh archiso work/output and package staging directories for each build; a nonempty package staging directory is rejected to prevent publishing stale artifacts.

The build host uses a local staging repository. The live USB boots Linux LTS and includes firmware, networking, the rolling-channel helper and release key. Both installer paths verify the signed public channel before changing disks and fetch the selected desktop packages during installation. The target retains its selected kernels and the signed channel for future upgrades. Existing installations can [enable rolling updates](rolling-updates.md).

Use the ISO build date for the filename and release title. If a second snapshot is published on the same day, supply a distinct release tag such as `rolling-YYYYMMDD.2`. Each snapshot has its own download URL and signed checksum.

## Install and recover

Use the [installation guide](getting-started.md) for the current console ISO and the earlier published image. The former unattended XFS installer is exercised by the [legacy boot test](../tests/qemu/README.md).

Use the LTS boot entry when Zen fails after an update. Use `sudo arche-rollback PACKAGE` for a cached older package. Reflink workspaces can be created with `cp -a --reflink=always SOURCE DESTINATION` on the same XFS filesystem.

Inference is opt-in, with no models downloaded:

```sh
sudo pacman -S ollama
systemctl --user enable --now ollama.service
# Alternatively install llama.cpp, set LLAMA_MODEL to an absolute GGUF path in
# ~/.config/arche/llama-server.env, then enable llama-server.service.
```

Both servers bind to loopback. User units normally stop at logout; enable lingering explicitly if desired. For supported NVIDIA hardware, choose `arche-cuda` in the installer or run `sudo pacman -S arche-cuda` after installation.

## CI and releases

`build-iso.yml` runs Docker explicitly on Ubuntu with `--privileged` and `/dev:/dev`, checks loop-device availability, and runs package build/lint, mkarchiso and runtime smoke tests. The build and boot checks also run monthly against the current Arch repositories to catch dependency drift. Monthly runs produce a test artifact. Publishing signed installation media uses the release workflow. ISOs are written into the workspace `out/` directory for artifact upload. `release.yml` calls the build workflow, waits for the QEMU installation and desktop boot to pass, then signs the ISO from that run. `release-pkgs.yml` builds a candidate without signing credentials. A separate signing job stages the candidate in a disposable checkout of the rolling channel. The upgrade job installs the verified 2.0.0 ISO into a VM, upgrades the installed desktop using the signed candidate, exercises package rollback, reapplies the update and cold-boots the upgraded desktop. Only that tested commit can be promoted. See [rolling updates](rolling-updates.md) for the user transition, signing and publication procedure.

## Verification status and VM acceptance

`tests/check.sh` checks shell syntax, source checksums, rollback edge cases, and formats a disposable sparse file to inspect XFS geometry. `arche-smoke-test` checks image binaries, LSP registration and parser loading and measures warm interactive shell startup over 20 samples. The median must stay below 15 ms for Bash and Fish and below 100 ms for Zsh with Oh My Zsh, the bureau theme and the default plugins.

Before publishing an ISO, install in a disposable QEMU VM with both UEFI and BIOS firmware. Verify the USB boots LTS and both default installed kernel entries boot, then run:

```sh
findmnt -no FSTYPE,OPTIONS /
xfs_info /                         # agcount=16, isize=512, reflink=1, crc=1
cat /etc/fstab
printf 'reflink test\n' > ~/clone-source
cp --reflink=always ~/clone-source ~/clone-copy
zramctl
systemctl is-enabled paccache.timer iwd systemd-networkd systemd-resolved
systemctl --user is-enabled ollama llama-server  # disabled
nvim example.lua                   # :checkhealth vim.lsp, :InspectTree
```

The release job boots the sealed ISO under UEFI, installs to a fresh XFS disk,
removes the ISO, and boots the installed system. The guest checks the hostname,
the user’s Zsh configuration, the running SwayFX compositor and Waybar. Build
logs, the installer screenshot and the installed desktop screenshot are available
in the GitHub Actions run. For the older dual-kernel acceptance run, see
[the recorded QEMU log](../tests/install-test.log).

## Sway / Litho Dark

The selected desktop adapts [okubax/dotfiles](https://github.com/okubax/dotfiles)'s
Litho Dark palette and inset Waybar panel with a centered clock. Provenance and the upstream
license are installed in `/usr/share/doc/arche-tui-stack/`. Tiled and floating windows have a one-pixel outline. The recommended SwayFX compositor adds backdrop blur and gives Waybar and windows a nine-pixel corner radius. The workspace highlight sits eight pixels inside the panel and has a three-pixel radius. Applications that draw their own
internal chrome remain responsible for that chrome.

Alt+Return opens Foot; Alt+d opens Fuzzel; Alt+Shift+q closes a window;
Alt+h/j/k/l moves focus; Alt+r enters resize mode; Alt+Shift+c reloads
configuration; Alt+Shift+e exits Sway. No upstream dotfile installer or personal
cloud/service configuration is run. Media keys use WirePlumber and playerctl.

Login hooks exist for Zsh, Bash and Fish. They require a local non-root TTY1
session, no existing display, and no SSH connection. NVIDIA/nouveau detection
sets `WLR_NO_HARDWARE_CURSORS=1` and passes `--unsupported-gpu`; this is a fallback,
not a guarantee for every driver. No hook is added to the live root installer.
`useradd -m -U -k /usr/share/arche/skel` copies all templates directly into the
new user's home and assigns their ownership. Package templates never claim
Bash-owned `/etc/skel` files.

Sway fills the output with Twin Blades from `/usr/share/arche/twin-blades.jpg`. The artwork comes from the [dharmx/walls collection](https://github.com/dharmx/walls/blob/e8d8a42e4fbecb2cf9619995edbc7ce19610bbd8/anime/aeb9uhrbr41a1.webp). Artist and redistribution license are unverified.

For automated UEFI installation acceptance on a disposable qcow2 disk, see
[QEMU installation tests](../tests/qemu/README.md).
