import os

from singleton import Singleton
from execute import execute

class DetectorInterface(dict):
    __metaclass__ = Singleton

    def __init__(self):
        super(DetectorInterface, self).__init__()

        self.detect()

    def detect(self):
        raise NotImplementedError('detect method is not implemented')

    def which(self, executable):
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(executable)
        if fpath:
            if is_exe(executable):
                return executable
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, executable)
                if is_exe(exe_file):
                    return exe_file

        return None
