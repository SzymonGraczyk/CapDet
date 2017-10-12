import platform
import socket

from detector_interface import *

class HostDetector(DetectorInterface):
    def detect(self):
        self['hostname']       = socket.gethostname().strip()
        self['os']             = platform.system().strip()
        self['distro']         = platform.linux_distribution()[0].strip()
        self['distro_version'] = platform.linux_distribution()[1].strip()
        self['distro_arch']    = platform.linux_distribution()[2].strip()
        self['release']        = platform.release().strip()
