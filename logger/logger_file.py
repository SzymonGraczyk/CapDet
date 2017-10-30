import os

from logger.loggerabc import LoggerABC

class LoggerFile(LoggerABC):
    path = None

    def __init__(self, path, verbosity=0):
        super(LoggerFile, self).__init__()

        if self._verify_path(path):
            self.path = path
        else:
            raise Exception('Invalid logger path')

        self._verbosity = verbosity

    def msg(self, msg, **_):
        if self._verbosity > 1:
            self._log_to_file(msg, self.path)

    def info(self, info, **_):
        self._log_to_file(info, self.path)

    def warning(self, warning, **_):
        if self._verbosity > 0:
            self._log_to_file(warning, self.path)

    def error(self, error, **_):
        self._log_to_file(error, self.path)

    def _verify_path(self, path):
        if not path:
#            print 'Cannot log to None'
            return False

        if os.path.exists(path) and \
           not os.path.isfile(path):
#            print "Log path '%s' is not a file" % path
            return False

        if not os.path.exists(path):
#            print "Log file '%s' does not exist. Try to create one." % path

            try:
                with open(path, 'a') as f:
                    pass
#                    print "Log file '%s' created" % path
            except Exception as e:
#                print 'Error occurred while creating log file: %s' % e
                return False

        return True
