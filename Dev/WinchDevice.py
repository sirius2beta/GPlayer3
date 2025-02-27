import time
import serial
import struct
from Dev.Device import Device

# This device will connect to arduino, which canc accept command for winch control
# Command for arduino
            # stepper settings:          s,2,0,2 5 2000 1000 [operaton, header, ID, dirPin stepPin maxSpeed acceleration]
            # stepper control:           c,2,2,800 [operaton, header, ID, steps]
            # stepper stop:              z,2


CONTROL = b'\x05'

class WinchDevice(Device):
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)
        self.isSerialInit = False
        self.control_type = 0
        try:
            self.serialOut = serial.Serial(port = self.dev_path, baudrate = 9600, timeout = 5) 
            self.isSerialInit = True
            # initialize winch on arduino
            self.send(f's,2000 1000')

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
        if self.isSerialInit == False:
            return
        if control_type == self.control_type:
            command_type = int(cmd[0])
            print(f"control:{control_type}, command type:{command_type}, ")
            if command_type == 0:  # 讀取全部參數
                print("  - set")
                # 待新增
            elif command_type == 1:  # 讀取部分參數
                pass
            elif command_type == 2:  # 寫入全部參數
                pass

            elif command_type == 3: #寫入部分參數
                index = int(cmd[1])
                print(f"write index:{index}")
                if index == 0: #maxspeed
                    maxSpeed = int(struct.unpack("<I", cmd[2:])[0])
                    if maxSpeed>2000: #  maxspeed cant exceed 2000
                        pass
                    self.send(f's,{maxSpeed} {maxSpeed/2}')
                    print(f"set maxspeed:{maxSpeed}")

            elif command_type == 4: #回傳全部參數
                pass
            elif command_type == 5: #回傳部分參數
                pass
            elif command_type == 6: #move
                step = int(struct.unpack("<i", cmd[1:])[0])
                print(f"WinchDevice: move step {step}")
                if self.isSerialInit == True:
                    self.send(f'c,{step}')
            elif command_type == 7: #stop
                self.send(f'z,')
                print("WinchDevice: stop")
            elif command_type == 8: # report step tension
                pass
            elif command_type == 9: # reset position
                self.send(f're')
                print("WinchDevic: reset")

            
    def _io_loop(self):
        step = 0
        tension = 0
        status = 0
        while True:
            input = self.serialOut.readline()
            print(input)
            try:
                input = input.decode().split(",")
                if input[0] == "cs":
                    step = int(input[1])
                    tension = int(input[2])
                    if input[3][0] == 'S':
                        status = 0
                    elif input[3][0] == 'R':
                        status = 1
                    else:
                        status = 3
            except:
                pass
            time.sleep(0.2)
            data = struct.pack("<B", self.control_type)
            data += struct.pack("<B", 8)
            data += struct.pack("<i", step)
            data += struct.pack("<i", tension)
            data += struct.pack("<B", status)
            self.networkManager.sendMsg(b'\x05', data)

