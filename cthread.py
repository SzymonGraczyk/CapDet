import threading
import os

class CThread(threading.Thread):
    stop_event = None

    def __init__(self):
        threading.Thread.__init__(self)

        self.stop_event = threading.Event()
        
    def stop(self):
        self.stop_event.set()

    def isRunning(self):
        return not self.stop_event.is_set()
