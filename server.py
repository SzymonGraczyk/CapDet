#!/usr/bin/python

import signal
import sys
import zmq

from event_dispatcher import EventDispatcher
from binary_star_mt import BinaryStar
from cthread import CThread
from logger.capdet_logger import CapDetLogger
from capdet_config import CapDetConfig

log    = CapDetLogger()
config = CapDetConfig()

class Server(CThread):
    _runner = None
    _eq     = None

    def __init__(self, primary):
        super(Server, self).__init__()

        signal.signal(signal.SIGINT,  self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        self._eq = EventDispatcher()

        self._runner = Server.BStarRunner(primary, self._eq.enqueue)
       
    def run(self):
        self._runner.start()

    def stop(self):
        self._eq.stop()
        self._runner.stop()
        super(Server, self).stop()

    def exit_gracefully(self, signum, frame):
        log.info('Stopping server gracefully..')
        self.stop()
        log.info('Stopping server gracefully..done')

    class BStarRunner(CThread):
        _star    = None
        _enqueue = None

        def __init__(self, primary, enqueue_func):
            super(Server.BStarRunner, self).__init__()

#            server_address     = config['server']['address']
            server_address     = '*'
            server_port        = int(config['server']['in_port'])
            server_endpoint    = 'tcp://%s:%d' % (server_address, server_port)

            ha_local_address   = config['server']['ha']['local']['address']
            ha_local_port      = int(config['server']['ha']['local']['port'])
            ha_local_endpoint  = 'tcp://%s:%d' % (ha_local_address, ha_local_port)
            ha_remote_address  = config['server']['ha']['remote']['address']
            ha_remote_port     = int(config['server']['ha']['remote']['port'])
            ha_remote_endpoint = 'tcp://%s:%d' % (ha_remote_address, ha_remote_port)

            self._star = BinaryStar(primary, ha_local_endpoint, ha_remote_endpoint)
            self._star.register_voter(server_endpoint, zmq.ROUTER, self.receive_callback)

            self._enqueue = enqueue_func

        def receive_callback(self, socket, msg):
            assert self._enqueue is not True

            msg_id = msg[0]
            data   = msg[1:]
            data.append(socket)
            data.append(msg_id)

            msg[1] = 'ACK'
            socket.send_multipart(msg[:2])

            self._enqueue(data)

        def run(self):
            self._star.start()

        def stop(self):
            self._star.stop()
            super(Server.BStarRunner, self).stop()
