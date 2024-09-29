import time
from pathlib import Path
import depthai as dai

dipro_s2_mxid = '18443010E157E40F00'

def cam_grab(mxid=dipro_s2_mxid, duration=3, output_dir='image_eval_data'):
    # Start defining a pipeline
    pipeline = dai.Pipeline()

    # Define a source - color camera
    camRgb = pipeline.createColorCamera()
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    camRgb.setIspScale(2, 3)

    # Create encoder to produce JPEG images
    videoEnc = pipeline.createVideoEncoder()
    videoEnc.setDefaultProfilePreset(camRgb.getVideoSize(), camRgb.getFps(), dai.VideoEncoderProperties.Profile.MJPEG)
    camRgb.video.link(videoEnc.input)

    # Create JPEG output
    xoutJpeg = pipeline.createXLinkOut()
    xoutJpeg.setStreamName("jpeg")
    videoEnc.bitstream.link(xoutJpeg.input)

    # Connect and start the pipeline with the specified mxid
    with dai.Device(pipeline, dai.DeviceInfo(mxid)) as device:

        # Output queue to get JPEG frames from the output defined above
        qJpeg = device.getOutputQueue(name="jpeg", maxSize=30, blocking=True)

        # Make sure the destination path is present before starting to store the examples
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        end_time = start_time + duration
        while time.time() < end_time:
            # Save JPEG images after the first 1.5 seconds
            if time.time() > (start_time + 1.5):
                for encFrame in qJpeg.tryGetAll():
                    with open(f"{output_dir}/{int(time.time() * 1)}.jpeg", "wb") as f:  # Time as milliseconds
                        f.write(bytearray(encFrame.getData()))

# To test, uncomment the below line:
cam_grab()