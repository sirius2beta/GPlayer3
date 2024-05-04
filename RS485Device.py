import time
import serial
import struct

from Device import Device
from config import Config as CF

SENSOR = b'\x04'

class RS485Device(Device):
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)
        self.command_set = [
            ['01', '04', '00', '01', '00', '02', '20', '0B'], # Temperature and Humidity
            ["DD", "A5", "03", "00", "FF", "FD", "77"], 
            ["DD", "A5", "04", "00", "FF", "FC", "77"]
        ]
        self.data_list = [0.0] * 22
    
    def start_loop(self):
        super().start_loop()

    def send(self, ser, command):
        command = bytes([int(x, 16) for x in command]) # modbus RTU
        ser.write(command) # if use modbus ASCII, add .encode('utf-8')
        response = ser.readline()
        response = [format(x, '02x') for x in response]
        # print(f"response: {response}")
        return response

    def Reader(self):
        try:
            ser = serial.Serial(port = self.dev_path, baudrate = 9600, bytesize = 8, parity = 'N', stopbits = 1, timeout = 2) 
            for i in range(len(self.command_set)):
                if(i < 1):
                    data = self.send(ser = ser, command = self.command_set[i]) # send command to device
                    value1 = data[3] + data[4] # get the value
                    value1 = int(value1, 16) / 10 # convert hex to float
                    value2 = data[5] + data[6] # get the value
                    value2 = int(value2, 16) / 10 # convert hex to float
                    self.sensor_group_list[0].get_sensor(0).data = value1 # store the value
                    self.sensor_group_list[0].get_sensor(1).data = value2 # store the value
                elif(i < 3):
                    self.sensor_group_list[2].get_sensor(0).data = 1.1
                    self.sensor_group_list[2].get_sensor(1).data = 1.1
                    self.sensor_group_list[2].get_sensor(2).data = 1.1
                    self.sensor_group_list[2].get_sensor(3).data = 1.1

        except serial.serialutil.SerialException: # if serial error
            print("Serial Error...")
            print("Trying to reconnect...")

        except Exception as e: # if other error
            print(e) 

    def _io_loop(self):
        while(True):
            self.Reader()
            
            print(f"self.sensor_group_list[0].get_sensor(0).data:{self.sensor_group_list[0].get_sensor(0).data}")  
            print(f"self.sensor_group_list[0].get_sensor(1).data:{self.sensor_group_list[0].get_sensor(1).data}") 

            print(f"self.sensor_group_list[2].get_sensor(0).data:{self.sensor_group_list[2].get_sensor(0).data}")  
            print(f"self.sensor_group_list[2].get_sensor(1).data:{self.sensor_group_list[2].get_sensor(1).data}")  
            print(f"self.sensor_group_list[2].get_sensor(2).data:{self.sensor_group_list[2].get_sensor(2).data}")  
            print(f"self.sensor_group_list[2].get_sensor(3).data:{self.sensor_group_list[2].get_sensor(3).data}")  

            print(f"pack:{SENSOR, self.sensor_group_list[0].pack()}")
            print(f"pack:{SENSOR, self.sensor_group_list[2].pack()}")
            #self.networkManager.sendMsg(SENSOR, self.sensor_group_list[0].pack())
            time.sleep(1)

if __name__ == "__main__":
    cf = CF(toolBox = None)
    dev = RS485Device(device_type = 4, dev_path = "COM11", sensor_group_list = cf.sensor_group_list) 
    dev.start_loop()
    time.sleep(20)