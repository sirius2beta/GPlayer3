
import time
from PIL import Image
import multiprocessing 
import cv2
import numpy as np
import struct
from scipy.spatial.transform import Rotation
import math
from pathlib import Path
import threading
import argparse
import os

from GTool import GTool


class SeagrassDetect(GTool):
    def __init__(self, toolbox):
        super().__init__(toolbox)
        self.video_no = -1
        self.enabled = True
        
        

    def play(self, msg):
        msg_cpy = msg.copy()
        msg_cpy.insert(0, "p")
        self.video_no = msg_cpy[1]
        self.in_conn.put(msg_cpy)

    def stop(self):
        self.in_conn.put(["x"])
        self.video_no = -1
    def updateIMU(self, msg): #[pitch, roll]
        msg.insert(0, "i")
        self.in_conn.put(msg)
    def sendMsg(self, msg):
        self.in_conn.put(msg)

    def startLoop(self):
        print("Starting SeagrassDetect queue...")
        self.out_conn = multiprocessing.Queue(1)
        self.in_conn = multiprocessing.Queue(1)
        print("Starting SeagrassDetect process...")
        self.p = multiprocessing.Process(target = detectTask, args = (self._toolBox.OS, self.out_conn, self.in_conn))
        #self.p = multiprocessing.Process(target = work)
        
        self.p.start()
        print("Starting SeagrassDetect thread...")
        self.outputLoop = threading.Thread(target=self.OutputLoop)
        self.outputLoop.daemon = True
        self.outputLoop.start()
        print("SeagrassDetect initialized")

    def OutputLoop(self): # Thread that send data to the networkmanager
        while True:
            #d = self.out_conn.get()
            #self.sendDetectionResult(d)
            pass
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





# Define the streaming generator function


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
        encode_string = 'x264enc tune=zerolatency speed-preset=superfast'
    elif os == 'focal': # Jetson xavier
        encode_string = 'video/x-raw,format=I420 ! nvvideoconvert ! video/x-raw(memory:NVMM) ! nvv4l2h264enc'
    else:
        return
    # import here to avoid import time in profiling
    import os
    import torch
    from .unet import Unet
    from torch2trt import TRTModule
    # 找到 SeagrassDetect.py 所在的資料夾
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "model", "seagrass_model_resnet50.pth")
    print("model path:", model_path)
    while True:
        if not input.empty():
            msg = input.get()
            print("Received message:", msg)
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
                
                # Initialize Unet model (still needed even if we're loading a TensorRT-optimized model)
                model = Unet(
                    model_path=model_path,  # This path is not important after TRT is loaded
                    num_classes=2,
                    backbone="resnet50",
                    input_shape=[512, 512],
                    mix_type=0,
                    cuda=True
                )
                
                # If model is wrapped in DataParallel (multi-GPU), unwrap it
                if isinstance(model.net, torch.nn.DataParallel):
                    model.net = model.net.module
                # Load the pre-converted TensorRT-optimized model
                print("🔄 Loading TensorRT model...")
                trt_model = TRTModule()
                print(model_path)
                trt_model.load_state_dict(torch.load("unet/model/seagrass_model_resnet50_trt.pth"))
                model.net = trt_model
                print("✅ TensorRT model loaded!")
            elif msg[0] == "x":
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

        if not playing:
            time.sleep(0.1)
            continue    
        ret,frame = cap_send.read()
        if not ret:
            print('JetsonDetect: Error!! empty frame')
            break
        
        t1 = time.time()


        
        # Resize and convert to RGB (PIL uses RGB, OpenCV uses BGR)
        frame = cv2.resize(frame, (640, 480))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(frame_rgb)

        # Run inference using the model
        result_pil, mask = model.detect_image(image_pil, return_mask=True)

        # Calculate seagrass ratio
        total_pixels = mask.size
        seagrass_pixels = np.sum(mask == 0)  # Assuming class 0 = seagrass
        ratio = seagrass_pixels / total_pixels * 100

        # Calculate frame processing latency
        t2 = time.time()
        latency = t2 - t1
        text = f"Seagrass: {ratio:.2f}%, Time: {latency:.2f}s"

        # Convert result back to OpenCV format (BGR)
        result_np = np.array(result_pil)
        result_bgr = cv2.cvtColor(result_np, cv2.COLOR_RGB2BGR)

        # Overlay text info
        cv2.putText(result_bgr, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2, cv2.LINE_AA)

        # Encode frame as JPEG and yield to browser
        if out_send.isOpened():
            out_send.write(result_bgr)


        if conn.empty():
            if not conn.full():
                #conn.put(detect_matrix, block= False)
                pass

    out_send.release()
    cap_send.release()

# Start Flask server
if __name__ == '__main__':
    generate_frames()

