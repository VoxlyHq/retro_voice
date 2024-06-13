import queue

class MessageQueue:
    def __init__(self):
        self.queue = queue.Queue()

    def send_message(self, message):
        self.queue.put(message)

    def receive_message(self):
        try:
            message = self.queue.get(timeout=1)
            return message
        except queue.Empty:
            return None
