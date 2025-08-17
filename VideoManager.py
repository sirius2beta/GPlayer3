import gi
import glob
import logging
import subprocess
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib, GObject

import GToolBox
from GTool import GTool
import VideoFormat


class VideoManager(GTool):
	def __init__(self, toolbox):
		super().__init__(toolbox)
		self.sys = 'buster'


		# pipeline 管理：key=cam index, value=dict
		self.pipelines = {}  # { cam: {"pipeline": Gst.Pipeline, "state": bool, "port": int, "encoder": str} }
		self.camera_format = []
		self.videoFormatList = {}
		self.videoWithYUYV = []
		self.ai_cam = -1
		self.seagrass_cam = -1
		self.seagrass_cam_format = None
		self.portOccupied = {}  # {port: cam}
		

		self.get_video_format_generic()

		self.portOccupied = {} # {port, videoNo}

		GObject.threads_init()
		Gst.init(None)

		print("[o] VideoManager: started")

	def getFormatInfoByIndex(self, formatIndex):
		formatMap = {
			0: (1920, 1080, 30),
			1: (1280, 720, 30),
			2: (640, 480, 30),
			3: (320, 240, 30),
		}
		return formatMap.get(formatIndex, None)  # 找不到回 None
	
	def getFormatInfoByIndexMap(self):
		return {
			0: (1920, 1080, 30),
			1: (1280, 720, 30),
			2: (640, 480, 30),
			3: (320, 240, 30),
		}

	#get video format from existing camera devices
	def get_video_format_generic(self):
		"""掃描 /dev/video*，只保留 MJPEG>YUYV，h264 不加入"""
		devices = sorted(glob.glob("/dev/video*"))
		if not devices:
			print("[x] no video devices found")
			return

		for dev in devices:
			try:
				cam = int(dev.replace("/dev/video", ""))
			except ValueError:
				continue

			self.pipelines[cam] = {"pipeline": None, "state": False, "formats": []}

			try:
				output = subprocess.check_output(
					["v4l2-ctl", "-d", dev, "--list-formats-ext"],
					stderr=subprocess.DEVNULL,
					text=True
				)
			except subprocess.CalledProcessError:
				print(f"[!] failed to read formats from {dev}")
				continue

			fmt = None
			all_formats = []
			for line in output.splitlines():
				line = line.strip()
				if line.startswith("[") and "]" in line:
					parts = line.split("'")
					fmt = parts[1] if len(parts) > 1 else None
				elif fmt and "Size:" in line:
					toks = line.replace("Size: Discrete", "").strip().split("x")
					if len(toks) == 2:
						w, h = map(int, toks)
						fps = 30
						key = (w, h, fps)
						all_formats.append((fmt, w, h, fps	))
			logging.info(f"video{cam} formats: {all_formats}")
			self.pipelines[cam]["formats"] = all_formats
	def get_videoFormatList_legacy(self):
		"""
		產生舊版 videoFormatList 結構：
		{
			formatIndex: [ [videoNo, fmt], ...]
		}
		"""
		legacyList = {}
		for cam, info in self.pipelines.items():
			for fmt, w, h, fps in info["formats"]:
				if fmt == "H264":
					continue
				# 找到對應 formatIndex
				formatIndex = None
				for idx, res in self.getFormatInfoByIndexMap().items():
					if (w, h, fps) == res:
						formatIndex = idx
						break
				if formatIndex is None:
					continue
				if formatIndex not in legacyList:
					legacyList[formatIndex] = []
				# 若已存在同相機且 MJPEG 優先
				add = True
				for i, (vno, enc) in enumerate(legacyList[formatIndex]):
					if vno == cam:
						# MJPEG 替換 YUYV
						if fmt == "MJPEG" and enc == "YUYV":
							legacyList[formatIndex][i][1] = "MJPEG"
						add = False
						break
						
				if add:
					legacyList[formatIndex].append([cam, fmt])
		return legacyList
	def getYUYVFrameRate(self, cam, width=None, height=None):
		"""
		從系統抓出 cam 支援的 YUYV 格式最高 fps。
		如果 width/height 提供，就限定解析度。
		"""
		import re, subprocess
		dev = f"/dev/video{cam}"
		try:
			output = subprocess.check_output(
				["v4l2-ctl", "-d", dev, "--list-formats-ext"],
				stderr=subprocess.DEVNULL,
				text=True
			)
		except subprocess.CalledProcessError:
			return ""

		fmt = None
		match_res = False
		fps_list = []

		for line in output.splitlines():
			line = line.strip()

			# --- 找格式 ---
			if line.startswith("[") and "]" in line:
				# e.g. [0]: 'YUYV' (YUYV 4:2:2)
				parts = line.split("'")
				fmt = parts[1] if len(parts) > 1 else None
				continue

			# --- 找尺寸 ---
			if fmt == "YUYV" and line.startswith("Size: Discrete"):
				# e.g. Size: Discrete 1280x720
				toks = line.replace("Size: Discrete", "").strip().split("x")
				if len(toks) == 2:
					w, h = map(int, toks)
					if (width is None or w == width) and (height is None or h == height):
						match_res = True
					else:
						match_res = False
				continue

			# --- 找 fps ---
			if match_res and line.startswith("Interval: Discrete"):
				# e.g. Interval: Discrete 0.033s (30.000 fps)
				m = re.search(r"\(([\d\.]+)\s*fps\)", line)
				if m:
					fps_list.append(float(m.group(1)))

		if fps_list:
			return int(max(fps_list))  # 回傳最高 fps
		return ""


	# ---------------- Pipeline 管理 ---------------- #
	def _create_pipeline(self, cam, gstring, port, encoder):
		"""建立新的 pipeline，若已存在則先釋放"""
		if cam in self.pipelines:
			self._stop_pipeline(cam)

		pipeline = Gst.parse_launch(gstring)
		self.pipelines[cam]['pipeline'] = pipeline
		self.pipelines[cam]['state'] = False
		self.pipelines[cam]['port'] = port
		self.pipelines[cam]['encoder'] = encoder
		
		return pipeline

	def _start_pipeline(self, cam):
		"""啟動 pipeline"""
		if cam not in self.pipelines:
			return False
		pipeline = self.pipelines[cam]["pipeline"]
		pipeline.set_state(Gst.State.PLAYING)
		self.pipelines[cam]["state"] = True
		return True

	def _stop_pipeline(self, cam):
		"""停止並釋放 pipeline，但保留 camera 格式資訊"""
		if cam not in self.pipelines:
			return

		pipeline = self.pipelines[cam].get("pipeline")
		if pipeline:
			pipeline.set_state(Gst.State.NULL)
			pipeline.get_state(Gst.CLOCK_TIME_NONE)  # 等待切換完成
			self.pipelines[cam]["pipeline"] = None  # 清掉 pipeline，但保留格式

		# 更新 pipeline 狀態
		self.pipelines[cam]["state"] = False

		# 釋放 portOccupied
		ports_to_remove = [p for p, c in self.portOccupied.items() if c == cam]
		for p in ports_to_remove:
			self.portOccupied.pop(p, None)

		# 若是 AI 或 Seagrass camera，也重置對應標誌
		if cam == self.ai_cam:
			self.ai_cam = -1
		if cam == self.seagrass_cam:
			self.seagrass_cam = -1
			self.seagrass_cam_format = None

		logging.info(f"_stop_pipeline: video{cam} stopped and cleaned")



	# ---------------- 播放控制 ---------------- #
	def play(self, cam, width, height, fps, encoder, IP, port, YOLO_detection_enabled):
		"""
		新版 play()，完全用 self.pipelines 管理 pipeline
		"""
		if cam not in self.pipelines:
			print(f"video{cam} not found")
			return

		# 找對應格式
		fmtFound = None
		for fmt, w, h, f in self.pipelines[cam]["formats"]:
			if w == width and h == height and f == fps:
				fmtFound = fmt
				break
		if fmtFound is None:
			print(f"video{cam} has no format {width}x{height}@{fps}")
			return

		# 生成 GStreamer 指令
		gstring = VideoFormat.getFormatCMD(self._toolBox.OS, cam, fmtFound, width, height, fps, encoder, IP, port)
		print(f"[Pipeline] cam={cam}, port={port}, encoder={encoder}")
		print(gstring)

		# 釋放被占用的 port
		if port in self.portOccupied:
			videoToStop = self.portOccupied[port]
			self._stop_pipeline(videoToStop)
			print(f"  -quit occupied: video{videoToStop}")

		# AI / seagrass 特例
		if cam == self.seagrass_cam:
			if self._toolBox.seagrassDetect is None:
				print("seagrassDetect not ready")
				return
			self._toolBox.seagrassDetect.play()
			print(f"start seagrass camera on cam:{cam}")
			self.portOccupied[port] = cam
			return

		if YOLO_detection_enabled == 1:
			if self._toolBox.jetsonDetect is None:
				print("JetsonDetect not ready")
				return
			if cam != self.ai_cam:		
				YUYVfps = self.getYUYVFrameRate(cam, width, height)
				if YUYVfps != "":
					self._toolBox.jetsonDetect.play([cam, "YUYV", width, height, YUYVfps, IP, port])
					print(f"start ai on cam:{cam}")
					self.ai_cam = cam
					self.portOccupied[port] = cam
					return
				else:
					print(f"video{cam} had no YUYV format")
					return
			else:
				print(f"restart ai on cam:{cam}")
				return

		# 一般播放
		pipeline = self._create_pipeline(cam, gstring, port, encoder)
		self._start_pipeline(cam)
		self.portOccupied[port] = cam


	def stop(self, cam):
		if cam == self.seagrass_cam:
			self._toolBox.seagrassDetect.stop()
			self.seagrass_cam = -1
			self.seagrass_cam_format = None
			print(f"stop seagrass on cam:{cam}")
			return

		if cam == self.ai_cam:
			self._toolBox.jetsonDetect.stop()
			self.ai_cam = -1
			print(f"stop ai on cam:{cam}")
			return

		# 停止 pipeline
		self._stop_pipeline(cam)
		print(f"stop pipeline on cam:{cam}")
	def setSeagrassCamera(self, cam, format, width, height, framerate, encoder, IP, port):
		print(f"set seagrass camera: {cam} {format} {width} {height} {framerate} {encoder} {IP} {port}")
		YUYVfps = self.getYUYVFrameRate(cam, width, height)
		if YUYVfps != "":
			logging.info(f"YUYV fps for video{cam}: {YUYVfps}")
			self.seagrass_cam_format = [cam, "YUYV", width, height, YUYVfps, IP, port]
			print(f"start ai on cam:{cam}")
			self.seagrass_cam = cam
			self._toolBox.seagrassDetect.setFormat(self.seagrass_cam_format)
		else:
			print(f"video{cam} had no YUYV format")
	def startSeagrassRecording(self):
		if self.seagrass_cam_format == None:
			print("seagrass camera not set, please set first")
			return
		print(f"start seagrass recording")
		self._toolBox.seagrassDetect.startRecording()
	def stopSeagrassRecording(self):
		print(f"stop seagrass recording")
		self._toolBox.seagrassDetect.stopRecording()
	

	def processDetection(self, msg):
		cmd_ID = int(msg[0])
		videoNo = int(msg[1])
		if cmd_ID == 0:
			enabled = msg[2]
			formatIndex = msg[3]
			if formatIndex not in self.videoFormatList:
				print('format error')
				return
			formatStr = ""
			for formatpair in self.videoFormatList[formatIndex]:
				if formatpair[0] == videoNo:
					formatStr = formatpair[1]
			if formatStr == "":
				return
			print(f"VideoManager::processDetection: video{videoNo} {formatStr} {self._toolBox.config.getFormatInfo(formatIndex)} set {enabled}")
		elif cmd_ID == 1:
			if cmd_ID == 0:
				print("VideoManager::processDetection: cmd:1")
	def handleMsg(self, data, addr):

		operation = int(data[0])
		if operation == 0 and len(data) >= 9:
			self.handleSetFormat(data, addr)
		elif operation == 1:
			self.handleSetFormat(data, addr)
		elif operation == 2:
			self.handleQuit(data, addr)
		elif operation == 3:
			self.handleControl(data, addr)
		elif operation == 4:
			self.handleDetect(data, addr)
		elif operation == 5:
			self.handleSeagrass(data, addr)
		else:
			logging.warning(f"Unknown operation: {operation}")
		
	def handleSetFormat(self, data, addr):
		"""
		兼容舊版 formatIndex，呼叫新版 play()
		"""
		videoNo = int(data[1])
		formatIndex = int(data[2])
		encoder = 'h264' if int(data[3]) == 0 else 'mjpeg'
		port = int.from_bytes(data[4:8], 'little')
		ai_enabled = int(data[8])
		ip = addr[0]

		# 1. 取得舊版解析度
		formatInfo = self.getFormatInfoByIndex(formatIndex)
		if not formatInfo:
			logging.warning(f"Invalid formatIndex {formatIndex}")
			return
		width, height, fps = formatInfo

		# 2. 檢查相機是否存在，並確認有該解析度
		if videoNo not in self.pipelines:
			logging.warning(f"video{videoNo} not found")
			return

		cam_formats = self.pipelines[videoNo]["formats"]
		fmtFound = None
		for fmt, w, h, f in cam_formats:
			if w == width and h == height and f == fps:
				fmtFound = fmt
				break
		if not fmtFound:
			logging.warning(f"video{videoNo} does not support {width}x{height}@{fps}")
			return

		# 3. 呼叫新版 play()
		self.play(videoNo, width, height, fps, encoder, ip, port, ai_enabled)
		logging.info(f"handleSetFormat: video{videoNo} {fmtFound} {width}x{height}@{fps} encoder={encoder}, ai={ai_enabled}")

