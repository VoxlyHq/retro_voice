import unittest
from pathlib import Path
from PIL import Image, ImageDraw
import json
import imagehash
from process_frames import FrameProcessor
from utils import draw_translation

class TestFrameProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = FrameProcessor(language='en', save_outputs=True)
        self.test_data_dir = Path("unit_test_data")
        self.input_image_path = self.test_data_dir / "test_image.jpg"
        self.expected_output_image_path = self.test_data_dir / "test_translation_annotated.jpg"
        self.annotations_path = self.test_data_dir / "test_ocr_annotations.json"
        self.translation_path = self.test_data_dir / "test_translation.json"
        
        # Load input image
        self.input_image = Image.open(self.input_image_path)
        
        # Load expected output image
        self.expected_output_image = Image.open(self.expected_output_image_path)
        
        # Load annotations
        with open(self.annotations_path, 'r', encoding='utf-8') as f:
            self.annotations = json.load(f)
        
        with open(self.translation_path, 'r', encoding='utf-8') as f:
            self.translation = json.load(f)

    def test_process_frame(self):
        # Create an annotated image based on the input image and annotations
        annotated_image = draw_translation(self.input_image, self.translation, self.annotations)
        
        # Ensure the generated annotated image matches the expected output image
        input_image_hash = imagehash.average_hash(self.expected_output_image)
        output_image_hash = imagehash.average_hash(annotated_image)
        
        self.assertEqual(input_image_hash, output_image_hash, "The annotated image does not match the expected output image.")
    
    def test_save_outputs(self):
        # Run the image through the processor
        last_played, previous_image, highlighted_image, annotations, translation = self.processor.run_image(self.input_image)
        
        # Save the outputs to disk
        self.processor.save_outputs_to_disk(self.input_image, highlighted_image, annotations, translation, None)
        
        # Check that the files were created
        output_dir = Path("outputs")
        self.assertTrue((output_dir / "input_images").exists())
        self.assertTrue((output_dir / "annotated_images").exists())
        self.assertTrue((output_dir / "ocr_annotations").exists())
        self.assertTrue((output_dir / "translations").exists())
    
if __name__ == '__main__':
    unittest.main()
