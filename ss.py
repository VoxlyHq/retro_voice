from osx_screenshot import find_window_id, capture_window_to_file
import os


if __name__ == "__main__":
    window_name = "RetroArch"  # Adjust this to the target window's name
    file_path = os.path.expanduser("window_capture.jpg")  # Save location
    window_id = find_window_id(window_name)
    if window_id:
        capture_window_to_file(window_id, file_path)
    else:
        print(f"No window found with name containing '{window_name}'.")
