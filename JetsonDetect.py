import argparse
from pathlib import Path
import threading
import time
import multiprocessing 
import math
import struct
from scipy.spatial.transform import Rotation
import cv2
import numpy as np

from config import CLASSES, COLORS
from models.torch_utils import det_postprocess
from models.utils import blob, letterbox, path_to_list
from GTool import GTool
from distance import distance, getR0

multiprocessing.set_start_method('spawn', force=True)

def detectTask(os, conn, input): # Thread that read data from oak camera
    enabled = True
    cap_send = None
    out_send = None
    w = 0
    h = 0
    playing = False
    engine = ''
    encode_string = ''
    if os == 'jammy': # Jetson orin nano
        engine = 'engine/orin_nano/yolov8s.engine'
        encode_string = 'x264enc tune=zerolatency speed-preset=superfast'
    elif os == 'focal': # Jetson xavier
        engine = 'engine/xavier/yolov8s.engine'
        encode_string = 'video/x-raw,format=I420 ! nvvideoconvert ! video/x-raw(memory:NVMM) ! nvv4l2h264enc'
    else:
        return
    K0 = np.array(
        [[1000, 0., 320],
        [0., 1000, 240],
        [0., 0., 1.]]
    )
    cam_height = 0.4
    R0 = getR0(0, 0)
    
    while True:
        if not playing:
            msg = input.get()
            if msg[0] == "p": # play
                msg = msg[1:]
                if cap_send != None:
                    cap_send.release()
                if out_send != None:
                    cap_send.release()
                video_pipeline = f'v4l2src device=/dev/video{msg[0]} ! video/x-raw, format=YUY2, width={msg[2]}, height={msg[3]}, framerate={msg[4]}/1 ! videoconvert ! appsink'
                cap_send = cv2.VideoCapture(video_pipeline, cv2.CAP_GSTREAMER)
                w = cap_send.get(cv2.CAP_PROP_FRAME_WIDTH)
                h = cap_send.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap_send.get(cv2.CAP_PROP_FPS)
                out_send = cv2.VideoWriter(f'appsrc ! videoconvert ! {encode_string} ! rtph264pay pt=96 config-interval=1 ! udpsink host={msg[5]} port={msg[6]}'\
                    ,cv2.CAP_GSTREAMER\
                    ,0\
                    , int(fps)\
                    , (int(w), int(h))\
                    , True)

                if not cap_send.isOpened():
                    print('VideoCapture not opened')
                    continue
                if not out_send.isOpened():
                    print('VideoWriter not opened')
                    continue
                playing = True
                from ultralytics import YOLO
                model = YOLO(engine)
            else:
                continue
        elif not input.empty():
            msg = input.get()
            if msg[0] == "x":
                if cap_send != None:
                    cap_send.release()
                if out_send != None:
                    cap_send.release()
                playing = False
                continue
            elif msg[0] == "i":
                pitch = float(msg[1])  # 直接使用 pitch
                roll = float(msg[2])   # 直接使用 roll
                R0 = getR0(pitch, roll)
                #print(R0)
            
        ret,frame = cap_send.read()
        if not ret:
            print('JetsonDetect: Error!! empty frame')
            break
        
        results = model.predict(frame, conf=0.5, verbose=False)
        count = 0
        boxes = results[0].boxes.xyxy
        cls_name = results[0].names
        classes = results[0].boxes.cls
        depth = 0
        detect_matrix = []
        for box, clas in zip(boxes,classes):
            x1, y1, x2, y2 = box
            coord = distance(K0, R0, cam_height, int(x1)+(int(x2)-int(x1))/2, int(y2))
            detect_matrix.append([int(clas), int(x1), int(y1), int(x2)-int(x1), int(y2)-int(y1), coord[0], coord[1]])

        if out_send.isOpened():
            out_send.write(frame)
        if conn.empty():
            if not conn.full():
                conn.put(detect_matrix, block= False)

    out_send.release()
    cap_send.release()


class JetsonDetect(GTool):
    def __init__(self, toolbox):
        super().__init__(toolbox)
        self.out_conn = multiprocessing.Queue(1)
        self.in_conn = multiprocessing.Queue(1)
        self.video_no = -1
        self.enabled = True

    def play(self, msg):
        msg.insert(0, "p")
        self.video_no = msg[1]
        self.in_conn.put(msg)
    def stop(self):
        self.in_conn.put(["x"])
        self.video_no = -1
    def updateIMU(self, msg): #[pitch, roll]
        msg.insert(0, "i")
        self.in_conn.put(msg)
    def sendMsg(self, msg):
        self.in_conn.put(msg)

    def startLoop(self):
        self.p = multiprocessing.Process(target = detectTask, args = (self._toolBox.OS, self.out_conn, self.in_conn))
        #self.p = multiprocessing.Process(target = work)
        self.p.start()
        self.outputLoop = threading.Thread(target=self.OutputLoop)
        self.outputLoop.daemon = True
        self.outputLoop.start()

    def OutputLoop(self): # Thread that send data to the networkmanager
        while True:
            #self.toolBox.mavManager.send_distance_sensor_data(7, int(min(distances[:3])))
            #self.toolBox.mavManager.send_distance_sensor_data(0, int(min(distances[3:6])))
            #self.toolBox.mavManager.send_distance_sensor_data(1, int(min(distances[6:])))
            d = self.out_conn.get()
            self.sendDetectionResult(d)
            time.sleep(0.1)
    def sendDetectionResult(self, results):
        data = struct.pack("<B", 1) #cmd id
        if self.video_no == -1:
            return
        data += struct.pack("<B", int(self.video_no)) #video no
        for result in results:
            data += struct.pack("<B", result[0])
            data += struct.pack("<H", result[1])
            data += struct.pack("<H", result[2])
            data += struct.pack("<H", result[3])
            data += struct.pack("<H", result[4])
            data += struct.pack("<f", result[5])
            data += struct.pack("<f", result[6])
        self._toolBox.networkManager.sendMsg(b'\x06', data)


if __name__ == '__main__':
    jd = JetsonDetect(0)
    jd.startLoop()
    input()
