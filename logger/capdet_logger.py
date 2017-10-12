import datetime
import os

from logger.mlogger import MessageLogger
from singleton import Singleton

class CapDetLogger(MessageLogger):
    __metaclass__ = Singleton

    def add_logger(self, *loggers):
        self._loggers |= set(loggers)

    def remove_logger(self, *loggers):
        self._loggers -= set(loggers)

    def list_loggers(self):
        return self._loggers
