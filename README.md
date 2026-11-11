# Arche Linux

An Arch-based system for Neovim, tmux, and local agent workflows. TTY1 starts Sway on normal user login, with a borderless Litho Dark desktop and a centered Arche logo on black. TTY2–6 remain console recovery sessions. No display manager, Oh My Zsh, or model server is started automatically.

## Architecture

- **Storage:** XFS with reflink and CRC enabled, 512-byte inodes, 16 allocation groups. Root mounts with `rw,noatime,nodiratime,logbufs=8,logbsize=256k,allocsize=64M` and fstab dump/fsck fields `0 0`.
- **Kernels:** Arch's `linux-zen` and matching headers, plus `linux-lts` and headers. Zen is the permitted performance-kernel fallback; no CachyOS repository is required. LTS provides a recovery boot choice, not a security-hardening guarantee.
- **Boot:** systemd-boot on UEFI (provided by `systemd`), GRUB on BIOS; Zen default, explicit LTS entry, two-second timeout. Both kernels also boot the live image.
- **Memory:** RAM-sized zstd ZRAM at priority 100; the requested VM, dirty-page and inotify tuning lives in `airootfs/etc/sysctl.d/99-arche-perf.conf`.
- **Recovery:** weekly `paccache.timer` and a transaction hook retain three cached versions. `arche-rollback PACKAGE` selects the newest cached version older than the installed version using pacman's metadata and version ordering. It rejects prefix matches and missing history. This is package recovery, not a filesystem backup; related libraries may need coordinated downgrades. Only versions actually downloaded remain available.

## Packages and configuration

| Package | Contents |
| --- | --- |
| `arche-base` | Base development tools, both kernels, firmware, XFS, ZRAM, NetworkManager, cache retention and rollback |
| `arche-tui-stack` | Sway, top Waybar, Fuzzel, Mako, fonts/audio controls, tmux, terminals, CLI tools, shells, Neovim and preinstalled language servers |
| `arche-agentic-core` | uv, pinned AUR bun-bin, cargo-binstall, ast-grep, tree-sitter-cli, disabled inference user units |
| `arche-cuda` | Optional nvidia-open-dkms, nvidia-utils, Arch's `cuda` toolkit and cudnn |

`pkgs/*/PKGBUILD` are the canonical dependency lists. `packages.x86_64` adds only live-media tools. CUDA is built as a metapackage but excluded from the default image and installation. `arche-base` provides `paccache-hook` with a locally maintained hook backed by `pacman-contrib`; there is no additional AUR hook dependency.

Live configuration overrides and package-owned files are linked into package sources with SHA-256 checksums. Package-owned `/usr` files live in `pkgs/*/files/`, outside the live overlay, so archiso does not pre-create files that pacman must install. After changing an overlay source, update its PKGBUILD checksum (`updpkgsums` from `pacman-contrib`). Package templates live under `/usr/share/arche/skel` to avoid colliding with Bash-owned skeleton files. The installer copies these into `/etc/skel` before creating the user. Installing metapackages on an existing Arch system does not overwrite user dotfiles; copy the templates explicitly.

The TUI package generates `zoxide init --cmd cd SHELL` and `direnv hook SHELL` once at build time and compiles the Zsh hook loader. Shell startup sources those files, sets `EDITOR=nvim` and `FZF_DEFAULT_COMMAND`, and runs no plugin manager. Rebuild the package when upgrading hook generators to refresh their output. Interactive prompt hooks still perform the intended directory tracking and environment checks.

Neovim uses its built-in LSP API (0.11+) with no Mason or plugin download. Lua, C, Vim, Vimdoc, query, Python and Rust parsers are installed; Python and Rust have baseline highlight queries. Other filetypes retain standard syntax highlighting; Go has its preinstalled LSP. Inside Wayland, Neovim uses wl-copy/wl-paste for system clipboard synchronization. In console/SSH sessions, OSC 52 copies through supported terminals/tmux and paste uses the local yank register. Ctrl-h/j/k/l navigates Neovim windows and adjacent tmux panes.

## Build

Use a disposable privileged **Arch Linux** container or Arch build host with several tens of GiB free. The scripts install build dependencies and require network access to Arch mirrors, AUR and upstream Bun releases.

