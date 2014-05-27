from Queue import Queue
from threading import RLock

import virt_dev
import proc_mgmt
import voodo_parser

root_cmd = '/usr/bin/VBoxManage'
cmds = { 'showvminfo'  : [ root_cmd, 'showvminfo', '', '--machinereadable' ],
        'list' : [ root_cmd, 'list', 'vms' ], }

class VM_Pool(object):

    def __init__(self, vm_map):
        self.proc_mgr = proc_mgmt.ProcMgr()
        self.vm_map = vm_map
        self.vm_rdy = {}
        self.init_map()
        self.pool_gate = RLock()
        
    def acquire(self, *names):
        self.pool_gate.acquire()
        for name in names:
            if self.vm_rdy.get(name):
                self.vm_rdy[name] = False
                return self.vm_map.get(name)
        self.pool_gate.release()
        return None
    
    def release(self, name):
        self.vm_rdy[name] = True
      
    def init_map(self):
        for name, vm_obj in self.vm_map.items():
            self.vm_rdy[name] = True

    def __str__(self):
        string = 'Pool:'
        for vm in self.vm_map.keys():
            string += vm + ": " + str(self.vm_rdy.get(vm)) + ", "
        return string
    
if __name__ == '__main__':
    pool = VM_Pool()
    print pool
    poss = ['test7a', 'test7b']
    print 'Acquire 3'
    for i in range(3):
        print pool.acquire(*poss)
    pool.release('test7a')
    print 'Released 1'
    print 'Acquire 3'
    for i in range(3):
        print pool.acquire(*poss)
