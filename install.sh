#!/bin/bash
#Program:
# This program will auto install mavproxy, openvpn, gstreamer
# History:
# 2021/12/22  Sirius  First release

PATH=/usr/local/cuda-11.4/bin:/home/sirius2beta/.vscode-server/cli/servers/Stable-4437686ffebaf200fa4a6e6e67f735f3edf24ada/server/bin/remote-cli:/home/sirius2beta/.local/bin:/usr/local/cuda-11.4/bin:/home/sirius2beta/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
export PATH

echo "start downloading pymavlink..."
sudo pip3 install pymavlink pyserial scipy supervision==0.1.0
sudo cp GPlayer3.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable GPlayer3.service
sudo systemctl start GPlayer3.service
sudo cp 79-sir.rules /etc/udev/rules.d/
sudo cp wpa_supplicant.conf /etc/wpa_supplicant

chmod +x push.sh
chmod +x update.sh 

echo "start downloading snmp..."
sudo apt-get install snmp