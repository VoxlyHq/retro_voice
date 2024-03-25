import queue

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



# Create a shared data instance
shared_data = ThreadSafeData()

def shared_data_put_data(data):
    shared_data.put_data(data)  # Put data into the shared queue

def shared_data_put_line(line):
    shared_data.put_line(line)  # Put data into the shared queue
