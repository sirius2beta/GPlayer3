import GToolBox
import time
from NetworkManager import NetworkManager

class GPlayer:
	def __init__(self):
		self.toolBox = GToolBox.GToolBox(self) # GToolBox包含所有的模組，包含不同的thread
		self.mainLoop()	#為了不讓主程式結束，在主程式run loop

	def mainLoop(self):
		# keep main thread alive
		while True:
			time.sleep(10)



	

