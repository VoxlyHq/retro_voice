"""  
Copyright (c) 2019-present NAVER Corp.
MIT License
"""

# -*- coding: utf-8 -*-
import cupy as cp
import numpy as np
import cv2
import math
from scipy.ndimage import label
import numba

def threshold_image(image, low_text):
    # Perform thresholding using cv2 (outside Numba)
    _, thresholded_image = cv2.threshold(image, low_text, 1, 0)
    return thresholded_image

@numba.njit
def getDetBoxes_core(textmap, linkmap, text_threshold, link_threshold, low_text, estimate_num_chars=False):
    # Ensure the correct data type and prepare data
    textmap = (textmap * 255).astype(np.uint8)
    linkmap = (linkmap * 255).astype(np.uint8)
    img_h, img_w = textmap.shape

    # Thresholding
    text_score = threshold_image(textmap, low_text, 1, 0)
    link_score = threshold_image(linkmap, link_threshold, 1, 0)
    text_score_comb = np.clip(text_score + link_score, 0, 1).astype(np.uint8)

    # Connected components
    nLabels, labels, stats, centroids = cv2.connectedComponentsWithStats(text_score_comb, connectivity=4)

    det = []
    mapper = []
    for k in range(1, nLabels):
        size = stats[k, cv2.CC_STAT_AREA]
        if size < 10:
            continue

        if np.max(textmap[labels == k]) < text_threshold:
            continue

        segmap = np.zeros_like(textmap)
        segmap[labels == k] = 255

        if estimate_num_chars:
            character_locs = (textmap - linkmap) * segmap / 255.0
            _, character_locs = cv2.threshold(character_locs, text_threshold, 1, 0)
#            _, n_chars = label(character_locs)
#            mapper.append(n_chars)
        else:
            mapper.append(k)

        segmap[(link_score == 1) & (text_score == 0)] = 0

        x, y, w, h = stats[k, cv2.CC_STAT_LEFT], stats[k, cv2.CC_STAT_TOP], stats[k, cv2.CC_STAT_WIDTH], stats[k, cv2.CC_STAT_HEIGHT]
        niter = int(math.sqrt(size * min(w, h) / (w * h)) * 2)
        sx, ex = max(0, x - niter), min(img_w, x + w + niter + 1)
        sy, ey = max(0, y - niter), min(img_h, y + h + niter + 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1 + niter, 1 + niter))
        segmap[sy:ey, sx:ex] = cv2.dilate(segmap[sy:ey, sx:ex], kernel)

        np_contours = np.roll(np.array(np.where(segmap != 0)), 1, axis=0).transpose().reshape(-1, 2)
        rectangle = cv2.minAreaRect(np_contours)
        box = cv2.boxPoints(rectangle)

        w, h = np.linalg.norm(box[0] - box[1]), np.linalg.norm(box[1] - box[2])
        box_ratio = max(w, h) / (min(w, h) + 1e-5)
        if abs(1 - box_ratio) <= 0.1:
            l, r = min(np_contours[:, 0]), max(np_contours[:, 0])
            t, b = min(np_contours[:, 1]), max(np_contours[:, 1])
            box = np.array([[l, t], [r, t], [r, b], [l, b]], dtype=np.float32)

        startidx = box.sum(axis=1).argmin()
        box = np.roll(box, 4 - startidx, 0)
        det.append(box)

    return det, labels, mapper


def getDetBoxes(textmap, linkmap, text_threshold, link_threshold, low_text, poly=False, estimate_num_chars=False):
    if poly and estimate_num_chars:
        raise Exception("Estimating the number of characters not currently supported with poly.")
    boxes, labels, mapper = getDetBoxes_core(textmap, linkmap, text_threshold, link_threshold, low_text, estimate_num_chars)

    if poly:
        polys = getPoly_core(boxes, labels, mapper, linkmap)
    else:
        polys = [None] * len(boxes)

    return boxes, polys, mapper

def adjustResultCoordinates(polys, ratio_w, ratio_h, ratio_net = 2):
    if len(polys) > 0:
        polys = np.array(polys)
        for k in range(len(polys)):
            if polys[k] is not None:
                polys[k] *= (ratio_w * ratio_net, ratio_h * ratio_net)
    return polys
