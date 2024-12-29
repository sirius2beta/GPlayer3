import time
import serial
import threading
from Device import Device

SENSOR = b'\x04'

class ArduSimpleDevice(Device):           
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)
        
        # [message_id, utc_position_fix, rms_pseudorange_residual, semi_major_error, semi_minor_error, ellipse_orientation, lat_acc, lon_acc, alt_acc, checksum]
        self.GST_list = [None, None, None, None, None, None, None, None, None, None]
        self.ser = serial.Serial(port = self.dev_path, baudrate = 115200, timeout = 2)
        threading.Thread(target = self.reader, daemon = True).start() # start the reader thread

    def reader(self):
        try: 
            while(True):
                raw_data = self.ser.readline()
                decode_data = raw_data.decode('utf-8').strip().lstrip('$')
                fields = decode_data.split(',')
                if('*' in fields[-1]):
                    checksum_data = fields[-1].split('*')
                    fields[-1] = checksum_data[0]
                    checksum = checksum_data[1]
                else:
                    checksum = None
                self.GST_list = [
                    fields[0],               # message_id
                    fields[1],               # utc_position_fix
                    float(fields[2]) if fields[2] else None,  # rms_pseudorange_residual
                    float(fields[3]) if fields[3] else None,  # semi_major_error
                    float(fields[4]) if fields[4] else None,  # semi_minor_error
                    float(fields[5]) if fields[5] else None,  # ellipse_orientation
                    float(fields[6]) if fields[6] else None,  # lat_acc
                    float(fields[7]) if fields[7] else None,  # lon_acc
                    float(fields[8]) if fields[8] else None,  # alt_acc
                    checksum               # checksum
                ]
                print(f"raw_data:\n{raw_data}")
                print(self.GST_list)

        except(serial.serialutil.SerialException): # if serial error
            print("Serial Error...")
            print("Trying to reconnect...")

        except Exception as e: # if other error
            print(e)
        
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

            self.networkManager.sendMsg(SENSOR, self.sensor_group_list[6].pack()) # send the data to the network manager  
            time.sleep(1)
            

if(__name__ == "__main__"):
    ArduSimpleDevice(None, "/dev/ttyACM0", None, None)
    time.sleep(1000)