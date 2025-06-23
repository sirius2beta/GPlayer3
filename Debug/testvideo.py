import cv2
video_pipeline = f'v4l2src device=/dev/video0 ! video/x-raw, format=YUY2, width=640, height=480, framerate=30/1 ! videoconvert ! appsink'
cap_send = cv2.VideoCapture(video_pipeline, cv2.CAP_GSTREAMER)
w = cap_send.get(cv2.CAP_PROP_FRAME_WIDTH)
h = cap_send.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = cap_send.get(cv2.CAP_PROP_FPS)
out_send = cv2.VideoWriter(f'appsrc ! videoconvert ! video/x-raw,format=I420 ! nvvideoconvert ! video/x-raw(memory:NVMM) ! nvv4l2h264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host=192.168.0.110 port=5201'\
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
        out_send.write(frame)

out_send.release()
cap_send.release()
