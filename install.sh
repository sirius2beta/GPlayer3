#!/bin/bash
#Program:
# This program will auto install mavproxy, openvpn, gstreamer
# History:
# 2021/12/22  Sirius  First release

PATH=/home/pi/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games:/home/pi/.local/bin
export PATH

echo "start downloading pymavlink..."
sudo pip3 install pymavlink pyserial scipy supervision==0.1.0
sudo cp GPlayer3.service /etc/systemd/system/
#sudo cp GPlayer3.conf /etc/rsyslog.d/
sudo cp GPlayer3.log /var/log/
sudo cp logrotate/GPlayer3.conf /etc/logrotate.d
sudo systemctl daemon-reload
sudo systemctl enable GPlayer3.service
sudo systemctl start GPlayer3.service
sudo cp 79-sir.rules /etc/udev/rules.d/
sudo cp wpa_supplicant.conf /etc/wpa_supplicant

chmod +x push.sh
chmod +x update.sh 

echo "start downloading snmp..."
sudo apt-get install snmp