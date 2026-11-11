# Archelinux

**An Arch-based Linux distribution with a preconfigured Sway environment.**

Arche brings together keyboard-driven window management, a minimal interface,
and a terminal environment ready for development. It is built for people who
want a working tiling setup from the first login and ordinary configuration
files they can change themselves.

[Download](https://github.com/archelinux/archelinux/releases/latest)
 · [Getting started](docs/getting-started.md)
 · [Build documentation](docs/architecture.md)
 · [Issues](https://github.com/archelinux/archelinux/issues)

![Archelinux running Sway with a compact top bar and the Arche logo centered on black](https://github.com/archelinux/archelinux/releases/download/v2.0.0-rc1/e2e-live-desktop.png)

## The environment

- **Work from the keyboard.** Sway tiles your windows and organizes them into
  workspaces. A shared set of shortcuts connects window, terminal pane, and
  editor navigation.
- **A minimal interface.** Borderless windows, a compact Waybar, and Fuzzel for
  launching applications. The default appearance adapts Litho Dark, with the
  Arche logo on a black background.
- **Ready to work.** Shell navigation, search, project environment hooks, and
  clipboard integration are configured together. Neovim and Tmux are included,
  along with language servers and syntax parsers.
- **Yours to configure.** User settings are copied into your home at installation.
  Edit them directly, replace the defaults, and install what you need with pacman.

Sway is the tiling Wayland compositor that provides window management. Archelinux
is the distribution that packages and configures the system around it.

## Underneath

Arche uses Arch's rolling package base, with Zen and LTS kernels, an XFS root
filesystem with reflink support, and compressed ZRAM swap. An LTS boot entry,
console sessions on TTY2–6, and cached package versions provide recovery options.
You maintain the system as an Arch user; package rollback does not replace backups.

See the [architecture guide](docs/architecture.md) for package lists, system
configuration, optional local inference services, and build instructions.

## Try Archelinux

Download the signed image from [Releases](https://github.com/archelinux/archelinux/releases/latest)
and follow the [installation guide](docs/getting-started.md). The ISO is published
in parts; reconstruct and verify it before writing installation media.

Installation requires a network connection and formats the partitions you select.
The current installer uses XFS and does not support disk encryption.

## Project status

The release passed automated QEMU installation and separate UEFI boots with both
Zen and LTS. Physical NVIDIA/CUDA, Wi-Fi, suspend/resume, multiple monitors, and
BIOS installation still need hardware validation.

[Test details](tests/qemu/README.md) · [Test log](tests/install-test.log)

## Contributing

Hardware reports, installation fixes, documentation, and improvements to the
configured environment are welcome. Include your hardware, kernel, and steps to
reproduce when [reporting an issue](https://github.com/archelinux/archelinux/issues).
The [build guide](docs/architecture.md) explains the archiso profile and packages.

Archelinux is licensed under [GPL-3.0](LICENSE). Included software retains its
upstream licenses. The Sway environment adapts
[okubax/dotfiles](https://github.com/okubax/dotfiles)' Litho Dark design; its
attribution and license ship with the terminal package.
