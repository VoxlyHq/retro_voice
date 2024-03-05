import http.server
import socketserver
import threading
import queue

class ThreadSafeData:
    def __init__(self):
        self.queue = queue.Queue()

    def put_data(self, data):
        self.queue.put(data)

    def get_data(self):
        if not self.queue.empty():
            return self.queue.get()
        return None

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Let's assume you want to fetch and display data from the shared queue
        data = shared_data.get_data()
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        response_message = f"Data from queue: {data}" if data else "No data in queue."
        self.wfile.write(response_message.encode())

# Create a shared data instance
shared_data = ThreadSafeData()

def shared_data_put_data(data):
    shared_data.put_data(data)  # Put data into the shared queue

def run_server(handler_class=CustomHTTPRequestHandler, port=8000):
    with socketserver.TCPServer(("", port), handler_class) as httpd:
        print(f"Serving HTTP on port {port}...")
        httpd.serve_forever()