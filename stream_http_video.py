import asyncio
from io import BytesIO
import logging
import atexit
import time

import numpy as np
import av
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaRelay, MediaBlackhole
from quart import Quart, send_from_directory, request, jsonify

app = Quart(__name__,
            static_url_path='',
            static_folder='html')


def generate_encoded():
    # Parameters for the video
    width, height = 640, 480
    fps = 24
    frame_delay = 1 / fps  # Delay to achieve ~24 FPS
    
    # Setup memory buffer
    buffer = BytesIO()

    # Create a video encoder
    codec_name = 'libx264'  # H.264 codec
    output = av.open(buffer, mode='w', format='mpegts')
    stream = output.add_stream(codec_name, rate=fps)
    stream.width = width
    stream.height = height
    stream.pix_fmt = 'yuv420p'
    
    while True: # Infinite loop for continuous streaming
        for angle in range(0, 360, 15):
            # Create a black image
            image = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Define the square's properties
            center = (width // 2, height // 2)
            size = min(width, height) // 4
            rect_pts = np.array([
                [-size, -size],
                [size, -size],
                [size, size],
                [-size, size]
            ], dtype=np.float32)
            
            # Rotate the square
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated_pts = cv2.transform(np.array([rect_pts]), M)[0].astype(np.int32)
            
            # Draw the rotated square
            cv2.fillPoly(image, [rotated_pts], (0, 255, 0))
            
            # Create frame from the image
            frame = av.VideoFrame.from_ndarray(image, format='bgr24')
            for packet in stream.encode(frame):
                output.mux(packet)
                buffer.seek(0)
                chunk = buffer.read()
                buffer.seek(0)
                buffer.truncate()
                yield chunk

        time.sleep(frame_delay)  # Wait to control the frame rate

    # NOTE: this never actually runs due to the infinite loop above
    # Finalize video stream
    for packet in stream.encode(None):
        output.mux(packet)
        buffer.seek(0)
        chunk = buffer.read()
        buffer.seek(0)
        buffer.truncate()
        if chunk:
            yield chunk
    
    # Close everything
    output.close()
    buffer.close()


@app.route('/video')
async def video():
    return generate_encoded(), 200, { 'mimetype': 'video/mp2t' }


class VideoTransformTrack(MediaStreamTrack):
    """
    Custom WebRTC MediaStreamTrack that overlays a watermark onto each video frame.
    """
    kind = "video"

    def __init__(self, track, watermark_data):
        super().__init__()
        self.track = track
        self.watermark_data = watermark_data
        self.alpha = watermark_data[:,:,3] / 255.0 # normalize the alpha channel
        self.inverse_alpha = 1 - self.alpha

    async def recv(self):
        frame = await self.track.recv()
        return self.overlay_watermark(frame, self.watermark_data, self.alpha, self.inverse_alpha)
    
    def overlay_watermark(self, frame, watermark_data, alpha, inverse_alpha):
        frame_data = frame.to_ndarray(format='rgba')

        # place watermark in bottom right corner of the frame
        x_offset = frame_data.shape[1] - watermark_data.shape[1]
        y_offset = frame_data.shape[0] - watermark_data.shape[0]

        for c in range(3):
            frame_data[y_offset:, x_offset:, c] = (alpha * watermark_data[:,:,c] + inverse_alpha * frame_data[y_offset:, x_offset:, c])

        # rebuild frame while preserving timing info
        new_frame = av.VideoFrame.from_ndarray(frame_data, format='rgba')
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame


logger = logging.getLogger("pc")
pcs = set() # current WebRTC  peer connections
relay = MediaRelay()


@app.route('/offer', methods=['POST'])
async def offer():
    """
    This endpoint is used to establish a WebRTC connection between a client
    and the server. Once the connection has been established the client
    will stream video to the server, the server will add a watermark to each
    video frame and stream the modified video back to the client. 
    """
    params = await request.get_json()
    #print('Offer params', params)
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = 'PeerConnection(%s)' % id(pc)
    pcs.add(pc)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    recorder = MediaBlackhole()

    # shouldn't need this
    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info('Connection state is %s', pc.connectionState)
        if pc.connectionState == 'failed':
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        log_info('Track received: %s', track.kind)

        if track.kind == 'video':
            log_info('Creating video transform track')
            watermark_data = load_watermark()
            pc.addTrack(VideoTransformTrack(relay.subscribe(track), watermark_data))
            recorder.addTrack(relay.subscribe(track))

        @track.on("ended")
        async def on_ended():
            log_info('Track %s ended', track.kind)
            await recorder.stop()
    
    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()
    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return jsonify({'sdp': pc.localDescription.sdp, 'type': pc.localDescription.type})


def load_watermark():
    watermark_data = cv2.imread('watermark.png', cv2.IMREAD_UNCHANGED)
    # convert to RGBA if needed
    if watermark_data.shape[2] == 3:
        watermark_data = cv2.cvtColor(watermark_data, cv2.COLOR_BGR2RGBA)
    elif watermark_data.shape[2] == 1:
        watermark_data = cv2.cvtColor(watermark_data, cv2.COLOR_GRAY2BGRA)
    return watermark_data


def on_shutdown():
    # close peer connections
    for pc in list(pcs):
        asyncio.run(pc.close())
        pcs.discard(pc)
    pcs.clear()


@app.route('/')
async def index():
    return await send_from_directory('html', 'video.html')


@app.route('/webrtc')
async def webrtc():
    return await send_from_directory('html', 'webrtc.html')


if __name__ == '__main__':
    atexit.register(on_shutdown)
    app.run(debug=True, threaded=True, port=5001)