import cv2
from text_detector_fast import TextDetectorFast
from PIL import Image
from pathlib import Path
import time
import torch
import torch.profiler
import cProfile

# Initialize the OCR reader
reader = TextDetectorFast('')

# Initialize total durations and item count
total_durations = 0
item_count = 0

#oimage = loadImage(img)
oimage = Image.open("ff2_en_1.png")

mag_ratio = 1.
canvas_size = 2560

#img_resized, target_ratio, size_heatmap = resize_aspect_ratio(oimage, canvas_size,
#                                                              interpolation=cv2.INTER_LINEAR,
#                                                              mag_ratio=mag_ratio)
#print(target_ratio)

# Create a list to store the results for later analysis
results = []

#ignore the first result so you dont get loading issues
with torch.cuda.amp.autocast():
    _ = reader.has_text(oimage)


profiler = cProfile.Profile()
profiler.enable()

# Process the first image 60 times with PyTorch Profiler
for _ in range(400):
    start = time.time()
    with torch.cuda.amp.autocast():
        result = reader.has_text(oimage)
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
profiler.dump_stats('f2.pro')

# Calculate the average time per item
if item_count > 0:
    average_time_per_item = total_durations / item_count
else:
    average_time_per_item = 0

print("Total elapsed time:", total_durations)
print("Number of items:", item_count)
print("Average time per item:", average_time_per_item)
