import GToolBox
import time
from NetworkManager import NetworkManager

class GPlayer:
	def __init__(self):
		self.toolBox = GToolBox.GToolBox(self)
		self.mainLoop()	

	def mainLoop(self):
		print('GPlayer started...')
		# keep main GPlayer alive
		while True:
			time.sleep(10)



	

