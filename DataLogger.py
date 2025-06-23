import os
import time
import threading

from GTool import GTool
from datetime import datetime
from log_format import LogFormat

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
        
        self.log_directory = os.path.expanduser(self.log_folder_path)       # 設定log存放路徑
        if(not os.path.exists(self.log_directory)):                         # 如果路徑不存在，則建立
            os.makedirs(self.log_directory)                                 # 建立路徑
        current_time = datetime.now()                                       # 取得目前時間
        file_name = f"log_{current_time.strftime('%Y%m%d_%H%M')}.txt"       # 設定檔案名稱
        self.log_file = os.path.join(self.log_directory, file_name)         # 檔案路徑
        # ================================================================================

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

        # 更新 Log 資料
        try:
            # Pixhawk Data
            self.log_data.time_usec = mav_gps_data['time_usec']
            self.log_data.fix_type = mav_gps_data['fix_type']
            self.log_data.lat = mav_gps_data['lat']
            self.log_data.lon = mav_gps_data['lon']
            self.log_data.alt = mav_gps_data['alt']
            self.log_data.HDOP = mav_gps_data['HDOP']
            self.log_data.VDOP = mav_gps_data['VDOP']
            self.log_data.depth = mav_depth
            # V2新增
            self.log_data.speed = mav_vfr_hud['groundspeed']
            self.log_data.roll = mav_attitude['roll']
            self.log_data.pitch = mav_attitude['pitch']
            self.log_data.yaw = mav_gps['yaw'] 

            # ArduSimple Accuracy
            self.log_data.lat_acc = acc_data[0]
            self.log_data.lon_acc = acc_data[1]
            self.log_data.alt_acc = acc_data[2]
            # V2新增
            self.log_data.gps_speed = rmc_data[5]
            self.log_data.gps_tilt = avr_data[4]
            self.log_data.gps_yaw = avr_data[2]
            # V3新增
            self.log_data.gps_orthometric_height = gga_data[9]
            self.log_data.geoid_separation = gga_data[11]



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

            # 保存到日誌檔案
            with open(self.log_file, 'a') as log:
                log.write(self.log_data.get_all())

        except Exception as e:
            print(f'DataLogger exception: log_entry: msg:{e}')

    def looper(self):
        while True:
            self.save_data()
            time.sleep(1)