from pathlib import Path
import json

def evaluate(groundtruth, predictions):
    
    gt_values = {item['filename']: item['text_detected'] for item in groundtruth}
    pred_values = {item['filename']: item['text_detected'] for item in predictions}

    incorrect_filenames = [filename for filename in gt_values if gt_values[filename] != pred_values[filename]]

    TP = sum(1 for filename in gt_values if gt_values[filename] and pred_values[filename])
    TN = sum(1 for filename in gt_values if not gt_values[filename] and not pred_values[filename])
    FP = sum(1 for filename in gt_values if not gt_values[filename] and pred_values[filename])
    FN = sum(1 for filename in gt_values if gt_values[filename] and not pred_values[filename])

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (TP + TN) / (TP + TN + FP + FN) if (TP + TN + FP + FN) > 0 else 0

    return precision, recall, f1, accuracy, incorrect_filenames


if __name__ == "__main__":
    gt_file = Path('eval_data/gt.json')
    pred_file = Path('eval_data/preds.json')

    with open(gt_file) as f:
        ground_truths = json.load(f)
    
    with open(pred_file) as f:
        predictions = json.load(f)

    precision, recall, f1, accuracy, incorrect_filenames = evaluate(ground_truths, predictions)

    print(f'Precision : {precision}, Recall : {recall}, F1 : {f1}, Accuracy : {accuracy}')

    print('Incorrect filenames', incorrect_filenames)