import unittest
from PIL import Image, ImageDraw
from ocr import OCRProcessor  
from video_stream_with_annotations import VideoStreamWithAnnotations
from text_detector_fast import TextDetectorFast
from process_frames import FrameProcessor
from thefuzz import fuzz
from ocr_enum import OCREngine
from shapely.geometry import box
from image_diff import calculate_image_hash_different

def calculate_iou(bbox1, bbox2):
    box1 = box(bbox1[0][0], bbox1[0][1], bbox1[1][0], bbox1[1][1])
    box2 = box(bbox2[0][0], bbox2[0][1], bbox2[1][0], bbox2[1][1])

    intersection = box1.intersection(box2).area
    union = box1.union(box2).area

    iou = intersection / union if union != 0 else 0
    return iou

def calculate_aggregate_iou_with_missing(bbox1_list, bbox2_list):
    min_length = min(len(bbox1_list), len(bbox2_list))
    ious = [calculate_iou(b1, b2) for b1, b2 in zip(bbox1_list[:min_length], bbox2_list[:min_length])]
    
    # Penalize missing boxes by considering their IoU as 0
    num_missing = abs(len(bbox1_list) - len(bbox2_list))
    ious.extend([0] * num_missing)
    
    aggregate_iou = sum(ious) / (len(bbox1_list) + len(bbox2_list) - min_length)
    return aggregate_iou

def crop_image(img, bbox):
    
    # bbox should be in the form (left, upper, right, lower)
    left, upper, right, lower = bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1]
    
    # Crop the image
    cropped_img = img.crop((left, upper, right, lower))
    
    return cropped_img

class TestDialogueOverlay(unittest.TestCase):
    def setUp(self):
        self.ocr_processor = OCRProcessor(language='en', method=OCREngine.EASYOCR)
        self.video_stream = VideoStreamWithAnnotations(background_task=None, background_task_args={'translate' : ''}, show_fps=False,
                                                       frameProcessor=FrameProcessor('en'), textDetector=TextDetectorFast('pretrained/fast_base_tt_640_finetune_ic17mlt.pth'))
        self.test_bbox_image = Image.open('unit_test_data/overlap_bbox.jpg')
        self.annotated_bbox_image = Image.open('unit_test_data/annotated_bbox.jpg')
        self.blurred_bbox_image = Image.open('unit_test_data/blurred_bbox.jpg')

        self.ann = [([(934, 54), (1177, 129)], '#rUali'),
                ([(984, 710), (1206, 782)], 'HP 200-'),
                ([(85, 721), (457, 785)], '7D-9-f_J'),
                ([(478, 732), (538, 780)], '3'),
                ([(626, 732), (768, 780)], 'tvl'),
                ([(1210, 730), (1350, 782)], '200')]

    def test_combine_overlapping_bbox(self):
        """
        Test postprocessing step of ocr , combining overlapping bounding box
        """
        self.ocr_processor.method = OCREngine.EASYOCR
        _, _, annotations, _ = self.ocr_processor.run_ocr(self.test_bbox_image)
        gt_bbox = [[(934, 54), (1177, 129)],
                    [(984, 710), (1206, 782)],
                    [(85, 721), (457, 785)],
                    [(478, 732), (538, 780)],
                    [(626, 732), (768, 780)],
                    [(1210, 730), (1350, 782)]]
        pred_bbox = [i[0] for i in annotations]
        IoU = calculate_aggregate_iou_with_missing(gt_bbox, pred_bbox)
        self.assertGreaterEqual(IoU, 0.8)


    def test_print_annotations_pil(self):
        self.video_stream.current_annotations = self.ann
        self.video_stream.current_translations = "Example Translation"
        self.video_stream.background_task_args = {'translate': True}
        result_image = self.video_stream.print_annotations_pil(self.test_bbox_image)
        result_image.save('unit_test_data/test_print_annotations_pil.jpg')
        self.assertIsInstance(result_image, Image.Image)

    def test_print_annotations_pil_with_no_annotations(self):
        self.video_stream.current_annotations = []
        self.video_stream.current_translations = ""
        self.video_stream.background_task_args = {'translate': False}
        result_image = self.video_stream.print_annotations_pil(self.test_bbox_image)
        result_image.save('unit_test_data/test_print_annotations_pil_with_no_annotations.jpg')
        self.assertIsInstance(result_image, Image.Image)

    def test_print_annotations_pil_with_no_translation(self):
        self.video_stream.current_annotations = self.ann
        self.video_stream.current_translations = ""
        self.video_stream.background_task_args = {'translate': False}
        result_image = self.video_stream.print_annotations_pil(self.test_bbox_image)
        result_image.save('unit_test_data/test_print_annotations_pil_with_no_translation.jpg')
        self.assertIsInstance(result_image, Image.Image)

    def test_calculate_annotation_bounds_single(self):
        # Single annotation
        annotations = [([(934, 54), (1177, 129)], '#rUali')]
        self.video_stream.current_annotations = annotations
        result = self.video_stream._calculate_annotation_bounds(annotations)
        expected_result = (934, 54)
        self.assertEqual(result, expected_result, "Should extract the top-left corner from a single annotation")

    def test_calculate_annotation_bounds_multiple(self):
        
        self.video_stream.current_annotations = self.ann
        result = self.video_stream._calculate_annotation_bounds(self.ann)
        expected_result = (934, 54)
        self.assertEqual(result, expected_result, "Should correctly extract the top-left corner from the first annotation")

    def test_calculate_annotation_bounds_empty(self):
        # Test with no annotations
        annotations = []
        self.video_stream.current_annotations = annotations
        with self.assertRaises(IndexError):
            self.video_stream._calculate_annotation_bounds(annotations)

    # def test_bbox_annotated_image(self):
    
    #     self.video_stream.set_annotations(self.ann)
    #     annotated_image = self.video_stream.print_annotations_pil(self.test_bbox_image)
    #     result = calculate_image_hash_different(annotated_image, self.annotated_bbox_image)
    #     self.assertLessEqual(result, 1)

    # def test_blur_orig_text(self):
        
    #     self.video_stream.set_annotations(self.ann)
    #     self.video_stream.set_translation('')
    #     draw = ImageDraw.Draw(self.test_bbox_image)
    #     top_left = (934, 54)
    #     blurred_image = self.video_stream._annotate_translation(self.test_bbox_image, draw, top_left)

    #     count = 0
    #     for bbox, _ in self.ann:
    #         cropped_image = crop_image(blurred_image, bbox)
    #         test_cropped_image = Image.open(f'unit_test_data/{count}.jpg')
    #         result = calculate_image_hash_different(cropped_image, test_cropped_image)
    #         print(result)

if __name__ == '__main__':
    unittest.main()
