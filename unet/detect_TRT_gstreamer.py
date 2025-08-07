from flask import Flask, Response
from unet import Unet
from torch2trt import TRTModule
from PIL import Image

import cv2
import numpy as np
import torch
import time
import socket



host_IP = "100.127.124.45"

# Initialize Unet model (still needed even if we're loading a TensorRT-optimized model)
model = Unet(
    model_path="model/seagrass_model_resnet50.pth",  # This path is not important after TRT is loaded
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
trt_model.load_state_dict(torch.load("model/seagrass_model_resnet50_trt.pth"))
model.net = trt_model
print("✅ TensorRT model loaded!")

# Open the video file
#cap = cv2.VideoCapture("video/v2_7m_s.mp4")

width, height = 640, 480  # Resize frames to this resolution
# GStreamer pipeline for real-time processing
video = "video2"

video_pipeline = f'v4l2src device=/dev/{video} ! video/x-raw, format=YUY2, width={width}, height={height}, framerate={30}/1 ! videoconvert ! appsink'
cap = cv2.VideoCapture(video_pipeline, cv2.CAP_GSTREAMER)
w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = cap.get(cv2.CAP_PROP_FPS)
encode_string = 'video/x-raw,format=I420 ! nvvideoconvert ! video/x-raw(memory:NVMM) ! nvv4l2h264enc'
out_send = cv2.VideoWriter(f'appsrc ! videoconvert ! {encode_string} ! rtph264pay pt=96 config-interval=1 ! udpsink host={host_IP} port={5201}'\
    ,cv2.CAP_GSTREAMER\
    ,0\
    , int(fps)\
    , (int(width), int(height))\
    , True)

# Define the streaming generator function
def generate_frames():
    while True:
        t1 = time.time()
        success, frame = cap.read()
        if not success:
            break  # Stop when video ends or read fails

        
        # Resize and convert to RGB (PIL uses RGB, OpenCV uses BGR)
        frame = cv2.resize(frame, (width, height))
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
            out_send.write(frame)


# Start Flask server
if __name__ == '__main__':
    generate_frames()

