import os
import platform
import cv2
import threading
import time
import numpy as np

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
    def __init__(self, background_task=None):
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.current_annotations = None

        self.cap = None
        self.background_task = background_task
        if self.background_task is not None:
            self.thread = threading.Thread(target=self.background_task)
            self.thread.daemon = True  # Daemonize thread
            self.thread.start()


    def open_camera(self):
        self.cap = cv2.VideoCapture(0)  # 0 is usually the default camera
        if not self.cap.isOpened():
            print("Error: Could not open video stream.")
            exit()


    def run_ss(self):
        print("run_ss")
        last_time = time.time()
        while True:
            window_name = "RetroArch"  # Adjust this to the target window's name
            file_path = os.path.expanduser("window_capture.jpg")  # Save location
            window_id = find_window_id(window_name)
            if window_id:
                img = capture_window_to_pil(window_id, file_path)
                if not img:
                    print("Error: Can't receive frame (stream end?). Exiting ...")
                    break

                # Update the latest_frame every second
                if time.time() - last_time >= 1:
                    with self.frame_lock:
                        self.latest_frame = img
                    last_time = time.time()

                image_array = np.array(img)
                frame = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)                


                with self.frame_lock:
                    if self.current_annotations != None:
                        # Add an annotation on top of the video
                        cv2.putText(frame, 'Hello, OpenCV!', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                                    1, (255, 255, 255), 2, cv2.LINE_AA)

                        for (bbox, text, prob) in self.current_annotations:
#                            filtered_result.append((bbox, text, prob))
                            
                            # Extracting min and max coordinates for the rectangle
                            top_left = bbox[0]
                            bottom_right = bbox[2]
                            
                            # Ensure the coordinates are in the correct format (floats or integers)
                            top_left = tuple(map(int, top_left))
                            bottom_right = tuple(map(int, bottom_right))
                            
                            # Draw the bounding box
                            #draw.rectangle([top_left, bottom_right], outline="red", width=2)
                            cv2.rectangle(frame, top_left, bottom_right, (0, 0, 255), 2)  # BGR color format, red box

                            # Annotate text. Adjust the position if necessary.
                            #draw.text(top_left, text, fill="yellow")
                            text_position = (top_left[0], top_left[1] - 10)  # Adjusted position to draw text above the box
                            cv2.putText(frame, text, text_position, cv2.FONT_HERSHEY_SIMPLEX, 
                                        0.5, (0, 255, 255), 2, cv2.LINE_AA)  # BGR color format, yellow text    
                
                # Display the resulting frame
                cv2.imshow('Video Stream with Annotations', frame)

            # Break the loop on pressing 'q'
            if cv2.waitKey(1) == ord('q'):
                break

        cv2.destroyAllWindows()


    def run(self):
        self.open_camera()
        print("run")
        return
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Can't receive frame (stream end?). Exiting ...")
                break

            # Update the latest_frame every second
            if time.time() - last_time >= 1:
                with self.frame_lock:
                    self.latest_frame = frame #TODO this needs to be PIL FORMAT!!!
                last_time = time.time()

            # Add an annotation on top of the video
            cv2.putText(frame, 'Hello, OpenCV!', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                        1, (255, 255, 255), 2, cv2.LINE_AA)
            
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
        
    def set_annotations(self, annotations):
        with self.frame_lock:
            self.current_annotations = annotations


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
