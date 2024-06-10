import io
import time
from process_frames import FrameProcessor
from video_stream_with_annotations import VideoStreamWithAnnotations
from PIL import Image

dummy_image = Image.new('RGB', (100, 100), (255, 255, 255))

#This handles per user video processing
class UserVideo:
    def __init__(self, lang="jp", disable_dialog=False, disable_translation=False, enable_cache=False, translate="", textDetector=None, debug_bbox=False, eval=False):
        self.last_inboard_frame = None
        self.last_frame_count = 0
        self.crop_height = 71

        if eval is False:
            self.frameProcessor = FrameProcessor(lang, disable_dialog)

            self.video_stream = VideoStreamWithAnnotations(
                background_task=self.process_video_thread,
                background_task_args={"translate": translate, 'enable_cache': enable_cache},
                show_fps=True,
                crop_y_coordinate=None,
                frameProcessor=self.frameProcessor,
                textDetector=textDetector,
                debug_bbox=debug_bbox
            )

        if eval is True:
            self.frameProcessor_jp = FrameProcessor(language='jp', disable_dialog=disable_dialog)
            self.frameProcessor_en = FrameProcessor(language='en', disable_dialog=disable_dialog)

            self.video_stream = VideoStreamWithAnnotations(
                background_task=self.process_video_thread,
                background_task_args={"translate": translate, 'enable_cache': enable_cache},
                show_fps=True,
                crop_y_coordinate=None,
                frameProcessor=self.frameProcessor_en,
                textDetector=textDetector,
                debug_bbox=debug_bbox
            )


    def process_video_thread(self, translate="", enable_cache=False):
        time.sleep(1)  # Wait for 1 second, threading ordering issue, this is not the correct way to fix it
        while True:
            frame = self.video_stream.get_latest_frame()
            if frame is not None:
                #print("Background task accessing the latest frame...")
                self.video_stream.process_screenshot(frame, translate=translate, show_image_screen=True, enable_cache=enable_cache) # crop is hard coded make it per user
                time.sleep(1/24)  # Wait for 1 second


    def async_process_frame(self, frame):
        #TODO put the frame onto a queue, in mean time lets only put 1/3 of the frames 
        self.last_frame_count += 1
        self.last_inboard_frame =  self.video_stream.preprocess_image(frame, crop_y_coordinate= self.crop_height) #preprocess all images
        if self.last_frame_count % 3 == 0:
            self.video_stream.set_latest_frame(self.last_inboard_frame)
            if self.last_frame_count == 100:
                self.last_frame_count = 0 # paranoia so it doesn't overflow

    def has_frame(self):
        return  self.last_inboard_frame is not None
    
    def get_immediate_frame(self):
#        img_byte_arr = io.BytesIO()

        if  self.last_inboard_frame is not None:
            processed_latest_inboard_frame = self.video_stream.print_annotations_pil(self.last_inboard_frame) #TODO have translate and cache options
        else:
            processed_latest_inboard_frame = dummy_image

#        processed_latest_inboard_frame.save(img_byte_arr, format='JPEG')
            
        print(f"processed_latest_inboard_frame {processed_latest_inboard_frame}")
        return processed_latest_inboard_frame
    
    def get_predictions(self, image_path):
        """
        Return the results of text detection, text recognition and translation for the Input Image.
        """
        results = []

        print(image_path)
        game, lang, number = image_path.stem.split('_')
        img = Image.open(image_path)
        img = self.video_stream.preprocess_image(img, crop_y_coordinate=self.crop_height)
        
        image = self.video_stream.textDetector.preprocess_image(image=img)
        if not self.video_stream.textDetector.has_text(image):
            return {
                "image": str(image_path),
                "text_detected": False,
                "recognized_text": '',
                "annotations": [],
                "translation": ''
            }
        
        if lang == 'EN':
            closest_match, previous_image, highlighted_image, annotations, translation = self.frameProcessor_en.run_image(img, translate=self.video_stream.background_task_args.get("translate", None), enable_cache=self.video_stream.background_task_args.get("enable_cache", False))
        if lang == 'JP':
            closest_match, previous_image, highlighted_image, annotations, translation = self.frameProcessor_jp.run_image(img, translate=self.video_stream.background_task_args.get("translate", None), enable_cache=self.video_stream.background_task_args.get("enable_cache", False))

        return {
            "image": str(image_path),
            "text_detected": True,
            "recognized_text": closest_match,
            "annotations": annotations,
            "translation": translation
        }
    
    