import zmq

from zmq.eventloop.ioloop import IOLoop, PeriodicCallback
from multiprocessing import Process

from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

HEARTBEAT = 1000

class Heartbeat(Process):
    ctx      = None
    local_ep = None
    state    = None

    def __init__(self, local_ep, state):
        Process.__init__(self)

        self.state    = state

        self.ctx      = zmq.Context()
        self.local_ep = local_ep

        log.info('Heartbeat service binding to: %s' % self.local_ep)
        self.statepub = self.ctx.socket(zmq.PUB)
        self.statepub.bind(local_ep)

        self.loop = IOLoop.instance()
        self.heartbeat = PeriodicCallback(self.send_state, HEARTBEAT, self.loop)

    def run(self):
        self.heartbeat.start()

        try:
            self.loop.start()
        except Exception as e:
            log.error('Exception occurred: %s' % e)

        print 'adasdsad'
        self.heartbeat.stop()

    def send_state(self):
        print self.state.value
        self.statepub.send_string("%d" % self.state.value)

    def stop(self):
        self.heartbeat.stop()
        self.loop.stop()
