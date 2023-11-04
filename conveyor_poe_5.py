import time
import cv2
import depthai as dai
import numpy as np
import blobconverter
import zbar
import eval_loop_notimeout
from conveyor import Conveyor

def move(panel_id, my_speed, direction, corr_40):

    conveyor = Conveyor()
    # my_speed = 20 # set speed to 20 Hz
    conveyor.speed(my_speed)

    if corr_40 == True:
        if my_speed >= 30:
            my_speed = 20
            conveyor.speed(my_speed)

    if direction == 'forw':
        conveyor.forward()

    # if direction == 'reve':
    # reve = True

    DISPLAY = False  # display camera image (set to none on RPi)

    FRAME_SIZE = (1440, 1080)
    FOCUS_VALUE = 175  # 0-255, 0>inf, 150>30cm, 200>10cm, 255>8cm
    FPS = 30

    BLUR = False  # apply blur to image before decoding
    BLUR_KERNEL = (7, 7)  # blur kernel size (width, height)

    BBOX_EXPANSION_PERCENT = 200  # expand bounding box by percent before decoding
    DETECTION_THRESHOLD = 0.9  # minimum confidence threshold for detection

    USE_EXP_LIMIT_TUNING = False  # use exposure limit tuning, will disable manual exposure
    EXP_LIMIT = 8300  # exposure limit in us, either 8300 (default) or 500

    MANUAL_EXPOSURE = True  # set manual exposure
    EXP_TIME = 1000  # sensor exposure time, range 1 to 33000
    SENS_ISO = 1600  # sesnor sensitivity, range 100 to 1600

    # Create pipeline
    pipeline = dai.Pipeline()
    if USE_EXP_LIMIT_TUNING:
        MANUAL_EXPOSURE = False
        if EXP_LIMIT == 500:
            pipeline.setCameraTuningBlobPath('./tuning_exp_limit_500us.bin')
        else:
            pipeline.setCameraTuningBlobPath('./tuning_exp_limit_8300us.bin')

    # Define camera node
    cam = pipeline.create(dai.node.ColorCamera)
    cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    cam.setPreviewSize(FRAME_SIZE)
    cam.setInterleaved(False)
    cam.initialControl.setManualFocus(FOCUS_VALUE)
    cam.setFps(FPS)

    # Define image preprocessor node
    # --> dection model requires 384x384, grayscale input image
    proc = pipeline.create(dai.node.ImageManip)
    proc.initialConfig.setResize(384, 384)
    proc.initialConfig.setFrameType(dai.ImgFrame.Type.GRAY8)
    proc.initialConfig.setKeepAspectRatio(False)

    # Define QR detection model
    nn = pipeline.create(dai.node.MobileNetDetectionNetwork)
    nn.setConfidenceThreshold(DETECTION_THRESHOLD)
    nn.setBlobPath(blobconverter.from_zoo(name="qr_code_detection_384x384", zoo_type="depthai", shaves=6))
    nn.input.setQueueSize(1)
    nn.input.setBlocking(False)

    # Define input nodes
    controlIn = pipeline.create(dai.node.XLinkIn)
    controlIn.setStreamName("control")

    # Define output nodes
    camOut = pipeline.create(dai.node.XLinkOut)
    camOut.setStreamName("camera")
    nnOut = pipeline.create(dai.node.XLinkOut)
    nnOut.setStreamName("nn")

    # Link the nodes
    cam.preview.link(proc.inputImage)
    proc.out.link(nn.input)
    cam.preview.link(camOut.input)
    nn.out.link(nnOut.input)
    controlIn.out.link(cam.inputControl)

    # Define a variable to specify the number of connection retry attempts
    MAX_CONNECTION_RETRIES = 5

    oak_d_poe = "1844301021A55C1200"

    while True:
        try:

            # Connect to a device and start the pipeline
            with dai.Device(pipeline, dai.DeviceInfo(oak_d_poe)) as device:

                class TextHelper:
                    def __init__(self) -> None:
                        self.bg_color = (0, 0, 0)
                        self.color = (255, 255, 255)
                        self.text_type = cv2.FONT_HERSHEY_SIMPLEX
                        self.line_type = cv2.LINE_AA

                    def putText(self, frame, text, coords):
                        cv2.putText(frame, text, coords, self.text_type, 0.8, self.bg_color, 3, self.line_type)
                        cv2.putText(frame, text, coords, self.text_type, 0.8, self.color, 1, self.line_type)

                    def rectangle(self, frame, p1, p2):
                        cv2.rectangle(frame, p1, p2, self.bg_color, 6)
                        cv2.rectangle(frame, p1, p2, self.color, 1)

                def decode(frame, bbox, scanner):
                    # crop frame to bbox area
                    img = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]

                    # zbar requires grayscale images
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                    if BLUR:
                        # remove high frequency noise
                        img = cv2.GaussianBlur(img, BLUR_KERNEL, 0)

                    # decode QR code
                    results = scanner.scan(img)

                    if results:
                        # decoding successful
                        return results[0].data.decode('utf-8')
                    else:
                        # decoding failed
                        return None

                def expandDetection(det, percent=BBOX_EXPANSION_PERCENT):
                    ''' expand bounding box by percent '''
                    percent /= 200
                    w = det.xmax - det.xmin
                    h = det.ymax - det.ymin
                    det.xmin = max(0, det.xmin - w * percent)
                    det.xmax = min(1, det.xmax + w * percent)
                    det.ymin = max(0, det.ymin - h * percent)
                    det.ymax = min(1, det.ymax + h * percent)

                def frameNorm(frame, bbox):
                    ''' de-normalize bounding box coordinates '''
                    normVals = np.full(len(bbox), frame.shape[0])
                    normVals[::2] = frame.shape[1]
                    return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)

                def clamp(num, v0, v1):
                    return max(v0, min(num, v1)

                qCam = device.getOutputQueue("camera", maxSize=4, blocking=False)
                qDet = device.getOutputQueue("nn", maxSize=4, blocking=False)
                controlQueue = device.getInputQueue('control')

                if MANUAL_EXPOSURE:
                    # set manual exposure
                    expTime = EXP_TIME
                    sensIso = SENS_ISO
                    expTime = clamp(expTime, 1, 33000)
                    sensIso = clamp(sensIso, 100, 1600)
                    print("Setting manual exposure -- time:", expTime, "  iso:", sensIso)
                    ctrl = dai.CameraControl()
                    ctrl.setManualExposure(expTime, sensIso)
                    controlQueue.send(ctrl)

                c = TextHelper()
                scanner = zbar.Scanner()

                while True:
                    frame = qCam.get().getCvFrame()
                    detections = qDet.get().detections
                    qr_bbox = [9999, 9999, 9999, 9999]
                    stop_bbox = [999, 999, 999, 999]

                    qr_bbox_left_bound = 50
                    qr_bbox_right_bound = 999

                    if direction == "reve":
                        time.sleep(7)  # allows time for focus
                        conveyor.reverse()

                    for det in detections:
                        # expand and denormalize bbox
                        expandDetection(det)
                        bbox = frameNorm(frame, (det.xmin, det.ymin, det.xmax, det.ymax))

                        # decode QR image
                        text = decode(frame, bbox, scanner)

                        if text == "STOP":
                            print("Text = STOP")
                            stop_bbox = bbox
                            print("STOP bbox: ", stop_bbox)

                        elif text != None and len(text) > 5 and text == panel_id:
                            print("Panel QR code")
                            qr_bbox = bbox
                            print("QR bbox: ", qr_bbox)
                            time.sleep(0.1)
                            conveyor.stop()
                            device.close()
                            return qr_bbox[0]
                        c.putText(frame, text, (bbox[0] + 10, bbox[1] + 40))

                        if qr_bbox[0] - 500 < stop_bbox[0] < qr_bbox[0] + 500:
                            print("ALIGNED")
                            conveyor.stop()
                            device.close()
                            return

                        # add bbox, confidence, and decoded text to image
                        c.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]))
                        c.putText(frame, f"{int(det.confidence * 100)}%", (bbox[0] + 10, bbox[1] + 30))
                        c.putText(frame, text, (bbox[0] + 10, bbox[1] + 60))

                    if DISPLAY:
                        cv2.imshow("Image", frame)

                        if cv2.waitKey(1) == ord('q'):
                            break

                qr_bbox_0 = 9999

                while qr_bbox_0 > 780:
                    frame = qCam.get().getCvFrame()
                    detections = qDet.get().detections
                    qr_bbox = [9999, 9999, 9999, 9999]
                    stop_bbox = [999, 999, 999, 999]

                    qr_bbox_left_bound = 50
                    qr_bbox_right_bound = 999

                    for det in detections:
                        # expand and denormalize bbox
                        expandDetection(det)
                        bbox = frameNorm(frame, (det.xmin, det.ymin, det.xmax, det.ymax))

                        # decode QR image
                        text = decode(frame, bbox, scanner)

                        if text == "STOP":
                            print("Text = STOP")
                            stop_bbox = bbox
                            print("STOP bbox: ", stop_bbox)

                        elif text != None and len(text) > 5 and text == panel_id:
                            print("Panel QR code")
                            qr_bbox = bbox
                            print("QR bbox: ", qr_bbox)
                            qr_bbox_0 = qr_bbox[0]
                            print("QR bbox [0]: ", qr_bbox_0)
                            conveyor = Conveyor()
                            conveyor.speed(19)

                            if qr_bbox_0 > 840:
                                conveyor.reverse()
                                time.sleep(0.25)
                                conveyor.stop()
                                time.sleep(2)
                            elif qr_bbox_0 > 700:
                                conveyor.reverse()
                                time.sleep(0.25)
                                conveyor.stop()
                                time.sleep(2)
                            if qr_bbox_0 < 780:
                                return
                        c.putText(frame, text, (bbox[0] + 10, bbox[1] + 40))

                        # add bbox, confidence, and decoded text to image
                        c.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]))
                        c.putText(frame, f"{int(det.confidence * 100)}%", (bbox[0] + 10, bbox[1] + 30))
                        c.putText(frame, text, (bbox[0] + 10, bbox[1] + 60))

                    if DISPLAY:
                        cv2.imshow("Image", frame)

                        if cv2.waitKey(1) == ord('q'):
                            break
# except RuntimeError as e:
# print(f"Error: {e}")
# print("Camera not detected. Retrying in 5 seconds...")
# time.sleep(5)  # wait for 5 s before retry

# my_id = input("Which panel would you like to move? ")
# my_speed = int(input("What speed would you like to run at? "))
my_id = "11-111-111"
my_speed = 19
qr_bbox_0 = move(my_id, my_speed, 'forw', False)
conveyor.stop()
