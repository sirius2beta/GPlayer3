import serial
import time
import struct
import threading
from enum import Enum

# creat XML reader
class SensorType(Enum):
    TEMPERATURE = 0
    HUMIDITY = 1

class SensorReader:
    # consructor
    def __init__(self, toolBox):
        self.temperature = 0.0
        self.humidity = 0.0
        self.comport = "/dev/ttyAMA0" # define comport

        send_thread = threading.Thread(target=self.send)
        send_thread.daemon = True # open deamon thread
        send_thread.start()

    def read_value(self, sensor_type):
        if sensor_type == SensorType.TEMPERATURE:
            value = self.temperature
        elif sensor_type == SensorType.HUMIDITY:
            value = self.humidity
        else:
            raise ValueError("Unsupported sensor type")
        return self.packed_data(sensor_type.value, value)

    def send(self): # Thread
        ser = ""
        while(True):   
            try:
                if(ser == ""): 
                    ser = serial.Serial(self.comport, baudrate=9600, timeout=2)
                origin_send = ["01", "04", "00", "01", "00", "02", "20", "0B"]
                bytes_send = bytes([int(x, 16) for x in origin_send]) 
                ser.write(bytes_send)
                time.sleep(1)
                data = ser.read(9) 
                data = [format(x, '02x') for x in data]
                value1 = data[3] + data[4]
                value2 = data[5] + data[6]
                self.temperature = int(value1, 16) / 10
                self.humidity = int(value2, 16) / 10
            except:
                ser = ""
                print("COM PORT ERROR Trying to reconnect.") 
                time.sleep(1)
                continue
            
    def packed_data(self, sensor_type, value):
        data = struct.pack(">If", sensor_type, value)
        max_size = 256
        if len(data) > max_size:
            pass 
        return data