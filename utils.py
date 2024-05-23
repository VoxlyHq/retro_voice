import io
import platform
import numpy as np
from collections import Counter
from PIL import Image, ImageDraw, ImageFont

os_name = platform.system()
if os_name == 'Windows':
    font_path = "C:/Windows/Fonts/YuGothB.ttc"
elif os_name == 'Darwin':
    font_path = "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc"
else:
    raise Exception(f"Unsupported OS: {os_name}")

def draw_highlight(image_bytes, result, outline_color="red", text_color="yellow", outline_width=2):
    """
    Draw bounding boxes and text on the image based on OCR results.

    :param image_bytes: The image in bytes
    :param result: OCR result containing bounding boxes and text
    :param outline_color: Color of the bounding box outline
    :param text_color: Color of the text
    :param outline_width: Width of the bounding box outline
    :return: The annotated image as a PIL Image
    """
    drawable_image = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(drawable_image)
    for bbox, text, prob in result:
        try:
            top_left, bottom_right = tuple(map(int, bbox[0])), tuple(map(int, bbox[2]))
            draw.rectangle([top_left, bottom_right], outline=outline_color, width=outline_width)
            draw.text(top_left, text, fill=text_color)
        except Exception as e:
            print(f"Error drawing rectangle - {top_left} - {bottom_right}: {e}")
    return drawable_image

def cal_abs_diff(color1, color2):
    abs_diff = sum([abs(i - j) for i,j in zip(color1, color2)])
    return abs_diff

def set_dialogue_bg_color(pil_image, current_annotations):
    bbox = current_annotations[0]['bbox']

    top_left, bottom_right = bbox[0], bbox[2]
    bbox = top_left[0], top_left[1], bottom_right[0], bottom_right[1]

    bg_color_ref_point = (top_left[0] - 10, top_left[1] + 40)
    dialogue_bg_color = pil_image.getpixel(bg_color_ref_point)

    return dialogue_bg_color

def set_dialogue_text_color(pil_image, dialogue_bg_color, current_annotations):
    
    # random threshold number to determine difference between background color and text color
    abs_diff_const = 500
    colors = []

    bbox = current_annotations[0]['bbox']

    top_left, bottom_right = bbox[0], bbox[2]
    bbox = top_left[0], top_left[1], bottom_right[0], bottom_right[1]

    img_crop = pil_image.crop(bbox)
    for i in range(img_crop.size[0]):
        for j in range(img_crop.size[1]):
            colors.append(img_crop.getpixel((i,j)))
    
    counter = Counter(colors)

    for k in counter.most_common()[:20]:
        color = k[0]
        if cal_abs_diff(dialogue_bg_color, color) > abs_diff_const:
            return color

def adjust_translation_text(translation, draw, font, dialogue_bbox_width):
    """Adding newline when translation text is longer than dialogue_bbox_width"""

    char_width = 0
    translation_adjusted = ""
    for char in translation:
        char_width += draw.textlength(char, font=font)
        if char_width > dialogue_bbox_width:
            char_width = 0
            translation_adjusted += "\n"
        else:
            translation_adjusted += char
    return translation_adjusted


def draw_translation(image, translation_json, annotation):
    top_left = annotation[0]['bbox'][0]
    # finding largest x and y coordinates for bottom_right
    largest_x = 0
    largest_y = 0
    for i in annotation:
        ann = i['bbox'][2]
        if ann[0] >= largest_x:
            largest_x = ann[0]
        if ann[1] >= largest_y:
            largest_y = ann[1]
    bottom_right = [largest_x, largest_y]
        
    # Ensure the coordinates are in the correct format (floats or integers)
    top_left = tuple(map(int, top_left))
    bottom_right = tuple(map(int, bottom_right))
    font = ImageFont.truetype(font_path, 35)
    draw = ImageDraw.Draw(image)

    dialogue_bg_color = set_dialogue_bg_color(image, annotation)
    dialogue_text_color = set_dialogue_text_color(image, dialogue_bg_color, annotation)

    dialogue_bbox = [tuple(top_left), tuple(bottom_right)]
    draw.rectangle(dialogue_bbox, fill=dialogue_bg_color)

    dialogue_bbox_width = dialogue_bbox[1][0] - dialogue_bbox[0][0]
    content =  translation_json['choices'][0]['message']['content']     
    current_translation = str(content)
    translation_adjusted = adjust_translation_text(current_translation, draw, 
                                                        font, dialogue_bbox_width)

    text_position = (top_left[0], top_left[1])
    draw.text(text_position, translation_adjusted, font=font, fill=dialogue_text_color)

    return image


