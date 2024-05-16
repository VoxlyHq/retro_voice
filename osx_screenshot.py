import Quartz
from Cocoa import NSURL
from Quartz import CGWindowListCopyWindowInfo, kCGNullWindowID, kCGWindowListOptionAll, kCGWindowImageBoundsIgnoreFraming, CGWindowListCreateImage, CGRectNull
from Quartz import CGImageGetWidth, CGImageGetHeight, CGImageGetDataProvider, CGDataProviderCopyData, CGImageGetAlphaInfo
from Quartz.CoreGraphics import CGImageGetBitsPerPixel, CGImageGetBitsPerComponent, CGImageGetBytesPerRow
from Quartz import CGImageGetWidth, CGImageGetHeight, CGImageGetDataProvider, CGDataProviderCopyData
from Quartz.CoreGraphics import CGImageGetBitsPerPixel, CGImageGetBitsPerComponent, CGImageGetBytesPerRow, CGImageGetAlphaInfo, kCGImageAlphaNoneSkipFirst, kCGImageAlphaNoneSkipLast, kCGImageAlphaPremultipliedFirst, kCGImageAlphaPremultipliedLast, kCGImageAlphaFirst, kCGImageAlphaLast, kCGImageAlphaNone
from Quartz.CoreGraphics import kCGImageAlphaPremultipliedFirst
import Quartz.CoreGraphics as CG
import os
import numpy as np
from PIL import Image
from image_diff import image_crop_title_bar

def cgimage_to_pil(cgimage):
    width = CGImageGetWidth(cgimage)
    height = CGImageGetHeight(cgimage)
    provider = CGImageGetDataProvider(cgimage)
    data = CGDataProviderCopyData(provider)
    bpp = CGImageGetBitsPerPixel(cgimage) // 8
    bytes_per_row = CGImageGetBytesPerRow(cgimage)
    alpha_info = CGImageGetAlphaInfo(cgimage)

    # Check the alpha channel presence and position
    if alpha_info in (kCGImageAlphaNoneSkipFirst, kCGImageAlphaPremultipliedFirst, kCGImageAlphaFirst, kCGImageAlphaNoneSkipLast, kCGImageAlphaPremultipliedLast, kCGImageAlphaLast):
        mode = 'RGBA'
    else:
        mode = 'RGB'
    
    # Convert the data to a numpy array
    np_data = np.frombuffer(data, dtype=np.uint8)
    np_data = np_data.reshape((height, bytes_per_row // bpp, bpp))
    
    # Correct the color channel order if necessary
    if mode == 'RGBA':
        # Assume the source is BGRA, convert to RGBA
        np_data = np_data[:, :, [2, 1, 0, 3]]
    else:
        # Assume the source is BGR, convert to RGB
        np_data = np_data[:, :, [2, 1, 0]]
    
    # Create the PIL image
    return Image.fromarray(np_data, mode)


def find_window_id(window_name):
    options = kCGWindowListOptionAll
    window_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
    for window in window_list:
        if window_name.lower() in window.get('kCGWindowName', '').lower():
            #print(f"Found window '{window.get('kCGWindowName', '')}' with ID {window['kCGWindowNumber']}")
            return window['kCGWindowNumber']
    print(f"Osx Window '{window_name}' not found.")
    return None


def capture_window_to_pil(window_id, file_path, crop_y_coordinate=37):
    #print(f"Capturing window {window_id}")
    #kCGWindowListOptionIncludingWindow
    image = CGWindowListCreateImage(CGRectNull, CG.kCGWindowListOptionIncludingWindow, window_id, 0)
    if image:
        url = NSURL.fileURLWithPath_(file_path)
        destination = Quartz.CGImageDestinationCreateWithURL(url, 'public.jpeg', 1, None)
        if destination:
            Quartz.CGImageDestinationAddImage(destination, image, None)
            Quartz.CGImageDestinationFinalize(destination)
        else:
            print("Failed to create image destination.")
        pil_image = cgimage_to_pil(image)
        # Assuming pil_image is your PIL Image object in 'RGBA' mode
        if pil_image.mode == 'RGBA':
            pil_image = pil_image.convert('RGB')

        pil_image = image_crop_title_bar(pil_image, crop_y_coordinate)

        return pil_image         
    else:
        print("Failed to capture window.")
        return None

def capture_window_to_file(window_id, file_path, crop_y_coordiante=37):
    print(f"Capturing window {window_id} to {file_path}")
    pil_image = capture_window_to_pil(window_id, file_path, crop_y_coordiante)
    if pil_image != None:
        print(f"Saved window capture to {file_path}")
        pil_image.save('output.jpg')
    return pil_image

if __name__ == "__main__":
    x = find_window_id("RetroArch")
    res = capture_window_to_file(x, "window_capture.jpg")
    print(res)