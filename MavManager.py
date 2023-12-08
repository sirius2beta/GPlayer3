from pymavlink import mavutil
import threading
import time


# PyMAVLink has an issue that received messages which contain strings
# cannot be resent, because they become Python strings (not bytestrings)
# This converts those messages so your code doesn't crash when
# you try to send the message again.
def fixMAVLinkMessageForForward(msg):
	msg_type = msg.get_type()
	if msg_type in ('PARAM_VALUE', 'PARAM_REQUEST_READ', 'PARAM_SET'):
		if type(msg.param_id) == str:
			msg.param_id = msg.param_id.encode()
	elif msg_type == 'STATUSTEXT':
		if type(msg.text) == str:
			msg.text = msg.text.encode()
	return msg

class MavManager:
	def __init__(self, toolBox):
		self.toolBox = toolBox
		self.thread_terminate = False
		self.gcs_conn_p = None
		self.gcs_conn_s = None
		self.vehicle = None
		self.loop = threading.Thread(target=self.loopFunction)
		self.loop.start()

	def __del__(self):
		self.thread_terminate = True
		self.loop.join()
	def connectGCS(self, ip, isPrimary):
		if isPrimary:
			if self.gcs_conn_p != None:
				self.gcs_conn_p.close()
			self.gcs_conn_p = mavutil.mavlink_connection(ip, input=False)
		else:
			if self.gcs_conn_s != None:
				self.gcs_conn_s.close()
			self.gcs_conn_s = mavutil.mavlink_connection(ip, input=False)

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
				vcl_msg = self.vehicle.recv_match(blocking=False)
				gcs_msg_p = ''
				gcs_msg_s = ''
				if self.gcs_conn_p != None:
					gcs_msg_p = self.gcs_conn_p.recv_match(blocking=False)
					self.handleMsg(vcl_msg, self.gcs_conn_p)
					self.handleMsg(gcs_msg_p, self.vehicle)
				if self.gcs_conn_s != None:
					gcs_msg_s = self.gcs_conn_s.recv_match(blocking=False)
					self.handleMsg(vcl_msg, self.gcs_conn_s)
					self.handleMsg(gcs_msg_s, self.vehicle)
					
			# Don't abuse the CPU by running the loop at maximum speed
			time.sleep(0.001)
	def handleMsg(self, msg, target):
		if msg is None:
			pass
		elif msg.get_type() != 'BAD_DATA':
			if msg.get_type() == 'HEARTBEAT':
				print(msg)
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






