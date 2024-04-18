
import depthai as dai
import time
import datetime

def record_oak(duration_seconds=5):
    # Create pipeline
    pipeline = dai.Pipeline()

    # Define sources and output
    camRgb = pipeline.create(dai.node.ColorCamera)
    videoEnc = pipeline.create(dai.node.VideoEncoder)
    xout = pipeline.create(dai.node.XLinkOut)

    xout.setStreamName('h265')

    # Properties
    camRgb.setBoardSocket(dai.CameraBoardSocket.CAM_B)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
    videoEnc.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.H265_MAIN)

    # Linking
    camRgb.video.link(videoEnc.input)
    videoEnc.bitstream.link(xout.input)

    # Connect to device and start pipeline
    with dai.Device(pipeline) as device:
        # Output queue will be used to get the encoded data from the output defined above
        q = device.getOutputQueue(name="h265", maxSize=30, blocking=True)

        cameras = device.getConnectedCameraFeatures()
        for camera in cameras:
            print(f"Camera socket: {camera['socket']}, Sensor: {camera['sensorName']}")

        # Create a unique timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'video_{timestamp}.h265'

        # The .h265 file is a raw stream file (not playable yet)
        with open(filename, 'wb') as videoFile:
            print(f"Recording for {duration_seconds} seconds.")
            start_time = time.time()

            try:
                while time.time() - start_time < duration_seconds:
                    h265Packet = q.get()  # Blocking call, will wait until new data has arrived
                    h265Packet.getData().tofile(videoFile)  # Appends the packet data to the opened file
            except KeyboardInterrupt:
                # Keyboard interrupt (Ctrl + C) detected
                pass

        print(f"Recording complete. Video saved as {filename}. ")

# Call the function with the default duration (5 seconds)
# record_oak()


def record_oak_interval(interval_seconds=10,duration_seconds=5,total_duration_seconds=86400):
    start_time = time.time()

    while time.time() - start_time < total_duration_seconds:
        record_oak(duration_seconds)  # Call the record_oak function

        # Wait for the specified interval before recording again
        time.sleep(interval_seconds)

# Example: Record every 5 seconds for a total duration of 30 seconds
record_oak_interval(interval_seconds=5, duration_seconds = 5, total_duration_seconds=30)


