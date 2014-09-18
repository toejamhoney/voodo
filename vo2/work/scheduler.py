# Python Modules
import signal
import threading
from multiprocessing import Pool
from Queue import Queue

from task import Task


#NUMPROCS = 5
#NUMTASKS = 1


#POOL = Pool(NUMPROCS, maxtasksperchild=NUMTASKS)
POOL = None


def sigint_handler(signum, frame):
    print 'Shutting down'
    POOL.terminate()
    POOL.close()


class Scheduler(object):

    def __init__(self, job, vm_mgr):
        global POOL
        POOL = Pool(len(job.cfg.vms.split(',')), maxtasksperchild=1)
        self.job = job
        self.vms = job.cfg.vms.split(',')
        self.vm_mgr = vm_mgr
        self.vm_queue = Queue()
        self.vm_mgr_thread = threading.Thread(target=self.vm_mgr.find_vm, args=(self.vms, self.vm_queue))
        self.vm_mgr_thread.daemon = True
        self.engine_thread = threading.Thread(target=self.engine)
        self.stop_flag = threading.Event()

    def start(self):
        signal.signal(signal.SIGINT, sigint_handler)
        self.stop_flag.clear()
        self.engine_thread.start()
        self.vm_mgr_thread.start()

    def stop(self):
        POOL.terminate()
        self.cleanup()

    def engine(self):
        for job in self.job.jobs:
            vm = self.vm_queue.get()
            #vm = self.vm_mgr.find_vm(self.job.cfg.vms.split(','))
            task = Task(vm, job.name, job.path, self.job.cfg)
            print "%s" % task
            POOL.apply_async(self.job.tool.run, (task,), callback=self.job.tool.callback)
        self.cleanup()

    @staticmethod
    def cleanup():
        POOL.close()
        POOL.join()
