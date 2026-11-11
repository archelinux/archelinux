# Login-only; never launch a compositor from an interactive terminal tab.
[[ -o interactive ]] && source /usr/share/arche/start-sway.sh
