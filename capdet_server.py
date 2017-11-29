#!/usr/bin/env python

import argparse

from multiprocessing import Process

from server_config import ServerConfig, ServerConfigManager
from server import Server

from logger.capdet_logger import CapDetLogger
from logger.logger_stdout import LoggerStdout
from logger.logger_file import LoggerFile

log = CapDetLogger()


def _pickle_method(method):
    func_name = method.im_func.__name__
    if not func_name == 'execute_test':
        return ''
    obj = method.im_self
    cls = method.im_class
    print func_name, obj, cls
    return _unpickle_method, (func_name, obj, cls)

def _pickle_method2(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    if func_name.startswith('__') and not func_name.endswith('__'):
        cls_name = cls.__name__.lstrip('_')
        if cls_name:
            func_name = '_' + cls_name + func_name
    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            print func_name
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)

import copy_reg
import types
copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)

def start_server(msg_types, config):
    s = Server(msg_types, config)
    s.start()

def main():
    parser = argparse.ArgumentParser(prog='CapDetServer')
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='Verbosity level')

    args = parser.parse_args()

    log_stdout = LoggerStdout(args.verbosity)
    log.add_logger(log_stdout)

    log_file = LoggerFile('/var/log/CapDet/server.log', args.verbosity)
    log.add_logger(log_file)

    manager = ServerConfigManager()
    manager.start()

    config = manager.ServerConfig()

    processes = []

    p = Process(target=start_server, args=(['4', '10', '12', '14'], config))
    processes.append(p)

    p = Process(target=start_server, args=(['4', '5', '11', '14'], config))
    processes.append(p)

    p = Process(target=start_server, args=(['4', '12', '14'], config))
    processes.append(p)

    try:
        for p in processes:
            p.start()

        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print 'Keyboard interrupt occured...'

if __name__ == '__main__':
    main()
