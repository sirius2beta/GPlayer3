# Device class
class Device:
    # device_type is the index of the device in the XML file, EX: AT600 -> 0, xy_md02 -> 1
    def __init__(self, device_type):
        self.device_type = device_type 
        self.metadata = {}
    # getter
    def get(self): 
        pass
    # setter
    def set(self):
        pass

    def __str__(self):
        return f'DeviceType:{self.device_type}'

# Sensor class used to store the information of the sensor EX: temperature_sensor, pH_sensor
class Sensor:
    def __init__(self, device_type, sensor_type, data, data_type):
        self.device_type = device_type # EX : AT600 -> 0, xy_md02 -> 1
        self.sensor_type = sensor_type # EX : temperature -> 0, pH -> 1, humidity -> 2, depth -> 3
        self.data = data # EX : 23.5, 7.2, 60, 50
        self.data_type = data_type # EX : INT, FLOAT, STRING 
    def __str__(self):
        return f'DeviceIndex:{self.device_index}, Data:{self.data}, DataType:{self.data_type}'

# SensorGroup class is used to store multiple sensors
class SensorGroup:
    def __init__(self, sensors = None):
        # if sensors is not None, then initialize it as sensors, else initialize it as empty list
        self.sensor_group = sensors if sensors else [] # EX : [temperature_sensor, pH_sensor]

    def add_sensor(self, sensor): # add sensor to sensor_group
        self.sensor_group.append(sensor) 

    def get_sensor(self, index): # get sensor from sensor_group
        return self.sensor_group[index] 
    
    def get_sensor_group(self): # get sensor_group
        return self.sensor_group
    
    def __str__(self):
        return f'SensorGroup:{self.sensor_group}'

class SensorManager:
    def __init__(self):
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

    def io_loop(self):
        pass

if __name__ == '__main__':
    # if xml is like below
    """
    <enum name="Device">
        <entry index="0"></entry>
        <entry index="1"></entry>
    </enum>
    <enum name="Sensors">
        <entry index="0" name="TEMPERATURE" type="float"></entry>
        <entry index="1" name="pH" type="float"></entry>
        <entry index="2" name="HUMIDITY" type="float"></entry>
        <entry index="3" name="DEPTH" type="float"></entry>
    </enum>
    
    """
    # add device
    aqua_device = Device(device_type=0)
    xy_md02_device = Device(device_type=1)

    # add sensor
    temperature_sensor = Sensor(device_type=0, sensor_type=0, data=23.5, data_type='float')
    pH_sensor = Sensor(device_type=0, sensor_type=1, data=7.2, data_type='float')
    humidity_sensor = Sensor(device_type=1, sensor_type=2, data=60, data_type='float')
    depth_sensor = Sensor(device_type=1, sensor_type=3, data=50, data_type='float')

    # create sensor_group object sensor_group1
    sensor_group1 = SensorGroup()
    sensor_group2 = SensorGroup()
    # add sensor to sensor_group1
    sensor_group1.add_sensor(temperature_sensor)
    sensor_group1.add_sensor(pH_sensor)
    sensor_group1 = sensor_group1.get_sensor_group()
    print(sensor_group1)
    # add sensor to sensor_group2
    sensor_group2.add_sensor(humidity_sensor)
    sensor_group2.add_sensor(depth_sensor)
    sensor_group2 = sensor_group2.get_sensor_group()
    print(sensor_group2)
    
    # create sensor_manager object sensor_manager
    sensor_manager = SensorManager()
    # add device to sensor_manager
    sensor_manager.add_device(aqua_device)
    sensor_manager.add_device(xy_md02_device)
    device_list = sensor_manager.get_device_list()
    print(device_list)

    # add sensor_group to sensor_manager
    sensor_manager.add_sensor_group(sensor_group1)
    sensor_manager.add_sensor_group(sensor_group2)
    sensor_group_list = sensor_manager.get_sensor_group_list()
    print(sensor_group_list)