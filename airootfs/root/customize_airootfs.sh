#!/bin/bash

systemctl enable systemd-networkd
systemctl enable iwd
systemctl enable iptables

systemctl start systemd-networkd
systemctl start iwd
systemctl start iptables

[ -f /etc/systemd/network/20-ethernet.network ] || {
  echo "Error: Missing 20-ethernet.network"
  exit 1
}
[ -f /etc/systemd/network/20-wlan.network ] || {
  echo "Error: Missing 20-wlan.network"
  exit 1
}
[ -f /etc/systemd/network/20-wwan.network ] || {
  echo "Error: Missing 20-wwan.network"
  exit 1
}
[ -f /etc/iwd/main.conf ] || {
  echo "Error: Missing iwd main.conf"
  exit 1
}

install -Dm644 /etc/systemd/network/20-ethernet.network /mnt/etc/systemd/network/20-ethernet.network
install -Dm644 /etc/systemd/network/20-wlan.network /mnt/etc/systemd/network/20-wlan.network
install -Dm644 /etc/systemd/network/20-wwan.network /mnt/etc/systemd/network/20-wwan.network
install -Dm644 /etc/iwd/main.conf /mnt/etc/iwd/main.conf
chmod 600 /mnt/etc/iwd/main.conf