import cv2
from easyocr import Reader
from PIL import Image
from pathlib import Path
import time
import torch
import torch.profiler
from easyocr.imgproc import resize_aspect_ratio, loadImage
import cProfile

# Initialize the OCR reader
reader = Reader(['en'])

# Get the list of image files
img_files = [i for i in Path('data/MSRA-TD500/test').iterdir() if i.is_file() and i.suffix.lower() in {'.jpg', '.jpeg'}]

# Load the first image
if img_files:
    print(img_files[0])
    img = img_files[0]
else:
    raise FileNotFoundError("No image files found in the specified directory.")

# Initialize total durations and item count
total_durations = 0
item_count = 0

oimage = loadImage(img)
oimage = loadImage("ff2_en_1.png")

mag_ratio = 1.
canvas_size = 2560

img_resized, target_ratio, size_heatmap = resize_aspect_ratio(oimage, canvas_size,
                                                              interpolation=cv2.INTER_LINEAR,
                                                              mag_ratio=mag_ratio)
print(target_ratio)

# Create a list to store the results for later analysis
results = []

#ignore the first result so you dont get loading issues
with torch.cuda.amp.autocast():
    _ = reader.detect(oimage)


profiler = cProfile.Profile()
profiler.enable()

# Process the first image 60 times with PyTorch Profiler
for _ in range(60):
    start = time.time()
    with torch.cuda.amp.autocast():
        result = reader.detect(oimage)
    end = time.time()

    infer_time = end - start
    print('Infer time:', infer_time)
    
    total_durations += infer_time
    item_count += 1

    # Step through the profiler
#    prof.step()

    # Store the result for later analysis
    results.append(result)


# Stop profiling
profiler.disable()

# Save the profiling results to a file
profiler.dump_stats('tmp19.pro')

# Calculate the average time per item
if item_count > 0:
    average_time_per_item = total_durations / item_count
else:
    average_time_per_item = 0

print("Total elapsed time:", total_durations)
print("Number of items:", item_count)
print("Average time per item:", average_time_per_item)
