import http.server
import socketserver
import threading
from urllib.parse import urlparse
import signal
import sys
import socket
import json
from PIL import Image
import cgi
import io

from process_frames import FrameProcessor
from thread_safe import shared_data_put_data, shared_data_put_line, ThreadSafeData

dialog_file = "dialogues_en_web.json"

def set_dialog_file(file):
    global dialog_file
    dialog_file = file
class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, custom_variable='default_value', **kwargs):
        #TODO make one per language
        self.frameProcessor =  FrameProcessor()

        # Call the superclass's __init__ method
        super().__init__(*args, **kwargs)

    def do_POST(self):
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
                        last_played, previous_image =  self.frameProcessor.run_image(image)


                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        if None != last_played:
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

    def do_GET(self):
        global dialogfile
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
            data = shared_data.get_data()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            response_message = f"Data from queue: {data}" if data else ""
            self.wfile.write(response_message.encode())
        elif url_path == "/highlight":
            # Return a JSON object with highlightedLine set to 3
            response = {"highlightedLine": shared_data.get_line()}
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

    server_address = ('', port)
    httpd = MyHTTPServer(server_address, CustomHTTPRequestHandler)
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
