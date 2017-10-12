from event_queue import EventQueue
from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

class EventDispatcher(EventQueue):
    _callbacks = {}

    def __init__(self):
        super(EventDispatcher, self).__init__()

    def enqueue(self, msg, highPriority = False):
        msg_type = msg[0]

        if not msg_type in self._callbacks:
            msg_type = '-1'
            msg_data = msg
        else:
            msg_data = msg[1:]

        callback = self._callbacks[msg_type]
        return super(EventDispatcher, self).enqueue(callback, [msg_data], {}, highPriority)

    def register_callback(self, msg_type, callback):
        if msg_type in self._callbacks:
            log.error('Callback already registered for msg type: %s' % msg_type)
            return -1

        if not callback:
            log.error('Cannot register empty callback')
            return -2

        self._callbacks[msg_type] = callback
