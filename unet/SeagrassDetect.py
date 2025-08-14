import os
import time
import csv
import cv2
import math

import queue as _queue
import numpy as np
from PIL import Image
from datetime import datetime
from pathlib import Path
import multiprocessing
import threading

from GTool import GTool

class SeagrassDetect(GTool):
    def __init__(self, toolbox):
        super().__init__(toolbox)
        self.video_no = -1
        self.enabled = True
        self.format_setted = False
        self.is_playing = False
        self.is_recording = False

        today_str = datetime.now().strftime("%Y%m%d")
        base_path = "../record/seagrass"
        self.seagrass_directory = os.path.join(os.path.expanduser(base_path), today_str)
        os.makedirs(self.seagrass_directory, exist_ok=True)

        self.csv_lock = threading.Lock()

    def safe_enqueue(self, queue, msg):
        """Safely put a message into a queue without blocking."""
        try:
            queue.put_nowait(msg)
        except _queue.Full:
            try:
                queue.get_nowait()
            except Exception:
                pass
            try:
                queue.put_nowait(msg)
            except Exception:
                print(f"Warning: failed to enqueue message {msg}")

    def setFormat(self, msg):
        msg_cpy = ["f"] + msg
        self.video_no = msg[0]
        self.safe_enqueue(self.in_conn, msg_cpy)

    def play(self):
        self.safe_enqueue(self.in_conn, ["p"])
        self.is_playing = True
    def stop(self):
        self.safe_enqueue(self.in_conn, ["x"])
        self.video_no = -1
        self.is_playing = False

    def updateIMU(self, msg):
        self.safe_enqueue(self.in_conn, ["i"] + msg)

    def sendMsg(self, msg):
        self.safe_enqueue(self.in_conn, msg)

    def startLoop(self):
        self.out_conn = multiprocessing.Queue()
        self.in_conn = multiprocessing.Queue()

        self.p = multiprocessing.Process(
            target=detectTask,
            args=(self._toolBox.OS, self.out_conn, self.in_conn, self.seagrass_directory)
        )
        self.p.start()

        self.outputLoop = threading.Thread(target=self.OutputLoop, daemon=True)
        self.outputLoop.start()
        print("SeagrassDetect initialized")

    def OutputLoop(self):
        while True:
            results = self.out_conn.get()
            self.sendDetectionResult(results)
            time.sleep(0.05)

    def sendDetectionResult(self, results):
        index_path = os.path.join(self.seagrass_directory, "index.csv")
        with self.csv_lock:
            with open(index_path, mode='a', newline='') as f:
                csv.writer(f).writerow([results[0], results[1]])
        print("Detection results:", results)

    def startRecording(self):
        self.safe_enqueue(self.in_conn, ["r"])
        self.is_recording = True

    def stopRecording(self):
        self.safe_enqueue(self.in_conn, ["s"])
        self.is_recording = False





def detectTask(os_type, conn, input_q, seagrass_dir):
    import torch
    from torch2trt import TRTModule
    from .unet import Unet

    def load_model():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        trt_path = os.path.join(current_dir, "model", "seagrass_model_resnet50_trt.pth")
        model_path = os.path.join(current_dir, "model", "seagrass_model_resnet50.pth")
        model = Unet(model_path=model_path, num_classes=2, backbone="resnet50",
                    input_shape=[512, 512], mix_type=0, cuda=True)

        if isinstance(model.net, torch.nn.DataParallel):
            model.net = model.net.module

        trt_model = TRTModule()
        trt_model.load_state_dict(torch.load(trt_path))
        model.net = trt_model
        print("✅ TensorRT model loaded!")
        return model


    def reopen_camera(device_id, pipeline):
        while not os.path.exists(f"/dev/video{device_id}"):
            time.sleep(1)
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        time.sleep(1)
        return cap

    
        encode_string = {
            'jammy': 'x264enc tune=zerolatency speed-preset=superfast',
            'focal': 'video/x-raw,format=I420 ! nvvideoconvert ! video/x-raw(memory:NVMM) ! nvv4l2h264enc'
        }.get(os_type, None)

        if not encode_string:
            print("Unsupported OS type")
            return
    encode_string = {
            'jammy': 'x264enc tune=zerolatency speed-preset=superfast',
            'focal': 'video/x-raw,format=I420 ! nvvideoconvert ! video/x-raw(memory:NVMM) ! nvv4l2h264enc'
        }.get(os_type, None)

    if not encode_string:
        print("Unsupported OS type")
        return
    cap_send = None
    out_send = None
    playing = False
    recording = False
    model_loaded = False
    model = None
    video_pipeline = ""
    device_id = 0
    frame_count = 0
    last_infer_time = time.time()

    while True:
        # Process incoming commands
        while not input_q.empty():
            msg = input_q.get()
            print("Received:", msg)

            if msg[0] == "f":
                device_id, vformat, width, height, fps, host, port = msg[1:]
                video_pipeline = f'v4l2src device=/dev/video{device_id} ! video/x-raw, format=YUY2, width={width}, height={height}, framerate={fps}/1 ! videoconvert ! appsink'
                cap_send = reopen_camera(device_id, video_pipeline)

                out_send = cv2.VideoWriter(
                    f'appsrc ! videoconvert ! {encode_string} ! rtph264pay pt=96 config-interval=1 ! udpsink host={host} port={port}',
                    cv2.CAP_GSTREAMER, 0, int(fps), (int(width), int(height)), True
                )

                if not model_loaded:
                    model = load_model()
                    model_loaded = True

            elif msg[0] == "p":
                playing = True
            elif msg[0] == "x":
                playing = False
            elif msg[0] == "r":
                recording = True
            elif msg[0] == "s":
                recording = False

        if not (recording or playing):
            time.sleep(0.05)
            continue

        if time.time() - last_infer_time < 0.5:
            time.sleep(0.02)
            continue
        last_infer_time = time.time()

        ret, frame = cap_send.read()
        if not ret or frame is None:
            print("⚠️ Camera disconnected...")
            cap_send = reopen_camera(device_id, video_pipeline)
            continue

        t1 = time.time()
        frame = cv2.resize(frame, (640, 480))
        image_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        result_pil, mask = model.detect_image(image_pil, return_mask=True)

        seagrass_pixels = np.sum(mask == 0)
        ratio = seagrass_pixels / mask.size * 100
        latency = time.time() - t1

        result_bgr = cv2.cvtColor(np.array(result_pil), cv2.COLOR_RGB2BGR)
        cv2.putText(result_bgr, f"Seagrass: {ratio:.2f}%, Time: {latency:.2f}s",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if out_send.isOpened() and playing:
            out_send.write(result_bgr)

        if recording:
            frame_count += 1
            file_name = f"seagrass_{frame_count:07d}.jpg"
            cv2.imwrite(os.path.join(seagrass_dir, file_name), result_bgr)
            if not conn.full():
                conn.put([file_name, ratio], block=False)

    if out_send: out_send.release()
    if cap_send: cap_send.release()
