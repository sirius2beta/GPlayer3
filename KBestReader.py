import subprocess
import threading
import time
import re

SENSOR = b'\x04'

class KBestReader():
    def __init__(self, toolbox):
        self._toolBox = toolbox
        self.sensor_group_list = toolbox.config.sensor_group_list

        self.local_rssi_oid = '.1.3.6.1.4.1.17455.70.701.2.8.1.4.1'
        self.remote_rssi_oid = '.1.3.6.1.4.1.17455.70.701.2.8.1.9.1'
        self.tx_rate_oid = '.1.3.6.1.4.1.17455.70.701.2.8.1.5.1'
        self.rx_rate_oid = '.1.3.6.1.4.1.17455.70.701.2.8.1.6.1'
        
        self.local_rssi = 0
        self.remote_rssi = 0
        self.tx_rate = 0
        self.rx_rate = 0

        threading.Thread(target = self.reader, daemon = True).start() # start the reader thread
        threading.Thread(target = self._io_loop, daemon = True).start() # start the _io_loop

    def reader(self):
        while(True):
            try:
                snmp_read_local_rssi_cmd = ['snmpget', '-v', '2c', '-c', 'public', '192.168.1.11', self.local_rssi_oid]
                snmp_read_local_rssi_result = subprocess.run(snmp_read_local_rssi_cmd, capture_output=True, text=True, timeout = 5)

                snmp_read_remote_rssi_cmd = ['snmpget', '-v', '2c', '-c', 'public', '192.168.1.11', self.remote_rssi_oid]
                snmp_read_remote_rssi_result = subprocess.run(snmp_read_remote_rssi_cmd, capture_output=True, text=True, timeout = 5)

                snmp_read_tx_rate_cmd = ['snmpget', '-v', '2c', '-c', 'public', '192.168.1.11', self.tx_rate_oid]
                snmp_read_tx_rate_result = subprocess.run(snmp_read_tx_rate_cmd, capture_output=True, text=True, timeout = 5)

                snmp_read_rx_rate_cmd = ['snmpget', '-v', '2c', '-c', 'public', '192.168.1.11', self.rx_rate_oid]
                snmp_read_rx_rate_result = subprocess.run(snmp_read_rx_rate_cmd, capture_output=True, text=True, timeout = 5)
                
                stdout = snmp_read_local_rssi_result.stdout
                match = re.search(r'(-?\d+)(?=dBm)', stdout)
                if(match):
                    extracted_value = int(match.group(1))
                    self.local_rssi = extracted_value

                stdout = snmp_read_remote_rssi_result.stdout
                match = re.search(r'(-?\d+)(?=dBm)', stdout)
                if(match):
                    extracted_value = int(match.group(1))
                    self.remote_rssi = extracted_value

                stdout = snmp_read_tx_rate_result.stdout
                match = re.search(r'(\d+\.\d+)(?=Mbps)', stdout)
                if(match):
                    extracted_value = float(match.group(1))
                    self.tx_rate = extracted_value

                stdout = snmp_read_rx_rate_result.stdout
                match = re.search(r'(\d+\.\d+)(?=Mbps)', stdout)
                if(match):
                    extracted_value = float(match.group(1))
                    self.rx_rate = extracted_value

            except subprocess.TimeoutExpired:
                print("SNMP command timed out.")
                print("Please confirm whether the KBest device is connected.")
                return None
            except FileNotFoundError:
                print("Please confirm that the SNMP method has been downloaded to the computer.")
            except Exception as e:
                print(f"Exception occurred: {e}")
                return None
            finally:
                time.sleep(1)
        
    def _io_loop(self):
        while(True):
            try:
                self.sensor_group_list[5].get_sensor(0).data = self.local_rssi  # boat RSSI
                self.sensor_group_list[5].get_sensor(1).data = self.remote_rssi # remote RSSI
                self.sensor_group_list[5].get_sensor(2).data = self.tx_rate  # TX Rate
                self.sensor_group_list[5].get_sensor(3).data = self.rx_rate  # RX Rate
                # print(f"local_rssi:{self.local_rssi}dBm, remote_rssi:{self.remote_rssi}dBm, tx_rate:{self.tx_rate}Mbps, rx_rate:{self.rx_rate}Mbps")
                self._toolBox.networkManager.sendMsg(SENSOR, self.sensor_group_list[5].pack()) # send the data to the network manager  
            except Exception as e:
                print(f'KBestReader exception: {e}')

            finally:
                time.sleep(1) 