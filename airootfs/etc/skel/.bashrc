# Interactive-only, pre-generated hooks: no subprocesses during shell startup.
[[ $- == *i* ]] || return
export EDITOR=nvim
export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git'
[[ ! -r /usr/share/arche/shell/bash.sh ]] || source /usr/share/arche/shell/bash.sh
