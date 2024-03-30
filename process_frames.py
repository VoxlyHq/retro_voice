
from datetime import datetime
import io
import os
import requests
from cloudvision import detect_text_google_pil, detect_text_google, detect_text_and_draw_boxes
from thefuzz import fuzz
import pytesseract
import easyocr
import base64
import json
from PIL import Image
from image_diff import calculate_image_difference
import time
from thread_safe import shared_data_put_data, shared_data_put_line, ThreadSafeData
from PIL import Image, ImageDraw, ImageFont


OPENAI_API_KEY = os.environ.get("OPENAI_ACCESS_TOKEN")

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
        #print(self.dialogues)
        #TODO remove this from this class and store this somewhere else, so its multi user
        self.previous_image = Image.new('RGB', (100, 100), (255, 255, 255))
        self.last_played = -1 #TODO this should be per user

        self.reader = easyocr.Reader(['en']) #(['ja', 'en'])  # comment this if you aren't using easy ocr


    def load_dialogues(self):
        print("load_dialogues-")
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


    def find_closest_entry(self, current_text):
        print(f"find_closest_entry- current_text: {current_text}")
        if "Contentless Cores Explore"   in current_text:
            print(f"skipping menu")
            return None

        
        # Initialize variables to track the highest similarity and corresponding entry number
        max_similarity_ratio = 0.33  # Start with your threshold
        closest_entry_number = None
        
        for number, entry in self.dialogues.items():
            dialogue = entry['dialogue']
            similarity_ratio = fuzz.ratio(current_text, dialogue) / 100.0  # Convert to a scale of 0 to 1
            #print(f"dialogue: {dialogue} -- similarity_ratio: {similarity_ratio} -- number {number}")
            
            # Update if this entry has a higher similarity ratio than current max and is above threshold
            if similarity_ratio > max_similarity_ratio:
                max_similarity_ratio = similarity_ratio
                closest_entry_number = number

        return closest_entry_number  # Return the entry number with the highest similarity ratio over 0.33

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def call_openai_vision_api(self, image_bytes):
        # Getting the base64 string
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        model_openai = "gpt-4-vision-preview"
        model_local = "llava_v16"
        model = model_local


        payload = {
        "model": model,
        "messages": [
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": "What is the text in the photo?"
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
                }
            ]
            }
        ],
        "max_tokens": 300
        }

        #openai_url = "https://api.openai.com/v1/chat/completions"
        local_url = "http://localhost:8080/v1/chat/completions"
        url = local_url

        response = requests.post(url, headers=headers, json=payload)
        print(response.json())
        return response.json()

    @staticmethod
    def thefuzz_test(ocr_text):
        # Known script text
        known_text = "some known text here"

        # Calculate similarity score
        score = fuzz.ratio(ocr_text, known_text)

        print(score)  # This will print the similarity score as a percentage

    def ocr_tesseract(self, image_path):
        # Use Tesseract to do OCR on the image
        #        text = pytesseract.image_to_string(img)
    
        # start_time = time.time() # Record the start time
        # text = pytesseract.image_to_string('window_capture.jpg') #, lang='jpn')
        # print("found text terrasect----")
        # print(text)
        # print("----")
        # end_time = time.time() # Record the end time
        # print(f"Time taken: {end_time - start_time} seconds")
        return None 

    def ocr_easyocr_and_highlight(self, image):
        # Convert the PIL Image to bytes
        byte_buffer = io.BytesIO()
        image.save(byte_buffer, format='JPEG')  # Change format if needed
        image_bytes = byte_buffer.getvalue()

        # Now, we want the locations as well, so detail=1
        result = self.reader.readtext(image_bytes, detail=1)

        # Creating a drawable image
        drawable_image = Image.open(io.BytesIO(image_bytes))
        draw = ImageDraw.Draw(drawable_image)
        
        # Optionally, load a font.
        # font = ImageFont.truetype("arial.ttf", 15)  # You might need to adjust the path and size

        filtered_result = []
        for (bbox, text, prob) in result:
            if 'RetroArch' not in text:
                filtered_result.append((bbox, text, prob))
                
                # Extracting min and max coordinates for the rectangle
                top_left = bbox[0]
                bottom_right = bbox[2]
                
                # Ensure the coordinates are in the correct format (floats or integers)
                top_left = tuple(map(int, top_left))
                bottom_right = tuple(map(int, bottom_right))
                
                # Draw the bounding box
                draw.rectangle([top_left, bottom_right], outline="red", width=2)
                
                # Annotate text. Adjust the position if necessary.
                draw.text(top_left, text, fill="yellow")
                
        # Assuming you want to return the concatenated text that doesn't include 'RetroArch'
        filtered_text = ' '.join([text for (_, text, _) in filtered_result])
        return filtered_text, drawable_image  # Now also returning the image with annotations

    def ocr_easyocr(self, image):
        # Convert the PIL Image to bytes
        byte_buffer = io.BytesIO()

        image.save(byte_buffer, format='JPEG')  # You can change format if needed
        image_bytes = byte_buffer.getvalue()


        result =  self.reader.readtext(image_bytes,detail = 0) #change detail if you want the locations
        filtered_array = [entry for entry in result if 'RetroArch' not in entry]
        str = ' '.join(filtered_array)
        return str



    def ocr_openai(self, image):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"frame_{timestamp}.png"
        # Convert the PIL Image to bytes
        byte_buffer = io.BytesIO()

        width, height = image.size
        new_height = height // 3

        # Crop the top half
        top_half = image.crop((0, 0, width, new_height))
        top_half.save(byte_buffer, format='JPEG')  # You can change format if needed
        image_bytes = byte_buffer.getvalue()

        result = self.call_openai_vision_api(image_bytes)

        result_filename = f"result_{timestamp}.json"
        with open(result_filename, 'w') as f:
            json.dump(result, f, indent=4)
        print(f"Saved analysis result to {result_filename}")
        content =  result['choices'][0]['message']['content']
        part_to_remove = " The text in the photo reads:"
        part_to_remove2 = "The text in the photo is"
        cleaned_string = content.replace(part_to_remove, "").replace(part_to_remove2, "").replace('"', '')    
        print(cleaned_string)
        return cleaned_string
    
    def ocr_google(self, image):
        result = detect_text_google_pil(image)
#        result = detect_text_and_draw_boxes('window_capture.jpg')

        filtered_array = [entry for entry in result if 'RetroArch' not in entry]
        str = ' '.join(filtered_array)
        print("found text google----")
        print(str)
        print("----")
        return str
    
    def run_ocr(self, image):
        start_time = time.time() # Record the start time

        str, highlighted_image = self.ocr_easyocr_and_highlight(image)
#        str = self.ocr_openai(image)
#        str = self.ocr_google(image)
        
        
        print("found text ocr----")
        print(str)
        print("----")
    


        end_time = time.time()
        print(f"Time taken: {end_time - start_time} seconds")
            
        #thefuzz_test(text)
        res = self.find_closest_entry(str)
        if res != None:
            print("found entry ")
            print(res)
            if res == self.last_played:
                print("Already played this entry")
            else:
                print(f"shared_data_put_line---{res}")
                shared_data_put_line(res+1)
                self.last_played = res
        return res, highlighted_image


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
            last_played, highlighted_image = self.run_ocr(img)
            print(f"finished ocr - {last_played} ")
            self.previous_image = img
            return last_played, self.previous_image, highlighted_image
        else:
            print("Difference is less than 10%. No need to call OCR again.")
            return None, None, None