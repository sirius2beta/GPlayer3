import time       
import serial 
import threading 
from Dev.Device import Device 

BAUD = 115200
READ_TIMEOUT = 0.05

class SuperTaiRaDevice(Device):
    def __init__(self, device_type, dev_path="", sensor_group_list=None, networkManager=None):
        super().__init__(device_type, dev_path, sensor_group_list or [], networkManager)
        self._stop = False
        self.strength = 0 
        self.error_byte = 0
        self.ser = serial.Serial(
            port=self.dev_path, timeout=READ_TIMEOUT, baudrate=BAUD
        )
        print(f"------> SuperTairaComport:{self.dev_path}")
        time.sleep(0.2)

        # 啟動讀寫執行緒
        threading.Thread(target=self.transmitter, daemon=True).start()

    def start_loop(self):
        super().start_loop()

    def _io_loop(self):
        pass

    def transmitter(self):
        while(True):
            try:
                data = b'\x55\x54\x53\x00\x01\x02'
                self.ser.write(data)
                # print(f"send:{data}")
            except Exception as e:
                print(f"Taira發送問題:{e}")   
                try:
                    self.ser.close()
                    time.sleep(1)
                    self.ser = serial.Serial(self.dev_path, baudrate=READ_TIMEOUT, timeout=READ_TIMEOUT)
                except Exception as re:
                    print(f"重連失敗:{re}") 

            finally:
                time.sleep(1)

if __name__ == "__main__":
    dev = SuperTaiRaDevice(device_type=None, dev_path="/dev/ttyUSB0", sensor_group_list=None, networkManager=None)
    try:
        time.sleep(1000) 
    except KeyboardInterrupt:
        dev.stop()
