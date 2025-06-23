import cv2
import multiprocessing

multiprocessing.set_start_method('spawn', force=True)


def work():
    

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
    from ultralytics import YOLO
    model = YOLO("../engine/xavier/yolov8s.engine")
    while True:
        

        if not cap_send.isOpened():
            print('VideoCapture not opened')
            exit(0)

            
        ret,frame = cap_send.read()
        if not ret:
            print('empty frame')
            break
        if out_send.isOpened():
            
            results = model.track(frame, persist=True)

            # Visualize the results on the frame
            annotated_frame = results[0].plot()
            out_send.write(annotated_frame)

    out_send.release()
    cap_send.release()
if __name__ == '__main__':
    p = multiprocessing.Process(target = work)
    p.start()