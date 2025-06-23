import multiprocessing 
import subprocess

from NetworkManager import NetworkManager
from VideoManager import VideoManager
from DeviceManager import DeviceManager
from MavManager import MavManager
from config import Config

# from OakCam import OakCam
from DataLogger import DataLogger
from KBestReader import KBestReader
# from CoolingModule import CoolingModule





# GToolBox stores all the modules and initialize them
class GToolBox:
	def __init__(self, core):
		# ================================== 取得OS資訊 ==================================  
		self.OS = 'None'
		try:
			cmd = " grep '^VERSION_CODENAME=' /etc/os-release"
			returned_value = subprocess.check_output(cmd,shell=True,stderr=subprocess.DEVNULL).replace(b'\t',b'').decode("utf-8") 
		except:
			returned_value = '0'
		if(len(returned_value) > 1): 
			self.OS = returned_value.split('=')[1].strip()
		print(f"Operating System: {self.OS}")
		# ===============================================================================
		self.AIDetection = False
		self.config = Config(self)
		self.core = core # core is GPlayer main function itself
		self.mav_conn, self.child_conn = multiprocessing.Pipe() # Pipe for modules with multiprocess

		# Initialize all modules here
		print("GPlayer initializing...")
		self.networkManager = NetworkManager(self)
		self.mavManager = MavManager(self)
		# need to set sensorgrouplist before DeviceManager started, which let sensor message of pixhawk come in
		self.mavManager.setSensorGroupList(self.config.sensor_group_list)
		self.mavManager.startLoop()
		#self.oakCam = OakCam(self)
		
		self.videoManager = VideoManager(self)
		self.deviceManager = DeviceManager(self)
		self.kBestReader = KBestReader(self)
		#self.oakCam = OakCam(self)
		self.dataLogger = DataLogger(self)

		if self.OS != 'buster':
			from JetsonDetect import JetsonDetect
			self.jetsonDetect = JetsonDetect(self)
			self.jetsonDetect.startLoop()
			pass
		
		
		# networkManager is not started until after everything is ready
		#self.oakCam.startLoop()
		self.networkManager.startLoop()
		
		print("start loops!!")

	def core(self):
		return self.core