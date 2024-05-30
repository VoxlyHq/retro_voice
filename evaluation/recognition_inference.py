import os
import io
import sys
import json
import time
import argparse
from PIL import Image
from dataset import Dataset
from ocr import OCRProcessor
from ocr_enum import OCREngine
import matplotlib.pyplot as plt
from image_diff import image_crop_dialogue_box

class RecognitionInference:
    def __init__(self, ocr_method):
        self.ocr_method = ocr_method.lower()
        if self.ocr_method not in ['easyocr', 'openai']:
            raise ValueError("Unsupported OCR method. Supported methods are 'easyocr' and 'openai'.")
        self.ocr_processor_eng = OCRProcessor(language='en', method=OCREngine.EASYOCR if self.ocr_method == 'easyocr' else OCREngine.OPENAI)
        self.ocr_processor_jp = OCRProcessor(language='jp', method=OCREngine.EASYOCR if self.ocr_method == 'easyocr' else OCREngine.OPENAI)

    def process_dataset(self, dataset, output_json, log_file):
        results = []
        with open(log_file, 'w') as log:
            for idx in range(len(dataset)):
                image, name_of_game, lang, number = dataset[idx]
                # Initialize OCRProcessor with the appropriate language for each image
                ocr_processor = OCRProcessor(language=lang, method=OCREngine.EASYOCR if self.ocr_method == 'easyocr' else OCREngine.OPENAI)
                start_time = time.time()
                output_text, highlighted_image, annotations, reg_result = ocr_processor.run_ocr(image)
                end_time = time.time()
                time_taken = end_time - start_time
                result = {
                    "filename": dataset.image_files[idx].name,
                    "time_taken": time_taken,
                    "text": output_text,
                    "annotations": annotations
                }
                results.append(result)
                
                # Write the output to the log file after each image is processed
                log.write(f"Processed {result['filename']}\n")
                log.write(f"Time taken: {result['time_taken']} seconds\n")
                log.write(f"Detected text: {result['text']}\n")
                log.write(f"Annotations: {result['annotations']}\n")
                log.write("\n")

        with open(output_json, 'w') as json_file:
            json.dump(results, json_file, indent=4)


    def visualize_single_image(self, image, annotations):
        if self.ocr_method == 'easyocr':
            image_bytes = self.ocr_processor_eng.process_image(image)
            drawable_image = self.ocr_processor_eng.draw_highlight(image_bytes, annotations)
        else:
            detection_result = self.ocr_processor_eng.det_easyocr(self.ocr_processor_eng.process_image(image))
            dialogue_box_img = image_crop_dialogue_box(image, detection_result)
            dialogue_box_image_bytes = self.ocr_processor_eng.process_image(dialogue_box_img)
            response = self.ocr_processor_eng.ocr_openai(dialogue_box_image_bytes)
            drawable_image = self.ocr_processor_eng.draw_highlight(dialogue_box_image_bytes, detection_result)

        plt.figure(figsize=(10, 10))
        plt.imshow(drawable_image)
        plt.title(f'OCR Results : {self.ocr_method.upper()}')
        plt.axis('off')
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run OCR on a dataset.')
    parser.add_argument('-m', '--ocr_method', type=str, required=True, choices=['easyocr', 'openai'], help='The OCR method to use (easyocr or openai).')
    parser.add_argument('-v', '--visualize', action='store_true', help='Visualize the results on a single image.')
    args = parser.parse_args()

    ocr_method = args.ocr_method
    output_json = f'eval_data/recognition_{ocr_method}.json'
    log_file = f'eval_data/recognition_{ocr_method}_log.txt'

    folder_path = 'eval_data/images'

    dataset = Dataset(folder_path)
    inference = RecognitionInference(ocr_method=ocr_method)

    inference.process_dataset(dataset, output_json, log_file)

    # sanity check, visualize one image
    if args.visualize:
        image, name_of_game, lang, number = dataset[3]
        ocr_processor = OCRProcessor(language='en', method=OCREngine.EASYOCR if ocr_method == 'easyocr' else OCREngine.OPENAI)
        output_text, highlighted_image, annotations, reg_result = ocr_processor.run_ocr(image)
        inference.visualize_single_image(image, annotations)
