# Python Modules
import time
import threading
import logging
from multiprocessing import Process

# Voodo Modules
import vm_mgmt
import tasks


class Scheduler(object):
    def __init__(self, storage_gateway, vm_map, proxy):
        self.storage = storage_gateway
        self.loop_thread = None
        self.proxy = proxy
        self.vm_pool = vm_mgmt.VM_Pool(vm_map)
        self.stop_flag = threading.Event()
        self.logger = logging.getLogger("voodo.main").getChild(__name__)
        self.logger.propagate = True

    def start(self):
        self.stop_flag.clear()
        self.loop_thread = threading.Thread(target=self.job_loop)
        self.loop_thread.start()

    def stop(self):
        self.stop_flag.set()
        try:
            self.loop_thread.join(4)
        except AttributeError:
            ''' Scheduler was never started '''
            pass
        else:
            if self.loop_thread.is_alive():
                self.logger.error("Scheduler.stop(): Unable to stop the schedulers analysis loop immediately.")

    def job_loop(self):
        threads = []
        self.logger.info('Scheduler begin job loop')

        while not self.stop_flag.is_set():
            job_dic = self.proxy.job.get_a_task()
            if not job_dic:
                print 'Jobber is empty. Stopping test loop'
                self.stop_flag.set()
                continue
            self.logger.debug('Scheduler job_loop found job: ' + str(job_dic))
            vms = job_dic.get('vms')
            test_vm = False
            while vms and not test_vm and not self.stop_flag.is_set():
                test_vm = self.vm_pool.acquire(*vms)
                time.sleep(1)
            if not self.stop_flag.is_set():
                self.logger.debug('Scheduler job_loop found vm: ' + test_vm.name)
                task = tasks.Task(job_dic, test_vm.name)
                '''
                job_dic['dest_vm'] = test_vm.name
                dst = job_dic.get('job') + '/'
                out = '.'.join([job_dic.get('dest_vm') + '-sp3', 'v5-msvc10', job_dic.get('sample_name'), 'out'])
                err = '.'.join([job_dic.get('dest_vm') + '-sp3', 'v5-msvc10', job_dic.get('sample_name'), 'err'])
                job_dic['out_path'] = dst
                job_dic['err_path'] = err
                '''
                self.logger.debug("Scheduler.job_loop creating task thread")
                threads.append(threading.Thread(target=self.task_handle, args=(test_vm, task)))
                self.proxy.job.begin_task((job_dic['job_id'], job_dic['sample_id']))
                self.logger.debug("Scheduler.job_loop marked task as begun. Starting task thread")
                threads[-1].start()

        for thread in threads:
            self.logger.debug('Scheduler job loop joining thread: ' + str(thread))
            thread.join(1)

        self.logger.info('Scheduler completed job loop')

    def task_handle(self, virt_dev, task):
        if task.proceed:
            self.logger.debug("Scheduler.task_handle creating task process")
            task_child = Process(target=virt_dev.run_task, args=(task, ))
            self.logger.debug("Scheduler.task_handle starting process")
            task_child.start()
            task_child.join(600)
            if task_child.is_alive():
                task_child.terminate()
                task_child.join(10)
        else:
            self.logger.debug("Task error before process creation. Aborting " + task.name)
            task.log("Task error before process creation. Aborting")
        self.vm_pool.release(virt_dev.name)


'''
if __name__ == '__main__':
    import vbox
    import proxy
   
    vm_pool = None
    rpc_proxy = proxy.RPCProxy('jobber')
    scheduler = Scheduler(vm_pool, rpc_proxy)
    
    print 'Starting scheduler',
    scheduler.start()
    time.sleep(3)
    print 'Stopping scheduler.'
    scheduler.stop()
    time.sleep(1)
    print 'Restarting scheduler',
    scheduler.start()
    time.sleep(3)
    print 'Ending test.'
    scheduler.stop()
'''
