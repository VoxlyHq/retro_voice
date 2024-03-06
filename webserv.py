import http.server
import socketserver
import threading
import queue
from urllib.parse import urlparse
import signal
import sys
import socket
import json

class ThreadSafeData:
    def __init__(self):
        self.queue = queue.Queue()
        self.line = 0

    def put_line(self, line):
        self.line = line

    def get_line(self):
        return self.line

    def put_data(self, data):
        self.queue.put(data)

    def get_data(self):
        if not self.queue.empty():
            return self.queue.get()
        return None


dialog_file = "dialogues_en_web.json"

def set_dialog_file(file):
    global dialog_file
    dialog_file = file
class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        global dialogfile
        # Parse the URL to get the path
        url_path = urlparse(self.path).path

        print(f"Received request for {url_path}")   
        if url_path == "/":
            # Serve the index.html file for the root URL
            self.path = 'index.html'
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


# Create a shared data instance
shared_data = ThreadSafeData()

def shared_data_put_data(data):
    shared_data.put_data(data)  # Put data into the shared queue

def shared_data_put_line(line):
    shared_data.put_line(line)  # Put data into the shared queue


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
    # Run the server
    run_server2()
    signal.signal(signal.SIGINT, signal_handler)
