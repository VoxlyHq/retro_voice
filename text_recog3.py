# USAGE
# python text_recognition.py --east frozen_east_text_detection.pb --image images/example_01.jpg
# python text_recognition.py --east frozen_east_text_detection.pb --image images/example_04.jpg --padding 0.05

import numpy as np
import pytesseract
import argparse
import tensorflow as tf
from imutils.object_detection import non_max_suppression
from PIL import Image, ImageDraw

def decode_predictions(scores, geometry):
    (numRows, numCols) = scores.shape[1:3]
    rects = []
    confidences = []

    for y in range(numRows):
        scoresData = scores[0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        for x in range(numCols):
            if scoresData[x] < args["min_confidence"]:
                continue

            (offsetX, offsetY) = (x * 4.0, y * 4.0)
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])

    return (rects, confidences)

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
print(H, W)

# load the pre-trained EAST text detector
print("[INFO] loading EAST text detector...")

# Load the .pb file
graph = tf.Graph()
with graph.as_default():
    graph_def = tf.compat.v1.GraphDef()
    with tf.io.gfile.GFile(args["east"], "rb") as f:
        graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, name="")

layerNames = [
    "feature_fusion/Conv_7/Sigmoid",
    "feature_fusion/concat_3"]

# Perform forward pass
with tf.compat.v1.Session(graph=graph) as sess:
    image_tensor = graph.get_tensor_by_name("input_images:0")
    scores_tensor = graph.get_tensor_by_name(layerNames[0] + ":0")
    geometry_tensor = graph.get_tensor_by_name(layerNames[1] + ":0")

    blob = np.expand_dims(image, axis=0)
    print(f"Blob shape: {blob.shape}")
    (scores, geometry) = sess.run([scores_tensor, geometry_tensor], feed_dict={image_tensor: blob})

# decode the predictions, then apply non-maxima suppression to suppress weak, overlapping bounding boxes
(rects, confidences) = decode_predictions(scores, geometry)
boxes = non_max_suppression(np.array(rects), probs=confidences)

# initialize the list of results
results = []

# loop over the bounding boxes
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
    print(results)
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
        print(temp[0][1], result[0][1])
        temp = result

if swap:
   for p1, p2 in swap:
       swapPositions(results, p1, p2)

resultslist = []
for ((startX, startY, endX, endY), text) in results:
    print("OCR TEXT")
    print("========")
    print("{}\n".format(text))
    resultslist.append(text)

    text = "".join([c if ord(c) < 128 else "" for c in text]).strip()
    output = orig.copy()
    output = Image.fromarray(output)
    draw = ImageDraw.Draw(output)
    draw.rectangle([(startX, startY), (endX, endY)], outline="red", width=2)
    draw.text((startX, startY - 20), text, fill="red")

    output.show()

print(resultslist)
