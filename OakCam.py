#!/usr/bin/env python3

import cv2
import depthai as dai
import math
import numpy as np
import threading
import time
from GTool import GTool
from pathlib import Path


# Open up connection with oak-D S2 camera for depth detection

nnBlobPath = str((Path(__file__).parent / Path('models/yolo-v4-tiny-tf_openvino_2021.4_6shave.blob')).resolve().absolute())

# Tiny yolo v3/4 label texts
labelMap = [
    "person",         "bicycle",    "car",           "motorbike",     "aeroplane",   "bus",           "train",
    "truck",          "boat",       "traffic light", "fire hydrant",  "stop sign",   "parking meter", "bench",
    "bird",           "cat",        "dog",           "horse",         "sheep",       "cow",           "elephant",
    "bear",           "zebra",      "giraffe",       "backpack",      "umbrella",    "handbag",       "tie",
    "suitcase",       "frisbee",    "skis",          "snowboard",     "sports ball", "kite",          "baseball bat",
    "baseball glove", "skateboard", "surfboard",     "tennis racket", "bottle",      "wine glass",    "cup",
    "fork",           "knife",      "spoon",         "bowl",          "banana",      "apple",         "sandwich",
    "orange",         "broccoli",   "carrot",        "hot dog",       "pizza",       "donut",         "cake",
    "chair",          "sofa",       "pottedplant",   "bed",           "diningtable", "toilet",        "tvmonitor",
    "laptop",         "mouse",      "remote",        "keyboard",      "cell phone",  "microwave",     "oven",
    "toaster",        "sink",       "refrigerator",  "book",          "clock",       "vase",          "scissors",
    "teddy bear",     "hair drier", "toothbrush"
]


syncNN = True

