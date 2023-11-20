# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 17:51:30 2023

@author: User
"""

from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2

import time

connection = mavutil.mavlink_connection('udpin:192.168.0.255:14540',source_system=2)

while True:
    #msg = connection.wait_heartbeat(blocking=False)
    #print(f"Heartbeat from system {msg.get_srcSystem()} {connection.target_component}")
    
    connection.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GROUND_ROVER, mavutil.mavlink.MAV_AUTOPILOT_GENERIC, 0, 0, 0)
    #msg = connection.recv_match(type='PARAM_REQUEST_READ', blocking=True, timeout=None)
    #print(f"Param {msg.param_index}")
    print("send")
    time.sleep(1)
