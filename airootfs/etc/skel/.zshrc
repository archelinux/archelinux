# Interactive-only, pre-generated hooks: no subprocesses during shell startup.
[[ -o interactive ]] || return
command -v nvim >/dev/null && export EDITOR=nvim
command -v fd >/dev/null && export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git'
[[ ! -r /usr/share/arche/shell/zsh.sh ]] || source /usr/share/arche/shell/zsh.sh
