from detectors.host import HostDetector
from detectors.cpu import CPUDetector
from detectors.fpga import FPGADetector
from detectors.network import NetworkDetector
from detectors.memory import MemoryDetector
from detectors.disk import DiskDetector

from singleton import Singleton

class Capabilities(dict):
    __metaclass__ = Singleton

    def __init__(self):
        super(Capabilities, self).__init__()

        self.update(HostDetector())
        self.update(CPUDetector())
        self.update(FPGADetector())
        self.update(NetworkDetector())
        self.update(MemoryDetector())
        self.update(DiskDetector())
