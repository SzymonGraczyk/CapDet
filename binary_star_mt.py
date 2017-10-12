import time
import zmq

from multiprocessing import Value

from zmq.eventloop.ioloop import IOLoop, PeriodicCallback
from zmq.eventloop.zmqstream import ZMQStream
from zmq import ZMQError

from logger.capdet_logger import CapDetLogger
from cthread import CThread

from heartbeat import Heartbeat

log = CapDetLogger()

# States we can be in at any point in time
STATE_PRIMARY = 1          # Primary, waiting for peer to connect
STATE_BACKUP  = 2          # Backup, waiting for peer to connect
STATE_ACTIVE  = 3          # Active - accepting connections
STATE_PASSIVE = 4          # Passive - not accepting connections

# Events, which start with the states our peer can be in
PEER_PRIMARY   = 1         # HA peer is pending primary
PEER_BACKUP    = 2         # HA peer is pending backup
PEER_ACTIVE    = 3         # HA peer is active
PEER_PASSIVE   = 4         # HA peer is passive
CLIENT_REQUEST = 5         # Client makes request

# We send state information every this often
# If peer doesn't respond in two heartbeats, it is 'dead'
HEARTBEAT      = 1000      # In msecs

REQUEST_TIMEOUT = 5000  # msecs
SETTLE_DELAY    = 2000  # before failing over

class FSMError(Exception):
    """Exception class for invalid state"""
    pass

class BinaryStar(object):
    def __init__(self, primary, local, remote):
        # initialize the Binary Star
        self.ctx = zmq.Context()  # Our private context
        self.loop = IOLoop.instance()  # Reactor loop
        self.state = Value('i', STATE_PRIMARY if primary else STATE_BACKUP)

        self.event           = None  # Current event
        self.peer_expiry     = 0     # When peer is considered 'dead'
        self.voter_callback  = None  # Voting socket handler
        self.master_callback = None  # Call when become master
        self.slave_callback  = None  # Call when become slave

        # Create publisher for state going to peer
#        self.statepub = self.ctx.socket(zmq.PUB)
#        self.statepub.bind(local)

        # Create subscriber for state coming from peer
        self.statesub = self.ctx.socket(zmq.SUB)
        self.statesub.setsockopt_string(zmq.SUBSCRIBE, u'')
        self.statesub.connect(remote)

        # wrap statesub in ZMQStream for event triggers
        self.statesub = ZMQStream(self.statesub, self.loop)

        # setup basic reactor events
#        self.heartbeat = PeriodicCallback(self.send_state,
#                                          HEARTBEAT, self.loop)
        self.statesub.on_recv(self.recv_state)

        self.heartbeat = Heartbeat(local, self.state)

    def update_peer_expiry(self):
        """Update peer expiry time to be 2 heartbeats from now."""
        self.peer_expiry = time.time() + 2e-3 * HEARTBEAT

    def start(self):
        self.update_peer_expiry()
#        self.heartbeat.start()

        self.heartbeat.start()

#        try:
#            self.loop.start()
#        except Exception as e:
#            log.error('Exception occurred: %s' % e)
#            raise

        self.workers = []
        for i in range(5):
            worker = self.BinaryStarWorker(self.ctx, self.voter_ready)
            worker.start()
            self.workers.append(worker)

        try:
            zmq.proxy(self.frontend, self.backend)
        except zmq.ContextTerminated as e:
            log.error("Context Terminated exception occurred as '%s'" % e)
            pass
        except zmq.ZMQError as e:
            log.error("Exception occurred as '%s'" % e)
            pass
        except:
            pass

	print 'aaxaxax'

    def stop(self):
        log.info('Stopping server...')
#        self.loop.stop()
#        self.heartbeat.stop()
        self.heartbeat.stop()
        self.heartbeat.join()
