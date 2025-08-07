from flask import Flask, Response
import cv2
from PIL import Image
import numpy as np
from unet import Unet

app = Flask(__name__)

model = Unet(
    model_path = "model/seagrass_model_4000.pth",
    num_classes = 2,
    backbone = "vgg",
    input_shape = [512, 512],
    mix_type = 0,
    cuda = True
)

cap = cv2.VideoCapture(r"video/v2_7m_s.mp4")
width, height = 640, 480

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.resize(frame, (width, height))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(frame_rgb)

        result_pil, mask = model.detect_image(image_pil, return_mask=True)

        total_pixels = mask.size
        seagrass_pixels = np.sum(mask == 0)
        ratio = seagrass_pixels / total_pixels * 100
        text = "Seagrass: {:.2f}%".format(ratio)

        result_np = np.array(result_pil)
        result_bgr = cv2.cvtColor(result_np, cv2.COLOR_RGB2BGR)

        cv2.putText(result_bgr, text, (10, 30),  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        _, buffer = cv2.imencode('.jpg', result_bgr)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
