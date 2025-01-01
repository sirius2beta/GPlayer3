import time
import serial

from Dev.Device import Device

# This device will connect to arduino, which canc accept command for winch control
# Command for arduino
            # stepper settings:          s,2,0,2 5 2000 1000 [operaton, header, ID, dirPin stepPin maxSpeed acceleration]
            # stepper control:           c,2,2,800 [operaton, header, ID, steps]
            # stepper stop:              z,2


SENSOR = b'\x04'

class WinchDevice(Device):
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)
        self.isSerialInit = False
        try:
            self.serialOut = serial.Serial(port = self.dev_path, baudrate = 9600, timeout = 5) 
            self.isSerialInit = True
            # initialize winch on arduino
            self.send(f's,2,0,2 5 2000 1000')

        except serial.serialutil.SerialException: # if serial error
            print("Serial Error...")
            print("Trying to reconnect...")

        except Exception as e: # if other error
            print(e) 
    
    def start_loop(self):
        super().start_loop()

    def send(self, command):
        self.serialOut.write((command+"\n").encode()) # if use modbus ASCII, add .encode('utf-8')
        
    
    # getter
    def get(self): 
        pass
    
    # setter
    def set(self):
        pass
        
    # process command for control
    def processCMD(self, control_type ,cmd):
        if control_type == 0:
            command_type = int(cmd[0])
            print(f"control:{control_type}, command type:{command_type}, ")
            if command_type == 0:  # set maxspeed, acceleration
                print("  - set")
                # 待新增
            elif command_type == 1:  # run steps
                steps = int.from_bytes(cmd[1:], 'little', signed=True)
                print(f"  - steps:{steps}")
                if self.isSerialInit == True:
                    self.send(f'c,2,2,{steps}')
            elif command_type == 2:  # stop
                print("  - stop")
                if self.isSerialInit == True:
                    self.send('z,2')
            
    def _io_loop(self):
        time.sleep(1)