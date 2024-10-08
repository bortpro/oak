import time
from pathlib import Path
import depthai as dai

dipro_s2_mxid = '18443010E157E40F00'
dipro_sr = '19443010F156DF1200'

def cam_grab_s2(mxid=dipro_s2_mxid, duration=2, output_dir='image_eval_data'):
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
def cam_grab_sr(mxid, duration=2, output_dir='image_eval_data'):
    # Start defining a pipeline
    pipeline = dai.Pipeline()

    # Define a source - color camera
    camRgb = pipeline.create(dai.node.ColorCamera)
    camRgb.setBoardSocket(dai.CameraBoardSocket.CAM_C)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_800_P)

    # Create encoder to produce JPEG images
    videoEnc = pipeline.create(dai.node.VideoEncoder)
    videoEnc.setDefaultProfilePreset(camRgb.getVideoSize(), camRgb.getFps(), dai.VideoEncoderProperties.Profile.MJPEG)
    camRgb.video.link(videoEnc.input)

    # Create JPEG output
    xoutJpeg = pipeline.create(dai.node.XLinkOut)
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
                    # Use time in milliseconds for the filename as in your original format
                    filename = f"{output_dir}/{int(time.time() * 1)}.jpeg"
                    with open(filename, "wb") as f:
                        f.write(bytearray(encFrame.getData()))

# Example usage:

# cam_grab_s2(mxid=dipro_s2_mxid)
cam_grab_sr(mxid=dipro_sr, duration=3, output_dir='image_eval_data')
