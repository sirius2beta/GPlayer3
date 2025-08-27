sudo cp GPlayer3.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable GPlayer3.service
sudo systemctl start GPlayer3.service