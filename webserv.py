from time import sleep
from flask import Flask, request, Response, jsonify, send_from_directory
from PIL import Image
import io
import base64
from thread_safe import shared_data_get_data
import time

from user_video import UserVideo

app = Flask(__name__, static_folder='static', static_url_path='/')


user_video = None

def init_web(lang="jp", disable_dialog=False, disable_translation=False, enable_cache=False, translate="", textDetector=None, debug_bbox=False):
    global user_video #TODO do one per user
    user_video = UserVideo(lang, disable_dialog, disable_translation, enable_cache, translate, textDetector, debug_bbox=debug_bbox, crop_height=72)

image_changed = False

def set_dialog_file(file):
    global dialog_file
    dialog_file = file

frame_rate = 24 / 3 # 6 fps hack for now
frame_delay = 1 / frame_rate  # Delay to achieve ~24 FPS

def generate_mjpeg():
    global image_changed, user_video

    print("generate_mjpeg1")
    while True:  # Loop to make it continuous
        print("generate_mjpeg2")
        image_changed = False

        if user_video.has_frame():
            img = user_video.print_annotations(user_video.last_inboard_frame)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')


            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + img_byte_arr.getvalue() + b'\r\n')
        time.sleep(1)  # Wait to control the frame rate

@app.route('/video_mjpeg')
def video_feed():
    return Response(generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload_screenshot', methods=['POST'])
def upload_screenshot():
    global previous_image, image_changed,video_stream
    image_file = request.files['image']
    if image_file:
        image = Image.open(image_file.stream).convert('RGB')
#        image.save('static/saved_image.jpg')  # Save images in the static directory
#        last_played, tmp_previous_image, tmp_previous_highlighted_image, annontations, translation = frameProcessor.run_image(image, None, None) #TODO have translate and cache options
        user_video.async_process_frame(user_video.preprocess_frame(image))
        image_changed = True
         #TODO we should have a minimal preprocessing step
        return '', 200
    else:
        return 'File is missing in the form', 400

@app.route('/stream')
def stream():
    def generate():
        global image_changed #TODO remove this
        while True:
            if image_changed:
                img_byte_arr = io.BytesIO()
                img = user_video.get_latest_processed_frame()
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
    textDetector = TextDetectorFast(checkpoint="checkpoints/checkpoint_60ep.pth.tar")    
    # from text_detector import TextDetector
    # textDetector = TextDetector('frozen_east_text_detection.pb')

    # Print bounding box annotations for debugging dialogue box
    debug_bbox = True

    init_web("jp", False, False, False, translate="jp,en", textDetector=textDetector, debug_bbox=debug_bbox)
    app.run(host='localhost', port=8000, debug=True)
