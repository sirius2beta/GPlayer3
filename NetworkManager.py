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
import struct

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
SYSTEM   = b'\x09'


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
        self.periodicClock = time.time()

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
            SEAGRASS[0]:  self.handleSeagrass,
            SYSTEM[0]:    self.handleSystem,
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
            
            self.periodicWork()

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
            # 使用新 pipelines，但產生舊版格式列表
            formatList = self._toolBox.videoManager.get_videoFormatList_legacy()
            if not formatList:
                logging.info("No video format available")
                return

            msg = b''
            for form in formatList:
                for video in formatList[form]:
                    videoIndex = video[0]
                    msg += struct.pack("<2B", videoIndex, form)
            self.sendMsg(FORMAT, msg)

    def handleCommand(self, data, addr):
        self._toolBox.videoManager.handleMsg(data, addr)

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
        ip = addr[0]

        if operation == 0 and len(data) >= 8:
            videoNo = int(data[1])
            formatIndex = int(data[2])
            encoder = 'h264' if int(data[3]) == 0 else 'mjpeg'
            port = int.from_bytes(data[4:8], 'little')

            # 取得解析度
            fmtMap = self._toolBox.videoManager.getFormatInfoByIndexMap()
            if formatIndex not in fmtMap:
                logging.warning(f"No resolution mapping for formatIndex {formatIndex}")
                return
            width, height, fps = fmtMap[formatIndex]

            # 檢查相機是否存在，並找對應格式
            if videoNo not in self._toolBox.videoManager.pipelines:
                logging.warning(f"video{videoNo} not found")
                return

            cam_formats = self._toolBox.videoManager.pipelines[videoNo]["formats"]
            fmtFound = next((f for f, w2, h2, f2 in cam_formats if w2 == width and h2 == height and f2 == fps), None)
            if not fmtFound:
                logging.warning(f"video{videoNo} does not support {width}x{height}@{fps}")
                return

            self._toolBox.videoManager.setSeagrassCamera(
                videoNo, fmtFound, width, height, fps, encoder, ip, port
            )

        elif operation == 1:
            self._toolBox.videoManager.startSeagrassRecording()
        elif operation == 2:
            self._toolBox.videoManager.stopSeagrassRecording()
    def handleSystem(self, data, addr):
        if not data:
            return

        command = int(data[0])
        if command == 0:
            # restart GPlayer3.service
            logging.info("Restarting GPlayer3.service as per SYSTEM command")
            try:
                subprocess.run(['systemctl', 'restart', 'GPlayer3.service'], check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to restart GPlayer3.service: {e}")
        elif command == 1:
            # reboot computer
            logging.info("Rebooting system as per SYSTEM command")
            try:
                subprocess.run(['reboot'], check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to reboot system: {e}")
    def periodicWork(self):
        now = time.time()
        if now - self.periodicClock >= 3: # every 10 seconds
            self.periodicClock = time.time()
            self.checkSystemStatus()

    def checkSystemStatus(self):
        status = self._toolBox.deviceManager.checkDeviceStatus()
        data = struct.pack("<B", status[0])
        data += struct.pack("<B", status[1])
        data += struct.pack("<B", status[2])
        data += struct.pack("<B", status[3])
        self.sendMsg(b'\x08', data)