import unittest
from PIL import Image
import io

from image_diff import image_crop_title_bar

class TestImageCropTitleBar(unittest.TestCase):

    def setUp(self):
        # Create a simple image for testing
        self.image = Image.open('unit_test_data/osx_jp_ff4.png')

    def test_image_crop_title_bar(self):
        cropped_image = image_crop_title_bar(self.image)
        cropped_image.save('unit_test_data/cropped_osx_jp.ff4.png')
        self.assertEqual(cropped_image.size, (self.image.size[0], self.image.size[1] - 37))  # 100 width, 63 height after cropping 37 pixels

    def test_image_crop_title_bar_custom_crop(self):
        cropped_image = image_crop_title_bar(self.image, crop_y_coordinate=50)
        self.assertEqual(cropped_image.size, (self.image.size[0], self.image.size[1] - 50))  # 100 width, 50 height after cropping 50 pixels

if __name__ == '__main__':
    unittest.main()
