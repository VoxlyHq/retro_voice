import os
import sys
import json
import argparse
import numpy as np
from PIL import Image
from pathlib import Path

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from user_video import UserVideo  
from text_detector_fast import TextDetectorFast

def get_predictions(Uservideo, image_path):
    """
    Return the results of text detection, text recognition, and translation for the input image.
    """
    results = []

    print(image_path)
    game, lang, number = image_path.stem.split('_')
    img = Image.open(image_path)
    img = Uservideo.video_stream.preprocess_image(img, crop_y_coordinate=Uservideo.crop_height)
    
    image = Uservideo.video_stream.textDetector.preprocess_image(image=img)
    if not Uservideo.video_stream.textDetector.has_text(image):
        return {
            "image": str(image_path),
            "text_detected": False,
            "recognized_text": '',
            "annotations": [],
            "translation": ''
        }
    
    if lang == 'EN':
        closest_match, previous_image, highlighted_image, annotations, translation = Uservideo.frameProcessor.run_image(
            img, 
            translate=Uservideo.video_stream.background_task_args.get("translate", None), 
            enable_cache=Uservideo.video_stream.background_task_args.get("enable_cache", False)
        )

        return {
            "image": str(image_path),
            "text_detected": True,
            "recognized_text": closest_match,
            "annotations": annotations,
            "translation": translation
        }

    else:
        return {
            "image": str(image_path),
            "text_detected": True,
            "recognized_text": '',
            "annotations": [],
            "translation": ''
        }

def convert_bbox_from_points(points):
    """
    Convert a list of bounding box corner points to (xmin, xmax, ymin, ymax).

    :param points: List of points [[x1, y1], [x2, y2], [x3, y3], [x4, y4]].
    :return: A tuple (xmin, xmax, ymin, ymax).
    """
    x_coordinates = [point[0] for point in points]
    y_coordinates = [point[1] for point in points]
    
    xmin = min(x_coordinates)
    xmax = max(x_coordinates)
    ymin = min(y_coordinates)
    ymax = max(y_coordinates)
    
    return xmin, xmax, ymin, ymax

def main():
    parser = argparse.ArgumentParser(description="Process images for text detection, recognition, and translation.")
    parser.add_argument('--folder_path', type=str, default="eval_data/images", help="Path to the folder containing images.")
    parser.add_argument('--output_file', type=str, default="eval_data/preds.json", help="Output file path for the predictions.")

    args = parser.parse_args()

    lang = "en"
    disable_dialog = True
    disable_translation = False
    enable_cache = False
    translate = ""  
    text_detector = TextDetectorFast("weeeee", checkpoint="pretrained/fast_base_tt_640_finetune_ic17mlt.pth")  
    debug_bbox = False

    Uservideo = UserVideo(lang, disable_dialog, disable_translation, enable_cache, translate, text_detector, debug_bbox=False, crop_height=72)

    folder_path = Path(args.folder_path)
    results = []

    files = [i for i in folder_path.glob('*EN*.jpg')]
    for image_path in files[:10]:
        preds = get_predictions(Uservideo, image_path)

        bbox = [convert_bbox_from_points(annotation[0]) for annotation in preds['annotations']]
        bbox = [box.astype(int).tolist() for box in [np.array(point) for point in bbox]]

        results.append({
            'filename': image_path.stem,
            'text_detected': preds['text_detected'],
            'bbox': bbox,
            'text': preds['recognized_text'] if preds['recognized_text'] is not None else ''
        })

    with open(args.output_file, 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    main()
