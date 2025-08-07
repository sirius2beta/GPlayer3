from flask import Flask, Response
from unet import Unet
from torch2trt import TRTModule
from PIL import Image

import cv2
import numpy as np
import torch
import time
import socket

app = Flask(__name__)

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
cap = cv2.VideoCapture("video/v2_7m_s.mp4")
width, height = 640, 480  # Resize frames to this resolution

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
        _, buffer = cv2.imencode('.jpg', result_bgr)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Route to stream video to browser
@app.route('/')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Optional: get Jetson's IP automatically
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP

# Start Flask server
if __name__ == '__main__':
    ip = get_ip()
    print(f"🌐 Stream available at: http://{ip}:5001")
    app.run(host='0.0.0.0', port=5001)
