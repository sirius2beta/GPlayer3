import time
import serial
import struct
import threading
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
        self.data_list = [0.0] * 22 # sensor data list
        self.send_interval = 5 # every 5 seconds send data to the network manager
        self.read_all = False # initialize read_all as False, only read depth data.
        self.ser = serial.Serial(port = self.dev_path, baudrate = 19200, bytesize = 8, parity = 'E', stopbits = 1, timeout = 3)
        
        self.wake_up() # wake up the AT600
        threading.Thread(target = self.reader, daemon = True).start() # start the reader thread
    
    def aqua_data(self):
        return self.data_list

    def send(self, command): # send command to device and get response, command is a list of hex values.
        command = bytes([int(x, 16) for x in command]) # commnad to bytes
        self.ser.write(command) # write command to device
        response = self.ser.read(19) # read response from device
        response = [format(x, '02x') for x in response] # convert to hex
        return response 
    
    def wake_up(self): # wake up the device
        while(True):
            wake_up_command = bytes([int(x, 16) for x in self.command_set[0]]) # commnad to bytes
            self.ser.write(wake_up_command) # write command to device
            response = self.ser.read(5) # read response from device
            response = [format(x, '02x') for x in response] # convert to hex
            
            if(response == ['01', '8d', '01', '84', '90']):
                print("AT600 is ready...")
                break
            else:
                print("retry to wake up the AT600...")
            
            time.sleep(2)

    def reader(self): # read data from the device and store it in the data_list.
        try: 
            while(True):
                if(self.read_all): # if read_all is True, read all data
                    for i in range(len(self.command_set)):
                        data = self.send(command = self.command_set[i]) # send command to device
                        try:
                            value = data[3] + data[4] + data[5] + data[6] # get the value
                            value = struct.unpack('>f', bytes.fromhex(value))[0] # convert hex to float
                            self.data_list[i] = value # store the value
                        except Exception as e:
                            print(f"{i}:{e}")
                            continue
                else:
                    data = self.send(command = self.command_set[3]) # send command to device
                    try:
                        value = data[3] + data[4] + data[5] + data[6] # get the value
                        value = struct.unpack('>f', bytes.fromhex(value))[0] # convert hex to float
                        self.data_list[3] = value # store the value
                    except Exception as e:
                        print(f"{3}:{e}")
                        continue
                time.sleep(1)

        except serial.serialutil.SerialException: # if serial error
            print("Serial Error...")
            print("Trying to reconnect...")

        except Exception as e: # if other error
            print(e)
        
    def start_loop(self):
        super().start_loop() 
            
    def _io_loop(self):
        while(True):
            time.sleep(self.send_interval)

            for i in range((len(self.data_list)-1)): # loop through the data list
                self.sensor_group_list[1].get_sensor(i).data = self.data_list[i+1] # store the data
            
            # print the data to the console, for testing
            """
            for i in range((len(self.data_list)-1)):
                print(f"{self.sensor_group_list[self.device_type].get_sensor(i).data}")  
            print(f"pack:{SENSOR, self.sensor_group_list[1].pack()}")
            """
            self.networkManager.sendMsg(SENSOR, self.sensor_group_list[1].pack()) # send the data to the network manager                         
