from abc import ABCMeta

class LoggerABC(object):
    __metaclass__ = ABCMeta

    @staticmethod
    def _log_to_file(log, path):
        with open(path, 'a', 1) as handler:
            handler.write(log + '\n')

    def msg(self, msg, **_):
        raise NotImplementedError

    def info(self, info, **_):
        raise NotImplementedError

    def warning(self, warning, **_):
        raise NotImplementedError

    def error(self, error, **_):
        raise NotImplementedError
