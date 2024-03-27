#pip install pywin32
import win32gui
import win32ui
import win32con
from PIL import Image
import numpy as np

def find_window_handle(window_name):
    def callback(hwnd, window_name):
        if window_name.lower() in win32gui.GetWindowText(hwnd).lower():
            print(f"Found window '{win32gui.GetWindowText(hwnd)}' with handle {hwnd}")
            window_handles.append(hwnd)
    window_handles = []
    win32gui.EnumWindows(callback, window_name)
    return window_handles[0] if window_handles else None

def capture_window_to_file(window_handle, file_path):
    print(f"Capturing window {window_handle} to {file_path}")
    
    # Get the window dimensions
    left, top, right, bottom = win32gui.GetWindowRect(window_handle)
    width = right - left
    height = bottom - top
    
    # Create a device context (DC) for the window
    hwndDC = win32gui.GetWindowDC(window_handle)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    
    # Create a bitmap to store the window capture
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitMap)
    
    # Perform the window capture
    result = saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
    
    # Convert the bitmap to a PIL image
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    pil_image = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )
    
    # Save the PIL image to a file
    pil_image.save(file_path)
    print(f"Saved window capture to {file_path}")
    
    # Clean up
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(window_handle, hwndDC)
    
    return pil_image

if __name__ == "__main__":
    window_handle = find_window_handle("RetroArch")
    if window_handle:
        res = capture_window_to_file(window_handle, "window_capture.jpg")
        print(res)
    else:
        print("Window not found.")