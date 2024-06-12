import json
from pathlib import Path

def convert_bbox_from_points(points):
    """
    Convert a list of bounding box corner points to (xmin, xmax, ymin, ymax).

    :param points: List of points [[x1, y1], [x2, y2]].
    :return: A tuple (xmin, xmax, ymin, ymax).
    """
    x_coordinates = [point[0] for point in points]
    y_coordinates = [point[1] for point in points]
    
    xmin = min(x_coordinates)
    xmax = max(x_coordinates)
    ymin = min(y_coordinates)
    ymax = max(y_coordinates)
    
    return xmin, xmax, ymin, ymax



if __name__ == '__main__':
    folder = Path('eval_data/images')
    output_file = Path('eval_data/gt.json')
    results = []
    files = [i for i in folder.glob('*.json')]
    for file in files:
        data = []
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        bbox = [convert_bbox_from_points(i['points']) for i in data['shapes']]
        text = ' '.join([i['description'] for i in data['shapes']])
        results.append({'filename' : file.stem,
                         'bbox' : bbox,
                         'text' : text})
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False,indent=4)