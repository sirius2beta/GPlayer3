import gi
import os
import subprocess
import time
import threading
import socket
import struct
import GClass as GC
import VideoFormat as VF
import DeviceManager as DM
import GToolBox
import MavManager

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib, GObject




class GPlayer:
	def __init__(self):
		self.toolBox = GToolBox.GToolBox()
		self.BOAT_ID = 0
		self.GROUND_NAME = 'ground1'

		self.PC_IP='10.10.10.205'
		self.SERVER_IP = ''
		self.P_CLIENT_IP = '127.0.0.1' #PC IP
		self.S_CLIENT_IP = '127.0.0.1'
		self.OUT_PORT = 50008
		self.IN_PORT = 50006 
		self.primaryNewConnection = False
		self.secondaryNewConnection = False

		self.pipelinesexist = []
		self.pipelines = []
		self.pipelines_state = []
		self.camera_format = []
		self.get_video_format()
		
		self._on_setDevice = None
		
		self.toolBox.deviceManager.on_message = self.sendMsg

		GObject.threads_init()
		Gst.init(None)

		self.createPipelines()

		self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.server.bind((self.SERVER_IP, self.IN_PORT))
		self.server.setblocking(0)
		
		self.thread_terminate = False
		self.lock = threading.Lock()

		

		
	def __del__(self):
		print("------------------------del")
		self.toolBox.mav_conn.send("x x")
		self.thread_terminate = True
		self.thread_cli.join()
		self.thread_ser.join()
		
		self.toolBox.mavManager.join()

	def startLoop(self):
		self.thread_cli = threading.Thread(target=self.aliveLoop)
		self.thread_ser = threading.Thread(target=self.listenLoop)
		self.thread_cli.start()
		self.thread_ser.start()

	def test(self, msg):
		print(f"called outside: {msg}")

	def sendMsg(self, topic, msg):
		# Send message from outside
		msg = topic + bytes(chr(self.BOAT_ID),'ascii') + msg
		print(f"sendMsg:\n -topic:{msg[0]}\n -msg: {msg}")
		try:
			self.client.sendto(msg,(self.P_CLIENT_IP,self.OUT_PORT))

		except:
			print(f"Primary unreached: {self.P_CLIENT_IP}:{self.OUT_PORT}")
		# Send secondary heartbeat every 0.5s
		try:
			self.client.sendto(msg,(self.S_CLIENT_IP, self.OUT_PORT))
		except:
			print(f"Secondary unreached: {self.S_CLIENT_IP}:{self.OUT_PORT}")
	
	def aliveLoop(self):
		print('client started...')
		run = True
		checkAlive = False
		while run:
			if self.thread_terminate is True:
				break

			beat = b'\x10'+chr(self.BOAT_ID).encode()
			# Send primary heartbeat every 0.5s
			try:
				
				if self.primaryNewConnection:
					print(f"\n=== New connection ===\n -Primary send to: {self.P_CLIENT_IP}:{self.OUT_PORT}\n", flush=True)
					self.toolBox.mav_conn.send(f"p {self.P_CLIENT_IP}")
					
					self.primaryNewConnection = False
				self.client.sendto(beat,(self.P_CLIENT_IP,self.OUT_PORT))
				time.sleep(0.5)
			except:
				if self.primaryNewConnection:
					print(f"\n=== Bad connection ===\n -Primary unreached: {self.P_CLIENT_IP}:{self.OUT_PORT}\n")
					self.primaryNewConnection = False
			# Send secondary heartbeat every 0.5s
			try:
				self.client.sendto(beat,(self.S_CLIENT_IP, self.OUT_PORT))
				time.sleep(0.5)
				if self.secondaryNewConnection:
					print(f"\n=== New connection ===\n -Secondarysend to: {self.S_CLIENT_IP}:{self.OUT_PORT}\n")
					self.toolBox.mav_conn.send(f"s {self.S_CLIENT_IP}")
					self.secondaryNewConnection = False
			except:
				if self.secondaryNewConnection:
					print(f"\n=== Bad connection ===\n -Secondary unreached: {self.S_CLIENT_IP}:{self.OUT_PORT}\n")
					self.secondaryNewConnection = False

	def createPipelines(self):
		for i in self.camera_format:
			j = int(i.split()[0][5]);
			if(j not in self.pipelinesexist):
				pipeline = Gst.Pipeline()
				self.pipelines.append(pipeline)
				self.pipelinesexist.append(j)
		for i in self.pipelines:
			self.pipelines_state.append(False)
		print(self.pipelinesexist)
	

#get video format from existing camera devices
	def get_video_format(self):
		try:
			cmd = " grep '^VERSION_CODENAME=' /etc/os-release"
			returned_value = subprocess.check_output(cmd,shell=True).replace(b'\t',b'').decode("utf-8") 
		except:
			returned_value = '0'
		sys = returned_value.split('=')[1]
		if sys == 'buster':
			print('system: buster')
		else:
			print(f'system: {sys}')
		#Check camera device
		for i in range(0,10):
				try:
					cmd = "v4l2-ctl -d /dev/video{} --list-formats-ext".format(i)
					returned_value = subprocess.check_output(cmd,shell=True).replace(b'\t',b'').decode("utf-8")  # returns the exit code in unix
				except:
					continue
				line_list = returned_value.splitlines()
				new_line_list = list()
				for j in line_list:
					if len(j.split()) == 0:
						continue
					elif j.split()[0][0] =='[':
						form = j.split()[1][1:-1]
					elif j.split()[0] =='Size:':
						size = j.split()[2]
						width, height = size.split('x')
					elif j.split()[0] == 'Interval:':
						self.camera_format.append('video{} {} width={} height={} framerate={}'.format(i,form, width, height , j.split()[3][1:].split('.')[0]))
						print('video{} {} width={} height={} framerate={}'.format(i,form, width, height , j.split()[3][1:].split('.')[0]))
	
	def get_video_format_for_diffNx(self):	
		#Check camera device
		for i in range(0,10):
				try:
					cmd = "v4l2-ctl -d /dev/video{} --list-formats-ext".format(i)
					returned_value = subprocess.check_output(cmd,shell=True).replace(b'\t',b'').decode("utf-8")  # returns the exit code in unix
				except:
					continue
				line_list = returned_value.splitlines()
				new_line_list = list()
				for j in line_list:
					if len(j.split()) == 0:
						continue
					elif j.split()[0] =='Pixel':
						form = j.split()[2][1:-1]
					elif j.split()[0] =='Size:':
						size = j.split()[2]
						width, height = size.split('x')
					elif j.split()[0] == 'Interval:':
						self.camera_format.append('video{} {} width={} height={} framerate={}'.format(i,form, width, height , j.split()[3][1:].split('.')[0]))
						print('video{} {} width={} height={} framerate={}'.format(i,form, width, height , j.split()[3][1:].split('.')[0]))
	

	
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
				self.BOAT_ID = indata[0]
				primary = indata[1:].decode()
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
					encoder, mid, quality, port = indata.split()[5:]
				
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


	
	#def on_msg_callback(self):
	#	def decorator(func):
	#		self._on_setDevice = func
	#		return func
	#	return decorator
			

# The callback for when a PUBLISH message is received from the server.
