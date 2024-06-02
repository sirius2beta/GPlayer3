from pymavlink import mavutil
import threading
import time
import multiprocessing 

from GTool import GTool
# PyMAVLink has an issue that received messages which contain strings
# cannot be resent, because they become Python strings (not bytestrings)
# This converts those messages so your code doesn't crash when
# you try to send the message again.
class MavManager(GTool):
	def __init__(self, toolbox):
		super().__init__(toolbox)
		self.mav_connected = False
		self.p = multiprocessing.Process(target =self.mav_worker, args = (self._toolBox.child_conn,)) 
		self.p.start()
	def mav_worker(self, conn):
		mavrouter = MavWorker(None, conn)
		while True:
			
			time.sleep(0.1)
		

def fixMAVLinkMessageForForward(msg):
	msg_type = msg.get_type()

	if msg_type in ('PARAM_VALUE', 'PARAM_REQUEST_READ', 'PARAM_SET'):
		if type(msg.param_id) == str:
			msg.param_id = msg.param_id.encode()
	elif msg_type == 'STATUSTEXT':
		if type(msg.text) == str:
			msg.text = msg.text.encode()
	return msg

class MavWorker:
	def __init__(self, toolBox, conn):
		self.toolBox = toolBox
		self._conn = conn
		self.thread_terminate = False
		self.gcs_conn_p = None
		self.vehicle = None
		self.lock = threading.Lock()
		self.lock2 = threading.Lock()
		self.ip = ""
		self.data = ""
		self.loop = threading.Thread(target=self.loopFunction)
		self.loop.daemon = True
		self.loop.start()
		self.loop2 = threading.Thread(target=self.processLoop)
		self.loop2.daemon = True
		self.loop2.start()
		
		

	def __del__(self):
		self.thread_terminate = True
		self.loop.join()
		self.loop2.join()
	def connectGCS(self, ip, isPrimary):
		if isPrimary:
			self.lock.acquire()
			if self.ip != ip:
			
				self.ip = ip
				if self.gcs_conn_p != None:
					self.gcs_conn_p.close()			
				self.gcs_conn_p = mavutil.mavlink_connection(ip, input=False)
			self.lock.release()
		else:
			self.lock.acquire()
			if self.gcs_conn_s != None:
				self.gcs_conn_s.close()
			self.gcs_conn_s = mavutil.mavlink_connection(ip, input=False)
			self.lock.release()
	def connectVehicle(self, dev):
		if self.vehicle != None:
				self.vehicle.close()
		self.vehicle = mavutil.mavlink_connection(dev, baud=57600)
	def loopFunction(self):
		while True:
			if self.thread_terminate is True:
				break
            # Don't block for a GCS message - we have messages
            # from the vehicle to get too
			if self.vehicle != None:
				self.lock.acquire()
				vcl_msg = self.vehicle.recv_match(blocking=False)
				
				gcs_msg_p = ''

				if self.gcs_conn_p != None:
					gcs_msg_p = self.gcs_conn_p.recv_match(blocking=False)
					self.handleMsg(vcl_msg, self.gcs_conn_p)
					self.handleMsg(gcs_msg_p, self.vehicle)
				
				self.lock.release()
			# Don't abuse the CPU by running the loop at maximum speed
			time.sleep(0.0001)
	def handleMsg(self, msg, target):
		
		if msg is None:
			pass
		elif msg.get_type == '':
			print("*** Fatal MavManager: Mavlink_message base type")
			pass
		elif msg.get_type() != 'BAD_DATA':
			#For debug
			
			if msg.get_type() == 'HEARTBEAT':
				self.lock2.acquire()
				self.data ='HEARTBEAT'
				self.lock2.release()

			# We now have a message we want to forward. Now we need to
			# make it safe to send
			msg = fixMAVLinkMessageForForward(msg)
			# Finally, in order to forward this, we actually need to
			# hack PyMAVLink so the message has the right source
			# information attached.
			target.mav.srcSystem = msg.get_srcSystem()
			target.mav.srcComponent = msg.get_srcComponent()
	
			# Only now is it safe to send the message
			target.mav.send(msg)

	def processLoop(self):
		while True:
			self.lock2.acquire()
			out_msg = self.data
			self.data = ""
			self.lock2.release()
			if self.thread_terminate is True:
				break
			msg = self._conn.recv() 
			print(f"  MavManager receive msg:{msg}")
			header = msg.split()[0]
			body = msg.split()[1]
			if header == "p": 
				self.connectGCS(f'udp:{body}:14450',True)
			elif header == "s": 
				self.connectGCS(f'udp:{body}:14550',False)
			elif header == "g":
				self.connectVehicle(body)
			else:
				print(msg)
				self.send_distance_sensor_data()
			time.sleep(0.1)

			if msg == 'HEARTBEAT':
				self._conn.send(out_msg)
				time.sleep(0.1)

	def send_distance_sensor_data(self):
		try:
			distance = 500  # 固定距离值，单位为厘米（5米 = 500厘米）
			min_distance = 20   # 最小检测距离，单位为厘米
			max_distance = 1000 # 最大检测距离，单位为厘米
			current_time = 0  # 当前时间，单位为毫秒
			sensor_type = 0  # 传感器类型
			sensor_id = 0  # 传感器ID
			orientation = 0  # 方向，0表示正前方
			covariance = 0  # 协方差，0表示测量无误差
			

			
			# 调用距离传感器编码函数
			msg = self.vehicle.mav.distance_sensor_encode(
				current_time,
				min_distance,
				max_distance,
				distance,
				sensor_type,
				sensor_id,
				orientation,
				covariance,
				)

			# 发送消息
			self.vehicle.mav.send(msg)
			#print("Distance data sent")
		except Exception as e:
			print(f"Error sending distance data: {e}")



