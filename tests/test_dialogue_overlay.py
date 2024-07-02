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
from pathlib import Path

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
                                                       frameProcessor=FrameProcessor('en'), textDetector=TextDetectorFast('pretrained/fast_tiny_ic15_736_finetune_ic17mlt.pth',checkpoint='checkpoints/checkpoint_60ep.pth.tar'))
        self.test_data_dir = Path('tests/unit_test_data')
        self.test_bbox_image = Image.open(self.test_data_dir / 'overlap_bbox.jpg')
        self.draw = ImageDraw.Draw(self.test_bbox_image)
        self.translate_image = Image.open(self.test_data_dir / 'test_font_size.jpg')

        self.ann = [([(934, 54), (1177, 129)], '#rUali'),
                ([(984, 710), (1206, 782)], 'HP 200-'),
                ([(85, 721), (457, 785)], '7D-9-f_J'),
                ([(478, 732), (538, 780)], '3'),
                ([(626, 732), (768, 780)], 'tvl'),
                ([(1210, 730), (1350, 782)], '200')]
        
        self.ann2 = [([(136, 121), (502, 178)], 'Crew: Why'),
                        ([(543, 131), (681, 173)], 'ore'),
                        ([(721, 131), (815, 173)], 'We'),
                        ([(858, 119), (1171, 179)], 'robbing'),
                        ([(185, 199), (546, 255)], 'crystols'),
                        ([(592, 202), (772, 250)], 'from'),
                        ([(825, 201), (1172, 255)], 'innocent'),
                        ([(185, 272), (496, 340)], 'People?'),
                        ([(135, 353), (634, 407)], "Crew: Thot' s"),
                        ([(681, 363), (813, 403)], 'our'),
                        ([(859, 349), (1070, 413)], 'duty.')]

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


    def test_print_annotations(self):
        self.video_stream.current_annotations = self.ann
        self.video_stream.current_translations = "Example Translation"
        self.video_stream.background_task_args = {'translate': True}
        result_image = self.video_stream.print_annotations(self.test_bbox_image)
        result_image.save(self.test_data_dir / 'test_print_annotations_pil.jpg')
        self.assertIsInstance(result_image, Image.Image)

    def test_print_annotations_with_no_annotations(self):
        self.video_stream.current_annotations = []
        self.video_stream.current_translations = ""
        self.video_stream.background_task_args = {'translate': False}
        result_image = self.video_stream.print_annotations(self.test_bbox_image)
        result_image.save(self.test_data_dir / 'test_print_annotations_pil_with_no_annotations.jpg')
        self.assertIsInstance(result_image, Image.Image)

    def test_print_annotations_with_no_translation(self):
        self.video_stream.current_annotations = self.ann
        self.video_stream.current_translations = ""
        self.video_stream.background_task_args = {'translate': False}
        result_image = self.video_stream.print_annotations(self.test_bbox_image)
        result_image.save(self.test_data_dir / 'test_print_annotations_pil_with_no_translation.jpg')
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
    
    def test_draw_bboxes_single_annotation(self):
        # Setup a single annotation
        annotations = [([(934, 54), (1177, 129)], '#rUali')]
        self.video_stream._draw_bboxes(self.draw, annotations)
        # Check for red bounding box
        self.assertEqual(self.test_bbox_image.getpixel((934, 54)), (255, 0, 0), "Top left should be red")
        self.assertEqual(self.test_bbox_image.getpixel((1177, 129)), (255, 0, 0), "Bottom right should be red")
        # Save annotated image
        self.test_bbox_image.save(self.test_data_dir / 'test_draw_bboxes_single_annotation.jpg')

    def test_draw_bboxes_multiple_annotations(self):
        # Setup multiple annotations
        annotations = self.ann
        self.video_stream._draw_bboxes(self.draw, annotations)
        # Check for red bounding box
        self.assertEqual(self.test_bbox_image.getpixel((934, 54)), (255, 0, 0), "Top left of first bbox should be red")
        self.assertEqual(self.test_bbox_image.getpixel((1177, 129)), (255, 0, 0), "Bottom right of first bbox should be red")
        self.assertEqual(self.test_bbox_image.getpixel((626, 732)), (255, 0, 0), "Top left of fifth bbox should be red")
        self.assertEqual(self.test_bbox_image.getpixel((457, 785)), (255, 0, 0), "Bottom right of third bbox should be red")
        self.assertEqual(self.test_bbox_image.getpixel((1350, 782)), (255, 0, 0), "Bottom right of last bbox should be red")
        # Save annotated image
        self.test_bbox_image.save(self.test_data_dir / 'test_draw_bboxes_multiple_annotations.jpg')

    def test_draw_bboxes_no_annotations(self):
        # No annotations
        annotations = []
        self.video_stream._draw_bboxes(self.draw, annotations)
        # Check that no changes were made to the image (still white)
        self.assertEqual(self.test_bbox_image.getpixel((934, 54)), (3, 2, 106), "Should remain the same")

    def test_calculate_font_size_basic(self):
        text = "This is a test text to fit within the dialogue box."
        result_size = self.video_stream.calculate_font_size(1016, 500, text, 35)
        self.assertEqual(result_size, 35)

    def test_calculate_font_long_text(self):
        text = "This is a very long test text that should span multiple lines within the dialogue box to test the font size calculation." * 20
        result_size = self.video_stream.calculate_font_size(1016, 500, text, 35)
        self.assertEqual(result_size, 12)

    def test_calculate_font_size_zero_dimensions(self):
        text = "Sample Text"
        result_size = self.video_stream.calculate_font_size(0, 100, text, 35)
        self.assertIsNone(result_size, "Font size calculation should return None for zero width")

        result_size = self.video_stream.calculate_font_size(300, 0, text, 35)
        self.assertIsNone(result_size, "Font size calculation should return None for zero height")

        result_size = self.video_stream.calculate_font_size(0, 0, text, 35)
        self.assertIsNone(result_size, "Font size calculation should return None for zero dimensions")

    def test_calculate_font_size_negative_dimensions(self):
        text = "sample text"
        result_size = self.video_stream.calculate_font_size(-300, 100, text, 35)
        self.assertIsNone(result_size, "Font size calculation should return None for negative width")

        result_size = self.video_stream.calculate_font_size(300, -100, text, 35)
        self.assertIsNone(result_size, "Font size calculation should return None for negative height")

        result_size = self.video_stream.calculate_font_size(-300, -100, text, 35)
        self.assertIsNone(result_size, "Font size calculation should return None for negative dimensions")
    
    def test_adjust_translation_text_basic(self):
        translation = "This is a test text to fit within the dialogue box."
        dialogue_box_width = 1016
        adjusted_text = self.video_stream.adjust_translation_text(translation, self.video_stream.font, dialogue_box_width)
        self.assertIsInstance(adjusted_text, str)
        self.assertEqual("This is a test text to fit within the dialogue box. ", adjusted_text)

    def test_adjust_translation_text_long_text(self):
        translation = "This is a very long test text that should span multiple lines within the dialogue box to test the text adjustment functionality."
        dialogue_box_width = 1016
        adjusted_text = self.video_stream.adjust_translation_text(translation, self.video_stream.font, dialogue_box_width)
        self.assertIsInstance(adjusted_text, str)
        self.assertEqual('This is a very long test text that should span multiple lines within the\ndialogue box to test the text adjustment functionality. '
, adjusted_text)
        self.assertIn("\n", adjusted_text, "Long text should contain newline characters to fit within the dialogue box width.")

    def test_annotate_translation_basic(self):
        translation = "This is a test translation."
        top_left = (136, 121)
        self.video_stream.current_annotations = self.ann2
        self.video_stream.current_translations = translation
        dialogue_box_width = 1016
        dialogue_text_color = 'white'
        input_image = self.video_stream._generate_blurred_image(self.translate_image.copy())
        draw = ImageDraw.Draw(input_image)
        adjusted_text = self.video_stream.adjust_translation_text(translation, self.video_stream.font, dialogue_box_width)
        self.video_stream._annotate_translation(draw, top_left, adjusted_text, dialogue_text_color)
        input_image.save(self.test_data_dir / 'test_annotate_translation_basic.jpg')
        self.assertIsInstance(input_image, Image.Image)
        self.assertNotEqual(input_image, self.translate_image, "Image should be different after annotation.")

    def test_annotate_translation_long_text(self):
        translation = "This is a very long translation text that should span multiple lines within the dialogue box to test the annotation functionality." * 5
        top_left = (136, 121)
        self.video_stream.current_annotations = self.ann2
        self.video_stream.current_translations = translation
        dialogue_box_width = 1016
        dialogue_text_color = 'white'
        input_image = self.video_stream._generate_blurred_image(self.translate_image.copy())
        draw = ImageDraw.Draw(input_image)
        adjusted_text = self.video_stream.adjust_translation_text(translation, self.video_stream.font, dialogue_box_width)
        self.video_stream._annotate_translation(draw, top_left, adjusted_text, dialogue_text_color)
        input_image.save(self.test_data_dir / 'test_annotate_translation_long_text.jpg')
        self.assertIsInstance(input_image, Image.Image)
        self.assertNotEqual(input_image, self.translate_image, "Image should be different after annotation.")
    

    def test_annotate_translation_empty(self):
        translation = ""
        top_left = (136, 121)
        self.video_stream.current_annotations = self.ann2
        self.video_stream.current_translations = translation
        dialogue_box_width = 1016
        dialogue_text_color = 'white'
        input_image = self.video_stream._generate_blurred_image(self.translate_image.copy())
        draw = ImageDraw.Draw(input_image)
        adjusted_text = self.video_stream.adjust_translation_text(translation, self.video_stream.font, dialogue_box_width)
        self.video_stream._annotate_translation(draw, top_left, adjusted_text, dialogue_text_color)
        input_image.save(self.test_data_dir / 'test_annotate_translation_empty.jpg')
        self.assertIsInstance(input_image, Image.Image)

    
if __name__ == '__main__':
    unittest.main()
