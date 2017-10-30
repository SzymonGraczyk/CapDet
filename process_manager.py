import multiprocessing

from singleton import Singleton

class ProcessManager(object):
    __metaclass__ = Singleton

    pool = None

    def __init__(self):
        self.pool = multiprocessing.Pool(multiprocessing.cpu_count() - 1)

    def runProcesses(self, jobs):
        print jobs
        self.pool.apply_async(worker_process, jobs)

def worker_process(sub_job):
    print sub_job
