import gi
import os
import subprocess
import time
import threading
import socket
import struct
import sys
import logging
import numpy as np

import VideoFormat as VF
import MavManager
from GTool import GTool

# Headers
HEARTBEAT = b'\x00'
FORMAT    = b'\x01'
COMMAND   = b'\x02'
QUIT      = b'\x03'
SENSOR    = b'\x04'
CONTROL   = b'\x05'
DETECT    = b'\x06'
SEAGRASS  = b'\x07'


class NetworkManager(GTool):
    def __init__(self, toolbox):
        super().__init__(toolbox)

        # Connection info
        self.BOAT_ID = 0
        self.PC_IP = '10.10.10.205'
        self.SERVER_IP = ''
        self.P_CLIENT_IP = '127.0.0.1'
        self.S_CLIENT_IP = '127.0.0.1'
        self.OUT_PORT = 50008
        self.IN_PORT = 50006

        # State
        self.primaryNewConnection = False
        self.secondaryNewConnection = False
        self.mavLastConnectedIP = ''
        self.primaryLastHeartBeat = 0
        self.secondaryLastHeartBeat = 0
        self.isSecondaryConnected = False
        self.isPrimaryConnected = False

        # Socket setup
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((self.SERVER_IP, self.IN_PORT))
        self.server.settimeout(0.1)  # avoid busy loop

        self.thread_terminate = False
        self.lock = threading.Lock()

        # Packet handlers
        self.handlers = {
            HEARTBEAT[0]: self.handleHeartbeat,
            FORMAT[0]:    self.handleFormat,
            COMMAND[0]:   self.handleCommand,
            SENSOR[0]:    self.handleSensor,
            QUIT[0]:      self.handleQuit,
            CONTROL[0]:   self.handleControl,
            DETECT[0]:    self.handleDetect,
            SEAGRASS[0]:  self.handleSeagrass
        }

    def startLoop(self):
        self.thread_cli = threading.Thread(target=self.aliveLoop, daemon=True)
        self.thread_ser = threading.Thread(target=self.listenLoop, daemon=True)
        self.thread_cli.start()
        self.thread_ser.start()
        logging.info("NetworkManager started")

    def stopLoop(self):
        self.thread_terminate = True
        logging.info("Stopping NetworkManager threads...")

    def sendMsg(self, topic, msg):
        now = time.time()
        msg = topic + chr(self.BOAT_ID).encode() + msg

        target_ip = None
        if now - self.primaryLastHeartBeat < 2:
            target_ip = self.P_CLIENT_IP
        elif now - self.secondaryLastHeartBeat < 2:
            target_ip = self.S_CLIENT_IP
        else:
            target_ip = self.P_CLIENT_IP  # default to primary

        try:
            self.client.sendto(msg, (target_ip, self.OUT_PORT))
        except Exception as e:
            logging.warning(f"Send failed to {target_ip}:{self.OUT_PORT} - {e}")

    def aliveLoop(self):
        while not self.thread_terminate:
            now = time.time()
            beat = HEARTBEAT + chr(self.BOAT_ID).encode()

            # Connection status
            self.isPrimaryConnected = now - self.primaryLastHeartBeat <= 3
            self.isSecondaryConnected = now - self.secondaryLastHeartBeat <= 3

            # New connections
            if self.primaryNewConnection:
                logging.info(f"New primary connection: {self.P_CLIENT_IP}:{self.OUT_PORT}")
                self._toolBox.mavManager.connectGCS(self.P_CLIENT_IP)
                self.mavLastConnectedIP = 'p'
                self.primaryNewConnection = False
            if self.secondaryNewConnection:
                logging.info(f"New secondary connection: {self.S_CLIENT_IP}:{self.OUT_PORT}")
                if not self.isPrimaryConnected:
                    self._toolBox.mavManager.connectGCS(self.S_CLIENT_IP)
                    self.mavLastConnectedIP = 's'
                self.secondaryNewConnection = False

            # Send heartbeats
            for ip in [self.P_CLIENT_IP, self.S_CLIENT_IP]:
                try:
                    self.client.sendto(beat, (ip, self.OUT_PORT))
                except Exception as e:
                    logging.warning(f"Heartbeat failed to {ip}:{self.OUT_PORT} - {e}")
                time.sleep(0.5)

    def listenLoop(self):
        while not self.thread_terminate:
            try:
                indata, addr = self.server.recvfrom(1024)
            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"Socket recv error: {e}")
                continue

            header = indata[0]
            handler = self.handlers.get(header)
            if handler:
                handler(indata[1:], addr)
            else:
                logging.warning(f"Unknown packet header: {header}")

    # === Packet handlers ===

    def handleHeartbeat(self, data, addr):
        ip = addr[0]
        if len(data) < 2:
            return
        self.BOAT_ID = data[0]
        primary = data[1:].decode()

        if primary == 'P':
            if self.P_CLIENT_IP != ip or time.time() - self.primaryLastHeartBeat > 3:
                self.P_CLIENT_IP = ip
                self.primaryNewConnection = True
            self.primaryLastHeartBeat = time.time()
        else:
            if self.S_CLIENT_IP != ip or time.time() - self.secondaryLastHeartBeat > 3:
                self.S_CLIENT_IP = ip
                self.secondaryNewConnection = True
            self.secondaryLastHeartBeat = time.time()

    def handleFormat(self, data, addr):
        self._toolBox.videoManager.get_video_format()
        if not self._toolBox.videoManager.videoFormatList:
            logging.info("No video format available")
            return

        msg = b''
        for form in self._toolBox.videoManager.videoFormatList:
            for video in self._toolBox.videoManager.videoFormatList[form]:
                videoIndex = video[0]
                msg += struct.pack("<2B", videoIndex, form)
        self.sendMsg(FORMAT, msg)

    def handleCommand(self, data, addr):
        if len(data) < 8:
            logging.warning("COMMAND packet too short")
            return
        videoNo = int(data[0])
        formatIndex = int(data[1])
        encoder = 'h264' if int(data[2]) == 0 else 'mjpeg'
        port = int.from_bytes(data[3:7], 'little')
        ai_enabled = int(data[7])

        if formatIndex not in self._toolBox.videoManager.videoFormatList:
            logging.warning("Invalid format index")
            return

        formatStr = ""
        for formatpair in self._toolBox.videoManager.videoFormatList[formatIndex]:
            if formatpair[0] == videoNo:
                formatStr = formatpair[1]
        if not formatStr:
            return

        ip = addr[0]
        formatInfo = self._toolBox.config.getFormatInfo(formatIndex)
        self._toolBox.videoManager.play(videoNo, formatStr, formatInfo[0], formatInfo[1], formatInfo[2],
                                        encoder, ip, port, ai_enabled)

    def handleSensor(self, data, addr):
        logging.info("SENSOR packet received")

    def handleQuit(self, data, addr):
        try:
            video = int(data.decode()[5:])
            self._toolBox.videoManager.stop(video)
            logging.info(f"Stopped video {video}")
        except Exception as e:
            logging.warning(f"QUIT packet parse error: {e}")

    def handleControl(self, data, addr):
        if len(data) < 2:
            return
        boat_id = int(data[0])
        control_type = int(data[1])
        self._toolBox.deviceManager.processControl(control_type, data[2:])

    def handleDetect(self, data, addr):
        boat_id = int(data[0])
        self._toolBox.videoManager.processDetection(data[1:])

    def handleSeagrass(self, data, addr):
        if not data:
            return
        operation = int(data[0])
        if operation == 0 and len(data) >= 8:
            videoNo = int(data[1])
            formatIndex = int(data[2])
            encoder = 'h264' if int(data[3]) == 0 else 'mjpeg'
            port = int.from_bytes(data[4:8], 'little')

            if formatIndex not in self._toolBox.videoManager.videoFormatList:
                return

            formatStr = ""
            for formatpair in self._toolBox.videoManager.videoFormatList[formatIndex]:
                if formatpair[0] == videoNo:
                    formatStr = formatpair[1]
            if not formatStr:
                return

            ip = addr[0]
            formatInfo = self._toolBox.config.getFormatInfo(formatIndex)
            self._toolBox.videoManager.setSeagrassCamera(videoNo, formatStr, formatInfo[0], formatInfo[1],
                                                         formatInfo[2], encoder, ip, port)
        elif operation == 1:
            self._toolBox.videoManager.startSeagrassRecording()
        elif operation == 2:
            self._toolBox.videoManager.stopSeagrassRecording()
