import numpy as np
import cv2
from skimage import io
import time

def loadImage(img_file):
    img = io.imread(img_file)           # RGB order
    if img.shape[0] == 2: img = img[0]
    if len(img.shape) == 2 : img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    if img.shape[2] == 4:   img = img[:,:,:3]
    img = np.array(img)
    return img

def normalizeMeanVariance(in_img, mean=(0.485, 0.456, 0.406), variance=(0.229, 0.224, 0.225)):
    # should be RGB order
    img = in_img.copy().astype(np.float32)
    img -= np.array([mean[0] * 255.0, mean[1] * 255.0, mean[2] * 255.0], dtype=np.float32)
    img /= np.array([variance[0] * 255.0, variance[1] * 255.0, variance[2] * 255.0], dtype=np.float32)
    return img

def main():
    img_file = 'ff2_en_1.png'  # replace with your image file path
    img = loadImage(img_file)

    total_time = 0
    num_iterations = 1000

    for _ in range(num_iterations):
        start_time = time.time()
        normalizeMeanVariance(img)
        end_time = time.time()
        
        total_time += end_time - start_time

    average_time = total_time / num_iterations
    print(f"Total time: {total_time:.6f} seconds")
    print(f"Average time per iteration: {average_time:.6f} seconds")

if __name__ == "__main__":
    main()
