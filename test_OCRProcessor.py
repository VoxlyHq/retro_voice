import unittest
from PIL import Image
from ocr import OCRProcessor  
from thefuzz import fuzz

class TestOCRProcessor(unittest.TestCase):
    def setUp(self):
        self.ocr_processor = OCRProcessor(language='en', method=1)
        self.image = Image.open('unit_test_data/windows_eng_ff4.png').convert('RGB')
        self.dialogue_image = Image.open('unit_test_data/orig_dialogue_box.jpg')
    
    def test_process_image(self):
        image_bytes = self.ocr_processor.process_image(self.image)
        self.assertIsNotNone(image_bytes)
        self.assertIsInstance(image_bytes, bytes)

    def test_ocr_easyocr(self):
        image_bytes = self.ocr_processor.process_image(self.image)
        result = self.ocr_processor.ocr_easyocr(image_bytes)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], tuple)
        self.assertEqual(len(result[0]), 3)        

    def test_filter_ocr_result(self):
        result = [([[23, 255], [4, 255], [599, 293], [42, 293]], 'Retroarch', 0.833242342332),
                  ([[88, 201], [306, 201], [306, 242], [88, 242]], 'Crew:do', 0.8719411100252771),
                  ([[328, 208], [390, 208], [390, 236], [328, 236]], 'We', 0.9169464750485676), 
                  ([[420, 199], [604, 199], [604, 242], [420, 242]], 'reo]1y', 0.3580370079020545), 
                  ([[630, 202], [753, 202], [753, 239], [630, 239]], 'have', 0.6034191846847534), 
                  ([[778, 204], [842, 204], [842, 236], [778, 236]], 't0', 0.26148517784655595), 
                  ([[121, 257], [243, 257], [243, 293], [121, 293]], 'keep', 0.971559464931488), 
                  ([[270, 255], [419, 255], [419, 295], [270, 295]], 'doing', 0.9933700775761459), 
                  ([[447, 255], [599, 255], [599, 293], [447, 293]], 'this?', 0.9645945643878401)]
        filtered_result = self.ocr_processor.filter_ocr_result(result)

        self.assertEqual(len(filtered_result[0]), 3)
        self.assertEqual(filtered_result[0][1], 'Crew:do')

    def test_ocr_and_highlight(self):
        text, drawable_image, annotations = self.ocr_processor.ocr_and_highlight(self.image)
        self.assertIsInstance(text, str)
        self.assertIsInstance(drawable_image, Image.Image)
        self.assertEqual(len(annotations[0]), 3)

    def test_det_easyocr(self):
        """
        Test the det_easyocr method 
        """
        image_bytes = self.ocr_processor.process_image(self.dialogue_image)
        detection_results = self.ocr_processor.det_easyocr(image_bytes)

        # Check if the detection results are formatted correctly
        self.assertIsInstance(detection_results[0], tuple)
        self.assertEqual(len(detection_results[0]), 3)
        self.assertIsInstance(detection_results[0][0], list)
        self.assertIsInstance(detection_results[0][0][0], list)
        self.assertEqual(len(detection_results[0][0][0]), 2)
        self.assertEqual(detection_results[0][0][0], [97, 203])

    def test_ocr_and_highlight_method2(self):
        """
        Test the ocr_and_highlight method for method 2.
        """
        self.ocr_processor.method = 2
        # Process the image and get the OCR results
        output_text, highlighted_image, detection_results = self.ocr_processor.ocr_and_highlight(self.dialogue_image)

        # Check the OCR output text
        similarity_ratio = similarity_ratio = fuzz.ratio(output_text, "Crew: Why are we robbing crystals from innocent people? Crew: That's our duty.") / 100.0
        self.assertGreater(similarity_ratio, 0.33)

if __name__ == '__main__':
    unittest.main()
