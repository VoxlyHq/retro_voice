from collections import namedtuple
import numpy as np
import math
import importlib
from pathlib import Path
import json
import pprint


def evaluation_imports():
    """
    evaluation_imports: Dictionary ( key = module name , value = alias  )  with python modules used in the evaluation. 
    """    
    return {
            'Polygon':'plg',
            'numpy':'np'
            }

def evaluate_bboxes(groundtruth, predictions):
    """
    Evaluate bounding box predictions against ground truth.

    Args:
    groundtruth: List of dictionaries with 'filename' and 'bbox' keys. 
                 'bbox' is a list of tuples representing ground truth bounding boxes (xmin, xmax, ymin, ymax).
    predictions: List of dictionaries with 'filename' and 'bbox' keys. 
                 'bbox' is a list of tuples representing predicted bounding boxes (xmin, xmax, ymin, ymax).

    Returns:
    Dictionary containing evaluation metrics for each file and overall metrics.
    """
    for module,alias in evaluation_imports().items():
        globals()[alias] = importlib.import_module(module)    

    Rectangle = namedtuple('Rectangle', 'xmin xmax ymin ymax')

    def polygon_from_rectangle(rect):
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

    def get_intersection(pD, pG):
        pInt = pD & pG
        if len(pInt) == 0:
            return 0
        return pInt.area()

    def calculate_IoU(pD, pG):
        interaction = get_intersection(pD, pG)
        union = pD.area() + pG.area() - interaction
        if union == 0:
            return 0
        iou = interaction / union
        return iou

    def aggregate_metrics(metrics_list):
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


def overall_bbox(points):
    # finding largest x and y coordinates for bottom_right
    if points:
        xmin = min([i[0] for i in points])
        xmax = max([i[1] for i in points])
        ymin = min([i[2] for i in points])
        ymax = max([i[3] for i in points])

        return [(xmin, xmax, ymin, ymax)]
    else:
        return []

if __name__ == '__main__':
    gt_file = Path('eval_data/gt.json')
    pred_file = Path('eval_data/preds.json')

    with open(gt_file, encoding='utf-8') as f:
        groundtruth = json.load(f)
    
    with open(pred_file, encoding='utf-8') as f:
        predictions = json.load(f)

    for pred in predictions:
        pred['bbox'] = overall_bbox(pred['bbox'])
    for gt in groundtruth:
        gt['bbox'] = overall_bbox(gt['bbox'])

    metrics = evaluate_bboxes(groundtruth, predictions)
    pprint.pp(metrics['overall'])