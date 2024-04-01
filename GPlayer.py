import GToolBox

from NetworkManager import NetworkManager

class GPlayer:
	def __init__(self):
		self.toolBox = GToolBox.GToolBox(self)
		
	def __del__(self):
		self.toolBox.NetworkManager.thread_terminate = True
		self.toolBox.mav_conn.send("x x")		


	
	
	


	
		
	

	

	
	

	

