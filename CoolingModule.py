import serial
import subprocess
import threading
import time

class CoolingModule():
    def __init__(self):
        self.release_rfcomm_connections() # 先釋放所有 rfcomm 連接
        bluetooth_devices_list = self.get_paired_bluetooth_devices() # 取得已配對的藍牙裝置
        self.stop_event = threading.Event()  # 用於停止 listener 執行緒
        for device in bluetooth_devices_list: # 逐一檢查配對裝置
            addr, name = device['address'], device['name'] # 取得裝置的地址和名稱
            if(name == "CoolingModule"): # 如果名稱是 AutoFeeder
                print("      ...Devicefactory create CoolingModule...")
                self.bind_rfcomm(0, addr) # 綁定到 rfcomm 0
                time.sleep(1)
                self.ser = serial.Serial(port = "/dev/rfcomm0", baudrate = 115200, timeout = 5)
                threading.Thread(target=self.listener).start()
                print("\t啟動 CoolingModule.py")
    
    def listener(self): # 監聽ESP32的回傳
        print("open listener")
        while(not self.stop_event.is_set()):
            response = self.ser.readline()
            print(f"response: {response.decode('utf-8')}")
    
    def transmitter(self, command): # 傳送指令給ESP32
        if(command == "open"):
            self.ser.write('1'.encode('utf-8'))
        elif(command == "close"):
            self.ser.write('0'.encode('utf-8'))

    def release_rfcomm_connections(self): # 釋放所有 rfcomm 連接
        result = subprocess.run(['rfcomm'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        connections = []

        for line in output.split('\n'):
            if line.startswith('rfcomm'):
                parts = line.split()
                device = parts[0]
                connections.append(device)
        
        for device in connections:
            # print(f"Releasing {device}")
            subprocess.run(['sudo', 'rfcomm', 'release', device])

    def get_paired_bluetooth_devices(self): # 取得已配對的藍牙裝置
        # 進入 bluetoothctl 並執行指令
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

    def bind_rfcomm(self, channel, device_address): # 把藍牙綁訂到 rfcomm            
        try:
            subprocess.check_call(['sudo', 'rfcomm', 'bind', str(channel), device_address, '1'])
            # print(f"綁定 {device_address} 到 RFCOMM channel {channel}")
        except subprocess.CalledProcessError as e:
            print(f"綁定失敗: {e}")

    def stop_listener(self):  # 停止 listener 執行緒
        self.stop_event.set()
        self.listener_thread.join()
        self.ser.close()
        

if __name__ == "__main__":
    cm = CoolingModule()
    cm.transmitter("open")
    time.sleep(3)
    cm.transmitter("close")
    cm.stop_listener()
    


    
    