import GToolBox
import time
from NetworkManager import NetworkManager

class GPlayer:
	def __init__(self):
		self.toolBox = GToolBox.GToolBox(self)
		self.mainLoop()	

	def mainLoop(self):
		print('GPlayer started...')
		run = True
		# keep main thread alive
		while run:
			time.sleep(10)



	

