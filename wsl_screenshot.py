#pip install mss pillow pywin32


import mss
import mss.tools
import numpy as np
from PIL import Image
import win32gui

def find_window_handle(window_name):
    return win32gui.FindWindow(None, window_name)

def capture_window_to_file(window_handle, file_path):
    print(f"Capturing window {window_handle} to {file_path}")
    
    left, top, right, bot = win32gui.GetWindowRect(window_handle)
    width = right - left
    height = bot - top

    with mss.mss() as sct:
        monitor = {"top": top, "left": left, "width": width, "height": height}
        sct_img = sct.grab(monitor)
        
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img.save(file_path)
        print(f"Saved window capture to {file_path}")

    return img

if __name__ == "__main__":
    window_handle = find_window_handle("RetroArch")
    if window_handle:
        res = capture_window_to_file(window_handle, "window_capture.jpg")
        print(res)
    else:
        print("Window not found.")