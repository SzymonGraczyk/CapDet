from logger.loggerabc import LoggerABC

class LoggerStdout(LoggerABC):
    def __init__(self, verbosity=0):
        super(LoggerStdout, self).__init__()
        self._verbosity = verbosity

    def msg(self, msg, **_):
        if self._verbosity > 1:
            print(msg)

    def info(self, info, **_):
        print(info)

    def warning(self, warning, **_):
        if self._verbosity > 0:
            print(warning)

    def error(self, error, **_):
        print(error)
