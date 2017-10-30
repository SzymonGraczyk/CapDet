#!/usr/bin/python

import argparse
import random
import socket
import uuid
import pika
import json
import sys
import os

from cthread import CThread

from host import Host, HostFilter, HostAlive
from dynamic_host import DynamicHost
from hostlist import HostList
from msg import MsgACK, MsgGetHostList, MsgClaimHost, MsgReclaimHost, MsgScheduleTest
from drivers.operators_factory import OperatorsFactory
from test.test_script import TestScript
from capdet_config import CapDetConfig

from logger.capdet_logger import CapDetLogger
from logger.logger_stdout import LoggerStdout
from logger.logger_file import LoggerFile

log    = CapDetLogger()
config = CapDetConfig()

class Cli(CThread):
    response = None

    def __init__(self):
        super(Cli, self).__init__()

        address = config['server']['address']
        port    = config['server']['in_port']
        
        os = OperatorsFactory()

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange      = 'messages',
                                      exchange_type = 'direct')

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response,
                                   no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def run(self):
        while self.isRunning():
            import time
            time.sleep(1)

    def stop(self):
        self.connection.close()
        super(Cli, self).stop()

    def send(self, msg):
        key  = str(msg[0])
        if len(msg) > 1:
            data = json.dumps(msg[1:])
        else:
            data = ''

        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='messages',
                                   routing_key=key,
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         content_type = 'application/json',
                                         delivery_mode = 2,
                                         ),
                                   body=data)

    def receive(self, timeout=10):
        ticks = 0
        while self.response is None and \
              ticks < timeout:
            self.connection.process_data_events(1)
            ticks = ticks + 1

        if ticks == timeout:
            log.warning('Receive timed out')
            return None

        return self.response

    def get_hosts(self):
        msg = MsgGetHostList()
        self.send(msg)

        log.msg('get_hosts send to server')

        msg = self.receive()
        if not msg:
            return HostList()

#        msg_id = msg[0]
#        if msg_id != '6':
#            log.error('Invalid reply from server')
#            return

        data = eval(msg)
        hostlist = HostList.from_json(data)

        return hostlist

    def claim_host(self, host_id, claim_id):
        assert host_id > 0

        msg = MsgClaimHost(host_id, claim_id)
        self.send(msg)

        log.msg("claim_host (id: %d) send to server" % host_id)

        msg = self.receive()
        if not msg:
            return HostList()

#        msg_id = msg[0]
#        if msg_id != '6':
#            log.error('Invalid reply from server')
#            return

        data = eval(msg)
        hostlist = HostList.from_json(data)

        return hostlist

    def reclaim_host(self, host_id, claim_id):
        assert host_id > 0

        msg = MsgReclaimHost(host_id, claim_id)
        self.send(msg)

        log.msg("reclaim_host (id: %d) send to server" % host_id)

        msg = self.receive()
        if not msg:
            return HostList()

#        msg_id = msg[0]
#        if msg_id != '6':
#            log.error('Invalid reply from server')
#            return

        data = eval(msg)
        hostlist = HostList.from_json(data)

        return hostlist

    def schedule_test(self, host_id, claim_id, script):
        assert host_id > 0

        msg = MsgScheduleTest(host_id, claim_id, script)
        self.send(msg)

        log.msg("schedule_test (id: %d) send to server" % host_id)

        msg = self.receive()
        if not msg:
            return HostList()

#        msg_id = msg[0]
#        if msg_id != '6':
#            log.error('Invalid reply from server')
#            return

        data = eval(msg)
        hostlist = HostList.from_json(data)

        return hostlist

    class CliRunner(CThread):
        _star = None

        def __init__(self):
            super(Cli.CliRunner, self).__init__()

            server_address  = config['server']['address']
            server_in_port  = int(config['server']['in_port'])
            server_out_endpoint = 'tcp://%s:%d' % (server_address, server_in_port)

            self._star = GenericAgent()
            self._star.register_sender(server_out_endpoint, zmq.DEALER)

        def run(self):
            self._star.start()

        def stop(self):
            self._star.stop()
            super(Cli.CliRunner, self).stop()

