import depthai as dai
import time
import argparse
from pathlib import Path

# Default Device mxids (you can change these or use custom mxids via command-line argument)
default_oak_s2_mxid = '18443010E157E40F00'  # OAK-D-S2 mxid
default_oak_sr_mxid = '19443010F156DF1200'  # OAK-SR mxid

# Function to record video from the OAK-D-S2
def record_oak_s2(mxid, duration_seconds=5, output_dir='image_eval_data'):
    # Create pipeline
    pipeline = dai.Pipeline()

    # Define sources and output
    camRgb = pipeline.create(dai.node.ColorCamera)
    videoEnc = pipeline.create(dai.node.VideoEncoder)
    xout = pipeline.create(dai.node.XLinkOut)

    xout.setStreamName('h265')

    # Properties
    camRgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
    videoEnc.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.H265_MAIN)

    # Linking
    camRgb.video.link(videoEnc.input)
    videoEnc.bitstream.link(xout.input)

    # Make sure the destination path is present before starting the recording
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Connect to device with specified mxid and start the pipeline
    with dai.Device(pipeline, dai.DeviceInfo(mxid)) as device:
        # Output queue to get encoded data from the output
        q = device.getOutputQueue(name="h265", maxSize=30, blocking=True)

        # Create a unique timestamp for the filename using time.time()
        timestamp = int(time.time())  # Get seconds since epoch as an integer
        filename = f'{output_dir}/video_{timestamp}.h265'

        # The .h265 file is a raw stream file (not playable yet)
        with open(filename, 'wb') as videoFile:
            print(f"Recording for {duration_seconds} seconds.")
            start_time = time.time()

            try:
                while time.time() - start_time < duration_seconds:
                    h265Packet = q.get()  # Blocking call, waits for new data
                    h265Packet.getData().tofile(videoFile)  # Appends the packet data to the file
            except KeyboardInterrupt:
                # Keyboard interrupt (Ctrl + C) detected
                pass

        print(f"Recording complete. Video saved as {filename}.")

# Function to record video from the OAK-SR
def record_oak_sr(mxid, duration_seconds=5, output_dir='image_eval_data'):
    # Create pipeline
    pipeline = dai.Pipeline()

    # Define sources and output
    camRgb = pipeline.create(dai.node.ColorCamera)
    videoEnc = pipeline.create(dai.node.VideoEncoder)
    xout = pipeline.create(dai.node.XLinkOut)

    xout.setStreamName('h265')

    # Properties
    camRgb.setBoardSocket(dai.CameraBoardSocket.CAM_B)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_800_P)
    videoEnc.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.H265_MAIN)

    # Linking
    camRgb.video.link(videoEnc.input)
    videoEnc.bitstream.link(xout.input)

    # Make sure the destination path is present before starting the recording
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Connect to device with specified mxid and start the pipeline
    with dai.Device(pipeline, dai.DeviceInfo(mxid)) as device:
        # Output queue to get encoded data from the output
        q = device.getOutputQueue(name="h265", maxSize=30, blocking=True)

        # Create a unique timestamp for the filename using time.time()
        timestamp = int(time.time())  # Get seconds since epoch as an integer
        filename = f'{output_dir}/video_{timestamp}.h265'

        # The .h265 file is a raw stream file (not playable yet)
        with open(filename, 'wb') as videoFile:
            print(f"Recording for {duration_seconds} seconds.")
            start_time = time.time()

            try:
                while time.time() - start_time < duration_seconds:
                    h265Packet = q.get()  # Blocking call, waits for new data
                    h265Packet.getData().tofile(videoFile)  # Appends the packet data to the file
            except KeyboardInterrupt:
                # Keyboard interrupt (Ctrl + C) detected
                pass

        print(f"Recording complete. Video saved as {filename}.")

# Main function to parse arguments and run the appropriate recording function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record video from OAK-D-S2 or OAK-SR cameras.")
    parser.add_argument("--camera", choices=["oak_s2", "oak_sr"], required=True, help="Select the camera to record from.")
    parser.add_argument("--duration", type=int, default=5, help="Duration of the recording in seconds.")
    parser.add_argument("--output_dir", type=str, default='image_eval_data', help="Output directory for recorded videos.")
    parser.add_argument("--mxid", type=str, help="Specify the mxid of the camera. If not provided, the default mxid will be used.")

    args = parser.parse_args()

    # Determine which camera to record from and use either the provided mxid or the default one
    if args.camera == "oak_s2":
        mxid = args.mxid if args.mxid else default_oak_s2_mxid
        record_oak_s2(mxid=mxid, duration_seconds=args.duration, output_dir=args.output_dir)
    elif args.camera == "oak_sr":
        mxid = args.mxid if args.mxid else default_oak_sr_mxid
        record_oak_sr(mxid=mxid, duration_seconds=args.duration, output_dir=args.output_dir)
