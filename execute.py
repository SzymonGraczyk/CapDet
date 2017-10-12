import subprocess

from subprocess import PIPE, Popen
from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

def cmdline(command):
    process = Popen(args=command, stdout=PIPE, stderr=subprocess.STDOUT, shell=True)
    return process.communicate()[0], process.returncode

def execute(cmd):
    log.msg("Execute: '%s'" % cmd)
    
    res, rc = cmdline(cmd)
    return res, rc

class ExecutionError(Exception):
    pass
