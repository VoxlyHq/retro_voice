import os
import platform
import signal
import time
import keyboard
import pytesseract
import easyocr
import pygame
import time
import threading
import argparse
import cv2 
from PIL import Image
import concurrent.futures

from thefuzz import fuzz
from cloudvision import detect_text_google, detect_text_and_draw_boxes
from image_diff import calculate_image_difference

from PIL import Image
import json

from webserv import CustomHTTPRequestHandler, run_server2, set_dialog_file, shared_data_put_data, shared_data_put_line, signal_handler

# Detect the operating system
os_name = platform.system()
#reader = easyocr.Reader(['en']) #(['ja', 'en']) 

dialogues = {}
last_played = -1

dialog_file_path = "dialogues_v2.json"
lang = ""

def load_dialogues():
    global dialog_file_path
    # File path to your JSON data
    file_path = dialog_file_path

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
    file_name = f"ff4_v1_prologue_{langnumber_padded}.mp3"

    return file_name

def play_audio(filename):
    print(f"output_en_elevenlabs/{filename}")
    # Initialize the mixer module
    pygame.mixer.init()
    
    # Load the MP3 file
    pygame.mixer.music.load(f"output_v2_{lang}_elevenlabs/{filename}")
    
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
    #result = detect_text_google('window_capture.jpg')
    result = detect_text_and_draw_boxes('window_capture.jpg')

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
        if res == last_played:
            print("Already played this entry")
        else:
            print(f"shared_data_put_line---{res}")
            shared_data_put_line(res+1)
            last_played = res
            start_time = time.time() # Record the start time
            play_audio_threaded(format_filename(res))
            end_time = time.time()
            print(f"Audio Time taken: {end_time - start_time} seconds")


def process_frame(frame_pil, frame_count, fps):
    """
    Process the frame: Save it to disk and possibly do more processing.
    """
    # Assume run_image is a function you want to run on the frame
    run_image(frame_pil)
    
    print(f"Frame at {frame_count//fps} seconds")

def process_video(video_path):
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    
    fps = cap.get(cv2.CAP_PROP_FPS)  # Get the frames per second of the video
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # Exit the loop if we've reached the end of the video

        # Process one frame per second (approximately)
        if frame_count % int(fps) == 0:
            # Convert the frame (which is in BGR format) to RGB format for PIL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Save to disk
            pil_image.save("window_capture.jpg")
            print(f"Frame at {frame_count//fps} seconds saved as debug.jpg")
            run_image(pil_image)
        
        frame_count += 1

    cap.release()  # Release the video capture object

def process_video_threaded(video_path, max_workers=10):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)  # Frames per second of the video
    frame_count = 0
    
    # Use ThreadPoolExecutor to manage concurrency
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break  # Exit the loop if we've reached the end of the video

            # Process one frame per second (approximately)
            if frame_count % int(fps) == 0:
                # Convert the frame (which is in BGR format) to RGB format for PIL
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                #TODO need to bundle like 10 frames together, cause the previous image check isnt working threaded

                # Submit the frame for processing in a separate thread
                future = executor.submit(process_frame, pil_image, frame_count, fps)
                futures.append(future)
            
            frame_count += 1
        
        # Wait for all futures to complete processing
        for future in concurrent.futures.as_completed(futures):
            # You can check for exceptions if needed and handle them
            pass

    cap.release()  # Release the video capture object

def run_image(img):
    global previous_image

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

def timed_action_screencapture():
    print("Action triggered by timer")
    global dialogues

    window_name = "RetroArch"  # Adjust this to the target window's name
    file_path = os.path.expanduser("window_capture.jpg")  # Save location
    window_id = find_window_id(window_name)
    if window_id:
        img = capture_window_to_file(window_id, file_path)
        run_image(img)
    else:
        print(f"No window found with name containing '{window_name}'.")
        shared_data_put_data(f"No window found with name containing '{window_name}'.")

def main():
    global dialogues
    global dialog_file_path
    global lang

    print("Press ESC to exit...")
    parser = argparse.ArgumentParser(description="Process a video or do a screencapture.")
    parser.add_argument('-v', '--video', type=str, help="Path to the video file to process.")
    parser.add_argument('-t', '--threads', type=int, default=10, help="Max threads for concurrent processing. Default is 10.")
    parser.add_argument('-w', '--webserver',  action='store_true', help="Enable Webserver")
    parser.add_argument('-jp', '--japanese',  action='store_true', help="Enable Japanese")

    args = parser.parse_args()

    if args.japanese:
        set_dialog_file("dialogues_web_jp.json")
        dialog_file_path = "dialogues_v2_jp.json"
        lang = "jp_"

    dialogues =load_dialogues()
    print(dialogues)

    if args.webserver:
        server_thread = threading.Thread(target=run_server2, args=(8000, ""), daemon=True)
        server_thread.start()
        signal.signal(signal.SIGINT, signal_handler)


        # Main thread: Put data into the shared queue
        shared_data_put_data("Hello from the main thread!")
        shared_data_put_line(0)

    if args.video:
        process_video(args.video)
        #process_video_threaded(args.video)
    else:
        while True:
            timed_action_screencapture()
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
