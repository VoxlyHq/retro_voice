import numpy as np
import argparse
import time
import os


from PIL import Image
import fast

class TextDetectorFast:
    def __init__(self, model_path, min_confidence=0.5, width=320, height=320, padding=0.0):
        self.model_path = model_path
        self.min_confidence = min_confidence
        self.width = width
        self.height = height
        self.padding = padding

        self.graph = self.load_model()
        self.fast = fast.FAST(config="test_detector_configs/tt_fast_base_tt_640_finetune_ic17mlt.py", checkpoint="checkpoints/fast_base_tt_640_finetune_ic17mlt.pth",ema=True)

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

    def process_single_image(self, image, orig, rW, rH, origW, origH):
        
        results = None

        return results
    
    def has_text(self, image):
        return self.fast.has_text(image)

    def close_session(self):
        None

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--images", type=str, nargs='+', required=True, help="paths to input images")
    ap.add_argument("-east", "--east", type=str, required=True, help="path to input EAST text detector")
    ap.add_argument("-c", "--min-confidence", type=float, default=0.5, help="minimum probability required to inspect a region")
    ap.add_argument("-w", "--width", type=int, default=320, help="nearest multiple of 32 for resized width")
    ap.add_argument("-e", "--height", type=int, default=320, help="nearest multiple of 32 for resized height")
    ap.add_argument("-p", "--padding", type=float, default=0.0, help="amount of padding to add to each border of ROI")
    args = vars(ap.parse_args())

    # total_duration = 0
    # image_path = args["images"][0]
    
    # abs_start_time = time.time()

    # detector = TextDetector(args["east"], args["min_confidence"], args["width"], args["height"], args["padding"])
    # image, orig, rW, rH, origW, origH = detector.get_image_attrs(Image.open(image_path))
    # for i in range(100):
    #     start_time = time.time()
    #     results = detector.has_text(image)
    #     # print(f"Results for {image_path}:")
        
    #     # print(results)
    #     end_time = time.time()
    #     total_duration += end_time - start_time

    # detector.close_session()
    # average_duration = total_duration / 100
    # print(f"Average duration: {average_duration:.4f} seconds")
    # print(f"Total duration: {total_duration:.4f} seconds")
    # fps = 100 / (time.time() - abs_start_time)
    # print(f"FPS: {fps:.2f}")