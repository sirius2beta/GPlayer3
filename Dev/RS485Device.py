import time
import serial

from Dev.Device import Device
from config import Config as CF

SENSOR = b'\x04'

class RS485Device(Device):
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)
        self.command_set = [
            ['01', '04', '00', '01', '00', '02', '20', '0B'], # Temperature and Humidity
            ["DD", "A5", "03", "00", "FF", "FD", "77"] # battery0
        ]
        self.cabin_temp = 0.0
        self.cabin_hum = 0.0

        self.total_voltage = 0.0
        self.current = 0.0
        self.capacity = 0.0
        self.battery_temp = 0.0
    
    def start_loop(self):
        super().start_loop()

    def send(self, ser, command, length):
        command = bytes([int(x, 16) for x in command]) # modbus RTU
        ser.write(command) # if use modbus ASCII, add .encode('utf-8')
        response = ser.read(length)
        response = [format(x, '02x') for x in response]
        # print(f"response: {response}")
        return response

    def Reader(self):
        try:
            ser = serial.Serial(port = self.dev_path, baudrate = 9600, timeout = 5) 
            for i in range(len(self.command_set)):
                # print(i)
                if(i == 0):
                    data = self.send(ser = ser, command = self.command_set[i], length = 9) # send command to device
                    if(len(data) == 9): # if data is not empty (check if data is correct)
                        value1 = data[3] + data[4] # get the value
                        self.cabin_temp = int(value1, 16) / 10 # convert hex to float
                        value2 = data[5] + data[6] # get the value
                        self.cabin_hum = int(value2, 16) / 10 # convert hex to float

                elif(i == 1):
                    data = self.send(ser = ser, command = self.command_set[i], length = 34) # send command to device
                    if(len(data) == 34): # if data is not empty (check if data is correct
                        value1 = data[4] + data[5] # total voltage
                        self.total_voltage = int(value1, 16) / 100 # convert hex to float (V)

                        value2 = data[6] + data[7] # current
                        self.current = int(value2, 16) / 100 # convert hex to float (A)

                        value3 = data[23] # capacity
                        self.capacity = int(value3, 16) # convert hex to float (%)

                        value4 = data[27] + data[28] # battery temp 
                        self.battery_temp = (int(value4, 16) - 2731) / 10 # convert hex to float (C)
                time.sleep(1)

        except serial.serialutil.SerialException: # if serial error
            print("Serial Error...")
            print("Trying to reconnect...")

        except Exception as e: # if other error
            print(e) 

    def _io_loop(self):
        while(True):
            self.Reader()
            
            self.sensor_group_list[0].get_sensor(0).data = self.cabin_temp
            self.sensor_group_list[0].get_sensor(1).data = self.cabin_hum

            self.sensor_group_list[2].get_sensor(0).data = self.total_voltage
            self.sensor_group_list[2].get_sensor(1).data = self.current
            self.sensor_group_list[2].get_sensor(2).data = self.capacity
            self.sensor_group_list[2].get_sensor(3).data = self.battery_temp
            
            self.networkManager.sendMsg(SENSOR, self.sensor_group_list[0].pack())
            self.networkManager.sendMsg(SENSOR, self.sensor_group_list[2].pack())
            time.sleep(1)
