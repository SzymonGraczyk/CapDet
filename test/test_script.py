import ConfigParser
import importlib
import shutil
import json
import os

from test.git_ops import GitOps
from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

class TestScript(dict):
    exec_dir = None

    def __init__(self):
        super(TestScript, self).__init__()

        self['products']       = {}
        self['configurations'] = {}
        self['hosts']          = {}
        self['installer']      = {}
        self['executor']       = {}
        self['report']         = {}

        self.exec_dir = None

    def load(self, path):
        if os.path.splitext(path)[1].lower() == '.json':
            with open(path, 'r') as f:
                d = json.load(f)
                self.update(d)
        else:
            self.parse(path)

    @staticmethod
    def is_json(data):
        try:
            json_object = json.loads(data)
        except ValueError, e:
            return False
        return True

    def parse(self, path):
        path = os.path.abspath(path)
        log.info("Parsing: '%s'" % path)

        parser = ConfigParser.ConfigParser()
        parser.read(path)

        if not parser.has_section('products'):
            log.error("Test script is missing 'products' section")
            return

        self._parse_products(parser)

        if not parser.has_section('configurations'):
            log.error("Test script is missing 'configurations' section")
            return

        self._parse_configurations(parser)

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

    def get_execution_dir(self):
        return self.exec_dir

    def _get_next_execution_dir(self, dst):
        dirs = os.listdir(dst)
        if len(dirs) == 0:
            return '1'

        sorted_dirs = sorted([fname for fname in dirs], key=lambda f: int(f.rsplit(os.path.extsep, 1)[0].rsplit(None, 1)[-1]))
        last_dir = sorted_dirs[-1]
        next_dir = str(int(last_dir) + 1)
        return next_dir

    def make_execution_dir(self):
        if not os.path.exists('/var/lib/CapDet') and \
           not os.path.isdir('/var/lib/CapDet'):
            log.error("Folder does not exist: '%s'" % '/var/lib/CapDet')
            return False

        d = self._get_next_execution_dir('/var/lib/CapDet')
        self.exec_dir = '/var/lib/CapDet/%s' % d

        try:
            os.mkdir(self.exec_dir)
        except Exception as e:
            log.error("Exception occurred making execution folder '%s': %s" % (self.exec_dir, e))
            return False

        log.info("Execution folder created: '%s'" % self.exec_dir)
        return True

    def get_products(self):
        if not self.exec_dir:
            raise NoExecutionDir()

        for product_name in self['products'].keys():
            product_url = self['products'][product_name]['url']

            if 'dst' in self['products'][product_name]:
                product_path = self['products'][product_name]['dst']
            else:
                product_path = os.path.join(self.exec_dir, product_name)

            if os.path.exists(product_path):
                log.error('Cannot create a folder for a product. Already exists.')
                return

            log.msg('Create product folder: %s' % product_path)
            try:
                os.mkdir(product_path)
            except Exception as e:
                log.error('Cannot create a folder for a product. Exception occurred: %s.' % e)
                return

            log.msg("Cloning git repo '%s' to '%s'..." % (product_url, product_path))
            GitOps.clone(product_url, product_path)
            log.msg("Cloning git repo '%s' to '%s'... done" % (product_url, product_path))

    def remove_products(self):
        if not self.exec_dir:
            raise NoExecutionDir()

        for product_name in self['products'].keys():
            product_url = self['products'][product_name]['url']

            if 'dst' in self['products'][product_name]:
                product_path = self['products'][product_name]['dst']
            else:
                product_path = os.path.join(self.exec_dir, product_name)

            if not os.path.exists(product_path):
                log.warning('Product path does not exist: %s' % product_path)
                continue

            log.msg("Removing product path: '%s'..." % product_path)

            try:
                shutil.rmtree(product_path)
            except Exception as e:
                log.error("Error occcurred while removing product '%s': %s" % (product_path, e))
                continue

            log.msg("Removing product path: '%s'... done" % product_path)

    def install_products(self):
        if not self.exec_dir:
            raise NoExecutionDir()

        if not 'path' in self['installer']:
            log.error("No path defined for installer")
            return False

        installer_path = self['installer']['path']
        if not os.path.exists(installer_path):
            log.error("Installer path does not exist: '%s'" % installer_path)
            return False

#        importlib.import_module(installer_path)
        
#        import sys
#        print sys.modules[__name__]

        print os.getcwd()

        name = installer_path.replace('.py', '')
        name = name.replace('/', '.')
        print name
#        print __import__(name)
#        cls = getattr(importlib.import_module('samples.sample_installer'), 'SampleInstaller')
#        print cls

        return True

    def to_json(self):
        return json.dumps(self)

    def from_json(self, data):
        self.update(data)

    def _parse_products(self, parser):
        if parser.has_option('products', 'url'):
            self['products']['url'] = parser.get('products', 'url')
        if parser.has_option('products', 'local_path'):
            self['products']['local_path'] = parser.get('products', 'url')

    def _parse_configurations(self, parser):
        if parser.has_option('configurations', 'file'):
            self['configurations']['file'] = parser.get('configurations', 'file')

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

class NoExecutionDir(Exception):
    pass
