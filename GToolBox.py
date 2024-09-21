import multiprocessing 

from NetworkManager import NetworkManager
from VideoManager import VideoManager
from DeviceManager import DeviceManager
from MavManager import MavManager
from config import Config
from OakCam import OakCam
from DataLogger import DataLogger
from CoolingModule import CoolingModule

# GToolBox stores all the modules and initialize them
class GToolBox:
	def __init__(self, core):
		self.config = Config(self)
		self.core = core # core is GPlayer main function itself
		self.mav_conn, self.child_conn = multiprocessing.Pipe() #Pipe for modules with multiprocess

		# Initialize all modules here
		print("GPlayer initializing...")
		self.networkManager = NetworkManager(self)
		self.mavManager = MavManager(self)		
		self.videoManager = VideoManager(self)
		self.deviceManager = DeviceManager(self)
		self.oakCam = OakCam(self)
		self.mavManager.setSensorGroupList(self.config.sensor_group_list)
		# networkManager is not started until after everything is ready
		self.dataLogger = DataLogger(self)
		self.networkManager.startLoop()

		print("GPlayer initialized!")
		
	def core(self):
		return self.core