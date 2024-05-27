from PIL import Image
from pathlib import Path

from openai_api import OpenAI_API
from ocr import OCRProcessor
from ocr_enum import OCREngine
from image_diff import image_crop_dialogue_box

ocr = OCRProcessor(OCREngine.OPENAI)
openai = OpenAI_API(vision_model="gpt-4o")


image_path = Path('data_en/22_window_capture.jpg')

image = Image.open(image_path)

image_bytes = ocr.process_image(image)

detection_result = ocr.det_easyocr(image_bytes)
if detection_result != []:
    dialogue_box_img = image_crop_dialogue_box(image, detection_result)
    dialogue_box_image_bytes = ocr.process_image(dialogue_box_img)
    response = ocr.ocr_openai(dialogue_box_image_bytes)
    reg_result = response['choices'][0]['message']['content']
    # # TODO : experiment with prompts to get better results
    # if ocr.lang == 'en':
    #     filtered_text = reg_result.removeprefix('The text in the photo reads:').removeprefix('The text in the photo says:').replace('`', '').replace('\n', ' ').replace('"', '').strip()
    # else:
    #     filtered_text = [i for i in reg_result.split("\n\n") if self.extract_non_english_text(i) != ""]
    #     if filtered_text != []:
    #         filtered_text = filtered_text[0].replace('\n', ' ').replace('"', '').replace('`', '')
print(reg_result)