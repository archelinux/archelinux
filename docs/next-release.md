# archelinux 2.0.0-rc2

The USB boots to the installer. Connect to the internet so it can fetch the software you select. Back up files on the destination disk before starting.

**What you get.** New accounts use Zsh with the Oh My Zsh `bureau` prompt, autosuggestions, syntax highlighting and searchable history. The recommended installation opens an i3-style Sway desktop with Foot, LazyVim for Neovim, tmux, bat, ripgrep, fd, fzf and zoxide. The installer shows the selected tools. You can change them or clear the list for a console system. Language servers, local model runtimes and CUDA are optional.

**What happens to the disk.** Arche uses XFS for the root filesystem. Choose your disk and enable LUKS in Disk configuration if you want encryption. Review which disks and partitions will be erased or formatted before confirming. Package rollback restores individual versions available in the local cache. Keep a separate backup for your files and system recovery.

**Your first login.** On Sway, press Super+Enter for Foot and Super+D for the launcher. Use Ctrl+H/J/K/L to move between Neovim splits and tmux panes. Edit your prompt in `~/.zshrc` and your desktop shortcuts in `~/.config/sway/config`. Packages distribute templates under `/usr/share/arche`; your account owns the copies in your home directory.

Physical GPU, external-display, Wi-Fi and suspend behavior depends on the machine. Alternate consoles are available on TTY2 through TTY6.

On first launch, Neovim downloads the LazyVim plugins. Keep the internet connection active until setup finishes. Change the default `archevim` colorscheme in `~/.config/nvim/lua/plugins/colors.lua`.

**Optional bundles.** The ISO carries the archelinux pacman repository. Select `arche-base`, `arche-tui-stack`, `arche-agentic-core`, or `arche-cuda` in **Arche software**, or install them later with pacman. CUDA, cuDNN and NVIDIA drivers download from official Arch mirrors when selected.

Twin Blades wallpaper sourced from the [dharmx/walls collection](https://github.com/dharmx/walls/blob/e8d8a42e4fbecb2cf9619995edbc7ce19610bbd8/anime/aeb9uhrbr41a1.webp).

## Verify the download

Download the ISO, checksum, both signatures and release public key into a fresh directory. If the download is split, place all numbered parts together. Verify the signing-key fingerprint using a trusted source. Set `iso` to the ISO filename from the checksum file and run:

```sh
iso=$(awk 'NR == 1 { print $2 }' ./*.iso.sha256)
if [ ! -f "$iso" ]; then cat "$iso".part[0-9][0-9] > "$iso"; fi
gpg --show-keys --fingerprint archelinux-release-public.asc
gpg --import archelinux-release-public.asc
gpg --verify "$iso.sha256.sig" "$iso.sha256"
sha256sum -c "$iso.sha256"
gpg --verify "$iso.sig" "$iso"
```

Write the verified ISO to USB. Follow the [installation guide](https://github.com/archelinux/archelinux/blob/main/docs/getting-started.md) for the walkthrough.
