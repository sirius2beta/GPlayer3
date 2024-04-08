class Device:
    def __init__(self, device_type):
        self.device_type = device_type
        self.metadata = {}

    def get(self):
        return self.device_type

    def set(self):
        pass

    def __str__(self):
        return f'DeviceType:{self.device_type}'

class Sensor:
    def __init__(self, device_index, data, data_type):
        self.device_index = device_index  # 從XML定義中取得
        self.data = data  # data 是感測器的數值嗎?
        self.data_type = data_type  # data_type 是感測器的類型嗎?
    def __str__(self):
        return f'DeviceIndex:{self.device_index}, Data:{self.data}, DataType:{self.data_type}'

class SensorGroup:
    def __init__(self, sensors = None):
        self.sensor_group = sensors if sensors else []

    def add_sensor(self, sensor):
        self.sensor_group.append(sensor)
    def get_sensor(self, index):
        return self.sensor_group[index]
    def get_sensor_group(self):
        return self.sensor_group
    def __str__(self):
        return f'SensorGroup:{self.sensor_group}'

class SensorManager:
    def __init__(self):
        self.device_list = []
        self.sensor_group_list = []

    def add_device(self, device):
        self.device_list.append(device)
    def get_device(self, index):
        return self.device_list[index]
    def get_device_list(self):
        return self.device_list

    def add_sensor_group(self, group):
        self.sensor_group_list.append(group)
    def get_sensor_group(self, index):
        return self.sensor_group_list[index]
    def get_sensor_group_list(self):
        return self.sensor_group_list

    def io_loop(self):
        pass



if __name__ == '__main__':
    aqua_device = Device(device_type='AT600')
    xy_md02_device = Device(device_type='xy_md02')

    temperature_sensor = Sensor(device_index=0, data=23.5, data_type='temperature')
    pH_sensor = Sensor(device_index=1, data=7.2, data_type='pH')

    humidity_sensor = Sensor(device_index=2, data=60, data_type='humidity')
    depth_sensor = Sensor(device_index=3, data=50, data_type='depth')
    
    sensor_manager = SensorManager()

    sensor_manager.add_device(aqua_device)
    sensor_manager.add_device(xy_md02_device)
    device_list = sensor_manager.get_device_list()

    sensor_manager.add_sensor(temperature_sensor)
    sensor_manager.add_sensor(pH_sensor)
    sensor_group1 = sensor_manager.get_sensor_group()