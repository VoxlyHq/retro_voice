from easyocr import Reader
from PIL import Image
from pathlib import Path
import time

reader = Reader(['en'])

img_files = [i for i in Path('data').iterdir() if i.is_file()]

total_durations = 0

for img in img_files:
    start = time.time()
    result = reader.detect(Image.open(img))
    end = time.time()

    print('infer time ', end - start)
    print(result)
    total_durations += end - start

print("elapsed_time", total_durations)