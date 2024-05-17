import io
import time
import logging
from PIL import Image, ImageDraw
import easyocr
from openai_api import OpenAI_API

# Configure logging
logging.basicConfig(level=logging.INFO)

class OCRProcessor:
    def __init__(self, language='en', method=1):
        """
        Initialize the OCRProcessor with the specified language and method.

        :param language: The language for OCR ('en' for English, 'jp' for Japanese)
        :param method: The OCR method to use (1 for easyocr, future methods can be added)
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

    def ocr_and_highlight(self, image):
        """
        Perform OCR on the image and highlight the detected text.

        :param image: The input PIL Image
        :return: Tuple containing the concatenated detected text, annotated image, and OCR result
        """
        image_bytes = self.process_image(image)
        if self.method == 1:
            result = self.ocr_easyocr(image_bytes, detail=1)
            filtered_result = self.filter_ocr_result(result)
            drawable_image = self.draw_highlight(image_bytes, filtered_result)
            filtered_text = ' '.join([text for _, text, _ in filtered_result])
            return filtered_text, drawable_image, filtered_result

    def run_ocr(self, image):
        """
        Perform OCR on the image, log the time taken, and return the results.

        :param image: The input PIL Image
        :return: Tuple containing the concatenated detected text, annotated image, and OCR result
        """
        start_time = time.time()
        output_text, highlighted_image, annotations = self.ocr_and_highlight(image)
        end_time = time.time()
        logging.info(f"OCR found text: {output_text}")
        logging.info(f"Time taken: {end_time - start_time} seconds")
        return output_text, highlighted_image, annotations

if __name__ == "__main__":
    ocr_processor = OCRProcessor()
    
    image_path = 'unit_test_data/windows_eng_ff4.png'
    image = Image.open(image_path).convert('RGB')
    output_text, highlighted_image, annotations = ocr_processor.ocr_and_highlight(image)
    highlighted_image.save("unit_test_data/highlighted_windows_eng_ff4.jpg")
    print(f'{output_text=}')
    print(f'{annotations=}')
    print('Output Image is saved as unit_test_data/highlighted_windows_eng_ff4.png')