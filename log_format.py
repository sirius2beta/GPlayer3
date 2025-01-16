import csv
from io import StringIO

class LogFormat:
    def __init__(self):
        # Pixhawk 資料
        self.time_usec = -1     # 時間戳記 (微秒)
        self.fix_type = -1      # 定位類型
        self.lat = -1           # 緯度
        self.lon = -1           # 經度
        self.alt = -1           # 海拔高度
        self.HDOP = -1          # 水平精度因子 (HDOP)
        self.VDOP = -1          # 垂直精度因子 (VDOP)
        self.depth = -1         # 深度

        # ArduSimple 精度數據
        self.lat_acc = -1       # 緯度精度
        self.lon_acc = -1       # 經度精度
        self.alt_acc = -1       # 高度精度

        # Aqua 資料 (根據 XML 修改名稱並轉換為小寫)
        self.temperature = -1                       # 1. 水溫
        self.pressure = -1                          # 2. 壓力
        self.aqua_depth = -1                        # 3. 深度
        self.level_depth_to_water = -1              # 4. 水位深度
        self.level_surface_elevation = -1           # 5. 表面高程
        self.actual_conductivity = -1               # 6. 實際導電率
        self.specific_conductivity = -1             # 7. 特定導電率
        self.resistivity = -1                       # 8. 電阻率
        self.salinity = -1                          # 9. 鹽度
        self.total_dissolved_solids = -1            # 10. 總溶解固體
        self.density_of_water = -1                  # 11. 水密度
        self.barometric_pressure = -1               # 12. 大氣壓力
        self.ph = -1                                # 13. pH 值
        self.ph_mv = -1                             # 14. pH 毫伏
        self.orp = -1                               # 15. 氧化還原電位 (ORP)
        self.dissolved_oxygen_concentration = -1    # 16. 溶解氧濃度
        self.dissolved_oxygen_saturation = -1       # 17. 溶解氧飽和度百分比
        self.turbidity = -1                         # 18. 濁度
        self.oxygen_partial_pressure = -1           # 19. 氧分壓
        self.external_voltage = -1                  # 20. 外部電壓
        self.battery_capacity_remaining = -1        # 21. 電池剩餘容量

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

if __name__ == "__main__":
    log = LogFormat()
    csv_data = log.get_all()
    print(f"csv_data:{csv_data}, type:{type(csv_data)}")  # 輸出 CSV 格式
