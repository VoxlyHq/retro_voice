import json
import string
import argparse
import numpy as np
import Polygon as plg
from collections import namedtuple
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple, Any


class TextRecognitionEvaluator:
    def __init__(self, predictions: Optional[List[dict]] = None, ground_truths: Optional[List[dict]] = None) -> None:
        self.predictions = predictions if predictions else []
        self.ground_truths = ground_truths if ground_truths else []

    def calculate_cer(self, pred_text: str, gt_text: str) -> float:
        """
        Calculate Character Error Rate (CER) between predicted and ground truth text.
        """
        pred_chars = list(pred_text)
        gt_chars = list(gt_text)
        matcher = SequenceMatcher(None, pred_chars, gt_chars)
        cer = 1 - matcher.ratio()
        return cer

    def calculate_wer(self, pred_text: str, gt_text: str) -> float:
        """
        Calculate Word Error Rate (WER) between predicted and ground truth text.
        """
        pred_words = pred_text.split()
        gt_words = gt_text.split()
        matcher = SequenceMatcher(None, pred_words, gt_words)
        wer = 1 - matcher.ratio()
        return wer

    def evaluate(self) -> Tuple[float, float]:
        """
        Evaluate CER and WER for all predictions.
        """
        total_cer = 0
        total_wer = 0
        num_samples = len(self.predictions)

        for gt in self.ground_truths:
            filename = gt['filename']
            pred = next((item for item in self.predictions if item['filename'] == filename), '')
            if pred:
                cer = self.calculate_cer(pred['text'], gt['text'])
                wer = self.calculate_wer(pred['text'], gt['text'])
                total_cer += cer
                total_wer += wer

        average_cer = total_cer / num_samples if num_samples > 0 else 0
        average_wer = total_wer / num_samples if num_samples > 0 else 0
        return average_cer, average_wer

    def clean_text(self, text: str) -> str:
        """
        Clean text by converting to lowercase, removing punctuation, and extra spaces.
        """
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = ' '.join(text.split())
        return text

    def print_evaluation(self) -> None:
        """
        Print the evaluation summary.
        """
        average_cer, average_wer = self.evaluate()
        print("="*50)
        print(f"{'Recognition Evaluation':^50}")
        print("="*50)
        print(f"{'Average Character Error Rate (CER)':<35}: {average_cer * 100:.2f}%")
        print(f"{'Average Word Error Rate (WER)':<35}: {average_wer * 100:.2f}%")
        print("="*50)

