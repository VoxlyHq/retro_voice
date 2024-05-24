from Xlib import display
import numpy as np
from PIL import Image
from mss import mss
import subprocess

def find_window_id(window_name):
    root = display.Display().screen().root
    window_id = None

    def _find_window(root, window_name):
        nonlocal window_id
        children = root.query_tree().children
        for child in children:
            try:
                if window_name.lower() in (child.get_wm_name() or "").lower():
                    window_id = child.id
                    return
            except:
                pass
            _find_window(child, window_name)

    _find_window(root, window_name)
    return window_id

def capture_window_to_pil(window_id, file_path):
    cmd = f"xwininfo -id {window_id}"
    proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    out = out.decode()

    # Improved parsing logic to handle the xwininfo output
    geom = {}
    for line in out.split("\n"):
        if "Absolute upper-left X:" in line:
            geom["x"] = int(line.split()[-1])
        if "Absolute upper-left Y:" in line:
            geom["y"] = int(line.split()[-1])
        if "Width:" in line:
            geom["width"] = int(line.split()[-1])
        if "Height:" in line:
            geom["height"] = int(line.split()[-1])

    if not all(key in geom for key in ["x", "y", "width", "height"]):
        raise ValueError("Failed to get window geometry from xwininfo output")

    monitor = {
        "top": geom["y"],
        "left": geom["x"],
        "width": geom["width"],
        "height": geom["height"]
    }

    with mss() as sct:
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        pil_image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    
    return pil_image

def capture_window_to_file(window_id, file_path):
    print(f"Capturing window {window_id} to {file_path}")
    try:
        pil_image = capture_window_to_pil(window_id, file_path)
        if pil_image is not None:
            print(f"Saved window capture to {file_path}")
            pil_image.save(file_path)
    except Exception as e:
        print(f"Failed to capture window: {e}")
    return pil_image

if __name__ == "__main__":
    window_handle = find_window_id("RetroArch")
    if window_handle:
        res = capture_window_to_file(window_handle, "window_capture.jpg")
    else:
        print("Window not found.")
