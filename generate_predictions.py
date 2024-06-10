import os
from user_video import UserVideo  # Ensure this imports your UserVideo class correctly
from pathlib import Path
from text_detector_fast import TextDetectorFast
import pprint
import json
import numpy as np

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


if __name__ == "__main__":
    lang = "jp"
    disable_dialog = True
    disable_translation = False
    enable_cache = False
    translate = ""  
    text_detector = TextDetectorFast("weeeee", checkpoint="pretrained/fast_base_tt_640_finetune_ic17mlt.pth")  
    debug_bbox = False

    user_video = UserVideo(lang, disable_dialog, disable_translation, enable_cache, translate, text_detector, debug_bbox=False, eval=True)

    # Path to the folder containing images
    folder_path = Path("eval_data/images")

    results = []
    files = [i for i in folder_path.glob('*EN*.jpg')]
    for image_path in files:

        preds = user_video.get_predictions(image_path)

        bbox =  [i[0] for i in preds['annotations']]
        bbox = [convert_bbox_from_points(i) for i in bbox]
        bbox = [box.astype(int).tolist() for box in [np.array(point) for point in bbox]]

        results.append({'filename' : image_path.stem,
                        'text_detected' : preds['text_detected'],
                        'bbox' : bbox, 
                        'text' : preds['recognized_text'] if preds['recognized_text'] is not None else ''})

    with open('eval_data/preds.json', 'w') as f:
        json.dump(results, f, indent=4)

