import os
import platform
import cv2
import threading
import time
import numpy as np
from collections import Counter
from PIL import Image, ImageFont, ImageDraw
from image_diff import image_crop_title_bar

os_name = platform.system()
#TODO we should remove this from this file 
if os_name == 'Windows':
    # Import Windows-specific module
    from windows_screenshot import find_window_id, capture_window_to_pil 
elif os_name == 'Darwin':
    # Import macOS-specific module
    from osx_screenshot import find_window_id, capture_window_to_pil
elif os_name == 'Linux':
    print("disabled on linux")
    # Import Linux-specific module
    #from wsl_screenshot import find_window_id, capture_window_to_pil
else:
    raise Exception(f"Unsupported OS: {os_name}")


class VideoStreamWithAnnotations:
    def __init__(self, background_task=None, background_task_args={}, show_fps=False, crop_y_coordinate=None, frameProcessor=None, textDetector=None, debug_bbox=False):
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.current_annotations = None
        self.current_translations = None
        self.show_fps = show_fps
        self.frame_count = 0
        self.fps = 0
        self.fps_counter_start_time = time.time()
        self.frameProcessor = frameProcessor
        self.textDetector = textDetector
        self.debug_bbox = debug_bbox

        # Check the operating system, and language these two are for japanese
        if platform.system() == "Windows":
            self.font_path = "C:/Windows/Fonts/YuGothB.ttc"  # Path to MS Gothic on Windows
            self.crop_y_coordinate = 72
        elif platform.system() == "Darwin":  # Darwin is the system name for macOS
            self.font_path = "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc"  # Path to Hiragino Maru Gothic Pro
            self.crop_y_coordinate = 72
        else: #linux?
