if status is-login; and status is-interactive
    if not set -q WAYLAND_DISPLAY; and not set -q DISPLAY; and not set -q SSH_CONNECTION
        if test "$XDG_VTNR" = 1; and test (id -u) != 0; and test (tty) = /dev/tty1; and command -q sway
            exec sh /usr/share/arche/start-sway.sh
        end
    end
end
