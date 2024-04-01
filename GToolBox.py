import multiprocessing 
import sys
sys.path.append("NPUCO/TemperatureSensorInterface")

from temp_sensor_interface_V3_1 import SensorReader
from NetworkManager import NetworkManager
from VideoManager import VideoManager
from DeviceManager import DeviceManager
import MavManager
from config import Config

class GToolBox:
	def __init__(self, core):
		self.config = Config(self)
		self.core = core
		self.mav_conn, child_conn = multiprocessing.Pipe()
		# mavmanager 用multiprocessing處理，因為之前用thread會有問題
		self.p = multiprocessing.Process(target = MavManager.task, args = (child_conn,)) 
		self.p.start()
		
		# ToDo:
		# 1. SensorManager
		# 2. ControlManager
		self.videoManager = VideoManager(self)
		self.networkManager = NetworkManager(self)
		self.deviceManager = DeviceManager(self)
		self.sensorReader = SensorReader()
		self.sensorReader.setSerialPort("/dev/ttyUSB0")
		self.sensorReader.setXMLPath("NPUCO/TemperatureSensorInterface/SensorType.xml")

		self.networkManager.startLoop()
		
	def core():
		return self.core