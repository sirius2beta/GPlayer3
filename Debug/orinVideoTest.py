import cv2

from ultralytics import YOLO

model = YOLO("yolov8s.engine")
video_pipeline = f'v4l2src device=/dev/video0 ! video/x-raw, format=YUY2, width=1280, height=720, framerate=10/1 ! videoconvert ! appsink'
cap_send = cv2.VideoCapture(video_pipeline, cv2.CAP_GSTREAMER)
w = cap_send.get(cv2.CAP_PROP_FRAME_WIDTH)
h = cap_send.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = cap_send.get(cv2.CAP_PROP_FPS)
out_send = cv2.VideoWriter(f'appsrc ! videoconvert ! x264enc tune=zerolatency speed-preset=superfast ! rtph264pay pt=96 config-interval=1 ! udpsink host=192.168.0.110 port=5201'\
    ,cv2.CAP_GSTREAMER\
    ,0\
    , int(fps)\
    , (int(w), int(h))\
    , True)
    
while True:
    

    if not cap_send.isOpened():
        print('VideoCapture not opened')
        exit(0)

        
    ret,frame = cap_send.read()
    if not ret:
        print('empty frame')
        break
    if out_send.isOpened():
        results = model.predict(frame, conf=0.5)
        annotated_frame = frame.copy()
        bbox = results[0].boxes.xyxy
        cls_name = results[0].names
        classes = results[0].boxes.cls
        for box, clas in zip(bbox,classes):
            x1, y1, x2, y2 = box
            
            color = (0, 0, 255)
            cv2.rectangle(annotated_frame,(int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
            cv2.putText(annotated_frame,
                f'{cls_name[int(clas)]}', (int(x1), int(y1) - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75, [225, 255, 255], thickness=2)
        # Visualize the results on the frame
        #annotated_frame = results[0].plot()
        out_send.write(annotated_frame)

out_send.release()
cap_send.release()
# gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw, format=YUY2, width=640, height=480, framerate=30/1 ! videoconvert ! x264enc tune=zerolatency speed-preset=superfast ! rtph264pay pt=96 config-interval=1 ! udpsink host=192.168.0.110 port=5201