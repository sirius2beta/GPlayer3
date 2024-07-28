import serial
import subprocess
import threading
import time

class CoolingModule():
    def __init__(self):
        self.release_rfcomm_connections()  # 先釋放所有 rfcomm 連接
        bluetooth_devices_list = self.get_paired_bluetooth_devices()  # 取得已配對的藍牙裝置


        for device in bluetooth_devices_list:  # 逐一檢查配對裝置
            addr, name = device['address'], device['name']  # 取得裝置的地址和名稱
            
            if(name == "CoolingModule"):  # 如果名稱是 CoolingModule
                self.is_open  = False # 定義散熱模組現在的狀態
                self.is_leaking =  False # 定義是否有漏水的情況發生
                
                self.bind_rfcomm(0, addr)  # 綁定到 rfcomm 0
                time.sleep(1)
                self.ser = serial.Serial(port="/dev/rfcomm0", baudrate=115200, timeout=5)
                self.listener_thread = threading.Thread(target=self.listener)
                self.listener_thread.start()
                print("      ...Devicefactory create CoolingModule...")
            elif():
                # other bluetooth device
                pass
    
    def release_rfcomm_connections(self):  # 釋放所有 rfcomm 連接
        result = subprocess.run(['rfcomm'], stdout=subprocess.PIPE) 
        output = result.stdout.decode('utf-8') 
        connections = []

        for line in output.split('\n'):
            if line.startswith('rfcomm'):
                parts = line.split()
                device = parts[0]
                connections.append(device)
        
        for device in connections:
            subprocess.run(['sudo', 'rfcomm', 'release', device])

    def get_paired_bluetooth_devices(self):  # 取得已配對的藍牙裝置
        process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(input=b'devices\nexit\n')

        devices = []
        for line in stdout.decode('utf-8').split('\n'):
            if 'Device' in line:
                parts = line.split(' ')
                device_address = parts[1]
                device_name = ' '.join(parts[2:])
                devices.append({'address': device_address, 'name': device_name})
        
        return devices

    def bind_rfcomm(self, channel, device_address):  # 把藍牙綁訂到 rfcomm
        try:
            subprocess.check_call(['sudo', 'rfcomm', 'bind', str(channel), device_address, '1'])
        except subprocess.CalledProcessError as e:
            print(f"綁定失敗: {e}")

    def listener(self):  # 監聽ESP32的回傳
        # print("open listener")
        while(True):
            response = self.ser.readline().decode('utf-8').replace('\n', '').strip()
            # print(f"{response}")
            if(response == "warning: water leaking"):
                self.is_open = False
                self.is_leaking = True
                print("warning: water leaking")
            elif(response == "open"):
                self.is_open = True
                self.is_leaking = False
                print("open")
            elif(response == "close"):
                self.is_open = False
                print("close")
    
    def transmitter(self, command):  # 傳送指令給ESP32
        if command == "open":
            self.ser.write('1'.encode('utf-8'))
        elif command == "close":
            self.ser.write('0'.encode('utf-8'))

if __name__ == "__main__":
    cooling_module = CoolingModule()
    print(f"1: isopen:{cooling_module.is_open}, isleaking:{cooling_module.is_leaking}")
    
    cooling_module.transmitter("open")
    time.sleep(2)
    print(f"2: isopen:{cooling_module.is_open}, isleaking:{cooling_module.is_leaking}")
    time.sleep(5)
    
    cooling_module.transmitter("close")
    time.sleep(2)
    print(f"3: isopen:{cooling_module.is_open}, isleaking:{cooling_module.is_leaking}")
    time.sleep(5)
    