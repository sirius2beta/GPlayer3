import glob
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor

from GTool import GTool
from Dev.Device import Device
from Dev.TestDevice import TestDevice
from Dev.AquaDevice import AquaDevice
from Dev.RS485Device import RS485Device
from Dev.WinchDevice import WinchDevice
from Dev.ArduSimpleDevice import ArduSimpleDevice
from Dev.SonarDevice import SonarDevice
from Dev.SuperTaiRaDevice import SuperTaiRaDevice


DEVICE_TYPES = {
	("1209", "5740"): ("Pixhawk", Device, 0, False),
	("1d6b", "0002"): ("Winch", WinchDevice, 2, True),
	("0bda", "5489"): ("Winch", WinchDevice, 2, True),
	("1a86", "7523"): ("RS485Device", RS485Device, 2, True),
	("0403", "6001"): ("Aqua", AquaDevice, 7, True),
	("10c4", "ea60"): ("NodeMCU", Device, 3, True),
	("067b", "2303"): ("RS485", RS485Device, 4, True),
	("2341", "8037"): ("Arduino", WinchDevice, 5, True),
	("152a", "85c0"): ("ArduSimple", ArduSimpleDevice, 6, True),
	('067b', '2303'): ('SuperTaiRa', SuperTaiRaDevice, 8, False),  # Example test device
	('067b', '23a3'): ('SuperTaiRa', SuperTaiRaDevice, 8, False),  # Example test device
}


class DeviceManager(GTool):
	def __init__(self, toolBox):
		super().__init__(toolBox)
		self.aqua_device = None
		self.ardusimple_device = None
		self.winch_device = None
		self.super_taira_device = None
		self.sensor_group_list = toolBox.config.sensor_group_list
		self.device_list = []
		self.Pixhawk_exist = False
		self.ardusimple_exist = False
		self.SITL_connect = False
		self.device_status = [
			0,  # 0: Flight control
			0,  # 1: GPS
			0,  # 2: Winch
			0,  # 3: Aqua
		]

		# 掃描 USB 裝置
		devlist = self._scan_devices()

		# 平行檢查 USB 裝置並建立物件
		with ThreadPoolExecutor() as executor:
			for device in executor.map(self._inspect_device, devlist):
				if device:
					self.device_list.append(device)

		# 建立 GPIO 類裝置（例：Sonar）
		for device in self._createGPIODevice():
			self.device_list.append(device)
		
	def _createGPIODevice(self):
		"""建立 GPIO 相關的裝置，例如 SonarDevice"""
		devices = []
		try:
			sonar_device = SonarDevice(self._toolBox)
			devices.append(sonar_device)
		except Exception as e:
			logging.error(f"建立 SonarDevice 失敗: {e}")
		return devices

	def _scan_devices(self):
		"""取得所有可能的 serial device 路徑"""
		patterns = ["/dev/ttyACM*", "/dev/ttyUSB*", "/dev/ttyAMA*", "/dev/video*"]
		devlist = []
		for pattern in patterns:
			devlist.extend(glob.glob(pattern))
		return devlist

	def _inspect_device(self, dev_path):
		"""用 udevadm 查詢裝置資訊並建立對應的 Device 物件"""
		try:
			udev_path = subprocess.check_output(
				["udevadm", "info", "-q", "path", "-n", dev_path]
			).decode().strip()

			output = subprocess.check_output(
				["udevadm", "info", "-a", "-p", udev_path]
			).decode()

			idVendor = idProduct = manufacturer = None
			for line in output.splitlines():
				line = line.strip()
				if line.startswith("looking at"):
					idVendor = idProduct = manufacturer = None
					continue

				if "ATTRS{idVendor}" in line:
					idVendor = line.split("==")[1].strip().strip('"')
				elif "ATTRS{idProduct}" in line:
					idProduct = line.split("==")[1].strip().strip('"')
				elif "ATTRS{manufacturer}" in line or "ATTRS{product}" in line:
					manufacturer = line.split("==")[1].strip().strip('"')

				if idVendor and idProduct:
					if (idVendor, idProduct) in DEVICE_TYPES:
						device = self._deviceFactory(idVendor, idProduct, dev_path)
						logging.info(
							f"Device found: {manufacturer}, Vendor={idVendor}, Product={idProduct}, Path={dev_path}"
						)
						return device
					else:
						logging.info(
							f"Skip non-supported device: {manufacturer}, Vendor={idVendor}, Product={idProduct}, Path={dev_path}"
						)
					break

		except subprocess.CalledProcessError as e:
			logging.error(f"udevadm failed for {dev_path}: {e}")
		except Exception as e:
			logging.exception(f"Unexpected error for {dev_path}: {e}")
		return None

	def _deviceFactory(self, idVendor, idProduct, dev_path):
		"""建立對應的 Device 物件"""
		name, cls, dev_type, start_loop = DEVICE_TYPES[(idVendor, idProduct)]

		# 特殊條件
		if name == "Pixhawk":
			if self.SITL_connect or self.Pixhawk_exist:
				return None
		elif name == "ArduSimple" and self.ardusimple_exist:
			return None

		logging.info(f"Creating {name} device on {dev_path}")
		dev = cls(dev_type, dev_path, self.sensor_group_list, self._toolBox.networkManager)

		if start_loop:
			dev.start_loop()
		dev.isOpened = True

		if name == "Pixhawk":
			self._toolBox.mavManager.connectVehicle(dev_path)
			self.device_status[0] = 1  # Flight control connected
			self.Pixhawk_exist = True
		elif name == "ArduSimple":
			self.ardusimple_device = dev
			self.device_status[1] = 1  # GPS connected
			#self.ardusimple_exist = True
		elif name == "Aqua":
			self.aqua_device = dev
			self.device_status[3] = 1  # Aqua connected
		elif name == "RS485Device":
			self.winch_device = dev
			self.aqua_device = dev  # RS485Device 也負責 Aqua 功能
			self.device_status[2] = 1  # Winch connected
		elif name == "SuperTaiRa":
			self.super_taira_device = dev
			# Add any specific initialization for SuperTaiRa if needed
		return dev

	def processControl(self, control_type, cmd):
		logging.info(f"Control type: {control_type}")
		for d in self.device_list:
			d.processCMD(control_type, cmd)

	def processCMD(self, devID, cmd):
		logging.info(f"Processing command for device ID {devID}")
		for d in self.device_list:
			logging.debug(f"  Checking device {d.ID}")
			if d.ID == devID:  # 修正原本 dev 未定義的問題
				if d.type == 2:
					logging.info(f"Sending stepper command to {d.ID}")
					# TODO: 實際寫入的命令依需求加上

	def __del__(self):
		logging.info("Cleaning up DeviceManager...")
		for d in self.device_list:
			try:
				if hasattr(d, "stop_loop"):
					d.stop_loop()
			except Exception as e:
				logging.error(f"Error stopping device {d}: {e}")
	def checkDeviceStatus(self):
		if self.aqua_device:
			self.device_status[3] = self.aqua_device.status_code
		return self.device_status