import os
import platform
import time
import keyboard
import pytesseract
import easyocr

from thefuzz import fuzz
from cloudvision import detect_text_google


# Detect the operating system
os_name = platform.system()
reader = easyocr.Reader(['en']) #(['ja', 'en']) 

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


def timed_action():
    print("Action triggered by timer")
    window_name = "RetroArch"  # Adjust this to the target window's name
    file_path = os.path.expanduser("window_capture.jpg")  # Save location
    window_id = find_window_id(window_name)
    if window_id:
        img = capture_window_to_file(window_id, file_path)

        # Use Tesseract to do OCR on the image
#        text = pytesseract.image_to_string(img)
        import time

        start_time = time.time() # Record the start time
        text = pytesseract.image_to_string('window_capture.jpg') #, lang='jpn')
        print("found text terrasect----")
        print(text)
        print("----")
        end_time = time.time() # Record the end time
        print(f"Time taken: {end_time - start_time} seconds")
        thefuzz_test(text)

        start_time = time.time() # Record the start time
        result = reader.readtext('window_capture.jpg')
        print("found text easyocr----")
        print(result)
        print("----")
        end_time = time.time() # Record the end time
        print(f"Time taken: {end_time - start_time} seconds")

        start_time = time.time() # Record the start time
        # Replace the path below with the path to your image file
        result = detect_text_google('window_capture.jpg')
        print("found text google----")
        print(result)
        print("----")
        print(f"Time taken: {end_time - start_time} seconds")

    else:
        print(f"No window found with name containing '{window_name}'.")

def main():
    print("Press ESC to exit...")
    while True:
        timed_action()
        time.sleep(1)  # Wait for 1 second
        if keyboard.is_pressed('esc'):
            print("Escape pressed, exiting...")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interrupted")
    except PermissionError:
        print("Permission denied: You might need to run as administrator/root or check your security settings.")