class OakCam(GTool):
    def __init__(self, toolBox):
        super().__init__(toolBox)
        self.distances = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.lock = threading.Lock() # lock for internect communication
        
        self.hasCamera = False
        self.detectionMetric = [
        #   label[0], x[1], y[2], width[3], height[4], dist[5]
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
        ]
        self.d_label = 0
        self.d_x1 = 0
        self.d_y1 = 0
        self.d_x2 = 0
        self.d_y2 = 0
        timeout = 0
        try:
            pipeline = dai.Pipeline()
            # Connect to device and start pipeline
            with dai.Device(pipeline) as device:
                
                self.hasCamera = True
        except Exception as e:
            print(f"[*] OakCam: not connected: {e}")
        
    def startLoop(self):
        if self.hasCamera:
            self.inputLoop = threading.Thread(target=self.InputLoop)
            self.inputLoop.daemon = True
            self.inputLoop.start()
            self.outputLoop = threading.Thread(target=self.OutputLoop)
            self.outputLoop.daemon = True
            self.outputLoop.start()
    def OutputLoop(self): # Thread that send data to the networkmanager
        while True:
            self.lock.acquire()
            distances = self.distances
            self.lock.release()
            #self.toolBox.mavManager.send_distance_sensor_data(7, int(min(distances[:3])))
            #self.toolBox.mavManager.send_distance_sensor_data(0, int(min(distances[3:6])))
            #self.toolBox.mavManager.send_distance_sensor_data(1, int(min(distances[6:])))
            
            self.toolBox().sensorManager.send_detection_result(self.detectionMetric)



    def InputLoop(self): # Thread that read data from oak camera
        
        out = cv2.VideoWriter(f'appsrc ! videoconvert ! omxh264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host=192.168.0.99 port=5201'
        , cv2.CAP_GSTREAMER, 0, 30, (int(416),int(416)), True)
        out2 = cv2.VideoWriter(f'appsrc ! videoconvert ! omxh264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host=192.168.0.99 port=5202'
        , cv2.CAP_GSTREAMER, 0, 30, (int(640),int(400)), True)
        # Create pipeline
        # Create pipeline
        pipeline = dai.Pipeline()

        # Define sources and outputs
        camRgb = pipeline.create(dai.node.ColorCamera)
        spatialDetectionNetwork = pipeline.create(dai.node.YoloSpatialDetectionNetwork)
        monoLeft = pipeline.create(dai.node.MonoCamera)
        monoRight = pipeline.create(dai.node.MonoCamera)
        stereo = pipeline.create(dai.node.StereoDepth)
        nnNetworkOut = pipeline.create(dai.node.XLinkOut)

        xoutRgb = pipeline.create(dai.node.XLinkOut)
        xoutNN = pipeline.create(dai.node.XLinkOut)
        xoutDepth = pipeline.create(dai.node.XLinkOut)

        xoutRgb.setStreamName("rgb")
        xoutNN.setStreamName("detections")
        xoutDepth.setStreamName("depth")
        nnNetworkOut.setStreamName("nnNetwork")

        # Properties
        camRgb.setPreviewSize(416, 416)
        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camRgb.setInterleaved(False)
        camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        camRgb.setPreviewKeepAspectRatio(False)

        monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        monoLeft.setCamera("left")
        monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        monoRight.setCamera("right")

        # setting node configs
        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        # Align depth map to the perspective of RGB camera, on which inference is done
        stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)
        stereo.setOutputSize(monoLeft.getResolutionWidth(), monoLeft.getResolutionHeight())
        stereo.setSubpixel(True)

        spatialDetectionNetwork.setBlobPath(nnBlobPath)
        spatialDetectionNetwork.setConfidenceThreshold(0.5)
        spatialDetectionNetwork.input.setBlocking(False)
        spatialDetectionNetwork.setBoundingBoxScaleFactor(0.5)
        spatialDetectionNetwork.setDepthLowerThreshold(100)
        spatialDetectionNetwork.setDepthUpperThreshold(5000)

        # Yolo specific parameters
        spatialDetectionNetwork.setNumClasses(80)
        spatialDetectionNetwork.setCoordinateSize(4)
        spatialDetectionNetwork.setAnchors([10,14, 23,27, 37,58, 81,82, 135,169, 344,319])
        spatialDetectionNetwork.setAnchorMasks({ "side26": [1,2,3], "side13": [3,4,5] })
        spatialDetectionNetwork.setIouThreshold(0.5)

        # Linking
        monoLeft.out.link(stereo.left)
        monoRight.out.link(stereo.right)

        camRgb.preview.link(spatialDetectionNetwork.input)
        if syncNN:
            spatialDetectionNetwork.passthrough.link(xoutRgb.input)
        else:
            camRgb.preview.link(xoutRgb.input)

        spatialDetectionNetwork.out.link(xoutNN.input)

        stereo.depth.link(spatialDetectionNetwork.inputDepth)
        spatialDetectionNetwork.passthroughDepth.link(xoutDepth.input)
        spatialDetectionNetwork.outNetwork.link(nnNetworkOut.input)
        try:
            # Connect to device and start pipeline
            with dai.Device(pipeline) as device:
                
                self.hasCamera = True
                # Output queues will be used to get the rgb frames and nn data from the outputs defined above
                previewQueue = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
                detectionNNQueue = device.getOutputQueue(name="detections", maxSize=4, blocking=False)
                depthQueue = device.getOutputQueue(name="depth", maxSize=4, blocking=False)
                networkQueue = device.getOutputQueue(name="nnNetwork", maxSize=4, blocking=False)

                startTime = time.monotonic()
                counter = 0
                fps = 0
                color = (255, 255, 255)
                printOutputLayersOnce = True

                while True:
                    
                    inPreview = previewQueue.get()
                    inDet = detectionNNQueue.get()
                    depth = depthQueue.get()
                    inNN = networkQueue.get()

                    if printOutputLayersOnce:
                        toPrint = 'Output layer names:'
                        for ten in inNN.getAllLayerNames():
                            toPrint = f'{toPrint} {ten},'
                        print(toPrint)
                        printOutputLayersOnce = False

                    frame = inPreview.getCvFrame()
                    depthFrame = depth.getFrame() # depthFrame values are in millimeters

                    depth_downscaled = depthFrame[::4]
                    if np.all(depth_downscaled == 0):
                        min_depth = 0  # Set a default minimum depth value when all elements are zero
                    else:
                        min_depth = np.percentile(depth_downscaled[depth_downscaled != 0], 1)
                    max_depth = np.percentile(depth_downscaled, 99)
                    depthFrameColor = np.interp(depthFrame, (min_depth, max_depth), (0, 255)).astype(np.uint8)
                    depthFrameColor = cv2.applyColorMap(depthFrameColor, cv2.COLORMAP_HOT)

                    counter+=1
                    current_time = time.monotonic()
                    if (current_time - startTime) > 1 :
                        fps = counter / (current_time - startTime)
                        counter = 0
                        startTime = current_time

                    detections = inDet.detections

                    # If the frame is available, draw bounding boxes on it and show the frame
                    height = frame.shape[0]
                    width  = frame.shape[1]
                    count = 0
                    self.detectionMetric = [
                    #   label[0], x[1], y[2], width[3], height[4], dist[5]
                        0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0,
                    ]
                    for detection in detections:
                        roiData = detection.boundingBoxMapping
                        roi = roiData.roi
                        roi = roi.denormalize(depthFrameColor.shape[1], depthFrameColor.shape[0])
                        topLeft = roi.topLeft()
                        bottomRight = roi.bottomRight()
                        xmin = int(topLeft.x)
                        ymin = int(topLeft.y)
                        xmax = int(bottomRight.x)
                        ymax = int(bottomRight.y)
                        cv2.rectangle(depthFrameColor, (xmin, ymin), (xmax, ymax), color, 1)

                        # Denormalize bounding box
                        x1 = int(detection.xmin * width)
                        x2 = int(detection.xmax * width)
                        y1 = int(detection.ymin * height)
                        y2 = int(detection.ymax * height)
                        try:
                            label = labelMap[detection.label]
                        except:
                            label = detection.label
                        #cv2.putText(frame, str(label), (x1 + 10, y1 + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                        #cv2.putText(frame, "{:.2f}".format(detection.confidence*100), (x1 + 10, y1 + 35), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                        #cv2.putText(frame, f"X: {x1}", (x1 + 10, y1 + 50), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                        #cv2.putText(frame, f"Y: {int(detection.spatialCoordinates.y)} mm", (x1 + 10, y1 + 65), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                        #cv2.putText(frame, f"Z: {int(detection.spatialCoordinates.z)} mm", (x1 + 10, y1 + 80), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)

                        #cv2.rectangle(frame, (x1, y1), (x2, y2), color, cv2.FONT_HERSHEY_SIMPLEX)
                        if count < 5:
                            self.detectionMetric[count*6] = detection.label
                            self.detectionMetric[count*6+1] = x1
                            self.detectionMetric[count*6+2] = y1
                            self.detectionMetric[count*6+3] = x2 - x1
                            self.detectionMetric[count*6+4] = y2 - y1
                            self.detectionMetric[count*6+5] = int(detection.spatialCoordinates.z)
                        count += 1

                    cv2.putText(frame, "NN fps: {:.2f}".format(fps), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color)
                    
                    out.write(frame)
                    out2.write(depthFrameColor)

        except Exception as e:
            print(f"[*] OakCam: not connected: {e}")
            self.hasCamera = False
