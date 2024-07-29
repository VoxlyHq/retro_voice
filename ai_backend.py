from flask import Flask, request
import time
from urllib.parse import urlparse
from PIL import Image, ImageDraw, ImageFilter
import base64
import io
import json

from ocr_enum import OCREngine, DETEngine, TranslationEngine
from text_detector_fast import TextDetectorFast
from process_frames import FrameProcessor
from video_stream_with_annotations import VideoStreamWithAnnotations

app = Flask(__name__)

def load_image(image_data):
    if type(image_data) == Image.Image:
        return image_data
    byte_data = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(byte_data))
    image = image.convert("RGBA")
    return image

def image_to_string(img):
    output = io.BytesIO()
    img.save(output, format="png")
    string = output.getvalue()
    return base64.b64encode(string).decode('utf-8')

@app.route("/", methods=["GET"])
def index():
    return """
    <html>
        <head><title></title></head>
        <body>Hello, Retroarch AI Backend</body>
    </html>
    """

@app.route("/", methods=["POST"])
def process_request():
    start_time = time.time()

    print('URL : ', end = '\t')
    print(request.url)

    query = urlparse(request.url).query
    print('query :\t', query)

    if query:
        output_format = dict(q.split('=') for q in query.split("&"))

    print('output_format:\t', output_format)

    data = request.get_data()
    
    data = json.loads(data)
    
    print('coords', data['coords'])
    print('viewport', data['viewport'])

    result = _process_request(data, output_format)
    print('Request took: ', time.time() - start_time)
    if result.get('text', None):
        print('result:\t', result['text'])

    output = json.dumps(result)

    response = app.response_class(
        response=output,
        status=200,
        mimetype='application/json'
    )

    return response

def _process_request(body, output_format):

    image_data = body.get("image")

    image = load_image(image_data).convert('RGB')
    image = image.resize((1162, 895))
    print('image width and height', image.width, image.height)

    image.save('tmp_input.png')

    if 'text' in output_format['output']:
        output = ai_service.process_text_mode(image)
        return_output = {"text" : output, "auto" : "auto"}
    if 'image' in output_format['output']:
        output = ai_service.process_image_mode1(image)
        return_output = {"image": output, "auto" : "auto"}

    return return_output

class AI_SERVICE:
    def __init__(self, lang, disable_dialog, disable_translation, enable_cache, translate, textDetector, debug_bbox, show_fps, crop_height, method, detection_method, translation_method):
        self.lang = lang
        self.disable_dialog = disable_dialog
        self.disable_translation = disable_translation
        self.enable_cache = enable_cache
        self.translate = translate
        self.textDetector = textDetector
        self.debug_bbox = debug_bbox
        self.show_fps = show_fps
        self.crop_height = crop_height
        self.method = method
        self.detection_method = detection_method
        self.translation_method = translation_method

        self.frameProcessor = FrameProcessor(self.lang, self.disable_dialog, method=self.method, detection_method=self.detection_method, translation_method=self.translation_method)

        self.video_stream = VideoStreamWithAnnotations(background_task=None,
                                              background_task_args={"translate" : self.translate, 'enable_cache' : self.enable_cache, 'crop_y_coordinate' : self.crop_height},
                                              show_fps=self.show_fps, crop_y_coordinate=self.crop_height, frameProcessor=self.frameProcessor,
                                              textDetector=self.textDetector, debug_bbox=self.debug_bbox)
        
    def process_text_mode(self, image):
        self.video_stream.set_latest_frame(image)
        self.video_stream.process_screenshot(image, self.translate, show_image_screen=True, enable_cache=self.enable_cache, 
                                             crop_y_coordinate=self.crop_height)
        translation = self.video_stream.current_translations.replace('\n', ' ')
        return translation
    
    def process_image_mode1(self, image):
        """
        no background image and transparent becomes background image
        """
        image_object = Image.new("RGBA",
                            (image.width, image.height),
                            (0,0,0,0))
        
        self.video_stream.set_latest_frame(image_object)
        self.video_stream.background_image = None
        self.video_stream.process_screenshot(image, self.translate, show_image_screen=True, enable_cache=self.enable_cache, 
                                             crop_y_coordinate=self.crop_height)

        annotated_image = self.video_stream.print_annotations(image_object)
        annotated_image.save("tmp_output.png")
        return image_to_string(annotated_image)

if __name__ == "__main__":
    local_server_host = "localhost"
    local_server_port = 4404

    lang = "jp"
    disable_dialog = True
    disable_translation = False
    enable_cache = False
    translate = "jp,en"
    textDetector = TextDetectorFast("")
    debug_bbox = False
    show_fps = True
    crop_height = 0
    method = OCREngine.EASYOCR
    detection_method = DETEngine.FAST
    translation_method = TranslationEngine.OPENAI

    ai_service = AI_SERVICE(lang=lang, disable_dialog=disable_dialog, disable_translation=disable_translation, 
               enable_cache=enable_cache, translate=translate, textDetector=textDetector, 
               debug_bbox=debug_bbox, show_fps=show_fps, crop_height=crop_height, 
               method=method, detection_method=detection_method, translation_method=translation_method)

    app.run(host=local_server_host, port=local_server_port, debug=True)