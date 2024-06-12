import json
import math
from collections import Counter

def ngram(tokens, n):
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

def modified_precision(reference, candidate, n):
    ref_ngrams = Counter(ngram(reference, n))
    cand_ngrams = Counter(ngram(candidate, n))
    numerator = sum(min(count, ref_ngrams[gram]) for gram, count in cand_ngrams.items())
    denominator = sum(cand_ngrams.values())
    return numerator / denominator if denominator > 0 else 0

def calculate_bleu(reference, candidate, max_n=4):
    if len(candidate) == 0:
        return 0.0
    weights = [0.25] * 4
    p_ns = [modified_precision(reference, candidate, i) for i in range(1, max_n+1)]
    s = math.fsum(w * math.log(p) for w, p in zip(weights, p_ns) if p > 0)
    bp = math.exp(min(1 - len(reference) / len(candidate), 0))
    return bp * math.exp(s)

class TranslationEvaluator:
    def __init__(self, prediction_file, ground_truth_file):
        self.prediction_file = prediction_file
        self.ground_truth_file = ground_truth_file
        self.predictions = self.load_json(prediction_file)
        self.ground_truths = self.load_json(ground_truth_file)

    def load_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def evaluate(self):
        total_bleu = 0
        num_samples = len(self.predictions)
        filename_to_gt = {item['filename']: item['text'] for item in self.ground_truths}

        for pred in self.predictions:
            filename = pred['filename']
            if filename in filename_to_gt:
                reference_text = filename_to_gt[filename].split()
                candidate_text = pred['translated_text'].split()
                if reference_text and candidate_text:  # Ensure both texts are not empty
                    bleu = calculate_bleu(reference_text, candidate_text)
                    total_bleu += bleu

        average_bleu = total_bleu / num_samples if num_samples > 0 else 0
        return average_bleu

    def get_wrong_translations(self):
        wrong_translations = []
        filename_to_gt = {item['filename']: item['text'] for item in self.ground_truths}

        for pred in self.predictions:
            filename = pred['filename']
            if filename in filename_to_gt:
                reference_text = filename_to_gt[filename].split()
                candidate_text = pred['translated_text'].split()
                if reference_text and candidate_text:  # Ensure both texts are not empty
                    bleu_score = calculate_bleu(reference_text, candidate_text)
                    if bleu_score < 1.0:  # assuming perfect translations should have a BLEU score of 1.0
                        wrong_translations.append({
                            'filename': pred['filename'],
                            'original_text': pred['original_text'],
                            'translated_text': ' '.join(candidate_text),
                            'ground_truth': ' '.join(reference_text),
                            'bleu_score': bleu_score
                        })
        return wrong_translations

    def print_evaluation(self):
        average_bleu = self.evaluate()
        print(f"Average BLEU Score: {average_bleu * 100:.2f}%")

        wrong_translations = self.get_wrong_translations()

        print("\nWrong Translations:")
        for item in wrong_translations:
            print(f"Filename: {item['filename']}")
            print(f"Original Text: {item['original_text']}")
            print(f"Translated Text: {item['translated_text']}")
            print(f"Ground Truth: {item['ground_truth']}")
            print(f"BLEU Score: {item['bleu_score']:.2f}\n")

# Usage
prediction_file = 'eval_data/translation_prediction_dummy.json'
ground_truth_file = 'eval_data/translation_ground_truth_dummy.json'
evaluator = TranslationEvaluator(prediction_file, ground_truth_file)
evaluator.print_evaluation()
