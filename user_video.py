import io
import time
from process_frames import FrameProcessor
from video_stream_with_annotations import VideoStreamWithAnnotations
from PIL import Image
from ocr_enum import OCREngine, DETEngine

dummy_image = Image.new('RGB', (100, 100), (255, 255, 255))

#This handles per user video processing
class UserVideo:
    def __init__(self, lang="jp", disable_dialog=False, disable_translation=False, enable_cache=False, translate="", textDetector=None, debug_bbox=False, crop_height=None):
        self.last_inboard_frame = None
        self.last_frame_count = 0
        self.crop_height = crop_height
        self.closest_match = [] #this can be a list of items

        self.frameProcessor = FrameProcessor(lang, disable_dialog, method=OCREngine.OPENAI, detection_method=DETEngine.FAST)

        self.video_stream = VideoStreamWithAnnotations(background_task=self.process_video_thread, background_task_args={"translate" : translate, 'enable_cache' : enable_cache},
                                                    show_fps=True, crop_y_coordinate=crop_height, frameProcessor=self.frameProcessor, textDetector=textDetector, debug_bbox=debug_bbox) #TODO crop should be set later by user
        #video_stream.stop()


    def process_video_thread(self, translate="", enable_cache=False):
        time.sleep(1)  # Wait for 1 second, threading ordering issue, this is not the correct way to fix it
        while True:
            frame = self.video_stream.get_latest_frame()
            if frame is not None:
                #print("Background task accessing the latest frame...")
                closest_match = self.video_stream.process_screenshot(frame, translate=translate, show_image_screen=True, enable_cache=enable_cache) # crop is hard coded make it per user
                if closest_match != None and closest_match != 0:
                    print("Closest match(uservideo): ", closest_match)
                    self.closest_match = closest_match 
                time.sleep(1/24)  # Wait for 1 second

    def preprocess_frame(self, frame):
        return self.video_stream.preprocess_image(frame, crop_y_coordinate= self.crop_height) #preprocess all images

    def async_process_frame(self, frame):
        #TODO put the frame onto a queue, in mean time lets only put 1/3 of the frames 
        self.last_frame_count += 1
        self.last_inboard_frame =  frame
        if self.last_frame_count % 3 == 0:
            self.video_stream.set_latest_frame(self.last_inboard_frame)
            if self.last_frame_count == 100:
                self.last_frame_count = 0 # paranoia so it doesn't overflow

    def has_frame(self):
        return  self.last_inboard_frame is not None
    
#        img_byte_arr = io.BytesIO()
#        processed_latest_inboard_frame.save(img_byte_arr, format='JPEG')

    def print_annotations(self, frame):
        return self.video_stream.print_annotations_pil(frame) #TODO have translate and cache options
    
    def dump_annotations(self):
        return self.video_stream.dump_annotations()