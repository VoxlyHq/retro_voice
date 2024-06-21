import os
import platform
import cv2
import threading
import time
import numpy as np
from collections import Counter
from PIL import Image, ImageFont, ImageDraw, ImageFilter
from image_diff import image_crop_title_bar
import textwrap

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
        elif platform.system() == "Darwin":  # Darwin is the system name for macOS
            self.font_path = "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc"  # Path to Hiragino Maru Gothic Pro
        else: #linux?
            self.font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" #sudo apt-get install fonts-noto-cjk
        self.font = ImageFont.truetype(self.font_path, 35)

        self.crop_y_coordinate = crop_y_coordinate # This can be None or an integer you should set this
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

    def adjust_translation_text(self, translation, font, dialogue_bbox_width):
        """Adding newline when translation text is longer than dialogue_bbox_width"""

        word_width = 0
        translation_adjusted = ""
        for word in translation.split():
            text_bbox = font.getbbox(word)
            #text_size = font.getsize(text)
            text_width = text_bbox[2] - text_bbox[0]

            word_width += text_width
            if word_width > dialogue_bbox_width:
                word_width = 0
                translation_adjusted += word + "\n"
            else:
                translation_adjusted += word + ' '
        return translation_adjusted
    
    def calculate_font_size(self, dialogue_box_width, dialogue_box_height, text, initial_font_size=35):
        """
        Find the font size that can fit all text in the dialogue box
        """
        if dialogue_box_width <= 0 or dialogue_box_height <= 0:
            return None

        def fits(font_size):
            try:
                font = self.font.font_variant(size=font_size)
                # Calculate the line width to wrap text
                line_width = dialogue_box_width // font_size
                wrapped_text = textwrap.fill(text, width=line_width)

                bbox = draw.textbbox((0, 0), wrapped_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                return text_width <= dialogue_box_width and text_height <= dialogue_box_height
            except IOError:
                print(f"Error: Font file not found at {self.font_path}")
                return False
            except Exception as e:
                print(f"An error occurred: {e}")
                return False

        draw = ImageDraw.Draw(Image.new('RGB', (dialogue_box_width, dialogue_box_height)))
        min_size, max_size = 1, initial_font_size
        result_size = min_size

        while min_size <= max_size:
            mid_size = (min_size + max_size) // 2
            if fits(mid_size):
                result_size = mid_size
                min_size = mid_size + 1
            else:
                max_size = mid_size - 1

        return result_size

    #TODO merge this and print_annotations
    def dump_annotations(self):
        out_annotations = {
            "translations": [],
            "annotations": [],
            "debug_bbox": []
        }
        translate = self.background_task_args["translate"]
        with self.frame_lock:
            if self.current_annotations != None and self.current_annotations != []:
                if translate:
                    top_left = self.current_annotations[0][0][0]
                    # finding largest x and y coordinates for bottom_right
                    largest_x = 0
                    largest_y = 0
                    for i in self.current_annotations:
                        print(f"i[0] - #{i[0]}")
                        ann = i[0][2]
                        if ann[0] >= largest_x:
                            largest_x = ann[0]
                        if ann[1] >= largest_y:
                            largest_y = ann[1]
                    bottom_right = [largest_x, largest_y]
                    # Ensure the coordinates are in the correct format (floats or integers)
                    top_left = tuple(map(int, top_left))
                    bottom_right = tuple(map(int, bottom_right))

                    # Annotate text. Adjust the position if necessary.
                    #TODO send bg_color self.dialogue_bg_color = self.set_dialogue_bg_color(pil_image)
                    #TODO send bg_color self.dialogue_text_color = self.set_dialogue_text_color(pil_image, self.dialogue_bg_color)


                    dialogue_bbox = [tuple(top_left), tuple(bottom_right)]
                    #TODO send rectangle info draw.rectangle(dialogue_bbox, fill=self.dialogue_bg_color)

                    dialogue_bbox_width = dialogue_bbox[1][0] - dialogue_bbox[0][0]
                    translation_adjusted = self.adjust_translation_text(self.current_translations,
                                                                        self.font, dialogue_bbox_width)

                    text_position = (top_left[0], top_left[1])
#                    draw.text(text_position, translation_adjusted, font=self.font, fill=self.dialogue_text_color)

                    oanno = {"pos": text_position, "text": translation_adjusted, "bbox": dialogue_bbox}
                    out_annotations["translations"].append(oanno)

                if self.debug_bbox is True:
                    for (bbox, text, prob) in self.current_annotations:
                        # Extracting min and max coordinates for the rectangle
                        top_left = bbox[0]
                        bottom_right = bbox[2]

                        # Ensure the coordinates are in the correct format (floats or integers)
                        top_left = tuple(map(int, top_left))
                        bottom_right = tuple(map(int, bottom_right))

                        # Annotate text. Adjust the position if necessary.
                        #TODO rectangle info draw.rectangle([top_left, bottom_right], outline="red", width=2)
                        text_position = (top_left[0], top_left[1] - 10)  # Adjusted position to draw text above the box
                        #draw.text(text_position, text, fill="yellow")
                        oanno = {"pos": text_position, "text": text}
                        out_annotations["debug_bbox"].append(oanno)
                
                if self.debug_bbox is False and translate is None:
                    for (bbox, text, prob) in self.current_annotations:
                        # Extracting min and max coordinates for the rectangle
                        top_left = bbox[0]
                        bottom_right = bbox[2]

                        # Ensure the coordinates are in the correct format (floats or integers)
                        top_left = tuple(map(int, top_left))
                        bottom_right = tuple(map(int, bottom_right))

                        # Annotate text. Adjust the position if necessary.
                        #TODO rectangle info draw.rectangle([top_left, bottom_right], outline="red", width=2)
                        text_position = (top_left[0], top_left[1] - 10)  # Adjusted position to draw text above the box
                        #draw.text(text_position, text, fill="yellow")

                        oanno = {"pos": text_position, "text": text}
                        out_annotations["annotations"].append(oanno)

        return out_annotations

    def print_annotations_pil(self, pil_image):
        translate = self.background_task_args["translate"]
        with self.frame_lock:
            if self.current_annotations:
                draw = ImageDraw.Draw(pil_image)

                if translate:
                    top_left = self._calculate_annotation_bounds(self.current_annotations)
                    pil_image = self._annotate_translation(pil_image, draw, top_left)

                if self.debug_bbox:
                    draw = ImageDraw.Draw(pil_image)
                    self._draw_bboxes(draw, self.current_annotations)

                if not bool(translate) and not self.debug_bbox:
                    self._draw_bboxes(draw, self.current_annotations)

        return pil_image
    
    def _calculate_annotation_bounds(self, annotations):
        top_left = annotations[0][0][0]
        return tuple(map(int, top_left))

    def _annotate_translation(self, pil_image, draw, top_left):

        # Blurring the background text
        blurred_image = pil_image.filter(ImageFilter.GaussianBlur(10))
        mask = Image.new("L", pil_image.size, 0)
        draw_mask = ImageDraw.Draw(mask)

        for res_ in self.current_annotations:
            # Draw the rectangle on the mask
            draw_mask.rectangle(res_[0], fill=255)
        
        image_with_blur = Image.composite(blurred_image, pil_image, mask)

        # Add translation text 
        dialogue_text_color = "white"
        draw = ImageDraw.Draw(image_with_blur)
        text_position = top_left

        # calculate allowed width for translation text (top left x position to 100 pixel before edge of image)
        pixel_offset = pil_image.size[0] // 5
        dialogue_bbox_width = (pil_image.size[0] - pixel_offset) -  top_left[0]
        dialogue_bbox_height = 500 # approximately the height of bbox
        font_size = self.calculate_font_size(dialogue_bbox_width, dialogue_bbox_height, self.current_translations)
        font = self.font.font_variant(size=font_size)

        adjusted_translation_text = self.adjust_translation_text(self.current_translations, font, dialogue_bbox_width)
        draw.text(text_position, adjusted_translation_text, font=font, fill=dialogue_text_color)
        return image_with_blur

    def _draw_bboxes(self, draw, annotations):
        for bbox, text in annotations:
            top_left, bottom_right = bbox
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
