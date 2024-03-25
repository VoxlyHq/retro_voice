
from cloudvision import detect_text_google_pil, detect_text_google, detect_text_and_draw_boxes
from thefuzz import fuzz
import pytesseract
import easyocr
import json
from PIL import Image
from image_diff import calculate_image_difference
import time
from thread_safe import shared_data_put_data, shared_data_put_line, ThreadSafeData

class FrameProcessor:
    def __init__(self, language='en'):
        self.counter = 0  # Convert the global variable to an instance attribute
        self.lang = language
        if language == 'en':
            self.dialog_file_path = "dialogues_en_v2.json"
        elif language == 'jp':
            self.dialog_file_path = "dialogues_jp_v2.json"
        else:   
            raise("Invalid language")   

        self.dialogues = self.load_dialogues()
        print(self.dialogues)
        #TODO remove this from this class and store this somewhere else, so its multi user
        self.previous_image = Image.new('RGB', (100, 100), (255, 255, 255))
        self.last_played = -1 #TODO this should be per user


    def load_dialogues(self):
        # File path to your JSON data
        file_path = self.dialog_file_path

        # Read JSON data from the file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Convert list to a numbered dictionary
        dialogues = {index: item for index, item in enumerate(data)}

        # Print the numbered dictionary
        for number, entry in dialogues.items():
            print(f"{number}: Name: {entry['name']}, Dialogue: {entry['dialogue']}")
        #    print(format_filename(number))
        
        return dialogues


    def find_closest_entry(self, numbered_data, current_text):
        print(f"find_closest_entry- current_text: {current_text}")
        if "Contentless Cores Explore"   in current_text:
            print(f"skipping menu")
            return None

        
        # Initialize variables to track the highest similarity and corresponding entry number
        max_similarity_ratio = 0.33  # Start with your threshold
        closest_entry_number = None
        
        for number, entry in numbered_data.items():
            dialogue = entry['dialogue']
            similarity_ratio = fuzz.ratio(current_text, dialogue) / 100.0  # Convert to a scale of 0 to 1
            #print(f"dialogue: {dialogue} -- similarity_ratio: {similarity_ratio} -- number {number}")
            
            # Update if this entry has a higher similarity ratio than current max and is above threshold
            if similarity_ratio > max_similarity_ratio:
                max_similarity_ratio = similarity_ratio
                closest_entry_number = number

        return closest_entry_number  # Return the entry number with the highest similarity ratio over 0.33


    @staticmethod
    def thefuzz_test(ocr_text):
        # Known script text
        known_text = "some known text here"

        # Calculate similarity score
        score = fuzz.ratio(ocr_text, known_text)

        print(score)  # This will print the similarity score as a percentage

    def run_ocr(self, image):
            # Use Tesseract to do OCR on the image
    #        text = pytesseract.image_to_string(img)
    
        # start_time = time.time() # Record the start time
        # text = pytesseract.image_to_string('window_capture.jpg') #, lang='jpn')
        # print("found text terrasect----")
        # print(text)
        # print("----")
        # end_time = time.time() # Record the end time
        # print(f"Time taken: {end_time - start_time} seconds")

        # start_time = time.time() # Record the start time
        # result = reader.readtext('window_capture.jpg')
        # print("found text easyocr----")
        # print(result)
        # print("----")
        # end_time = time.time() # Record the end time
        # print(f"Time taken: {end_time - start_time} seconds")
    
        start_time = time.time() # Record the start time
        # # Replace the path below with the path to your image file
        result = detect_text_google_pil(image)
        #result = detect_text_and_draw_boxes('window_capture.jpg')

        filtered_array = [entry for entry in result if 'RetroArch' not in entry]
        str = ' '.join(filtered_array)
        print("found text google----")
        print(str)
        print("----")
        end_time = time.time()
        print(f"Time taken: {end_time - start_time} seconds")
            
        #thefuzz_test(text)
        res = self.find_closest_entry(self.dialogues, str)
        if res != None:
            print("found entry ")
            print(res)
            if res == self.last_played:
                print("Already played this entry")
            else:
                print(f"shared_data_put_line---{res}")
                shared_data_put_line(res+1)
                self.last_played = res
        return res


    def process_frame(self, frame_pil, frame_count, fps):
        """
        Process the frame: Save it to disk and possibly do more processing.
        """
        # Assume run_image is a function you want to run on the frame
        x, y = self.run_image(frame_pil)
        
        print(f"Frame at {frame_count//fps} seconds")
        return x,y

    def run_image(self, img):
        print("previous_image--{previous_image}")
        print(self.previous_image)
        print("-0--")
        percent_diff = calculate_image_difference(img, self.previous_image)
        print(f'Images differ by {percent_diff:.2f}%')

        # Decide whether to call OCR based on the difference
        if percent_diff > 10:
            print("Images are more than 10% different. Proceed with OCR.")
            last_played = self.run_ocr(img)
            print(f"finished ocr - {last_played} ")
            self.previous_image = img
            return last_played, self.previous_image
        else:
            print("Difference is less than 10%. No need to call OCR again.")
            return None, None