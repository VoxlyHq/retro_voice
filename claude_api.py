from dotenv import load_dotenv
import requests
import base64
import os
import json

load_dotenv()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")

class Claude_API:
    def __init__(self, translation_model="claude-3-sonnet-20240229", 
                       vision_model="claude-3-opus-20240229"):
        self.translation_model = translation_model
        self.vision_model = vision_model
        self.lang_list = {'en': 'English', 'jp': 'Japanese'}
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01"
        }

    def preprocess(self, image):
        with open(image, "rb") as image_file:
            binary_data = image_file.read()
            base_64_encoded_data = base64.b64encode(binary_data)
            base64_string = base_64_encoded_data.decode('utf-8')
        return base64_string

    def call_api(self, payload):
        response = requests.post(self.base_url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()['content'][0]['text']

    def call_translation_api(self, content, target_lang):
        ocr_text = content if isinstance(content, str) else f"{content.get('name', '')} : {content.get('dialogue', '')}"
        target_lang = self.lang_list.get(target_lang, target_lang)
        source_lang = 'English' if target_lang == "Japanese" else "Japanese"
        self.set_translation_payload(ocr_text, source_lang, target_lang)

        payload = {
            "model": self.translation_model,
            "max_tokens": 1000,
            "temperature": 0,
            "messages": self.translation_message
        }

        return self.call_api(payload)

    def call_translation_vision_api(self, base64_string):
        self.set_translation_vision_payload(base64_string)

        payload = {
            "model": self.vision_model,
            "max_tokens": 1000,
            "temperature": 0,
            "messages": self.translation_vision_payload
        }

        return self.call_api(payload)

    def set_translation_vision_payload(self, base64_string):
        self.translation_vision_payload = [
            {
                "role": 'user',
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64_string}},
                    {"type": "text", "text": "You are an AI assistant tasked with performing Optical Character Recognition (OCR) on images, particularly those from retro games or containing pixel-based text. The image may contain text in any language, not just English. Your goal is to accurately identify and transcribe any text present in the image.\n\nHere is the image you need to analyze:\n\nPlease follow these steps to complete the OCR task:\n\n1. Carefully examine the image for any visible text. This may include menu items, dialogue, on-screen instructions, or any other textual elements.\n\n2. If the text appears to be in a pixel font or low resolution, pay extra attention to the shape and arrangement of the pixels to discern the characters accurately.\n\n3. Identify the language of the text if possible. If you're unsure about the language, make your best guess and note your uncertainty.\n\n4. Transcribe all text you can identify in the image. If the text is not in English, provide both the original text and an English translation if you're able to translate it.\n\n5. If there are multiple separate text elements in the image (e.g., a title and a menu), transcribe them separately and indicate their relative positions in the image (e.g., \"top center\", \"bottom right\").\n\n6. If any text is partially obscured or ambiguous, make your best guess and indicate your uncertainty.\n\n7. If you cannot identify any text in the image, state this clearly.\n\nPresent your findings in the following format:\n\n<ocr_results>\n<text_element1>\n<position>Position in the image</position>\n<original_text>Text as it appears in the image</original_text>\n<language>Identified or suspected language</language>\n<translation>English translation (if applicable)</translation>\n</text_element1>\n<!-- Repeat for each separate text element -->\n<notes>Any additional observations or uncertainties</notes>\n</ocr_results>\n\nIf you cannot identify any text in the image, respond with:\n\n<ocr_results>\n<no_text_found>No text could be identified in this image.</no_text_found>\n</ocr_results>\n\nRemember, accuracy is crucial. If you're unsure about any aspect of the text, it's better to express your uncertainty than to make an incorrect transcription."}
                ]
            }
        ]

    def set_translation_payload(self, ocr_text, source_lang, target_lang):
        self.translation_message = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"You are tasked with translating text from one language to another. The text you will be working with comes from Optical Character Recognition (OCR) results, which means it may contain errors, typos, or inconsistencies. Your job is to translate the text as accurately as possible while accounting for these potential issues.\n\nThe source language (the language you will be translating from) is:\n<source_language>\n{source_lang}\n</source_language>\n\nThe target language (the language you will be translating to) is:\n<target_language>\n{target_lang}\n</target_language>\n\nHere is the OCR text you need to translate:\n<ocr_text>\n{ocr_text}\n</ocr_text>\n\nFollow these steps to complete the translation:\n\n1. Carefully read through the OCR text to identify any obvious errors or typos. Make a mental note of these, but do not correct them yet.\n\n2. If you encounter any words or phrases that seem out of place or don't make sense in the context, consider whether they might be OCR errors. Use your knowledge of the source language and the context to make educated guesses about what these words or phrases might actually be.\n\n3. Begin the translation process, keeping in mind the potential errors you've identified. Translate the text as accurately as possible, using your best judgment to interpret unclear or erroneous parts.\n\n4. If you come across a word or phrase that you cannot confidently translate due to potential OCR errors, provide your best guess for the translation but mark it with [?] to indicate uncertainty.\n\n5. Maintain the original formatting of the text as much as possible, including line breaks and paragraph structures.\n\n6. After completing the translation, briefly review it to ensure it reads coherently in the target language.\n\nProvide your translation inside <translation> tags. If you have any comments or notes about specific challenges you encountered during the translation process, include them after the translation inside <notes> tags.\n\nRemember, your goal is to provide an accurate translation while being mindful of potential OCR-related issues in the source text. Do your best to interpret and translate the intended meaning, even if the original text contains errors."
                    }
                ]
            }
        ]

import re
def extract_between_tags(tag: str, string: str, strip: bool = False) -> list[str]:
    ext_list = re.findall(f"<{tag}>(.+?)</{tag}>", string, re.DOTALL)
    if strip:
        ext_list = [e.strip() for e in ext_list]
    return ext_list

if __name__ == "__main__":
    claude = Claude_API()

    print("Translation from text")
    print("======================================")
    result = claude.call_translation_api("hello", 'jp')
    print(result)
    print(extract_between_tags('translation', result))

    print("\nOCR and Translation from image")
    print("======================================")
    image = 'eval_data/images/FF4_JP_1.jpg'
    base64_string = claude.preprocess(image)
    result = claude.call_translation_vision_api(base64_string)
    print(result)
    print(extract_between_tags('original_text', result))
    print(extract_between_tags('translation', result))