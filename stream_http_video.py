import av
import io
import cv2
import numpy as np
from flask import Flask, Response, send_from_directory
from io import BytesIO
import time


app = Flask(__name__,
            static_url_path='',
            static_folder='html')

def generate_mjpeg():
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


@app.route('/video_mjpeg')
def video_feed():
    return Response(generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')



def generate_encoded():
    # Parameters for the video
    width, height = 640, 480
    fps = 24
    
    # Setup memory buffer
    buffer = BytesIO()

    # Create a video encoder
    codec_name = 'libx264'  # H.264 codec
    output = av.open(buffer, mode='w', format='mpegts')
    stream = output.add_stream(codec_name, rate=fps)
    stream.width = width
    stream.height = height
    stream.pix_fmt = 'yuv420p'
    
    for angle in range(0, 360):
        # Create a black image
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Define the square's properties
        center = (width // 2, height // 2)
        size = min(width, height) // 4
        rect_pts = np.array([
            [-size, -size],
            [size, -size],
            [size, size],
            [-size, size]
        ], dtype=np.float32)
        
        # Rotate the square
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_pts = cv2.transform(np.array([rect_pts]), M)[0].astype(np.int32)
        
        # Draw the rotated square
        cv2.fillPoly(image, [rotated_pts], (0, 255, 0))
        
        # Create frame from the image
        frame = av.VideoFrame.from_ndarray(image, format='bgr24')
        for packet in stream.encode(frame):
            output.mux(packet)
            buffer.seek(0)
            chunk = buffer.read()
            buffer.seek(0)
            buffer.truncate()
            yield chunk
    
    # Finalize video stream
    for packet in stream.encode(None):
        output.mux(packet)
        buffer.seek(0)
        chunk = buffer.read()
        buffer.seek(0)
        buffer.truncate()
        if chunk:
            yield chunk
    
    # Close everything
    output.close()
    buffer.close()


@app.route('/video')
def video():
    return Response(generate_encoded(), mimetype='video/mp2t')


@app.route('/')
def index():
    return send_from_directory('html', 'video.html')

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5001)