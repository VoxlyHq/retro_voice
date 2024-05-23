from time import sleep
from flask import Flask, request, Response, jsonify, send_from_directory
from PIL import Image
import io
import base64
from process_frames import FrameProcessor
from thread_safe import shared_data_get_data
import time
from video_stream_with_annotations import VideoStreamWithAnnotations

app = Flask(__name__, static_folder='static', static_url_path='/')


frameProcessor = None
last_inboard_frame = None
last_frame_count = 0
crop_height = 90

#TODO all this global code more to a class, and make an instance of it per user

def process_video_thread(translate, enable_cache=False):
    time.sleep(1)  # Wait for 1 second, threading ordering issue, this is not the correct way to fix it
    global video_stream, frameProcessor,crop_height
    print(video_stream)
    while True:
        frame = video_stream.get_latest_frame()
        if frame is not None:
            print("Background task accessing the latest frame...")
            video_stream.process_screenshot(frame, translate=translate, show_image_screen=True, enable_cache=enable_cache) # crop is hard coded make it per user
            time.sleep(1/24)  # Wait for 1 second


def async_process_frame(frame):
    #TODO put the frame onto a queue, in mean time lets only put 1/3 of the frames 
    global last_frame_count, last_inboard_frame, video_stream
    last_frame_count += 1
    last_inboard_frame =  video_stream.preprocess_image(frame, crop_y_coordinate=crop_height) #preprocess all images
    if last_frame_count % 3 == 0:
        video_stream.set_latest_frame(last_inboard_frame)
        if last_frame_count == 100:
            last_frame_count = 0 # paranoia so it doesn't overflow


def init_web(lang="jp", disable_dialog=False, disable_translation=False, enable_cache=False, translate="", textDetector=None):
    global frameProcessor
    frameProcessor = FrameProcessor(lang, disable_dialog,)

    global video_stream
    video_stream = VideoStreamWithAnnotations(background_task=process_video_thread, background_task_args={"translate" : translate, 'enable_cache' : enable_cache},
                                                show_fps=True, crop_y_coordinate=72, frameProcessor=frameProcessor, textDetector=textDetector) #TODO crop should be set later by user
    #video_stream.stop()


dummy_image = Image.new('RGB', (100, 100), (255, 255, 255))
image_changed = False

def set_dialog_file(file):
    global dialog_file
    dialog_file = file

frame_rate = 24 / 3 # 6 fps hack for now
frame_delay = 1 / frame_rate  # Delay to achieve ~24 FPS

def generate_mjpeg():
    global image_changed,last_inboard_frame, video_stream

    print("generate_mjpeg1")
    while True:  # Loop to make it continuous
        print("generate_mjpeg2")
        image_changed = False

        img_byte_arr = io.BytesIO()

        if last_inboard_frame is not None:
            processed_latest_inboard_frame = video_stream.print_annotations_pil(last_inboard_frame) #TODO have translate and cache options
        else:
            processed_latest_inboard_frame = dummy_image

        processed_latest_inboard_frame.save(img_byte_arr, format='JPEG')
            
        print(img_byte_arr)
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + img_byte_arr.getvalue() + b'\r\n')
        time.sleep(frame_delay)  # Wait to control the frame rate

@app.route('/video_mjpeg')
def video_feed():
    return Response(generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload_screenshot', methods=['POST'])
def upload_screenshot():
    global previous_image, image_changed,video_stream
    image_file = request.files['image']
    if image_file:
        image_changed = True
        image = Image.open(image_file.stream).convert('RGB')
#        image.save('static/saved_image.jpg')  # Save images in the static directory
#        last_played, tmp_previous_image, tmp_previous_highlighted_image, annontations, translation = frameProcessor.run_image(image, None, None) #TODO have translate and cache options
        async_process_frame(image)
         #TODO we should have a minimal preprocessing step
        return '', 200
    else:
        return 'File is missing in the form', 400

@app.route('/stream')
def stream():
    def generate():
        global image_changed
        while True:
            if image_changed:
                img_byte_arr = io.BytesIO()
                img = video_stream.get_latest_processed_frame()
                img.save(img_byte_arr, format='JPEG')
                encoded_img = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                yield f'data: data:image/jpeg;base64,{encoded_img}\n\n'
                image_changed = False
            else:
                yield 'data: none\n\n'
                sleep(1) 
    return app.response_class(generate(), mimetype='text/event-stream')

@app.route('/script.json')
def script_json():
    return send_from_directory('static', 'dialogues_en_web.json')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/log')
def log():
    data = shared_data_get_data()
    return f"Data from queue: {data}" if data else ""

@app.route('/highlight')
def highlight():
    line_number = shared_data_get_data()
    return jsonify(highlightedLine=line_number)

def run_server():
    app.run(host='localhost', port=8000, debug=True, use_reloader=False)

# Static file handling is automatically done by Flask for the 'static' folder
if __name__ == '__main__':
    from text_detector_fast import TextDetectorFast
    textDetector = TextDetectorFast("weeeee")    

    init_web("jp", False, False, False, translate="jp,en", textDetector=textDetector)
    app.run(host='localhost', port=8000, debug=True)
