import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from eval import TextRecognitionEvaluator, BoundingBoxEvaluator, TextDetectionEvaluator
from generate_predictions import get_predictions, convert_bbox_from_points

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from user_video import UserVideo  
from text_detector_fast import TextDetectorFast

def main():
    parser = argparse.ArgumentParser(description="Process images for text detection, recognition, and translation, and evaluate the results.")
    parser.add_argument('--folder_path', type=str, default="eval_data/images", help="Path to the folder containing images.")
    parser.add_argument('--pred_file', type=str, default="eval_data/preds.json", help="Output file path for the predictions.")
    parser.add_argument('--gt_file', type=str, default='eval_data/gt.json', help='Path to the ground truth file')

    args = parser.parse_args()

    if not os.path.exists(args.pred_file):
        lang = "en"
        disable_dialog = True
        disable_translation = False
        enable_cache = False
        translate = ""  
        text_detector = TextDetectorFast("weeeee", checkpoint="pretrained/fast_base_tt_640_finetune_ic17mlt.pth")  
        debug_bbox = False

        Uservideo = UserVideo(lang, disable_dialog, disable_translation, enable_cache, translate, text_detector, debug_bbox=debug_bbox, crop_height=72)

        folder_path = Path(args.folder_path)
        results = []

        files = [i for i in folder_path.glob('*EN*.jpg')]
        for image_path in files:
            preds = get_predictions(Uservideo, image_path)

            bbox = [convert_bbox_from_points(annotation[0]) for annotation in preds['annotations']]
            bbox = [box.astype(int).tolist() for box in [np.array(point) for point in bbox]]

            results.append({
                'filename': image_path.stem,
                'text_detected': preds['text_detected'],
                'bbox': bbox,
                'text': preds['recognized_text'] if preds['recognized_text'] is not None else ''
            })

        with open(args.pred_file, 'w') as f:
            json.dump(results, f, indent=4)

    try:
        with open(args.gt_file, encoding='utf-8') as f:
            ground_truths = json.load(f)
    except Exception as e:
        print(f"Error reading ground truth file: {e}")
        return

    try:
        with open(args.pred_file, encoding='utf-8') as f:
            predictions = json.load(f)
    except Exception as e:
        print(f"Error reading predictions file: {e}")
        return

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
    main()
