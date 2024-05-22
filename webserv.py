from time import sleep
from flask import Flask, request, jsonify, send_from_directory
from PIL import Image
import io
import base64
from process_frames import FrameProcessor
from thread_safe import shared_data_get_data

app = Flask(__name__, static_folder='static', static_url_path='/')


frameProcessor = None

def init_web(lang="en", disable_dialog=False, disable_translation=False, disable_cache=False):
    FrameProcessor(lang, disable_dialog)

previous_image = Image.new('RGB', (100, 100), (255, 255, 255))
previous_highlighted_image = Image.new('RGB', (100, 100), (255, 255, 255))
image_changed = False

def set_dialog_file(file):
    global dialog_file
    dialog_file = file
    

@app.route('/upload_screenshot', methods=['POST'])
def upload_screenshot():
    global previous_image, previous_highlighted_image, image_changed
    image_file = request.files['image']
    if image_file:
        image = Image.open(image_file.stream).convert('RGB')
        image.save('static/saved_image.jpg')  # Save images in the static directory
        last_played, tmp_previous_image, tmp_previous_highlighted_image, annontations, translation = frameProcessor.run_image(image, None, None) #TODO have translate and cache options
        #closest_match, previous_image, highlighted_image, annotations, translation = frameProcessor.run_image(img, translate=translate,enable_cache=enable_cache)


        if last_played is not None:
            image_changed = True
            previous_image = tmp_previous_image
            previous_highlighted_image = tmp_previous_highlighted_image
            return f"Last played: {last_played}", 200
        else:
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
                previous_highlighted_image.save(img_byte_arr, format='JPEG')
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
    return send_from_directory('.', 'index.html')

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
    init_web("en", False, False, False)
    app.run(host='localhost', port=8000, debug=True)
