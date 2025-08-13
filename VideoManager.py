import gi
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


		self.pipelinesexist = []
		self.pipelines = []
		self.pipelines_state = []
		self.camera_format = []
		self.videoFormatList = {}
		self.videoWithYUYV = []
		self.ai_cam = -1
		self.seagrass_cam = -1
		self.seagrass_cam_format = None
		
		if(self._toolBox.OS == 'bionic'): # for Ubuntu 18.04 (Jetson Nano
				self.get_video_format_Ubuntu_18_04()
		else:
			self.get_video_format()

		self.portOccupied = {} # {port, videoNo}

		GObject.threads_init()
		Gst.init(None)

		self.createPipelines()
		print("[o] VideoManager: started")
		index = 0
		if len(self.videoFormatList) == 0:
			print("      - no camera connected")
		for form in self.videoFormatList:
			for video in self.videoFormatList[form]:
				print(f"      - {index}:  video{video[0]} {video[1]}")
			index += 1
		#if self.toolBox().oakCam.hasCamera:
		#	print("      - OAK camera connected")

		

	def createPipelines(self):
		for i in range(0, 10):
			pipeline = Gst.Pipeline()
			self.pipelines.append(pipeline)
			self.pipelinesexist.append(i)
			self.pipelines_state.append(False)

	#get video format from existing camera devices
	def get_video_format(self):
		#Check camera device
		for i in range(0,10):
			newCamera = True
			try:
				cmd = "v4l2-ctl -d /dev/video{} --list-formats-ext".format(i)
				returned_value = subprocess.check_output(cmd,shell=True,stderr=subprocess.DEVNULL).replace(b'\t',b'').decode("utf-8")  # returns the exit code in unix
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
					fps = j.split()[3][1:].split('.')[0]
					self.camera_format.append([i,form, width, height , fps])
					index = self._toolBox.config.getVideoFormatIndex(width,height,fps)
					if index != -1:
						if form == 'YUYV':
								if i not in self.videoWithYUYV:
									self.videoWithYUYV.append(i)
								else:
									pass
						if index not in self.videoFormatList:
							self.videoFormatList[index] = []
							self.videoFormatList[index].append([i,form])
							
						else:
							video_index = 0
							add = True
							for video in self.videoFormatList[index]:
								if video[0] == i:
									if form =='MJPG':
										self.videoFormatList[index].pop(video_index)
										self.videoFormatList[index].append([i,form])
										add = False
									else:
										add = False
										break
								video_index += 1
							if add == True:
								self.videoFormatList[index].append([i,form])
		print("video with YUYV:", self.videoWithYUYV)			
	def get_video_format_Ubuntu_18_04(self):	
		#Check camera device
		for i in range(0,10):
			newCamera = True
			try:
				cmd = "v4l2-ctl -d /dev/video{} --list-formats-ext".format(i)
				returned_value = subprocess.check_output(cmd,shell=True,stderr=subprocess.DEVNULL).replace(b'\t',b'').decode("utf-8")  # returns the exit code in unix
			except:
				continue
			line_list = returned_value.splitlines()
			new_line_list = list()
			for j in line_list:
				# print(j.split())
				if len(j.split()) == 0:
					continue
				elif j.split()[0] =='Pixel':
					form = j.split()[2][1:-1]
				elif j.split()[0] =='Size:':
					size = j.split()[2]
					width, height = size.split('x')
				elif j.split()[0] == 'Interval:':
					fps = j.split()[3][1:].split('.')[0]
					self.camera_format.append('video{} {} width={} height={} framerate={}'.format(i,form, width, height , fps))
					index = self._toolBox.config.getVideoFormatIndex(width, height, fps)
					if index != -1:
						if index not in self.videoFormatList:
							self.videoFormatList[index] = []
							self.videoFormatList[index].append([i,form])
						else:
							video_index = 0
							add = True
							for video in self.videoFormatList[index]:
								if video[0] == i:
									if form =='MJPG':
										self.videoFormatList[index].pop(video_index)
										self.videoFormatList[index].append([i,form])
										add = False
									else:
										add = False
										break
								video_index += 1
							if add == True:
								self.videoFormatList[index].append([i,form])

	def getYUYVFrameRate(self, cam, width, height):
		fps = []
		for format in self.camera_format:
			if cam == format[0] and  format[1] == "YUYV" and format[2] == width and format[3] == height:
				return format[4]
		return ""

	def play(self, cam, format, width, height, framerate, encoder, IP, port, YOLO_detection_enabled):
		gstring = VideoFormat.getFormatCMD(self._toolBox.OS, cam, format, width, height, framerate, encoder, IP, port)
		print(gstring)
		
		if port in self.portOccupied:
			videoToStop = self.portOccupied[port]
			self.stop(videoToStop)
			
			print("  -quit occupied: video"+str(videoToStop))
		
		if self.pipelines_state[cam] == True:
			self.pipelines[cam].set_state(Gst.State.NULL)
		if self.seagrass_cam == cam:
			if self._toolBox.seagrassDetect == None:
				print("seagrassDetect not ready, please wait...")
				return	
			print(self.seagrass_cam_format)
			self._toolBox.seagrassDetect.play()
			print(self.seagrass_cam_format)
			print(f"start seagrass camera on cam:{cam}")

		elif YOLO_detection_enabled == 1:
			if self._toolBox.jetsonDetect == None:
				print("JetsonDetect not ready, please wait...")
				return
			if cam != self.ai_cam:
				YUYVfps = self.getYUYVFrameRate(cam, width, height)
				if YUYVfps != "":
					self._toolBox.jetsonDetect.play([cam, "YUYV", width, height, YUYVfps, IP, port])
					print(f"start ai on cam:{cam}")
					self.ai_cam = cam
				else:
					print(f"video{cam} had no YUYV format")
					return

				# start ai camera
			else:
				print(f"restart ai on cam:{cam}")
				# restart ai camera
				return

		else:
			if cam == self.ai_cam:
				# stop ai cam

				print(f"stop ai on cam:{cam}")
				self._toolBox.jetsonDetect.stop()
				self.ai_cam = -1
				return
			else:
				self.pipelines[cam] = Gst.parse_launch(gstring)
				self.pipelines[cam].set_state(Gst.State.PLAYING)
				self.pipelines_state[cam] = True
		self.portOccupied[port] = cam
	def setSeagrassCamera(self, cam, format, width, height, framerate, encoder, IP, port):
		print(f"set seagrass camera: {cam} {format} {width} {height} {framerate} {encoder} {IP} {port}")
		YUYVfps = self.getYUYVFrameRate(cam, width, height)
		if YUYVfps != "":
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
	def stop(self, cam):
		for port in self.portOccupied:
			if self.portOccupied[port] == cam:
				self.portOccupied.pop(port, None)
				break
		if cam == self.seagrass_cam:
			self._toolBox.seagrassDetect.stop()
			#self.seagrass_cam = -1
			print(f"stop seagrass on cam:{cam}")
			return
		if cam == self.ai_cam:
			# stop ai cam
			print(f"stop ai on cam:{cam}")
			self._toolBox.jetsonDetect.stop()
			#self._toolBox.seagrassDetect.stop()
			self.ai_cam = -1
			pass
		if self.pipelines_state[cam] == True:
			self.pipelines[cam].set_state(Gst.State.NULL)
			self.pipelines_state[cam] = False

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