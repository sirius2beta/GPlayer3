sudo pip install Jetson.GPIO
sudo groupadd -f -r gpio
sudo usermod -a -G gpio sirius2beta
sudo cp lib/python3.8/Jetson/GPIO/99-gpio.rules /etc/udev/rules.d/