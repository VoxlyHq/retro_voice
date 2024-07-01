import io
import time
import logging
from PIL import Image, ImageDraw
import easyocr
from openai_api import OpenAI_API
from image_diff import crop_image_by_bboxes, combine_images
from ocr_enum import OCREngine, DETEngine
import re
from utils import clean_vision_model_output
from text_detector_fast import TextDetectorFast, convert_to_four_points_format
from claude_api import Claude_API, extract_between_tags

# Configure logging
logging.basicConfig(level=logging.INFO)

class OCRProcessor:
    def __init__(self, language='en', method=OCREngine.EASYOCR, detection_method=DETEngine.EASYOCR):
        """
        Initialize the OCRProcessor with the specified language and method.

        :param language: The language for OCR ('en' for English, 'jp' for Japanese)
        :param method: The OCR method to use (easyocr, openai)
        """
        self.lang = language
        self.method = method
        self.detection_method = detection_method

        if self.method == OCREngine.EASYOCR or self.detection_method == DETEngine.EASYOCR:
            self.reader = easyocr.Reader(['en']) if language == 'en' else easyocr.Reader(['en', 'ja'])
        
        self.openai_api = OpenAI_API()
        self.claude_api = Claude_API()

        if self.detection_method == DETEngine.FAST:
            self.fast = TextDetectorFast("pretrained/fast_tiny_ic15_736_finetune_ic17mlt.pth")

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
    
    def det_fast(self, image):
        """
        Perform text detection using FAST.

        :param image: PIL Image
        :return: OCR detection results containing bounding boxes
        """
        result = self.fast.process_single_image(image)
        four_points_format = convert_to_four_points_format(result)
        # reformat to (bbox, text, prob) format
        final_format = [(bbox, '', 0.0) for bbox in four_points_format]
        return final_format
    
    def ocr_openai(self, image_bytes):
        response = self.openai_api.call_vision_api(image_bytes)
        return response
    
    def ocr_claude(self, image_bytes):
        response = self.claude_api.call_vision_api(image_bytes)
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
        else:
            if self.detection_method == DETEngine.FAST:
                detection_result = self.det_fast(image)
            else:
                detection_result = self.det_easyocr(image_bytes)
            if detection_result != []:
                drawable_image = self.draw_highlight(image_bytes, detection_result)
                if self.method == OCREngine.OPENAI:
                    image_bytes = self.process_image(image)
                    response = self.ocr_openai(image_bytes)
                    if response.get('choices', None) is None:
                        reg_result = ''
                    else:
                        reg_result = response['choices'][0]['message']['content']
                    # TODO : experiment with prompts to get better results
                    filtered_text = clean_vision_model_output(reg_result)
                if self.method == OCREngine.CLAUDE:
                    image_bytes = self.claude_api.preprocess(image)
                    response = self.ocr_claude(image_bytes)
                    filtered_text = ' '.join(extract_between_tags('original_text', response))
                return filtered_text, drawable_image, detection_result, response
            return '', None, [], {}

    def det_and_highlight(self, image):
        """
        Perform Text Detection on the image and highlight bounding boxes.

        :param image: The input PIL Image
        :return: Tuple containing the annotated image, and Detection result
        """
        image_bytes = self.process_image(image)
        if self.detection_method == DETEngine.FAST:
            result = self.det_fast(image)
        else:
            result = self.det_easyocr(image_bytes)
        drawable_image = self.draw_highlight(image_bytes, result)
        return drawable_image, result

    def combine_overlapping_rectangles(self, rectangles):
        """
        Combine overlapping rectangles from a list of rectangles.

        Args:
            rectangles (list of tuples): A list of rectangles, each defined by a tuple of two points (top-left and bottom-right).

        Returns:
            list of tuples: A list of combined rectangles.
        """
        combined_rectangles = list(rectangles)  # Make a copy of the input list

        while True:
            overlap_found = False
            new_rectangles = []

            i = 0
            while i < len(combined_rectangles):
                rect1 = combined_rectangles[i]
                combined = False
                for j in range(i + 1, len(combined_rectangles)):
                    rect2 = combined_rectangles[j]
                    if self.check_overlap(rect1, rect2):
                        combined_rect = self.combine_rectangles(rect1, rect2)
                        new_rectangles.append(combined_rect)
                        combined_rectangles.pop(j)
                        overlap_found = True
                        combined = True
                        break

                if not combined:
                    new_rectangles.append(rect1)
                i += 1

            combined_rectangles = new_rectangles

            if not overlap_found:
                break

        return combined_rectangles

    def check_overlap(self, rect1, rect2):
        """
        Check if two rectangles overlap.

        Args:
            rect1 (tuple of tuples): First rectangle defined by two points (top-left and bottom-right).
            rect2 (tuple of tuples): Second rectangle defined by two points (top-left and bottom-right).

        Returns:
            bool: True if the rectangles overlap, False otherwise.
        """
        x1, y1 = rect1[0]
        x2, y2 = rect1[1]
        x3, y3 = rect2[0]
        x4, y4 = rect2[1]
        if x2 < x3 or x4 < x1 or y2 < y3 or y4 < y1:
            return False
        return True

    def combine_rectangles(self, rect1, rect2):
        """
        Combine two overlapping rectangles into a single rectangle.

        Args:
            rect1 (tuple of tuples): First rectangle defined by two points (top-left and bottom-right).
            rect2 (tuple of tuples): Second rectangle defined by two points (top-left and bottom-right).

        Returns:
            tuple of tuples: A combined rectangle defined by two points (top-left and bottom-right).
        """
        x1 = min(rect1[0][0], rect2[0][0])
        y1 = min(rect1[0][1], rect2[0][1])
        x2 = max(rect1[1][0], rect2[1][0])
        y2 = max(rect1[1][1], rect2[1][1])
        return [(x1, y1), (x2, y2)]

    def postprocess_bbox(self, results):
        """
        Combine overlapping bounding boxes and their associated text.

        Args:
            results (list of tuples): A list of results, each containing a bounding box, recognized text and probability.

        Returns:
            list of tuples: A list of combined bounding boxes and concatenated text.
        """
        text_regions = []
        for result in results:
            bbox = result[0]  # Get the bounding box coordinates
            x1, y1 = int(bbox[0][0]), int(bbox[0][1])
            x2, y2 = int(bbox[2][0]), int(bbox[2][1])
            points = [(x1, y1), (x2, y2)]
            # If needed, add thresholds to ignore tiny text fields based on height and width
            text = result[1]  # Get the recognized text
            text_regions.append((points, text))
        
        # Combine overlapping rectangles into a single rectangle
        combined_regions = self.combine_overlapping_rectangles([region[0] for region in text_regions])
        
        # Update the combined regions with the recognized text
        final_regions = []
        for combined_region in combined_regions:
            text = ""
            for region in text_regions:
                if self.check_overlap(region[0], combined_region):
                    text += region[1] + " "
            text = text.strip()
            final_regions.append((combined_region, text))
        
        return final_regions


    def run_ocr(self, image):
        """
        Perform OCR on the image, log the time taken, and return the results.

        :param image: The input PIL Image
        :return: Tuple containing the concatenated detected text, annotated image, annotations and recognition result
        """
        start_time = time.time()
        output_text, highlighted_image, annotations, reg_result = self.ocr_and_highlight(image)
        annotations = self.postprocess_bbox(annotations)
        end_time = time.time()
        logging.info(f"OCR found text: {output_text}")
        logging.info(f"Time taken: {end_time - start_time} seconds")
        return output_text, highlighted_image, annotations, reg_result

    def run_det(self, image):
        """
        Perform Text Detection on the image, log the time taken, and return the results.

        :param image: The input PIL Image
        :return: Tuple containing the  annotated image and annotations 
        """
        start_time = time.time()
        highlighted_image, annotations = self.det_and_highlight(image)
        annotations = self.postprocess_bbox(annotations)
        end_time = time.time()
        logging.info(f"Detection found bboxes: {len(annotations)}")
        logging.info(f"Time taken: {end_time - start_time} seconds")
        return  highlighted_image, annotations

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
    ocr_processor = OCRProcessor('en', method=OCREngine.CLAUDE, detection_method=DETEngine.FAST)
    
    image_path = 'tests/unit_test_data/windows_eng_ff4.png'
    image = Image.open(image_path).convert('RGB')
    output_text, highlighted_image, annotations,response = ocr_processor.ocr_and_highlight(image)
    highlighted_image.save("tests/unit_test_data/highlighted_windows_eng_ff4.jpg")
    print(f'{output_text=}')
    print(f'{annotations=}')
    print('Output Image is saved as unit_test_data/highlighted_windows_eng_ff4.jpg')