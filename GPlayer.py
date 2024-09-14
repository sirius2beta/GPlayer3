import GToolBox
import time
from NetworkManager import NetworkManager

class GPlayer:
	def __init__(self):
		version = 2.0
		print(f"GPlayer version {version}")
		self.toolBox = GToolBox.GToolBox(self) # initiate all modules
		self.toolBox.startLoops()
		print("GPlayer initialized!")
		input("Press anykey to exit")
		#self.mainLoop()	# keep main thread alive
		

	def mainLoop(self):
		# keep main GPlayer alive
		while True:
			time.sleep(10)



	

