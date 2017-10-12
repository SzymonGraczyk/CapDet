import threading

from singleton import Singleton
from hostlist import HostList

class ServerConfig(object):
    __metaclass__ = Singleton

    _hostlist = None
    _lock     = None

    def __init__(self):
        self._hostlist = HostList()
        self._lock     = threading.Lock()

    def hostlist(self):
        with self._lock:
            return self._hostlist
