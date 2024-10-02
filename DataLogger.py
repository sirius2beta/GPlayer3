import os
import time
import threading

from GTool import GTool
from datetime import datetime

#self._toolBox.mavManager.depth  存取深度資料

class DataLogger(GTool):
    def __init__(self, toolbox):
        super().__init__(toolbox)
        self._toolBox = toolbox
        self.log_directory = os.path.expanduser("/home/pi/GPlayerLog") # 設定log存放路徑
        if(not os.path.exists(self.log_directory)): # 如果路徑不存在，則建立
            os.makedirs(self.log_directory) # 建立路徑
        self.log_file = self._create_log_file() # 建立log檔案

        threading.Thread(target = self.looper, daemon = True).start() # 開始log

    def _create_log_file(self):
        current_time = datetime.now() # 取得目前時間
        file_name = f"aqua_{current_time.strftime('%Y%m%d_%H%M')}.txt" # 設定檔案名稱
        return os.path.join(self.log_directory, file_name) # 回傳檔案路徑

    def log_gps_data(self):
        self.gps_data = {
            'time_usec': 0,
            'fix_type': 0,
            'lat': 0,
            'lon': 0,
            'alt': 0,
            'HDOP': 0,
            'VDOP': 0
        }
        aqua_data = [] * 21 
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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
            
        with open(self.log_file, 'a') as log:
            log_entry = f"Pi time:{now}, {gps_data['time_usec']}, {gps_data['fix_type']}, {gps_data['lat']}, {gps_data['lon']}, {gps_data['alt']}, {gps_data['HDOP']}, {gps_data['VDOP']}, {depth}, {aqua_data}\n"
            log.write(log_entry)

    def looper(self):
        while(True):
            self.log_gps_data()
            time.sleep(1)
