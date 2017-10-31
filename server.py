import signal
import random
import pika
import json

from host import Host, HostAlive
from dynamic_host import DynamicHost
from hostlist import HostList
from host_fsm import HostEvent, FSMEvents
from server_config import ServerConfig
from msg import MsgHostList, MsgExecuteTest
#from alive_detector import AliveDetector
from test.test_script import TestScript

from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

class Server(object):
    connection = None
    channel    = None
    msg_types  = []
    callbacks  = {}

    config     = None
    
    def __init__(self, msg_types, config):
        signal.signal(signal.SIGINT,  self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        self.msg_types = msg_types
        self.config    = config

        address = config['server']['address']
        log.info("Connecting to server: %s" % address)

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=address))
#        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='192.168.0.132'))
#        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', heartbeat_interval=10))

        self.channel = self.connection.channel(channel_number=1)

#        self.channel.exchange_delete(exchange = 'messagles')
        self.channel.exchange_declare(exchange      = 'messages',
                                      exchange_type = 'direct')

        self.queue_name = 'msg_queue'
        res = self.channel.queue_declare(queue=self.queue_name, exclusive=False)

        for msg_type in msg_types:
            self.channel.queue_bind(exchange    = 'messages',
                                    queue       = self.queue_name,
                                    routing_key = msg_type)

        self.register_callback('4',  self.msg4_callback)
        self.register_callback('5',  self.get_hostlist)
        self.register_callback('10', self.claim_host)
        self.register_callback('11', self.reclaim_host)
        self.register_callback('12', self.schedule_test)
        self.register_callback('14', self.execution_done)

    def exit_gracefully(self, signum, frame):
        log.info('Stopping server gracefully..')
        self.stop()
        log.info('Stopping server gracefully..done')

    def register_callback(self, msg_type, callback):
        assert not callback is None

        self.callbacks[msg_type] = callback

    def msg4_callback(self, ch, method, props, body):
        log.msg('Capabilities received')

        data = eval(eval(body))
        assert type(data) is dict

        if not 'hostname' in data['capabilities']:
            log.error('No hostname in host capabilities')
            return

        hostname = data['capabilities']['hostname']
        
        host = self.config.hostlist().get_by_hostname(hostname)
        if not host:
            host = self.config.create_dynamic_host()
            host.set_execute_test_callback(self.execute_test)
        
        host.update(data)
        host.set_alive(HostAlive.HA_ALIVE)
        self.config.update_host(host)

    def get_hostlist(self, ch, method, props, body):
        log.msg('Hostlist request received')

        hostlist = self.config.hostlist()
        msg = hostlist.to_json()

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(
                             correlation_id = props.correlation_id,
                             content_type = 'application/json',
                         ),
                         body=str(msg))
        
        log.msg('Hostlist sent')

    def claim_host(self, ch, method, props, body):
        log.msg('Claim host msg received')

        hostlist = HostList()

        body = json.loads(body)
        if len(body) == 2:
            host_id  = body[0]
            claim_id = body[1]

            host = self.config.claim_host(host_id, claim_id)
            if host:
                hostlist.append(host)

        msg = hostlist.to_json()

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(
                             correlation_id = props.correlation_id,
                             content_type = 'application/json',
                         ),
                         body=str(msg))

        log.msg('Claimed hostlist sent')

    def reclaim_host(self, ch, method, props, body):
        log.msg('Reclaim host msg received')

        hostlist = HostList()

        body = json.loads(body)
        if len(body) == 2:
            host_id  = body[0]
            claim_id = body[1]

            host = self.config.reclaim_host(host_id, claim_id)
            if host:
                hostlist.append(host)

        msg = hostlist.to_json()

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(
                             correlation_id = props.correlation_id,
                             content_type = 'application/json',
                         ),
                         body=str(msg))

        log.msg('Reclaimed hostlist sent')

    def schedule_test(self, ch, method, props, body):
        log.msg('Schedule test msg received')

        hostlist = HostList()

        host_id  = None
        claim_id = None
        body = json.loads(body)
        if len(body) == 3:
            host_id  = body[0]
            claim_id = body[1]
            script   = eval(body[2])

            test_script = TestScript()
            test_script.from_json(script)

            host = self.config.schedule(host_id, claim_id, script)
            if host:
                hostlist.append(host)

        msg = hostlist.to_json()

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(
                             correlation_id = props.correlation_id,
                             content_type = 'application/json',
                         ),
                         body=str(msg))

        log.msg('Execute schedule response sent')

        # Try to start tests
        if host_id:
            self.config.try_start_testing(host_id, claim_id)

    def execution_done(self, ch, method, props, body):
        log.msg('Execution done received')

        hostname = body

        self.config.execution_done(hostname)

    def execute_test(self, host, script):
        print host
        print script
        import time
        time.sleep(5)

    def dispatch(self, msg_type, ch, method, props, body):
        if not msg_type in self.callbacks:
            log.error('No callback for %s' % msg_type)
            return

        self.callbacks[msg_type](ch, method, props, body)

    def on_request(self, ch, method, props, body):
        self.dispatch(method.routing_key, ch, method, props, body)

        ch.basic_ack(delivery_tag = method.delivery_tag)

    def start(self):
        self.channel.basic_qos(prefetch_count=1)
        self.consumer_tag = self.channel.basic_consume(self.on_request, queue=self.queue_name)

        log.msg(" [x] Awaiting RPC requests (%s)" % self.msg_types)
        self.channel.start_consuming()

    def stop(self):
        for msg_type in self.msg_types:
            self.channel.queue_unbind(exchange    = 'messages',
                                      queue       = self.queue_name,
                                      routing_key = msg_type)

        self.connection.add_timeout(1, self.close_cb)
        
    def close_cb(self):
        self.channel.stop_consuming(self.consumer_tag)
        self.channel.close()
        self.connection.close()
