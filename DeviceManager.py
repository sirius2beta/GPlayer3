import time
import threading
import subprocess
import serial

from GTool import GTool

from Dev.Device import Device
from Dev.TestDevice import TestDevice
from Dev.AquaDevice import AquaDevice
from Dev.RS485Device import RS485Device
from Dev.WinchDevice import WinchDevice
from Dev.ArduSimpleDevice import ArduSimpleDevice
from Dev.SonarDevice import SonarDevice

SENSOR = b'\x50'

class DeviceManager(GTool):	
	def __init__(self, toolBox):
		super().__init__(toolBox)
		self.aqua_device = None 		# aqua_device object
		self.ardusimple_device = None 	# ardusimple_device object
		self.winch_device = None
		self.sensor_group_list = toolBox.config.sensor_group_list # store all sensor_groups
		self.device_list = []  		# 目前連在pi上的裝置
		self.Pixhawk_exist = False 	# 會有出現兩個pixhawk的情形，確保指讀取一個
		self.ardusimple_exist = False # ArduSimple有兩Port，確保只讀取一個
		self.SITL_connect = False 	# 如果要測試SITL，此值為True
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
				if word[0].find("KERNELS") != -1: # not used
					kernals = word[1]
					count = 0
				elif word[0].find("idProduct") != -1:
					idProduct = word[1][1:-1]
					count += 1
				elif word[0].find("idVendor") != -1:
					idVendor = word[1][1:-1]
					count += 1
				elif word[0].find("manufacturer") != -1:
					manufacturer = word[1][1:-1] # only take first word for identification
					count += 1
				if count == 3:
					device = self._deviceFactory(idVendor, idProduct, i)
					#print(f" - dev:: idProduct:{idProduct}, idVendor:{idVendor}, Path:{i}, ID:{j}")
					if device != None:
						self.device_list.append(device)
					break

		if self.SITL_connect == True:
			self._toolBox.mavManager.connectVehicle("udp:127.0.0.1:14550")
			print("Running SITL..")	
				
		print(f"[o] DeviceManager: started, current device:")
		if len(self.device_list) == 0:
			print("      - no device found")
		for i in self.device_list:
			print(f"     - devtype:{i.device_type}, path:{i.dev_path}")
		# 不是從USB中創建的 device
		sonarDevice = SonarDevice(self.toolBox())
		self.device_list.append(sonarDevice)
	
	def processControl(self, control_type, cmd):
		print(f"control type: {control_type}")
		for d in self.device_list:
			d.processCMD(control_type, cmd)


	def processCMD(self, devID, cmd):
		print(" --dev: processCMD")
		for d in self.device_list:
			print(f"  - received ID:{devID}, dev.ID:{d.ID}")
			if d.ID == dev.periID:
				if d.type == 2:
					print("  -stepper cmd--")
					#d.write(f"s,{dev.type},0,{dev.pinIDList[0]} {dev.pinIDList[1]} {dev.settings[0]} {dev.settings[1]}")
					#d.write(f"c,{dev.type},{dev.pinIDList[0]},{dev.settings[2]}")

	def _deviceFactory(self, idVendor, idProduct, dev_path):
		# Pixhawk
		if(idVendor == "1209" and idProduct == "5740"): 
			if self.SITL_connect == True:
				return None
			if self.Pixhawk_exist == True:
				return None
			print("      ...Devicefactory create ardupilot FC")
			device_type = 0
			dev = Device(device_type , dev_path, self.sensor_group_list, self._toolBox.networkManager)
			# Pixhawk device don't need to start loop
			dev.isOpened = True
			
			self._toolBox.mavManager.connectVehicle(f"{dev_path}")
			self.Pixhawk_exist = True
			return dev
		elif(idVendor == "1d6b" and idProduct == "0002"): # Winch device
			print("      ...Devicefactory create Winch Device")
			device_type = 2
			dev = WinchDevice(device_type , dev_path, self.sensor_group_list, self._toolBox.networkManager)
			self.winch_device = dev
			dev.isOpened = True
			dev.start_loop()
			return dev
		elif(idVendor == "0403" and idProduct == "6001"): # Aqua 
			print("      ...Devicefactory create Aqua Device")
			device_type = 7
			dev = AquaDevice(device_type , dev_path, self.sensor_group_list, self._toolBox.networkManager)
			self.aqua_device = dev
			dev.start_loop()
			dev.isOpened = True
			return dev
		elif(idVendor == "10c4" and idProduct == "ea60"): # Node MCU
			print("      ...Devicefactory create Node MCU")
			device_type = 3
			dev = Device(device_type, dev_path, self.sensor_group_list, self._toolBox.networkManager)
			dev.start_loop()
			dev.isOpened = True
			return dev
		elif(idVendor == "067b" and idProduct == "2303"): # RS485Module
			print("      ...Devicefactory create RS485Module")
			device_type = 4
			dev = RS485Device(device_type, dev_path, self.sensor_group_list, self._toolBox.networkManager)
			dev.start_loop()
			dev.isOpened = True
			return dev
		elif(idVendor == "2341" and idProduct == "8037"): # 保留arduino做為測試用
			print("      ...Devicefactory create Arduino")
			device_type = 5
			dev = WinchDevice(device_type , dev_path, self.sensor_group_list, self._toolBox.networkManager)
			dev.isOpened = True
			dev.start_loop()
			return dev

		elif(idVendor == "152a" and idProduct == "85c0"): # ArduSimple
			if(self.ardusimple_exist): # ardusimple 存在，就不再呼叫
				return None
			print("      ...Devicefactory create ArduSimple")
			device_type = 6
			dev = ArduSimpleDevice(device_type, dev_path, self.sensor_group_list, self._toolBox.networkManager)
			self.ardusimple_device = dev
			dev.start_loop()
			dev.isOpened = True
			self.ardusimple_exist = True # 設定 ardusimple 存在
			return dev
				
		else:
			return None
		
	def __del__(self):
		pass
