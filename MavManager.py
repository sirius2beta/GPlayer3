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
			msg = conn.recv() 
			print(f"  MavManager receive msg:{msg}")
			header = msg.split()[0]
			body = msg.split()[1]
			if header == "p": 
				mavrouter.connectGCS(f'udp:{body}:14450',True)
			elif header == "s": 
				mavrouter.connectGCS(f'udp:{body}:14550',False)
			elif header == "g":
				mavrouter.connectVehicle(body)
			elif header == "x":
				del mavrouter
				break
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
			msg = self.data
			self.data = ""
			self.lock2.release()
			if self.thread_terminate is True:
				break
			if msg == 'HEARTBEAT':
				self._conn.send(msg)
				time.sleep(0.1)





