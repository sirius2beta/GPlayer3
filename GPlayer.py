import GToolBox
import time
from NetworkManager import NetworkManager
from DataLogger import DataLogger

class GPlayer:
	def __init__(self):
		self.toolBox = GToolBox.GToolBox(self) # initiate all modules
		
		DataLogger(self.toolBox)
		
		self.mainLoop()	# keep main thread alive

	def mainLoop(self):
		# keep main GPlayer alive
		while True:
			time.sleep(10)



	

