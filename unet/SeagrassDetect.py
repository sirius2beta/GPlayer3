
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
import queue as _queue  # 用於捕捉 Full
from datetime import datetime
import csv



from GTool import GTool


#multiprocessing.set_start_method('spawn', force=True)

class SeagrassDetect(GTool):
    def __init__(self, toolbox):
        super().__init__(toolbox)
        self.video_no = -1
        self.enabled = True
        # 取得今天的日期，格式為 YYYY-MM-DD
        today_str = datetime.now().strftime("%Y%m%d")
        seagrass_folder_path = "../record/seagrass"
        self.seagrass_directory = os.path.expanduser(seagrass_folder_path)       # 設定log存放路徑
        self.seagrass_directory = os.path.join(self.seagrass_directory, today_str)  # 例如 output/20250811
        if(not os.path.exists(self.seagrass_directory)):                         # 如果路徑不存在，則建立
            os.makedirs(self.seagrass_directory)                                 # 建立路徑
        
        self.format_setted = False
    def setFormat(self, msg):
        msg_cpy = msg.copy()
        msg_cpy.insert(0, "f")
        self.video_no = msg_cpy[1]
        try:
            self.in_conn.put_nowait(msg_cpy)
        except _queue.Full:
            # 若真的滿了，選擇丟棄舊指令或先清掉再放
            try:
                self.in_conn.get_nowait()
            except Exception:
                pass
            try:
                self.in_conn.put_nowait(msg_cpy)
            except Exception:
                print("Warning: failed to enqueue play msg")

    def play(self):
        try:
            self.in_conn.put_nowait(["p"])
        except _queue.Full:
            # 若真的滿了，選擇丟棄舊指令或先清掉再放
            try:
                self.in_conn.get_nowait()
            except Exception:
                pass
            try:
                self.in_conn.put_nowait(msg_cpy)
            except Exception:
                print("Warning: failed to enqueue play msg")
        #self.in_conn.put(["x"])
        self.video_no = -1

    def stop(self):
        try:
            self.in_conn.put_nowait(["x"])
        except _queue.Full:
            # 若真的滿了，選擇丟棄舊指令或先清掉再放
            try:
                self.in_conn.get_nowait()
            except Exception:
                pass
            try:
                self.in_conn.put_nowait(msg_cpy)
            except Exception:
                print("Warning: failed to enqueue play msg")
        #self.in_conn.put(["x"])
        self.video_no = -1
    def updateIMU(self, msg): #[pitch, roll]
        msg.insert(0, "i")
        self.in_conn.put(msg)
    def sendMsg(self, msg):
        self.in_conn.put(msg)

    def startLoop(self):
        print("Starting SeagrassDetect queue...")
        self.out_conn = multiprocessing.Queue()
        self.in_conn = multiprocessing.Queue()
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
            d = self.out_conn.get()
            self.sendDetectionResult(d)
            pass
            time.sleep(0.1)
    def sendDetectionResult(self, results):
        index_path = os.path.join(self.seagrass_directory, "index.csv")
        with open(index_path, mode='a', newline='') as index_file:
            writer = csv.writer(index_file)
            writer.writerow([results[0], results[1]])
        print("Sending detection results:", results)
    def startRecording(self):
        try:
            self.in_conn.put_nowait(["r"])
        except _queue.Full:
            # 若真的滿了，選擇丟棄舊指令或先清掉再放
            try:
                self.in_conn.get_nowait()
            except Exception:
                pass
            try:
                self.in_conn.put_nowait(["r"])
            except Exception:
                print("Warning: failed to enqueue record msg")
    def stopRecording(self):
        try:
            self.in_conn.put_nowait(["s"])
        except _queue.Full:
            # 若真的滿了，選擇丟棄舊指令或先清掉再放
            try:
                self.in_conn.get_nowait()
            except Exception:
                pass
            try:
                self.in_conn.put_nowait(msg_cpy)
            except Exception:
                print("Warning: failed to enqueue play msg")
        #self.in_conn.put(["x"])
        self.video_no = -1

# Define the streaming generator function


def detectTask(os, conn, input): # Thread that read data from oak camera
    enabled = True
    cap_send = None
    out_send = None
    w = 0
    h = 0
    playing = False
    format = None
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

    # 設定初始時間
    ta = time.time()
    frame_count = 0

    # 取得今天的日期，格式為 YYYY-MM-DD
    today_str = datetime.now().strftime("%Y%m%d")

    # 資料夾路徑（可以依需要修改路徑）
    
    seagrass_folder_path = "../record/seagrass"
    seagrass_directory = os.path.expanduser(seagrass_folder_path)       # 設定log存放路徑
    seagrass_directory = os.path.join(seagrass_directory, today_str)  # 例如 output/20250811
    if(not os.path.exists(seagrass_directory)):                         # 如果路徑不存在，則建立
        os.makedirs(seagrass_directory)                                 # 建立路徑
    
    recording = False
    modelLoaded = False
    while True:
        if not input.empty():
            msg = input.get()
            print("Received message:", msg)
            if msg[0] == "f": # set format
                print("Setting format:", msg)
                format = msg
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
                modelLoaded = True
            elif msg[0] == "p": # play
                if format == None:
                    print("format not set, please set first")
                    continue
                playing = True
            elif msg[0] == "x":

                playing = False
                continue
            elif msg[0] == "i":
                pitch = float(msg[1])  # 直接使用 pitch
                roll = float(msg[2])   # 直接使用 roll
                R0 = getR0(pitch, roll)
                #print(R0)
            elif msg[0] == "r":
                recording = True
            elif msg[0] == "s":
                recording = False
        
        if not recording and not playing:
            time.sleep(0.1)
            continue
            
        if not modelLoaded:
            print("Model not loaded yet, waiting...")
            time.sleep(1)
            continue

        if time.time() - ta < 0.5:
            time.sleep(0.1)
            continue
        ta = time.time()
        ret,frame = cap_send.read()
        #if not ret:
            #print('JetsonDetect: Error!! empty frame')
            #break
        if not ret or frame is None:
            print("⚠️ Camera disconnected, waiting to reconnect...")

            # 等待攝影機重新掛載
            while not os.path.exists(f"/dev/video{msg[0]}"):
                time.sleep(1)

            print("🔄 Camera detected again, reopening...")
            cap_send.release()
            time.sleep(1)  # 等待 UVC driver 初始化
            cap_send = cv2.VideoCapture(video_pipeline, cv2.CAP_GSTREAMER)
            continue
        
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
        if out_send.isOpened() and playing:
            out_send.write(result_bgr)

        # 儲存照片
        if recording:
            frame_count += 1
            file_name = f"seagrass_{frame_count:07d}.jpg"       # 設定檔案名稱
            seagrass_file = os.path.join(seagrass_directory, file_name)         # 檔案路徑
            cv2.imwrite(seagrass_file, result_bgr)
            detect_matrix = [file_name, ratio]
            if conn.empty():
                if not conn.full():
                    conn.put(detect_matrix, block= False)

    out_send.release()
    cap_send.release()

# Start Flask server
if __name__ == '__main__':
    generate_frames()