```sh
pacman -Syu --needed archiso grub git python python-yaml shellcheck xfsprogs
bash tests/check.sh
bash scripts/build-repo.sh
mkarchiso -v -w /tmp/archiso-tmp -o /tmp/archiso-out .
arch-chroot /tmp/archiso-tmp/x86_64/airootfs /bin/bash /root/arche-smoke-test
```

Run these from the repository root. `build-repo.sh` builds all four packages as an unprivileged user, runs namcap, and builds bun-bin plus basedpyright-bin (which provides basedpyright) from pinned AUR revisions with upstream source checksums. Bun and Basedpyright are built and indexed first in `pkgs/local-repo/arche.db.tar.zst`. Internal packages then build in base/TUI/agentic/CUDA order with `makepkg --syncdeps --needed --noconfirm`, refreshing the local database after each package. The empty optional CUDA metapackage validates its dependency transaction with `pacman -Sp --needed` and packages metadata with `makepkg --nodeps`, avoiding GPU-driver installation and DKMS execution on the builder. The default packages use full dependency installation. Root invocations create a temporary builder with passwordless sudo for pacman only; normal users use their existing sudo access. The builder and its sudoers rule are removed at exit, and the build host pacman configuration is restored. The build rewrites the `[arche]` stanza in the profile's `pacman.conf` to point at the generated local repository and generates the live image's corresponding configuration. Run it again after moving the checkout. Use fresh archiso work/output and package staging directories for each build; a nonempty package staging directory is rejected to prevent publishing stale artifacts.

The local repository contains unsigned packages built with the ISO and has a scoped `SigLevel = Optional TrustAll`; official Arch repositories continue to require signatures. The installer copies this repository into the target so its package sources remain accessible after reboot. Configure a signed release repository for future Arche package updates.

## Install and recover

Boot the ISO, connect using `nmcli`, and run `/root/arche-install` (also offered on tty1). The installer opens `cfdisk`; create a root partition of at least 16 GiB and a 1 GiB EFI system partition for UEFI. BIOS/GPT also needs a BIOS boot partition. The installer validates distinct unmounted partitions and asks for `ERASE` before formatting. Partition changes made in cfdisk take effect when you explicitly write them.

Locale defaults to `en_US.UTF-8`; timezone defaults to UTC. The installer initializes pacman's keyring, rebuilds normal installed-system initramfs images, creates the user, enables NetworkManager and paccache, and installs the bootloader. A network connection is required for official packages. It does not support encryption, automated disk partitioning, or non-XFS roots.

Use the LTS boot entry when Zen fails after an update. Use `sudo arche-rollback PACKAGE` for a cached older package. Reflink workspaces can be created with `cp -a --reflink=always SOURCE DESTINATION` on the same XFS filesystem.

Inference is opt-in, with no models downloaded:

```sh
sudo pacman -S ollama
systemctl --user enable --now ollama.service
# Alternatively install llama.cpp, set LLAMA_MODEL to an absolute GGUF path in
# ~/.config/arche/llama-server.env, then enable llama-server.service.
```

Both servers bind to loopback. User units normally stop at logout; enable lingering explicitly if desired. For supported NVIDIA hardware, install `arche-cuda` after configuring a repository containing it.

## CI and releases

`build-iso.yml` runs Docker explicitly on Ubuntu with `--privileged` and `/dev:/dev`, checks loop-device availability, and runs package build/lint, mkarchiso and runtime smoke tests. ISOs are written into the workspace `out/` directory for artifact upload. `release.yml` uses the same package preparation for manual ISO releases. `release-pkgs.yml` builds packages without signing secrets, then signs them in a separate `package-release` environment and publishes an immutable GitHub Release tag.

Configure these environment secrets before running package publication:

- `ARCHE_SIGNING_KEY`: ASCII-armored persistent private key.
- `ARCHE_SIGNING_FINGERPRINT`: signing key fingerprint.
- `ARCHE_SIGNING_PASSPHRASE`: key passphrase (empty for an unencrypted CI key).

Verify the published public key fingerprint through a trusted channel, import and locally sign it with `pacman-key`, then replace the local `[arche]` entry with:

```ini
[arche]
SigLevel = Required DatabaseRequired
Server = https://github.com/archelinux/archelinux/releases/download/pkgs-RUN_ID-RUN_ATTEMPT
```

