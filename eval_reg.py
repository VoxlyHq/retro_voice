import json
from difflib import SequenceMatcher
from pathlib import Path
import string

class OCR_Evaluator:
    def __init__(self, predictions=None, ground_truths=None):
        self.predictions = predictions if predictions else []
        self.ground_truths = ground_truths if ground_truths else []

    def calculate_cer(self, pred_text, gt_text):
        pred_chars = list(pred_text)
        gt_chars = list(gt_text)
        matcher = SequenceMatcher(None, pred_chars, gt_chars)
        cer = 1 - matcher.ratio()
        return cer

    def calculate_wer(self, pred_text, gt_text):
        pred_words = pred_text.split()
        gt_words = gt_text.split()
        matcher = SequenceMatcher(None, pred_words, gt_words)
        wer = 1 - matcher.ratio()
        return wer

    def evaluate_pair(self, groundtruth, prediction):
        if groundtruth['filename'] == prediction['filename']:
            cer = self.calculate_cer(prediction['text'], groundtruth['text'])
            wer = self.calculate_wer(prediction['text'], groundtruth['text'])
            return {'filename': groundtruth['filename'], 'cer': cer, 'wer': wer}
        else:
            return {'error': 'Filenames do not match'}

    def evaluate(self):
        total_cer = 0
        total_wer = 0

        num_samples = len(self.predictions)

        for gt in self.ground_truths:
            filename = gt['filename']
            pred = next((item for item in self.predictions if item['filename'] == filename), '')
            cer = self.calculate_cer(pred['text'], gt['text'])
            wer = self.calculate_wer(pred['text'], gt['text'])
            total_cer += cer
            total_wer += wer

        average_cer = total_cer / num_samples if num_samples > 0 else 0
        average_wer = total_wer / num_samples if num_samples > 0 else 0
        return average_cer, average_wer

    def get_wrong_characters(self):
        wrong_chars = []
        for pred, gt in zip(self.predictions, self.ground_truths):
            for gt in self.ground_truths:
                filename = gt['filename']
                
                pred = next((item for item in self.predictions if item['filename'] == filename), None)
                pred_chars = list(pred['text'])
                gt_chars = list(gt['text'])
                
                matcher = SequenceMatcher(None, pred_chars, gt_chars)
                for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                    if tag != 'equal':
                        wrong_chars.append({
                            'filename': pred['filename'],
                            'predicted': pred['text'][i1:i2],
                            'ground_truth': gt['text'][j1:j2]
                        })
        return wrong_chars

    def get_wrong_words(self):
        wrong_words = []
        for pred, gt in zip(self.predictions, self.ground_truths):
            for gt in self.ground_truths:
                filename = gt['filename']
                
                pred = next((item for item in self.predictions if item['filename'] == filename), None)
                pred_words = pred['text'].split()
                gt_words = gt['text'].split()

                matcher = SequenceMatcher(None, pred_words, gt_words)
                for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                    if tag != 'equal':
                        wrong_words.append({
                            'filename': pred['filename'],
                            'predicted': ' '.join(pred_words[i1:i2]),
                            'ground_truth': ' '.join(gt_words[j1:j2])
                        })
        return wrong_words

    def print_evaluation(self, verbose=False):
        average_cer, average_wer = self.evaluate()
        print(f"Average Character Error Rate (CER): {average_cer * 100:.2f}%")
        print(f"Average Word Error Rate (WER): {average_wer * 100:.2f}%")

        wrong_chars = self.get_wrong_characters()
        wrong_words = self.get_wrong_words()

        if verbose:
            print("\nWrong Characters:")
            for item in wrong_chars:
                print(f"Filename: {item['filename']}, Predicted: {item['predicted']}, Ground Truth: {item['ground_truth']}")

            print("\nWrong Words:")
            for item in wrong_words:
                print(f"Filename: {item['filename']}, Predicted: {item['predicted']}, Ground Truth: {item['ground_truth']}")

def clean_text(text):
    # Convert to lower case
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove double spaces
    text = ' '.join(text.split())
    
    return text

if __name__ == "__main__":
    gt_file = Path('eval_data/gt.json')
    pred_file = Path('eval_data/preds_openai1.json')

    with open(gt_file, encoding='utf-8') as f:
        ground_truths = json.load(f)

    # only english for now
    ground_truths = [i for i in ground_truths if 'EN' in i["filename"]]
    
    with open(pred_file, encoding='utf-8') as f:
        predictions = json.load(f)

    for i in ground_truths:
        i['text'] = clean_text(i['text'])

    for i in predictions:
        i['text'] = clean_text(i['text'])
        
    evaluator = OCR_Evaluator(predictions, ground_truths)
    evaluator.print_evaluation()
