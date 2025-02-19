import time

from Dev.Device import Device

# This is a test device, it will send fake sensor data

# we will set pin 11 as power switch

SENSOR = b'\x04'

class SonarDevice():
    def __init__(self, toolBox):
        self._toolBox = toolBox
        self.control_type = 1 # sonar control type: 1
        
        if self._toolBox.OS == 'buster':
            print(f"SonarDevice::create sonar device: OS:{self._toolBox.OS}")
            import RPi.GPIO as GPIO
            #GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(11, GPIO.OUT)
            GPIO.output(11, GPIO.LOW)
    def processMsg(self, msg):
        if control_type == self.control_type:
            print("SonarDevice::getMsg")
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
                pass

            elif command_type == 4: #回傳全部參數
                pass
            elif command_type == 5: #回傳部分參數
                pass
            elif command_type == 6: #power
                power = cmd[1]
                if power == 1:
                    print("power on")
                else:
                    print("power off")
                
    