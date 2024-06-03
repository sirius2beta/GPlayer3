import multiprocessing 

from NetworkManager import NetworkManager
from VideoManager import VideoManager
from DeviceManager import DeviceManager
from MavManager import MavManager
from config import Config
from OakCam import OakCam

# GToolBox包含所有的模組，負責模組的初始化，threading的開始
class GToolBox:
	def __init__(self, core):
		self.config = Config(self)
		self.core = core # core即為GPlayer，主程式loop
		self.mav_conn, self.child_conn = multiprocessing.Pipe() # 與其他process傳輸的pipe

		self.networkManager = NetworkManager(self)
		self.mavManager = MavManager(self)		
		self.videoManager = VideoManager(self)
		self.deviceManager = DeviceManager(self)
		self.oakCam = OakCam(self)

		self.networkManager.startLoop()
		
	def core(self):
		return self.core