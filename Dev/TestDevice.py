import time

from Dev.Device import Device

# This is a test device, it will send fake sensor data

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
        self.sensor_group_list[0].get_sensor(0).data = 33
        self.sensor_group_list[0].get_sensor(1).data = 57
        self.sensor_group_list[1].get_sensor(0).data = 33
        self.sensor_group_list[1].get_sensor(20).data = 57
        self.sensor_group_list[2].get_sensor(0).data = 19.1
        self.sensor_group_list[2].get_sensor(1).data = 1.5
        self.sensor_group_list[2].get_sensor(2).data = 97.1
        self.sensor_group_list[2].get_sensor(3).data = 30
        while True:
            self.sensor_group_list[0].get_sensor(0).data += 0.1
            self.sensor_group_list[0].get_sensor(0).data += 1
            time.sleep(1)
            print(f"sensor: {self.sensor_group_list[0].get_sensor(0).sensor_type} {self.sensor_group_list[0].get_sensor(0).data}")
            self.networkManager.sendMsg(SENSOR, self.sensor_group_list[0].pack())
            self.networkManager.sendMsg(SENSOR, self.sensor_group_list[1].pack())
            self.networkManager.sendMsg(SENSOR, self.sensor_group_list[2].pack())