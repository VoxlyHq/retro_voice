from PIL import Image
import numpy as np
import imagehash

def image_crop_in_top_half(img):
    w,h = img.size
    top_left = (0, 0)
    bottom_right = (w, h//2)
    img = img.crop((*top_left, *bottom_right))

    return img

def image_crop_title_bar(img, crop_y_coordinate=37):
    # crop the title bar
    w,h = img.size
    top_left = tuple((0, crop_y_coordinate))
    bottom_right = tuple((w, h))
    img = img.crop((*top_left, *bottom_right))

    return img

def image_crop_dialogue_box(img, ann):
    top_left = ann[0][0][0]
    # finding largest x and y coordinates for bottom_right
    largest_x = 0
    largest_y = 0
    for i in ann:
        ann = i[0][2]
        if ann[0] >= largest_x:
            largest_x = ann[0]
        if ann[1] >= largest_y:
            largest_y = ann[1]
    bottom_right = [largest_x, largest_y]

    # Ensure the coordinates are in the correct format (floats or integers)
    top_left = tuple(map(int, top_left))
    bottom_right = tuple(map(int, bottom_right))
    img_crop = img.crop((*top_left, *bottom_right))
    return img_crop

def calculate_image_difference(img1, img2):
    if img1 == None or img2 == None:
        return 0
    img2 = img2.resize(img1.size, Image.NEAREST)
    
    # Convert images to NumPy arrays
    img1_array = np.asarray(img1)
    img2_array = np.asarray(img2)
    
    # Calculate the absolute difference between the images
    diff = np.abs(img1_array - img2_array)
    
    # Calculate the percentage of difference
    num_diff_pixels = np.sum(diff > 0)  # Count pixels that are different
    total_pixels = np.prod(img1.size) * 3  # Total number of values in the array
    percent_diff = (num_diff_pixels / total_pixels) * 100
    return percent_diff

def calculate_image_hash_different(img1, img2):
    if img1 == None or img2 == None:
        return 0
    
    img1 = image_crop_in_top_half(img1)

    img2 = image_crop_in_top_half(img2)

    img1_hash = imagehash.average_hash(img1, hash_size=16)
    img2_hash = imagehash.average_hash(img2, hash_size=16)
    return img1_hash - img2_hash
    

def calculate_image_file_difference(img_path1, img_path2):
    # Open the images
    img1 = Image.open(img_path1).convert('RGB')
    img2 = Image.open(img_path2).convert('RGB')
    
    percent_diff = calculate_image_difference(img1, img2)

    return percent_diff

def crop_image_by_bboxes(image, bboxes):
    """
    crop the image into a list of small images based on bounding boxes
    """
    cropped_images = []
    for bbox in bboxes:
        x1,y1, x2, y2 = bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1]
        img_cropped = image.crop((x1, y1, x2, y2))
        cropped_images.append(img_cropped)
    return cropped_images

def combine_images(images, orientation='vertical', padding=10):
    widths, heights = zip(*(i.size for i in images))

    if orientation == 'horizontal':
        total_width = sum(widths) + padding * (len(images) - 1)
        max_height = max(heights)
        combined_image = Image.new('RGB', (total_width, max_height), color=(255, 255, 255))

        x_offset = 0
        for img in images:
            combined_image.paste(img, (x_offset, 0))
            x_offset += img.width + padding
    else:  # vertical
        total_height = sum(heights) + padding * (len(images) - 1)
        max_width = max(widths)
        combined_image = Image.new('RGB', (max_width, total_height), color=(255, 255, 255))

        y_offset = 0
        for img in images:
            combined_image.paste(img, (0, y_offset))
            y_offset += img.height + padding

    return combined_image

if __name__ == "__main__":
    # Example usage
    img_path1 = 'window_capture.jpg'
    img_path2 = 'screen_capture.jpg'
    percent_diff = calculate_image_file_difference(img_path1, img_path2)
    print(f'Images differ by {percent_diff:.2f}%')

    # Decide whether to call OCR based on the difference
    if percent_diff > 10:
        print("Images are more than 10% different. Proceed with OCR.")
    else:
        print("Difference is less than 10%. No need to call OCR again.")
