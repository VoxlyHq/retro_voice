import unittest
from PIL import Image
import io

from image_diff import image_crop_title_bar, image_crop_in_top_half

class TestImageCropTitleBar(unittest.TestCase):

    def setUp(self):
        # Create a simple image for testing
        self.osx_image = Image.open('unit_test_data/osx_jp_ff4.png')
        self.windows_image = Image.open('unit_test_data/windows_jp_ff4.png')

    def test_image_crop_title_bar(self):
        cropped_image = image_crop_title_bar(self.osx_image)
        cropped_image.save('unit_test_data/cropped_osx_jp_ff4.png')
        self.assertEqual(cropped_image.size, (self.osx_image.size[0], self.osx_image.size[1] - 37))  # 100 width, 63 height after cropping 37 pixels
        cropped_image = image_crop_title_bar(self.windows_image, 50)
        cropped_image.save('unit_test_data/cropped_windows_jp_ff4.png')
        self.assertEqual(cropped_image.size, (self.windows_image.size[0], self.windows_image.size[1] - 50))

    def test_image_crop_in_top_half(self):
        cropped_image = image_crop_in_top_half(self.osx_image)
        cropped_image.save('unit_test_data/half_osx_jp_ff4.png')
        self.assertEqual(cropped_image.size, (self.osx_image.size[0], self.osx_image.size[1] // 2))  # 100 width, 50 height after cropping 50 pixels

if __name__ == '__main__':
    unittest.main()
