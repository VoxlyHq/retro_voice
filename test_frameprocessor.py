import unittest
from unittest.mock import patch, mock_open
from process_frames import FrameProcessor  # Replace 'your_module' with the name of your Python file containing the FrameProcessor class

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
        self.assertEqual(fp.dialogues[closest_entry]['dialogue'], "Captain Cecil, we are about to arrive!")


    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open, read_data='[{"name": "test", "dialogue": "hello"}]')
    def test_load_dialogues(self, mock_file, mock_json_load):
        mock_json_load.return_value = [{"name": "test", "dialogue": "hello"}]
        fp = FrameProcessor()
        dialogues = fp.load_dialogues()
        self.assertEqual(len(dialogues), 1)
        self.assertEqual(dialogues[0]['dialogue'], 'hello')

    @patch('process_frames.fuzz.ratio', return_value=100)  # Assume perfect match for simplicity, replace 'your_module' accordingly
    def test_find_closest_entry(self, mock_fuzz_ratio):
        fp = FrameProcessor()
        # Pretend the dialogues loaded are as follows
        fp.dialogues = {0: {'name': 'Test', 'dialogue': 'hello'}}
        closest_entry = fp.find_closest_entry('hello')
        self.assertEqual(closest_entry, 0)
        


if __name__ == '__main__':
    unittest.main()
