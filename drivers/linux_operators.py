import os

from os_interface import OSInterface
from logger.capdet_logger import CapDetLogger
from execute import execute, ExecutionError

log = CapDetLogger()

class LinuxOperators(OSInterface):
    def __init__(self):
        super(LinuxOperators, self).__init__()

    def reboot(self):
        cmd = "sudo shutdown -r now"
        res, rc = execute(cmd)
        if rc != 0:
            log.error("Error rebooting host: '%s'" % res.strip())
            return

    def shutdown(self):
        cmd = "sudo shutdown now"
        res, rc = execute(cmd)
        if rc != 0:
            log.error("Error shutting down host: '%s'" % res.strip())
            return

    def __has_reboot(self):
        return not self.which('reboot') is None

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
