import os
import time
import threading
import subprocess
from GTool import GTool
from datetime import datetime

class DataLogger(GTool):
    def __init__(self, toolbox):
        super().__init__(toolbox) 
        self._toolBox = toolbox
        """
        1. 在初始化 DataLogger 時，會檢查是否存在存放log的資料夾 "/home/pi/GPlayerLog"，
            若不存在，則自動建立該資料夾。
        2. 使用初始化當下的時間來定義日誌文件的名稱，格式為：log_YYYYMMDD_HHMM.txt，
            其中 YYYY 是西元年，MM 是月份，DD 是日期，HHMM 是時間的時和分。
        """
        # ================================================================================
        try:
            cmd = " grep '^VERSION_CODENAME=' /etc/os-release"
            returned_value = subprocess.check_output(cmd,shell=True,stderr=subprocess.DEVNULL).replace(b'\t',b'').decode("utf-8") 
        except:
            returned_value = '0'
		
        if(len(returned_value) > 1):
            sys = returned_value.split('=')[1].strip()
            if(sys == 'buster'):
                self.log_folder_path = "/home/pi/GPlayerLog"
            elif(sys == 'bionic'):
                self.log_folder_path = "/home/jetson/GPlayerLog"
        
        self.log_directory = os.path.expanduser(self.log_folder_path)      # 設定log存放路徑
        if(not os.path.exists(self.log_directory)):                         # 如果路徑不存在，則建立
            os.makedirs(self.log_directory)                                 # 建立路徑
        current_time = datetime.now()                                       # 取得目前時間
        file_name = f"log_{current_time.strftime('%Y%m%d_%H%M')}.txt"       # 設定檔案名稱
        self.log_file = os.path.join(self.log_directory, file_name)         # 檔案路徑
        # ================================================================================

        threading.Thread(target = self.looper, daemon = True).start() # 開始log

    def log_data(self):
        gps_data = {
            'time_usec': 0,
            'fix_type': 0,
            'lat': 0,
            'lon': 0,
            'alt': 0,
            'HDOP': 0,
            'VDOP': 0,
        }
        aqua_data = [] * 21 
        pi_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            gps_data = self._toolBox.mavManager.gps_data
            depth = self._toolBox.mavManager.depth
        except Exception as e:
            print(f'DataLogger exception: GPS_data: msg:{e}')
            pass
            
        try:
            if(self._toolBox.deviceManager.aqua_device != None):
                aqua_data = self._toolBox.deviceManager.aqua_device.get_aqua_data()
        except Exception as e:
            print(f'DataLogger exception: Aqua_data: msg:{e}')
            pass

        try:
            with open(self.log_file, 'a') as log:
                log_entry = (
                    f"Pi time:{pi_time}, {gps_data['time_usec']}, {gps_data['fix_type']}, "
                    f"{gps_data['lat']}, {gps_data['lon']}, {gps_data['alt']}, "
                    f"{gps_data['HDOP']}, {gps_data['VDOP']}, {depth}, {aqua_data}\n"
                )
                log.write(log_entry)

        except Exception as e:
            print(f'DataLogger exception: log_entry: msg:{e}')
            pass

    def looper(self):
        while(True):
            self.log_data()
            time.sleep(1)
