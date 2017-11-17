import json

from multiprocessing import Lock
from multiprocessing.managers import BaseManager

from host_state import HostAlive
from host import Host
from dynamic_host import DynamicHost

class HostList(list):
    count = -1
    lock  = None

    def __init__(self, hostlist=[]):
        super(HostList, self).__init__()

        self.count = len(hostlist)
        if len(hostlist) > 0:
            self.extend(hostlist)

#        self.lock  = Lock()

    def append(self, host):
#        with self.lock:
            self.count = self.count + 1
            super(HostList, self).append(host)

    def create_host(self):
#        with self.lock:
            self.count = self.count + 1

            host = Host(self.count)
            super(HostList, self).append(host)

            return host

    def create_dynamic_host(self):
#        with self.lock:
            self.count = self.count + 1

            host = DynamicHost(self.count)
            super(HostList, self).append(host)

            return host

    def get_by_hostname(self, name):
#        with self.lock:
            for host in self:
                hostname = host.get_capabilities('hostname')
                if hostname == name:
                    return host

            return None

    def get_by_id(self, id):
#        with self.lock:
            for host in self:
                if host.get_id() == id:
                    return host

            return None

    def get_by_state(self, state):
#        with self.lock:
            hosts = HostList()
            for host in self:
                if host.get_state() == state:
                    super(HostList, hosts).append(host)

            return hosts

    def dump(self):
#        with self.lock:
            for h in self:
                h.dump()

    def to_json(self):
#        with self.lock:
            l = []
            for host in self:
                l.append(host.to_json())

            return l

    @staticmethod
    def from_json(data):
        hostlist = HostList()
        for l in data:
#            host = hostlist.create_host()
            host = Host()

            d = eval(l)
            host.update(d)

            if 'id' in d:
                host._id = int(d['id'])
            else:
                log.warning('No host ID in data')

            hostlist.append(host)

        return hostlist
