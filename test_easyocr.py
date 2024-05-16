import cv2
from easyocr import Reader
from PIL import Image
from pathlib import Path
import time

from easyocr.imgproc import resize_aspect_ratio
from easyocr.imgproc2 import loadImage, resize_aspect_ratio2

# Initialize the OCR reader
reader = Reader(['en'])

# Get the list of image files
img_files = [i for i in Path('data/MSRA-TD500/test').iterdir() if i.is_file() and i.suffix.lower() in {'.jpg', '.jpeg'}]

# Load the first image
if img_files:
    img = img_files[0]
else:
    raise FileNotFoundError("No image files found in the specified directory.")

# Initialize total durations and item count
total_durations = 0
item_count = 0

oimage = loadImage(img)
mag_ratio = 1.
canvas_size = 2560


img_resized, target_ratio, size_heatmap = resize_aspect_ratio2(oimage, canvas_size,
                                                                    interpolation=cv2.INTER_LINEAR,
                                                                    mag_ratio=mag_ratio)
print(target_ratio)
#for img in image_arrs:
#    img_resized, target_ratio, size_heatmap = resize_aspect_ratio(img, canvas_size,
#                                                                    interpolation=cv2.INTER_LINEAR,
#                                                                    mag_ratio=mag_ratio)
#    img_resized_list.append(img_resized)


# Process the first image 60 times
for _ in range(60):
    start = time.time()
    result = reader.detect(img_resized)
    end = time.time()

    infer_time = end - start
    print('Infer time:', infer_time)
    #print(result)
    
    total_durations += infer_time
    item_count += 1

# Calculate the average time per item
if item_count > 0:
    average_time_per_item = total_durations / item_count
else:
    average_time_per_item = 0

print("Total elapsed time:", total_durations)
print("Number of items:", item_count)
print("Average time per item:", average_time_per_item)
