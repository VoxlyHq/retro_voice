import argparse
from enum import Enum

class OCREngine(Enum):
    EASYOCR = 1
    OPENAI = 2
    OCR_TRANSLATE = 3

    @staticmethod
    def from_str(label):
        if label.lower() in ('easyocr', 'openai', 'ocr_translate'):
            return OCREngine[label.upper()]
        else:
            raise argparse.ArgumentTypeError(f"Invalid value for OCR method: {label}")