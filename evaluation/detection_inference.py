import os
import sys
import cv2
import json
import time
import random
import numpy as np
import matplotlib.pyplot as plt
import argparse

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from text_detector import TextDetector
from text_detector_fast import TextDetectorFast
from dataset import Dataset

class DetectionInference:
    def __init__(self, model_type):
        self.model_type = model_type.lower()
        if self.model_type.lower() == 'east':
            self.model_path = 'frozen_east_text_detection.pb'
            self.text_detector = TextDetector(self.model_path)
        elif self.model_type.lower() == 'fast':
            self.model_path = 'pretrained/fast_base_tt_640_finetune_ic17mlt.pth'
            self.text_detector = TextDetectorFast(self.model_path)
        else:
            raise ValueError("Unsupported model type. Supported types are 'EAST' and 'FAST'.")

    def process_dataset(self, dataset, output_json):
        results = []
        for idx in range(len(dataset)):
            image, _, _, _ = dataset[idx]
            start_time = time.time()
            bbox = self.text_detector.process_single_image(image)
            end_time = time.time()
            time_taken = end_time - start_time
            results.append({
                "filename": dataset.image_files[idx].name,
                "time_taken": time_taken,
                "predictions": bbox
            })

        with open(output_json, 'w') as json_file:
            json.dump(results, json_file, indent=4)

        self.text_detector.close_session()

    def visualize_single_image(self, image, rects):
        if self.model_type == 'east':
            detections = [{"box": rect} for rect in rects]
            orig = np.array(image)
            for detection in detections:
                box = detection["box"]
                (startX, startY, endX, endY) = box
                cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)
            
            plt.figure(figsize=(10, 10))
            plt.imshow(cv2.cvtColor(orig, cv2.COLOR_BGR2RGB))
            plt.title('Text Detections : EAST')
            plt.axis('off')
            plt.show()
        elif self.model_type == 'fast':
            plt.imshow(self.text_detector.fast.add_annotations(np.array(image), rects))
            plt.title('Text Detection : FAST')
            plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run text detection on a dataset.')
    parser.add_argument('-m', '--model_type', type=str, required=True, choices=['east', 'fast'], help='The type of text detection model to use (east or fast).')
    parser.add_argument('-v','--visualize', action='store_true', help='Visualize the results on a single image.')
    args = parser.parse_args()

    model_type = args.model_type
    output_json = f'eval_data/detection_{model_type}.json'
    folder_path = 'eval_data/images'

    dataset = Dataset(folder_path)
    inference = DetectionInference(model_type=model_type)

    inference.process_dataset(dataset, output_json)

    # sanity check, visualize one image
    if args.visualize:
        inference = DetectionInference(model_type=model_type)

        image, name_of_game, lang, number = dataset[3]  
        rects = inference.text_detector.process_single_image(image)
        
        print(rects)

        inference.visualize_single_image(image, rects)
