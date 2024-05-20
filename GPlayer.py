import GToolBox

from NetworkManager import NetworkManager

class GPlayer:
	def __init__(self):
		self.toolBox = GToolBox.GToolBox(self)
		
	def __del__(self):
		self.toolBox.NetworkManager.thread_terminate = True
		self.toolBox.mav_conn.send("x x")		

	def listenLoop(self):
		print('server started...')
		run = True
		while run:
			if self.thread_terminate is True:
				break
			try:
				indata, addr = self.server.recvfrom(1024)
				
			except:
				continue

			print(f'[GP] => message from: {str(addr)}, data: {indata}')
			
			indata = indata
			header = indata[0]

			if header == GC.HEARTBEAT[0]:
				indata = indata[1:]
				#ip = f"{indata[3]}.{indata[2]}.{indata[1]}.{indata[0]}"
				ip = addr[0]
				self.BOAT_ID = indata[4]
				primary = indata[5:].decode()
				print("[HEARTBEAT]")
				print(f" -id:{self.BOAT_ID}, primary:{primary}")
				if primary == 'P':
					#self.P_CLIENT_IP = indata.split()[0]
					if self.P_CLIENT_IP != ip:
						self.P_CLIENT_IP = ip
						self.primaryNewConnection = True
					
				else:
					#self.S_CLIENT_IP = indata.split()[0]
					if self.S_CLIENT_IP != ip:
						print(f"S:{self.S_CLIENT_IP}, s:{ip}")
						self.S_CLIENT_IP = ip
						self.secondaryNewConnection = True
				

			elif header == GC.FORMAT[0]:
				indata = indata[1:].decode()
				print("[FORMAT]")
				msg = chr(self.BOAT_ID)+"\n".join(self.camera_format)
				msg = GC.FORMAT + msg.encode()

				self.client.sendto(msg,(self.P_CLIENT_IP,self.OUT_PORT))
				self.client.sendto(msg,(self.S_CLIENT_IP,self.OUT_PORT))

				
			elif header == GC.COMMAND[0]:
				indata = indata[1:].decode()
				print("[COMMAND]")
				print(indata)
				cformat = indata.split()[:5]




	

