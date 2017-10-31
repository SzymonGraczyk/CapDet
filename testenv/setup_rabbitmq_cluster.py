#!/usr/bin/python

import subprocess

from subprocess import PIPE, Popen

USER        = 'vagrant'
PASS        = 'vagrant'
NODES       = [ "192.168.64.100", "192.168.64.101", "192.168.64.102" ]
MASTER_NODE = "192.168.64.100"
SLAVE_NODES = [ "192.168.64.101", "192.168.64.102" ]

def cmdline(command):
    process = Popen(args=command, stdout=PIPE, stderr=subprocess.STDOUT, shell=True)
    return process.communicate()[0], process.returncode

def execute(cmd):
    print "[MSG]   Execute: '%s'" % cmd

    res, rc = cmdline(cmd)
    return res, rc

def main():
    print 'Stopping rabbitmq-server...'
    for node in NODES:
        cmd = 'ssh -q %s@%s sudo service rabbitmq-server stop' % (USER, node)
        res, rc = execute(cmd)
        if rc != 0:
            print '[ERROR] Cannot stop rabbimq-server: %s' % res
    print 'Stopping rabbitmq-server...done'

    print 'Copy erlang cookie from master node to slaves...'
    for node in SLAVE_NODES:
        cmd = 'sudo scp -3 %s@%s:/var/lib/rabbitmq/.erlang.cookie %s@%s:/var/lib/rabbitmq/' % (USER, MASTER_NODE, USER, node)
        res, rc = execute(cmd)
        if rc != 0:
            print '[ERROR] Cannot copy erlang cookie: %s' % res
    print 'Copy erlang cookie from master node to slaves...done'

if __name__ == '__main__':
    main()
