import unittest
import base64
import json
from io import BytesIO
from PIL import Image
from claude_api import Claude_API, extract_between_tags
from utils import clean_vision_model_output
from thefuzz import fuzz
from pathlib import Path

class TestOpenAI_API(unittest.TestCase):
    
    def setUp(self):
        self.api = Claude_API()
        self.test_data_dir = Path("tests/unit_test_data")
        self.sample_image = Image.open(self.test_data_dir / 'windows_eng_ff4.png')
        if self.sample_image.mode == "RGBA":
            self.sample_image = self.sample_image.convert("RGB")
        buffered = BytesIO()
        self.sample_image.save(buffered, format="JPEG")
        self.sample_image_bytes = buffered.getvalue()
        self.base64_image = base64.b64encode(self.sample_image_bytes).decode('utf-8')

    def test_call_vision_api(self):
        base64_image = self.api.preprocess(self.sample_image)
        response = self.api.call_vision_api(base64_image)
        cleaned_text = ' '.join(extract_between_tags('original_text', response))
        
        similarity_ratio = similarity_ratio = fuzz.ratio(cleaned_text, "Crew: Do we really have to keep doing this?") / 100.0
        self.assertGreater(similarity_ratio, 0.33)

   
if __name__ == '__main__':
    unittest.main()
