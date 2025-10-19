import time
import serial
import threading
from pysbf2.sbfreader import SBFReader
from pysbf2.sbftypes_core import SBF_PROTOCOL, NMEA_PROTOCOL
import math
from datetime import datetime, timedelta
from Dev.Device import Device

SENSOR = b'\x04'

def gps_time_to_utc(wnc, tow):
    gps_start = datetime(1980, 1, 6)
    total_seconds = wnc * 7 * 86400 + tow/1000
    utc_time = gps_start + timedelta(seconds=total_seconds)

    # 注意：GPS 時間比 UTC 多 18 秒（截至目前），要減去 leap seconds
    LEAP_SECONDS = 18  # 根據當前標準，可能會變
    utc_time -= timedelta(seconds=LEAP_SECONDS)

    return utc_time

def position_accuracy(cov_latlat, cov_lonlon, cov_heightheight):
    def safe_sqrt(x):
        # 如果因浮點誤差導致略小於0，強制設為0
        return math.sqrt(x) if x >= 0 else math.sqrt(max(0, x))
    
    sigma_lat = safe_sqrt(cov_latlat)
    sigma_lon = safe_sqrt(cov_lonlon)
    sigma_h   = safe_sqrt(cov_heightheight)
    
    return sigma_lat, sigma_lon, sigma_h

class ArduSimpleDevice(Device):           
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)
        
        # [message_id, utc_position_fix, rms_pseudorange_residual, semi_major_error, semi_minor_error, ellipse_orientation, lat_acc, lon_acc, alt_acc, checksum]
        self.GST_list = [None, None, None, None, None, None, None, None, None, None]
        # [lat_acc, lon_acc, alt_acc]
        self.ACC_list = [None, None, None]
        # [message_id, utc_position_fix, Status , Latitude, Longitude, Speed , Track_angle, Date, Magnetic_variation, checksum]
        self.RMC_list = [None, None, None, None, None, None, None, None, None, None]
        
        # [message_id, utc_vector_fix, yaw_angle, yaw, tilt_angle, tilt, None, None, range_meters, gps_quality_indicator, pdop, num_satellites_used, checksum]
        self.AVR_list = [None, None, None, None, None, None, None, None, None, None, None, None, None]

        self.GGA_list = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]
        self.utc_time = ""
        self.lon = 0.0
        self.lat = 0.0
        self.alt = 0.0
        self.undulation = 0.0
        self.lon_acc = 0.0
        self.lat_acc = 0.0
        self.alt_acc = 0.0
        self.HDOP = 0.0
        self.VDOP = 0.0
        self.tilt = 0.0
        self.yaw = 0.0
        self.speed = 0.0
        self.ser = serial.Serial(port = self.dev_path, baudrate = 115200, 
                                timeout = 2,
                                bytesize=serial.EIGHTBITS,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE)
        threading.Thread(target = self.reader, daemon = True).start() # start the reader thread

    def reader(self):
        while(True):
            try: 
                # =====這裡做資料處理輸出field List=====

                reader = SBFReader(self.ser, protfilter=SBF_PROTOCOL|NMEA_PROTOCOL)  # 只讀 SBF 協定
                
                # 連續讀取
                for raw, msg in reader:
                    # raw 是原始二進位資料 bytes
                    # msg 是已解析的 SBFMessage 物件
                    #print("Raw len:", len(raw), " bytes")
                    #print(msg)  # 會以可讀形式顯示欄位與值
                    if msg.identity == 'PVTGeodetic':
                        # 根據 msg 屬性名稱取經緯度（若 msg 有這些屬性）
                        tow = msg.TOW  # 秒
                        wnc = msg.WNc  # 週
                        utc = gps_time_to_utc(wnc, tow)
                        self.utc_time = utc
                        
                        #print(f"🕒 GPS Time (UTC): {utc.strftime('%Y-%m-%d %H:%M:%S')} TOW:{tow}, WNC:{wnc}")
                        lat = msg.Latitude  # 有些 PVT message 有這欄
                        lon = msg.Longitude

                        self.utc_time = utc
                        self.lat = math.degrees(lat)
                        self.lon = math.degrees(lon)
                        self.alt = msg.Height
                        self.undulation = msg.Undulation
                        # 有時候是 X, Y, Z 坐標，而不是經緯度
                        #print(f"Latitude: {math.degrees(lat)}°, Longitude: {math.degrees(lon)}°")
                    elif msg.identity == 'DOP':
                        HDOP = msg.HDOP
                        VDOP = msg.VDOP
                        self.HDOP = HDOP
                        self.VDOP = VDOP
                        #print(f"HDOP: {HDOP}, VDOP: {VDOP}")
                    elif msg.identity == 'PosCovGeodetic':
                        cov_latlat = msg.Cov_latlat
                        cov_lonlon = msg.Cov_lonlon
                        cov_heightheight = msg.Cov_hgthgt
                        lat_acc, lon_acc, alt_acc = position_accuracy(cov_latlat, cov_lonlon, cov_heightheight)
                        self.lat_acc = lat_acc
                        self.lon_acc = lon_acc
                        self.alt_acc = alt_acc
                        #print(f"Position Accuracy - Lat: {lat_acc:.3f} m, Lon: {lon_acc:.3f} m, Alt: {alt_acc:.3f} m")
                    elif msg.identity == 'PTNLAVR':
                        self.tilt = msg.tilt
                        self.yaw = msg.yaw
                        #print(f"  Tilt: {msg.tilt:.2f}°, Heading: {msg.yaw:.2f}°")
                    elif msg.identity == 'GPRMC':
                        self.speed = msg.spd
                        #print(f"  Speed: {msg.spd:.2f}")
                    else:
                        #print("其他 SBF 訊息類型:", msg.identity)
                        pass

                

            except(serial.serialutil.SerialException): # if serial error
                print("Serial Error...")
                print("Trying to reconnect...")
            except Exception as e: # if other error
                print("❌ 開啟串口或解析時發生錯誤：", e)
        
    def get_GSTList(self):
        return self.GST_list
    
    def get_ACCList(self):
        return self.ACC_list
    
    def get_RMCList(self):
        return self.RMC_list
    
    def get_AVRList(self):
        return self.AVR_list
    
    def get_GGAList(self):
        return self.GGA_list

    def start_loop(self):
        super().start_loop() 
            
    def _io_loop(self):
        while(True):
            if(self.GST_list[6] == None):
                self.sensor_group_list[6].get_sensor(0).data = -1 # lat_acc
            else:
                self.sensor_group_list[6].get_sensor(0).data = self.GST_list[6] # lat_acc

            if(self.GST_list[6] == None):
                self.sensor_group_list[6].get_sensor(1).data = -1 # lon_acc
            else:
                self.sensor_group_list[6].get_sensor(1).data = self.GST_list[7] # lon_acc

            if(self.GST_list[6] == None):
                self.sensor_group_list[6].get_sensor(2).data = -1 # alt_acc
            else:
                self.sensor_group_list[6].get_sensor(2).data = self.GST_list[8] # alt_acc
            time.sleep(1)
            

if(__name__ == "__main__"):
    ArduSimpleDevice(None, "/dev/ttyACM0", None, None)
    time.sleep(1000)