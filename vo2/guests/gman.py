import sys
from importlib import import_module
from threading import Thread
from multiprocessing import Manager

import gpool


class GuestManager(object):

    def __init__(self, cfg):
        setting = cfg.setting('guests', 'vms').split(',')
        self.vm_map = dict(zip(setting, [None for i in setting]))
        self.populate_map(cfg)
        self.pool = gpool.GuestPool(self.vm_map)
        self.mgr = Manager()
        self.msgs = self.mgr.Queue()
        self.reader = Thread(target=self.check_msgs)
        self.reader.daemon = True
        self.reader.start()

    def populate_map(self, cfg):
        factory = VmFactory(cfg)
        for vm in self.vm_map:
            self.vm_map[vm] = factory.make(vm)

    def find_vm(self, names, queue):
        """
        :type names: list
        :type queue: Queue.Queue
        """
        while True:
            for name in names:
                vm = self.pool.acquire(name)
                if vm:
                    vm.msgs = self.msgs
                    queue.put(vm)

    def release_vm(self, name):
        self.pool.release(name)

    def check_msgs(self):
        while True:
            msg = self.msgs.get()
            self.release_vm(msg)


class VmFactory(object):

    def __init__(self, cfg):
        self.cfg = cfg

    def make(self, vmname):
        vm = self.cfg.setting('guests', vmname)
        type_, os, addr, port, host_addr = vm.split(',')
        return self.instanciate(vmname, type_, os, addr, port, host_addr)

    def instanciate(self, name, type_, os, addr, port, host_addr):
        try:
            gmodule = import_module('guests.%s' % type_)
        except ImportError as e:
            sys.stderr.write("%s\n\n" % e)
            sys.stderr.write("Unable to import virtual device module: %s\n" % type_)
            return None
        else:
            sys.stdout.write("Register VM: %s @ %s:%s -> %s\n" % (name, addr, port, host_addr))
            return gmodule.VirtualMachine(name, addr, port, host_addr)
