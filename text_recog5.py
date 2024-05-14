import numpy as np
import pytesseract
import argparse
import tensorflow as tf
import time
from PIL import Image
import os

# Set TensorFlow logging level to errors only
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def decode_predictions(scores, geometry):
    (numRows, numCols) = scores.shape[1:3]
    rects = []
    confidences = []

    for y in range(numRows):
        scoresData = scores[0, y]
        for x in range(numCols):
            if scoresData[x] < args["min_confidence"]:
                continue

            xData0 = geometry[0, y, x, 0]
            xData1 = geometry[0, y, x, 1]
            xData2 = geometry[0, y, x, 2]
            xData3 = geometry[0, y, x, 3]

            (offsetX, offsetY) = (x * 4.0, y * 4.0)
            anglesData = geometry[0, y, x, 4]
            angle = anglesData
            cos = np.cos(angle)
            sin = np.sin(angle)
            h = xData0 + xData2
            w = xData1 + xData3
            endX = int(offsetX + (cos * xData1) + (sin * xData2))
            endY = int(offsetY - (sin * xData1) + (cos * xData2))
            startX = int(endX - w)
            startY = int(endY - h)

            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])

    return (rects, confidences)

def non_max_suppression(boxes, scores, overlapThresh=0.3):
    if len(boxes) == 0:
        return []

    boxes = np.array(boxes)
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    pick = []
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(scores)

    while len(idxs) > 0:
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)
        overlap = (w * h) / area[idxs[:last]]

        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0])))

    return boxes[pick].astype("int")

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", type=str, help="path to input image")
ap.add_argument("-east", "--east", type=str, help="path to input EAST text detector")
ap.add_argument("-c", "--min-confidence", type=float, default=0.5, help="minimum probability required to inspect a region")
ap.add_argument("-w", "--width", type=int, default=320, help="nearest multiple of 32 for resized width")
ap.add_argument("-e", "--height", type=int, default=320, help="nearest multiple of 32 for resized height")
ap.add_argument("-p", "--padding", type=float, default=0.0, help="amount of padding to add to each border of ROI")
args = vars(ap.parse_args())

# load the input image and grab the image dimensions
image = Image.open(args["image"])
image = image.convert('RGB')
orig = np.array(image)
(origH, origW) = orig.shape[:2]

# set the new width and height and then determine the ratio in change
(newW, newH) = (args["width"], args["height"])
rW = origW / float(newW)
rH = origH / float(newH)

# resize the image and grab the new image dimensions
image = image.resize((newW, newH))
image = np.array(image)
(H, W) = image.shape[:2]

# load the pre-trained EAST text detector
graph = tf.Graph()
with graph.as_default():
    graph_def = tf.compat.v1.GraphDef()
    with tf.io.gfile.GFile(args["east"], "rb") as f:
        graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, name="")

layerNames = [
    "feature_fusion/Conv_7/Sigmoid",
    "feature_fusion/concat_3"]

total_duration = 0

with tf.compat.v1.Session(graph=graph) as sess:
    image_tensor = graph.get_tensor_by_name("input_images:0")
    scores_tensor = graph.get_tensor_by_name(layerNames[0] + ":0")
    geometry_tensor = graph.get_tensor_by_name(layerNames[1] + ":0")

    # Perform forward pass
    for _ in range(10):
        start_time = time.time()
        blob = np.expand_dims(image, axis=0)
        (scores, geometry) = sess.run([scores_tensor, geometry_tensor], feed_dict={image_tensor: blob})

        # Decode the predictions, then apply non-maxima suppression to suppress weak, overlapping bounding boxes
        (rects, confidences) = decode_predictions(scores, geometry)
        boxes = non_max_suppression(rects, confidences)

        flattened_confidences = np.concatenate(confidences).ravel()
        boxes = non_max_suppression(rects, flattened_confidences)

        # Initialize the list of results
        results = []

        # Loop over the bounding boxes
        for (startX, startY, endX, endY) in boxes:
            startX = int(startX * rW)
            startY = int(startY * rH)
            endX = int(endX * rW)
            endY = int(endY * rH)

            dX = int((endX - startX) * args["padding"])
            dY = int((endY - startY) * args["padding"])

            startX = max(0, startX - dX)
            startY = max(0, startY - dY)
            endX = min(origW, endX + (dX * 2))
            endY = min(origH, endY + (dY * 2))

            startX = startX - 10
            startY = startY - 5
            endX = endX + 10
            endY = endY + 10

            roi = orig[startY:endY, startX-3:endX+3]

            config = ("-l eng --oem 1 --psm 7")
            text = pytesseract.image_to_string(roi, config=config)

            results.append(((startX, startY, endX, endY), text))

        results = sorted(results, key=lambda r: r[0][1])

        def swapPositions(list, pos1, pos2):
            list[pos1], list[pos2] = list[pos2], list[pos1]
            return list

        First = True
        swap = []
        for pos, result in enumerate(results):
            if First:
                temp = result
                First = False
            else:
                if (temp[0][1] + 10) >= result[0][1]:
                    if temp[0][0] > result[0][0]:
                        swap.append((pos - 1, pos))
                temp = result

        if swap:
            for p1, p2 in swap:
                swapPositions(results, p1, p2)

        end_time = time.time()
        total_duration += (end_time - start_time)

average_duration = total_duration / 10
print(f"Average duration: {average_duration:.4f} seconds")
print(f"Total duration: {total_duration:.4f} seconds")
