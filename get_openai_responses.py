import json
from PIL import Image
from pathlib import Path
from openai_api import OpenAI_API
from ocr import OCRProcessor
from ocr_enum import OCREngine
from image_diff import image_crop_dialogue_box

ocr = OCRProcessor(OCREngine.OPENAI)
openai = OpenAI_API(vision_model="gpt-4o")

# Specify the directories for input images and outputs
images_folder = Path('../data/data_jp/')
output_file = Path('../data/ocr_responses_jp_gpt4o.json')
dialogue_box_folder = Path('../data/dialogue_boxes_jp_gpt4o/')

# Create the dialogue box folder if it doesn't exist
dialogue_box_folder.mkdir(parents=True, exist_ok=True)

ocr_responses = {}

# Iterate over all image files in the specified folder
for image_path in images_folder.glob('*.jpg'):
    try:
        image = Image.open(image_path)
        image_bytes = ocr.process_image(image)
        detection_result = ocr.det_easyocr(image_bytes)
        
        if detection_result != []:
            dialogue_box_img = image_crop_dialogue_box(image, detection_result)
            dialogue_box_image_bytes = ocr.process_image(dialogue_box_img)
            response = ocr.ocr_openai(dialogue_box_image_bytes)
            reg_result = response['choices'][0]['message']['content']
            
            ocr_responses[str(image_path)] = reg_result

            # Save the cropped dialogue box image
            dialogue_box_image_path = dialogue_box_folder / image_path.name
            dialogue_box_img.save(dialogue_box_image_path)
        else:
            ocr_responses[str(image_path)] = "No dialogue box detected."
    except Exception as e:
        ocr_responses[str(image_path)] = f"Error processing image: {e}"

# Save the OCR responses to a JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(ocr_responses, f, ensure_ascii=False, indent=4)

print(f"OCR responses saved to {output_file}")
print(f"Cropped dialogue box images saved in {dialogue_box_folder}")
