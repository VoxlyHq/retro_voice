import io
import time
import logging
from PIL import Image, ImageDraw
import easyocr
from openai_api import OpenAI_API
from image_diff import image_crop_dialogue_box
from ocr_enum import OCREngine
import re
from utils import clean_vision_model_output

# Configure logging
logging.basicConfig(level=logging.INFO)

class OCRProcessor:
    def __init__(self, language='en', method=OCREngine.EASYOCR):
        """
        Initialize the OCRProcessor with the specified language and method.

        :param language: The language for OCR ('en' for English, 'jp' for Japanese)
        :param method: The OCR method to use (easyocr, openai)
        """
        self.lang = language
        self.reader = easyocr.Reader(['en']) if language == 'en' else easyocr.Reader(['en', 'ja'])
        self.openai_api = OpenAI_API()
        self.method = method

    def process_image(self, image):
        """
        Convert a PIL Image to bytes.

        :param image: The input PIL Image
        :return: The image as bytes
        """
        byte_buffer = io.BytesIO()
        image.save(byte_buffer, format='JPEG')
        image_bytes = byte_buffer.getvalue()
        return image_bytes

    def draw_highlight(self, image_bytes, result, outline_color="red", text_color="yellow", outline_width=2):
        """
        Draw bounding boxes and text on the image based on OCR results.

        :param image_bytes: The image in bytes
        :param result: OCR result containing bounding boxes and text
        :param outline_color: Color of the bounding box outline
        :param text_color: Color of the text
        :param outline_width: Width of the bounding box outline
        :return: The annotated image as a PIL Image
        """
        drawable_image = Image.open(io.BytesIO(image_bytes))
        draw = ImageDraw.Draw(drawable_image)
        for bbox, text, prob in result:
            try:
                top_left, bottom_right = tuple(map(int, bbox[0])), tuple(map(int, bbox[2]))
                draw.rectangle([top_left, bottom_right], outline=outline_color, width=outline_width)
                draw.text(top_left, text, fill=text_color)
            except Exception as e:
                logging.error(f"Error drawing rectangle - {top_left} - {bottom_right}: {e}")
        return drawable_image

    def filter_ocr_result(self, result, exclude_keywords=['retroarch', 'retronrch']):
        """
        Filter out unwanted OCR results based on keywords.

        :param result: OCR result containing bounding boxes and text
        :param exclude_keywords: List of keywords to filter out
        :return: Filtered OCR result
        """
        return [(bbox, text, prob) for bbox, text, prob in result if not any(keyword in text.lower() for keyword in exclude_keywords)]

    def ocr_easyocr(self, image_bytes, detail=1):
        """
        Perform OCR using easyocr.

        :param image_bytes: The image in bytes
        :param detail: Level of detail for OCR results
        :return: OCR result containing bounding boxes and text
        """
        return self.reader.readtext(image_bytes, detail=detail)
    
    def det_easyocr(self, image_bytes):
        """
        Perform text detection using easyocr.

        :param image_bytes: The image in byes
        :return:OCR result containing bounding boxes
        """
        return self.reformat(self.reader.detect(image_bytes))
    
    def ocr_openai(self, image_bytes):
        response = self.openai_api.call_vision_api(image_bytes)
        return response


    def ocr_and_highlight(self, image):
        """
        Perform OCR on the image and highlight the detected text.

        :param image: The input PIL Image
        :return: Tuple containing the concatenated detected text, annotated image, and OCR result
        """
        image_bytes = self.process_image(image)
        if self.method == OCREngine.EASYOCR:
            result = self.ocr_easyocr(image_bytes, detail=1)
            filtered_result = self.filter_ocr_result(result)
            drawable_image = self.draw_highlight(image_bytes, filtered_result)
            filtered_text = ' '.join([text for _, text, _ in filtered_result])
            return filtered_text, drawable_image, filtered_result, None
        elif self.method == OCREngine.OPENAI:
            detection_result = self.det_easyocr(image_bytes)
            if detection_result != []:
                dialogue_box_img = image_crop_dialogue_box(image, detection_result)
                dialogue_box_image_bytes = self.process_image(dialogue_box_img)
                drawable_image = self.draw_highlight(image_bytes, detection_result)
                response = self.ocr_openai(dialogue_box_image_bytes)
                if response.get('choices', None) is None:
                    reg_result = ''
                else:
                    reg_result = response['choices'][0]['message']['content']
                # TODO : experiment with prompts to get better results
                filtered_text = clean_vision_model_output(reg_result)
                return filtered_text, drawable_image, detection_result, response
            return '', None, [], {}

    def run_ocr(self, image):
        """
        Perform OCR on the image, log the time taken, and return the results.

        :param image: The input PIL Image
        :return: Tuple containing the concatenated detected text, annotated image, annotations and recognition result
        """
        start_time = time.time()
        output_text, highlighted_image, annotations, reg_result = self.ocr_and_highlight(image)
        end_time = time.time()
        logging.info(f"OCR found text: {output_text}")
        logging.info(f"Time taken: {end_time - start_time} seconds")
        return output_text, highlighted_image, annotations, reg_result

    def reformat(self,det_res):
        '''
        reformat detection result as the details 1 format of easyocr readtext output
        :params: det_res a tuple containing (a list of detection bbox)
        :returns: reformatted output 
        '''
        reformatted_output = []
        for x1, x2, y1, y2 in det_res[0][0]:
            reformatted_output.append(([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], '', 0.0))

        return reformatted_output

    def extract_non_english_text(self, response):
        """
        Extracts non-English characters from the provided response.
        
        :param response: The response containing the text
        :return: The extracted non-English text
        """
        # Use a regular expression to match non-English characters
        match = re.findall(r'[^\x00-\x7F]+', response)
        if match:
            non_english_text = ' '.join(match)
            return non_english_text.strip()
        return ""


if __name__ == "__main__":
    ocr_processor = OCRProcessor()
    
    image_path = 'unit_test_data/windows_eng_ff4.png'
    image = Image.open(image_path).convert('RGB')
    output_text, highlighted_image, annotations = ocr_processor.ocr_and_highlight(image)
    highlighted_image.save("unit_test_data/highlighted_windows_eng_ff4.jpg")
    print(f'{output_text=}')
    print(f'{annotations=}')
    print('Output Image is saved as unit_test_data/highlighted_windows_eng_ff4.png')