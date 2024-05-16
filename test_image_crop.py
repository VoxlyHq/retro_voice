from image_diff import image_crop_title_bar
from PIL import Image


test_img = Image.open('unit_test_data/osx_jp_ff4.png')

if test_img.mode == 'RGBA':
    test_img = test_img.convert('RGB')

cropped_image = image_crop_title_bar(test_img, 37)
cropped_image.save('unit_test_data/cropped_image_osx.jpg')

test_img = Image.open('unit_test_data/windows_jp_ff4.png')

if test_img.mode == 'RGBA':
    test_img = test_img.convert('RGB')

cropped_image = image_crop_title_bar(test_img, 50)
cropped_image.save('unit_test_data/cropped_image_windows.jpg')

