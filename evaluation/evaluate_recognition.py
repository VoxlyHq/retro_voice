import json
from difflib import SequenceMatcher

class OCR_Evaluator:
    def __init__(self, prediction_file, ground_truth_file):
        self.prediction_file = prediction_file
        self.ground_truth_file = ground_truth_file
        self.predictions = self.load_json(prediction_file)
        self.ground_truths = self.load_json(ground_truth_file)

    def load_json(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

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

    def evaluate(self):
        total_cer = 0
        total_wer = 0
        num_samples = len(self.predictions)

        for pred, gt in zip(self.predictions, self.ground_truths):
            if pred['filename'] == gt['filename']:
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
            if pred['filename'] == gt['filename']:
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
            if pred['filename'] == gt['filename']:
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

    def print_evaluation(self):
        average_cer, average_wer = self.evaluate()
        print(f"Average Character Error Rate (CER): {average_cer * 100:.2f}%")
        print(f"Average Word Error Rate (WER): {average_wer * 100:.2f}%")

        wrong_chars = self.get_wrong_characters()
        wrong_words = self.get_wrong_words()

        print("\nWrong Characters:")
        for item in wrong_chars:
            print(f"Filename: {item['filename']}, Predicted: {item['predicted']}, Ground Truth: {item['ground_truth']}")

        print("\nWrong Words:")
        for item in wrong_words:
            print(f"Filename: {item['filename']}, Predicted: {item['predicted']}, Ground Truth: {item['ground_truth']}")

if __name__ == "__main__":
    prediction_file = 'eval_data/recognition_prediction_dummy.json'
    ground_truth_file = 'eval_data/recognition_ground_truth_dummy.json'
    evaluator = OCR_Evaluator(prediction_file, ground_truth_file)
    evaluator.print_evaluation()
