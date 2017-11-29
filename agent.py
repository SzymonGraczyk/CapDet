#!/usr/bin/python

import argparse
import signal
import pika
import uuid
import os

from event_dispatcher import EventDispatcher
from cthread import CThread

from logger.capdet_logger import CapDetLogger
from logger.logger_stdout import LoggerStdout
from logger.logger_file import LoggerFile

from capdet_config import CapDetConfig
from detectors.capabilities import Capabilities

from host import Host
from host_state import HostState, HostAlive

from msg import MsgHostCapabilities, MsgHeartbeat, MsgSetState, MsgGetState, MsgExecuteDone

from test.test_script import TestScript

config = CapDetConfig()
log    = CapDetLogger()

class Agent(CThread):
    host = None

    connections = []

    def __init__(self):
        super(Agent, self).__init__()

        signal.signal(signal.SIGINT,  self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        capabilities = Capabilities()

        self.host = Host()
        self.host.set_alive(HostAlive.HA_ALIVE)
        self.host.set_capabilities(capabilities)

        self._init_server_connection()
        self._init_agent_connection()

    def _init_server_connection(self):
        address = config['server']['address']
        log.info("Connecting to server: %s" % address)

        server_conn = {}

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=address))
        server_conn['connection'] = connection

        channel = connection.channel()

        channel.exchange_declare(exchange      = 'messages',
                                 exchange_type = 'direct')

        result = channel.queue_declare(exclusive=False)
        server_conn['queue'] = result.method.queue

        channel.basic_consume(self.on_response1,
                              no_ack=True,
                              queue=server_conn['queue'])

        server_conn['channel'] = channel

        self.connections.append(server_conn)

    def _init_agent_connection(self):
        address = config['agent']['address']
        log.info("Creating agent connection: %s" % address)

        agent_conn = {}

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=address))
        agent_conn['connection'] = connection

        channel = connection.channel()

        channel.exchange_declare(exchange      = 'tests',
                                 exchange_type = 'direct')
        
        agent_conn['queue'] = 'tests_queue'
        result = channel.queue_declare(queue     = agent_conn['queue'],
                                       exclusive = False)

        channel.queue_bind(exchange    = 'tests',
                           queue       = agent_conn['queue'],
                           routing_key = '1')

        channel.basic_qos(prefetch_count=1)
        agent_conn['consumer_tag'] = channel.basic_consume(self.on_response2,
#                                                           no_ack=False,
                                                           queue=agent_conn['queue'])

        agent_conn['channel'] = channel

        self.connections.append(agent_conn)

    def exit_gracefully(self, signum, frame):
        log.info('Stopping agent gracefully..')
        self.stop()
        log.info('Stopping agent gracefully..done')

    def on_response1(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def on_response2(self, ch, method, props, body):
        ch.basic_ack(delivery_tag = method.delivery_tag)
        log.msg('Received test script')

        body = eval(body)
        test_script = TestScript()
        test_script.from_json(body)

        res = test_script.make_execution_dir()
        if res:
            get_products_log_path = os.path.join(test_script.get_execution_dir(), 'get_products.log')
            get_products_log = LoggerFile(get_products_log_path, 2)
            log.add_logger(get_products_log)

            test_script.get_products()

            log.remove_logger(get_products_log)

            install_log_path = os.path.join(test_script.get_execution_dir(), 'install.log')
            install_log = LoggerFile(install_log_path, 2)
            log.add_logger(install_log)

            test_script.install_products()

            log.remove_logger(install_log)

        import time
        time.sleep(10)

        remove_products_log_path = os.path.join(test_script.get_execution_dir(), 'remove_products.log')
        remove_products_log = LoggerFile(remove_products_log_path, 2)
        log.add_logger(remove_products_log)

        test_script.remove_products()

        log.remove_logger(remove_products_log)

        hostname = self.host.get_capabilities('hostname')
        if not hostname:
            log.error("Unknown hostname... shouldn't happen")
            return

        log.msg('Send execution done message...')
        msg = MsgExecuteDone(hostname)
        self.send(0, msg)
        log.msg('Send execution done message...done')

    def send(self, conn, msg):
        key  = str(msg[0])
        data = msg[1]

        channel = self.connections[conn]['channel']
        queue   = self.connections[conn]['queue']

        self.response = None
        self.corr_id = str(uuid.uuid4())
        channel.basic_publish(exchange='messages',
                              routing_key=key,
                              properties=pika.BasicProperties(
                                  reply_to = queue,
                                  correlation_id = self.corr_id,
                                  content_type = 'application/json',
                              ),
                              body=data)

    def receive(self, timeout=10):
        ticks = 0
        while self.response is None and \
              ticks < timeout:
            self.connection.process_data_events(1)
            ticks = ticks + 1

        if ticks == timeout:
            return None

        return int(self.response)

    def call(self, n):
        msg = MsgHeartbeat()
        return self.send(0, msg)

    def send_capabilities(self):
        msg = MsgHostCapabilities(self.host)

        self.send(0, msg)
        log.msg('Capabilities sent to server')

    def run(self):
        self.send_capabilities()

        channel = self.connections[1]['channel']
        channel.start_consuming()

    def stop(self):
        self.connections[0].add_timeout(1, self.close_server_conn_cb)
        self.connections[1].add_timeout(1, self.close_agent_conn_cb)

        super(Agent, self).stop()

    def close_server_conn_cb(self):
        channel = self.connections[0]['channel']
        channel.close()

        self.connections[0].close()

    def close_agent_conn_cb(self):
        channel = self.connections[1]['channel']
        channel.stop_consuming(self.connections[1]['consumer_tag'])
        channel.close()

        self.connections[1].close()
        
def main():
    parser = argparse.ArgumentParser(prog='agent')
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='Verbosity level')
    args = parser.parse_args()

    log_stdout = LoggerStdout(args.verbosity)
    log.add_logger(log_stdout)

    log_file = LoggerFile('/var/log/CapDet/agent.log', args.verbosity)
    log.add_logger(log_file)

    agent = Agent()
    agent.run()

if __name__ == '__main__':
    main()
