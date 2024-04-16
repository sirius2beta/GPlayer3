import time
import threading
import subprocess
import serial

from GTool import GTool
from Device import Device
from TestDevice import TestDevice

SENSOR = b'\x50'

class DeviceManager(GTool):	
	def __init__(self, toolBox):
		super().__init__(toolBox)
		self.sensor_group_list = toolBox.config.sensor_group_list # store all sensor_groups
		self.device_list = []  # 目前連在pi上的裝置
		self.Pixhawk_exist = False #會有出現兩個pixhawk的情形，確保指讀取一個

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
					print(f" - dev:: idProduct:{idProduct}, idVendor:{idVendor}, Path:{i}, ID:{j}")
					if device != None:
						self.device_list.append(device)
					break
		
				
		print(f"DM::Current device:")
		for i in self.device_list:
			#如果是ardupilot，交給mavmanager處理
			#if i.manufacturer == "ArduPilot":
			#	
			print(f" - dev:: devtype:{i.device_type}, , Path:{i.dev_path}")
			#i.connect()
			#break #Only the first FC connect
		

	def processCMD(self, devID, cmd):
		print(" --dev: processCMD")
		for d in self.device_list:
			print(f"  - received ID:{devID}, dev.ID:{d.ID}")
			if d.ID == dev.periID:
				if d.type == 2:
					pass
					#print("  -stepper cmd--")
					#d.write(f"s,{dev.type},0,{dev.pinIDList[0]} {dev.pinIDList[1]} {dev.settings[0]} {dev.settings[1]}")
					#d.write(f"c,{dev.type},{dev.pinIDList[0]},{dev.settings[2]}")
	def _deviceFactory(self, idVendor, idProduct, dev_path):
		# Pixhawk
		if idVendor == "1209" and idProduct == "5740": 
			if self.Pixhawk_exist == True:
				return None
			print("Devicefactory create ardupilot FC")
			device_type = 0
			dev = Device(device_type , dev_path, self.sensor_group_list, self._toolBox.networkManager)
			# Pixhawk device don't need to start loop
			dev.isOpened = True
			self._toolBox.mav_conn.send(f"g {dev_path}")
			self.Pixhawk_exist = True
			return None
		elif idVendor == "2341" and idProduct == "8037": 
			# 暫時性用arduino作為範例測試
			print("Devicefactory create Arduino")
			device_type = 1
			dev = TestDevice(device_type , dev_path, self.sensor_group_list, self._toolBox.networkManager)
			dev.start_loop()
			dev.isOpened = True
			return dev
		elif idVendor == "1d6b" and idProduct == "0002": 
			print("Devicefactory create ESP32BT")
			device_type = 2
			dev = Device(davice_type, dev_path, self.sensor_group_list, self._toolBox.networkManager)
			dev.start_loop()
			dev.isOpened = True
			return dev
		elif idVendor == "10c4" and idProduct == "ea60": 
			print("Devicefactory create Node MCU")
			device_type = 3
			dev = Device(device_type, dev_path, self.sensor_group_list, self._toolBox.networkManager)
			dev.start_loop()
			dev.isOpened = True
			return dev
		else:
			return None
	def __del__(self):
		pass
