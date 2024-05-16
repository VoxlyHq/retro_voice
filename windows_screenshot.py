#pip install pywin32
import win32gui
import numpy as np

from PIL import Image
from mss import mss

def find_window_id(window_name):
    def callback(hwnd, window_name):
        if window_name.lower() in win32gui.GetWindowText(hwnd).lower():
            print(f"Found window '{win32gui.GetWindowText(hwnd)}' with handle {hwnd}")
            window_handles.append(hwnd)
    window_handles = []
    win32gui.EnumWindows(callback, window_name)
    
    return window_handles[0] if window_handles else None

def capture_window_to_pil(window_handle, file_path):
    
    # # Create a device context (DC) for the window
    hwndDC = win32gui.GetWindowDC(window_handle)

    left, top, right, bottom = win32gui.GetWindowRect(window_handle)
    
    monitor = {"top": top, "left": left, "width": right, "height": bottom}

    with mss() as sct:
        # Capture the screen
        screenshot = sct.grab(monitor)

        # Convert to an array
        img = np.array(screenshot)

        # Convert from BGR to RGB
        pil_image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    

    win32gui.ReleaseDC(window_handle, hwndDC)
    
    return pil_image



def capture_window_to_file(window_id, file_path):
    print(f"Capturing window {window_id} to {file_path}")
    pil_image = capture_window_to_pil(window_id, file_path)
    if pil_image != None:
        print(f"Saved window capture to {file_path}")
        pil_image.save(file_path)
    return pil_image

if __name__ == "__main__":
    window_handle = find_window_id("RetroArch")
    if window_handle:
        res = capture_window_to_file(window_handle, "window_capture.jpg")
    else:
        print("Window not found.")