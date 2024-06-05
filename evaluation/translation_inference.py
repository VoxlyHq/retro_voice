import os
import time
import json
import argparse
from datetime import datetime
from PIL import Image
from dataset import Dataset
from ocr import OCRProcessor
from ocr_enum import OCREngine
from openai_api import OpenAI_API
from utils import clean_vision_model_output

class TranslationInference:
    def __init__(self, ocr_method):
        self.ocr_method = ocr_method.lower()
        if self.ocr_method not in ['easyocr', 'openai']:
            raise ValueError("Unsupported OCR method. Supported methods are 'easyocr' and 'openai'.")
        self.ocr_processor_eng = OCRProcessor(language='en', method=OCREngine.EASYOCR if self.ocr_method == 'easyocr' else OCREngine.OPENAI)
        self.ocr_processor_jp = OCRProcessor(language='jp', method=OCREngine.EASYOCR if self.ocr_method == 'easyocr' else OCREngine.OPENAI)
        self.openai_api = OpenAI_API()

    def process_dataset(self, dataset, output_json, log_file, reuse_ocr_json=None):
        if reuse_ocr_json:
            with open(reuse_ocr_json, 'r', encoding='utf-8') as file:
                ocr_results = json.load(file)
        else:
            ocr_results = self.run_ocr_on_dataset(dataset, log_file)
        
        results = []
        with open(log_file, 'w', encoding='utf-8') as log:
            for ocr_result in ocr_results:
                filename = ocr_result['filename']
                original_text = ocr_result['text']
                lang = 'en' if any(ord(char) > 127 for char in original_text) else 'jp'
                translated_text, translation_result = self.translate_openai(original_text, lang)
                result = {
                    "filename": filename,
                    "original_text": original_text,
                    "translated_text": translated_text,
                }
                results.append(result)
                
                log.write(f"Processed {result['filename']}\n")
                log.write(f"Original text: {result['original_text']}\n")
                log.write(f"Translated text: {result['translated_text']}\n")
                log.write("\n")

        with open(output_json, 'w', encoding='utf-8') as json_file:
            json.dump(results, json_file, indent=4)

    def run_ocr_on_dataset(self, dataset, log_file):
        results = []
        with open(log_file, 'w', encoding='utf-8') as log:
            for idx in range(len(dataset)):
                image, name_of_game, lang, number = dataset[idx]
                ocr_processor = OCRProcessor(language=lang, method=OCREngine.EASYOCR if self.ocr_method == 'easyocr' else OCREngine.OPENAI)
                start_time = time.time()
                output_text, highlighted_image, annotations, reg_result = ocr_processor.run_ocr(image)
                end_time = time.time()
                time_taken = end_time - start_time
                result = {
                    "filename": dataset.image_files[idx].name,
                    "time_taken": time_taken,
                    "text": output_text,
                }
                results.append(result)
                
                log.write(f"Processed {result['filename']}\n")
                log.write(f"Time taken: {result['time_taken']} seconds\n")
                log.write(f"Detected text: {result['text']}\n")
                log.write("\n")

        return results

    def translate_openai(self, content, target_lang):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        result = self.openai_api.call_translation_api(content, target_lang)
        content = result['choices'][0]['message']['content']
        cleaned_string = clean_vision_model_output(content)
        return cleaned_string, result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run OCR and translation on a dataset.')
    parser.add_argument('-m', '--ocr_method', type=str, required=True, choices=['easyocr', 'openai'], help='The OCR method to use (easyocr or openai).')
    parser.add_argument('-o', '--output_json', type=str, required=True, help='The output JSON file to save the translation results.')
    parser.add_argument('-l', '--log_file', type=str, required=True, help='The log file to save the processing details.')
    parser.add_argument('-r', '--reuse_ocr_json', type=str, help='Reuse a previous OCR JSON file instead of running OCR again.')
    args = parser.parse_args()

    ocr_method = args.ocr_method
    output_json = args.output_json
    log_file = args.log_file
    reuse_ocr_json = args.reuse_ocr_json

    folder_path = 'eval_data/images'

    dataset = Dataset(folder_path)
    inference = TranslationInference(ocr_method=ocr_method)

    inference.process_dataset(dataset, output_json, log_file, reuse_ocr_json)
