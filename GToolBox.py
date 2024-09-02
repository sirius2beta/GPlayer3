import multiprocessing 

from NetworkManager import NetworkManager
from VideoManager import VideoManager
from DeviceManager import DeviceManager
from MavManager import MavManager
from config import Config
from OakCam import OakCam

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
		# need to set sensorgrouplist before DeviceManager started, which let sensor message of pixhawk come in
		self.mavManager.setSensorGroupList(self.config.sensor_group_list)
		self.mavManager.startLoop()
		self.videoManager = VideoManager(self)
		self.deviceManager = DeviceManager(self)
		self.oakCam = OakCam(self)

		# networkManager is not started until after everything is ready
		self.networkManager.startLoop()

		print("GPlayer initialized!")
		
	def core(self):
		return self.core
