import base64
import http.server
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import socketserver
import threading
from time import sleep
from urllib.parse import urlparse
import signal
import sys
import socket
import json
from PIL import Image
import cgi
import io

from process_frames import FrameProcessor
from thread_safe import shared_data_get_data, shared_data_put_data, shared_data_put_line, ThreadSafeData

dialog_file = "dialogues_en_web.json"
previous_image = Image.new('RGB', (100, 100), (255, 255, 255))
previous_highlighted_image = Image.new('RGB', (100, 100), (255, 255, 255))

image_changed = False

HOST = 'localhost'
PORT = 8000


def set_dialog_file(file):
    global dialog_file
    dialog_file = file
    
class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    #TODO make one per language
    frameProcessor =  FrameProcessor() #potentially not thread safe

    def __init__(self, *args, custom_variable='default_value', **kwargs):
        # Call the superclass's __init__ method
        super().__init__(*args, **kwargs)

    def do_POST(self):
        global image_changed
        global previous_image
        global previous_highlighted_image
        # Parse the URL to get the path
        url_path = urlparse(self.path).path
        print(f"Received POST request for {url_path}")

        if url_path == "/upload_screenshot":
            # Handle screenshot upload
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            if ctype == 'multipart/form-data':
                # Parse the multipart data
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                        environ={'REQUEST_METHOD': 'POST',
                                                 'CONTENT_TYPE': self.headers['Content-Type']})
                if 'image' in form:
                    file_item = form['image']
                    if file_item.filename:
                        # Convert to bytes and then to PIL Image
                        image_data = file_item.file.read()
                        image = Image.open(io.BytesIO(image_data))
                        image = image.convert('RGB')
                        image.save('saved_image.jpg')


                       # image.show()  # Or perform any other operation with the Pillow image
                        last_played, tmp_previous_image, tmp_previous_highlighted_image =  self.frameProcessor.run_image(image)


                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        if None != last_played:
                            image_changed = True
                            previous_image = tmp_previous_image
                            previous_highlighted_image = tmp_previous_highlighted_image
                            print("image changed---")
                            self.wfile.write(f"Last played: {last_played}".encode())
                        else:
                            self.wfile.write("".encode())
                    else:
                        self.send_error(400, "File is missing in the form")
                else:
                    self.send_error(400, "Form is missing 'image' field")
            else:
                self.send_error(400, "Only 'multipart/form-data' is supported")
        else:
            self.send_error(404, 'File Not Found: %s' % self.path)


    def dump_image(self):
        global dialogfile
        global previous_highlighted_image
        # Load your image using PIL here
        img_byte_arr = io.BytesIO()
        previous_highlighted_image.save(img_byte_arr, format='JPEG') # You can change the format if needed
        
        # Convert image bytes to a base64 encoded string
        encoded_img = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{encoded_img}" # This assumes JPEG format
        
        # Send the data URL as the event data
        self.wfile.write(b'data: ' + data_url.encode() + b'\n\n')
        self.wfile.flush()

    def do_GET(self):
        global dialogfile
        global image_changed
        # Parse the URL to get the path
        url_path = urlparse(self.path).path

        print(f"Received request for {url_path}")   
        if url_path == "/":
            # Serve the index.html file for the root URL
            self.path = 'index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif url_path == "/html_scrape.html":
            # Serve the index.html file for the root URL
            self.path = 'html_scraper/html_scrape.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif url_path == "/script.js":
            # Serve the index.html file for the root URL
            self.path = 'html_scraper/script.js'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)        
        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            self.dump_image() # send them the first image
            while True: 
                try:
                    if not image_changed:
                        print("image not changed")
                        sleep(1)
                        continue
                    print("image changed")
                    image_changed = False
                    self.dump_image()
                except Exception as e:
                    print("Connection closed by client or error:", e)
                    break
        elif url_path == "/script.json":
            # Return the contents of the script.json file
            try:
                with open(dialog_file, "rb") as file:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(file.read())
            except FileNotFoundError:
                self.send_error(404, 'File Not Found: script.json')
        elif url_path == "/log":
            # Let's assume you want to fetch and display data from the shared queue
            data = shared_data_get_data()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            response_message = f"Data from queue: {data}" if data else ""
            self.wfile.write(response_message.encode())
        elif url_path == "/highlight":
            # Return a JSON object with highlightedLine set to 3
            response = {"highlightedLine": shared_data_get_data()}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            # For any other endpoint, return a 404 Not Found response
            self.send_error(404, 'File Not Found: %s' % self.path)


httpd = None
class MyHTTPServer(http.server.HTTPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()


# Use MyHTTPServer instead of HTTPServer
def run_server2(port=8000, dummy=""):
    global httpd

    httpd = ThreadingHTTPServer((HOST, PORT), CustomHTTPRequestHandler)
    print(f"Serving HTTP on port {port}...")
    httpd.serve_forever()


# Signal handler function
def signal_handler(sig, frame):
    global httpd
    print('Shutting down server...')
    httpd.server_close()  # Properly close the server
    sys.exit(0)


if __name__ == "__main__":
#    set_dialog_file("dialogues_jp_web.json")
    # Run the server
    run_server2()
    signal.signal(signal.SIGINT, signal_handler)
