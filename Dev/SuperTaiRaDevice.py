import time
import serial
import threading
from Dev.Device import Device

SENSOR = b'\x04'

class SuperTaiRaDevice(Device):           
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)

        self.ser = serial.Serial(port = self.dev_path, baudrate = 115200, timeout = 2)
        threading.Thread(target = self.reader, daemon = True).start() # start the reader thread
        self.strength = -1
        self.error_byte = -1

    def reader(self):
        while(True):
            try:
                self.ser.read(self.ser.in_waiting)  # 清空緩衝區
                # ===== 送出封包 =====
                packet = bytes([0x01, 0x02, 0x03])
                self.ser.write(packet)
                print(f"📤 Packet sent: {packet.hex()}")
                time.sleep(1)  # 送包間隔
                # ===== 嘗試讀回傳 binary =====
                try:
                    if self.ser.in_waiting >= 6:  # 至少要有原始資料+3個尾部
                        response = self.ser.read(self.ser.in_waiting)
                        if response:
                            main_data = response[:-3]
                            rssi1 = response[0]
                            rssi2 = response[1]
                            error_byte = response[2]
                            self.strength = rssi1 - rssi2
                            self.error_byte = error_byte
                            print(f"📥 Received: {response.hex()}")
                            print(f"strength: {rssi1-rssi2}")
                            print(f"error byte: {error_byte}")
                        else:
                            print("⏳ No response (timeout)")
                except serial.SerialException:
                    print("⚠️ Serial read error")

                

            except serial.serialutil.SerialException:
                print("⚠️ Serial Error... Trying to reconnect...")
                self.connect()

            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                time.sleep(1)

    def start_loop(self):
        super().start_loop() 
            
    def _io_loop(self):
        while(True):
            
            time.sleep(1)
            

if(__name__ == "__main__"):
    ArduSimpleDevice(None, "/dev/ttyACM0", None, None)
    time.sleep(1000)