status is-interactive; or return
command -q nvim; and set -gx EDITOR nvim
command -q fd; and set -gx FZF_DEFAULT_COMMAND 'fd --type f --hidden --exclude .git'
if test -r /usr/share/arche/shell/fish.fish
    source /usr/share/arche/shell/fish.fish
end
