import subprocess
import threading
import time
from config import Config as CF
# snmpwalk -v 2c -c public 192.168.1.11 .1.3.6.1
# snmpget -v 2c -c public 192.168.1.11 .1.3.6.1.4.1.17455.70.701.2.8.1.4.1
# snmpget -v 2c -c public 192.168.1.11 .1.3.6.1.4.1.17455.70.701.2.8.1.9.1

SENSOR = b'\x04'

class KBestReader():
    def __init__(self, toolbox):
        super().__init__(toolbox)
        self._toolBox = toolbox

        self.local_rssi_oid = '.1.3.6.1.4.1.17455.70.701.2.8.1.4.1'
        self.remote_rssi_oid = '.1.3.6.1.4.1.17455.70.701.2.8.1.9.1'
        
        self.local_rssi = 0
        self.remote_rssi = 0

        threading.Thread(target = self.reader, daemon = True).start() # start the reader thread
        threading.Thread(target = self._io_loop, daemon = True).start() # start the _io_loop

    def reader(self):
        while(True):
            try:
                snmp_read_local_rssi_cmd = ['snmpget', '-v', '2c', '-c', 'public', '192.168.1.11', self.local_rssi_oid]
                snmp_read_local_rssi_result = subprocess.run(snmp_read_local_rssi_cmd, capture_output=True, text=True, timeout = 5)

                snmp_read_remote_rssi_cmd = ['snmpget', '-v', '2c', '-c', 'public', '192.168.1.11', self.remote_rssi_oid]
                snmp_read_remote_rssi_result = subprocess.run(snmp_read_remote_rssi_cmd, capture_output=True, text=True, timeout = 5)

                self.local_rssi = snmp_read_local_rssi_result
                self.remote_rssi = snmp_read_remote_rssi_result

                print(f'snmp_read_local_rssi_result:{snmp_read_local_rssi_result}')
                print(f'snmp_read_remote_rssi_result:{snmp_read_remote_rssi_result}')

                time.sleep(1)

            except subprocess.TimeoutExpired:
                print("SNMP command timed out.")
                return None
            except Exception as e:
                print(f"Exception occurred: {e}")
                return None
        
    def _io_loop(self):
        while(True):
            try:
                self.sensor_group_list[5].get_sensor(0).data = self.local_rssi_oid  # boat RSSI
                self.sensor_group_list[5].get_sensor(1).data = self.remote_rssi_oid # remote RSSI
                self._toolBox.networkManager.sendMsg(SENSOR, self.sensor_group_list[5].pack()) # send the data to the network manager  
                time.sleep(1) 
            
            except Exception as e:
                print(f'KBestReader exception: {e}')