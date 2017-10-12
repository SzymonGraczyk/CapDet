import threading

from cthread import CThread

class IntervalThread(CThread):
    _interval  = 60
    _func      = None
    _int_event = None
    _int_lock  = None

    def __init__(self, func):
        super(IntervalThread, self).__init__()

        self._func      = func
        self._int_event = threading.Event()
        self._int_lock  = threading.Lock()

    def set_interval(self, interval):
        if interval <= 0:
            print '[ERROR] Invalid interval value: %d' % interval
            raise ValueError('Invalid interval value: %d' % interval)

        with self._int_lock:
            self._interval = interval

    def run(self):
        while self.isRunning():
            self._func()
        
            interval = 0
            with self._int_lock:
                interval = self._interval

            self._int_event.wait(timeout=interval)    

    def stop(self):
        super(IntervalThread, self).stop()
        self._int_event.set()
