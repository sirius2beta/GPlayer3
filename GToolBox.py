import multiprocessing 
import subprocess
import concurrent.futures
import logging
from datetime import datetime


from NetworkManager import NetworkManager
from VideoManager import VideoManager
from DeviceManager import DeviceManager
from MavManager import MavManager
from config import Config


# from OakCam import OakCam
from DataLogger import DataLogger
from KBestReader import KBestReader
# from CoolingModule import CoolingModule

def load_seagrass_detect(toolBox):
    from unet.SeagrassDetect import SeagrassDetect
    return SeagrassDetect(toolBox)

def load_jetson_detect(toolBox):
    from JetsonDetect import JetsonDetect
    return JetsonDetect(toolBox)


# GToolBox stores all the modules and initialize them
class GToolBox:
	def __init__(self, core):
		# ================================== 取得OS資訊 ==================================  
		self.OS = 'None'
		try:
			cmd = " grep '^VERSION_CODENAME=' /etc/os-release"
			returned_value = subprocess.check_output(cmd,shell=True,stderr=subprocess.DEVNULL).replace(b'\t',b'').decode("utf-8") 
		except:
			logging.error("Failed to get OS information. Defaulting to 'None'.")
			returned_value = ''
		if(len(returned_value) > 1): 
			self.OS = returned_value.split('=')[1].strip()
			logging.info(f"Operating System: {self.OS}")
		# ===============================================================================
		self.config = Config(self)
		self.mav_conn, self.child_conn = multiprocessing.Pipe() # Pipe for modules with multiprocess

		# Initialize all modules here
		logging.info("Modules initializing...")
		self.networkManager = NetworkManager(self)
		self.mavManager = MavManager(self)
		# need to set sensorgrouplist before DeviceManager started, which let sensor message of pixhawk come in
		self.mavManager.setSensorGroupList(self.config.sensor_group_list)		
		self.videoManager = VideoManager(self)
		self.deviceManager = DeviceManager(self)
		self.kBestReader = KBestReader(self)
		self.dataLogger = DataLogger(self)
		
		if self.OS != "buster":


			self.seagrassDetect = load_seagrass_detect(self) # add to toolbox
			self.jetsonDetect = load_jetson_detect(self) # add to toolbox
			self.jetsonDetect.startLoop() # start the JetsonDetect loop
			self.seagrassDetect.startLoop() # start the SeagrassDetect loop

		self.mavManager.startLoop()
		self.networkManager.startLoop()
		
