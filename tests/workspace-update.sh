#!/usr/bin/env bash
# Run inside the disposable image filesystem, after mkarchiso has sealed the ISO.
set -euo pipefail
account=arche-update-test
pacman -S --needed --noconfirm arche-zsh arche-workspace-defaults
useradd --create-home --skel /usr/share/arche/skel --shell /bin/zsh "$account"
trap 'userdel --remove "$account"' EXIT
home_dir=$(getent passwd "$account" | cut -d: -f6)
install -o "$account" -g "$(id -gn "$account")" -m644 /usr/share/arche/zshrc "$home_dir/.zshrc"
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
for config in waybar/style.css waybar/config.jsonc alacritty/alacritty.toml foot/foot.ini nvim/colors/archevim.lua; do
  path="$home_dir/.config/$config"
  cmp "/usr/share/arche/skel/.config/$config" "$path"
  printf '\n' >> "$path"
  files+=("$path")
done
before=$(sha256sum "${files[@]}")
pacman -S --noconfirm arche-zsh arche-workspace-defaults
sha256sum --check <<< "$before"