class BoundingBoxEvaluator:
    def evaluate_bboxes(self, groundtruth: List[Dict[str, Any]], predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate bounding box predictions against ground truth.

        Args:
            groundtruth : List of ground truth data, each containing 'filename' and 'bbox'.
            predictions : List of prediction data, each containing 'filename' and 'bbox'.

        Returns:
            Dict[str, Any]: Dictionary containing evaluation metrics for each file and overall metrics.
        """

        Rectangle = namedtuple('Rectangle', 'xmin xmax ymin ymax')

        def polygon_from_rectangle(rect: Rectangle) -> Any:
            """
            Create a polygon from a rectangle.

            Args:
                rect (Rectangle): Namedtuple representing the rectangle coordinates.

            Returns:
                Any: Polygon object created from the rectangle.
            """
            resBoxes = np.empty([1, 8], dtype='int32')
            resBoxes[0, 0] = int(rect.xmin)
            resBoxes[0, 4] = int(rect.ymin)
            resBoxes[0, 1] = int(rect.xmax)
            resBoxes[0, 5] = int(rect.ymin)
            resBoxes[0, 2] = int(rect.xmax)
            resBoxes[0, 6] = int(rect.ymax)
            resBoxes[0, 3] = int(rect.xmin)
            resBoxes[0, 7] = int(rect.ymax)
            pointMat = resBoxes[0].reshape([2, 4]).T
            return plg.Polygon(pointMat)

        def get_intersection(pD: Any, pG: Any) -> float:
            """
            Get the intersection area of two polygons.
            """
            pInt = pD & pG
            if len(pInt) == 0:
                return 0
            return pInt.area()

        def calculate_IoU(pD: Any, pG: Any) -> float:
            """
            Calculate the Intersection over Union (IoU) of two polygons.
            """
            interaction = get_intersection(pD, pG)
            union = pD.area() + pG.area() - interaction
            if union == 0:
                return 0
            iou = interaction / union
            return iou

        def aggregate_metrics(metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
            """
            Aggregate metrics from a list of individual file metrics.
            """
            total_recall = sum([metrics['recall'] for metrics in metrics_list])
            total_precision = sum([metrics['precision'] for metrics in metrics_list])
            total_iou = sum([metrics['IoU'] for metrics in metrics_list])
            n = len(metrics_list)
            recall = total_recall / n
            precision = total_precision / n
            iou = total_iou / n
            hmean = 0 if (precision + recall) == 0 else 2.0 * precision * recall / (precision + recall)
            return {'recall': recall, 'precision': precision, 'hmean': hmean, 'IoU': iou}

        results = {}
        metrics_list = []

        for gt_entry in groundtruth:
            filename = gt_entry['filename']
            gt_bboxes = gt_entry['bbox']
            pred_entry = next((item for item in predictions if item['filename'] == filename), None)

            if pred_entry is None or not gt_bboxes or not pred_entry['bbox']:
                continue

            pred_bboxes = pred_entry['bbox']
            gtPols = [polygon_from_rectangle(Rectangle(*bbox)) for bbox in gt_bboxes]
            detPols = [polygon_from_rectangle(Rectangle(*bbox)) for bbox in pred_bboxes]

            recallMat = np.empty([len(gtPols), len(detPols)])
            precisionMat = np.empty([len(gtPols), len(detPols)])
            iouMat = np.empty([len(gtPols), len(detPols)])

            for gtNum in range(len(gtPols)):
                for detNum in range(len(detPols)):
                    pG = gtPols[gtNum]
                    pD = detPols[detNum]
                    intersected_area = get_intersection(pD, pG)
                    recallMat[gtNum, detNum] = 0 if pG.area() == 0 else intersected_area / pG.area()
                    precisionMat[gtNum, detNum] = 0 if pD.area() == 0 else intersected_area / pD.area()
                    iouMat[gtNum, detNum] = calculate_IoU(pD, pG)

            numGtCare = len(gtPols)
            numDetCare = len(detPols)
            recall = np.mean([recallMat[i, :].max() for i in range(numGtCare)])
            precision = np.mean([precisionMat[:, j].max() for j in range(numDetCare)])
            hmean = 0 if (precision + recall) == 0 else 2.0 * precision * recall / (precision + recall)
            iou = np.mean([iouMat[i, :].max() for i in range(numGtCare)])

            metrics = {'recall': recall, 'precision': precision, 'hmean': hmean, 'IoU': iou}
            metrics_list.append(metrics)
            results[filename] = metrics

        overall_metrics = aggregate_metrics(metrics_list)
        results['overall'] = overall_metrics

        return results

    def print_evaluation(self, bbox_metrics: Dict[str, float]) -> None:
        """
        Print the bounding box evaluation summary.
        """
        precision_bbox = bbox_metrics['overall']['precision']
        recall_bbox = bbox_metrics['overall']['recall']
        hmean_bbox = bbox_metrics['overall']['hmean']
        iou_bbox = bbox_metrics['overall']['IoU']
        print("="*50)
        print(f"{'Bounding Box Evaluation':^50}")
        print("="*50)
        print(f"{'Precision':<20}: {precision_bbox:.2f}")
        print(f"{'Recall':<20}: {recall_bbox:.2f}")
        print(f"{'Hmean':<20}: {hmean_bbox:.2f}")
        print(f"{'IoU':<20}: {iou_bbox:.2f}")
        print("="*50)


class TextDetectionEvaluator:
    def evaluate_text_detection(self, groundtruth: List[Dict[str, Any]], predictions: List[Dict[str, Any]]) -> Tuple[float, float, float, float, List[str]]:

        # Create dictionaries with filename as the key and text detection result as the value
        gt_values = {item['filename']: item['text_detected'] for item in groundtruth}
        pred_values = {item['filename']: item['text_detected'] for item in predictions}

        # Identify filenames with incorrect text detection results
        incorrect_filenames = [filename for filename in gt_values if gt_values[filename] != pred_values[filename]]

        # Calculate True Positives (TP), True Negatives (TN), False Positives (FP), and False Negatives (FN)
        TP = sum(1 for filename in gt_values if gt_values[filename] and pred_values[filename])
        TN = sum(1 for filename in gt_values if not gt_values[filename] and not pred_values[filename])
        FP = sum(1 for filename in gt_values if not gt_values[filename] and pred_values[filename])
        FN = sum(1 for filename in gt_values if gt_values[filename] and not pred_values[filename])

        # Calculate precision, recall, F1 score, and accuracy
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (TP + TN) / (TP + TN + FP + FN) if (TP + TN + FP + FN) > 0 else 0

        return precision, recall, f1, accuracy, incorrect_filenames

    def print_evaluation(self, precision_text: float, recall_text: float, f1_text: float, accuracy_text: float, incorrect_filenames_text: List[str]) -> None:
        print(f"{'Detection Evaluation':^50}")
        print("="*50)
        print(f"{'Precision':<20}: {precision_text:.2f}")
        print(f"{'Recall':<20}: {recall_text:.2f}")
        print(f"{'F1 Score':<20}: {f1_text:.2f}")
        print(f"{'Accuracy':<20}: {accuracy_text:.2f}")
        print("="*50)
        print(f'Incorrect filenames for text detection: {incorrect_filenames_text}')
        print("="*50)

def main(gt_file_path, pred_file_path):
    try:
        with open(gt_file_path, encoding='utf-8') as f:
            ground_truths = json.load(f)
    except Exception as e:
        print(f"Error reading ground truth file: {e}")
        return

    try:
        with open(pred_file_path, encoding='utf-8') as f:
            predictions = json.load(f)
    except Exception as e:
        print(f"Error reading predictions file: {e}")
        return

    # Filter ground truths for English texts
    ground_truths = [i for i in ground_truths if 'EN' in i["filename"]]

    text_recognition_evaluator = TextRecognitionEvaluator()
    for i in ground_truths:
        i['text'] = text_recognition_evaluator.clean_text(i['text'])
    for i in predictions:
        i['text'] = text_recognition_evaluator.clean_text(i['text'])

    text_recognition_evaluator.predictions = predictions
    text_recognition_evaluator.ground_truths = ground_truths
    text_recognition_evaluator.print_evaluation()

    for pred in predictions:
        pred['bbox'] = overall_bbox(pred['bbox'])
    for gt in ground_truths:
        gt['bbox'] = overall_bbox(gt['bbox'])

    bbox_evaluator = BoundingBoxEvaluator()
    bbox_metrics = bbox_evaluator.evaluate_bboxes(ground_truths, predictions)
    bbox_evaluator.print_evaluation(bbox_metrics)

    text_detection_evaluator = TextDetectionEvaluator()
    precision_text, recall_text, f1_text, accuracy_text, incorrect_filenames_text = text_detection_evaluator.evaluate_text_detection(ground_truths, predictions)
    text_detection_evaluator.print_evaluation(precision_text, recall_text, f1_text, accuracy_text, incorrect_filenames_text)

def overall_bbox(points):
    """
    Calculate the overall bounding box for a set of points.
    """
    if points:
        xmin = min([i[0] for i in points])
        xmax = max([i[1] for i in points])
        ymin = min([i[2] for i in points])
        ymax = max([i[3] for i in points])
        return [(xmin, xmax, ymin, ymax)]
    else:
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evaluate OCR predictions.')
    parser.add_argument('--gt_file', type=str, default='eval_data/gt10.json', help='Path to the ground truth file')
    parser.add_argument('--pred_file', type=str, default='eval_data/preds.json', help='Path to the predictions file')
    args = parser.parse_args()

    main(args.gt_file, args.pred_file)
