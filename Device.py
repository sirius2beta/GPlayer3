import threading
import time

class Device():
    def __init__(self, device_type, dev_path="", sensor_group_list = []):
        self.dev_path = dev_path
        self.isOpened = False
        self.device_type = device_type
        self.isOpened = False
        self.sensor_group_list = sensor_group_list
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
        self.sensor_group_list[0].get_sensor(0).data = 1.1
        time.sleep(1)
        print(f"sensor: {self.sensor_group_list[0].get_sensor(0).sensor_type} {self.sensor_group_list[0].get_sensor(0).data}")
    def __str__(self):
        return f'DeviceType:{self.device_type}'
    
        
    