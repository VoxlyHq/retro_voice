import os
import sys
import json
import time
import cv2
import numpy as np
import matplotlib.pyplot as plt

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from text_detector import TextDetector
from dataset import Dataset

class DetectionInference:
    def __init__(self, model_type):
        if model_type.lower() == 'east':
            self.model_path = 'frozen_east_text_detection.pb'
            self.text_detector = TextDetector(self.model_path)
        else:
            raise ValueError("Unsupported model type. Currently, only 'EAST' is supported.")

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

    def visualize_single_image(self, image, detections):
        orig = np.array(image)
        for detection in detections:
            box = detection["box"]
            (startX, startY, endX, endY) = box
            cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)
        
        plt.figure(figsize=(10, 10))
        plt.imshow(cv2.cvtColor(orig, cv2.COLOR_BGR2RGB))
        plt.title('Text Detections')
        plt.axis('off')
        plt.show()


# Example usage
if __name__ == "__main__":

    model_type = 'east'
    output_json = f'eval_data/detection_{model_type}.json'
    folder_path = 'eval_data/images'
    visualize = False

    dataset = Dataset(folder_path)

    inference = DetectionInference(model_type=model_type)

    inference.process_dataset(dataset, output_json)



    # sanity check, visualize one image
    if visualize:
        inference = DetectionInference(model_type=model_type)

        image, name_of_game, lang, number = dataset[0]  
        
        rects = inference.text_detector.process_single_image(image)
        
        detections = [{"box": [int(coord) for coord in rect]} for rect in rects]

        inference.visualize_single_image(image, detections)