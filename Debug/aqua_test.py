import time
import serial
import struct
import threading

class AquaDevice():           
    def __init__(self, dev_path=""):
        self.dev_path = dev_path
        self.command_set = [
            ['01', '03', '15', '4A', '00', '07', '21', 'D2'], # 0:溫度 o
            #['01', '03', '15', '51', '00', '07', '51', 'D5'], # 壓力 
            #['01', '03', '15', '58', '00', '07', '81', 'D7'], # 深度 
            #['01', '03', '15', '5F', '00', '07', '30', '16'], # 水位，對水的深度
            ['01', '03', '15', '66', '00', '07', 'E0', '1B'], # 表面高程 o
            ['01', '03', '15', '82', '00', '07', 'A0', '2C'], # 5:實際導電率 o
            #['01', '03', '15', '89', '00', '07', 'D1', 'EE'], # 特定導電率
            #['01', '03', '15', '90', '00', '07', '00', '29'], # 電阻率
            #['01', '03', '15', '97', '00', '07', 'B1', 'E8'], # 鹽度
            #['01', '03', '15', '9E', '00', '07', '61', 'EA'], # 總溶解固體
            #['01', '03', '15', 'A5', '00', '07', '10', '27'], # 10:水密度
            #['01', '03', '15', 'B3', '00', '07', 'F1', 'E3'], # 大氣壓力
            ['01', '03', '15', 'BA', '00', '07', '21', 'E1'], # pH值 o
            #['01', '03', '15', 'C1', '00', '07', '51', 'F8'], # pH毫伏
            ['01', '03', '15', 'C8', '00', '07', '81', 'FA'], # 氧化還原電位（ORP）o
            #['01', '03', '15', 'CF', '00', '07', '30', '3B'], # 15:溶解氧濃度
            ['01', '03', '15', 'D6', '00', '07', 'E1', 'FC'], # 溶解氧飽和度百分比 o
            ['01', '03', '15', 'F2', '00', '07', 'A1', 'F7'], # 濁度 o
            #['01', '03', '16', '15', '00', '07', '11', '84'], # 氧分壓
            #['01', '03', '16', '23', '00', '07', 'F1', '8A'], # 外部電壓
            #['01', '03', '16', '2A', '00', '07', '21', '88'], # 20:電池剩餘容量
        ]
        self.data_list = [0.0] * 21 # sensor data list (empty list, length = 22)
        self.read_all = True # If read_all as False, only read depth data.
        self.ser = serial.Serial(port = self.dev_path, baudrate = 19200, bytesize = 8, parity = 'E', stopbits = 1, timeout = 6)
        threading.Thread(target = self.reader, daemon = True).start() # start the reader thread
    
    def get_aqua_data(self):
        return self.data_list

    def send(self, command): # send command to device and get response, command is a list of hex values.
        #print(f"Request:{command}")
        command = bytes([int(x, 16) for x in command]) # commnad: list to bytes
        self.ser.write(command) # write command to device
        response = self.ser.read(19) # read response from device
        response = [format(x, '02x') for x in response] # convert to hex
        #print(f"response:{response}")
        return response 

    def reader(self): # read data from the device and store it in the data_list.
        try: 
            while(True):
                if(self.read_all): # if read_all is True, read all data
                    tt1 = time.time()
                    for i in range(len(self.command_set)):
                        t1 = time.time()
                        data = self.send(command = self.command_set[i]) # send command to device
                        try:
                            value = data[3] + data[4] + data[5] + data[6] # get the value
                            value = struct.unpack('>f', bytes.fromhex(value))[0] # convert hex to float
                            self.data_list[i] = value # store the value
                        except Exception as e:
                            print(f"{i}:{e}")
                            continue
                        t2 = time.time()

                        print(f"用時:{t2 - t1}")
                    tt2 = time.time()
                    print(f"完成讀取一圈，用時:{tt2-tt1}")
                else:
                    data = self.send(command = self.command_set[3]) # send command to device
                    try:
                        value = data[3] + data[4] + data[5] + data[6] # get the value
                        value = struct.unpack('>f', bytes.fromhex(value))[0] # convert hex to float
                        self.data_list[3] = value # store the value
                    except Exception as e:
                        print(f"{3}:{e}")
                        continue

        except serial.serialutil.SerialException: # if serial error
            print("Serial Error...")
            print("Trying to reconnect...")

        except Exception as e: # if other error
            print(e)

if(__name__ == "__main__" ):
    aqua = AquaDevice("/dev/ttyUSB0")     
    time.sleep(1000)