import cv2
import numpy as np
from mss import mss

import Quartz
from Foundation import NSSet, NSDictionary

def find_window_by_name(window_name):
    # Get the list of windows
    window_list = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    
    # Convert the window list to a more Python-friendly format
    window_list = [dict(window) for window in window_list]
    
    # Filter the list to windows containing the specified name
    matching_windows = [window for window in window_list if window_name.lower() in window.get('kCGWindowName', '').lower()]
    
    return matching_windows

# Example usage
if __name__ == "__main__":
    window_name = "RetroArch"  # Adjust this to the exact window title
    matching_windows = find_window_by_name(window_name)
    res_window = {}
    if matching_windows:
        print(f"Found {len(matching_windows)} window(s) matching '{window_name}':")
        for window in matching_windows:
            print(window)
            res_window = window['kCGWindowBounds']
    else:
        print(f"No windows found with name containing '{window_name}'.")
        exit(0)


    # Specify the screen part to capture
    monitor = {"top": res_window['Y'], "left": res_window["X"], "width": res_window["Width"], "height": res_window["Height"]}
    print(monitor)

    with mss() as sct:
        # Capture the screen
        screenshot = sct.grab(monitor)

        # Convert to an array
        img = np.array(screenshot)

        # Convert from BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Save the image
        cv2.imwrite("screen_capture.jpg", img)
