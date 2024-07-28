import GToolBox
import time
from NetworkManager import NetworkManager

class GPlayer:
	def __init__(self):
		self.toolBox = GToolBox.GToolBox(self) # initiate all modules
		
		self.mainLoop()	# keep main thread alive

	def mainLoop(self):
		# keep main GPlayer alive
		while True:
			time.sleep(10)



	

