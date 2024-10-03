import time
from pathlib import Path
import depthai as dai
import argparse

# Default mxids for the cameras
dipro_s2_mxid = '18443010E157E40F00'
dipro_sr_mxid = '19443010F156DF1200'

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
        print(f"Images saved in {output_dir}")

def cam_grab_sr(mxid=dipro_sr_mxid, duration=2, output_dir='image_eval_data'):
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
        print(f"Images saved in {output_dir}")

if __name__ == '__main__':
    # Argument parser to select between cam_grab_s2 and cam_grab_sr
    parser = argparse.ArgumentParser(description='Capture still images from OAK-D camera with different modes.')

    # Positional argument to select function (cam_grab_s2 or cam_grab_sr)
    parser.add_argument('mode', choices=['cam_grab_s2', 'cam_grab_sr'], help='Select which function to run')

    # Add arguments common to both functions
    parser.add_argument('mxid', type=str, help='MXID of the OAK-D camera')
    parser.add_argument('--duration', type=int, default=2, help='Duration of the recording in seconds')
    parser.add_argument('--output_dir', type=str, default='image_eval_data', help='Directory to save the images')

    args = parser.parse_args()

    # Run the appropriate function based on the mode argument
    if args.mode == 'cam_grab_s2':
        cam_grab_s2(mxid=args.mxid, duration=args.duration, output_dir=args.output_dir)
    elif args.mode == 'cam_grab_sr':
        cam_grab_sr(mxid=args.mxid, duration=args.duration, output_dir=args.output_dir)