def get_filters(filters_str):
    if not filters_str:
        return []
    
    hfilters = []
    filters = filters_str.split(',')
    for f in filters:
        f = f.strip()

        parts = f.split(' ')
        parts = filter(None, parts)
        if len(parts) != 3:
            log.error("Illegally formed filter: '%s'" % f)
            raise Exception("Illegally formed filter: '%s'" % f)

        hfilters.append(HostFilter(parts[0], parts[1], parts[2]))
   
    return hfilters

def action_list_hosts(args):
    client = Cli()

    filters = get_filters(args.filters)

    hostlist = client.get_hosts()
    client.stop()

    for h in hostlist:
        if args.alive and \
           h.get_alive() != HostAlive.HA_ALIVE:
            continue

        try:
            matched = h.match(filters)
        except:
            continue

        if not matched:
            continue

        caps = h.get_capabilities()
        if args.details:
            print "Host:          %d" % h.get_id()
            print " Hostname:     %s" % caps['hostname']
            print " State:        %s" % h.get_state().name
            print " Alive:        %s" % h.get_alive().name
            print " Age:          %d" % h.get_age()
            print " Capabilities: %s" % caps
        elif args.short:
            print "Host:          %d" % h.get_id()
            print " Hostname:     %s" % caps['hostname']
            print " State:        %s" % h.get_state().name
            print " Alive:        %s" % h.get_alive().name

def action_claim_host(args):
    host_id = args.id
    if not host_id or \
       host_id <= 0:
        log.error('Invalid host id to claim: %d' % host_id)
        return

    claim_id = args.claim_id
    if not claim_id:
        log.error('Invalid claim id: %d' % claim_id)
        return

    client = Cli()
    hostlist = client.claim_host(host_id, claim_id)
    client.stop()

    if len(hostlist) <= 0:
        log.error("Claim host (id: %d) failed" % host_id)
        return

    for h in hostlist:
        caps = h.get_capabilities()
        if args.details:
            print "Host:          %d" % h.get_id()
            print " Hostname:     %s" % caps['hostname']
            print " State:        %s" % h.get_state().name
            print " Alive:        %s" % h.get_alive().name
            print " Age:          %d" % h.get_age()
            print " Capabilities: %s" % caps
        else:
            print "Host:          %d" % h.get_id()
            print " Hostname:     %s" % caps['hostname']
            print " State:        %s" % h.get_state().name
            print " Alive:        %s" % h.get_alive().name

def action_reclaim_host(args):
    host_id = args.id
    if not host_id or \
       host_id <= 0:
        log.error('Invalid host id to reclaim: %d' % host_id)
        return

    claim_id = args.claim_id
    if not claim_id:
        log.error('Invalid claim id: %d' % claim_id)
        return

    client = Cli()
    hostlist = client.reclaim_host(host_id, claim_id)
    client.stop()

    if len(hostlist) <= 0:
        log.error("Reclaim host (id: %d) failed" % host_id)
        return

    for h in hostlist:
        caps = h.get_capabilities()
        if args.details:
            print "Host:          %d" % h.get_id()
            print " Hostname:     %s" % caps['hostname']
            print " State:        %s" % h.get_state().name
            print " Alive:        %s" % h.get_alive().name
            print " Age:          %d" % h.get_age()
            print " Capabilities: %s" % caps
        else:
            print "Host:          %d" % h.get_id()
            print " Hostname:     %s" % caps['hostname']
            print " State:        %s" % h.get_state().name
            print " Alive:        %s" % h.get_alive().name

