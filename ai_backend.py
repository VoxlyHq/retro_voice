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
    x,y,w,h = body.get("coords")
    viewport = body.get("viewport")
    image = image.resize((w, h))
    print('image width and height', image.width, image.height)

    image.save('tmp_input.png')

    if 'text' in output_format['output']:
        output = ai_service.process_text_mode(image)
        return_output = {"text" : output, "auto" : "auto"}
    if 'image' in output_format['output']:
        output = ai_service.process_image_mode2(image)
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
        self.prev_image = None

        self.prev_translation = None

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
    
    def process_image_mode2(self, image):
        """
        """
        image_object = Image.new("RGBA",
                            (image.width, image.height),
                            (0,0,0,0))
        
        self.video_stream.set_latest_frame(image_object)
        self.video_stream.background_image = None
        self.video_stream.process_screenshot(image, self.translate, show_image_screen=True, enable_cache=self.enable_cache, 
                                             crop_y_coordinate=self.crop_height)

        annotated_image = self.video_stream.print_annotations(image_object)
        annotated_image.save('tmp_before_output.png')
        print(self.video_stream.current_translations)
        # no text found in the image
        if self.video_stream.current_translations is None:
            return image_to_string(image_object)
        
        if self.video_stream.current_annotations == self.prev_translation:
            return image_to_string(self.prev_image)

        if self.video_stream.current_annotations:

            self.prev_translation = self.video_stream.current_annotations
            # get text bbox
            text_position = self.video_stream._calculate_annotation_bounds(self.video_stream.current_annotations)
            translation_adjusted = self.video_stream.adjust_translation_text(self.video_stream.current_translations, self.video_stream.font, self.video_stream.dialogue_bbox_width)
            draw = ImageDraw.Draw(annotated_image)
            font_size = self.video_stream.calculate_font_size(self.video_stream.dialogue_bbox_width, self.video_stream.dialogue_bbox_height, self.video_stream.current_translations)
            text_bbox = draw.textbbox(text_position, translation_adjusted, font=self.video_stream.font,font_size=font_size)
            bboxes_to_extract = []
            for bbox in self.video_stream.current_annotations:
                bbox = bbox[0]
                x1, y1, x2, y2 = bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1]
                bboxes_to_extract.append([x1, y1, x2, y2])
            bboxes_to_extract.append(text_bbox)
            annotated_image = extract_blur_rectangles(annotated_image, bboxes_to_extract)
        annotated_image.save("tmp_output.png")
        self.prev_image = annotated_image
        return image_to_string(annotated_image)
    
    
def extract_blur_rectangles(original_image, bboxes_to_extract):

    # Ensure the image has an alpha channel
    if original_image.mode != 'RGBA':
        original_image = original_image.convert('RGBA')

    # Create a new transparent image of the same size as the original
    result = Image.new('RGBA', original_image.size, (0, 0, 0, 0))

    for rect in bboxes_to_extract:
        extracted_area = original_image.crop(rect)
        result.paste(extracted_area, (rect[0], rect[1]))

    return result

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