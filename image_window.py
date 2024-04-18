import os
import platform
import cv2
import threading
import time
import numpy as np
from collections import Counter
from PIL import Image, ImageFont, ImageDraw

os_name = platform.system()
if os_name == 'Windows':
    # Import Windows-specific module
    from windows_screenshot import find_window_id, capture_window_to_pil 
elif os_name == 'Darwin':
    # Import macOS-specific module
    from osx_screenshot import find_window_id, capture_window_to_pil
elif os_name == 'Linux':
    # Import Linux-specific module
    from wsl_screenshot import find_window_id, capture_window_to_pil
else:
    raise Exception(f"Unsupported OS: {os_name}")


class VideoStreamWithAnnotations:
    def __init__(self, background_task=None, background_task_args={}, show_fps=False):
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.current_annotations = None
        self.current_translations = None
        self.show_fps = show_fps
        self.frame_count = 0
        self.fps = 0
        self.fps_counter_start_time = time.time()


        # Check the operating system, and language these two are for japanese
        if platform.system() == "Windows":
            self.font_path = "C:/Windows/Fonts/YuGothB.ttc"  # Path to MS Gothic on Windows
        elif platform.system() == "Darwin":  # Darwin is the system name for macOS
            self.font_path = "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc"  # Path to Hiragino Maru Gothic Pro
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

                self.print_annotations(frame)


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



    def print_annotations(self, frame):
        translate = self.background_task_args["translate"]
        with self.frame_lock:
            if self.current_annotations != None and self.current_annotations != []:
                if translate:
                    top_left = self.current_annotations[0][0][0]
                    # finding largest x and y coordinates for bottom_right
                    largest_x = 0
                    largest_y = 0
                    for i in self.current_annotations:
                        ann = i[0][2]
                        if ann[0] >= largest_x:
                            largest_x = ann[0]
                        if ann[1] >= largest_y:
                            largest_y = ann[1]
                    bottom_right = [largest_x, largest_y]
                        
                    # Ensure the coordinates are in the correct format (floats or integers)
                    top_left = tuple(map(int, top_left))
                    bottom_right = tuple(map(int, bottom_right))
                    
                    # # Draw the bounding box
                    # try:
                    #     cv2.rectangle(frame, top_left, bottom_right, self.dialogue_box_bg_color, cv2.FILLED)  # BGR color format, red box
                    # except Exception as e:
                    #     print(f"Weird: y1 must be greater than or equal to y0, but got {top_left} and {bottom_right} respectively. Swapping...")

                    # Annotate text. Adjust the position if necessary.
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(image)

                    self.dialogue_bg_color = self.set_dialogue_bg_color(pil_image)
                    self.dialogue_text_color = self.set_dialogue_text_color(pil_image, self.dialogue_bg_color)

                    font = ImageFont.truetype(self.font_path, 35)
                    draw = ImageDraw.Draw(pil_image)

                    dialogue_bbox = [tuple(top_left), tuple(bottom_right)]
                    draw.rectangle(dialogue_bbox, fill=self.dialogue_bg_color)

                    text_position = (top_left[0], top_left[1])
                    draw.text(text_position, self.current_translations, font=font, fill=self.dialogue_text_color)

                    image = np.asarray(pil_image)
                    frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
                else:
    #               print(f"print_annotations- {self.current_annotations}")
                    for (bbox, text, prob) in self.current_annotations:
                        # Extracting min and max coordinates for the rectangle
                        top_left = bbox[0]
                        bottom_right = bbox[2]
                        
                        # Ensure the coordinates are in the correct format (floats or integers)
                        top_left = tuple(map(int, top_left))
                        bottom_right = tuple(map(int, bottom_right))
                        
                        # Draw the bounding box
                        try:
                            cv2.rectangle(frame, top_left, bottom_right, (0, 0, 255), 2)  # BGR color format, red box
                        except Exception as e:
                            print(f"Weird: y1 must be greater than or equal to y0, but got {top_left} and {bottom_right} respectively. Swapping...")

                        # Annotate text. Adjust the position if necessary.
                        text_position = (top_left[0], top_left[1] - 10)  # Adjusted position to draw text above the box
                        cv2.putText(frame, text, text_position, cv2.FONT_HERSHEY_SIMPLEX, 
                                    0.5, (0, 255, 255), 2, cv2.LINE_AA)  # BGR color format, yellow text  
        cv2.imshow("Image with Annotations", frame)


    def run_video(self, path):
        last_time = time.time()
        if path == "webcam":
            self.cap = cv2.VideoCapture(0)  # 0 is usually the default camera
            if not self.cap.isOpened():
                print("Error: Could not open video stream.")
                exit() 
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

            self.print_annotations(frame)
            
            # Display the resulting frame
            # cv2.imshow('Video Stream with Annotations', frame)

            # Break the loop on pressing 'q'
            if cv2.waitKey(1) == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()


    def get_latest_frame(self):
        with self.frame_lock:
            return self.latest_frame
        
    def set_annotations(self, annotations):
        if annotations == None:
            return
        with self.frame_lock:
            self.current_annotations = annotations

    def set_translation(self, translation):
        if translation == None:
            return
        with self.frame_lock:
            self.current_translations = translation


    def stop(self):
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join()

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
