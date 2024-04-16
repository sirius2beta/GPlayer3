import threading
import time

class Device():
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        self.networkManager = networkManager
        self.dev_path = dev_path
        self.isOpened = False
        self.device_type = device_type
        self.isOpened = False
        self.sensor_group_list = sensor_group_list

    def start_loop(self):
        io_thread = threading.Thread(target = self._io_loop)
        io_thread.daemon = True
        io_thread.start()
        print("device loop started")

    # getter
    def get(self): 
        pass
    # setter
    def set(self):
        pass
    def _io_loop(self):
        time.sleep(1)

    def __str__(self):
        return f'DeviceType:{self.device_type}'
    
        
    