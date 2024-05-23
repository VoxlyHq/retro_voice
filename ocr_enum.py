import argparse
from enum import Enum

class OCREngine(Enum):
    EASYOCR = 1
    OPENAI = 2

    @staticmethod
    def from_str(label):
        if label.lower() in ('easyocr', 'openai'):
            return OCREngine[label.upper()]
        else:
            raise argparse.ArgumentTypeError(f"Invalid value for OCR method: {label}")