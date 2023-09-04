import time
import threading
import subprocess
import serial
import GClass as GC
import GClass

SENSOR = b'\x50'
class DeviceManager:
	
		
	def __init__(self):
		self.savedPeripherals = []
		self.currentPeriperals = []
		self.registeredPeriphrals = []
		self.devices = []

		self._on_message = None
		self._deviceList = [[1,'i']]
		self.thread_terminate = False
		self.thread_sensor = threading.Thread(target=self.sensorLoop)
		self.thread_sensor.start()
		
		# get all tty* device (ACM, USB..)
		cmd = "ls /dev/tty*"
		returncode = subprocess.check_output(cmd,shell=True).decode("utf-8")
		codelist = returncode.split()
		devlist = []
		for i in codelist:
			
			#if i.find("ttyS") != -1:
			#	devlist.append(i)
			#	print(i)
			if i.find("ttyACM") != -1:
				devlist.append(i)
			elif i.find("ttyUSB") != -1:
				devlist.append(i)
			elif i.find("ttyAMA") != -1:
				devlist.append(i)
		# find device detail
		idProduct = ''
		for i in devlist:
			cmd = f"udevadm info -a -p  $(udevadm info -q path -n {i})"
			returncode = subprocess.check_output(cmd,shell=True).decode("utf-8")
			dlist = returncode.split('\n')
			count = 0
			for j in dlist:
				word = j.split("==")
				#print(f"------: {word[0]}")
				if word[0].find("KERNELS") != -1: # not used
					kernals = word[1]
				elif word[0].find("idProduct") != -1:
					idProduct = word[1]
					count += 1
				elif word[0].find("idVendor") != -1:
					idVendor = word[1]
					count += 1
				elif word[0].find("manufacturer") != -1:
					manufacturer = word[1][1:-1] # only take first word for identification
					count += 1
				if count == 3:
					self.currentPeriperals.append(GC.Peripheral(idProduct, idVendor, manufacturer, i))
					break

		udev_file = open('/etc/udev/rules.d/79-sir.rules','r+')
		lines = udev_file.readlines()

		
		# generate registerd dev list
		id_exist = [] # specific number for PD that exist, e.g PD0, PD1, PD5...
		for line in lines:
			wa = line.split(', ')
			for wb in wa:
				wc = wb.split("=")
				if wc[0] == "KERNELS": # Not used
					kernals = wc[2]
				elif wc[0] == "ATTRS{idProduct}":
					idProduct = wc[2]
				elif wc[0] == "ATTRS{idVendor}":
					idVendor = wc[2]
				elif wc[0] == "SYMLINK+":
					SYMLINK = wc[1][1:-1]
					id = int(SYMLINK[2:])
					id_exist.append(id)
					self.savedPeripherals.append(GC.Peripheral(idProduct, idVendor, "", SYMLINK, id))
			
		print(f"DM::Registered device:")
		for i in self.savedPeripherals:
			print(f" -P:{i.idProduct}, V:{i.idVendor}, M:{i.ID}")
			i.connect()
	
		
		# compare exist and added device
		for i in self.currentPeriperals:
			add = True
			for j in self.savedPeripherals:
				if (i.idProduct  == j.idProduct) and (i.idVendor == j.idVendor):
					i.dev = "/dev/"+j.dev
					i.ID = j.ID
					add = False
			if add:	
				n = 0
				while True:
					if n in id_exist:
						n+=1
					else:
						id_exist.append(n)
						break
				udev_file.write(f"SUBSYSTEM==\"tty\", ATTRS{{idProduct}}=={i[0]}, ATTRS{{idVendor}}=={i[1]}, SYMLINK+=\"PD{n}\", MODE=\"0777\"\n")
				i.ID = n
			
		udev_file.close()
		print(f"DM::Current device:")
		for i in self.currentPeriperals:
			print(f" -P:{i.idProduct}, V:{i.idVendor}, M:{i.manufacturer}, D:{i.dev}, ID:{i.ID}")
			i.connect()
		
		
		
		
	def __del__(self):
		self.thread_terminate = True
		self.thread_sensor.join()
	def on_dev_info(self):
		sensorMsg = b""
		sensorMsg += bytes('r', 'ascii')
		Msg=""
		for i in self.currentPeriperals:
			",".join(map(str,i.getList()))
			Msg+= ",".join(map(str,i.getList()))+"\n"
		sensorMsg += bytes(Msg, 'ascii')
		#print(sensorMsg)

		if self._on_message != None:
			try:
				on_message = self.on_message
				on_message(SENSOR, sensorMsg)
			except:
				print(f"Sensor failed")	
	def sensorLoop(self):
		value = 0

		
		
		while self.thread_terminate == False:
			content = b''
			count = 0
			for cp in self.currentPeriperals:
				if cp.IO != None:
					indata = cp.read()
					content+=indata
					count+=1
			if content != b'':	
				if self._on_message != None:
					try:
						on_message = self.on_message
						on_message(SENSOR, content)
						time.sleep(1)
					except:
						print(f"Sensor failed")			
			
			
			
			#value += 1;
			#sensorMsg = SENSOR
			#sensorMsg += bytes(num_sensor, 'ascii')
			#sensorMsg += bytes('i', 'ascii')
			#sensorMsg+=bytes(chr(1),'ascii')
			#sensorMsg+=bytes(chr(1),'ascii')
			#sensorMsg+=value.to_bytes(4, 'big')
			#sensorMsg += bytes('i', 'ascii')
			#sensorMsg+=bytes(chr(1),'ascii')
			#sensorMsg+=bytes(chr(0),'ascii')
			#sensorMsg+=int(value/2).to_bytes(4, 'big')
			
			
			if self.thread_terminate is True:
				break
			
	
	def setDevice(self, slist):
		self._deviceList = slist
		#for sensor in self._deviceList:
		#	print(f'setDevice: sensor:{sensor[0]}, {sensor[1]}')

	def addDevice(self, device):
		# register device
		self.devices.append(device)
	@property
	def sensorList(self):
		return self.sensorList
	@sensorList.setter
	def sensorList(self, slist):
		self._deviceList = slist
	@property
	def on_message(self):
		return self._on_message
	@on_message.setter
	def on_message(self, func):
		self._on_message = func
