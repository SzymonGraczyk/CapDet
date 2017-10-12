#!/usr/bin/python

import time

import zmq
from zmq import ZMQError
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback
from zmq.eventloop.zmqstream import ZMQStream

from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

REQUEST_TIMEOUT = 5000  # msecs
SETTLE_DELAY    = 2000  # before failing over

class GenericAgent(object):
    def __init__(self):
        # initialize the Binary Star
        self.ctx = zmq.Context()  # Our private context
        self.loop = IOLoop.current()  # Reactor loop

        self.event = None  # Current event
        self.peer_expiry = 0  # When peer is considered 'dead'
        self.receiver_callback = None  # Voting socket handler

    def start(self):
        try:
            res = self.loop.start()
            return res
        except Exception as e:
            log.error('Exception occurred: %s' % e)
            raise

    def stop(self):
        log.msg('Stopping server...')
        self.loop.stop()
        log.msg('Stopping server...done')

    def receiver_ready(self, msg):
        self.receiver_callback(self.receiver_socket, msg)

    def register_receiver(self, endpoint, type, handler):
        """Create socket, bind to local endpoint, and register as reader for
        voting. The socket will only be available if the Binary Star state
        machine allows it. Input on the socket will act as a "vote" in the
        Binary Star scheme.  We require exactly one voter per bstar instance.

        handler will always be called with two arguments: (socket,msg)
        where socket is the one we are creating here, and msg is the message
        that triggered the POLLIN event.
        """
        assert self.receiver_callback is None

        socket = self.ctx.socket(type)

        log.info("Binding to: '%s'" % endpoint)
        socket.bind(endpoint)
        self.receiver_socket = socket
        self.receiver_callback = handler

        self.stream = ZMQStream(socket, self.loop)
        self.stream.on_recv(self.receiver_ready)

    def register_sender(self, endpoint, type):
        """Create socket, bind to local endpoint, and register as reader for
        voting. The socket will only be available if the Binary Star state
        machine allows it. Input on the socket will act as a "vote" in the
        Binary Star scheme.  We require exactly one voter per bstar instance.

        handler will always be called with two arguments: (socket,msg)
        where socket is the one we are creating here, and msg is the message
        that triggered the POLLIN event.
        """
        socket = self.ctx.socket(type)

        log.info("Connecting to: '%s'" % endpoint)
        socket.connect(endpoint)
        self.sender_socket = socket

        self.poller = zmq.Poller()
        self.poller.register(socket, zmq.POLLIN)

    def send(self, msg):
        self.sender_socket.send_multipart(msg)

        expect_reply = True
        while expect_reply:
            try:
                socks = dict(self.poller.poll(REQUEST_TIMEOUT))
            except ZMQError:
                break

            if socks.get(self.sender_socket) == zmq.POLLIN:
                reply = self.sender_socket.recv_string()
                if reply == 'ACK':
                    log.msg("Server replied OK (%s)" % reply)
                    expect_reply = False
                else:
                    log.error("Malformed reply from server: %s" % reply)
            else:
                log.warning("No response from server, failing over")
                return
                time.sleep(SETTLE_DELAY / 1000)
                self.poller.unregister(self.socket)
                self.sender_socket.close()
                server_nbr = (server_nbr + 1) % 2
                log.info("Connecting to server at %s.." % server[server_nbr])
                self.sender_socket = self.ctx.socket(zmq.REQ)
                self.poller.register(self.sender_socket, zmq.POLLIN)
                # reconnect and resend request
                self.sender_socket.connect(server[server_nbr])
#                self.socket.send_string("%s" % sequence)

    def receive(self):
        reply = None

        try:
            socks = dict(self.poller.poll(REQUEST_TIMEOUT))
        except ZMQError:
            return reply

        if socks.get(self.sender_socket) == zmq.POLLIN:
            log.msg('Reply from server received')
            reply = self.sender_socket.recv_multipart()
        else:
            log.warning('No reply')

        return reply
