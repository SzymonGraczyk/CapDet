#!/usr/bin/python

import argparse
import signal
import sys
import zmq

from zmq.eventloop.ioloop import IOLoop, PeriodicCallback

from event_dispatcher import EventDispatcher
from generic_agent import GenericAgent
from cthread import CThread

from logger.capdet_logger import CapDetLogger
from logger.logger_stdout import LoggerStdout

from capdet_config import CapDetConfig
from detectors.capabilities import Capabilities

from host import Host
from host_state import HostState, HostAlive

from msg import MsgHostCapabilities, MsgHeartbeat, MsgSetState, MsgGetState

config = CapDetConfig()
log    = CapDetLogger()

class Agent(CThread):
    _eq     = None
    _runner = None
    _host   = None

    def __init__(self):
        super(Agent, self).__init__()

        signal.signal(signal.SIGINT,  self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        capabilities = Capabilities()

        self._host = Host()
        self._host.set_alive(HostAlive.HA_ALIVE)
        self._host.set_capabilities(capabilities)

        self._eq = EventDispatcher()
        self._eq.register_callback('-1', self.dispatch_unknown_msg_type)
        self._eq.register_callback('1',  self.send_capabilities)
        self._eq.register_callback('2',  self.dispatch1)
        self._eq.register_callback('3',  self.dispatch2)
        self._eq.register_callback('7',  self.get_state)
        self._eq.register_callback('9',  self.set_state)
        self._eq.register_callback('13', self.execute_test)

        self._runner = self.BStarRunner(self._eq.enqueue)

        self._heartbeat = PeriodicCallback(self.send_heartbeat, 5000, IOLoop.current())
       
    def run(self):
        import time
        time.sleep(2)

        self._heartbeat.start()
        log.info('Heartbeat started')

        self._runner.start()
        self.send_capabilities([])

        while self.isRunning():
            import time
            time.sleep(1)

    def stop(self):
        self._heartbeat.stop()
        self._eq.stop()
        self._runner.stop()
        super(Agent, self).stop()

    def exit_gracefully(self, signum, frame):
        log.info('Stopping server gracefully..')
        self.stop()
        log.info('Stopping server gracefully..done')

    def dispatch1(self, msg):
        log.info('d1')

    def dispatch2(self, msg):
        log.info('d2')
        self._runner._star.send(['2', 'tralalla'])

    def send_heartbeat(self):
        hostname = self._host.get_capabilities()['hostname']
        msg = MsgHeartbeat(hostname)

        self._runner._star.send(msg)
        log.msg('Heartbeat send to server')

    def send_capabilities(self, msg):
        msg = MsgHostCapabilities(self._host)

        self._runner._star.send(msg)
        log.msg('Capabilities sent to server')

    def send_state(self):
        state = self._host.get_state()
        msg = MsgSetState(state)
        
        self._runner._star.send(msg)
        log.msg('Host state sent to server')

    def get_state(self, msg):
        log.msg('Get state request received')
        self.send_state(msg)

    def set_state(self, msg):
        log.msg('Set state request received')
        state = eval(msg[0])
        self._host.set_state(state)

    def execute_test(self, msg):
        log.msg('Execute test request received')
        
        with open('/tmp/rec_script', 'w') as f:
            f.write(msg[0])

    def dispatch_unknown_msg_type(self, msg):
        log.error('Unknown message type: %s' % msg[0])

    class BStarRunner(CThread):
        _star    = None
        _enqueue = None

        def __init__(self, enqueue_func):
            super(Agent.BStarRunner, self).__init__()

            self._enqueue = enqueue_func

            server_address  = config['server']['address']
            server_in_port  = int(config['server']['in_port'])
            server_out_port = int(config['server']['out_port'])
            server_in_endpoint = 'tcp://*:%d' % (server_out_port)
            server_out_endpoint = 'tcp://%s:%d' % (server_address, server_in_port)

            self._star = GenericAgent()
            self._star.register_sender(server_out_endpoint, zmq.DEALER)
            self._star.register_receiver(server_in_endpoint, zmq.ROUTER, self.receive_callback)

        def receive_callback(self, socket, msg):
            assert self._enqueue is not None

            data = msg[1:]

            msg[1] = 'ACK'
            socket.send_multipart(msg[:2])

            self._enqueue(data)

        def run(self):
            self._star.start()

        def stop(self):
            self._star.stop()
            super(Agent.BStarRunner, self).stop()

def main():
    parser = argparse.ArgumentParser(prog='agent')
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='Verbosity level')
    args = parser.parse_args()

    log_stdout = LoggerStdout(args.verbosity)
    log.add_logger(log_stdout)

    agent = Agent()
    agent.run()

if __name__ == '__main__':
    main()
