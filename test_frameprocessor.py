import unittest
from unittest.mock import patch, mock_open
from process_frames import FrameProcessor  # Replace 'your_module' with the name of your Python file containing the FrameProcessor class
from PIL import Image

import numpy as np
import io

class TestFrameProcessor(unittest.TestCase):
    def test_init_language_selection(self):
        # Test English language setup
        fp_en = FrameProcessor(language='en')
        self.assertEqual(fp_en.dialog_file_path, "dialogues_en_v2.json")
        # Test Japanese language setup
        fp_jp = FrameProcessor(language='jp')
        self.assertEqual(fp_jp.dialog_file_path, "dialogues_jp_v2.json")
        # Test invalid language
        with self.assertRaises(Exception):
            FrameProcessor(language='invalid')

    def test_find_closest_entry_cecil(self):
        fp = FrameProcessor()
        dialogues = fp.load_dialogues()
        self.assertEqual(len(dialogues), 61)

#        fp.dialogues = {1: {'name': 'Test', 'dialogue': 'Captain Cecil, we are about to arrive!'}}
        closest_entry = fp.find_closest_entry('Crew: Captain Cecil, we are about to arrive! Cecil:Good')
        self.assertEqual(fp.dialogues[closest_entry[0]]['dialogue'], "Captain Cecil, we are about to arrive!")


    # @patch('json.load')
    # @patch('builtins.open', new_callable=mock_open, read_data='[{"name": "test", "dialogue": "hello"}]')
    # def test_load_dialogues(self, mock_file, mock_json_load):
    #     mock_json_load.return_value = [{"name": "test", "dialogue": "hello"}]
    #     fp = FrameProcessor()
    #     dialogues = fp.load_dialogues()
    #     self.assertEqual(len(dialogues), 1)
    #     self.assertEqual(dialogues[0]['dialogue'], 'hello')

    @patch('process_frames.fuzz.ratio', return_value=100)  # Assume perfect match for simplicity, replace 'your_module' accordingly
    def test_find_closest_entry(self, mock_fuzz_ratio):
        fp = FrameProcessor()
        # Pretend the dialogues loaded are as follows
        fp.dialogues = {0: {'name': 'Test', 'dialogue': 'hello'}}
        closest_entry = fp.find_closest_entry('hello')
        self.assertEqual(closest_entry, [0])

    def test_ocr_easyocr(self):
        fp = FrameProcessor('jp')
        img = Image.open('./unit_test_data/osx_jp_ff4.png')
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        byte_buffer = io.BytesIO()
        img.save(byte_buffer, format='JPEG')  # Change format if needed
        image_bytes = byte_buffer.getvalue()

        results = fp.ocr_easyocr(image_bytes)
        # results are not None, easyocr is working
        self.assertIsNotNone(results)
        # results is not an empty list
        self.assertNotEqual(len(results), 0)
        # results are a list of tuples
        self.assertIsInstance(results[0], tuple)
        # each tuple have three items (bbox, text, confidence score)
        self.assertEqual(len(results[0]), 3)
        self.assertIsInstance(results[0][0], list)
        self.assertIsInstance(results[0][1], str)
        self.assertIsInstance(results[0][2], np.float64)

    
    def test_filter_ocr_result(self):
        ocr_result = [([[856, 10], [990, 10], [990, 38], [856, 38]],
                        'Retronrch',
                        0.9557131589705165),
                        ([[856, 10], [990, 10], [990, 38], [856, 38]],
                        'Retroarch',
                        0.9557131589705165),
                        ([[226, 568], [698, 568], [698, 643], [226, 643]],
                        '"い「われわた',
                        0.08521686866863509),
                        ([[741, 559], [1157, 559], [1157, 643], [741, 643]],
                        'あかいつばさは',
                        0.17052240726762918),
                        ([[281, 664], [638, 664], [638, 743], [281, 743]],
                        'ほこりたおき',
                        0.3215586623738657),
                        ([[678, 658], [1145, 658], [1145, 744], [678, 744]],
                        '己くうていだ』 !',
                        0.06408965848308544),
                        ([[279, 766], [752, 766], [752, 840], [279, 840]],
                        ' 上つしも 山がら',
                        0.003661678415233707),
                        ([[801, 757], [1261, 757], [1261, 841], [801, 841]],
                        'りゃりだつなじ !',
                        0.33074903181913384),
                        ([[821, 1095], [915, 1095], [915, 1183], [821, 1183]],
                        'お',
                        0.019716543217956684)]

        fp = FrameProcessor()
        filter_result = fp.filter_ocr_result(ocr_result)
        print([i[1].lower() for i in ocr_result])
        self.assertNotIn('retronrch', [i[1].lower() for i in filter_result])
        self.assertNotIn('retroarch', [i[1].lower() for i in filter_result])

        fp = FrameProcessor('jp')
        filter_result = fp.filter_ocr_result(ocr_result)
        print([i[1].lower() for i in ocr_result])
        self.assertNotIn('retronrch', [i[1].lower() for i in filter_result])
        self.assertNotIn('retroarch', [i[1].lower() for i in filter_result])

        
    def test_ocr_easyocr_and_highlight(self):
        fp = FrameProcessor('jp')

        img = Image.open('./unit_test_data/osx_jp_ff4.png')
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        results, highlighted_img, annotations = fp.ocr_easyocr_and_highlight(img)

        # easyocr is working, results are not None
        self.assertIsNotNone(results)

        # retroarch is filtered
        self.assertNotIn('retroarch', results.lower())
        self.assertNotIn('retronrch', results.lower())

        # highlighted_img is returned
        self.assertIsNotNone(highlighted_img)

        # annotations are also returned
        self.assertIsNotNone(annotations)

        # annotation starts from actual dialogue
        first_y_coordinate = annotations[0][0][0][1]
        second_y_coordinate = annotations[0][0][1][1]
        # the first detected word or phrase and the second one should be more or less on the same line. 
        self.assertAlmostEqual(first_y_coordinate, second_y_coordinate, 25)



if __name__ == '__main__':
    unittest.main()
