import os
import asyncio
from io import BytesIO
import logging
import sys
import time
from http import HTTPStatus
from typing import IO, Any, Dict

from aiohttp import web
import aiohttp_wsgi
from aiohttp_wsgi.utils import parse_sockname
from wsgiref.util import is_hop_by_hop
import numpy as np
import av
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay, MediaBlackhole
import flask
from flask import Flask
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

from text_detector_fast import TextDetectorFast
# from text_detector import TextDetector
from user_video import UserVideo

from .msq import MessageQueue
from .models import db, User
from .oauth import google_oauth_blueprint
from .commands import create_db
from process_frames import FrameProcessor

from PIL import Image


WSGIEnviron = Dict[str, Any]

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
            static_url_path='/',
            static_folder='../static')
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
    scheme = flask.request.scheme
    print(f"Request Scheme: {scheme}")
    
    # Print all the request headers
    headers = flask.request.headers
    print("Request Headers:")
    for header, value in headers.items():
        print(f"{header}: {value}")
    
    # Create a response that includes the scheme and headers
    response = f"Request Scheme: {scheme}\n\nRequest Headers:\n"
    for header, value in headers.items():
        response += f"{header}: {value}\n"
    
    return response


@app.route('/signup', methods=['POST'])
def signup():
    form = flask.request.form
    email = form.get('email')
    password = form.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user:
        return flask.jsonify({ "error": "Unauthorized" }), 401
    
    # create a new local user account
    password_hash = generate_password_hash(password)
    user = User(email=email, password=password_hash)
    db.session.add(user)
    db.session.commit()

    return flask.jsonify({ "email": user.email })


@app.route('/signin', methods=['POST'])
def signin():
    form = flask.request.form
    email = form.get('email')
    password = form.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user is None or not check_password_hash(user.password, password):
        return flask.jsonify({ "error": "Unauthorized" }), 401

    login_user(user)
    return flask.jsonify({ "email": user.email })


@app.route('/user', methods=['GET', 'POST'])
def get_user():
    if current_user.is_authenticated:
        return flask.jsonify({ "email": current_user.email })
    
    return flask.jsonify({ "error": "Unauthorized" }), 401


@app.route('/signout', methods=['POST'])
def signout():
    if current_user.is_authenticated:
        logout_user()
    return flask.jsonify({}), 200


@app.route('/protected')
@login_required
def protected():
    return f'Hello, {current_user.id}! You are logged in.'

@app.route('/app/api/script.json')
@app.route('/script.json')
def script_json():
    return flask.send_from_directory('../static', 'dialogues_jp_web.json')


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
disable_dialog = False #True
disable_translation = False
enable_cache = False
translate = "jp,en" 
debug_bbox = True

class VideoTransformTrack(MediaStreamTrack):
    """
    Custom WebRTC MediaStreamTrack that overlays a watermark onto each video frame.
    """
    kind = "video"

    def __init__(self, track, watermark_data, message_queue=None,crop_height=None):
        global textDetector
        super().__init__()
        self.track = track
        self.watermark_data = watermark_data
        self.alpha = watermark_data[:,:,3] / 255.0 # normalize the alpha channel
        self.inverse_alpha = 1 - self.alpha
        print("making user_video----")
        self.user_video =  UserVideo(lang, disable_dialog, disable_translation, enable_cache, translate, textDetector, debug_bbox=debug_bbox, crop_height=crop_height)
        self.message_queue = message_queue
        print("making user_video done----")
        self.closest_match = []

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

        frame_cropped = self.user_video.preprocess_frame(frame_img)
        self.user_video.async_process_frame(frame_cropped.copy())

        new_frame = av.VideoFrame.from_image(self.user_video.print_annotations(frame_cropped))
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        if self.closest_match is not None and self.user_video.closest_match != self.closest_match and self.user_video.closest_match != 0:
            self.closest_match = self.user_video.closest_match
            print(f"closest match(VTT): {self.closest_match}")
            for element in self.closest_match:
                message = f"selectedLineID {element}"
                self.message_queue.send_message(message)


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
    message_queue = MessageQueue()


    async def send_data(message_queue, data_channel):
        print("starting send_data")
        while True:
            if data_channel == None:
                print("datachannel is none")
            else:
                message = message_queue.receive_message()
                if message:
                    data_channel.send(message)
            await asyncio.sleep(1)

    # shouldn't need this
    @pc.on("datachannel")
    def on_datachannel(channel):
        log_info("Data channel is open")
        asyncio.ensure_future(send_data(message_queue, channel))

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
            crop_height = params.get("crop_height")
            
            if crop_height is not None:
                try:
                    crop_height = int(crop_height)
                except ValueError:
                    crop_height = None
            
            print(f"crop height = {crop_height}")
            vc = VideoTransformTrack(relay.subscribe(track), watermark_data, message_queue, crop_height=crop_height)
            pc.addTrack(vc)
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


