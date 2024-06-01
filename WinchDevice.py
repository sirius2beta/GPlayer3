import time
from Device import Device

SENSOR = b'\x04'

class WinchDevice(Device):
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)
    
    def start_loop(self):
        super().start_loop()

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
            if command_type == 0:
                print("  - set")
            elif command_type == 1:
                steps = int.from_bytes(cmd[1:], 'little', signed=True)
                print(f"  - steps:{steps}")
            elif command_type == 2:
                print("  - stop")
            

    def _io_loop(self):
        time.sleep(1)