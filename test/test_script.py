import ConfigParser
import json
import os

from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

class TestScript(dict):
    def __init__(self):
        super(TestScript, self).__init__()

        self['product']       = {}
        self['configuration'] = {}
        self['hosts']         = {}
        self['installer']     = {}
        self['executor']      = {}
        self['report']        = {}

    def parse(self, path):
        path = os.path.abspath(path)
        log.info("Parsing: '%s'" % path)

        parser = ConfigParser.ConfigParser()
        parser.read(path)

        if not parser.has_section('product'):
            log.error("Test script is missing 'product' section")
            return

        self._parse_product(parser)

        if not parser.has_section('configuration'):
            log.error("Test script is missing 'configuration' section")
            return

        self._parse_configuration(parser)

        if not parser.has_section('hosts'):
            log.error("Test script is missing 'hosts' section")
            return

        self._parse_hosts(parser)

        if not parser.has_section('installer'):
            log.error("Test script is missing 'installer' section")
            return

        self._parse_installer(parser)

        if not parser.has_section('executor'):
            log.error("Test script is missing 'executor' section")
            return

        self._parse_executor(parser)

        if not parser.has_section('report'):
            log.error("Test script is missing 'executor' section")
            return

        self._parse_report(parser)

    def to_json(self):
        return json.dumps(self)

    def from_json(self, data):
        self.update(data)

    def _parse_product(self, parser):
        if parser.has_option('product', 'url'):
            self['product']['url'] = parser.get('product', 'url')

    def _parse_configuration(self, parser):
        if parser.has_option('configuration', 'file'):
            self['configuration']['file'] = parser.get('configuration', 'file')

    def _parse_hosts(self, parser):
        if parser.has_option('hosts', 'filter'):
            self['hosts']['filter'] = parser.get('hosts', 'filter')
        if parser.has_option('hosts', 'count'):
            self['hosts']['count'] = parser.get('hosts', 'count')

    def _parse_installer(self, parser):
        if parser.has_option('installer', 'file'):
            self['installer']['file'] = parser.get('installer', 'file')

    def _parse_executor(self, parser):
        if parser.has_option('executor', 'file'):
            self['executor']['file'] = parser.get('executor', 'file')

    def _parse_report(self, parser):
        if parser.has_option('report', 'file'):
            self['report']['file'] = parser.get('report', 'file')
