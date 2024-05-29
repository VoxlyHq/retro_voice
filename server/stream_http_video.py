import os
import asyncio
from io import BytesIO
import logging
import atexit
from threading import Thread
import time

from aiohttp import web
import aiohttp_wsgi
import numpy as np
import av
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay, MediaBlackhole
from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, url_for
from flask_login import LoginManager, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from text_detector_fast import TextDetectorFast
# from text_detector import TextDetector
from user_video import UserVideo

from .models import db, User
from .oauth import google_oauth_blueprint
from .commands import create_db
from process_frames import FrameProcessor

from PIL import Image

from dotenv import load_dotenv
load_dotenv()

default_dev_db_path = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dev.sqlite3')

class Config(object):
    # used for signing the Flask session cookie
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or default_dev_db_path
    print(f"SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Google Auth2 stuff can be obtained from https://console.developers.google.com
    # OAuth2 client ID from Google Console
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    # OAuth2 client secret from Google Console
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME") #or 'http'


ROOT = os.path.dirname(__file__)


app = Flask(__name__,
            static_url_path='',
            static_folder='../html')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.secret_key = Config.SECRET_KEY
app.config.from_object(Config)
print(app.config)
app.register_blueprint(google_oauth_blueprint, url_prefix="/login")
db.init_app(app)

app.cli.add_command(create_db)


# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'google.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/test')
def test():
    # Print the request scheme
    scheme = request.scheme
    print(f"Request Scheme: {scheme}")
    
    # Print all the request headers
    headers = request.headers
    print("Request Headers:")
    for header, value in headers.items():
        print(f"{header}: {value}")
    
    # Create a response that includes the scheme and headers
    response = f"Request Scheme: {scheme}\n\nRequest Headers:\n"
    for header, value in headers.items():
        response += f"{header}: {value}\n"
    
    return response

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('webrtc'))


@app.route('/protected')
@login_required
def protected():
    return f'Hello, {current_user.id}! You are logged in.'


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
def video():
    return generate_encoded(), 200, { 'mimetype': 'video/mp2t' }


#TODO do a better then this, i just want this loaded at boot, but it will slow down if you dont need it lol
# textDetector = TextDetector('frozen_east_text_detection.pb')
textDetector = TextDetectorFast("", checkpoint="pretrained/fast_base_tt_640_finetune_ic17mlt.pth")    
#TODO do one per user
lang = "jp" #hard code all options for now
disable_dialog = True
disable_translation = False
enable_cache = False
translate = "jp,en" 
debug_bbox = True
user_video = UserVideo(lang, disable_dialog, disable_translation, enable_cache, translate, textDetector, debug_bbox=debug_bbox)

class VideoTransformTrack(MediaStreamTrack):
    """
    Custom WebRTC MediaStreamTrack that overlays a watermark onto each video frame.
    """
    kind = "video"

    def __init__(self, track, watermark_data):
        global textDetector, user_video
        super().__init__()
        self.track = track
        self.watermark_data = watermark_data
        self.alpha = watermark_data[:,:,3] / 255.0 # normalize the alpha channel
        self.inverse_alpha = 1 - self.alpha
        print("making user_video----")
        self.user_video = user_video
        print("making user_video done----")
        

    async def recv(self):
        try:
            frame = await self.track.recv()
            #return self.overlay_watermark(frame, self.watermark_data, self.alpha, self.inverse_alpha)
            return self.process_frame(frame)
        except Exception as e:
            print(f"exception - {e}")
            logging.error("An error occurred: %s", e)
            raise


    def process_frame(self, frame):
        frame_img = av.VideoFrame.to_image(frame)

        self.user_video.async_process_frame(frame_img)

        new_frame = av.VideoFrame.from_image(self.user_video.get_immediate_frame())
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        return new_frame

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


async def handle_offer(params):
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection(RTCConfiguration([RTCIceServer('stun:stun.l.google.com:19302')]))
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

    return pc.localDescription


# NOTE: This route is currently handled by aiohttp server
#@app.post('/offer')
def offer():
    """
    This endpoint is used to establish a WebRTC connection between a client
    and the server. Once the connection has been established the client
    will stream video to the server, the server will add a watermark to each
    video frame and stream the modified video back to the client. 
    """

    # While Flask does support async route handlers (with flask[async] extension),
    # it will kill the WebRTC connections spawned by the handler as soon as the
    # handler returns a response. The workaround is to use asyncio to run
    # the async part of the handler and then keep the WebRTC connections alive
    # on another thread... it's not clear though if the WebRTC stuff will get
    # cleaned up properly when the client disconnects, might need to do some
    # additional housekeeping!
    #
    # See https://github.com/aiortc/aiortc/issues/792 for additional context. 
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    localDescription = loop.run_until_complete(handle_offer(request.get_json()))
    Thread(target = loop.run_forever).start()
    return jsonify({'sdp': localDescription.sdp, 'type': localDescription.type})


async def async_offer(request):
    params = await request.json()
    localDescription = await handle_offer(params)
    return web.json_response({
        'sdp': localDescription.sdp,
        'type': localDescription.type
    })

def load_watermark():
    watermark_data = cv2.imread(os.path.join(ROOT, 'watermark.png'), cv2.IMREAD_UNCHANGED)
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


async def on_async_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


@app.route('/mpegts')
def mpegts():
    return send_from_directory('../html', 'video.html')


@app.route('/webrtc')
def webrtc():
    return send_from_directory('../html', 'webrtc.html')


@app.route('/')
def index():
    return render_template('index.j2')


#atexit.register(on_shutdown)

def make_aiohttp_app(flask_app):
    wsgi_handler = aiohttp_wsgi.WSGIHandler(flask_app)
    aioapp = web.Application()
    aioapp.on_shutdown.append(on_async_shutdown)
    aioapp.router.add_post('/offer', async_offer)
    aioapp.router.add_route('*', '/{path_info:.*}', wsgi_handler)
    return aioapp

aioapp = make_aiohttp_app(app)

if __name__ == '__main__':
    web.run_app(aioapp, host='localhost', port=5001)