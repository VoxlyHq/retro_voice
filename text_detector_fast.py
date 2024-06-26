import numpy as np
import argparse
import time
import os


from PIL import Image, ImageDraw
from pathlib import Path
from tqdm import tqdm

import fast

class TextDetectorFast:
    def __init__(self, model_path, min_confidence=0.5, width=240, height=240, padding=0.0, checkpoint="checkpoints/checkpoint_31ep.pth.tar"):
        self.model_path = model_path
        self.min_confidence = min_confidence
        self.width = width
        self.height = height
        self.padding = padding

        self.graph = self.load_model()
        self.fast = fast.FAST(config="test_detector_configs/fast_tiny_ic15_736_finetune_ic17mlt.py", checkpoint=checkpoint,ema=True)
        # self.fast = fast.FAST(config="test_detector_configs/tt_fast_base_tt_640_finetune_ic17mlt.py", checkpoint=checkpoint,ema=True)

    def load_image(self, image_path):
        image = Image.open(image_path).convert('RGB')
        orig = np.array(image)
        origH, origW = orig.shape[:2]

        rW, rH = origW / float(self.width), origH / float(self.height)
        image = image.resize((self.width, self.height))
        image = np.array(image)
        return image, orig, rW, rH, origW, origH

    def preprocess_image(self, image):
        image = image.convert('RGB')
        
        image = image.resize((self.width, self.height))
        image = np.array(image)
        return image

    def load_model(self):
        return None

    def process_single_image(self, image):
        
        results = self.fast.run_model(image)
        if len(results['results']) == 0:
            return []
        return results['results'][0]['bboxes']
    
    def has_text(self, image):
        return self.fast.has_text(image)

    def close_session(self):
        None

def convert_to_top_left_bottom_right(coordinate_sets):
    converted_sets = []
    for coords in coordinate_sets:
        x_coords = coords[0::2]
        y_coords = coords[1::2]
        top_left = (min(x_coords), min(y_coords))
        bottom_right = (max(x_coords), max(y_coords))
        converted_sets.append((top_left, bottom_right))
    return converted_sets

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image_dir", type=str, default='eval_data/images', help="paths to input images")
    ap.add_argument("-m", "--pretrained_model", type=str, default="pretrained/fast_tiny_ic15_736_finetune_ic17mlt.pth", help="path to input pretrained model")
    ap.add_argument("-c", "--min-confidence", type=float, default=0.5, help="minimum probability required to inspect a region")
    ap.add_argument("-w", "--width", type=int, default=320, help="nearest multiple of 32 for resized width")
    ap.add_argument("-e", "--height", type=int, default=320, help="nearest multiple of 32 for resized height")
    ap.add_argument("-p", "--padding", type=float, default=0.0, help="amount of padding to add to each border of ROI")
    args = vars(ap.parse_args())


    total_duration = 0

    pretrained_model = args["pretrained_model"]
    assert Path(pretrained_model).exists(), 'Please download the pretrained model from here. [https://github.com/czczup/FAST/blob/main/config/fast/ic15/fast_tiny_ic15_736_finetune_ic17mlt.py]'

    image_dir = Path(args["image_dir"])
    image_paths = [i for i in image_dir.iterdir() if i.is_file() and i.suffix == '.jpg']

    output_dir = Path('visualize')
    output_dir.mkdir(exist_ok=True)
    
    abs_start_time = time.time()

    detector = TextDetectorFast(pretrained_model, args["min_confidence"], args["width"], args["height"], args["padding"])

    for image_path in tqdm(image_paths):
        image = Image.open(image_path)
        start_time = time.time()
        results = detector.process_single_image(image)
        end_time = time.time()
        total_duration += end_time - start_time

        converted_coordinates = convert_to_top_left_bottom_right(results)
        
        draw = ImageDraw.Draw(image)

        for xy in converted_coordinates:
            draw.rectangle(xy)
        output = output_dir.joinpath(image_path.stem + '_visualize' + image_path.suffix)
        image.save(output)

    print(f"Output images are saved in {output_dir}")
    detector.close_session()

    average_duration = total_duration / 100
    print(f"Average duration: {average_duration:.4f} seconds")
    print(f"Total duration: {total_duration:.4f} seconds")
    fps = len(image_paths) / (time.time() - abs_start_time)
    print(f"FPS: {fps:.2f}")