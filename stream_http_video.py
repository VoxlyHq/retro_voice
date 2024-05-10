from flask import Flask, Response, send_from_directory
import cv2
import numpy as np
import time

app = Flask(__name__)

def generate_video():
    # Constants for the video and square
    width, height = 640, 480
    square_size = 150
    frame_rate = 24
    frame_delay = 1 / frame_rate  # Delay to achieve ~24 FPS

    while True:  # Loop to make it continuous
        for angle in range(0, 360, 15):  # Increment angle for faster rotation and less frames
            # Create a black frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # Create a square
            square = np.zeros((square_size, square_size, 3), dtype=np.uint8)
            square[:] = (0, 0, 255)  # Red color

            # Rotate the square
            M = cv2.getRotationMatrix2D((square_size / 2, square_size / 2), angle, 1)
            rotated_square = cv2.warpAffine(square, M, (square_size, square_size))

            # Position the square in the center of the frame
            start_x = width // 2 - square_size // 2
            start_y = height // 2 - square_size // 2
            frame[start_y:start_y + square_size, start_x:start_x + square_size] = rotated_square

            # Encode frame as JPEG for streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue  # Skip the frame if encoding failed

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(frame_delay)  # Wait to control the frame rate


@app.route('/video_feed')
def video_feed():
    return Response(generate_video(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return send_from_directory('html', 'video.html')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
