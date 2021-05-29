#!/bin/bash
set -e -o pipefail
# Add the script to system startup

tname=/tmp/syslcd.service.new
exe_name=$(dirname $(readlink -f "$0"))/syslcd.py
cat >$tname <<EOF
[Unit]
Description=System monitor on attached 5110 LCD
After=sysinit.target
DefaultDependencies=no

[Service]
ExecStart=$exe_name
WorkingDirectory=/home/pi
Restart=always
User=pi
KillSignal=SIGINT

[Install]
WantedBy=basic.target
EOF

if diff -u $tname /etc/systemd/system/syslcd.service; then
   echo Everything up to date. You can reinstall anyway if you want to.
else
   echo
   echo Changes detected
fi

if [[ "$1" != "install" ]]; then
  echo To install, re-run this with install argument
  echo sudo $0 install
  exit 1
fi

set -x
cp $tname /etc/systemd/system/syslcd.service
systemctl daemon-reload
systemctl enable syslcd
systemctl restart syslcd
sleep 5
systemctl status syslcd
: "Success!"


