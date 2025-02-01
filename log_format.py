import csv
from io import StringIO

class LogFormat:
    def __init__(self):
        # Pixhawk 資料
        self.time_usec = None     # 時間戳記 (微秒)
        self.fix_type = None      # 定位類型
        self.lat = None           # 緯度
        self.lon = None           # 經度
        self.alt = None           # 海拔高度
        self.HDOP = None          # 水平精度因子 (HDOP)
        self.VDOP = None          # 垂直精度因子 (VDOP)
        self.depth = None         # 深度
        # V2新增
        self.speed = None         # 速度
        self.roll = None          # 姿態-翻滚
        self.pitch = None         # 姿態-俯仰
        self.yaw = None           # 姿態-航偏

        # ArduSimple 精度數據
        self.lat_acc = None       # 緯度精度
        self.lon_acc = None       # 經度精度
        self.alt_acc = None       # 高度精度
        # V2新增
        self.gps_speed = None         # GPS-速度
        self.gps_tilt = None          # GPS-俯仰
        self.gps_yaw = None           # GPS-航偏

        # Aqua 資料 (根據 XML 修改名稱並轉換為小寫)
        self.temperature = None                       # 1. 水溫
        self.pressure = None                          # 2. 壓力
        self.aqua_depth = None                        # 3. 深度
        self.level_depth_to_water = None              # 4. 水位深度
        self.level_surface_elevation = None           # 5. 表面高程
        self.actual_conductivity = None               # 6. 實際導電率
        self.specific_conductivity = None             # 7. 特定導電率
        self.resistivity = None                       # 8. 電阻率
        self.salinity = None                          # 9. 鹽度
        self.total_dissolved_solids =None            # 10. 總溶解固體
        self.density_of_water = None                  # 11. 水密度
        self.barometric_pressure = None               # 12. 大氣壓力
        self.ph = None                                # 13. pH 值
        self.ph_mv = None                             # 14. pH 毫伏
        self.orp = None                               # 15. 氧化還原電位 (ORP)
        self.dissolved_oxygen_concentration = None    # 16. 溶解氧濃度
        self.dissolved_oxygen_saturation = None       # 17. 溶解氧飽和度百分比
        self.turbidity = None                         # 18. 濁度
        self.oxygen_partial_pressure = None           # 19. 氧分壓
        self.external_voltage = None                  # 20. 外部電壓
        self.battery_capacity_remaining = None        # 21. 電池剩餘容量

    def get_all(self):
        """取得所有屬性和值，並返回 CSV 格式"""
        data = self.__dict__  # 獲取所有屬性和值，回傳型態為字典，key 為標題，value 為數值
        # 將屬性名稱和值分別存儲為標題和行內容
        values = list(data.values())

        # 使用 StringIO 作為內存中的 CSV 文件
        output = StringIO()  # 新增 StringIO 物件
        writer = csv.writer(output) 
        writer.writerow(values)   # 寫入值

        # 返回 CSV 格式內容
        return output.getvalue()
    
    def get_pixhawk_format():
        pass

    def get_ardusimple_format():
        pass

    def get_aqua_format():
        pass

if __name__ == "__main__":
    log = LogFormat()
    log.temperature = 20 # 假設溫度是20度
    
    csv_data = log.get_all()
    print(f"csv_data:{csv_data}, type:{type(csv_data)}")  # 輸出 CSV 格式