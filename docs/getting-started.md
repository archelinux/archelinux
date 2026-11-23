# Getting started

[Back to Archelinux](../README.md)

## Before you download

The recommended system is a keyboard-driven Sway desktop with Zsh, Oh My Zsh, Neovim and tmux. The USB boots to a console and needs internet access to install. Arche uses XFS for root. You can enable LUKS and choose your software. If you depend on booting filesystem snapshots, factor that into your choice: Arche provides individual cached-package rollback.

## Install

**Images built from this checkout** start the Archelinux adaptation of archinstall 4.5 on TTY1. Published release v2.0.0-rc1 uses the earlier XFS-only installer.

1. Download and verify the signed ISO as instructed on its release page, then write it to installation media.
2. Boot the console and connect to the network. Use NetworkManager or `nmcli` if needed.
3. Open **Arche software** to keep the recommended SwayFX workspace or toggle individual tools with Space. SwayFX supplies nine-pixel window corners and terminal background blur. For stock Sway, clear **arche-swayfx** and select **sway**. Both compositors use a slim mauve focus outline, small gaps and a floating Waybar panel. Optional tools include **github-cli** (`gh`), **yazi** (file manager) and **btop** (system monitor). For unread GitHub PRs and issues on the Sway bar, select **arche-waybar-github**, then run `gh auth login` after login. If your token needs notification access, run `gh auth refresh -h github.com -s notifications`. Hover for thread titles or click to open your inbox. Choose **spotify** for the desktop app from Flathub or **spotify-player** for the terminal client (Spotify Premium required). You can select both. Clear the list for a console system. Selecting Sway includes its terminal, launcher, bar, lock, media controls and region screenshots (`grim -g "$(slurp)" - | wl-copy --type image/png`). Select other packages in **Additional packages**.
4. New accounts start in Zsh with Oh My Zsh, the `bureau` theme and the shell plugins described below. Edit `~/.zshrc` to personalize them.
5. In **Disk configuration**, select the target and layout. Archelinux uses XFS for the root filesystem. UEFI uses a separate FAT32 EFI partition. Configure LUKS encryption here if wanted and retain your passphrase. The installer does not choose a target disk for you.
6. Review kernels, bootloader, networking, locale, time zone and authentication. Check the final configuration and selected disk before confirming. Formatting erases the selected partitions.

For **v2.0.0-rc1**, run `/root/arche-install`, choose a root partition of at least 16 GiB and, on UEFI, a 1 GiB EFI partition. Follow the hostname, username, locale and password prompts. That release installs the complete workspace.

Release signing-key fingerprint:

    E446 C26A 0B7B A1A6 6A3D CC9F 7EC5 6400 3573 C80B

Verification commands and signed package-repository setup are included in the
release notes. The [public key](../keys/archelinux-release.asc) is also in this repository.

On first launch, Neovim downloads the LazyVim plugins. Keep the internet connection active until setup finishes. Change the default `archevim` colorscheme in `~/.config/nvim/lua/plugins/colors.lua`.

## The Zsh workspace

| What you want to do | How to use it |
| --- | --- |
| Accept a suggestion from command history | Press Right at the end of the command. Syntax highlighting colors the command as you type. |
| Find an earlier command | Type a fragment and press Up or Down. With fzf installed, Ctrl+R opens fuzzy history search. |
| Complete a package, path or Git branch | Press Tab. With fzf installed, fzf-tab lets you filter the matches. Arch’s zsh-completions package supplies additional completions. |
| Work with Git or pacman | `gst` shows Git status. Run `alias pacin` to see the pacman install shortcut before using it. |
| Edit a command to run with sudo | Press Esc twice. At an empty prompt this recalls the previous command and adds `sudo`. Review it before pressing Enter. |
| Unpack an archive or read a manual | Use `extract FILE`, or `man COMMAND` for a colored manual page in a supported pager. |

For paired brackets and quotes, add `autopair` to `plugins=(...)` in `~/.zshrc`. Add `you-should-use` for reminders about existing aliases. Oh My Zsh also ships integrations such as `docker`, `kubectl` and `vi-mode`. Run `omz plugin list` for the installed catalog. The installed zoxide and direnv integrations also load automatically when you select those tools. Open a new terminal after editing your plugin list.

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

The live USB and guided installation default to the hostname `archelinux`. Choose **Hostname** in the installer to set a different name.

Your prompt lives in `~/.zshrc`. Sway bindings live in `~/.config/sway/config`. Edit those files in your home directory. Pacman updates the packaged templates under `/usr/share/arche`, so your personal copies keep your changes.

## Check your hardware after the first login

- On a laptop, suspend and resume once. Check that the lock screen appears and that Wi-Fi, audio and brightness controls still work after unlocking.
- If you use a dock, plug it in, unplug it and reconnect it. Run `swaymsg -t get_outputs` to see which displays Sway detects, then move a window between them and check the scale.
- Start a screen share in the browser or meeting app you actually use. Choose an output and confirm a second participant can see it.
- On a hybrid-GPU laptop, repeat the display and screen-sharing checks with the external monitor attached. If Sway fails to start, switch to TTY2 with Ctrl+Alt+F2 and log in to inspect the journal with `journalctl -b`.
