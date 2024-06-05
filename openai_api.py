from dotenv import load_dotenv

import os
import base64
import requests

load_dotenv()
OpenAI_API_KEY = os.environ.get("OPENAI_ACCESS_TOKEN")

class OpenAI_API:
    
    def __init__(self, translation_model="gpt-4o", 
                       vision_model="gpt-4o"):
        self.translation_model = translation_model
        self.vision_model = vision_model
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        self.lang_list = {'en' : 'English', 'jp' : 'Japanese'}

    def call_api(self, payload):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OpenAI_API_KEY}"
        }

        response = requests.post(self.openai_url, headers=headers, json=payload)
        print(response.json())
        return response.json()

    def call_translation_api(self, content, target_lang):

        content = content if type(content) is str else f"{content.get('name', '')} : {content.get('dialogue', '')}"
        target_lang = self.lang_list.get(target_lang, target_lang)
        self.set_translation_payload(content, target_lang)

        payload = {
            "model": self.translation_model,
            "messages": self.translation_message,
            "max_tokens": 300
            }
        
        response_json = self.call_api(payload)
        
        return response_json
    
    def call_vision_api(self, image_bytes):
        # Getting the base64 string
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        self.set_vision_payload(base64_image)

        payload = {
        "model": self.vision_model,
        "messages": self.vision_message,
        "max_tokens": 300
        }

        response_json = self.call_api(payload)
        if response_json.get('choices', None) is None:
            response_json = self.call_api(payload)
        return response_json
    
    def set_translation_payload(self, content, target_lang):
        self.translation_message = [
                
                {
                                "role": "system",
                                "content": "You are trained to translate or make assumption about text.Correct typos in the text. You are a helpful and great assistant designed to output text in this format. ``` ```. You are NOT to output any other unnecessary texts. ONLY ``` ```.If there is no translation, you MUST ONLY OUTPUT ``` ```"
                },
                {
                    "role": "user",
                    "content": [
                        {
                        "type": "text",
                        "text": f"Translate this sentence into {target_lang}.\n{content}"
                        },
                ]
                }
            ]
    
    def set_vision_payload(self, base64_image):
        # self.vision_message = [
        #     {
        #     "role": "user",
        #     "content": [
        #         {
        #         "type": "text",
        #         "text": "What is the text in the photo?"
        #         },
        #         {
        #         "type": "image_url",
        #         "image_url": {
        #             "url": f"data:image/jpeg;base64,{base64_image}"
        #         }
        #         }
        #     ]
        #     }
        # ]
        self.vision_message = [
                                {
                                "role": "system",
                                "content": "You are trained to identify or make assumption about multilinugal text within images. You are a helpful and great assistant designed to output text in this format. ``` ```. You are NOT to output any other unnecessary texts. ONLY ``` ```.If there is not text in the photo, you MUST ONLY OUTPUT ``` ```"
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
                                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                                }
                                                }
                                            ]
                                }
                            ]