import threading
import datetime

from singleton import Singleton

class MessageLogger(object):
    __metaclass__ = Singleton

    _loggers = set()
    _lock    = threading.Lock()

    @classmethod
    def _log(cls, message, log_type, loggers=None, **kwargs):
        if loggers is None:
            loggers = cls._loggers

        for logger in loggers:
            func = getattr(logger, log_type)
            func(message, **kwargs)

    def msg(self, log, loggers=None, **_):
        with self._lock:
            message = 'MSG:     %s|%s' % (datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f"), log)
            self._log(message, 'msg', loggers)

    def info(self, log, loggers=None, **_):
        with self._lock:
            message = 'INFO:    %s|%s' % (datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f"), log)
            self._log(message, 'info', loggers)

    def warning(self, log, loggers=None, **_):
        with self._lock:
            message = 'WARNING: %s|%s' % (datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f"), log)
            self._log(message, 'warning', loggers)

    def error(self, log, loggers=None, **_):
        with self._lock:
#        config['error_logged_flag'] = True
            message = 'ERROR:   %s|%s' % (datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f"), log)
            self._log(message, 'error', loggers)
