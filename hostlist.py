import threading
import json

from host_state import HostAlive
from host import Host
from dynamic_host import DynamicHost

class HostList(list):
    _count = -1
    _lock  = None

    def __init__(self):
        super(HostList, self).__init__()

        self._count = 0
        self._lock  = threading.Lock()

    def append(self, host):
        with self._lock:
            self._count = self._count + 1
            super(HostList, self).append(host)

    def create_host(self):
        with self._lock:
            self._count = self._count + 1

            host = Host(self._count)
            super(HostList, self).append(host)

            return host

    def create_dynamic_host(self):
        with self._lock:
            self._count = self._count + 1

            host = DynamicHost(self._count)
            super(HostList, self).append(host)

            return host

    def get_by_hostname(self, name):
        with self._lock:
            for host in self:
                caps = host.get_capabilities()
                if 'hostname' in caps and \
                   caps['hostname'] == name:
                    return host

            return None

    def get_by_id(self, id):
        with self._lock:
            for host in self:
                if host.get_id() == id:
                    return host

            return None

    def get_by_state(self, state):
        with self._lock:
            hosts = HostList()
            for host in self:
                if host.get_state() == state:
                    super(HostList, hosts).append(host)

            return hosts

    def dump(self):
        with self._lock:
            for h in self:
                h.dump()

    def to_json(self):
        with self._lock:
            l = []
            for host in self:
                l.append(host.to_json())

            return l

    @staticmethod
    def from_json(data):
        hostlist = HostList()
        list_json = json.loads(data)
        for l in list_json:
            host = hostlist.create_host()
            host.update(eval(l))

        return hostlist