Each immutable tag includes signed package archives, signed `arche.db` / `arche.files`, and the public key. Point clients at the new tag to adopt a later repository release. The existing ISO release workflow's ephemeral key is separate from this persistent package signing key.

## Verification status and VM acceptance

`tests/check.sh` checks shell syntax, source checksums, rollback edge cases, and formats a disposable sparse file to inspect XFS geometry. `arche-smoke-test` checks image binaries, LSP registration and parser loading and reports 20-sample warm shell startup medians, enforcing the requested 15 ms budget. Runner load and hardware affect that budget; it is not a universal latency guarantee.

Before publishing an ISO, install in a disposable QEMU VM with both UEFI and BIOS firmware. Verify both kernel entries boot, then run:

```sh
findmnt -no FSTYPE,OPTIONS /
xfs_info /                         # agcount=16, isize=512, reflink=1, crc=1
cat /etc/fstab
printf 'reflink test\n' > ~/clone-source
cp --reflink=always ~/clone-source ~/clone-copy
zramctl
systemctl is-enabled paccache.timer NetworkManager
systemctl --user is-enabled ollama llama-server  # disabled
nvim example.lua                   # :checkhealth vim.lsp, :InspectTree
```

Local validation on 2026-11-11 completed metapackage builds, namcap (with expected
metapackage dependency warnings), repository indexing, and a privileged Arch
Docker mkarchiso build. The final candidate contains arche-tui-stack 2.0.0-9.

The automated QEMU/KVM test installed onto a fresh 25 GiB disk with a 1 GiB ESP,
removed the ISO, and cold-booted Zen and LTS separately. Both passed the XFS
geometry/reflink and mount checks, EFI entry and rootflag checks, ZRAM/sysctl
checks, service activation, user ownership, Neovim LSP/parser checks (including
an unseeded SVG filetype), and Sway desktop startup. No system units failed.
The final run required no manual input.

The complete run history is in tests/install-test.log. Generated artifacts are
out/archelinux-2026.11.10-x86_64.iso and out/SHA256SUMS. Updated VM screenshots
are out/e2e-live-desktop.png, out/e2e-installed-desktop.png,
out/e2e-fuzzel-neovim.png, out/e2e-storage-terminal.png, and
out/e2e-lts-desktop.png. The retained test disk is out/e2e-rc5/target.qcow2.

Warm shell startup medians in the final image were Bash 1.90 ms, Zsh 1.13 ms,
and Fish 6.20 ms on this host. These measurements are not a hardware-independent
latency guarantee. BIOS installation and physical NVIDIA/CUDA, Wi-Fi,
suspend/resume, and multi-monitor behavior remain unverified. Signed release
publication and a hosted GitHub Actions run are also still outstanding.

## Sway / Litho Dark

The selected desktop adapts [okubax/dotfiles](https://github.com/okubax/dotfiles)'s
Litho Dark palette and centered top Waybar clusters. Provenance and the upstream
license are installed in `/usr/share/doc/arche-tui-stack/`. Window borders are
disabled for both tiled and floating clients. Applications that draw their own
internal chrome remain responsible for that chrome.

Super+Return opens Foot; Super+d opens Fuzzel; Super+Shift+q closes a window;
Super+h/j/k/l moves focus; Super+r enters resize mode; Super+Shift+c reloads
configuration; Super+Shift+e exits Sway. No upstream dotfile installer or personal
cloud/service configuration is run. Media keys use WirePlumber and playerctl.

Login hooks exist for Zsh, Bash and Fish. They require a local non-root TTY1
session, no existing display, and no SSH connection. NVIDIA/nouveau detection
sets `WLR_NO_HARDWARE_CURSORS=1` and passes `--unsupported-gpu`; this is a fallback,
not a guarantee for every driver. No hook is added to the live root installer.
`useradd -m -U -k /usr/share/arche/skel` copies all templates directly into the
new user's home and assigns their ownership. Package templates never claim
Bash-owned `/etc/skel` files.

The default background is a pure-black SVG wallpaper with the text-free Arche
symbol centered at 640 units tall on a 3840×2160 canvas. Run
`python3 scripts/make-wallpaper.py` to regenerate it from `assets/arche-logo.svg`.
Sway uses `/usr/share/arche/wallpaper.svg` directly.

For automated UEFI installation acceptance on a disposable qcow2 disk, see
[tests/qemu/README.md](tests/qemu/README.md).
