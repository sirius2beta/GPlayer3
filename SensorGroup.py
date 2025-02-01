import struct


# Sensor class used to store the information of the sensor EX: temperature_sensor, pH_sensor
class Sensor:
    def __init__(self, device_type = -1, sensor_type = -1, name = "", data = 0, data_type = 0):
        self.device_type = device_type # EX : AT600 -> 0, xy_md02 -> 1
        self.sensor_type = sensor_type # EX : temperature -> 0, pH -> 1, humidity -> 2, depth -> 3
        self.data = data # EX : 23.5, 7.2, 60, 50
        self.data_type = data_type # EX : INT, FLOAT, STRING 
    def pack(self):
        data = self.sensor_type.to_bytes(1, "big")
        if self.data_type == 'uint_8':
            data += struct.pack("<B", self.data)
        elif self.data_type == 'int_8':
            data += struct.pack("<b", self.data)
        elif self.data_type == 'uint_16':
            data += struct.pack("<H", self.data)
        elif self.data_type == 'int_16':
            data += struct.pack("<j", self.data)
        elif self.data_type == 'uint_32':
            data += struct.pack("<I", self.data)
        elif self.data_type == 'int_32':
            data += struct.pack("<i", self.data)
        elif self.data_type == 'double':
            data += struct.pack("<d", self.data)
        elif self.data_type == 'float':
            data += struct.pack("<f", self.data)
        else:
            data += struct.pack("<B", self.data)
        return data
    def __str__(self):
        return f'DeviceIndex:{self.device_index}, Data:{self.data}, DataType:{self.data_type}'

# SensorGroup class is used to store multiple sensors
class SensorGroup:
    def __init__(self, index = -1, name = "", sensors = None):
        # if sensors is not None, then initialize it as sensors, else initialize it as empty list
        self._sensors = sensors if sensors else [] # EX : [temperature_sensor, pH_sensor]
        self.index = index

    def add_sensor(self, sensor): # add sensor to _sensors
        self._sensors.append(sensor) 

    def get_sensor(self, index): # get sensor from _sensors
        return self._sensors[index] 
          

    def get_all(self): # get _sensors
        
        return self._sensors
    
    def pack(self):
        data = b''
        # Data: sensor_group_index + sensor_type + sensor_data
        data += self.index.to_bytes(1, "little") # sensorgroup index
        for sensor in self._sensors:
            data += sensor.pack()
        return data
    
    def __str__(self):
        return f'SensorGroup:{self._sensors}'