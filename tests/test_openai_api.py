import unittest
import base64
import json
from io import BytesIO
from PIL import Image
from openai_api import OpenAI_API  
from utils import clean_vision_model_output
from thefuzz import fuzz
from pathlib import Path

class TestOpenAI_API(unittest.TestCase):
    
    def setUp(self):
        self.api = OpenAI_API()
        self.test_data_dir = Path("tests/unit_test_data")
        self.sample_image = Image.open(self.test_data_dir / 'windows_eng_ff4.png')
        if self.sample_image.mode == "RGBA":
            self.sample_image = self.sample_image.convert("RGB")
        buffered = BytesIO()
        self.sample_image.save(buffered, format="JPEG")
        self.sample_image_bytes = buffered.getvalue()
        self.base64_image = base64.b64encode(self.sample_image_bytes).decode('utf-8')

    def test_call_api(self):
        vision_message = [
                                {
                                "role": "system",
                                "content": "You are trained to identify or make assumption about multilinugal text within images. You are a helpful and great assistant designed to output JSON successfully. {'text' : text}"
                                },
                                {
                                "role": "user",
                                "content": [
                                                {
                                                "type": "text",
                                                "text": "What is the text in the photo? The text are "
                                                },
                                                {
                                                "type": "image_url",
                                                "image_url": {
                                                    "url": f"data:image/jpeg;base64,{self.base64_image}"
                                                }
                                                }
                                            ]
                                }
                            ]
        sample_payload = {
                        "model": self.api.vision_model,
                        "messages": vision_message,
                        "max_tokens": 300
                        }
        
        response_json = self.api.call_api(sample_payload)

        self.assertIn(self.api.vision_model, response_json['model'])
        self.assertIsInstance(response_json['choices'][0]['message']['content'], str)

    def test_call_vision_api(self):
        
        response_json = self.api.call_vision_api(self.sample_image_bytes)
        cleaned_text = clean_vision_model_output(response_json)

        self.assertIn(self.api.vision_model, response_json['model'])
        
        similarity_ratio = similarity_ratio = fuzz.ratio(cleaned_text, "Crew: Do we really have to keep doing this?") / 100.0
        self.assertGreater(similarity_ratio, 0.33)

   
if __name__ == '__main__':
    unittest.main()
