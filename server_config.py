from multiprocessing.managers import BaseManager, NamespaceProxy
from multiprocessing import Lock

from singleton import Singleton
from hostlist import HostList
from host_fsm import HostEvent, FSMEvents, FSMStates

from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

class ServerConfig(object):
#    __metaclass__ = Singleton

    _hostlist = None
    _lock     = None

    def __init__(self):
        self._hostlist = HostList()
        self._lock     = Lock()

    def hostlist(self):
        with self._lock:
            return self._hostlist

    def create_host(self):
        with self._lock:
            host = self._hostlist.create_host()
            return host

    def create_dynamic_host(self):
        with self._lock:
            host = self._hostlist.create_dynamic_host()
            return host

    def update_host(self, host):
        with self._lock:
            print host.get_id()
            self._hostlist.dump()
            orig_host = self._hostlist.get_by_id(host.get_id())
            if not orig_host:
                log.error('No host in the host list')
                return

            orig_host.copy(host)

    def claim_host(self, host_id, claim_id):
        with self._lock:
            host = self._hostlist.get_by_id(host_id)
            if host:
                claim_event = HostEvent(FSMEvents.AE_CLAIM, claim_id)
                accepted = host.send_event(claim_event)
                if accepted:
                    return host

            return None

    def reclaim_host(self, host_id, claim_id):
        with self._lock:
            host = self._hostlist.get_by_id(host_id)
            if host:
                reclaim_event = HostEvent(FSMEvents.AE_RECLAIM, claim_id)
                accepted = host.send_event(reclaim_event)
                if accepted:
                    return host

            return None

    def schedule(self, host_id, claim_id, test_script):
        with self._lock:
            host = self._hostlist.get_by_id(host_id)
            if host:
                schedule_event = HostEvent(FSMEvents.AE_SCHEDULE_TEST, test_script)
                accepted = host.send_event(schedule_event)
                if accepted:
                    return host

            return None

    def try_start_testing(self, host_id, claim_id):
        with self._lock:
            host = self._hostlist.get_by_id(host_id)
            if host:
                if host.get_state() == FSMStates.AF_TESTING:
                    log.msg('Host already in Start Testing state')
                    return

                event = HostEvent(FSMEvents.AE_START_TESTING, claim_id)
                host.send_event(event)

    def execution_done(self, hostname):
        with self._lock:
            host = self._hostlist.get_by_hostname(hostname)
            if host:
                event = HostEvent(FSMEvents.AE_STOP_TESTING)
                host.send_event(event)

class ServerConfigManager(BaseManager):
    pass

class ServerConfigProxy(NamespaceProxy):
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__', 'hostlist')

    def hostlist(self):
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod(self.hostlist.__name__)

ServerConfigManager.register('ServerConfig', ServerConfig)
