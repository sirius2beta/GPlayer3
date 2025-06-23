import gi
import os
import subprocess
import time
import threading
import socket
import struct
import sys
import numpy as np

import VideoFormat as VF
import MavManager
from GTool import GTool

# definition of all the headers
HEARTBEAT = b'\x00'
FORMAT = b'\x01'
COMMAND = b'\x02'
QUIT = b'\x03'
SENSOR = b'\x04'
CONTROL = b'\x05'
DETECT = b'\x06'

# For dual ip auto switching mechanism, all internet traffics are going through NetworkManager
class NetworkManager(GTool):
    def __init__(self, toolbox):
        super().__init__(toolbox)  
        self.BOAT_ID = 0
        self.PC_IP='10.10.10.205'
        self.SERVER_IP = ''
        self.P_CLIENT_IP = '127.0.0.1' #PC IP
        self.S_CLIENT_IP = '127.0.0.1'
        self.OUT_PORT = 50008
        self.IN_PORT = 50006 
        self.primaryNewConnection = False
        self.secondaryNewConnection = False
        self.mavLastConnectedIP = ''

        self.mavPre = time.time()
        self.mavCurrent = self.mavPre

        self.primaryLastHeartBeat = 0
        self.secondaryLastHeartBeat = 0
        self.isSecondaryConnected = False
        self.isPrimaryConnected = False

        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((self.SERVER_IP, self.IN_PORT))
        self.server.setblocking(0)

        self.thread_terminate = False
        self.lock = threading.Lock()

    def __del__(self):
        print("------------------------del")

    # startLoop need to be called to start internet communication
    def startLoop(self):
        self.thread_cli = threading.Thread(target=self.aliveLoop)
        self.thread_ser = threading.Thread(target=self.listenLoop)
        self.thread_cli.daemon = True
        self.thread_ser.daemon = True
        self.thread_cli.start()
        self.thread_ser.start()
        print("[o] NetworkManager started")

    # send message with topic
    def sendMsg(self, topic, msg):
        now = time.time()
        # Send message from outside
        
        msg = topic + chr(self.BOAT_ID).encode() + msg
        #print(f"sendMsg:\n -topic:{msg[0]}\n -msg: {msg}")
        #print(f'primary timeout: {now-self.primaryLastHeartBeat}')
        #print(f'secondary timeout: {now-self.secondaryLastHeartBeat}')
        if now-self.primaryLastHeartBeat < 2:
            #print(f"P sendMsg:\n -topic:{msg[0]}\n -msg: {msg}")
            try:
                self.client.sendto(msg,(self.P_CLIENT_IP,self.OUT_PORT))

            except:
                print(f"Primary unreached: {self.P_CLIENT_IP}:{self.OUT_PORT}")
        # Send secondary heartbeat every 0.5s
        elif now-self.secondaryLastHeartBeat < 2:
            #print(f"S sendMsg:\n -topic:{msg[0]}\n -msg: {msg}")
            try:
                self.client.sendto(msg,(self.S_CLIENT_IP, self.OUT_PORT))
            except:
                print(f"Secondary unreached: {self.S_CLIENT_IP}:{self.OUT_PORT}")
        else:
            try:
                self.client.sendto(msg,(self.P_CLIENT_IP,self.OUT_PORT))
                #self.client.sendto(msg,(self.S_CLIENT_IP, self.OUT_PORT))
            except:
                print(f"Secondary/Primary unreached: {self.S_CLIENT_IP}:{self.OUT_PORT}")
    
    # sending heartbeat to ground control station
    def aliveLoop(self):        
        while True:
            now = time.time()
            beat = HEARTBEAT + chr(self.BOAT_ID).encode()
                        
            # Check primary/secondary heartBeat from PC, check if disconnected
            if now-self.primaryLastHeartBeat >3:
                if self.mavLastConnectedIP != 's' and self.isSecondaryConnected == True:
                    self._toolBox.mavManager.connectGCS(self.S_CLIENT_IP)
                    self.mavLastConnectedIP = 's'
                self.isPrimaryConnected = False
            else:
                self.isPrimaryConnected = True
            if now-self.secondaryLastHeartBeat >3:
                self.isSecondaryConnected = False
            else:
                self.isSecondaryConnected = True
                
            # Check newConnection 
            if self.primaryNewConnection:
                print(f"\n=== New connection ===\n -Primary send to: {self.P_CLIENT_IP}:{self.OUT_PORT}\n", flush=True)
                self._toolBox.mavManager.connectGCS(self.P_CLIENT_IP)
                self.mavLastConnectedIP = 'p'
                self.primaryLastHeartBeat = time.time()
                self.primaryNewConnection = False
            if self.secondaryNewConnection:
                print(f"\n=== New connection ===\n -Secondarysend to: {self.S_CLIENT_IP}:{self.OUT_PORT}\n")
                if not self.isPrimaryConnected:
                    self._toolBox.mavManager.connectGCS(self.S_CLIENT_IP)
                    self.mavLastConnectedIP = 's'
                self.secondaryNewConnection = False
            
            # Send primary heartbeat every 0.5s
            try:
                self.client.sendto(beat,(self.P_CLIENT_IP,self.OUT_PORT))
                #self._toolBox.mavManager.send_distance_sensor_data()
                #self.client.sendto(sns1,(self.P_CLIENT_IP,self.OUT_PORT))
                #self.client.sendto(sns2,(self.P_CLIENT_IP,self.OUT_PORT))
                time.sleep(0.5)
            except:
                print(f"\n=== Bad connection ===\n -Primary unreached: {self.P_CLIENT_IP}:{self.OUT_PORT}\n")
            # Send secondary heartbeat every 0.5s
            try:
                self.client.sendto(beat,(self.S_CLIENT_IP, self.OUT_PORT))
                time.sleep(0.5)
            except:
                print(f"\n=== Bad connection ===\n -Secondary unreached: {self.S_CLIENT_IP}:{self.OUT_PORT}\n")

    # handle all incomming traffic, sending them to corresponding module for processing
    def listenLoop(self):        
        while True:
            try:
                indata, addr = self.server.recvfrom(1024) 
            except:
                continue

            now = time.time()
            #print(f'[GP] => message from: {str(addr)}, data: {indata}')
            
            indata = indata
            header = indata[0]
            if header == HEARTBEAT[0]:
                indata = indata[1:]
                ip = addr[0]
                self.BOAT_ID = indata[0]
                primary = indata[1:].decode()
                #print("[HEARTBEAT]")
                #print(f" -id:{self.BOAT_ID}, primary:{primary}")
                if primary == 'P':
                    if self.P_CLIENT_IP != ip or now-self.primaryLastHeartBeat > 3:
                        self.P_CLIENT_IP = ip
                        self.primaryNewConnection = True
                    self.primaryLastHeartBeat = now
                else:
                    if self.S_CLIENT_IP != ip or now-self.secondaryLastHeartBeat > 3:
                        print(f"S:{self.S_CLIENT_IP}, s:{ip}")
                        self.S_CLIENT_IP = ip
                        self.secondaryNewConnection = True
                    self.secondaryLastHeartBeat = now

            elif header == FORMAT[0]:
                print("[FORMAT]")
                msg = b''
                if len(self._toolBox.videoManager.videoFormatList) == 0:
                    print("no videoformat")
                    continue
                else:
                    for form in self._toolBox.videoManager.videoFormatList:
                        for video in self._toolBox.videoManager.videoFormatList[form]:
                            videoIndex = video[0]
                            msg += struct.pack("<2B", videoIndex, form)   
                    print("send videoformat")
                    print(msg)
                    self.sendMsg(FORMAT, msg)

                
            elif header == COMMAND[0]:
                indata = indata[1:]
                print("[COMMAND]")
                print(indata)
                
                if len(indata)<2:
                    continue

                videoNo = int(indata[0])
                formatIndex = int(indata[1])
                encoder = int(indata[2])
                if encoder == 0:
                    encoder = 'h264'
                else:
                    encoder = 'mjpeg'
                #port = int(np.fromstring(indata[2:], dtype='<u4'))
                port = int.from_bytes(indata[3:7], 'little')
                ai_enabled = int(indata[7])
                print(f"videoNo: {videoNo}, formatIndex: {formatIndex}, port: {port}, ai: {ai_enabled}")

                if formatIndex not in self._toolBox.videoManager.videoFormatList:
                    print('format error')
                    continue
                formatStr = ""
                for formatpair in self._toolBox.videoManager.videoFormatList[formatIndex]:
                    if formatpair[0] == videoNo:
                        formatStr = formatpair[1]
                if formatStr == "":
                    continue
                ip = addr[0]
                formatInfo = self._toolBox.config.getFormatInfo(formatIndex)
                print(f"play: video{videoNo}, {formatStr}, {formatInfo[0]}x{formatInfo[1]} {formatInfo[2]}/1, encoder={encoder}, ip={ip}, port={port}")
                self._toolBox.videoManager.play(videoNo, formatStr, formatInfo[0], formatInfo[1], formatInfo[2], encoder, ip, port, ai_enabled)
                

            elif header == SENSOR[0]:
                print("[SENSOR]")
                
            elif header == QUIT[0]:
                print("[QUIT]")
                video = int(indata[6:].decode())
                self._toolBox.videoManager.stop(video)
                print("  -quit : video"+str(video))

            elif header == CONTROL[0]:
                indata = indata[1:]
                print("[CONTROL]")
                boat_id = int(indata[0])
                control_type = int(indata[1])
                self._toolBox.deviceManager.processControl(control_type, indata[2:])

            elif header == DETECT[0]:
                indata = indata[1:]
                print("[DETECT]")
                boat_id = int(indata[0])
                self._toolBox.videoManager.processDetection(indata[1:])