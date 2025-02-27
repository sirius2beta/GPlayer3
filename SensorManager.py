import GTool

SENSOR = b'\x04'

class SensorManager(GTool):
    def __init__(self, toolBox):
        super().__init__(toolBox)
        self.device_list = [] # store all devices
        self.sensor_group_list = [] # store all sensor_groups

    def add_device(self, device): # add device to device_list
        self.device_list.append(device)
    def get_device(self, index): # get device from device_list
        return self.device_list[index]
    def get_device_list(self): # get device_list
        return self.device_list

    def add_sensor_group(self, group): # add sensor_group to sensor_group_list
        self.sensor_group_list.append(group) 
    def get_sensor_group(self, index): # get sensor_group from sensor_group_list
        return self.sensor_group_list[index] 
    def get_sensor_group_list(self): # get sensor_group_list
        return self.sensor_group_list 
    
    def send_detection_result(self, detectionMatrix):
        data = b''
        for i in range(10):

            self.sensor_group_list[5].get_sensor(i*6).data = detectionMatrix[i*6]
            self.sensor_group_list[5].get_sensor(i*6+1).data = detectionMatrix[i*6+1]
            self.sensor_group_list[5].get_sensor(i*6+2).data = detectionMatrix[i*6+2]
            self.sensor_group_list[5].get_sensor(i*6+3).data = detectionMatrix[i*6+3]
            self.sensor_group_list[5].get_sensor(i*6+4).data = detectionMatrix[i*6+4]
            self.sensor_group_list[5].get_sensor(i*6+5).data = detectionMatrix[i*6+5]

        self.toolBox().networkManager.sendMsg(SENSOR, self.sensor_group_list[5].pack())
    def io_loop(self):
        pass
