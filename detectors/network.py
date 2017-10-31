from detector_interface import *

from capdet_config import CapDetConfig

config = CapDetConfig()

class NetworkDetector(DetectorInterface):
    def detect(self):
#        self['ip'] = '10.91.53.209'
#        self['ip'] = '192.168.0.132'
        self['ip'] = config['agent']['address']
