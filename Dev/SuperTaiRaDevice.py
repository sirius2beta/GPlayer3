import time       
import serial 
import threading 
import logging
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
        logging.info(f"SuperTairaComport:{self.dev_path}")
        logging.info(f"SuperTaira initialized")
        time.sleep(0.2)

        # 啟動讀寫執行緒
        threading.Thread(target=self.transmitter, daemon=True).start()

    def start_loop(self):
        super().start_loop()

    def _io_loop(self):
        pass

    def transmitter(self):
        logging.info(f"SuperTaira Started")
        while(True):
            try:
                data = b'\x55\x54\x53\x00\x01\x02'
                self.ser.write(data)
                print(f"send:{data}")
                # logging.info(f"send:{data}")
            except Exception as e:
                logging.error(f"Taira:{e}")
                self.ser = serial.Serial(self.dev_path, baudrate=READ_TIMEOUT, timeout=READ_TIMEOUT)
            finally:
                time.sleep(1)

if __name__ == "__main__":
    dev = SuperTaiRaDevice(device_type=None, dev_path="/dev/ttyUSB0", sensor_group_list=None, networkManager=None)
    try:
        time.sleep(1000) 
    except KeyboardInterrupt:
        dev.stop()
