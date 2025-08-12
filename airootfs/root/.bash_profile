#!/usr/bin/env bash
if [[ -z "$DISPLAY" && $(tty) == /dev/tty1 ]]; then
  arche-install || /usr/bin/arche-install || /root/arche-install
fi
