import time
import threading
import subprocess
import serial

from GTool import GTool
from Device import Device

SENSOR = b'\x50'

class DeviceManager(GTool):	
	def __init__(self, toolBox):
		super().__init__(toolBox)
		self.deviceList = []  # 目前連在pi上的裝置
		self.devices = []
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
					device = self.deviceFactory(idVendor, idProduct, i)
					if device != None:
						self.deviceList.append(device)
					break
				
		print(f"DM::Current device:")
		for i in self.deviceList:
			#如果是ardupilot，交給mavmanager處理
			#if i.manufacturer == "ArduPilot":
			#	
			print(f" - dev:: idProduct:{i.idProduct}, idVendor:{i.idVendor}, Path:{i.devPath}, ID:{i.ID}")
			#i.connect()
			#break #Only the first FC connect
	

	def processCMD(self, devID, cmd):
		print(" --dev: processCMD")
		for d in self.deviceList:
			print(f"  - received ID:{devID}, dev.ID:{d.ID}")
			if d.ID == dev.periID:
				if d.type == 2:
					pass
					#print("  -stepper cmd--")
					#d.write(f"s,{dev.type},0,{dev.pinIDList[0]} {dev.pinIDList[1]} {dev.settings[0]} {dev.settings[1]}")
					#d.write(f"c,{dev.type},{dev.pinIDList[0]},{dev.settings[2]}")
	def deviceFactory(self, idVendor, idProduct, devPath):
		# Pixhawk
		if idVendor == "1209" and idProduct == "5740": 
			if self.Pixhawk_exist == True:
				return None
			print("ardupilot FC")
			self._toolBox.mav_conn.send(f"g {devPath}")
			dev = Device(idVendor, idProduct, devPath)
			dev.isOpened = True
			dev.ID = 0
			self.Pixhawk_exist = True
			return dev
		elif idVendor == "1d6b" and idProduct == "0002": 
			print("Arduino/ESP32BT")
			dev = Device(idVendor, idProduct, devPath)
			dev.isOpened = True
			dev.ID = 1
			return dev
		elif idVendor == "10c4" and idProduct == "ea60": 
			print("Node MCU")
			dev = Device(idVendor, idProduct, devPath)
			dev.isOpened = True
			dev.ID = 1
			return dev
		else:
			return None
	def __del__(self):
		pass

	