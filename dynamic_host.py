import Queue
import json

from host import Host
from host_fsm import HostFSM, HostEvent, FSMEvents, FSMStates
from host_state import HostAlive
from logger.capdet_logger import CapDetLogger

from test_executor import execute_test

log = CapDetLogger()

class DynamicHost(Host):
    _fsm                   = None
    _eq                    = None
    _execute_test_callback = None
    
    def __init__(self, id=-1):
        super(DynamicHost, self).__init__(id)

        self._fsm                   = HostFSM()
        self._state                 = None
        self._test_queue            = Queue.Queue()
        self._execute_test_callback = None

    def copy(self, host):
        with self._lock:
#            self._id                                = host.get_id()
            self._alive                             = host.get_alive()
            self._age                               = host.get_age()
            self._capabilities                      = host.get_capabilities()
            self._state                             = None
            self._execute_test_callback             = host._execute_test_callback
            self._fsm._state                        = host._fsm._state
            self._fsm._claim_id                     = host._fsm._claim_id
            self._fsm.set_schedule_test_callback(self._schedule_test)
            self._fsm.set_has_scheduled_tests_callback(self.has_scheduled_tests)
            self._fsm.set_execute_test_callback(self.execute_test)

    def _schedule_test(self, test_script):
        self._test_queue.put(test_script)

    def has_scheduled_tests(self):
        return not self._test_queue.empty()

    def execute_test(self):
        test_script = self._test_queue.get()

        ip = self.get_capabilities('ip')
        if not ip:
            log.error("Host does not have IP... won't execute test")
            return

        execute_test(ip, test_script)
        
    def set_execute_test_callback(self, callback):
        self._execute_test_callback = callback
        self._fsm.set_schedule_test_callback(self._schedule_test)
        self._fsm.set_has_scheduled_tests_callback(self.has_scheduled_tests)
        self._fsm.set_execute_test_callback(self.execute_test)

    def decrease_age(self):
        super(DynamicHost, self).decrease_age()

        with self._lock:
            if self._age == 0:
                self._fsm.execute(HostEvent(FSMEvents.AE_DEMISE))

    def send_event(self, event):
        with self._lock:
            return self._fsm.execute(event)

    def get_state(self):
        with self._lock:
            return self._fsm.get_state()

    def set_alive(self, alive):
        super(DynamicHost, self).set_alive(alive)

        with self._lock:
            if alive == HostAlive.HA_ALIVE:
                self._fsm.execute(HostEvent(FSMEvents.AE_WAKE))

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
                param = self._fsm._state
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
                                            self._fsm._state.name,
                                            self._alive.name,
                                            self._age,
                                            self._capabilities)
            log.msg(info)

    def to_json(self):
        with self._lock:
            d                 = {}
            d['id']           = self._id
            d['state']        = self._fsm._state.name
            d['alive']        = self._alive.name
            d['age']          = self._age
            d['capabilities'] = self._capabilities

            d_json = json.dumps(d)
            return d_json

    def update(self, data):
        with self._lock:
#            self._id           = int(data['id'])
            self._alive        = eval('HostAlive.%s' % data['alive'])
            self._age          = int(data['age'])
            self._capabilities = data['capabilities']

    def __reduce__(self):
        kwargs                              = {}
        kwargs['id']                        = self._id
        kwargs['state']                     = None
        kwargs['alive']                     = self._alive
        kwargs['age']                       = self._age
        kwargs['capabilities']              = self._capabilities
        kwargs['fsm_state']                 = self._fsm._state
        kwargs['fsm_claim_id']              = self._fsm._claim_id

        return __new_host__, (self.__class__, kwargs), None

def __new_host__(cls, kwargs):
    instance = super(DynamicHost, cls).__new__(cls)
    instance.__init__(kwargs['id'])

    instance._state                             = kwargs['state']
    instance._alive                             = kwargs['alive']
    instance._age                               = kwargs['age']
    instance._capabilities                      = kwargs['capabilities']
    instance._fsm._state                        = kwargs['fsm_state']
    instance._fsm._claim_id                     = kwargs['fsm_claim_id']

    return instance
