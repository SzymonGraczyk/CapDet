import threading
import json
import os

from host_fsm import HostFSM, FSMStates
from host_state import HostAlive
from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

class HostFilter(dict):
    def __init__(self, param, op, value):
        super(HostFilter, self).__init__()

        self['param'] = param
        self['op']    = op
        self['value'] = value

        if not op in [ '==', '!=', '>', '<', '>=', '<=' ]:
            raise InvalidOperator("Operator not supported: %s" % op)

class Host(object):
    _id           = -1
    _alive        = HostAlive.HA_UNKNOWN
    _age          = -1
    _capabilities = {}
    _lock         = None
    _state        = FSMStates.AF_UNKNOWN
    
    def __init__(self, id=-1):
        self._id   = id
        self._lock = threading.Lock()
        self._age  = 5

        self._capabilities['hostname'] = ''
            
    def get_id(self):
        return self._id

    def get_age(self):
        with self._lock:
            return self._age

    def decrease_age(self):
        with self._lock:
            if self._age > 0:
                self._age = self._age - 1
                if self._age == 0:
                    self._alive = HostAlive.HA_DOWN

    def set_capabilities(self, capabilities):
        with self._lock:
            self._capabilities = capabilities

    def get_capabilities(self):
        with self._lock:
            return self._capabilities

    def get_state(self):
        with self._lock:
            return self._state

    def set_alive(self, alive):
        with self._lock:
            self._alive = alive
            if alive == HostAlive.HA_ALIVE:
                self._age = 5

    def get_alive(self):
        with self._lock:
            return self._alive

    def set_capabilities(self, capabilities):
        with self._lock:
            self._capabilities = capabilities

    def get_capabilities(self):
        with self._lock:
            return self._capabilities

    def has_param(self, param_name):
        with self._lock:
            return param_name in self._capabailities

    def match(self, filters):
        if not type(filters) is list:
            filters = [filters]

        for f in filters:
            res = self._match(f)
            if not res:
                return False

        return True

    def _match(self, host_filter):
        with self._lock:
            if host_filter['param'] == 'alive':
                param = self._alive
                op    = host_filter['op']
                value = HostAlive[host_filter['value']]

                if not op in [ '==', '!=' ]:
                    log.error("Operator not supported with enums: %s" % op)
                    raise InvalidOperator("Operator not supported with enums: %s" % op)

                comp = "%s %s %s" % (param, op, value)

                return eval(comp)
            elif host_filter['param'] == 'state':
                param = self._state
                op    = host_filter['op']

                if not host_filter['value'] in FSMStates.__members__:
                    log.error('Invalid host state: %s' % host_filter['value'])
                    raise Exception('Invalid host state: %s' % host_filter['value'])

                value = FSMStates[host_filter['value']]

                if not op in [ '==', '!=' ]:
                    log.error("Operator not supported with enums: %s" % op)
                    raise InvalidOperator("Operator not supported with enums: %s" % op)

                comp = "%s %s %s" % (param, op, value)

                return eval(comp)
            elif not host_filter['param'] in self._capabilities:
                raise Exception("Capabilities does not contain param: '%s'" % host_filter['param'])
            else:
                param = self._capabilities[host_filter['param']]
                value = host_filter['value']

            op = host_filter['op']

            try:
                value = int(value)
                comp = "%s %s %d" % (param, op, value)
            except ValueError:
                comp = "'%s' %s '%s'" % (str(param), op, str(value))

            return eval(comp)

    def dump(self):
        with self._lock:
            info = ("Host: %d\n"
                    " Hostname: %s\n"
                    " State: %s\n"
                    " Alive: %s\n"
                    " Age:   %d\n"
                    " Capabilities: %s") % (self._id,
                                            self._capabilities['hostname'],
                                            self._state.name,
                                            self._alive.name,
                                            self._age,
                                            self._capabilities)
            log.msg(info)

    def to_json(self):
        with self._lock:
            d                 = {}
            d['id']           = self._id
            d['state']        = self._state.name
            d['alive']        = self._alive.name
            d['age']          = self._age
            d['capabilities'] = self._capabilities

            d_json = json.dumps(d)
            return d_json

    def update(self, data):
        with self._lock:
            self._state        = eval('FSMStates.%s' % data['state'])
            self._alive        = eval('HostAlive.%s' % data['alive'])
            self._age          = int(data['age'])
            self._capabilities = data['capabilities']

class InvalidOperator(Exception):
    pass
