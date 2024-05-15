from pathlib import Path
from PIL import Image
import time

from text_detector import TextDetector


img_files = [i for i in Path('data/').iterdir() if i.is_file()]


east_path = 'frozen_east_text_detection.pb'
min_confidence = 0.5
width = 320
height = 320
padding = 0.0

total_durations = 0

detector = TextDetector(east_path, min_confidence, width, height, padding)


for image_path in img_files:

    start = time.time()
    image, orig, rW, rH, origW, origH = detector.load_image(image_path)
    

    results = detector.has_text(image)

    # print(f"Results for {image_path}:", results)
    end = time.time()
    total_durations += end - start
        

detector.close_session()

print("elapsed_time", total_durations)