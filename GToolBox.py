import multiprocessing 
import sys
sys.path.append("NPUCO/TemperatureSensorInterface")

from temp_sensor_interface_V3_1 import SensorReader
from NetworkManager import NetworkManager
from VideoManager import VideoManager
from DeviceManager import DeviceManager
from MavManager import MavManager
from config import Config

class GToolBox:
	def __init__(self, core):
		self.config = Config(self)
		self.core = core
		self.mav_conn, self.child_conn = multiprocessing.Pipe()

		self.networkManager = NetworkManager(self)
		self.mavManager = MavManager(self)		
		self.videoManager = VideoManager(self)
		self.deviceManager = DeviceManager(self)

		self.networkManager.startLoop()
		
	def core():
		return self.core