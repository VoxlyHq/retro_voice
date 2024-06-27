import unittest
from PIL import Image
from pathlib import Path
from text_detector_fast import TextDetectorFast  # Adjust the import based on your module structure

class TestTextDetectorFast(unittest.TestCase):

    def setUp(self):
        self.model_path = 'pretrained/fast_tiny_ic15_736_finetune_ic17mlt.pth'
        self.min_confidence = 0.5
        self.width = 240
        self.height = 240
        self.padding = 0.0
        self.checkpoint = "checkpoints/checkpoint_60ep.pth.tar"
        self.text_detector = TextDetectorFast(self.model_path, self.min_confidence, self.width, self.height, self.padding, self.checkpoint)

        self.test_data_dir = Path("tests/unit_test_data")
        self.image_with_text = Image.open(self.test_data_dir / 'orig_dialogue_box.jpg')
        self.image_with_no_text = Image.open(self.test_data_dir / 'blurred_bbox.jpg')

    def test_initialization(self):
        self.assertEqual(self.text_detector.model_path, self.model_path)
        self.assertEqual(self.text_detector.min_confidence, self.min_confidence)
        self.assertEqual(self.text_detector.width, self.width)
        self.assertEqual(self.text_detector.height, self.height)
        self.assertEqual(self.text_detector.padding, self.padding)
        self.assertIsNotNone(self.text_detector.fast)

    def test_process_single_image(self):
        result = self.text_detector.process_single_image(self.image_with_text)
        self.assertIsInstance(result, list)
        self.assertNotEqual(result, [])
        for bbox in result:
            self.assertIsInstance(bbox, list)

    def test_process_single_image_no_results(self):
        result = self.text_detector.process_single_image(self.image_with_no_text)
        self.assertIsInstance(result, list)
        self.assertListEqual(result, [])

    def test_has_text(self):
        result = self.text_detector.has_text(self.image_with_text)
        self.assertTrue(result)

    def test_has_text_no_text(self):
        result = self.text_detector.has_text(self.image_with_no_text)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
