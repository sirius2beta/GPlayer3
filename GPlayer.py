import GToolBox

from NetworkManager import NetworkManager

class GPlayer:
	def __init__(self):
		self.toolBox = GToolBox.GToolBox(self)
		
	def __del__(self):
		self.toolBox.NetworkManager.thread_terminate = True
		self.toolBox.mav_conn.send("x x")		


	
	
	


	
		
	

	
<<<<<<< HEAD
=======
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


				print(cformat)
				try:
					encoder, mid, quality, ip, port = indata.split()[5:]
				
				except:
					continue
				
				#print(quality, ip, port)
				ip = addr[0]
				if(' '.join(cformat) not in self.camera_format):
					print('format error')
				else:
					gstring = VF.getFormatCMD('buster', cformat[0], cformat[1], cformat[2].split('=')[1], cformat[3].split('=')[1],cformat[4].split('=')[1], encoder, ip, port)
					print(gstring)
					print(cformat[1])
					print(cformat[1][5:])
					videoindex = self.pipelinesexist.index(int(cformat[0][5:]))


					if self.pipelines_state[videoindex] == True:
						self.pipelines[videoindex].set_state(Gst.State.NULL)
						self.pipelines[videoindex] = Gst.parse_launch(gstring)
						self.pipelines[videoindex].set_state(Gst.State.PLAYING)

					else:
						self.pipelines[videoindex] = Gst.parse_launch(gstring)
						self.pipelines[videoindex].set_state(Gst.State.PLAYING)
						self.pipelines_state[videoindex] = True
			elif header == GC.SENSOR[0]:
				print("[SENSOR]")
				sensorList = [[1,'i']]
				indata = indata[1:].decode()
				action = indata[0]
				if action == 'd': # get device info
					self.toolBox.deviceManager.get_dev_info()

				if action == 'm': # device pin mapping and setting
					indata = indata[1:]
					print("Dev mapping:")
					deviceList = indata.split("\n")
					newDev = GC.Device()
					for i in deviceList:
						operation = indata[0]
						metaList = indata[1:].split(',')

						newDev.ID = int(metaList[0])
						newDev.periID = int(metaList[1])
						newDev.pinIDList = list(map(int,metaList[2].split()))
						newDev.type = int(metaList[3])
						newDev.settings = metaList[4].split()
						newDev.dataBuffer = ""
						print(f' -ID:{newDev.ID}')
						for j in newDev.pinIDList:
							print(f' -Device Pin:{j}')
						print(f' -type:{newDev.type}')
						print(f' -settings:{newDev.settings}')
						self.toolBox.deviceManager.addDevice(newDev)
				if action == 'c':
					indata = indata[1:]
					print("Dev command:")
					task = indata[0]
					dev = GC.Device()
					metaList = indata[1:].split(",")
					dev.ID = int(metaList[0])
					dev.periID = int(metaList[1])
					dev.pinIDList = list(map(int, metaList[2].split()))
					dev.type = int(metaList[3])
					dev.settings = metaList[4].split()
					self.toolBox.deviceManager.processCMD(dev)
			elif header == GC.QUIT[0]:
				print("[QUIT]")
				video = int(indata[6:].decode())
				if video in self.pipelinesexist:
					videoindex = self.pipelinesexist.index(video)
					self.pipelines[videoindex].set_state(Gst.State.NULL)
					self.pipelines_state[videoindex] = False
					print("  -quit : video"+str(video))

	@property
	def on_setDevice(self):
		return self._on_setDevice
	
	@on_setDevice.setter
	def on_setDevice(self, func):
		self._on_setDevice = func

>>>>>>> 8dfd625 (Update GPlayer.py)

	
	

	

