import os
import time
import threading

from datetime import datetime
from GToolBox import GToolBox

class DataLogger:
    def __init__(self, toolbox):
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
        gps_data = {"time_usec": 0, "fix_type": 0, "lat": 0, "lon": 0, "alt": 0, "HDOP": 0, "VDOP": 0}
        aqua_data = []
        
        if(not (self._toolBox.mavManager is None)):
            gps_data = self._toolBox.mavManager.gps_data()
        if(not (self._toolBox.deviceManager.aqua_device is None)):
            aqua_data = self._toolBox.deviceManager.aqua_device.aqua_data()
        
        with open(self.log_file, 'a') as log:
            log_entry = f"{gps_data['time_usec']}, {gps_data['fix_type']}, {gps_data['lat']}, {gps_data['lon']}, {gps_data['alt']}, {gps_data['HDOP']}, {gps_data['VDOP']}, {aqua_data}\n"
            log.write(log_entry)

    def looper(self):
        while(True):
            self.log_file = self._create_log_file()
            self.log_gps_data()
            time.sleep(5)
