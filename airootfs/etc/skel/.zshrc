# Interactive-only, pre-generated hooks: no subprocesses during shell startup.
[[ -o interactive ]] || return
export EDITOR=nvim
export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git'
[[ ! -r /usr/share/arche/shell/zsh.sh ]] || source /usr/share/arche/shell/zsh.sh
