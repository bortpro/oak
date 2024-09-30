import depthai as dai
import time
import datetime
from pathlib import Path

dipro_s2_mxid = '18443010E157E40F00'  # Add the mxid here

# Function to record video from the OAK-D-S2
def record_oak(mxid=dipro_s2_mxid, duration_seconds=5, output_dir='image_eval_data'):
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

        # Create a unique timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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

# Function to record video at intervals
def record_oak_interval(interval_seconds=10, duration_seconds=5, total_duration_seconds=86400, mxid=dipro_s2_mxid, output_dir='image_eval_data'):
    start_time = time.time()

    while time.time() - start_time < total_duration_seconds:
        # Call the record_oak function with mxid and output_dir
        record_oak(mxid=mxid, duration_seconds=duration_seconds, output_dir=output_dir)

        # Wait for the specified interval before recording again
        time.sleep(interval_seconds)

# Example: Record every 5 seconds for a total duration of 30 seconds
# record_oak_interval(interval_seconds=5, duration_seconds=5, total_duration_seconds=30)
#
record_oak()
