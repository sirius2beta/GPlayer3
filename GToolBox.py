import DeviceManager as DM
import MavManager
import multiprocessing 
import sys
sys.path.append("NPUCO/TemperatureSensorInterface")
from temp_sensor_interface_V2 import SensorReader, SensorType



class GToolBox:
	def __init__(self, core):
		self.core = core
		self.mav_conn, child_conn = multiprocessing.Pipe()
		self.p = multiprocessing.Process(target = MavManager.task, args = (child_conn,)) 
		# 啟動process，告訴作業系統幫你創建一個process，是Async的
		self.p.start()
		
		#self.mav_conn.send("g /dev/PD0")
		#self.mavManager = MavManager.MavManager(self)
		self.deviceManager = DM.DeviceManager(self)
		self.sensorReader = SensorReader()
	def core():
		return self.core