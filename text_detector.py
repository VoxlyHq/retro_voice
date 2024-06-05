import numpy as np
import argparse
import time
import os

from PIL import Image
import tensorflow as tf

# Set TensorFlow logging level to errors only
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class TextDetector:
    def __init__(self, east_path, min_confidence=0.5, width=320, height=320, padding=0.0):
        self.east_path = east_path
        self.min_confidence = min_confidence
        self.width = width
        self.height = height
        self.padding = padding

        self.graph = self.load_model()
        self.layerNames = ["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"]
        self.sess = tf.compat.v1.Session(graph=self.graph)
        self.image_tensor = self.sess.graph.get_tensor_by_name("input_images:0")
        self.scores_tensor = self.sess.graph.get_tensor_by_name(self.layerNames[0] + ":0")
        self.geometry_tensor = self.sess.graph.get_tensor_by_name(self.layerNames[1] + ":0")

    def load_image(self, image_path):
        image = Image.open(image_path).convert('RGB')
        orig = np.array(image)
        origH, origW = orig.shape[:2]

        rW, rH = origW / float(self.width), origH / float(self.height)
        image = image.resize((self.width, self.height))
        image = np.array(image)
        return image, orig, rW, rH, origW, origH

    def preprocess_image(self, image):
        image = image.convert('RGB')
        
        image = image.resize((self.width, self.height))
        image = np.array(image)
        return image

    def load_model(self):
        graph = tf.Graph()
        with graph.as_default():
            graph_def = tf.compat.v1.GraphDef()
            with tf.io.gfile.GFile(self.east_path, "rb") as f:
                graph_def.ParseFromString(f.read())
                tf.import_graph_def(graph_def, name="")
        return graph

    @staticmethod
    def decode_predictions(scores, geometry, min_confidence):
        (numRows, numCols) = scores.shape[1:3]
        rects = []
        confidences = []

        for y in range(numRows):
            scoresData = scores[0, y]
            for x in range(numCols):
                if scoresData[x] < min_confidence:
                    continue

                xData0 = geometry[0, y, x, 0]
                xData1 = geometry[0, y, x, 1]
                xData2 = geometry[0, y, x, 2]
                xData3 = geometry[0, y, x, 3]

                (offsetX, offsetY) = (x * 4.0, y * 4.0)
                angle = geometry[0, y, x, 4]
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

        return rects, confidences

    @staticmethod
    def non_max_suppression(boxes, scores, overlap_thresh=0.3):
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

            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlap_thresh)[0])))

        return boxes[pick].astype("int")

    def process_single_image(self, image):

        image = image.convert('RGB')
        orig = np.array(image)
        origH, origW = orig.shape[:2]

        rW, rH = origW / float(self.width), origH / float(self.height)
        image = image.resize((self.width, self.height))
        image = np.array(image)
        
        blob = np.expand_dims(image, axis=0)
        scores, geometry = self.sess.run([self.scores_tensor, self.geometry_tensor], feed_dict={self.image_tensor: blob})
        
        rects, confidences = self.decode_predictions(scores, geometry, self.min_confidence)
        if confidences == []:
            return []
        flattened_confidences = np.concatenate(confidences).ravel()
        boxes = self.non_max_suppression(rects, flattened_confidences)

        results = []
        for startX, startY, endX, endY in boxes:
            startX, startY, endX, endY = int(startX * rW), int(startY * rH), int(endX * rW), int(endY * rH)

            dX, dY = int((endX - startX) * self.padding), int((endY - startY) * self.padding)
            startX, startY = max(0, startX - dX), max(0, startY - dY)
            endX, endY = min(origW, endX + (dX * 2)), min(origH, endY + (dY * 2))

            results.append((startX, startY, endX, endY))

        results = sorted(results, key=lambda r: r[0])

        # Swapping logic
        def swap_positions(lst, pos1, pos2):
            lst[pos1], lst[pos2] = lst[pos2], lst[pos1]
            return lst

        first = True
        swap = []
        for pos, result in enumerate(results):
            if first:
                temp = result
                first = False
            else:
                if temp[1] + 10 >= result[1]:
                    if temp[0] > result[0]:
                        swap.append((pos - 1, pos))
                temp = result

        if swap:
            for p1, p2 in swap:
                swap_positions(results, p1, p2)

        return results
        
        
    def has_text(self, image):
        
        blob = np.expand_dims(image, axis=0)
        scores, geometry = self.sess.run([self.scores_tensor, self.geometry_tensor], feed_dict={self.image_tensor: blob})
        
        rects, confidences = self.decode_predictions(scores, geometry, self.min_confidence)
        # Check if there are any confidences above the min_confidence threshold
        if len(confidences) > 0:
            return True
        return False

    def close_session(self):
        self.sess.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--images", type=str, nargs='+', required=True, help="paths to input images")
    ap.add_argument("-east", "--east", type=str, required=True, help="path to input EAST text detector")
    ap.add_argument("-c", "--min-confidence", type=float, default=0.5, help="minimum probability required to inspect a region")
    ap.add_argument("-w", "--width", type=int, default=320, help="nearest multiple of 32 for resized width")
    ap.add_argument("-e", "--height", type=int, default=320, help="nearest multiple of 32 for resized height")
    ap.add_argument("-p", "--padding", type=float, default=0.0, help="amount of padding to add to each border of ROI")
    args = vars(ap.parse_args())

    total_duration = 0
    image_path = args["images"][0]
    
    abs_start_time = time.time()

    detector = TextDetector(args["east"], args["min_confidence"], args["width"], args["height"], args["padding"])
    image = detector.preprocess_image(Image.open(image_path))
    for i in range(100):
        start_time = time.time()
        results = detector.has_text(image)
        # print(f"Results for {image_path}:")
        
        # print(results)
        end_time = time.time()
        total_duration += end_time - start_time
    detector.close_session()
    average_duration = total_duration / 100
    print(f"Average duration: {average_duration:.4f} seconds")
    print(f"Total duration: {total_duration:.4f} seconds")
    fps = 100 / (time.time() - abs_start_time)
    print(f"FPS: {fps:.2f}")