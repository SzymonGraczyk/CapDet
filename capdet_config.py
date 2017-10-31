import ConfigParser
import sys
import os

from singleton import Singleton
from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

class CapDetConfig(dict):
    __metaclass__ = Singleton

    def __init__(self):
        super(self.__class__, self).__init__()

        self['server'] = {}
        self['server']['address']                 = ''
        self['server']['in_port']                 = -1
        self['server']['out_port']                = -1
        self['server']['alive_detector_interval'] = -1

        self['server']['ha']                      = {}
        self['server']['ha']['local']             = {}
        self['server']['ha']['local']['address']  = ''
        self['server']['ha']['local']['port']     = ''
        self['server']['ha']['remote']            = {}
        self['server']['ha']['remote']['address'] = ''
        self['server']['ha']['remote']['port']    = ''

        self['client'] = {}
        self['client']['heartbeat']               = False
        self['client']['heartbeat_interval']      = -1

        cfg_path = '/etc/capdet/capdet.cfg'
        if not os.path.exists(cfg_path):
            log.error("Config does not exist: '%s'" % cfg_path)
            sys.exit(-1)
        else:
            log.info("Loading config from: '%s'" % cfg_path)
            parser = ConfigParser.ConfigParser()
            parser.read(cfg_path)

            if parser.has_option('server', 'address'):
                self['server']['address'] = parser.get('server', 'address')
            if parser.has_option('server', 'in_port'):
                self['server']['in_port'] = int(parser.get('server', 'in_port'))
            if parser.has_option('server', 'out_port'):
                self['server']['out_port'] = int(parser.get('server', 'out_port'))
            if parser.has_option('server', 'alive_detector_interval'):
                self['server']['alive_detector_interval'] = int(parser.get('server', 'alive_detector_interval', 60))

            if parser.has_option('server_ha', 'local_address'):
                self['server']['ha']['local']['address'] = parser.get('server_ha', 'local_address')
            if parser.has_option('server_ha', 'local_port'):
                self['server']['ha']['local']['port'] = parser.get('server_ha', 'local_port')
            if parser.has_option('server_ha', 'remote_address'):
                self['server']['ha']['remote']['address'] = parser.get('server_ha', 'remote_address')
            if parser.has_option('server_ha', 'remote_port'):
                self['server']['ha']['remote']['port'] = parser.get('server_ha', 'remote_port')

            if parser.has_option('client', 'heartbeat'):
                self['client']['heartbeat'] = bool(parser.get('client', 'heartbeat', False))
            if parser.has_option('client', 'heartbeat_interval'):
                self['client']['heartbeat_interval'] = int(parser.get('client', 'heartbeat_interval', 60))
