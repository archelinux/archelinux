#!/usr/bin/env bash
# Run inside the disposable image filesystem, after mkarchiso has sealed the ISO.
set -euo pipefail
account=arche-update-test
pacman -S --needed --noconfirm arche-zsh arche-workspace-defaults
# The installed desktop launcher must open a package-owned, local guide.
launcher=/usr/share/applications/arche-first-session.desktop
guide=/usr/share/doc/arche-workspace-defaults/first-session.md
grep -Fxq 'Terminal=true' "$launcher"
grep -Fxq "Exec=less $guide" "$launcher"
command -v less >/dev/null
arche-mtp --help | grep -Fq "arche-mtp put LOCAL_FILE"
if arche-mtp get 4294967295 /tmp/invalid-mtp-target; then
  exit 1
else
  test "$?" -eq 2
fi
test "$(GSETTINGS_BACKEND=memory gsettings get org.gnome.desktop.interface color-scheme)" = "'prefer-dark'"
runuser -u nobody -- less "$guide" | cmp - "$guide"
source /root/arche-install
CHROOT=/
prepare_user_skeleton
useradd --create-home --skel /etc/skel --shell /bin/zsh "$account"
trap 'userdel --remove "$account"' EXIT
home_dir=$(getent passwd "$account" | cut -d: -f6)
cmp /usr/share/arche/zshrc "$home_dir/.zshrc"
runuser -u "$account" -- env HOME="$home_dir" TERM=xterm zsh -lic '
  [[ $ZSH_THEME == bureau ]] && (( $+functions[bureau_precmd] )) || exit 1
  for fn in omz _zsh_autosuggest_start _zsh_highlight history-substring-search-up; do
    (( $+functions[$fn] )) || exit 1
  done
  if (( $+commands[fzf] )); then
    [[ $(bindkey "^I") == *fzf-tab-complete && $(bindkey "^R") == *fzf-history-widget ]] || exit 1
  fi
  [[ $(bindkey -M emacs "^[^[") == *sudo-command-line ]] || exit 1
  alias gst pacin
'
printf '\nZSH_THEME=my-personal-theme\n' >> "$home_dir/.zshrc"
printf '\nbindsym Mod4+F10 exec foot\n' >> "$home_dir/.config/sway/config"
files=("$home_dir/.zshrc" "$home_dir/.config/sway/config")
for config in waybar/style.css waybar/config.jsonc foot/foot.ini nvim/colors/archevim.lua yazi/keymap.toml yazi/theme.toml; do
  path="$home_dir/.config/$config"
  cmp "/usr/share/arche/skel/.config/$config" "$path"
  printf '\n' >> "$path"
  files+=("$path")
done
test ! -e "$home_dir/.config/fish"
test ! -e /usr/share/arche/shell/fish.fish
test ! -e "$home_dir/.config/alacritty/alacritty.toml"
for plugin_file in main.lua cross.lua sudo.lua; do
  cmp "/usr/share/arche/skel/.config/yazi/plugins/mount.yazi/$plugin_file" \
    "$home_dir/.config/yazi/plugins/mount.yazi/$plugin_file"
done
# Existing user-owned terminal configs survive a workspace package upgrade.
runuser -u "$account" -- mkdir -p "$home_dir/.config/alacritty"
legacy_config="$home_dir/.config/alacritty/alacritty.toml"
printf '[window]\npadding = { x = 20, y = 20 }\n' | runuser -u "$account" -- tee "$legacy_config" >/dev/null
before=$(sha256sum "${files[@]}" "$legacy_config")
pacman -S --noconfirm arche-zsh arche-workspace-defaults
sha256sum --check <<< "$before"
