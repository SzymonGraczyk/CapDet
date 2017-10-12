#!/usr/bin/python

import argparse
import random
import json

from logger.logger_stdout import LoggerStdout
from host import Host, HostAlive
from dynamic_host import DynamicHost
from hostlist import HostList
from host_fsm import HostEvent, FSMEvents
from server import Server, log, config, zmq
from server_config import ServerConfig
from msg import MsgHostList, MsgExecuteTest
from alive_detector import AliveDetector
from test.test_script import TestScript

class CapDetServer(Server):
    _config         = ServerConfig()
    _alive_detector = None

    def __init__(self, primary):
        super(CapDetServer, self).__init__(primary)

        self._alive_detector = AliveDetector(ServerConfig())

        self._eq.register_callback('-1', self.dispatch_unknown_msg_type)
        self._eq.register_callback('3',  self.get_heartbeat)
        self._eq.register_callback('4',  self.get_capabilities)
        self._eq.register_callback('5',  self.get_hostlist)
        self._eq.register_callback('9',  self.set_state)
        self._eq.register_callback('10', self.claim_host)
        self._eq.register_callback('11', self.reclaim_host)
        self._eq.register_callback('12', self.schedule_test)

    def run(self):
        super(CapDetServer, self).run()

        self._alive_detector.start()

        while self.isRunning():
#            hostlist = self._config.hostlist()
#            for host in hostlist:
#                ip = host.get_capabilities()['ip']
#                host_endpoint = 'tcp://%s:%d' % (ip, config['server']['out_port'])
#                self._runner._star.send(host_endpoint, zmq.DEALER, ['%d' % random.randint(1,2), "msg do agenta"])

            import time
            time.sleep(2)

    def stop(self):
        self._alive_detector.stop()

        super(CapDetServer, self).stop()

    def get_heartbeat(self, msg):
#        log.msg('Heartbeat received')

        hostname = msg[0]
        if not hostname:
            log.error('No hostname in host capabilities')
            return

        host = self._config.hostlist().get_by_hostname(hostname)
        if not host:
            log.warning("No host with hostname: '%s'" % hostname)
            return

        host.set_alive(HostAlive.HA_ALIVE)

    def get_capabilities(self, msg):
        log.msg('Capabilities received')

        data = eval(eval(msg[0]))
        assert type(data) is dict

        if not 'hostname' in data['capabilities']:
            log.error('No hostname in host capabilities')
            return

        hostname = data['capabilities']['hostname']
        
        host = self._config.hostlist().get_by_hostname(hostname)
        if not host:
            host = self._config.hostlist().create_dynamic_host()
            host.set_execute_test_callback(self.execute_test)
        
        host.update(data)
        host.set_alive(HostAlive.HA_ALIVE)

    def get_hostlist(self, msg):
        log.msg('Hostlist request received')

        socket = msg[-2]
        msg_id = msg[-1]
        hostlist = self._config.hostlist()
        
        msg = MsgHostList(hostlist.to_json())
        msg.insert(0, msg_id)

        socket.send_multipart(msg)
        log.msg('Hostlist sent')

    def set_state(self, msg):
        log.msg('Set state msg received')
        print msg

    def claim_host(self, msg):
        log.msg('Claim host msg received')

        hostlist = HostList()

        if len(msg) == 4:
            socket   = msg[-2]
            msg_id   = msg[-1]
            host_id  = int(msg[0])
            claim_id = msg[1]

            host = self._config.hostlist().get_by_id(host_id)
            if host:
                claim_event = HostEvent(FSMEvents.AE_CLAIM, claim_id)
                accepted = host.send_event(claim_event)
                if accepted:
                    hostlist.append(host)

        msg = MsgHostList(hostlist.to_json())
        msg.insert(0, msg_id)

        socket.send_multipart(msg)
        log.msg('Claimed hostlist sent')

    def reclaim_host(self, msg):
        log.msg('Reclaim host msg received')

        hostlist = HostList()

        if len(msg) == 4:
            socket   = msg[-2]
            msg_id   = msg[-1]
            host_id  = int(msg[0])
            claim_id = msg[1]

            host = self._config.hostlist().get_by_id(host_id)
            if host:
                reclaim_event = HostEvent(FSMEvents.AE_RECLAIM, claim_id)
                accepted = host.send_event(reclaim_event)
                if accepted:
                    hostlist.append(host)

        msg = MsgHostList(hostlist.to_json())
        msg.insert(0, msg_id)

        socket.send_multipart(msg)
        log.msg('Reclaimed hostlist sent')

    def schedule_test(self, msg):
        log.msg('Schedule test msg received')

        hostlist = HostList()

        host = None
        if len(msg) == 5:
            socket   = msg[-2]
            msg_id   = msg[-1]
            host_id  = int(msg[0])
            claim_id = msg[1]
            script   = eval(msg[2])

            test_script = TestScript()
            test_script.from_json(script)

            host = self._config.hostlist().get_by_id(host_id)
            if host:
                event = HostEvent(FSMEvents.AE_SCHEDULE_TEST, [claim_id, test_script])

                accepted = host.send_event(event)
                if accepted:
                    hostlist.append(host)

#                host_ip = host.get_capabilities()['ip']
#                host_endpoint = 'tcp://%s:%d' % (host_ip, config['server']['out_port'])

#                msg = MsgExecuteTest(script_content)
#                res = self._runner._star.send(host_endpoint, zmq.DEALER, msg)
#                if not res:
#                    log.error('Failed to schedule test')
#                    host.send_event(HostEvent(FSMEvents.AE_STOP_TESTING, claim_id))
#                else:
#                    log.msg('Script sent to host@%s' % host_ip)

        msg = MsgHostList(hostlist.to_json())
        msg.insert(0, msg_id)

        socket.send_multipart(msg)
        log.msg('Execute schedule response sent')

        # Try to start tests
        if host:
            event = HostEvent(FSMEvents.AE_START_TESTING, claim_id)
            host.send_event(event)

    def dispatch_unknown_msg_type(self, msg):
        log.error('Unknown message type: %s' % msg[0])
        log.error(msg)

    def execute_test(self, host, script):
        print host
        print script
        import time
        time.sleep(5)

#        event = HostEvent(FSMEvents.AE_STOP_TESTING)
#        host.send_event(event)

def main():
    parser = argparse.ArgumentParser(prog='CapDetServer')
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='Verbosity level')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-p', '--primary', action='store_true', default=True, help='Run server as primary')
    group.add_argument('-b', '--backup', action='store_true', default=False, help='Run server as backup')

    args = parser.parse_args()

    log_stdout = LoggerStdout(args.verbosity)
    log.add_logger(log_stdout)

    if args.primary:
        server = CapDetServer(True)
    elif args.backup:
        server = CapDetServer(False)
    else:
        print 'Invalid server option'
        return -1

    server.run()

if __name__ == '__main__':
    main()
