# Getting started

[Back to Archelinux](../README.md)

## Install

Installation currently requires a network connection and manual disk selection.
The installer formats the root and EFI partitions you select, so back up their
contents before starting.

1. Download the ISO parts, ISO signature, checksums, and public key from the
   [release page](https://github.com/archelinux/archelinux/releases/latest).
   Follow its commands to reconstruct and verify the complete ISO. Write the
   reconstructed ISO to your installation media.
2. Boot the live image and connect to the network using NetworkManager or nmcli.
3. Follow the installer offered on TTY1, or run /root/arche-install.
4. For UEFI, create a root partition of at least 16 GiB and a **1 GiB EFI system
   partition**. The ESP is mounted at /boot. Select the partitions, hostname,
   username, locale, and passwords when prompted.
5. After installation, unmount /mnt recursively and reboot from the installed disk.

The default locale is en_US.UTF-8 and the timezone is UTC. The installer uses
XFS and currently does not provide disk encryption.

Release signing-key fingerprint:

    E446 C26A 0B7B A1A6 6A3D CC9F 7EC5 6400 3573 C80B

Verification commands and signed package-repository setup are included in the
release notes. The [public key](../keys/archelinux-release.asc) is also in this repository.

## Recovery and maintenance

Choose the LTS entry from the boot menu if you need an alternative to Zen.
TTY2–6 provide console access independently of the desktop.

For a package with an older version still in the local cache:

    sudo arche-rollback PACKAGE

Package rollback does not replace backups. Changes involving related libraries
may require coordinated downgrades.

## Your first few shortcuts

| Action | Shortcut |
| --- | --- |
| Open a terminal | Super + Return |
| Open the launcher | Super + D |
| Move focus | Super + H / J / K / L |
| Close the focused window | Super + Shift + Q |
| Enter resize mode | Super + R |
| Reload Sway configuration | Super + Shift + C |
| Move between editor splits and Tmux panes | Ctrl + H / J / K / L |

The defaults are templates, so you can edit them as your workflow develops.