#            self.crop_y_coordinate = 72
            self.font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" #sudo apt-get install fonts-noto-cjk
        self.font = ImageFont.truetype(self.font_path, 35)

        if crop_y_coordinate is not None:
            self.crop_y_coordinate = crop_y_coordinate
        self.cap = None
        self.background_task = background_task
        self.background_task_args = background_task_args
        if self.background_task is not None:
            self.thread = threading.Thread(target=self.background_task, kwargs=self.background_task_args)
            self.thread.daemon = True  # Daemonize thread
            self.thread.start()


    def get_frame_from_ss(self):
        window_name = "RetroArch"  # Adjust this to the target window's name
        file_path = os.path.expanduser("window_capture.jpg")  # Save location
        window_id = find_window_id(window_name)
        if window_id:
            
            img = capture_window_to_pil(window_id, file_path)
            if self.crop_y_coordinate is not None:
                img = image_crop_title_bar(img, self.crop_y_coordinate)
            
            if not img:
                print("Error: Can't receive frame (stream end?). Exiting ...")
                return None

            image_array = np.array(img)
            frame = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)                

            return img, frame
        return None 

    def display_fps(self, frame):
        self.frame_count += 1
        # Calculate FPS every second
        if time.time() - self.fps_counter_start_time >= 1:
            self.fps = self.frame_count / (time.time() - self.fps_counter_start_time)
            self.fps_counter_start_time = time.time()
            self.frame_count = 0

            print(f"FPS: {self.fps:.2f}")  # Optionally print FPS to console


        # Add FPS counter to the frame
        cv2.putText(frame, f"FPS: {self.fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)


    def run_ss(self):
        
        print("run_ss")
        last_time = time.time()
        while True:
            img, frame = self.get_frame_from_ss()
            if img != None:
                # Update the latest_frame every second
                if time.time() - last_time >= 1:
                    with self.frame_lock:
                        self.latest_frame = img
                    last_time = time.time()

                frame = self.print_annotations(frame)
                cv2.imshow("Image with Annotations", frame)


                if self.show_fps:
                    self.display_fps(frame)

                # Display the resulting frame
                # cv2.imshow('Video Stream with Annotations', frame)



            # Break the loop on pressing 'q'
            if cv2.waitKey(1) == ord('q'):
                break

        cv2.destroyAllWindows()
    
    def cal_abs_diff(self, color1, color2):
        abs_diff = sum([abs(i - j) for i,j in zip(color1, color2)])
        return abs_diff
    
    def set_dialogue_bg_color(self, pil_image):
        bbox, _, _ = self.current_annotations[0]

        top_left, bottom_right = bbox[0], bbox[2]
        bbox = top_left[0], top_left[1], bottom_right[0], bottom_right[1]

        bg_color_ref_point = (top_left[0] - 10, top_left[1] + 40)
        dialogue_bg_color = pil_image.getpixel(bg_color_ref_point)

        return dialogue_bg_color
    
    def set_dialogue_text_color(self, pil_image, dialogue_bg_color):
        
        # random threshold number to determine difference between background color and text color
        abs_diff_const = 500
        colors = []

        bbox, _, _ = self.current_annotations[0]

        top_left, bottom_right = bbox[0], bbox[2]
        bbox = top_left[0], top_left[1], bottom_right[0], bottom_right[1]

        img_crop = pil_image.crop(bbox)
        for i in range(img_crop.size[0]):
            for j in range(img_crop.size[1]):
                colors.append(img_crop.getpixel((i,j)))
        
        counter = Counter(colors)

        for k in counter.most_common()[:20]:
            color = k[0]
            if self.cal_abs_diff(dialogue_bg_color, color) > abs_diff_const:
                return color

    def adjust_translation_text(self, translation, draw, font, dialogue_bbox_width):
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


    def print_annotations_pil(self, pil_image):
        translate = self.background_task_args["translate"]
        with self.frame_lock:
            if self.current_annotations:
                draw = ImageDraw.Draw(pil_image)

                if translate:
                    top_left, bottom_right = self._calculate_annotation_bounds(self.current_annotations)
                    self._annotate_translation(pil_image, draw, top_left, bottom_right)

                if self.debug_bbox:
                    self._draw_bboxes(draw, self.current_annotations)

                else:
                    self._draw_bboxes(draw, self.current_annotations)

        return pil_image
    
    def _calculate_annotation_bounds(self, annotations):
        top_left = annotations[0][0][0]
        largest_x = max(ann[0][2][0] for ann in annotations)
        largest_y = max(ann[0][2][1] for ann in annotations)
        bottom_right = (largest_x, largest_y)
        return tuple(map(int, top_left)), tuple(map(int, bottom_right))

    def _annotate_translation(self, pil_image, draw, top_left, bottom_right):
        self.dialogue_bg_color = self.set_dialogue_bg_color(pil_image)
        self.dialogue_text_color = self.set_dialogue_text_color(pil_image, self.dialogue_bg_color)
        
        dialogue_bbox = [top_left, bottom_right]
        draw.rectangle(dialogue_bbox, fill=self.dialogue_bg_color)

        dialogue_bbox_width = dialogue_bbox[1][0] - dialogue_bbox[0][0]
        translation_adjusted = self.adjust_translation_text(self.current_translations, draw, self.font, dialogue_bbox_width)

        text_position = (top_left[0], top_left[1])
        draw.text(text_position, translation_adjusted, font=self.font, fill=self.dialogue_text_color)

    def _draw_debug_bboxes(self, draw, annotations):
        for bbox, text, prob in annotations:
            top_left, bottom_right = tuple(map(int, bbox[0])), tuple(map(int, bbox[2]))
            draw.rectangle([top_left, bottom_right], outline="red", width=2)
            text_position = (top_left[0], top_left[1] - 10)
            draw.text(text_position, text, fill="yellow")

    def _draw_bboxes(self, draw, annotations):
        for bbox, text, prob in annotations:
            top_left, bottom_right = tuple(map(int, bbox[0])), tuple(map(int, bbox[2]))
            draw.rectangle([top_left, bottom_right], outline="red", width=2)
            text_position = (top_left[0], top_left[1] - 10)
            draw.text(text_position, text, fill="yellow")

    def print_annotations(self, frame):
        pil_image = self.print_annotations_pil(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


    def run_video(self, path):
        last_time = time.time()
        if path.startswith("webcam"):
            print("opening webcam- ", path)
            webcam_index = int(path[6:])  # Extract the index from "webcamX"
            cap = cv2.VideoCapture(webcam_index)
            if not cap.isOpened():
                print(f"Error: Could not open video stream for {path}.")
                exit()
            self.cap = cap
        else:
            self.cap = cv2.VideoCapture(path)
            

        print("run video")
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Can't receive frame (stream end?). Exiting ...")
                break
            
            # Update the latest_frame every second
            if time.time() - last_time >= 1:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_image)
                with self.frame_lock:
                    self.latest_frame = img
                last_time = time.time()

            if self.show_fps:
                self.display_fps(frame)

            frame = self.print_annotations(frame)
            
            # Display the resulting frame
            cv2.imshow('Video Stream with Annotations', frame)

            # Break the loop on pressing 'q'
            if cv2.waitKey(1) == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def get_latest_frame(self):
        with self.frame_lock:
            return self.latest_frame
        
    #TODO do we need a queue?
    def set_latest_frame(self, img):
        with self.frame_lock:
            self.latest_frame = img

    def set_annotations(self, annotations):
        if annotations == None:
            return
        with self.frame_lock:
            #print(f"set_annotations- {annotations}")
            self.current_annotations = annotations

    def set_translation(self, translation):
        if translation == None:
            return
        with self.frame_lock:
            self.current_translations = translation


    def stop(self):
        if self.cap != None and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join()

    #TODO all preprocessing goes here
    def preprocess_image(self, img, crop_y_coordinate=None):
        if crop_y_coordinate != None:
            return image_crop_title_bar(img, crop_y_coordinate)
        return img

    def process_screenshot(self, img,translate=None, show_image_screen=False, enable_cache=False, crop_y_coordinate=None):
        if crop_y_coordinate != None:
            img = image_crop_title_bar(img, crop_y_coordinate)

        image = self.textDetector.preprocess_image(img)
        if not self.textDetector.has_text(image):
            print("No text Found in this frame. Skipping run_image")
            if show_image_screen:
                self.set_annotations([])
        else:
        
            closest_match, previous_image, highlighted_image, annotations, translation = self.frameProcessor.run_image(img, translate=translate,enable_cache=enable_cache)

            if annotations != None:
                if show_image_screen:
                    self.set_annotations(annotations)
                    self.set_translation(translation)
#            if closest_match == None: #TODO remember why this code exists? i think for dialogues
#                if show_image_screen:
#                    self.set_annotations(None)
#                    self.set_translation(None)
 
            if closest_match != None:
                return closest_match #TODO this is for playing audio, its still a bit messy, ss.py is playing audio, what if we want on web?
 
        return None

# Example background task function
def example_background_task(video_stream):
    while True:
        frame = video_stream.get_latest_frame()
        if frame is not None:
            print("Background task accessing the latest frame...")
            # Here you can process the frame or do something with it
        time.sleep(1)  # Simulating work

# Main function to start everything
def main():
    video_stream = VideoStreamWithAnnotations(background_task=example_background_task)
    try:
        video_stream.run()
    finally:
        video_stream.stop()

if __name__ == "__main__":
    main()
