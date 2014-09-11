# Python Modules
import signal
import threading
from multiprocessing import Pool

from task import Task


NUMPROCS = 5
NUMTASKS = 1


POOL = Pool(NUMPROCS, maxtasksperchild=NUMTASKS)


def sigint_handler(signum, frame):
    print 'Shutting down'
    POOL.terminate()


class Scheduler(object):

    def __init__(self, job, vm_mgr):
        self.job = job
        self.vm_mgr = vm_mgr
        self.engine_thread = None
        self.stop_flag = threading.Event()
        #self.pool = Pool(NUMPROCS, maxtasksperchild=NUMTASKS)

    def start(self):
        signal.signal(signal.SIGINT, sigint_handler)
        self.stop_flag.clear()
        self.engine_thread = threading.Thread(target=self.engine)
        self.engine_thread.start()
        self.engine_thread.join()

    def stop(self):
        POOL.terminate()
        self.cleanup()

    def engine(self):
        for job in self.job.jobs:
            vm = self.vm_mgr.find_vm(self.job.cfg.setting('job', 'vms'))
            task = Task(vm, job.name, job.path, self.job.cfg)
            POOL.apply_async(self.job.tool.run, (task,), callback=self.job.tool.callback)
        self.cleanup()

    @staticmethod
    def cleanup():
        POOL.close()
        POOL.join()
