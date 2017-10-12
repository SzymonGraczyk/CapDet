import threading

from capdet_config import CapDetConfig
from server_config import ServerConfig
from interval_thread import IntervalThread
from logger.capdet_logger import CapDetLogger

config = CapDetConfig()
log    = CapDetLogger()

class AliveDetector(IntervalThread):
    _server_config = None

    def __init__(self, server_config):
        super(AliveDetector, self).__init__(self.check_hosts_alive)

        self._server_config = server_config

        self.set_interval(config['server']['alive_detector_interval'])

    def check_hosts_alive(self):
        hostlist = self._server_config.hostlist()
        for host in hostlist:
            host.decrease_age()

    def stop(self):
        log.info('Terminating AliveDetector thread')
        super(AliveDetector, self).stop()
