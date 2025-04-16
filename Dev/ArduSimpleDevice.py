import time
import serial
import threading
from Dev.Device import Device

SENSOR = b'\x04'

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
        self.ser = serial.Serial(port = self.dev_path, baudrate = 115200, timeout = 2)
        threading.Thread(target = self.reader, daemon = True).start() # start the reader thread

    def reader(self):
        while(True):
            try: 
                # =====這裡做資料處理輸出field List=====
                raw_data = self.ser.readline()
                decode_data = raw_data.decode('utf-8').strip().lstrip('$')
                fields = decode_data.split(',')
                if('*' in fields[-1]):
                    checksum_data = fields[-1].split('*')
                    fields[-1] = checksum_data[0]
                    checksum = checksum_data[1]
                else:
                    checksum = None
                # ================= When output is GST =================
                if(fields[0] == "GPGST" or fields[0] == "GLGST" or fields[0] == "GNGST"):
                    self.GST_list = [
                        fields[0],  # message_id
                        fields[1],  # utc_position_fix
                        fields[2],  # rms_pseudorange_residual
                        fields[3],  # semi_major_error
                        fields[4],  # semi_minor_error
                        fields[5],  # ellipse_orientation
                        fields[6],  # lat_acc
                        fields[7],  # lon_acc
                        fields[8],  # alt_acc
                        checksum    # checksum
                    ] 

                    self.ACC_list = [
                        fields[6],  # lat_acc
                        fields[7],  # lon_acc
                        fields[8],  # alt_acc
                    ]
                    
                    # print(f"GST_list:\n{self.GST_list}")
                    # print(f"ACC_list:\n{self.ACC_list}")

                # ================= When output is RMC =================
                if(fields[0] == "GPRMC" or fields[0] == "GMRMC"):
                    self.RMC_list = [
                        fields[0],  # message_id
                        fields[1],  # utc_position_fix
                        fields[2],  # Status
                        fields[3] + "," + fields[4],  # Latitude
                        fields[5] + "," + fields[6],  # Longitude
                        fields[7],  # Speed
                        fields[8],  # Track_angle
                        fields[9],  # Date
                        fields[10], # Magnetic_variation
                        checksum    # checksum
                    ] 

                    #print(f"RMC_list:\n{self.RMC_list}")
                # ================= When output is AVR =================
                if(fields[0] == "PTNL" and fields[1] == "AVR"):
                    self.AVR_list = [
                        fields[0] + "," + fields[1],  # message_id
                        fields[2],  # utc_vector_fix
                        fields[3],  # yaw_angle
                        fields[4],  # yaw
                        fields[5],  # tilt_angle
                        fields[6],  # tilt
                        fields[7],  # None
                        fields[8],  # None
                        fields[9],  # range_meters
                        fields[10], # gps_quality_indicator
                        fields[11], # pdop
                        fields[12], # num_satellites_used
                        checksum    # checksum
                    ] 
                    
                    #print(f"AVR_list:\n{self.AVR_list}")
                
                # ================= When output is GGA =================
                if(fields[0] == "GPGGA"):
                    self.GGA_list = [
                        fields[0],  # message_id
                        fields[1],  # utc_vector_fix
                        fields[2],  # Latitude
                        fields[3],  # N or S
                        fields[4],  # Longitude
                        fields[5],  # E or W
                        fields[6],  # GPS Quality
                        fields[7],  # --
                        fields[8],  # HDOP
                        fields[9],  # Orthometric height
                        fields[10], # --
                        fields[11], # Geoid separation
                        fields[12], # --
                        fields[13], # --
                        fields[14], # --
                        checksum    # checksum
                    ]
                

            except(serial.serialutil.SerialException): # if serial error
                print("Serial Error...")
                print("Trying to reconnect...")

            except Exception as e: # if other error
                print(e)
        
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