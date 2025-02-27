import time
import struct

from Dev.Device import Device

# This is a test device, it will send fake sensor data

# we will set pin 11 as power switch

SENSOR = b'\x04'

class SonarDevice(Device):
    def __init__(self, toolBox):
        super().__init__(device_type = -1, networkManager = toolBox.networkManager)
        self._toolBox = toolBox
        self.control_type = 2 # sonar control type: 2
        self.power = 0
        
        if self._toolBox.OS == 'buster':
            print(f"SonarDevice::create sonar device: OS:{self._toolBox.OS}")
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            #GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(11, GPIO.OUT)
            GPIO.output(11, GPIO.LOW)
        elif self._toolBox.OS == "focal":
            print(f"SonarDevice::create sonar device: OS:{self._toolBox.OS}")
            import Jetson.GPIO as GPIO
            self.GPIO = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(13, GPIO.OUT)
            GPIO.output(13, GPIO.LOW)
    def __del__(self):
        GPIO.cleanup()
    def processCMD(self, control_type ,cmd):
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
                self.power = cmd[1]
                if self.power == 1:
                    self.GPIO.output(13, self.GPIO.HIGH)
                    print("power on")
                else:
                    self.GPIO.output(13, self.GPIO.LOW)
                    print("power off")
            elif command_type == 7: #power
                data = struct.pack("<B", self.control_type)
                data += struct.pack("<B", 7)
                data += struct.pack("<B", self.power)
                self.networkManager.sendMsg(b'\x05', data)
                
    