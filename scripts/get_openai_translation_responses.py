import json
from PIL import Image
from pathlib import Path
from openai_api import OpenAI_API
from ocr import OCRProcessor
from ocr_enum import OCREngine
from image_diff import image_crop_dialogue_box

ocr = OCRProcessor('en', OCREngine.EASYOCR)
openai = OpenAI_API(translation_model="gpt-4o")

# Specify the directories for input images and outputs
images_folder = Path('../data/data_en/')
output_file = Path('../data/translation_responses_en_gpt4o.json')
dialogue_box_folder = Path('../data/dialogue_boxes_en_gpt4o/')

# Create the dialogue box folder if it doesn't exist
dialogue_box_folder.mkdir(parents=True, exist_ok=True)

translation_responses = {}

# Iterate over all image files in the specified folder
for image_path in images_folder.glob('*.jpg'):
    try:
        image = Image.open(image_path)
        ocr_result, _, _, _ = ocr.ocr_and_highlight(image)

        print(image_path.name)
        print(ocr_result)
        if ocr_result != "":
            response = openai.call_translation_api(ocr_result, 'japanese')
            translation_responses[str(image_path)] = response
            print(response)
        else:
            translation_responses[str(image_path)] = "No dialogue box detected."
    except Exception as e:
        translation_responses[str(image_path)] = f"Error processing image: {e}"

# Save the OCR responses to a JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(translation_responses, f, ensure_ascii=False, indent=4)

print(f"OCR responses saved to {output_file}")
print(f"Cropped dialogue box images saved in {dialogue_box_folder}")