# Generate WSGI environ from aiohttp request,
# this is largely based on aiohttp_wsgi.WSGIHandler._get_environ()
# from https://github.com/etianen/aiohttp-wsgi
def _get_wsgi_environ(request: web.Request, body: IO[bytes], content_length: int) -> WSGIEnviron:
        # Resolve the path info.
        path_info = request.match_info.get_info()["path"]
        #path_info = request.match_info["path_info"]
        script_name = request.rel_url.path[:len(request.rel_url.path) - len(path_info)]
        # Special case: If the app was mounted on the root, then the script name will
        # currently be set to "/", which is illegal in the WSGI spec. The script name
        # could also end with a slash if the WSGIHandler was mounted as a route
        # manually with a trailing slash before the path_info. In either case, we
        # correct this according to the WSGI spec by transferring the trailing slash
        # from script_name to the start of path_info.
        if script_name.endswith("/"):
            script_name = script_name[:-1]
            path_info = "/" + path_info
        # Parse the connection info.
        assert request.transport is not None
        server_name, server_port = parse_sockname(request.transport.get_extra_info("sockname"))
        remote_addr, remote_port = parse_sockname(request.transport.get_extra_info("peername"))
        # Detect the URL scheme.
        url_scheme = "http" if request.transport.get_extra_info("sslcontext") is None else "https"
        # Create the environ.
        environ = {
            "REQUEST_METHOD": request.method,
            "SCRIPT_NAME": script_name,
            "PATH_INFO": path_info,
            "RAW_URI": request.raw_path,
            # RAW_URI: Gunicorn's non-standard field
            "REQUEST_URI": request.raw_path,
            # REQUEST_URI: uWSGI/Apache mod_wsgi's non-standard field
            "QUERY_STRING": request.rel_url.raw_query_string,
            "CONTENT_TYPE": request.headers.get("Content-Type", ""),
            "CONTENT_LENGTH": str(content_length),
            "SERVER_NAME": server_name,
            "SERVER_PORT": server_port,
            "REMOTE_ADDR": remote_addr,
            "REMOTE_HOST": remote_addr,
            "REMOTE_PORT": remote_port,
            "SERVER_PROTOCOL": "HTTP/{}.{}".format(*request.version),
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": url_scheme,
            "wsgi.input": body,
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": True,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "asyncio.executor": None,
            "aiohttp.request": request,
        }
        # Add in additional HTTP headers.
        for header_name in request.headers:
            header_name = header_name.upper()
            if not(is_hop_by_hop(header_name)) and header_name not in ("CONTENT-LENGTH", "CONTENT-TYPE"):
                header_value = ",".join(request.headers.getall(header_name))
                environ["HTTP_" + header_name.replace("-", "_")] = header_value
        # All done!
        return environ


async def async_offer(request):
    # Setup a Flask request context to access the Flask session.
    # We don't pass the request body to Flask because we don't
    # need Flask to process it, we just need it to extract cookies
    # from the headers, and run extensions (like Flask-Login).
    content_length = 0
    body = None
    environ = _get_wsgi_environ(request, body, content_length)
    with app.request_context(environ):
        if not current_user.is_authenticated:
            return web.json_response({ 'error': 'Unauthorized' }, status=401)

        print("current user in offer:", current_user.email)

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
    return flask.send_from_directory('../html', 'video.html')


@app.route('/app')
@app.route('/app/webrtc')
def frontend():
    return flask.send_from_directory('../static/app', 'index.html')


def format_filename(number):
    # Format the number with leading zeros to ensure it's four digits
    number_padded = f"{number:04d}"

    # Create the file name using the padded number
    file_name = f"ff4_v1_prologue_{number_padded}.mp3"

    return file_name

@app.route('/audio/<id>.mp3')
def serve_audio(id):
    lang = 'jp'
    return flask.send_from_directory(f"../output_v2_{lang}_elevenlabs/", format_filename(int(id)))




@app.route('/')
def index():
    return flask.redirect('/app')


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