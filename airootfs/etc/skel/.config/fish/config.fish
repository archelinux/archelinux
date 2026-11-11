status is-interactive; or return
set -gx EDITOR nvim
set -gx FZF_DEFAULT_COMMAND 'fd --type f --hidden --exclude .git'
if test -r /usr/share/arche/shell/fish.fish
    source /usr/share/arche/shell/fish.fish
end
