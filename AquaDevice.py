import time
import serial
import struct
from Device import Device
from config import Config as CF

SENSOR = b'\x04'

class AquaDevice(Device):
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)
        self.command_set = [
            ['01', '0D', 'C1', 'E5'],
            ['01', '03', '15', '4A', '00', '07', '21', 'D2'],
            ['01', '03', '15', '51', '00', '07', '51', 'D5'],
            ['01', '03', '15', '58', '00', '07', '81', 'D7'],
            ['01', '03', '15', '5F', '00', '07', '30', '16'],
            ['01', '03', '15', '66', '00', '07', 'E0', '1B'],
            ['01', '03', '15', '82', '00', '07', 'A0', '2C'],
            ['01', '03', '15', '89', '00', '07', 'D1', 'EE'],
            ['01', '03', '15', '90', '00', '07', '00', '29'],
            ['01', '03', '15', '97', '00', '07', 'B1', 'E8'],
            ['01', '03', '15', '9E', '00', '07', '61', 'EA'],
            ['01', '03', '15', 'A5', '00', '07', '10', '27'],
            ['01', '03', '15', 'B3', '00', '07', 'F1', 'E3'],
            ['01', '03', '15', 'BA', '00', '07', '21', 'E1'],
            ['01', '03', '15', 'C1', '00', '07', '51', 'F8'],
            ['01', '03', '15', 'C8', '00', '07', '81', 'FA'],
            ['01', '03', '15', 'CF', '00', '07', '30', '3B'],
            ['01', '03', '15', 'D6', '00', '07', 'E1', 'FC'],
            ['01', '03', '15', 'F2', '00', '07', 'A1', 'F7'],
            ['01', '03', '16', '15', '00', '07', '11', '84'],
            ['01', '03', '16', '23', '00', '07', 'F1', '8A'],
            ['01', '03', '16', '2A', '00', '07', '21', '88'],
        ]
        self.parameter_names = [  
            "wake_up",
            "temperature",
            "pressure",
            "depth",
            "level_depth_to_water",
            "level_surface_elevation",
            "actual_conductivity",
            "specific_conductivity",
            "resistivity",
            "salinity",
            "total_dissolved_solids",
            "density_of_water",
            "barometric_pressure",
            "pH",
            "pH_mv",
            "orp",
            "dissolved_oxygen_concentration",
            "dissolved_oxygen_percent_saturation",
            "turbidity",
            "oxygen_partial_pressure",
            "external_voltage",
            "battery_capacity_remaining"
        ]
        self.data_list = [0.0] * 22

    def start_loop(self):
        super().start_loop()

    def send(self, ser, command):
        command = bytes([int(x, 16) for x in command]) # modbus RTU
        ser.write(command) # if use modbus ASCII, add .encode('utf-8')
        response = ser.read(19)
        response = [format(x, '02x') for x in response]
        # print(f"response: {response}")
        return response

    def Reader(self):
        try:
            ser = serial.Serial(port = self.dev_path, baudrate = 19200, bytesize = 8, parity = 'E', stopbits = 1, timeout = 3) 
            for i in range(len(self.parameter_names)):
                data = self.send(ser = ser, command = self.command_set[i]) # send command to device
                if(i != 0 and i != 13 and i != 14 and i != 15 and i != 18): # skip the first data
                    # print(self.parameter_names[i], end = ":") # print the parameter name
                    value = data[3] + data[4] + data[5] + data[6] # get the value
                    value = struct.unpack('>f', bytes.fromhex(value))[0] # convert hex to float
                    self.data_list[i] = value # store the value

        except serial.serialutil.SerialException: # if serial error
            print("Serial Error...")
            print("Trying to reconnect...")

        except Exception as e: # if other error
            print(e) 
            
    def _io_loop(self):
        while(True):
            self.Reader() # read the data
            for i in range((len(self.data_list)-1)): # loop through the data list
                #print("i:", i, "data:", self.data_list[i])
                self.sensor_group_list[self.device_type].get_sensor(i).data = self.data_list[i+1] # store the data
            self.networkManager.sendMsg(SENSOR, self.sensor_group_list[1].pack()) # send the data
            time.sleep(1)
            """
            for i in range((len(self.data_list)-1)):
                print(f"{self.parameter_names[i+1]}:{self.sensor_group_list[self.device_type].get_sensor(i).data}")            
            print(f"pack:{SENSOR, self.sensor_group_list[1].pack()}")
            """
            # print()

if __name__ == "__main__":
    cf = CF(toolBox = None)
    dev = AquaDevice(device_type = 1, sensor_group_list = cf.sensor_group_list) 
    dev.start_loop()
    time.sleep(5)