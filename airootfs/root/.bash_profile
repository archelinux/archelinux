#!/usr/bin/env bash
if [[ -z ${DISPLAY:-} && $(tty) == /dev/tty1 ]]; then
  /root/arche-install
fi
