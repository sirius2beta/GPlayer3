import time
from Device import Device

SENSOR = b'\x04'

class TestDevice(Device):
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)
    
    def start_loop(self):
        super().start_loop()

    # getter
    def get(self): 
        pass
    
    # setter
    def set(self):
        pass

    def _io_loop(self):
        self.sensor_group_list[0].get_sensor(0).data = 1.1
        while True:
            self.sensor_group_list[0].get_sensor(0).data += 1.1
            time.sleep(1)
            print(f"sensor: {self.sensor_group_list[0].get_sensor(0).sensor_type} {self.sensor_group_list[0].get_sensor(0).data}")
            self.networkManager.sendMsg(SENSOR, self.sensor_group_list[0].pack())