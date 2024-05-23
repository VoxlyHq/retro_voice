import unittest
from PIL import Image
import io
import imagehash
from image_diff import image_crop_title_bar, image_crop_in_top_half, image_crop_dialogue_box

class TestImageCropTitleBar(unittest.TestCase):

    def setUp(self):
        # Create a simple image for testing
        self.osx_image = Image.open('unit_test_data/osx_jp_ff4.png')
        self.windows_image = Image.open('unit_test_data/windows_jp_ff4.png')
        self.dialogue_image_orig = Image.open('unit_test_data/orig_dialogue_box.jpg')
        self.dialogue_image = Image.open('unit_test_data/dialogue_box.jpg')

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
    
    def test_image_crop_dialogue_box(self):
        annotations = [([[97, 203], [344, 203], [344, 246], [97, 246]], '', 0.0),
                        ([[368, 212], [460, 212], [460, 238], [368, 238]], '', 0.0),
                        ([[486, 212], [550, 212], [550, 238], [486, 238]], '', 0.0),
                        ([[578, 202], [789, 202], [789, 245], [578, 245]], '', 0.0),
                        ([[130, 257], [373, 257], [373, 298], [130, 298]], '', 0.0),
                        ([[398, 257], [523, 257], [523, 298], [398, 298]], '', 0.0),
                        ([[556, 264], [582, 264], [582, 290], [556, 290]], '', 0.0),
                        ([[578, 258], [789, 258], [789, 298], [578, 298]], '', 0.0),
                        ([[128, 308], [341, 308], [341, 352], [128, 352]], '', 0.0),
                        ([[97, 363], [391, 363], [391, 399], [97, 399]], '', 0.0),
                        ([[398, 370], [432, 370], [432, 398], [398, 398]], '', 0.0),
                        ([[460, 368], [552, 368], [552, 398], [460, 398]], '', 0.0),
                        ([[576, 359], [720, 359], [720, 404], [576, 404]], '', 0.0)]
        cropped_image = image_crop_dialogue_box(self.dialogue_image_orig, annotations)

        cropped_image_hash = imagehash.average_hash(cropped_image)
        dialogue_box_image_hash = imagehash.average_hash(self.dialogue_image)

        self.assertEqual(cropped_image_hash, dialogue_box_image_hash, "The cropped images do not match.")


if __name__ == '__main__':
    unittest.main()
