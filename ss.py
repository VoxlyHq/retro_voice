import os
import platform
import time
import keyboard
import pytesseract
import easyocr
import pygame
import time
import threading


from thefuzz import fuzz
from cloudvision import detect_text_google
from image_diff import calculate_image_difference

from PIL import Image
import json

# Detect the operating system
os_name = platform.system()
#reader = easyocr.Reader(['en']) #(['ja', 'en']) 

dialogues = {}
last_played = -1

def load_dialogues():
    # File path to your JSON data
    file_path = 'dialogues.json'

    # Read JSON data from the file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Convert list to a numbered dictionary
    dialogues = {index: item for index, item in enumerate(data)}

    # Print the numbered dictionary
    for number, entry in dialogues.items():
        print(f"{number}: Name: {entry['name']}, Dialogue: {entry['dialogue']}")
        print(format_filename(number))
    
    return dialogues

def format_filename(number):
    # Format the number with leading zeros to ensure it's four digits
    number_padded = f"{number:04d}"

    # Create the file name using the padded number
    file_name = f"ff4_v1_prologue_{number_padded}.mp3"

    return file_name

def play_audio(filename):
    print(f"output_en_elevenlabs/{filename}")
    # Initialize the mixer module
    pygame.mixer.init()
    
    # Load the MP3 file
    pygame.mixer.music.load(f"output_en_elevenlabs/{filename}")
    
    # Play the music
    pygame.mixer.music.play()
    
    # Wait for the music to finish playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)  # Wait a bit for the music to finish

# Function to wrap your play_mp3 for threading
def play_audio_threaded(filename):
    # Create a thread targeting the play_mp3 function
    thread = threading.Thread(target=play_audio, args=(filename,))
    thread.start()  # Start the thread

def find_closest_entry(numbered_data, current_text):
    print(f"find_closest_entry- current_text: {current_text}")
    for number, entry in numbered_data.items():
        dialogue = entry['dialogue']
        similarity_ratio = fuzz.ratio(current_text, dialogue) / 100.0  # Convert to a scale of 0 to 1
        print(f"dialogue: {dialogue} -- comparing to {current_text} -- similarity_ratio: {similarity_ratio} -- number {number}")
        if similarity_ratio > 0.5:
            return number  # Return the first entry with a fuzz ratio greater than 0.3

    return None  # Return None if no entry meets the criterion


previous_image = Image.new('RGB', (100, 100), (255, 255, 255))

if os_name == 'Windows':
    # Import Windows-specific module
#    import windows_screenshot as os_module
    raise Exception(f"Windows unsupported OS: {os_name}")
elif os_name == 'Darwin':
    # Import macOS-specific module
    from osx_screenshot import find_window_id, capture_window_to_file
elif os_name == 'Linux':
    # Import Linux-specific module
#    import linux_module as os_module
        raise Exception(f"Linuex unsupported OS: {os_name}")
else:
    raise Exception(f"Unsupported OS: {os_name}")


def thefuzz_test(ocr_text):
    # Known script text
    known_text = "some known text here"

    # Calculate similarity score
    score = fuzz.ratio(ocr_text, known_text)

    print(score)  # This will print the similarity score as a percentage

def run_ocr(image):
    global last_played
    global dialogues

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
    result = detect_text_google('window_capture.jpg')
    filtered_array = [entry for entry in result if 'RetroArch' not in entry]
    str = ' '.join(filtered_array)
    print("found text google----")
    print(str)
    print("----")
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
        
    #thefuzz_test(text)
    res = find_closest_entry(dialogues, str)
    if res != None:
        print("found entry ")
        print(res)
        if res <= last_played:
            print("Already played this entry")
        else:
            last_played = res
            play_audio_threaded(format_filename(res))


def timed_action():
    print("Action triggered by timer")
    global previous_image
    global dialogues

    window_name = "RetroArch"  # Adjust this to the target window's name
    file_path = os.path.expanduser("window_capture.jpg")  # Save location
    window_id = find_window_id(window_name)
    if window_id:
        img = capture_window_to_file(window_id, file_path)


        print("previous_image--{previous_image}")
        print(previous_image)
        print("-0--")
        percent_diff = calculate_image_difference(img, previous_image)
        print(f'Images differ by {percent_diff:.2f}%')

        # Decide whether to call OCR based on the difference
        if percent_diff > 10:
            print("Images are more than 10% different. Proceed with OCR.")
            run_ocr(img)
            previous_image = img
        else:
            print("Difference is less than 10%. No need to call OCR again.")
            

    else:
        print(f"No window found with name containing '{window_name}'.")

def main():
    global dialogues
    dialogues =load_dialogues()
    print(dialogues)
    print("Press ESC to exit...")
    while True:
        timed_action()
        time.sleep(1)  # Wait for 1 second
        if keyboard.is_pressed('esc'): #TODO this doesn't seem to work without root on osx?
            print("Escape pressed, exiting...")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interrupted")
    except PermissionError:
        print("Permission denied: You might need to run as administrator/root or check your security settings.")
