import threading
import os

class CThread(threading.Thread):
    _stop_event = None

    def __init__(self):
        threading.Thread.__init__(self)

        self._stop_event = threading.Event()
        
    def stop(self):
        self._stop_event.set()

    def isRunning(self):
        return not self._stop_event.is_set()
