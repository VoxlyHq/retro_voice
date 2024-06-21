import unittest
from PIL import Image, ImageChops
import io
import imagehash
from image_diff import image_crop_title_bar, image_crop_in_top_half, image_crop_dialogue_box, crop_image_by_bboxes, combine_images
from pathlib import Path

class TestImageCropTitleBar(unittest.TestCase):

    def setUp(self):
        # Create a simple image for testing
        self.test_data_dir = Path("tests/unit_test_data")
        self.osx_image = Image.open(self.test_data_dir / 'osx_jp_ff4.png')
        self.windows_image = Image.open(self.test_data_dir / 'windows_jp_ff4.png')
        self.dialogue_image_orig = Image.open(self.test_data_dir / 'orig_dialogue_box.jpg')
        self.dialogue_image = Image.open(self.test_data_dir / 'dialogue_box.jpg')
        self.type2_image = Image.open(self.test_data_dir / 'overlap_bbox.jpg')
        self.bbox1 = [[(97, 203), (344, 246)],
                        [(368, 212), (462, 240)],
                        [(486, 212), (550, 238)],
                        [(578, 202), (789, 245)],
                        [(130, 257), (371, 298)],
                        [(398, 258), (523, 298)],
                        [(578, 258), (788, 294)],
                        [(128, 308), (341, 352)],
                        [(97, 363), (391, 399)],
                        [(398, 370), (430, 398)],
                        [(460, 368), (552, 398)],
                        [(578, 361), (720, 404)]]
        self.size1 = [(247, 43),
                        (94, 28),
                        (64, 26),
                        (211, 43),
                        (241, 41),
                        (125, 40),
                        (210, 36),
                        (213, 44),
                        (294, 36),
                        (32, 28),
                        (92, 30),
                        (142, 43)]
        self.bbox2 = [[(934, 54), (1177, 129)],
                        [(984, 710), (1206, 782)],
                        [(85, 721), (457, 785)],
                        [(478, 732), (538, 780)],
                        [(626, 732), (768, 780)],
                        [(1210, 730), (1350, 782)]]
        self.size2 = [(243, 75), (222, 72), (372, 64), (60, 48), (142, 48), (140, 52)]

    def compare_images(self, img1, img2):
        # Compare two images
        return ImageChops.difference(img1, img2).getbbox() is None

    def test_image_crop_title_bar(self):
        cropped_image = image_crop_title_bar(self.osx_image)
        cropped_image.save(self.test_data_dir / 'cropped_osx_jp_ff4.png')
        self.assertEqual(cropped_image.size, (self.osx_image.size[0], self.osx_image.size[1] - 37))  # 100 width, 63 height after cropping 37 pixels
        cropped_image = image_crop_title_bar(self.windows_image, 50)
        cropped_image.save(self.test_data_dir / 'cropped_windows_jp_ff4.png')
        self.assertEqual(cropped_image.size, (self.windows_image.size[0], self.windows_image.size[1] - 50))

    def test_image_crop_in_top_half(self):
        cropped_image = image_crop_in_top_half(self.osx_image)
        cropped_image.save(self.test_data_dir / 'half_osx_jp_ff4.png')
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
    
    def test_crop_image_by_bboxes_type1(self):
        '''type1 : normal dialogue box'''
        type1_image = self.dialogue_image_orig
        cropped_images = crop_image_by_bboxes(type1_image, self.bbox1)
        self.assertEqual(len(cropped_images), 12)
        for cropped_image, size in zip(cropped_images, self.size1):
            self.assertEqual(cropped_image.size, size)
            self.assertEqual(cropped_image.size, size)

    def test_crop_image_by_bboxes_type2(self):
        '''type2 : battle dialogue box : separated'''
        cropped_images = crop_image_by_bboxes(self.type2_image, self.bbox2)
        self.assertEqual(len(cropped_images), 6)
        for cropped_image, size in zip(cropped_images, self.size2):
            self.assertEqual(cropped_image.size, size)
            self.assertEqual(cropped_image.size, size)

    def test_combine_images_vertical_type1(self):
        cropped_images = crop_image_by_bboxes(self.dialogue_image_orig, self.bbox1)
        combined_image = combine_images(cropped_images, orientation='vertical', padding=10)
        expected_image = Image.open(self.test_data_dir / 'expected_combined_vertical_type1.jpg')
        self.assertTrue(self.compare_images(combined_image, expected_image))
    
    def test_combine_images_horizontal_type1(self):
        cropped_images = crop_image_by_bboxes(self.dialogue_image_orig, self.bbox1)
        combined_image = combine_images(cropped_images, orientation='horizontal', padding=10)
        expected_image = Image.open(self.test_data_dir / 'expected_combined_horizontal_type1.jpg')
        self.assertTrue(self.compare_images(combined_image, expected_image))

    def test_combine_images_vertical_type2(self):
        cropped_images = crop_image_by_bboxes(self.type2_image, self.bbox2)
        combined_image = combine_images(cropped_images, orientation='vertical', padding=10)
        expected_image = Image.open(self.test_data_dir / 'expected_combined_vertical_type2.jpg')
        self.assertTrue(self.compare_images(combined_image, expected_image))
    
    def test_combine_images_horizontal_type2(self):
        cropped_images = crop_image_by_bboxes(self.type2_image, self.bbox2)
        combined_image = combine_images(cropped_images, orientation='horizontal', padding=10)
        expected_image = Image.open(self.test_data_dir / 'expected_combined_horizontal_type2.jpg')
        self.assertTrue(self.compare_images(combined_image, expected_image))


if __name__ == '__main__':
    unittest.main()