def action_schedule(args):
    host_id = args.id
    if not host_id or \
       host_id <= 0:
        log.error('Invalid host id to schedule test: %d' % host_id)
        return

    claim_id = args.claim_id
    if not claim_id:
        log.error('Invalid claim id: %d' % claim_id)
        return

    script = args.script
    if not script or \
       not os.path.exists(script) or \
       not os.path.isfile(script):
        log.error('Invalid script path: %s' % script)
        return

    test_script = TestScript()
    test_script.load(script)

    client = Cli()
    hostlist = client.schedule_test(host_id, claim_id, test_script)
    client.stop()

    if len(hostlist) <= 0:
        log.error("Schedule failed (id: %d) failed" % host_id)
        return

    for h in hostlist:
        caps = h.get_capabilities()
        if args.details:
            print "Host:          %d" % h.get_id()
            print " Hostname:     %s" % caps['hostname']
            print " State:        %s" % h.get_state().name
            print " Alive:        %s" % h.get_alive().name
            print " Age:          %d" % h.get_age()
            print " Capabilities: %s" % caps
        else:
            print "Host:          %d" % h.get_id()
            print " Hostname:     %s" % caps['hostname']
            print " State:        %s" % h.get_state().name
            print " Alive:        %s" % h.get_alive().name

def main():
    parser = argparse.ArgumentParser(prog='cli')
    subparsers =parser.add_subparsers(title='Actions')

    parser_list_hosts = subparsers.add_parser('list-hosts', help='List hosts')
    parser_list_hosts.add_argument('-v', '--verbosity', action='count', default=0, help='Verbosity level')
    parser_list_hosts.add_argument('-a', '--alive', action='store_true', default=False, help='List alive hosts')
    parser_list_hosts.add_argument('-f', '--filters', type=str, help='List hosts matching filters')
    parser_list_hosts.set_defaults(func=action_list_hosts)

    group = parser_list_hosts.add_mutually_exclusive_group()
    group.add_argument('-s', '--short', action='store_true', default=True, help='List short descriptions')
    group.add_argument('-d', '--details', action='store_true', default=False, help='List detailed descriptions')
    
    parser_claim_host = subparsers.add_parser('claim-host', help='Claim host')
    parser_claim_host.add_argument('-v', '--verbosity', action='count', default=0, help='Verbosity level')
    parser_claim_host.add_argument('-i', '--id', type=int, required=True, help='Host ID')
    parser_claim_host.add_argument('-c', '--claim-id', type=str, required=True, help='Claim ID')
    parser_claim_host.add_argument('-d', '--details', action='store_true', default=False, help='List detailed descriptions')
    parser_claim_host.set_defaults(func=action_claim_host)

    parser_reclaim_host = subparsers.add_parser('reclaim-host', help='Reclaim host')
    parser_reclaim_host.add_argument('-v', '--verbosity', action='count', default=0, help='Verbosity level')
    parser_reclaim_host.add_argument('-i', '--id', type=int, required=True, help='Host ID')
    parser_reclaim_host.add_argument('-c', '--claim-id', type=str, required=True, help='Claim ID')
    parser_reclaim_host.add_argument('-d', '--details', action='store_true', default=False, help='List detailed descriptions')
    parser_reclaim_host.set_defaults(func=action_reclaim_host)

    parser_schedule = subparsers.add_parser('schedule', help='Schedule test')
    parser_schedule.add_argument('-v', '--verbosity', action='count', default=0, help='Verbosity level')
    parser_schedule.add_argument('-i', '--id', type=int, required=True, help='Host ID')
    parser_schedule.add_argument('-c', '--claim-id', type=str, required=True, help='Claim ID')
    parser_schedule.add_argument('-s', '--script', type=str, required=True, help='Script to schedule')
    parser_schedule.add_argument('-d', '--details', action='store_true', default=False, help='List detailed descriptions')
    parser_schedule.set_defaults(func=action_schedule)

    args = parser.parse_args()

    log_stdout = LoggerStdout(args.verbosity)
    log.add_logger(log_stdout)

    log_file = LoggerFile('/var/log/CapDet/cli.log', args.verbosity)
    log.add_logger(log_file)

    args.func(args)
    
if __name__ == '__main__':
    main()
