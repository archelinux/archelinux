# Sourced by login shells only. Keep recovery VTs, SSH and root on the console.
if [ -z "${WAYLAND_DISPLAY:-}" ] && [ -z "${DISPLAY:-}" ] &&
   [ "${XDG_VTNR:-}" = 1 ] && [ -z "${SSH_CONNECTION:-}" ] &&
   [ "$(id -u)" != 0 ] && [ "$(tty 2>/dev/null)" = /dev/tty1 ] &&
   command -v sway >/dev/null 2>&1; then
    export XDG_CURRENT_DESKTOP=sway
    export XDG_SESSION_DESKTOP=sway
    export XDG_SESSION_TYPE=wayland
    if grep -iqE '(nvidia|nouveau)' /proc/modules 2>/dev/null; then
        export WLR_NO_HARDWARE_CURSORS=1
        exec sway --unsupported-gpu
    else
        exec sway
    fi
fi