#        self.heartbeat.join()
        log.info('Stopping server...done')

    def execute_fsm(self):
        """Binary Star finite state machine (applies event to state)

        returns True if connections should be accepted, False otherwise.
        """
        accept = True

        with self.state.get_lock():
            if self.state.value == STATE_PRIMARY:
                # Primary server is waiting for peer to connect
                # Accepts CLIENT_REQUEST events in this state
                if self.event == PEER_BACKUP:
                    log.info("Connected to backup (slave), ready as master")
                    self.state.value = STATE_ACTIVE
                    if self.master_callback:
                        self.loop.add_callback(self.master_callback)
                elif self.event == PEER_ACTIVE:
                    log.info("Connected to backup (master), ready as slave")
                    self.state.value = STATE_PASSIVE
                    if self.slave_callback:
                        self.loop.add_callback(self.slave_callback)
                elif self.event == CLIENT_REQUEST:
                    if time.time() >= self.peer_expiry:
                        log.info("Request from client, ready as master")
                        self.state.value = STATE_ACTIVE
                        if self.master_callback:
                            self.loop.add_callback(self.master_callback)
                    else:
                        # don't respond to clients yet - we don't know if
                        # the backup is currently Active as a result of
                        # a successful failover
                        accept = False
            elif self.state.value == STATE_BACKUP:
                # Backup server is waiting for peer to connect
                # Rejects CLIENT_REQUEST events in this state
                if self.event == PEER_ACTIVE:
                    log.info("Connected to primary (master), ready as slave")
                    self.state.value = STATE_PASSIVE
                    if self.slave_callback:
                        self.loop.add_callback(self.slave_callback)
                elif self.event == CLIENT_REQUEST:
                    accept = False
            elif self.state.value == STATE_ACTIVE:
                # Server is active
                # Accepts CLIENT_REQUEST events in this state
                # The only way out of ACTIVE is death
                if self.event == PEER_ACTIVE:
                    # Two masters would mean split-brain
                    log.error("Fatal error - dual masters, aborting")
                    raise FSMError("Dual Masters")
            elif self.state.value == STATE_PASSIVE:
                # Server is passive
                # CLIENT_REQUEST events can trigger failover if peer looks dead
                if self.event == PEER_PRIMARY:
                    # Peer is restarting - become active, peer will go passive
                    log.info("Primary (slave) is restarting, ready as master")
                    self.state.value = STATE_ACTIVE
                elif self.event == PEER_BACKUP:
                    # Peer is restarting - become active, peer will go passive
                    log.info("Backup (slave) is restarting, ready as master")
                    self.state.value = STATE_ACTIVE
                elif self.event == PEER_PASSIVE:
                    # Two passives would mean cluster would be non-responsive
                    log.error("Fatal error - dual slaves, aborting")
                    raise FSMError("Dual slaves")
                elif self.event == CLIENT_REQUEST:
                    # Peer becomes master if timeout has passed
                    # It's the client request that triggers the failover
                    assert self.peer_expiry > 0
                    if time.time() >= self.peer_expiry:
                        # If peer is dead, switch to the active state
                        log.info("Failover successful, ready as master")
                        self.state.value = STATE_ACTIVE
                    else:
                        # If peer is alive, reject connections
                        accept = False
                # Call state change handler if necessary
                if self.state.value == STATE_ACTIVE and self.master_callback:
                    self.loop.add_callback(self.master_callback)
            return accept

    # ---------------------------------------------------------------------
    # Reactor event handlers

#    def send_state(self):
#        """Publish our state to peer"""
#        print 'aaaa'
#        self.statepub.send_string("%d" % self.state.value)

    def recv_state(self, msg):
        """Receive state from peer, execute finite state machine"""
        state = msg[0]
        if state:
            self.event = int(state)
            self.update_peer_expiry()
        self.execute_fsm()

    def voter_ready(self, socket, msg):
        """Application wants to speak to us, see if it's possible"""
        # If server can accept input now, call appl handler
        self.event = CLIENT_REQUEST
        if self.execute_fsm():
            log.msg("CLIENT REQUEST")
            self.voter_callback(socket, msg)
        else:
            # Message will be ignored
            pass

    # -------------------------------------------------------------------------
    #

    def register_voter(self, endpoint, type, handler):
        """Create socket, bind to local endpoint, and register as reader for
        voting. The socket will only be available if the Binary Star state
        machine allows it. Input on the socket will act as a "vote" in the
        Binary Star scheme.  We require exactly one voter per bstar instance.

        handler will always be called with two arguments: (socket,msg)
        where socket is the one we are creating here, and msg is the message
        that triggered the POLLIN event.
        """
        assert self.voter_callback is None

        self.frontend = self.ctx.socket(type)

        log.info("Binding to: '%s'" % endpoint)
        self.frontend.bind(endpoint)

        self.backend = self.ctx.socket(zmq.DEALER)
        self.backend.bind('inproc://backend')

#        self.voter_socket = self.frontend
        self.voter_callback = handler

#        self.stream = ZMQStream(socket, self.loop)
#        self.stream.on_recv(self.voter_ready)

    def send(self, endpoint, type, msg):
        success = False

        socket = self.ctx.socket(type)
        assert socket is not None

        log.info("Connecting to: '%s'" % endpoint)
        socket.connect(endpoint)

        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)

#        log.msg('Send msg: %s to %s' % (msg, endpoint))
        socket.send_multipart(msg)

        expect_reply = True
        while expect_reply:
            try:
                socks = dict(poller.poll(REQUEST_TIMEOUT))
            except ZMQError:
                break

            if socks.get(socket) == zmq.POLLIN:
                reply = socket.recv_string()
                if reply == 'ACK':
                    log.msg("ACK Received")
                    success = True
                    expect_reply = False
                else:
                    log.error("Malformed reply: %s" % reply)
            else:
                log.error("No ACK")
                expect_reply = False

        poller.unregister(socket)

        log.info("Disconnecting from: '%s'" % endpoint)
        socket.disconnect(endpoint)
        socket.close()

        return success

    class BinaryStarWorker(CThread):
        _context = None

        def __init__(self, context, voter_ready_callback):
            super(BinaryStar.BinaryStarWorker, self).__init__()

            self._context = context
            self._voter_callback = voter_ready_callback

        def receiver_callback(self, msg):
    	    print 'ssdasdsad'
            msg[1] = 'ACK'
            socket.send_multipart(msg)

        def run(self):
            self._worker = self._context.socket(zmq.DEALER)
            self._worker.setsockopt(zmq.SNDTIMEO, 2000)
            self._worker.setsockopt(zmq.LINGER, 0)

            self._worker.connect('inproc://backend')

#            self.stream = ZMQStream(self._worker)
#            self.stream.on_recv(self.receiver_callback)

            log.msg('Worker started')

            while self.isRunning():
                msg = self._worker.recv_multipart()
                self._voter_callback(self._worker, msg)
#                import time
#                time.sleep(2)

            self._worker.close()

        def stop(self):
            if not self._worker.closed:
                self._worker.close()

            super(BinaryStar.BinaryStarWorker, self).stop()
