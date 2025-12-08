import os
import time
import threading
import csv
import re

from GTool import GTool
from datetime import datetime
from log_format import LogFormat
from datetime import datetime

class DataLogger(GTool):
    def __init__(self, toolbox):
        super().__init__(toolbox) 
        self._toolBox = toolbox
        self.log_data = LogFormat() # 存放資料的地方
        """
        1. 在初始化 DataLogger 時，會檢查是否存在存放log的資料夾 "../GPlayerLog"，
            若不存在，則自動建立該資料夾。
        2. 使用初始化當下的時間來定義日誌文件的名稱，格式為：log_YYYYMMDD_HHMM.txt，
            其中 YYYY 是西元年，MM 是月份，DD 是日期，HHMM 是時間的時和分。
        """
        # ================================================================================
        self.log_folder_path = "../GPlayerLog"
        

        # 設定 log 存放路徑
        self.log_directory = os.path.expanduser(self.log_folder_path)
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

        # 找出所有 log_xxxxxxxx.csv 檔案
        existing_files = [f for f in os.listdir(self.log_directory) if f.startswith("log_") and f.endswith(".csv")]

        # 從檔名抓出數字部分
        indices = []
        for f in existing_files:
            match = re.search(r"log_(\d+)\.csv", f)
            if match:
                indices.append(int(match.group(1)))

        # 取最大值 + 1，如果沒有檔案就從 1 開始
        file_index = max(indices) + 1 if indices else 1

        # 檔名格式：log_00000001.csv
        file_name = f"log_{file_index:08d}.csv"
        self.log_file = os.path.join(self.log_directory, file_name)
        self.log_folder_path = "./GPlayerLog"

        # 建立 CSV 檔案，並寫入欄位名稱
        with open(self.log_file, 'w', newline='', encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.log_data.__dict__.keys())
            writer.writeheader()
        threading.Thread(target = self.looper, daemon = True).start() # 開始log

    def save_data(self):
        mav_gps_data = {'time_usec': -1, 'fix_type': -1, 'lat': -1, 'lon': -1, 'alt': -1, 'HDOP': -1, 'VDOP': -1}
        mav_attitude = {'pitch': 0.0, 'roll': 0.0 }
        mav_gps = {'yaw': 0}
        mav_vfr_hud = {'groundspeed' : 0}
        aqua_data = {key: -1 for key in range(21)}  # 初始化 21 個 Aqua 屬性為 -1
        acc_data = [-1]*3  # [lat_acc, lon_acc, alt_acc]
        rmc_data = [-1]*10
        avr_data = [-1]*13
        gga_data = [-1]*16
        super_taira_strength = -1
        kbest_boat_rssi = -1
        kbest_ground_rssi = -1
        super_taira_error_byte = -1

        # 嘗試從工具箱中調用數據
        try:
            mav_gps_data = self._toolBox.mavManager.gps_data
            mav_depth = self._toolBox.mavManager.depth
            mav_attitude = self._toolBox.mavManager.mav_attitude
            mav_gps = self._toolBox.mavManager.mav_gps
            mav_vfr_hud = self._toolBox.mavManager.vfr_hud
        except Exception as e:
            print(f'DataLogger exception: MAV_data: msg:{e}')
        
        try:
            if self._toolBox.deviceManager.aqua_device is not None:
                aqua_data = self._toolBox.deviceManager.aqua_device.get_aqua_data()
        except Exception as e:
            print(f'DataLogger exception: Aqua_data: msg:{e}')
        
        try:
            if self._toolBox.deviceManager.ardusimple_device is not None:
                acc_data = self._toolBox.deviceManager.ardusimple_device.get_ACCList()
                rmc_data = self._toolBox.deviceManager.ardusimple_device.get_RMCList()
                avr_data = self._toolBox.deviceManager.ardusimple_device.get_AVRList()
                gga_data = self._toolBox.deviceManager.ardusimple_device.get_GGAList()
        except Exception as e:
            print(f'DataLogger exception: ardusimple_device: msg:{e}')
        try:
            if self._toolBox.deviceManager.super_taira_device is not None:
                super_taira_strength = self._toolBox.deviceManager.super_taira_device.strength
                super_taira_error_byte = self._toolBox.deviceManager.super_taira_device.error_byte
        except Exception as e:
            print(f'DataLogger exception: super_taiRa: msg:{e}')

        kbest_ground_rssi = self._toolBox.kBestReader.local_rssi  # 獲取 Kbest 的 RSSI 數據
        kbest_boat_rssi = self._toolBox.kBestReader.remote_rssi  # 獲取 Kbest 的 Ground RSSI 數據


        # 更新 Log 資料
        try:
            self.log_data.timestamp = self._toolBox.deviceManager.ardusimple_device.utc_time if self._toolBox.deviceManager.ardusimple_device else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            # Pixhawk Data
            self.log_data.time_usec = self._toolBox.deviceManager.ardusimple_device.utc_time
            self.log_data.fix_type = mav_gps_data['fix_type']
            self.log_data.lat = self._toolBox.deviceManager.ardusimple_device.lat #mav_gps_data['lat']
            self.log_data.lon = self._toolBox.deviceManager.ardusimple_device.lon #mav_gps_data['lon']
            self.log_data.alt = self._toolBox.deviceManager.ardusimple_device.alt #mav_gps_data['alt']
            self.log_data.HDOP = self._toolBox.deviceManager.ardusimple_device.HDOP #mav_gps_data['HDOP']
            self.log_data.VDOP = self._toolBox.deviceManager.ardusimple_device.VDOP #mav_gps_data['VDOP']
            self.log_data.depth = mav_depth
            # V2新增
            self.log_data.speed = mav_vfr_hud['groundspeed']
            self.log_data.roll = mav_attitude['roll']
            self.log_data.pitch = mav_attitude['pitch']
            self.log_data.yaw = mav_gps['yaw'] 

            # ArduSimple Accuracy
            self.log_data.lat_acc = self._toolBox.deviceManager.ardusimple_device.lat_acc
            self.log_data.lon_acc = self._toolBox.deviceManager.ardusimple_device.lon_acc
            self.log_data.alt_acc = self._toolBox.deviceManager.ardusimple_device.alt_acc
            # V2新增
            self.log_data.gps_speed = self._toolBox.deviceManager.ardusimple_device.speed
            self.log_data.gps_tilt = self._toolBox.deviceManager.ardusimple_device.tilt
            self.log_data.gps_yaw = self._toolBox.deviceManager.ardusimple_device.yaw
            # V3新增
            self.log_data.gps_orthometric_height = self._toolBox.deviceManager.ardusimple_device.alt - self._toolBox.deviceManager.ardusimple_device.undulation
            self.log_data.geoid_separation = self._toolBox.deviceManager.ardusimple_device.undulation



            # Aqua Data
            self.log_data.temperature = aqua_data[0]                         # 1. 水溫
            self.log_data.pressure = aqua_data[1]                            # 2. 壓力
            self.log_data.aqua_depth = aqua_data[2]                          # 3. 深度
            self.log_data.level_depth_to_water = aqua_data[3]                # 4. 水位深度
            self.log_data.level_surface_elevation = aqua_data[4]             # 5. 表面高程
            self.log_data.actual_conductivity = aqua_data[5]                 # 6. 實際導電率
            self.log_data.specific_conductivity = aqua_data[6]               # 7. 特定導電率
            self.log_data.resistivity = aqua_data[7]                         # 8. 電阻率
            self.log_data.salinity = aqua_data[8]                            # 9. 鹽度
            self.log_data.total_dissolved_solids = aqua_data[9]              # 10. 總溶解固體
            self.log_data.density_of_water = aqua_data[10]                   # 11. 水密度
            self.log_data.barometric_pressure = aqua_data[11]                # 12. 大氣壓力
            self.log_data.ph = aqua_data[12]                                 # 13. pH 值
            self.log_data.ph_mv = aqua_data[13]                              # 14. pH 毫伏
            self.log_data.orp = aqua_data[14]                                # 15. 氧化還原電位 (ORP)
            self.log_data.dissolved_oxygen_concentration = aqua_data[15]     # 16. 溶解氧濃度
            self.log_data.dissolved_oxygen_saturation = aqua_data[16]        # 17. 溶解氧飽和度百分比
            self.log_data.turbidity = aqua_data[17]                          # 18. 濁度
            self.log_data.oxygen_partial_pressure = aqua_data[18]            # 19. 氧分壓
            self.log_data.external_voltage = aqua_data[19]                   # 20. 外部電壓
            self.log_data.battery_capacity_remaining = aqua_data[20]         # 21. 電池剩餘容量

            self.log_data.kbest_boat_rssi = kbest_boat_rssi            # Kbest-船載接收訊號強度指標
            self.log_data.kbest_ground_rssi = kbest_ground_rssi            # Kbest-基站接收訊
            self.log_data.super_taira_strength = super_taira_strength      # SuperTaiRa-訊號強度指標
            self.log_data.super_taira_error_byte = super_taira_error_byte    # SuperTaiRa-錯誤碼
        

            # 保存到日誌檔案
            with open(self.log_file, 'a', newline='', encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.log_data.__dict__.keys())
                writer.writerow(self.log_data.__dict__)

        except Exception as e:
            print(f'DataLogger exception: log_entry: msg:{e}')

    def looper(self):
        while True:
            self.save_data()
            time.sleep(1)
