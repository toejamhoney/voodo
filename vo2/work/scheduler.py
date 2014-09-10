# Python Modules
import sys
import threading
from multiprocessing import Process, Pool

NUMPROCS = 5
NUMTASKS = 1


class Scheduler(object):

    def __init__(self, job, vm_mgr):
        self.job = job
        self.vm_mgr = vm_mgr
        self.engine_thread = None
        self.stop_flag = threading.Event()
        self.pool = Pool(NUMPROCS, maxtasksperchild=NUMTASKS)

    def start(self):
        self.stop_flag.clear()
        self.engine_thread = threading.Thread(target=self.engine)
        self.engine_thread.start()

    def stop(self):
        self.pool.terminate()
        self.wait()

    def engine(self):
        for job in self.job.jobs:
            self.pool.apply_async(self.job.tool.run, (job.name, job.path), callback=self.job.tool.callback)
        self.wait()

    def wait(self):
        self.pool.close()
        self.pool.join()
